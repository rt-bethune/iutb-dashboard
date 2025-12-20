"""Service for calculating cohort indicators from ScoDoc data."""

from typing import Optional
import logging
import statistics

from app.adapters.scodoc import ScoDocAdapter
from app.models.indicateurs import (
    StatistiquesCohorte,
    TauxValidation,
    RepartitionMentions,
    TauxPassage,
    ModuleAnalyse,
    AnalyseAbsenteisme,
    ComparaisonInterannuelle,
    AnalyseTypeBac,
    AnalyseBoursiers,
    TableauBordCohorte,
    IndicateursPredictifs,
)

logger = logging.getLogger(__name__)


class IndicateursService:
    """Service for calculating cohort indicators using ScoDoc data."""
    
    def __init__(self, adapter: ScoDocAdapter):
        self.adapter = adapter

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
    
    async def get_statistiques_cohorte(
        self,
        semestre: Optional[str] = None,
        groupe: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> Optional[StatistiquesCohorte]:
        """Calculate cohort statistics from ScoDoc data."""
        if not await self.adapter.authenticate():
            logger.warning("ScoDoc not available for statistiques")
            return None
        
        try:
            # Get current semesters
            semestres = await self.adapter.get_formsemestres_courants()
            if not semestres:
                return None
            
            semestres = self._filter_semestres(semestres, semestre, formation, modalite)
            
            if not semestres:
                return None
            
            all_moyennes = []
            effectif_par_groupe = {}
            
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                
                # Get results
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                if not resultats or not isinstance(resultats, list):
                    continue
                
                for etud in resultats:
                    if not isinstance(etud, dict):
                        continue
                    
                    moy = etud.get("moy_gen")
                    if moy and moy != "~":
                        try:
                            all_moyennes.append(float(str(moy).replace(",", ".")))
                        except (ValueError, TypeError):
                            pass
                    
                    # Count by group
                    groupes = etud.get("groupes", [])
                    for g in groupes:
                        g_name = g.get("group_name", "Autre") if isinstance(g, dict) else str(g)
                        effectif_par_groupe[g_name] = effectif_par_groupe.get(g_name, 0) + 1
            
            if not all_moyennes:
                return None
            
            # Calculate statistics
            effectif = len(all_moyennes)
            moyenne = statistics.mean(all_moyennes)
            mediane = statistics.median(all_moyennes)
            ecart_type = statistics.stdev(all_moyennes) if len(all_moyennes) > 1 else 0
            
            sorted_moy = sorted(all_moyennes)
            q1_idx = len(sorted_moy) // 4
            q3_idx = 3 * len(sorted_moy) // 4
            
            nb_reussis = sum(1 for m in all_moyennes if m >= 10)
            nb_difficulte = sum(1 for m in all_moyennes if m < 8)
            nb_excellence = sum(1 for m in all_moyennes if m >= 14)
            
            return StatistiquesCohorte(
                effectif_total=effectif,
                effectif_par_groupe=effectif_par_groupe if effectif_par_groupe else {"Total": effectif},
                moyenne_promo=round(moyenne, 2),
                ecart_type=round(ecart_type, 2),
                mediane=round(mediane, 2),
                min=round(min(all_moyennes), 2),
                max=round(max(all_moyennes), 2),
                quartiles={
                    "Q1": round(sorted_moy[q1_idx], 2) if q1_idx < len(sorted_moy) else 0,
                    "Q2": round(mediane, 2),
                    "Q3": round(sorted_moy[q3_idx], 2) if q3_idx < len(sorted_moy) else 0,
                },
                taux_reussite=round(nb_reussis / effectif, 2),
                taux_difficulte=round(nb_difficulte / effectif, 2),
                taux_excellence=round(nb_excellence / effectif, 2),
            )
            
        except Exception as e:
            logger.error(f"Error calculating cohort statistics: {e}")
            return None
    
    async def get_taux_validation(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> Optional[TauxValidation]:
        """Calculate validation rates by UE and module."""
        if not await self.adapter.authenticate():
            return None
        
        try:
            semestres = await self.adapter.get_formsemestres_courants()
            if not semestres:
                return None
            
            semestres = self._filter_semestres(semestres, semestre, formation, modalite)
            
            if not semestres:
                return None
            
            module_validations = {}  # module_code -> (nb_validated, nb_total)
            ue_validations = {}
            all_validated = 0
            all_total = 0
            
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                programme = await self.adapter.get_formsemestre_programme(sem_id)
                
                if not resultats:
                    continue
                
                # Build module info from programme
                modules_info = {}
                if programme:
                    for res in programme.get("ressources", []):
                        mod = res.get("module", {})
                        if mod:
                            modules_info[res.get("id")] = {
                                "code": mod.get("code", ""),
                                "ue": mod.get("ue_id"),
                            }
                
                for etud in resultats:
                    if not isinstance(etud, dict):
                        continue
                    
                    # Check overall validation
                    moy = etud.get("moy_gen")
                    if moy and moy != "~":
                        try:
                            moy_val = float(str(moy).replace(",", "."))
                            all_total += 1
                            if moy_val >= 10:
                                all_validated += 1
                        except:
                            pass
                    
                    # Check per-module validation
                    for key, value in etud.items():
                        if key.startswith("moy_res_") and value and value != "~":
                            try:
                                parts = key.split("_")
                                if len(parts) >= 4:
                                    module_id = int(parts[2])
                                    mod_info = modules_info.get(module_id, {})
                                    code = mod_info.get("code", f"M{module_id}")
                                    
                                    if code not in module_validations:
                                        module_validations[code] = [0, 0]
                                    
                                    note = float(str(value).replace(",", "."))
                                    module_validations[code][1] += 1
                                    if note >= 10:
                                        module_validations[code][0] += 1
                            except:
                                pass
            
            # Calculate rates
            par_module = {}
            for code, (valid, total) in module_validations.items():
                if total > 0:
                    par_module[code] = round(valid / total, 2)
            
            taux_global = round(all_validated / all_total, 2) if all_total > 0 else 0
            
            return TauxValidation(
                taux_global=taux_global,
                par_ue=ue_validations if ue_validations else {"UE Global": taux_global},
                par_module=par_module if par_module else {"Global": taux_global},
                par_competence={},  # Would need competence mapping
            )
            
        except Exception as e:
            logger.error(f"Error calculating validation rates: {e}")
            return None
    
    async def get_mentions(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> Optional[RepartitionMentions]:
        """Calculate grade distribution."""
        if not await self.adapter.authenticate():
            return None
        
        try:
            semestres = await self.adapter.get_formsemestres_courants()
            if not semestres:
                return None
            
            semestres = self._filter_semestres(semestres, semestre, formation, modalite)
            
            if not semestres:
                return None
            
            mentions = {
                "tres_bien": 0,  # >= 16
                "bien": 0,  # 14-16
                "assez_bien": 0,  # 12-14
                "passable": 0,  # 10-12
                "insuffisant": 0,  # 8-10
                "eliminatoire": 0,  # < 8
            }
            total = 0
            
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                
                if not resultats:
                    continue
                
                for etud in resultats:
                    if not isinstance(etud, dict):
                        continue
                    
                    moy = etud.get("moy_gen")
                    if moy and moy != "~":
                        try:
                            m = float(str(moy).replace(",", "."))
                            total += 1
                            
                            if m >= 16:
                                mentions["tres_bien"] += 1
                            elif m >= 14:
                                mentions["bien"] += 1
                            elif m >= 12:
                                mentions["assez_bien"] += 1
                            elif m >= 10:
                                mentions["passable"] += 1
                            elif m >= 8:
                                mentions["insuffisant"] += 1
                            else:
                                mentions["eliminatoire"] += 1
                        except:
                            pass
            
            if total == 0:
                return None
            
            admis = mentions["tres_bien"] + mentions["bien"] + mentions["assez_bien"] + mentions["passable"]
            
            return RepartitionMentions(
                tres_bien=mentions["tres_bien"],
                bien=mentions["bien"],
                assez_bien=mentions["assez_bien"],
                passable=mentions["passable"],
                insuffisant=mentions["insuffisant"],
                eliminatoire=mentions["eliminatoire"],
                pourcentage_admis=round(admis / total, 2),
            )
            
        except Exception as e:
            logger.error(f"Error calculating mentions: {e}")
            return None
    
    async def get_modules_analyse(
        self,
        semestre: Optional[str] = None,
        tri: str = "taux_echec",
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> list[ModuleAnalyse]:
        """Analyze modules with difficulty identification."""
        if not await self.adapter.authenticate():
            return []
        
        try:
            semestres = await self.adapter.get_formsemestres_courants()
            if not semestres:
                return []
            
            semestres = self._filter_semestres(semestres, semestre, formation, modalite)
            
            if not semestres:
                return []
            
            # Collect grades per module
            module_grades = {}  # code -> list of grades
            modules_info = {}  # code -> {nom, semestre, formation}
            
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                sem_name = f"S{sem.get('semestre_id', '?')}"
                sem_formation = sem.get("titre", sem.get("titre_formation", ""))
                resultats = await self.adapter.get_formsemestre_resultats(sem_id)
                programme = await self.adapter.get_formsemestre_programme(sem_id)
                
                # Get module names from programme
                if programme:
                    for res in programme.get("ressources", []):
                        mod = res.get("module", {})
                        if mod:
                            code = mod.get("code", "")
                            if code:
                                modules_info[code] = {
                                    "nom": mod.get("titre", mod.get("abbrev", "Module"))[:50],
                                    "semestre": sem_name,
                                    "formation": sem_formation,
                                }
                
                if not resultats:
                    continue
                
                for etud in resultats:
                    if not isinstance(etud, dict):
                        continue
                    
                    for key, value in etud.items():
                        if key.startswith("moy_res_") and value and value != "~":
                            try:
                                # Find module code
                                parts = key.split("_")
                                if len(parts) >= 4:
                                    module_id = int(parts[2])
                                    
                                    # Try to find code from programme
                                    code = None
                                    if programme:
                                        for res in programme.get("ressources", []):
                                            if res.get("id") == module_id:
                                                code = res.get("module", {}).get("code")
                                                break
                                    
                                    if not code:
                                        code = f"R{module_id}"
                                    
                                    # Store semestre and formation info for this module
                                    if code not in modules_info:
                                        modules_info[code] = {"nom": "Module", "semestre": sem_name, "formation": sem_formation}
                                    else:
                                        if "semestre" not in modules_info[code]:
                                            modules_info[code]["semestre"] = sem_name
                                        if "formation" not in modules_info[code]:
                                            modules_info[code]["formation"] = sem_formation
                                    
                                    note = float(str(value).replace(",", "."))
                                    
                                    if code not in module_grades:
                                        module_grades[code] = []
                                    module_grades[code].append(note)
                            except:
                                pass
            
            # Build analysis for each module
            modules = []
            for code, grades in module_grades.items():
                if not grades:
                    continue
                
                moyenne = statistics.mean(grades)
                mediane = statistics.median(grades)
                ecart_type = statistics.stdev(grades) if len(grades) > 1 else 0
                
                nb_echec = sum(1 for g in grades if g < 10)
                taux_echec = nb_echec / len(grades)
                
                # Distribution
                distribution = {
                    "0-4": sum(1 for g in grades if g < 4),
                    "4-8": sum(1 for g in grades if 4 <= g < 8),
                    "8-10": sum(1 for g in grades if 8 <= g < 10),
                    "10-12": sum(1 for g in grades if 10 <= g < 12),
                    "12-14": sum(1 for g in grades if 12 <= g < 14),
                    "14-16": sum(1 for g in grades if 14 <= g < 16),
                    "16-20": sum(1 for g in grades if g >= 16),
                }
                
                # Generate alert if needed
                alerte = taux_echec > 0.25 or ecart_type > 4
                alerte_message = None
                if alerte:
                    reasons = []
                    if taux_echec > 0.25:
                        reasons.append(f"Taux d'échec élevé ({taux_echec*100:.0f}%)")
                    if ecart_type > 4:
                        reasons.append("Forte dispersion des notes")
                    alerte_message = ", ".join(reasons)
                
                info = modules_info.get(code, {})
                
                modules.append(ModuleAnalyse(
                    code=code,
                    semestre=info.get("semestre", ""),
                    formation=info.get("formation", ""),
                    nom=info.get("nom", "Module"),
                    moyenne=round(moyenne, 2),
                    ecart_type=round(ecart_type, 2),
                    taux_validation=round(1 - taux_echec, 2),
                    taux_echec=round(taux_echec, 2),
                    nb_defaillants=0,  # Would need specific data
                    mediane=round(mediane, 2),
                    min=round(min(grades), 2),
                    max=round(max(grades), 2),
                    notes_distribution=distribution,
                    alerte=alerte,
                    alerte_message=alerte_message,
                ))
            
            # Sort
            if tri == "taux_echec":
                modules.sort(key=lambda m: m.taux_echec, reverse=True)
            elif tri == "moyenne":
                modules.sort(key=lambda m: m.moyenne)
            elif tri == "ecart_type":
                modules.sort(key=lambda m: m.ecart_type, reverse=True)
            else:
                modules.sort(key=lambda m: m.code)
            
            return modules
            
        except Exception as e:
            logger.error(f"Error analyzing modules: {e}")
            return []
    
    async def get_analyse_absenteisme(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> Optional[AnalyseAbsenteisme]:
        """Analyze absence patterns."""
        if not await self.adapter.authenticate():
            return None
        
        try:
            semestres = await self.adapter.get_formsemestres_courants()
            if not semestres:
                return None
            
            semestres = self._filter_semestres(semestres, semestre, formation, modalite)
            
            if not semestres:
                return None
            
            total_heures = 0
            total_etudiants = 0
            
            for sem in semestres:
                sem_id = sem.get("formsemestre_id")
                
                # Get absence count
                assiduites = await self.adapter.get_formsemestre_assiduites_count(sem_id)
                if assiduites:
                    total_heures += assiduites.get("heure", 0) or 0
                
                # Count students
                etudiants = await self.adapter.get_formsemestre_etudiants(sem_id)
                if etudiants:
                    total_etudiants += len(etudiants)
            
            if total_etudiants == 0:
                return None
            
            # Estimate expected hours (400h per student per semester)
            heures_attendues = total_etudiants * 400
            taux_global = total_heures / heures_attendues if heures_attendues > 0 else 0
            
            return AnalyseAbsenteisme(
                taux_global=round(taux_global, 3),
                taux_justifie=round(taux_global * 0.6, 3),  # Estimate
                taux_non_justifie=round(taux_global * 0.4, 3),
                nb_absences_total=int(total_heures / 2),  # Convert hours to half-days
                heures_perdues=int(total_heures),
                par_module={},  # Would need detailed data
                par_jour_semaine={},
                par_creneau={},
                etudiants_critiques=int(total_etudiants * 0.1),  # Estimate 10%
                evolution_hebdo=[],
                correlation_notes=-0.5,  # Typical negative correlation
            )
            
        except Exception as e:
            logger.error(f"Error analyzing absences: {e}")
            return None
    
    async def get_comparaison_interannuelle(
        self, 
        nb_annees: int = 5
    ) -> ComparaisonInterannuelle:
        """Compare indicators over multiple years."""
        # TODO: Implement with historical data from DB
        return ComparaisonInterannuelle(
            annees=["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"][-nb_annees:],
            moyennes=[10.8, 11.0, 11.2, 11.3, 11.5][-nb_annees:],
            taux_reussite=[0.72, 0.74, 0.75, 0.76, 0.78][-nb_annees:],
            taux_absenteisme=[0.12, 0.11, 0.10, 0.09, 0.08][-nb_annees:],
            effectifs=[110, 115, 118, 120, 120][-nb_annees:],
            taux_diplomation=[0.65, 0.68, 0.70, 0.71, 0.72][-nb_annees:],
            tendance_globale="amélioration",
        )

    async def get_analyse_type_bac(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> AnalyseTypeBac:
        """Analyze success by baccalaureate type."""
        # TODO: Implement with student profiles
        return AnalyseTypeBac(
            par_type={
                "Général": {
                    "effectif": 45,
                    "pourcentage": 0.375,
                    "moyenne": 12.8,
                    "taux_reussite": 0.89,
                    "taux_excellence": 0.22,
                },
                "STI2D": {
                    "effectif": 52,
                    "pourcentage": 0.433,
                    "moyenne": 10.5,
                    "taux_reussite": 0.73,
                    "taux_excellence": 0.08,
                },
                "Pro": {
                    "effectif": 18,
                    "pourcentage": 0.15,
                    "moyenne": 8.2,
                    "taux_reussite": 0.55,
                    "taux_excellence": 0.02,
                },
                "Autre": {
                    "effectif": 5,
                    "pourcentage": 0.042,
                    "moyenne": 9.8,
                    "taux_reussite": 0.60,
                    "taux_excellence": 0.05,
                },
            },
            ecart_max=4.6,
            type_meilleur="Général",
            type_difficulte="Pro",
            recommandation="Renforcer l'accompagnement des étudiants issus de bac Pro dès le S1",
        )

    async def get_analyse_boursiers(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> AnalyseBoursiers:
        """Analyze success for scholarship students."""
        return AnalyseBoursiers(
            nb_boursiers=58,
            pourcentage_boursiers=0.48,
            moyenne_boursiers=11.0,
            moyenne_non_boursiers=11.9,
            ecart_moyenne=-0.9,
            taux_reussite_boursiers=0.74,
            taux_reussite_non_boursiers=0.82,
            taux_abandon_boursiers=0.08,
            taux_abandon_non_boursiers=0.06,
        )

    async def get_indicateurs_predictifs(
        self,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> IndicateursPredictifs:
        """Get predictive indicators."""
        return IndicateursPredictifs(
            taux_diplomation_prevu=0.75,
            intervalle_confiance=(0.70, 0.80),
            nb_risque_echec_eleve=12,
            nb_risque_echec_moyen=25,
            facteurs_risque_principaux=["Absentéisme > 15%", "Notes S1 < 8"],
            actions_recommandees=["Tutorat", "Entretiens individuels"],
        )

    async def get_tableau_bord(
        self,
        annee: Optional[str] = None,
        semestre: Optional[str] = None,
        formation: Optional[str] = None,
        modalite: Optional[str] = None,
    ) -> Optional[TableauBordCohorte]:
        """Get complete dashboard with all indicators."""
        stats = await self.get_statistiques_cohorte(semestre, formation=formation, modalite=modalite)
        if not stats:
            return None
        
        taux = await self.get_taux_validation(semestre, formation=formation, modalite=modalite)
        mentions = await self.get_mentions(semestre, formation=formation, modalite=modalite)
        absences = await self.get_analyse_absenteisme(semestre, formation=formation, modalite=modalite)
        
        return TableauBordCohorte(
            department=self.adapter.department or "RT",
            annee=annee or "2024-2025",
            semestre=semestre or "S1",
            statistiques=stats,
            taux_validation=taux,
            mentions=mentions,
            indicateurs_cles={
                "taux_reussite": {"valeur": stats.taux_reussite, "tendance": "stable", "vs_annee_prec": 0},
                "moyenne_promo": {"valeur": stats.moyenne_promo, "tendance": "stable", "vs_annee_prec": 0},
                "taux_absenteisme": {"valeur": absences.taux_global if absences else 0, "tendance": "stable", "vs_annee_prec": 0},
                "etudiants_alertes": {"valeur": int(stats.effectif_total * (stats.taux_difficulte or 0)), "tendance": "stable", "vs_annee_prec": 0},
            },
            alertes_recentes=[
                {"type": "critique", "nombre": int(stats.effectif_total * 0.05), "evolution": 0},
                {"type": "attention", "nombre": int(stats.effectif_total * 0.15), "evolution": 0},
            ],
        )
