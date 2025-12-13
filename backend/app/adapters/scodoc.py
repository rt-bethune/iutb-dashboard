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
        
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
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
        """Get absences count for a semester."""
        return await self._api_get(
            f"/api/assiduites/formsemestre/{formsemestre_id}/count",
            params={"metric": "compte", "split": "true"}
        )
    
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
        }
        
        try:
            # Get current semesters
            semestres = await self.get_formsemestres_courants()
            data["semestres"] = semestres
            logger.info(f"Found {len(semestres)} current semesters")
            
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
        
        # Collect module grades across all semesters
        # Key: (module_id, ue_id), Value: list of grades
        module_grades: dict[tuple, list[float]] = {}
        
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
                                        
                                        mod_key = (module_id, ue_id)
                                        if mod_key not in module_grades:
                                            module_grades[mod_key] = []
                                        module_grades[mod_key].append(grade_val)
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
        # Aggregate by module CODE (not module_id) to combine same modules across semesters
        import statistics
        
        module_grades_by_code: dict[str, dict] = {}
        for (module_id, ue_id), grades in module_grades.items():
            mod_info = modules_info.get(module_id, {})
            code = mod_info.get("code", "")
            titre = mod_info.get("titre", "Module")
            
            # Skip if no code
            if not code:
                continue
            
            if code not in module_grades_by_code:
                module_grades_by_code[code] = {"titre": titre, "grades": []}
            
            # Add grades (avoiding duplicates within same UE)
            module_grades_by_code[code]["grades"].extend(grades)
        
        for code, data in module_grades_by_code.items():
            grades = data["grades"]
            titre = data["titre"]
            
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
                nb_etudiants=len(grades),
                nb_notes=len(grades),
            ))
        
        # Sort modules by code
        modules_stats.sort(key=lambda m: m.code)
        
        # Calculate absence rate from assiduites data
        assiduites_list = raw_data.get("assiduites", [])
        total_absences = 0
        total_presences = 0
        for ass_item in assiduites_list:
            ass_data = ass_item.get("data", {})
            if isinstance(ass_data, dict):
                total_absences += ass_data.get("absent", {}).get("compte", 0)
                total_presences += ass_data.get("present", {}).get("compte", 0)
        
        taux_absenteisme = (total_absences / (total_absences + total_presences) * 100) if (total_absences + total_presences) > 0 else 0
        
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
        return {
            "etudiants": [
                {"etudid": i, "nom": f"Nom{i}", "prenom": f"Prenom{i}", 
                 "formation": "BUT RT", "semestre": f"S{(i % 6) + 1}"}
                for i in range(1, 151)
            ],
            "semestres": [
                {"formsemestre_id": i, "titre": f"Semestre {i}", "annee": "2024-2025"}
                for i in range(1, 7)
            ],
        }
    
    def transform(self, raw_data: dict[str, Any]) -> ScolariteIndicators:
        etudiants = raw_data.get("etudiants", [])
        
        par_formation = {"BUT RT": 100}
        par_semestre = {f"S{i}": 25 for i in range(1, 7)}
        
        return ScolariteIndicators(
            total_etudiants=len(etudiants),
            etudiants_par_formation=par_formation,
            etudiants_par_semestre=par_semestre,
            moyenne_generale=12.34,
            taux_reussite_global=0.78,
            taux_absenteisme=0.065,
            modules_stats=[
                ModuleStats(
                    code="R101", nom="Init Dev", moyenne=11.5, mediane=12.0,
                    ecart_type=3.2, taux_reussite=0.82, nb_etudiants=50, nb_notes=50
                ),
                ModuleStats(
                    code="R102", nom="Réseaux", moyenne=13.2, mediane=13.5,
                    ecart_type=2.8, taux_reussite=0.88, nb_etudiants=50, nb_notes=50
                ),
                ModuleStats(
                    code="R103", nom="Systèmes", moyenne=10.8, mediane=11.0,
                    ecart_type=4.1, taux_reussite=0.72, nb_etudiants=50, nb_notes=50
                ),
            ],
            semestres_stats=[
                SemestreStats(
                    code="S1", nom="Semestre 1", annee="2024-2025",
                    nb_etudiants=52, moyenne_generale=11.8, 
                    taux_reussite=0.75, taux_absenteisme=0.07
                ),
                SemestreStats(
                    code="S2", nom="Semestre 2", annee="2024-2025",
                    nb_etudiants=48, moyenne_generale=12.5,
                    taux_reussite=0.80, taux_absenteisme=0.05
                ),
            ],
            evolution_effectifs={
                "2021": 120, "2022": 135, "2023": 142, "2024": 150
            },
        )
