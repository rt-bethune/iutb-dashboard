"""Modèles pour les alertes et le suivi des étudiants."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class NiveauAlerte(str, Enum):
    """Niveaux de sévérité des alertes."""
    INFO = "info"
    ATTENTION = "attention"
    CRITIQUE = "critique"


class TypeAlerte(str, Enum):
    """Types d'alertes disponibles."""
    DIFFICULTE_ACADEMIQUE = "difficulte_academique"
    ASSIDUITE = "assiduite"
    DECROCHAGE = "decrochage"
    PROGRESSION_NEGATIVE = "progression_negative"
    RETARD_TRAVAUX = "retard_travaux"
    RISQUE_ECHEC = "risque_echec"


class ConfigAlerte(BaseModel):
    """Configuration des seuils d'alerte (paramétrable par département)."""
    # Seuils académiques
    moyenne_difficulte: float = Field(default=8.0, description="Moyenne sous laquelle l'étudiant est en difficulté")
    nb_modules_echec_difficulte: int = Field(default=3, description="Nombre de modules < 10 pour être en difficulté")
    
    # Seuils assiduité
    taux_absence_attention: float = Field(default=0.10, description="10% d'absences = attention")
    taux_absence_critique: float = Field(default=0.20, description="20% d'absences = critique")
    taux_absence_non_justifiee: float = Field(default=0.15, description="15% non justifiées = alerte")
    
    # Seuils progression
    delta_moyenne_alerte: float = Field(default=-2.0, description="Baisse de moyenne déclenchant une alerte")
    
    # Seuils décrochage (score composite)
    score_decrochage_attention: float = Field(default=0.5, description="Score 0-1, au-dessus = attention")
    score_decrochage_critique: float = Field(default=0.7, description="Score 0-1, au-dessus = critique")


class AlerteEtudiant(BaseModel):
    """Alerte individuelle pour un étudiant."""
    etudiant_id: str
    etudiant_nom: str
    etudiant_prenom: str
    type_alerte: TypeAlerte
    niveau: NiveauAlerte
    message: str
    valeur_actuelle: Optional[float] = None
    seuil: Optional[float] = None
    date_detection: date
    semestre: Optional[str] = None
    modules_concernes: list[str] = []


class StatistiquesAbsences(BaseModel):
    """Statistiques d'absences détaillées pour un étudiant."""
    etudiant_id: str
    total_absences: int
    absences_justifiees: int
    absences_non_justifiees: int
    taux_absenteisme: float
    taux_justification: float
    absences_par_module: dict[str, int] = {}
    absences_par_jour_semaine: dict[str, int] = {}  # "lundi" -> count
    absences_par_creneau: dict[str, int] = {}  # "matin" / "apres_midi"
    tendance: str = "stable"  # "hausse", "baisse", "stable"


class ProgressionEtudiant(BaseModel):
    """Suivi de progression d'un étudiant sur plusieurs semestres."""
    etudiant_id: str
    etudiant_nom: str
    etudiant_prenom: str
    historique_moyennes: list[dict] = []  # [{"semestre": "S1", "moyenne": 12.5, "rang": 45}]
    tendance_globale: str = "stable"  # "progression", "regression", "stable"
    delta_dernier_semestre: Optional[float] = None
    modules_progression: list[dict] = []  # Modules où l'étudiant progresse
    modules_regression: list[dict] = []  # Modules où l'étudiant régresse


class ScoreRisque(BaseModel):
    """Score de risque d'échec pour un étudiant."""
    etudiant_id: str
    score_global: float = Field(ge=0, le=1, description="Score de 0 (aucun risque) à 1 (risque max)")
    facteurs: dict[str, float] = {}  # {"notes": 0.3, "assiduite": 0.2, "progression": 0.1}
    probabilite_validation: float = Field(ge=0, le=1)
    recommandations: list[str] = []


class ProfilEtudiant(BaseModel):
    """Profil complet d'un étudiant avec toutes ses métriques."""
    # Identité
    id: str
    nom: str
    prenom: str
    email: Optional[str] = None
    formation: str
    semestre_actuel: str
    groupe: Optional[str] = None
    
    # Informations admission
    type_bac: Optional[str] = None
    mention_bac: Optional[str] = None
    annee_bac: Optional[int] = None
    lycee_origine: Optional[str] = None
    boursier: bool = False
    
    # Métriques académiques
    moyenne_actuelle: Optional[float] = None
    rang_promo: Optional[int] = None
    rang_groupe: Optional[int] = None
    effectif_promo: Optional[int] = None
    ects_valides: int = 0
    ects_total: int = 0
    
    # Alertes actives
    alertes: list[AlerteEtudiant] = []
    niveau_alerte_max: Optional[NiveauAlerte] = None
    
    # Absences
    statistiques_absences: Optional[StatistiquesAbsences] = None
    
    # Progression
    progression: Optional[ProgressionEtudiant] = None
    
    # Risque
    score_risque: Optional[ScoreRisque] = None
    
    # Notes par module
    notes_modules: list[dict] = []  # [{"code": "R1.01", "nom": "...", "moyenne": 12.5}]


class FicheEtudiantComplete(BaseModel):
    """Fiche complète pour le suivi individuel d'un étudiant."""
    profil: ProfilEtudiant
    historique_semestres: list[dict] = []
    graphique_progression: list[dict] = []  # Pour affichage frontend
    comparaison_promo: dict = {}  # Position relative
    recommandations_personnalisees: list[str] = []
