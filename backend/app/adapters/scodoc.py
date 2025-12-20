"""ScoDoc API adapter."""

import httpx
from typing import Any, Optional
from datetime import datetime, timedelta
import logging

from app.adapters.base import BaseAdapter
from app.models.scolarite import (
    Etudiant,
    Note,
    Absence,
    ModuleStats,
    SemestreStats,
    ScolariteIndicators,
)

logger = logging.getLogger(__name__)


class ScoDocAdapter(BaseAdapter[ScolariteIndicators]):
    """
    Adapter for ScoDoc API.
    
    ScoDoc is an open-source academic management software with a REST API.
    Documentation: https://scodoc.org/ScoDoc9API/
    
    API Endpoints used:
    - POST /api/tokens - Get JWT token
    - GET /api/departement/<acronym>/etudiants - List students
    - GET /api/departement/<acronym>/formsemestres_courants - Current semesters
    - GET /api/formsemestre/<id>/etudiants - Students in semester
    - GET /api/formsemestre/<id>/resultats - Results/grades
    - GET /api/formsemestre/<id>/programme - Modules/UEs
    - GET /api/assiduites/formsemestre/<id>/count - Absences count
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        department: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip('/') if base_url else None
        self.username = username
        self.password = password
        self.department = department
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.client: Optional[httpx.AsyncClient] = None
        self._cache: dict[str, Any] = {}
    
    @property
    def source_name(self) -> str:
        return "ScoDoc"
    
    async def is_available(self) -> bool:
        """Check if ScoDoc is configured."""
        return all([self.base_url, self.username, self.password, self.department])
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if not self.client:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                verify=True,  # SSL verification
                follow_redirects=True,
            )
    
    async def authenticate(self) -> bool:
        """Authenticate to ScoDoc API and get JWT token."""
        if not await self.is_available():
            logger.warning("ScoDoc not configured, cannot authenticate")
            return False
        
        # Check if token is still valid (tokens last ~1h by default)
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return True
        
        await self._ensure_client()
        
        try:
            logger.info(f"Authenticating to ScoDoc at {self.base_url}")
            response = await self.client.post(
                "/api/tokens",
                auth=(self.username, self.password),
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("token")
            # Token expires in ~1h, refresh 10 min before
            self.token_expiry = datetime.now() + timedelta(minutes=50)
            
            # Set token in client headers for subsequent requests
            self.client.headers["Authorization"] = f"Bearer {self.token}"
            logger.info("Successfully authenticated to ScoDoc")
            return True
            
        except httpx.HTTPStatusError as e:
            logger.error(f"ScoDoc authentication failed: {e.response.status_code} - {e.response.text}")
            return False
        except httpx.HTTPError as e:
            logger.error(f"ScoDoc connection error: {e}")
            return False
    
    async def _api_get(self, endpoint: str, params: dict = None) -> Optional[Any]:
        """Make authenticated GET request to ScoDoc API."""
        if not await self.authenticate():
            return None
        
        # Check instance cache (simple memoization for warmup sessions)
        cache_key = f"{endpoint}:{str(params)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            self._cache[cache_key] = data
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"ScoDoc API error {endpoint}: {e.response.status_code}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"ScoDoc request error {endpoint}: {e}")
            return None
    
    async def get_department_info(self) -> Optional[dict]:
        """Get department information."""
        return await self._api_get(f"/api/departement/{self.department}")
    
    async def get_formsemestres_courants(self) -> list[dict]:
        """Get current form semesters for the department."""
        result = await self._api_get(f"/api/departement/{self.department}/formsemestres_courants")
        return result if result else []
    
    async def get_formsemestres_by_annee(self, annee: str) -> list[dict]:
        """Get form semesters for a specific academic year.
        
        Args:
            annee: Academic year in format '2024-2025' or '2024'
        
        Returns:
            List of semesters that match the requested year
        """
        # First get all current semesters
        all_semesters = await self.get_formsemestres_courants()
        
        if not annee:
            return all_semesters
        
        # Extract year from format '2024-2025' or '2024'
        year_start = annee.split('-')[0] if '-' in annee else annee
        
        # Filter semesters by year
        # ScoDoc semesters have 'annee_scolaire' or 'annee' field (e.g., '2024')
        # or date_debut/date_fin fields
        filtered = []
        for sem in all_semesters:
            sem_annee = sem.get('annee_scolaire') or sem.get('annee') or ''
            if str(sem_annee) == str(year_start):
                filtered.append(sem)
                continue
            
            # Check by date_debut if available
            date_debut = sem.get('date_debut', '')
            if date_debut:
                # Format: '2024-09-01' -> year is 2024
                debut_year = date_debut.split('-')[0] if '-' in date_debut else ''
                # Academic year starts in September, so Sept-Dec is start of year
                if debut_year == year_start:
                    filtered.append(sem)
                    continue
                # Jan-Aug belongs to previous academic year
                if int(debut_year) == int(year_start) + 1:
                    debut_month = int(date_debut.split('-')[1]) if '-' in date_debut else 1
                    if debut_month < 9:  # Before September = previous academic year
                        filtered.append(sem)
        
        return filtered if filtered else all_semesters  # Fallback to all if no match
    async def get_formsemestre_etudiants(self, formsemestre_id: int) -> list[dict]:
        """Get students enrolled in a semester."""
        result = await self._api_get(f"/api/formsemestre/{formsemestre_id}/etudiants")
        return result if result else []
    
    async def get_formsemestre_resultats(self, formsemestre_id: int) -> Optional[dict]:
        """Get results/grades for a semester."""
        return await self._api_get(f"/api/formsemestre/{formsemestre_id}/resultats")
    
    async def get_formsemestre_programme(self, formsemestre_id: int) -> Optional[dict]:
        """Get program (UEs, modules) for a semester."""
        return await self._api_get(f"/api/formsemestre/{formsemestre_id}/programme")
    
    async def get_formsemestre_assiduites_count(self, formsemestre_id: int) -> Optional[dict]:
        """Get ONLY absences count for a semester.
        
        WARNING: The ScoDoc /api/assiduites/.../count endpoint does NOT support
        filtering by 'etat' parameter - it always returns totals for ALL assiduités
        (PRESENT + ABSENT + RETARD combined).
        
        This method fetches the detailed list and counts only ABSENT records.
        Returns dict with: heure (hours absent), heure_just, heure_non_just
        """
        from datetime import datetime
        
        # Fetch the detailed list instead of using /count (which ignores etat filter)
        assiduites_list = await self._api_get(
            f"/api/assiduites/formsemestre/{formsemestre_id}"
        )
        
        if not assiduites_list or not isinstance(assiduites_list, list):
            return {"heure": 0, "heure_just": 0, "heure_non_just": 0}
        
        # Filter to ONLY count ABSENT records
        total_hours = 0.0
        hours_just = 0.0
        hours_non_just = 0.0
        
        for item in assiduites_list:
            if item.get('etat') != 'ABSENT':
                continue  # Skip PRESENT and RETARD
            
            # Calculate duration in hours
            try:
                date_debut_str = item.get('date_debut', '')
                date_fin_str = item.get('date_fin', '')
                
                if date_debut_str and date_fin_str:
                    date_debut = datetime.fromisoformat(date_debut_str.replace('Z', '+00:00'))
                    date_fin = datetime.fromisoformat(date_fin_str.replace('Z', '+00:00'))
                    duration_hours = (date_fin - date_debut).total_seconds() / 3600
                else:
                    duration_hours = 2.0  # Default
            except Exception:
                duration_hours = 2.0
            
            total_hours += duration_hours
            if item.get('est_just'):
                hours_just += duration_hours
            else:
                hours_non_just += duration_hours
        
        return {
            "heure": round(total_hours, 1),
            "heure_just": round(hours_just, 1),
            "heure_non_just": round(hours_non_just, 1),
        }
    
    async def get_formsemestre_etudiants(self, formsemestre_id: int) -> list[dict]:
        """Get list of students enrolled in a semester."""
        result = await self._api_get(f"/api/formsemestre/{formsemestre_id}/etudiants")
        return result if result else []
    
    async def get_department_etudiants(self) -> list[dict]:
        """Get all students in department."""
        result = await self._api_get(f"/api/departement/{self.department}/etudiants")
        return result if result else []
    
    async def fetch_raw(self, **kwargs) -> dict[str, Any]:
        """Fetch all scolarité data from ScoDoc."""
        if not await self.authenticate():
            logger.error("Cannot fetch data: ScoDoc authentication failed")
            return {}
        
        data = {
            "etudiants": [],
            "semestres": [],
            "resultats": [],
            "programmes": [],
            "assiduites": [],
            "sem_etudiants": {},  # Map formsemestre_id -> nb_etudiants
        }
        
        try:
            # Get semesters - filter by year if provided
            annee = kwargs.get('annee')
            if annee:
                semestres = await self.get_formsemestres_by_annee(annee)
                logger.info(f"Found {len(semestres)} semesters for year {annee}")
            else:
                semestres = await self.get_formsemestres_courants()
                logger.info(f"Found {len(semestres)} current semesters")
            data["semestres"] = semestres
            
            # Get all students in department
            all_etudiants = await self.get_department_etudiants()
            data["etudiants"] = all_etudiants
            logger.info(f"Found {len(all_etudiants)} students in department")
            
            # For each semester, get detailed data
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                if not sem_id:
                    continue
                
                logger.info(f"Fetching data for semester {sem_id}: {sem.get('titre', 'N/A')}")
                
                # Get enrolled students count for this semester
                sem_etudiants = await self.get_formsemestre_etudiants(sem_id)
                data["sem_etudiants"][sem_id] = len(sem_etudiants)
                logger.info(f"  Semester {sem_id}: {len(sem_etudiants)} enrolled students")
                
                # Get results
                resultats = await self.get_formsemestre_resultats(sem_id)
                if resultats:
                    data["resultats"].append({
                        "formsemestre_id": sem_id,
                        "data": resultats
                    })
                
                # Get program
                programme = await self.get_formsemestre_programme(sem_id)
                if programme:
                    data["programmes"].append({
                        "formsemestre_id": sem_id,
                        "data": programme
                    })
                
                # Get absences count
                assiduites = await self.get_formsemestre_assiduites_count(sem_id)
                if assiduites:
                    data["assiduites"].append({
                        "formsemestre_id": sem_id,
                        "data": assiduites
                    })
                    logger.info(f"  Semester {sem_id}: {assiduites.get('heure', 0)} hours absent")
            
        except Exception as e:
            logger.error(f"Error fetching ScoDoc data: {e}")
        
        return data
    
    def transform(self, raw_data: dict[str, Any]) -> ScolariteIndicators:
        """Transform ScoDoc data to internal indicators."""
        etudiants = raw_data.get("etudiants", [])
        semestres = raw_data.get("semestres", [])
        resultats_list = raw_data.get("resultats", [])
        programmes_list = raw_data.get("programmes", [])
        
        # Total students will be calculated from current semesters results, not historical department list
        # (etudiants from /departement/etudiants includes all students ever enrolled)
        
        # Group by formation and semester
        par_formation: dict[str, int] = {}
        par_semestre: dict[str, int] = {}
        
        # Get formation info from semesters instead of students
        # (students from /departement/etudiants don't have formation info)
        for sem in semestres:
            formation = sem.get("titre", "").split(" semestre")[0].strip()
            if not formation:
                formation = sem.get("formation", {}).get("acronyme", "BUT RT") if isinstance(sem.get("formation"), dict) else "BUT RT"
        
        # Count per semester from current semesters
        for sem in semestres:
            sem_name = sem.get("titre_num") or sem.get("titre") or f"S{sem.get('semestre_id', '?')}"
            par_semestre[sem_name] = 0
        
        # Build module info dictionary from programmes
        # Key: module_id, Value: {code, titre, ...}
        modules_info: dict[int, dict] = {}
        for prog_item in programmes_list:
            prog_data = prog_item.get("data", {})
            # Ressources contain module info
            ressources = prog_data.get("ressources", [])
            if isinstance(ressources, list):
                for res in ressources:
                    module_data = res.get("module", {})
                    if module_data:
                        mod_id = res.get("id") or res.get("module_id")
                        if mod_id:
                            modules_info[mod_id] = {
                                "code": module_data.get("code", ""),
                                "titre": module_data.get("titre", module_data.get("abbrev", "")),
                                "ue_id": module_data.get("ue_id"),
                            }
            # SAEs
            saes = prog_data.get("saes", [])
            if isinstance(saes, list):
                for sae in saes:
                    module_data = sae.get("module", {})
                    if module_data:
                        mod_id = sae.get("id") or sae.get("module_id")
                        if mod_id:
                            modules_info[mod_id] = {
                                "code": module_data.get("code", ""),
                                "titre": module_data.get("titre", module_data.get("abbrev", "")),
                                "ue_id": module_data.get("ue_id"),
                            }
        
        # Calculate stats from resultats
        all_moyennes = []
        nb_validations = 0
        nb_total_notes = 0
        modules_stats = []
        semestres_stats = []
        
        # Collect module grades PER SEMESTER to avoid counting same module across semesters
        # Key: (sem_id, module_id, ue_id), Value: list of grades
        module_grades_per_sem: dict[tuple, list[float]] = {}
        
        for res_item in resultats_list:
            res_data = res_item.get("data")
            sem_id = res_item.get("formsemestre_id")
            
            # Find semester info
            sem_info = next(
                (s for s in semestres if (s.get("formsemestre_id") == sem_id or s.get("id") == sem_id)), 
                {}
            )
            
            # Get formation name from semester title
            if sem_info:
                formation_name = sem_info.get("titre", "").split(" semestre")[0].strip()
                if not formation_name:
                    formation_name = "BUT RT"
                # Count students per formation
                sem_nb_etudiants = len(res_data) if isinstance(res_data, list) else 0
                par_formation[formation_name] = par_formation.get(formation_name, 0) + sem_nb_etudiants
            
            # Moyennes for this semester
            sem_moyennes = []
            sem_validations = 0
            
            # ScoDoc resultats API returns a list of student results
            if isinstance(res_data, list):
                for etud_res in res_data:
                    if isinstance(etud_res, dict):
                        etudid = etud_res.get("etudid")  # Get student ID
                        
                        # moy_gen is the general average as a string like "16.38" or "~" if not calculated
                        moy = etud_res.get("moy_gen")
                        if moy and moy != "~" and moy != "":
                            try:
                                moy_val = float(str(moy).replace(",", "."))
                                all_moyennes.append(moy_val)
                                sem_moyennes.append(moy_val)
                                nb_total_notes += 1
                                if moy_val >= 10:
                                    nb_validations += 1
                                    sem_validations += 1
                            except (ValueError, TypeError):
                                pass
                        
                        # Extract module grades (keys like moy_res_10975_1578 or moy_sae_xxx_yyy)
                        for key, value in etud_res.items():
                            if (key.startswith("moy_res_") or key.startswith("moy_sae_")) and value and value != "~":
                                try:
                                    # Parse key: moy_res_{module_id}_{ue_id}
                                    parts = key.split("_")
                                    if len(parts) >= 4:
                                        module_id = int(parts[2])
                                        ue_id = int(parts[3])
                                        grade_val = float(str(value).replace(",", "."))
                                        
                                        # Key includes sem_id to keep modules separate per semester
                                        mod_key = (sem_id, module_id, ue_id)
                                        if mod_key not in module_grades_per_sem:
                                            module_grades_per_sem[mod_key] = []
                                        # Store (etudid, grade) tuple to track unique students
                                        module_grades_per_sem[mod_key].append((etudid, grade_val))
                                except (ValueError, TypeError, IndexError):
                                    pass
            
            # Also handle dict format (older API format)
            elif isinstance(res_data, dict):
                for etud_key, etud_res in res_data.items():
                    if isinstance(etud_res, dict):
                        moy = etud_res.get("moy_gen") or etud_res.get("moyenne")
                        if moy and moy != "~":
                            try:
                                moy_val = float(str(moy).replace(",", "."))
                                all_moyennes.append(moy_val)
                                sem_moyennes.append(moy_val)
                                nb_total_notes += 1
                                if moy_val >= 10:
                                    nb_validations += 1
                                    sem_validations += 1
                            except (ValueError, TypeError):
                                pass
            
            # Build semester stats
            if sem_info:
                annee_scolaire = sem_info.get("annee_scolaire", "")
                # Ensure annee is a string
                if isinstance(annee_scolaire, int):
                    annee_scolaire = f"{annee_scolaire}-{annee_scolaire + 1}"
                elif not isinstance(annee_scolaire, str):
                    annee_scolaire = str(annee_scolaire) if annee_scolaire else ""
                
                nb_etudiants_sem = len(res_data) if isinstance(res_data, list) else len(res_data.keys()) if isinstance(res_data, dict) else 0
                
                # Update par_semestre count
                sem_name = sem_info.get("titre_num") or sem_info.get("titre") or f"S{sem_info.get('semestre_id', '?')}"
                par_semestre[sem_name] = nb_etudiants_sem
                
                # Calculate semester success rate (as percentage 0-100)
                sem_taux_reussite = (sem_validations / len(sem_moyennes) * 100) if sem_moyennes else 0
                    
                semestres_stats.append(SemestreStats(
                    code=f"S{sem_info.get('semestre_id', '?')}",
                    nom=sem_info.get("titre", "Semestre"),
                    annee=annee_scolaire,
                    nb_etudiants=nb_etudiants_sem,
                    moyenne_generale=round(sum(sem_moyennes) / len(sem_moyennes), 2) if sem_moyennes else 0,
                    taux_reussite=round(sem_taux_reussite, 1),
                    taux_absenteisme=0.0,  # Would need to calculate from assiduites
                ))
        
        # Calculate global stats
        moyenne_generale = sum(all_moyennes) / len(all_moyennes) if all_moyennes else 0
        taux_reussite = (nb_validations / nb_total_notes * 100) if nb_total_notes > 0 else 0
        
        # Build module statistics from collected grades
        # Keep modules separate per semester, then aggregate by code within same semester
        import statistics
        
        # Group by (sem_id, code) to keep modules unique per semester
        module_grades_by_sem_code: dict[tuple, dict] = {}
        for (sem_id, module_id, ue_id), grades in module_grades_per_sem.items():
            mod_info = modules_info.get(module_id, {})
            code = mod_info.get("code", "")
            titre = mod_info.get("titre", "Module")
            
            # Skip if no code
            if not code:
                continue
            
            key = (sem_id, code)
            if key not in module_grades_by_sem_code:
                module_grades_by_sem_code[key] = {"titre": titre, "grades": [], "sem_id": sem_id}
            
            # Add grades for this UE (a module may have grades in multiple UEs)
            # grades is now a list of (etudid, grade_val) tuples
            module_grades_by_sem_code[key]["grades"].extend(grades)
        
        # Now aggregate same codes across semesters for display
        # But keep nb_etudiants as the UNIQUE count per code (using etudid)
        module_stats_by_code: dict[str, dict] = {}
        for (sem_id, code), data in module_grades_by_sem_code.items():
            grades = data["grades"]  # List of (etudid, grade) tuples
            titre = data["titre"]
            
            if not grades:
                continue
            
            if code not in module_stats_by_code:
                module_stats_by_code[code] = {
                    "titre": titre, 
                    "grade_values": [],  # Just the grade values for stats
                    "unique_students": set(),  # Set of etudid
                    "semesters": set()
                }
            
            module_stats_by_code[code]["semesters"].add(sem_id)
            for etudid, grade_val in grades:
                module_stats_by_code[code]["grade_values"].append(grade_val)
                if etudid:  # Only count if we have a valid etudid
                    module_stats_by_code[code]["unique_students"].add(etudid)
        
        for code, data in module_stats_by_code.items():
            grades = data["grade_values"]
            titre = data["titre"]
            nb_unique = len(data["unique_students"]) if data["unique_students"] else len(grades)
            
            if not grades:
                continue
            
            # Calculate statistics
            moyenne = sum(grades) / len(grades)
            mediane = statistics.median(grades) if grades else 0
            ecart_type = statistics.stdev(grades) if len(grades) > 1 else 0
            nb_reussis = sum(1 for g in grades if g >= 10)
            taux_reussite_mod = (nb_reussis / len(grades) * 100) if grades else 0
            
            modules_stats.append(ModuleStats(
                code=code,
                nom=titre[:50] if titre else "Module",  # Truncate long names
                moyenne=round(moyenne, 2),
                mediane=round(mediane, 2),
                ecart_type=round(ecart_type, 2),
                taux_reussite=round(taux_reussite_mod, 1),
                nb_etudiants=nb_unique,  # Unique students (by etudid)
                nb_notes=len(grades),
            ))
        
        # Sort modules by code
        modules_stats.sort(key=lambda m: m.code)
        
        # Calculate absence rate from assiduites data
        # ScoDoc returns: {"heure": total_hours_absent, "compte": nb_absences, ...}
        # We estimate expected hours: ~400h per semester per student
        HEURES_SEMESTRE_ESTIMEES = 400  # Estimated hours per student per semester
        
        assiduites_list = raw_data.get("assiduites", [])
        sem_etudiants = raw_data.get("sem_etudiants", {})  # Map sem_id -> nb_etudiants
        total_heures_absence = 0.0
        total_heures_attendues = 0.0
        
        for ass_item in assiduites_list:
            ass_data = ass_item.get("data", {})
            sem_id = ass_item.get("formsemestre_id")
            
            if isinstance(ass_data, dict):
                # Get hours of absence from ScoDoc
                heures_absence = ass_data.get("heure", 0) or 0
                total_heures_absence += heures_absence
                
                # Get student count for this semester from the pre-fetched data
                nb_etudiants_sem = sem_etudiants.get(sem_id, 0)
                
                if nb_etudiants_sem > 0:
                    total_heures_attendues += nb_etudiants_sem * HEURES_SEMESTRE_ESTIMEES
                    logger.debug(f"Semester {sem_id}: {heures_absence}h absent / {nb_etudiants_sem * HEURES_SEMESTRE_ESTIMEES}h expected")
        
        # Calculate absence rate
        taux_absenteisme = (total_heures_absence / total_heures_attendues * 100) if total_heures_attendues > 0 else 0
        logger.info(f"Taux absentéisme: {total_heures_absence}h absent / {total_heures_attendues}h expected = {taux_absenteisme:.2f}%")
        
        # Total students = sum of all students in current semesters
        total_etudiants_courants = sum(par_formation.values())
        
        return ScolariteIndicators(
            total_etudiants=total_etudiants_courants,
            etudiants_par_formation=par_formation,
            etudiants_par_semestre=par_semestre,
            moyenne_generale=round(moyenne_generale, 2),
            taux_reussite_global=round(taux_reussite, 2),
            taux_absenteisme=round(taux_absenteisme, 2),
            modules_stats=modules_stats,
            semestres_stats=semestres_stats,
            evolution_effectifs={},  # Would need historical data
        )
    
    async def get_etudiants(self, department: Optional[str] = None) -> list[Etudiant]:
        """Get list of students."""
        if not await self.authenticate():
            return []
        
        dept = department or self.department
        raw_etudiants = await self._api_get(f"/api/departement/{dept}/etudiants")
        
        if not raw_etudiants:
            return []
        
        return [
            Etudiant(
                id=str(e.get("etudid", "")),
                nom=e.get("nom", ""),
                prenom=e.get("prenom", ""),
                email=e.get("email"),
                formation=e.get("formation_acronyme", ""),
                semestre=f"S{e.get('semestre_id', '?')}" if e.get("semestre_id") else "",
                groupe=e.get("groupes", [{}])[0].get("group_name") if e.get("groupes") else None,
            )
            for e in raw_etudiants
        ]
    
    async def health_check(self) -> bool:
        """Check if ScoDoc API is reachable and authenticated."""
        try:
            if await self.authenticate():
                # Try to get department info as a simple test
                info = await self.get_department_info()
                return info is not None
            return False
        except Exception as e:
            logger.error(f"ScoDoc health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.token = None


# Factory function to get the appropriate adapter
def get_scodoc_adapter(
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    department: Optional[str] = None,
    use_mock: bool = False,
) -> BaseAdapter:
    """
    Get ScoDoc adapter - real or mock based on configuration.
    
    If use_mock=True or no credentials provided, returns MockScoDocAdapter.
    """
    if use_mock or not all([base_url, username, password, department]):
        return MockScoDocAdapter()
    return ScoDocAdapter(base_url, username, password, department)


# Mock adapter for development/testing without ScoDoc
class MockScoDocAdapter(BaseAdapter[ScolariteIndicators]):
    """Mock ScoDoc adapter with sample data for development."""
    
    @property
    def source_name(self) -> str:
        return "ScoDoc (Mock)"
    
    async def is_available(self) -> bool:
        return True
    
    async def authenticate(self) -> bool:
        return True
    
    async def fetch_raw(self, **kwargs) -> dict[str, Any]:
        """Return mock data."""
        annee = kwargs.get('annee', '2024-2025')
        # Parse year from format '2024-2025' or default to 2024
        year_start = int(annee.split('-')[0]) if annee and '-' in annee else 2024
        year_str = f"{year_start}-{year_start + 1}"
        
        # Generate different data based on year
        base_students = 120 + (year_start - 2020) * 10  # More students each year
        
        return {
            "etudiants": [
                {"etudid": i, "nom": f"Nom{i}", "prenom": f"Prenom{i}", 
                 "formation": "BUT RT", "semestre": f"S{(i % 6) + 1}"}
                for i in range(1, base_students + 1)
            ],
            "semestres": [
                {"formsemestre_id": i, "titre": f"Semestre {i}", "annee": year_str, "annee_scolaire": year_start}
                for i in range(1, 7)
            ],
            "annee": year_str,
        }
    
    def transform(self, raw_data: dict[str, Any]) -> ScolariteIndicators:
        etudiants = raw_data.get("etudiants", [])
        annee = raw_data.get("annee", "2024-2025")
        year_start = int(annee.split('-')[0]) if '-' in annee else 2024
        
        # Vary data by year for more realistic mock
        base_moyenne = 11.5 + (year_start - 2020) * 0.2
        base_reussite = 0.72 + (year_start - 2020) * 0.02
        nb_per_sem = len(etudiants) // 6
        
        par_formation = {"BUT RT": len(etudiants)}
        par_semestre = {f"S{i}": nb_per_sem + (i % 3) for i in range(1, 7)}
        
        return ScolariteIndicators(
            total_etudiants=len(etudiants),
            etudiants_par_formation=par_formation,
            etudiants_par_semestre=par_semestre,
            moyenne_generale=round(base_moyenne, 2),
            taux_reussite_global=round(min(base_reussite, 0.95), 2),
            taux_absenteisme=round(8.0 - (year_start - 2020) * 0.3, 1),  # Decreasing over years
            modules_stats=[
                ModuleStats(
                    code="R101", nom="Init Dev", moyenne=round(base_moyenne - 0.5, 2), mediane=round(base_moyenne, 2),
                    ecart_type=3.2, taux_reussite=round(base_reussite - 0.05, 2), nb_etudiants=nb_per_sem, nb_notes=nb_per_sem
                ),
                ModuleStats(
                    code="R102", nom="Réseaux", moyenne=round(base_moyenne + 1.0, 2), mediane=round(base_moyenne + 1.2, 2),
                    ecart_type=2.8, taux_reussite=round(base_reussite + 0.05, 2), nb_etudiants=nb_per_sem, nb_notes=nb_per_sem
                ),
                ModuleStats(
                    code="R103", nom="Systèmes", moyenne=round(base_moyenne - 1.0, 2), mediane=round(base_moyenne - 0.8, 2),
                    ecart_type=4.1, taux_reussite=round(base_reussite - 0.10, 2), nb_etudiants=nb_per_sem, nb_notes=nb_per_sem
                ),
            ],
            semestres_stats=[
                SemestreStats(
                    code="S1", nom="Semestre 1", annee=annee,
                    nb_etudiants=nb_per_sem + 2, moyenne_generale=round(base_moyenne - 0.3, 2), 
                    taux_reussite=round(base_reussite - 0.03, 2), taux_absenteisme=7.2
                ),
                SemestreStats(
                    code="S2", nom="Semestre 2", annee=annee,
                    nb_etudiants=nb_per_sem, moyenne_generale=round(base_moyenne + 0.2, 2),
                    taux_reussite=round(base_reussite + 0.02, 2), taux_absenteisme=4.5
                ),
            ],
            evolution_effectifs={
                "2021": 120, "2022": 135, "2023": 142, "2024": 150, "2025": 158
            },
        )
