"""Modèles pour les indicateurs de cohorte et statistiques avancées."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class TauxValidation(BaseModel):
    """Taux de validation par semestre/année."""
    semestre: Optional[str] = None
    annee: Optional[str] = None
    total_inscrits: Optional[int] = None
    total_valides: Optional[int] = None
    taux_validation: Optional[float] = None
    taux_ajourne: Optional[float] = None
    taux_abandon: Optional[float] = None
    comparaison_annee_precedente: Optional[float] = None
    # Alternative structure used in routes
    taux_global: Optional[float] = None
    par_ue: Optional[dict[str, float]] = None
    par_module: Optional[dict[str, float]] = None
    par_competence: Optional[dict[str, float]] = None


class RepartitionMentions(BaseModel):
    """Distribution des mentions dans une promo."""
    semestre: Optional[str] = None
    annee: Optional[str] = None
    tres_bien: int = 0  # >= 16
    bien: int = 0  # >= 14
    assez_bien: int = 0  # >= 12
    passable: int = 0  # >= 10
    insuffisant: int = 0  # < 10
    non_evalue: int = 0
    eliminatoire: int = 0  # used in route
    pourcentage_admis: Optional[float] = None  # used in route
    
    @property
    def total(self) -> int:
        return self.tres_bien + self.bien + self.assez_bien + self.passable + self.insuffisant


class StatistiquesCohorte(BaseModel):
    """Statistiques globales d'une cohorte."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    
    # Effectifs
    effectif: Optional[int] = None
    effectif_total: Optional[int] = None  # alias
    effectif_par_groupe: Optional[dict[str, int]] = None
    
    # Moyennes
    moyenne_generale: Optional[float] = None
    moyenne_promo: Optional[float] = None  # alias
    mediane: Optional[float] = None
    ecart_type: Optional[float] = None
    note_min: Optional[float] = None
    min: Optional[float] = None  # alias
    note_max: Optional[float] = None
    max: Optional[float] = None  # alias
    
    # Quartiles
    q1: Optional[float] = None  # 25%
    q3: Optional[float] = None  # 75%
    quartiles: Optional[dict[str, float]] = None  # {"Q1": ..., "Q2": ..., "Q3": ...}
    
    # Taux de réussite
    taux_reussite: Optional[float] = None
    taux_difficulte: Optional[float] = None  # < 8/20
    taux_excellence: Optional[float] = None  # >= 14/20
    
    # Homogénéité (faible écart-type = promo homogène)
    indice_homogeneite: str = "moyen"  # "homogene", "moyen", "heterogene"
    
    # Comparaisons
    evolution_vs_annee_precedente: Optional[float] = None
    comparaison_autres_formations: dict[str, float] = {}


class TauxPassage(BaseModel):
    """Taux de passage entre semestres."""
    # Original structure
    de_semestre: Optional[str] = None
    vers_semestre: Optional[str] = None
    annee: Optional[str] = None
    total_candidats: Optional[int] = None
    total_passes: Optional[int] = None
    taux_passage: Optional[float] = None
    total_redoublants: Optional[int] = None
    taux_redoublement: Optional[float] = None
    total_reorientes: Optional[int] = None
    taux_reorientation: Optional[float] = None
    
    # Route-specific fields
    s1_vers_s2: Optional[float] = None
    s2_vers_s3: Optional[float] = None
    s3_vers_s4: Optional[float] = None
    s4_vers_s5: Optional[float] = None
    s5_vers_s6: Optional[float] = None
    taux_diplomation: Optional[float] = None
    taux_abandon: Optional[float] = None
    par_parcours: Optional[dict] = None
    details_echecs: Optional[dict] = None


class ModuleAnalyse(BaseModel):
    """Analyse détaillée d'un module."""
    code: str
    nom: str
    semestre: Optional[str] = None
    annee: Optional[str] = None
    
    # Stats de base
    nb_inscrits: Optional[int] = None
    nb_notes: Optional[int] = None
    moyenne: float
    mediane: float
    ecart_type: float
    min: Optional[float] = None
    max: Optional[float] = None
    
    # Taux - support both naming conventions
    taux_reussite: Optional[float] = None  # >= 10 (can be computed from taux_validation)
    taux_validation: Optional[float] = None  # alias for taux_reussite
    taux_echec_grave: Optional[float] = None  # < 8
    taux_echec: Optional[float] = None  # general failure rate
    
    # Défaillants
    nb_defaillants: Optional[int] = None
    
    # Distribution des notes
    notes_distribution: Optional[dict[str, int]] = None
    
    # Alertes
    alerte: bool = False
    alerte_message: Optional[str] = None
    
    # Classification
    est_module_risque: bool = False  # taux_echec > 30%
    difficulte_relative: str = "normal"  # "facile", "normal", "difficile"
    
    # Évolution
    evolution_annuelle: list[dict] = []  # [{"annee": "2023", "moyenne": 11.2}]
    
    # Corrélation avec réussite globale
    correlation_reussite: Optional[float] = None


class AnalyseAbsenteisme(BaseModel):
    """Analyse de l'absentéisme au niveau cohorte."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    
    # Globaux
    taux_global: float = 0.0
    taux_justifie: float = 0.0
    taux_non_justifie: float = 0.0
    nb_absences_total: Optional[int] = None
    heures_perdues: Optional[int] = None
    
    # Par module (top 5 les plus touchés)
    modules_plus_absences: list[dict] = []
    par_module: Optional[dict] = None  # used in route
    
    # Par créneau
    absences_par_jour: dict[str, float] = {}
    par_jour_semaine: Optional[dict[str, float]] = None  # alias
    absences_par_creneau: dict[str, float] = {}
    par_creneau: Optional[dict[str, float]] = None  # alias
    
    # Corrélation avec notes
    correlation_notes_absences: float = 0.0
    correlation_notes: Optional[float] = None  # alias
    
    # Étudiants concernés
    nb_etudiants_assidus: int = 0  # < 5% absences
    nb_etudiants_moderement_absents: int = 0  # 5-15%
    nb_etudiants_tres_absents: int = 0  # > 15%
    etudiants_critiques: Optional[int] = None  # used in route
    
    # Evolution
    evolution_hebdo: list[dict] = []


class ComparaisonInterannuelle(BaseModel):
    """Comparaison des résultats sur plusieurs années."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annees: list[str] = []
    
    # Données par année (arrays - used in routes)
    moyennes: list[float] = []
    taux_reussite: list[float] = []
    taux_absenteisme: list[float] = []
    effectifs: list[int] = []
    taux_diplomation: list[float] = []
    
    # Données par année (alternative format)
    donnees: list[dict] = []  # [{"annee": "2023", "moyenne": 11.5, "taux_reussite": 0.72}]
    
    # Tendances
    tendance_moyenne: str = "stable"  # "hausse", "baisse", "stable"
    tendance_reussite: str = "stable"
    tendance_effectif: str = "stable"
    tendance_globale: Optional[str] = None  # used in route
    
    # Analyse
    meilleure_annee: Optional[str] = None
    points_attention: list[str] = []


class AnalyseTypeBac(BaseModel):
    """Performance par type de bac d'origine."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    
    # Par type de bac
    resultats_par_bac: list[dict] = []
    par_type: Optional[dict] = None  # used in route: {"Général": {...}, "Techno": {...}}
    
    # Meilleur profil
    type_bac_meilleur_resultat: Optional[str] = None
    meilleur_taux_reussite: Optional[str] = None  # used in route
    meilleur_moyenne: Optional[str] = None  # used in route
    
    # Recommandations recrutement
    recommandations: list[str] = []
    recommandation: Optional[str] = None  # used in route (singular)


class AnalyseBoursiers(BaseModel):
    """Comparaison boursiers vs non-boursiers."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    
    # Boursiers
    nb_boursiers: int = 0
    moyenne_boursiers: float = 0.0
    taux_reussite_boursiers: float = 0.0
    taux_abandon_boursiers: float = 0.0
    
    # Non-boursiers
    nb_non_boursiers: int = 0
    moyenne_non_boursiers: float = 0.0
    taux_reussite_non_boursiers: float = 0.0
    taux_abandon_non_boursiers: float = 0.0
    
    # Écarts
    ecart_moyenne: float = 0.0
    ecart_reussite: float = 0.0
    analyse: str = ""


class TableauBordCohorte(BaseModel):
    """Tableau de bord complet d'une cohorte."""
    department: Optional[str] = None  # used in route
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    date_mise_a_jour: Optional[date] = None
    
    # Vue d'ensemble
    statistiques: Optional[StatistiquesCohorte] = None
    repartition_mentions: Optional[RepartitionMentions] = None
    mentions: Optional[RepartitionMentions] = None  # alias for repartition_mentions
    taux_validation: Optional[TauxValidation] = None
    
    # Alertes niveau promo
    nb_etudiants_en_difficulte: int = 0
    nb_alertes_assiduite: int = 0
    nb_risque_decrochage: int = 0
    
    # Modules à surveiller
    modules_risque: list[ModuleAnalyse] = []
    
    # Absences
    analyse_absenteisme: Optional[AnalyseAbsenteisme] = None
    
    # Points d'attention
    alertes_promo: list[str] = []
    alertes_recentes: list[dict] = []  # used in route
    
    # Key indicators with trends (used in route)
    indicateurs_cles: Optional[dict] = None


class IndicateursPredictifs(BaseModel):
    """Indicateurs prédictifs pour la cohorte."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    
    # Prédictions
    taux_diplomation_prevu: float = 0.0
    intervalle_confiance: tuple[float, float] = (0.0, 1.0)
    
    # Étudiants à risque
    nb_risque_echec_eleve: int = 0  # Score > 0.7
    nb_risque_echec_moyen: int = 0  # Score 0.4-0.7
    
    # Facteurs de risque principaux
    facteurs_risque_principaux: list[str] = []
    
    # Recommandations
    actions_recommandees: list[str] = []


class RapportSemestre(BaseModel):
    """Rapport complet de fin de semestre."""
    formation: Optional[str] = None
    semestre: Optional[str] = None
    annee: Optional[str] = None
    date_generation: Optional[date] = None
    
    # Sections
    resume_executif: str = ""
    tableau_bord: Optional[TableauBordCohorte] = None
    comparaison_annuelle: Optional[ComparaisonInterannuelle] = None
    analyse_bacs: Optional[AnalyseTypeBac] = None
    analyse_boursiers: Optional[AnalyseBoursiers] = None
    indicateurs_predictifs: Optional[IndicateursPredictifs] = None
    
    # Listes
    etudiants_felicitations: list[dict] = []  # Top 10%
    etudiants_surveillances: list[dict] = []  # En difficulté
    
    # Annexes
    statistiques_modules: list[ModuleAnalyse] = []
