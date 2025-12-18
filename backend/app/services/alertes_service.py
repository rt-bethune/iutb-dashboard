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
        
        result = await self.adapter._api_get(
            f"/api/etudiant/etudid/{etudiant_id}/formsemestres"
        )
        return result if result else []
    
    async def get_etudiant_bulletin(self, etudiant_id: str, formsemestre_id: int) -> Optional[dict]:
        """Get student's grade bulletin for a semester."""
        if not await self.adapter.authenticate():
            return None
        
        return await self.adapter._api_get(
            f"/api/etudiant/etudid/{etudiant_id}/formsemestre/{formsemestre_id}/bulletin"
        )
    
    async def get_etudiant_absences(self, etudiant_id: str) -> Optional[dict]:
        """Get student's absence counts using the assiduites_count endpoint.
        
        Uses /api/assiduites/etudid/{id}/count with split=true to get counts by state.
        """
        if not await self.adapter.authenticate():
            return None
        
        try:
            # Use the correct assiduites_count endpoint with split to get breakdown
            count_data = await self.adapter._api_get(
                f"/api/assiduites/etudid/{etudiant_id}/count",
                params={"metric": "heure", "split": "true"}
            )
            
            if count_data is None:
                return {
                    "absences": [],
                    "counts": {"nbabs": 0, "nbabs_just": 0, "nbabs_non_just": 0}
                }
            
            # Parse the count response - it returns counts split by state
            # Example: {"absent": {"heure": 10, "heure_just": 2, "heure_non_just": 8}, ...}
            total_abs = 0
            abs_just = 0
            abs_non_just = 0
            
            if isinstance(count_data, dict):
                # Handle split response format
                absent_data = count_data.get("absent", {})
                if isinstance(absent_data, dict):
                    total_abs = absent_data.get("heure", 0) or 0
                    abs_just = absent_data.get("heure_just", 0) or 0
                    abs_non_just = absent_data.get("heure_non_just", 0) or 0
                else:
                    # Fallback for simple format
                    total_abs = count_data.get("heure", 0) or 0
                    abs_just = count_data.get("heure_just", 0) or 0
                    abs_non_just = count_data.get("heure_non_just", 0) or 0
                
                # If we don't have the breakdown, estimate
                if total_abs > 0 and abs_just == 0 and abs_non_just == 0:
                    abs_non_just = total_abs
            
            return {
                "absences": [],  # We don't have the detail list from count endpoint
                "counts": {"nbabs": total_abs, "nbabs_just": abs_just, "nbabs_non_just": abs_non_just}
            }
            
        except Exception as e:
            logger.debug(f"Assiduites count endpoint error for student {etudiant_id}: {e}")
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
            
            # Process each semester
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                sem_name = f"S{sem.get('semestre_id', '?')}"
                
                # Filter by semestre if specified
                if semestre and sem_name != semestre:
                    continue
                
                # Get results for this semester
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                if not resultats or not isinstance(resultats, list):
                    continue
                
                # Get absences for the semester
                assiduites = await self.adapter.get_formsemestre_assiduites_count(sem_id)
                total_absences_sem = assiduites.get("heure", 0) if assiduites else 0
                nb_etudiants = len(resultats)
                avg_absences_per_student = total_absences_sem / nb_etudiants if nb_etudiants > 0 else 0
                
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
                    
                    # Estimate individual absence rate (simplified - would need per-student data)
                    # For now, use department average as placeholder
                    taux_abs_estime = avg_absences_per_student / 400  # Assuming 400h/semester
                    
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
                        taux_absenteisme=taux_abs_estime,
                        progression=0,  # Would need historical data
                        semestre=sem_name,
                        modules_faibles=modules_faibles[:5],  # Limit to 5 modules
                    )
                    alertes.extend(student_alertes)
            
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
    
    async def get_statistiques_alertes(self, semestre: Optional[str] = None) -> dict:
        """Get global alert statistics."""
        alertes = await self.get_all_alertes(semestre=semestre, limit=500)
        
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
        
        Note: The assiduites endpoint may not be available on all ScoDoc instances.
        This method attempts to use the formsemestre-level absence count endpoint instead.
        """
        if not await self.adapter.authenticate():
            return []
        
        try:
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
                
                # Try to get absences count for the whole semester
                # This endpoint returns absence counts per student for the semester
                abs_count = await self.adapter._api_get(
                    f"/api/assiduites/formsemestre/{sem_id}/count",
                    params={"metric": "heure"}
                )
                
                if not abs_count or not isinstance(abs_count, dict):
                    continue
                
                # abs_count should be a dict with etudid -> {nbabs, nbabs_just, ...}
                # or it might be the total for the semester
                # Let's also get students from this semester
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                if not resultats or not isinstance(resultats, list):
                    continue
                
                for etud in resultats:
                    etudid = str(etud.get("etudid", ""))
                    if not etudid or etudid in seen_etudids:
                        continue
                    seen_etudids.add(etudid)
                    
                    # Check if this student has absence data
                    etud_abs = abs_count.get(etudid) or abs_count.get(int(etudid)) if isinstance(abs_count, dict) else None
                    
                    # If abs_count is not per-student, skip this approach
                    if not etud_abs:
                        continue
                    
                    nbabs = etud_abs.get("nbabs", 0) if isinstance(etud_abs, dict) else 0
                    nbabs_just = etud_abs.get("nbabs_just", 0) if isinstance(etud_abs, dict) else 0
                    nbabs_non_just = nbabs - nbabs_just
                    
                    # Check if exceeds threshold (5+ non-justified absences)
                    if nbabs_non_just >= 5:
                        niveau = "critique" if nbabs_non_just >= 10 else "attention"
                        
                        # Get name from resultats
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
            
            # If no results from formsemestre endpoint, log a warning
            if not result:
                logger.info("No absence data available - assiduites endpoint may not be enabled")
            
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
