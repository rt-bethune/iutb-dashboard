"""Service for calculating student alerts from ScoDoc data."""

from typing import Optional
from datetime import date
import logging

from app.adapters.scodoc import ScoDocAdapter
from app.models.alertes import (
    AlerteEtudiant,
    ConfigAlerte,
    NiveauAlerte,
    TypeAlerte,
    ProfilEtudiant,
    FicheEtudiantComplete,
    StatistiquesAbsences,
    ProgressionEtudiant,
    ScoreRisque,
)

logger = logging.getLogger(__name__)


class AlertesService:
    """Service for managing student alerts using ScoDoc data."""
    
    def __init__(self, adapter: ScoDocAdapter, config: Optional[ConfigAlerte] = None):
        self.adapter = adapter
        self.config = config or ConfigAlerte()

    def _filter_semestres(
        self,
        semestres: list[dict],
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> list[dict]:
        """Apply filters to a list of semesters."""
        if semestre:
            semestres = [s for s in semestres if f"S{s.get('semestre_id')}" == semestre]
        
        if formation:
            formation_norm = formation.lower()
            semestres = [
                s for s in semestres 
                if formation_norm in (s.get('titre', '') or '').lower() 
                or formation_norm in (s.get('titre_formation', '') or '').lower()
            ]

        if modalite:
            mod_norm = modalite.lower()
            if mod_norm == 'fa':
                semestres = [
                    s for s in semestres 
                    if ' fa' in (s.get('titre', '') or '').lower() 
                    or 'apprentissage' in (s.get('titre', '') or '').lower()
                ]
            elif mod_norm == 'fi':
                semestres = [
                    s for s in semestres 
                    if not (' fa' in (s.get('titre', '') or '').lower() 
                    or 'apprentissage' in (s.get('titre', '') or '').lower())
                ]
        return semestres
    
    async def get_etudiant_details(self, etudiant_id: str) -> Optional[dict]:
        """Fetch student details from ScoDoc."""
        if not await self.adapter.authenticate():
            logger.error("Cannot fetch student: ScoDoc authentication failed")
            return None
        
        # Get student info - use etudid endpoint
        etudiant = await self.adapter._api_get(
            f"/api/etudiant/etudid/{etudiant_id}"
        )
        return etudiant
    
    async def get_etudiant_formsemestres(self, etudiant_id: str) -> list[dict]:
        """Get all semesters the student has been enrolled in."""
        if not await self.adapter.authenticate():
            return []
        return await self.adapter.get_formsemestres_etudiant(etudiant_id)
    
    async def get_etudiant_bulletin(self, etudiant_id: str, formsemestre_id: int) -> Optional[dict]:
        """Get student's grade bulletin for a semester."""
        if not await self.adapter.authenticate():
            return None
        return await self.adapter.get_bulletin_etudiant(etudiant_id, formsemestre_id)
    
    async def get_etudiant_absences(self, etudiant_id: str) -> Optional[dict]:
        """Get student's absence counts by fetching the assiduités list and filtering.
        
        IMPORTANT: The ScoDoc /api/assiduites/etudid/{id}/count endpoint does NOT
        support filtering by 'etat' parameter - it always returns the total count
        for ALL assiduités (present + absent + retard).
        
        Therefore, we must:
        1. Fetch the detailed list from /api/assiduites/etudid/{id}
        2. Filter client-side by etat == 'ABSENT'
        3. Calculate hours from (date_fin - date_debut) for each absence
        
        ScoDoc assiduités states: ABSENT, PRESENT, RETARD
        """
        if not await self.adapter.authenticate():
            return None
        
        try:
            # Fetch the detailed assiduités list for this student
            assiduites_list = await self.adapter._api_get(
                f"/api/assiduites/etudid/{etudiant_id}"
            )
            
            if not assiduites_list or not isinstance(assiduites_list, list):
                return {
                    "absences": [],
                    "counts": {"nbabs": 0, "nbabs_just": 0, "nbabs_non_just": 0}
                }
            
            # Filter to get only ABSENT records (exclude PRESENT and RETARD)
            absences = [a for a in assiduites_list if a.get('etat') == 'ABSENT']
            
            # Calculate total hours from date_debut/date_fin
            total_hours = 0.0
            hours_just = 0.0
            hours_non_just = 0.0
            
            for absence in absences:
                # Calculate duration in hours
                try:
                    from datetime import datetime
                    date_debut_str = absence.get('date_debut', '')
                    date_fin_str = absence.get('date_fin', '')
                    
                    if date_debut_str and date_fin_str:
                        # Parse ISO format dates (e.g., '2024-10-11T15:00:00+02:00')
                        date_debut = datetime.fromisoformat(date_debut_str.replace('Z', '+00:00'))
                        date_fin = datetime.fromisoformat(date_fin_str.replace('Z', '+00:00'))
                        duration_hours = (date_fin - date_debut).total_seconds() / 3600
                    else:
                        # Default to 2 hours if no time info
                        duration_hours = 2.0
                except Exception:
                    duration_hours = 2.0  # Default duration
                
                total_hours += duration_hours
                
                # Check if justified
                if absence.get('est_just'):
                    hours_just += duration_hours
                else:
                    hours_non_just += duration_hours
            
            # Round to reasonable precision
            total_hours = round(total_hours, 1)
            hours_just = round(hours_just, 1)
            hours_non_just = round(hours_non_just, 1)
            
            logger.debug(f"Student {etudiant_id} absences: {len(absences)} records, "
                        f"total={total_hours}h, just={hours_just}h, non_just={hours_non_just}h")
            
            return {
                "absences": absences,  # Include the detail list for further processing
                "counts": {"nbabs": total_hours, "nbabs_just": hours_just, "nbabs_non_just": hours_non_just}
            }
            
        except Exception as e:
            logger.error(f"Error fetching assiduites for student {etudiant_id}: {e}")
            return {
                "absences": [],
                "counts": {"nbabs": 0, "nbabs_just": 0, "nbabs_non_just": 0}
            }
    
    def _calculate_niveau_alerte(self, valeur: float, seuil_attention: float, seuil_critique: float, inversed: bool = False) -> NiveauAlerte:
        """Calculate alert level based on value and thresholds.
        
        Args:
            valeur: Current value
            seuil_attention: Threshold for ATTENTION level
            seuil_critique: Threshold for CRITIQUE level
            inversed: If True, higher values are worse (e.g., absences). If False, lower values are worse (e.g., grades)
        """
        if inversed:
            # Higher is worse (absences, risk score)
            if valeur >= seuil_critique:
                return NiveauAlerte.CRITIQUE
            elif valeur >= seuil_attention:
                return NiveauAlerte.ATTENTION
            else:
                return NiveauAlerte.INFO
        else:
            # Lower is worse (grades)
            if valeur <= seuil_critique:
                return NiveauAlerte.CRITIQUE
            elif valeur <= seuil_attention:
                return NiveauAlerte.ATTENTION
            else:
                return NiveauAlerte.INFO
    
    def _calculate_risk_score(
        self,
        moyenne: float,
        taux_absenteisme: float,
        type_bac: str,
        progression: float = 0,
    ) -> tuple[float, dict[str, float]]:
        """Calculate dropout risk score based on multiple factors.
        
        Returns:
            Tuple of (global_score, factors_dict)
        """
        facteurs = {}
        
        # Notes factor (0-1, higher = more risk)
        # Scale: 20 -> 0, 10 -> 0.5, 0 -> 1
        facteurs["notes"] = max(0, min(1, (20 - moyenne) / 20))
        
        # Assiduité factor (0-1)
        # Scale: 0% -> 0, 15% -> 0.5, 30%+ -> 1
        facteurs["assiduite"] = max(0, min(1, taux_absenteisme / 0.30))
        
        # Progression factor (0-1)
        # Negative progression increases risk
        if progression < 0:
            facteurs["progression"] = min(1, abs(progression) / 5)  # -5 points = max risk
        else:
            facteurs["progression"] = 0
        
        # Bac type factor (based on historical success rates)
        bac_risk = {
            "Général": 0.1,
            "STI2D": 0.25,
            "STMG": 0.35,
            "Pro": 0.5,
            "Autre": 0.3,
        }
        facteurs["type_bac"] = bac_risk.get(type_bac, 0.3)
        
        # Weighted global score
        weights = {
            "notes": 0.40,
            "assiduite": 0.30,
            "progression": 0.15,
            "type_bac": 0.15,
        }
        
        score_global = sum(facteurs[k] * weights[k] for k in facteurs)
        
        return score_global, facteurs
    
    async def generate_alertes_for_student(
        self,
        etudiant_id: str,
        etudiant_nom: str,
        etudiant_prenom: str,
        moyenne: float,
        taux_absenteisme: float,
        progression: float,
        semestre: str,
        modules_faibles: list[str] = None,
    ) -> list[AlerteEtudiant]:
        """Generate alerts for a student based on their metrics."""
        alertes = []
        modules_faibles = modules_faibles or []
        
        # Check academic difficulty (moyenne_difficulte)
        if moyenne < self.config.moyenne_difficulte:
            niveau = self._calculate_niveau_alerte(
                moyenne,
                self.config.moyenne_difficulte,  # attention threshold
                self.config.moyenne_difficulte - 2,  # critique threshold (2 points below)
                inversed=False
            )
            alertes.append(AlerteEtudiant(
                etudiant_id=etudiant_id,
                etudiant_nom=etudiant_nom,
                etudiant_prenom=etudiant_prenom,
                type_alerte=TypeAlerte.DIFFICULTE_ACADEMIQUE,
                niveau=niveau,
                message=f"Moyenne générale de {moyenne:.1f}/20 - En dessous du seuil de {self.config.moyenne_difficulte}",
                valeur_actuelle=moyenne,
                seuil=self.config.moyenne_difficulte,
                date_detection=date.today(),
                semestre=semestre,
                modules_concernes=modules_faibles,
            ))
        
        # Check attendance (taux_absence_attention / critique)
        if taux_absenteisme > self.config.taux_absence_attention:
            niveau = self._calculate_niveau_alerte(
                taux_absenteisme,
                self.config.taux_absence_attention,
                self.config.taux_absence_critique,
                inversed=True
            )
            alertes.append(AlerteEtudiant(
                etudiant_id=etudiant_id,
                etudiant_nom=etudiant_nom,
                etudiant_prenom=etudiant_prenom,
                type_alerte=TypeAlerte.ASSIDUITE,
                niveau=niveau,
                message=f"Taux d'absences non justifiées de {taux_absenteisme*100:.0f}%",
                valeur_actuelle=taux_absenteisme,
                seuil=self.config.taux_absence_attention,
                date_detection=date.today(),
                semestre=semestre,
            ))
        
        # Check progression (delta_moyenne_alerte)
        if progression < self.config.delta_moyenne_alerte:
            niveau = NiveauAlerte.ATTENTION if progression > self.config.delta_moyenne_alerte * 1.5 else NiveauAlerte.CRITIQUE
            alertes.append(AlerteEtudiant(
                etudiant_id=etudiant_id,
                etudiant_nom=etudiant_nom,
                etudiant_prenom=etudiant_prenom,
                type_alerte=TypeAlerte.PROGRESSION_NEGATIVE,
                niveau=niveau,
                message=f"Baisse de {abs(progression):.1f} points par rapport au semestre précédent",
                valeur_actuelle=progression,
                seuil=self.config.delta_moyenne_alerte,
                date_detection=date.today(),
                semestre=semestre,
            ))
        
        # Check dropout risk (score_decrochage_attention / critique)
        score_risque, _ = self._calculate_risk_score(moyenne, taux_absenteisme, "Autre", progression)
        if score_risque > self.config.score_decrochage_attention:
            niveau = NiveauAlerte.ATTENTION if score_risque < self.config.score_decrochage_critique else NiveauAlerte.CRITIQUE
            alertes.append(AlerteEtudiant(
                etudiant_id=etudiant_id,
                etudiant_nom=etudiant_nom,
                etudiant_prenom=etudiant_prenom,
                type_alerte=TypeAlerte.DECROCHAGE,
                niveau=niveau,
                message=f"Score de décrochage élevé ({score_risque:.2f}) - Cumul de difficultés",
                valeur_actuelle=score_risque,
                seuil=self.config.score_decrochage_attention,
                date_detection=date.today(),
                semestre=semestre,
            ))
        
        return alertes
    
    async def get_all_alertes(
        self,
        semestre: Optional[str] = None,
        niveau: Optional[NiveauAlerte] = None,
        type_alerte: Optional[TypeAlerte] = None,
        limit: int = 50,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[AlerteEtudiant]:
        """Get all alerts for the department by analyzing current students."""
        alertes = []
        
        if not await self.adapter.authenticate():
            logger.warning("ScoDoc not available, returning empty alerts")
            return []
        
        try:
            # Get current semesters
            semestres = await self.adapter.get_formsemestres_courants()
            if not semestres:
                logger.warning("No current semesters found")
                return []
            
            # Filter semesters
            semestres = self._filter_semestres(semestres, semestre, formation, modalite)
            
            if not semestres:
                logger.warning("No semesters matching filters found")
                return []
            
            # Process each semester
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                if not sem_id:
                    continue
                
                sem_name = f"S{sem.get('semestre_id', '?')}"
                
                # Get results for this semester
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                if not resultats or not isinstance(resultats, list):
                    continue
                
                # Get ALL assiduités for this semester (list, not count)
                # to calculate per-student absence hours
                assiduites_list = await self.adapter._api_get(
                    f"/api/assiduites/formsemestre/{sem_id}"
                )
                
                # Build per-student absence hours map (only count ABSENT, not PRESENT/RETARD)
                absences_by_student = {}  # etudid -> hours_non_justified
                if assiduites_list and isinstance(assiduites_list, list):
                    from datetime import datetime
                    for item in assiduites_list:
                        if item.get('etat') != 'ABSENT':
                            continue  # Skip PRESENT and RETARD
                        
                        etudid = str(item.get('etudid', ''))
                        if not etudid:
                            continue
                        
                        # Only count non-justified absences for alerts
                        if item.get('est_just'):
                            continue
                        
                        # Calculate duration
                        try:
                            date_debut_str = item.get('date_debut', '')
                            date_fin_str = item.get('date_fin', '')
                            if date_debut_str and date_fin_str:
                                date_debut = datetime.fromisoformat(date_debut_str.replace('Z', '+00:00'))
                                date_fin = datetime.fromisoformat(date_fin_str.replace('Z', '+00:00'))
                                duration = (date_fin - date_debut).total_seconds() / 3600
                            else:
                                duration = 2.0
                        except Exception:
                            duration = 2.0
                        
                        absences_by_student[etudid] = absences_by_student.get(etudid, 0) + duration
                
                nb_etudiants = len(resultats)
                
                # Process each student
                for etud_res in resultats:
                    if not isinstance(etud_res, dict):
                        continue
                    
                    etudid = str(etud_res.get("etudid", ""))
                    # ScoDoc returns 'nom_disp' for last name in results
                    nom = etud_res.get("nom_disp", "") or etud_res.get("nom", "")
                    prenom = etud_res.get("prenom", "")
                    
                    # Get average
                    moy = etud_res.get("moy_gen")
                    if not moy or moy == "~":
                        continue
                    
                    try:
                        moyenne = float(str(moy).replace(",", "."))
                    except (ValueError, TypeError):
                        continue
                    
                    # Get actual per-student non-justified absence hours
                    student_abs_hours = absences_by_student.get(etudid, 0)
                    # Calculate rate: hours absent / estimated 400h per semester
                    taux_abs = student_abs_hours / 400
                    
                    # Find weak modules (moyenne < 10)
                    modules_faibles = []
                    for key, value in etud_res.items():
                        if key.startswith("moy_res_") and value and value != "~":
                            try:
                                note = float(str(value).replace(",", "."))
                                if note < 10:
                                    # Extract module code if available
                                    modules_faibles.append(key.split("_")[2])
                            except (ValueError, TypeError):
                                pass
                    
                    # Generate alerts for this student
                    student_alertes = await self.generate_alertes_for_student(
                        etudiant_id=etudid,
                        etudiant_nom=nom,
                        etudiant_prenom=prenom,
                        moyenne=moyenne,
                        taux_absenteisme=taux_abs,
                        progression=0,  # Would need historical data
                        semestre=sem_name,
                        modules_faibles=modules_faibles[:5],  # Limit to 5 modules
                    )
                    alertes.extend(student_alertes)
            
            # Apply individual student filters (search)
            if search:
                s_norm = search.lower()
                alertes = [
                    a for a in alertes 
                    if s_norm in a.etudiant_nom.lower() or s_norm in a.etudiant_prenom.lower()
                ]
            
            # Apply filters
            if niveau:
                alertes = [a for a in alertes if a.niveau == niveau]
            if type_alerte:
                alertes = [a for a in alertes if a.type_alerte == type_alerte]
            
            # Sort by severity
            ordre_severite = {NiveauAlerte.CRITIQUE: 0, NiveauAlerte.ATTENTION: 1, NiveauAlerte.INFO: 2}
            alertes.sort(key=lambda a: ordre_severite.get(a.niveau, 99))
            
            return alertes[:limit]
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
            return []
    
    async def get_fiche_etudiant(self, etudiant_id: str) -> Optional[FicheEtudiantComplete]:
        """Get complete student profile with all metrics."""
        if not await self.adapter.authenticate():
            logger.error("Cannot fetch student profile: ScoDoc authentication failed")
            return None
        
        try:
            # Get student details
            etudiant = await self.get_etudiant_details(etudiant_id)
            if not etudiant:
                logger.warning(f"Student {etudiant_id} not found")
                return None
            
            # Get admission info
            admission = etudiant.get("admission", {}) or {}
            
            # Get student's semesters
            semestres = await self.get_etudiant_formsemestres(etudiant_id)
            
            # Get current semester (most recent)
            current_sem = semestres[0] if semestres else None
            current_sem_id = current_sem.get("formsemestre_id") if current_sem else None
            
            # Get bulletin for current semester
            bulletin = None
            if current_sem_id:
                bulletin = await self.get_etudiant_bulletin(etudiant_id, current_sem_id)
            
            # Get absences
            absences_data = await self.get_etudiant_absences(etudiant_id)
            counts = absences_data.get("counts", {}) if absences_data else {}
            absences_list = absences_data.get("absences", []) if absences_data else []
            
            # Calculate absence stats
            total_abs = counts.get("nbabs", 0)
            abs_just = counts.get("nbabs_just", 0)
            abs_non_just = counts.get("nbabs_non_just", 0)
            taux_abs = total_abs / 400 if total_abs else 0  # Assuming 400h/semester
            taux_just = abs_just / total_abs if total_abs > 0 else 0
            
            # Calculate absences by day of week
            abs_par_jour = {"lundi": 0, "mardi": 0, "mercredi": 0, "jeudi": 0, "vendredi": 0}
            abs_par_module = {}
            for absence in absences_list:
                if isinstance(absence, dict):
                    # Parse date to get day of week
                    date_str = absence.get("date", "")
                    if date_str:
                        try:
                            from datetime import datetime
                            d = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d")
                            jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
                            jour = jours[d.weekday()]
                            if jour in abs_par_jour:
                                abs_par_jour[jour] += 1
                        except:
                            pass
                    
                    # Count by module
                    module_id = str(absence.get("moduleimpl_id", "unknown"))
                    abs_par_module[module_id] = abs_par_module.get(module_id, 0) + 1
            
            statistiques_absences = StatistiquesAbsences(
                etudiant_id=etudiant_id,
                total_absences=total_abs,
                absences_justifiees=abs_just,
                absences_non_justifiees=abs_non_just,
                taux_absenteisme=taux_abs,
                taux_justification=taux_just,
                absences_par_module=abs_par_module,
                absences_par_jour_semaine=abs_par_jour,
                absences_par_creneau={"matin": total_abs // 2, "apres_midi": total_abs - total_abs // 2},
                tendance="stable",
            )
            
            # Extract grades from bulletin
            notes_modules = []
            moyenne_generale = 0.0
            rang = 0
            ects_valides = 0
            ects_total = 30
            effectif_promo = 120  # Default
            
            if bulletin:
                sem_info = bulletin.get("semestre", {})
                
                # ScoDoc returns notes as {value, min, max, moy} and rang as {value, total}
                notes_data = sem_info.get("notes", {})
                rang_data = sem_info.get("rang", {})
                
                if isinstance(notes_data, dict):
                    try:
                        moyenne_generale = float(notes_data.get("value", 0) or 0)
                    except (ValueError, TypeError):
                        moyenne_generale = 0.0
                
                if isinstance(rang_data, dict):
                    try:
                        rang = int(rang_data.get("value", 0) or 0)
                        effectif_promo = int(rang_data.get("total", 0) or 0) or 120
                    except (ValueError, TypeError):
                        rang = 0
                
                # ECTS from decision_ue or elsewhere
                decision_ue = sem_info.get("decision_ue", {})
                if isinstance(decision_ue, dict):
                    ects_valides = sum(
                        ue.get("ects", 0) or 0 
                        for ue in decision_ue.values() 
                        if isinstance(ue, dict) and ue.get("code") in ("ADM", "CMP")
                    )
                
                # Extract module grades from ressources and SAEs
                ressources = bulletin.get("ressources", {})
                saes = bulletin.get("saes", {})
                
                for code, data in {**ressources, **saes}.items():
                    if isinstance(data, dict):
                        titre = data.get("titre", "")
                        moy_data = data.get("moyenne", {})
                        moy_val = None
                        
                        # Try to get moyenne from the moyenne field
                        if isinstance(moy_data, dict) and moy_data.get("value"):
                            try:
                                moy_val = float(moy_data.get("value"))
                            except (ValueError, TypeError):
                                pass
                        
                        # If no moyenne, calculate from evaluations
                        if moy_val is None:
                            evaluations = data.get("evaluations", [])
                            if evaluations:
                                notes = []
                                for ev in evaluations:
                                    if isinstance(ev, dict):
                                        note_data = ev.get("note", {})
                                        if isinstance(note_data, dict):
                                            note_val = note_data.get("value")
                                            if note_val is not None:
                                                try:
                                                    notes.append(float(note_val))
                                                except (ValueError, TypeError):
                                                    pass
                                if notes:
                                    moy_val = sum(notes) / len(notes)
                        
                        if moy_val is not None:
                            notes_modules.append({
                                "code": code,
                                "nom": titre[:50] if titre else code,
                                "moyenne": round(moy_val, 2),
                                "rang": 0,
                            })
            
            # Build historique from all semesters
            historique_semestres = []
            historique_moyennes = []
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                if sem_id:
                    sem_bulletin = await self.get_etudiant_bulletin(etudiant_id, sem_id)
                    if sem_bulletin:
                        sem_data = sem_bulletin.get("semestre", {})
                        notes_data = sem_data.get("notes", {})
                        rang_data = sem_data.get("rang", {})
                        
                        moy_val = None
                        rang_val = 0
                        
                        if isinstance(notes_data, dict):
                            try:
                                moy_val = float(notes_data.get("value", 0) or 0)
                            except (ValueError, TypeError):
                                pass
                        
                        if isinstance(rang_data, dict):
                            try:
                                rang_val = int(rang_data.get("value", 0) or 0)
                            except (ValueError, TypeError):
                                pass
                        
                        if moy_val is not None:
                            sem_code = f"S{sem.get('semestre_id', '?')}"
                            historique_semestres.append({
                                "semestre": sem_code,
                                "annee": sem.get("annee_scolaire", ""),
                                "moyenne": moy_val,
                                "rang": rang_val,
                                "decision": sem_data.get("decision", {}).get("code", "En cours") if isinstance(sem_data.get("decision"), dict) else "En cours",
                                "ects": 30,  # Default ECTS per semester
                            })
                            historique_moyennes.append({
                                "semestre": sem_code,
                                "moyenne": moy_val,
                                "rang": rang_val,
                            })
            
            # Calculate progression
            progression = ProgressionEtudiant(
                etudiant_id=etudiant_id,
                etudiant_nom=etudiant.get("nom", ""),
                etudiant_prenom=etudiant.get("prenom", ""),
                historique_moyennes=historique_moyennes,
                tendance_globale="stable",
            )
            
            # Calculate risk score
            type_bac = admission.get("bac", "Autre")
            score_global, facteurs = self._calculate_risk_score(
                moyenne_generale, taux_abs, type_bac
            )
            
            # Generate recommendations based on score
            recommandations = []
            if score_global > 0.5:
                recommandations.append("Proposer un accompagnement personnalisé")
            if facteurs.get("notes", 0) > 0.5:
                recommandations.append("Organiser des séances de soutien")
            if facteurs.get("assiduite", 0) > 0.3:
                recommandations.append("Convoquer pour discuter de l'assiduité")
            if score_global > 0.7:
                recommandations.append("Envisager un contrat pédagogique")
            
            score_risque = ScoreRisque(
                etudiant_id=etudiant_id,
                score_global=score_global,
                facteurs=facteurs,
                probabilite_validation=max(0, 1 - score_global),
                recommandations=recommandations,
            )
            
            # Generate alerts for this student
            alertes = await self.generate_alertes_for_student(
                etudiant_id=etudiant_id,
                etudiant_nom=etudiant.get("nom", ""),
                etudiant_prenom=etudiant.get("prenom", ""),
                moyenne=moyenne_generale,
                taux_absenteisme=taux_abs,
                progression=0,
                semestre=f"S{current_sem.get('semestre_id', '?')}" if current_sem else "S1",
            )
            
            # Determine max alert level
            niveau_max = NiveauAlerte.INFO
            if alertes:
                if any(a.niveau == NiveauAlerte.CRITIQUE for a in alertes):
                    niveau_max = NiveauAlerte.CRITIQUE
                elif any(a.niveau == NiveauAlerte.ATTENTION for a in alertes):
                    niveau_max = NiveauAlerte.ATTENTION
            
            # Use effectif from bulletin if available, otherwise fetch
            if effectif_promo == 120 and current_sem_id:
                sem_etudiants = await self.adapter.get_formsemestre_etudiants(current_sem_id)
                if sem_etudiants:
                    effectif_promo = len(sem_etudiants)
            
            # Build profile
            profil = ProfilEtudiant(
                id=etudiant_id,
                nom=etudiant.get("nom", ""),
                prenom=etudiant.get("prenom", ""),
                email=etudiant.get("email", ""),
                formation=current_sem.get("titre", "BUT RT").split(" semestre")[0] if current_sem else "BUT RT",
                semestre_actuel=f"S{current_sem.get('semestre_id', '?')}" if current_sem else "S1",
                groupe=etudiant.get("groupes", [{}])[0].get("group_name", "G1") if etudiant.get("groupes") else "G1",
                type_bac=type_bac,
                mention_bac=admission.get("mention", ""),
                annee_bac=admission.get("annee_bac", 2024),
                lycee_origine=f"{admission.get('lycee', '')} - {admission.get('ville_lycee', '')}".strip(" -"),
                boursier=etudiant.get("boursier") or False,
                moyenne_actuelle=moyenne_generale,
                rang_promo=rang,
                rang_groupe=0,
                effectif_promo=effectif_promo,
                ects_valides=ects_valides,
                ects_total=ects_total,
                alertes=alertes,
                niveau_alerte_max=niveau_max,
                statistiques_absences=statistiques_absences,
                progression=progression,
                score_risque=score_risque,
                notes_modules=notes_modules,
            )
            
            # Build personalized recommendations
            recommandations_perso = []
            if moyenne_generale < 10:
                recommandations_perso.append("🎯 Priorité : Renforcer les bases dans les modules en difficulté")
            if taux_abs > 0.1:
                recommandations_perso.append("📅 Améliorer l'assiduité aux cours")
            if score_global > 0.5:
                recommandations_perso.append("👥 Envisager un tutorat avec un étudiant avancé")
            if len(notes_modules) > 0:
                faibles = [m for m in notes_modules if m.get("moyenne", 0) < 10]
                if faibles:
                    codes = ", ".join(m.get("code", "") for m in faibles[:3])
                    recommandations_perso.append(f"📚 Soutien recommandé pour : {codes}")
            
            return FicheEtudiantComplete(
                profil=profil,
                historique_semestres=historique_semestres,
                graphique_progression=[
                    {"label": h["semestre"], "moyenne": h["moyenne"], "moyenne_promo": 11.5}
                    for h in historique_moyennes
                ],
                comparaison_promo={
                    "percentile": int((rang / effectif_promo) * 100) if effectif_promo > 0 else 50,
                    "ecart_moyenne": round(moyenne_generale - 11.5, 1),  # vs promo average
                    "position": "Quartile inférieur" if rang > effectif_promo * 0.75 else "Quartile supérieur" if rang < effectif_promo * 0.25 else "Médian",
                },
                recommandations_personnalisees=recommandations_perso if recommandations_perso else ["✅ Continuez sur cette lancée !"],
            )
            
        except Exception as e:
            logger.error(f"Error building student profile: {e}", exc_info=True)
            return None
    
    async def get_statistiques_alertes(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> dict:
        """Get global alert statistics."""
        alertes = await self.get_all_alertes(
            semestre=semestre, 
            formation=formation, 
            modalite=modalite, 
            limit=1000
        )
        
        par_niveau = {"critique": 0, "attention": 0, "info": 0}
        par_type = {}
        
        for a in alertes:
            # Count by level
            niveau_key = a.niveau.value if hasattr(a.niveau, 'value') else str(a.niveau)
            par_niveau[niveau_key] = par_niveau.get(niveau_key, 0) + 1
            
            # Count by type
            type_key = a.type_alerte.value if hasattr(a.type_alerte, 'value') else str(a.type_alerte)
            par_type[type_key] = par_type.get(type_key, 0) + 1
        
        return {
            "total_alertes": len(alertes),
            "par_niveau": par_niveau,
            "par_type": par_type,
            "evolution_semaine": [],  # Would need historical tracking
        }

    async def get_all_students_with_grades(self) -> list[dict]:
        """
        Get all students from current semesters with their grades.
        Returns a list of dicts with student info and moyenne.
        """
        if not await self.adapter.authenticate():
            logger.error("Cannot fetch students: ScoDoc authentication failed")
            return []
        
        try:
            # Get current semesters
            semesters = await self.adapter.get_formsemestres_courants()
            if not semesters:
                logger.warning("No current semesters found")
                return []
            
            all_students = []
            seen_etudids = set()
            
            for sem in semesters:
                sem_id = sem.get("formsemestre_id")
                if not sem_id:
                    continue
                
                # Get results for this semester (list of students with grades)
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                if not resultats:
                    continue
                
                # Results is a list of student records
                if not isinstance(resultats, list):
                    logger.warning(f"Unexpected resultats format for sem {sem_id}")
                    continue
                
                for etud_info in resultats:
                    etudid = str(etud_info.get("etudid", ""))
                    if not etudid or etudid in seen_etudids:
                        continue
                    seen_etudids.add(etudid)
                    
                    # Get moyenne (can be float directly or None)
                    moy_gen = etud_info.get("moy_gen")
                    moyenne = None
                    if moy_gen is not None:
                        try:
                            moyenne = float(moy_gen)
                        except (ValueError, TypeError):
                            pass
                    
                    # Get rang (usually int or string)
                    rang_data = etud_info.get("rang")
                    rang = None
                    if rang_data is not None:
                        try:
                            rang = int(rang_data)
                        except (ValueError, TypeError):
                            pass
                    
                    # Get name (nom_disp or nom_short)
                    nom = etud_info.get("nom_disp") or etud_info.get("nom_short") or ""
                    # Split nom_disp if it contains both nom and prenom
                    prenom = etud_info.get("prenom", "")
                    
                    # Build student record
                    student = {
                        "etudid": etudid,
                        "nom": nom.upper() if nom else "",
                        "prenom": prenom.capitalize() if prenom else "",
                        "civilite": etud_info.get("civilite_str", ""),
                        "moyenne": moyenne,
                        "rang": rang,
                        "formsemestre_id": sem_id,
                        "semestre_titre": sem.get("titre", ""),
                        "semestre_idx": sem.get("semestre_id", 1),
                    }
                    all_students.append(student)
            
            logger.info(f"Fetched {len(all_students)} students from {len(semesters)} semesters")
            return all_students
            
        except Exception as e:
            logger.error(f"Error fetching all students: {e}")
            return []
    
    async def get_etudiants_en_difficulte(self, seuil_moyenne: float = 8.0) -> list[ProfilEtudiant]:
        """Get students with average below threshold."""
        students = await self.get_all_students_with_grades()
        
        result = []
        for s in students:
            moyenne = s.get("moyenne")
            if moyenne is not None and moyenne < seuil_moyenne:
                niveau = "critique" if moyenne < 6 else "attention"
                profil = ProfilEtudiant(
                    id=str(s["etudid"]),
                    nom=s.get("nom", ""),
                    prenom=s.get("prenom", ""),
                    formation=s.get("semestre_titre", "BUT"),
                    semestre_actuel=f"S{s.get('semestre_idx', '?')}",
                    moyenne_actuelle=moyenne,
                    rang_promo=s.get("rang"),
                    niveau_alerte_max=niveau,
                )
                result.append(profil)
        
        # Sort by moyenne ascending (worst first)
        result.sort(key=lambda x: x.moyenne_actuelle or 20)
        return result
    
    async def get_etudiants_absents(self, seuil_absences: float = 0.15) -> list[ProfilEtudiant]:
        """Get students with high absenteeism rate.
        
        IMPORTANT: The ScoDoc /api/assiduites/.../count endpoint does NOT support
        filtering by 'etat' parameter. It always returns totals for ALL states.
        
        Therefore, we must:
        1. Fetch the detailed assiduités list for each formsemestre
        2. Filter client-side by etat == 'ABSENT'
        3. Group by student and calculate hours
        
        ScoDoc assiduités states: ABSENT, PRESENT, RETARD
        """
        if not await self.adapter.authenticate():
            return []
        
        try:
            from datetime import datetime
            
            # Get current semesters
            semesters = await self.adapter.get_formsemestres_courants()
            if not semesters:
                return []
            
            result = []
            seen_etudids = set()
            
            for sem in semesters:
                sem_id = sem.get("formsemestre_id")
                if not sem_id:
                    continue
                
                # Fetch ALL assiduités for this semester (list, not count)
                assiduites_list = await self.adapter._api_get(
                    f"/api/assiduites/formsemestre/{sem_id}"
                )
                
                if not assiduites_list or not isinstance(assiduites_list, list):
                    continue
                
                # Filter to only ABSENT records and group by student
                # Calculate hours for each student
                absences_by_student = {}  # etudid -> {"hours": float, "hours_just": float, "hours_non_just": float}
                
                for item in assiduites_list:
                    if item.get('etat') != 'ABSENT':
                        continue  # Skip PRESENT and RETARD
                    
                    etudid = str(item.get('etudid', ''))
                    if not etudid:
                        continue
                    
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
                    
                    if etudid not in absences_by_student:
                        absences_by_student[etudid] = {"hours": 0, "hours_just": 0, "hours_non_just": 0}
                    
                    absences_by_student[etudid]["hours"] += duration_hours
                    if item.get('est_just'):
                        absences_by_student[etudid]["hours_just"] += duration_hours
                    else:
                        absences_by_student[etudid]["hours_non_just"] += duration_hours
                
                # Get student results to match names
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                if not resultats or not isinstance(resultats, list):
                    continue
                
                # Build student lookup
                student_info = {str(e.get("etudid")): e for e in resultats}
                
                # Filter students exceeding threshold (default: 5+ hours non-justified)
                threshold_hours = 5.0  # Minimum non-justified absence hours to flag
                
                for etudid, abs_data in absences_by_student.items():
                    if etudid in seen_etudids:
                        continue
                    seen_etudids.add(etudid)
                    
                    hours_non_just = abs_data["hours_non_just"]
                    if hours_non_just < threshold_hours:
                        continue
                    
                    # Determine alert level
                    niveau = "critique" if hours_non_just >= 20 else "attention"
                    
                    # Get student info
                    etud = student_info.get(etudid, {})
                    nom = etud.get("nom_disp") or etud.get("nom_short") or ""
                    prenom = etud.get("prenom", "")
                    moyenne = None
                    try:
                        moyenne = float(etud.get("moy_gen")) if etud.get("moy_gen") is not None else None
                    except (ValueError, TypeError):
                        pass
                    
                    profil = ProfilEtudiant(
                        id=etudid,
                        nom=nom.upper() if nom else "",
                        prenom=prenom.capitalize() if prenom else "",
                        formation=sem.get("titre", "BUT"),
                        semestre_actuel=f"S{sem.get('semestre_id', '?')}",
                        moyenne_actuelle=moyenne,
                        rang_promo=etud.get("rang"),
                        niveau_alerte_max=niveau,
                    )
                    result.append(profil)
            
            logger.info(f"Found {len(result)} students with high absenteeism")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching absent students: {e}")
            return []
    
    async def get_etudiants_risque_decrochage(self, seuil_score: float = 0.6) -> list[ProfilEtudiant]:
        """Get students at risk of dropping out (low grades + possible absences)."""
        students = await self.get_all_students_with_grades()
        
        result = []
        for s in students:
            moyenne = s.get("moyenne")
            if moyenne is None:
                continue
            
            # Simple risk calculation based on average
            # In a full implementation, this would include absences, progression, etc.
            risk_score = 0.0
            
            if moyenne < 6:
                risk_score = 0.9
            elif moyenne < 8:
                risk_score = 0.7
            elif moyenne < 10:
                risk_score = 0.5
            else:
                risk_score = 0.2
            
            if risk_score >= seuil_score:
                niveau = "critique" if risk_score >= 0.8 else "attention"
                profil = ProfilEtudiant(
                    id=str(s["etudid"]),
                    nom=s.get("nom", ""),
                    prenom=s.get("prenom", ""),
                    formation=s.get("semestre_titre", "BUT"),
                    semestre_actuel=f"S{s.get('semestre_idx', '?')}",
                    moyenne_actuelle=moyenne,
                    rang_promo=s.get("rang"),
                    niveau_alerte_max=niveau,
                )
                result.append(profil)
        
        # Sort by moyenne ascending (highest risk first)
        result.sort(key=lambda x: x.moyenne_actuelle or 20)
        return result
    
    async def get_etudiants_felicitations(self, top_percent: int = 10) -> list[ProfilEtudiant]:
        """Get top X% of students."""
        students = await self.get_all_students_with_grades()
        
        # Filter students with valid grades
        with_grades = [s for s in students if s.get("moyenne") is not None]
        
        if not with_grades:
            return []
        
        # Sort by moyenne descending
        with_grades.sort(key=lambda x: x.get("moyenne", 0), reverse=True)
        
        # Take top X%
        cutoff = max(1, len(with_grades) * top_percent // 100)
        top_students = with_grades[:cutoff]
        
        result = []
        for s in top_students:
            profil = ProfilEtudiant(
                id=str(s["etudid"]),
                nom=s.get("nom", ""),
                prenom=s.get("prenom", ""),
                formation=s.get("semestre_titre", "BUT"),
                semestre_actuel=f"S{s.get('semestre_idx', '?')}",
                moyenne_actuelle=s.get("moyenne"),
                rang_promo=s.get("rang"),
                niveau_alerte_max="info",  # Félicitations = positive
            )
            result.append(profil)
        
        return result
