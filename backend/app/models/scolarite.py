"""Scolarité models."""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class Etudiant(BaseModel):
    """Student model."""
    id: str
    nom: str
    prenom: str
    email: Optional[str] = None
    formation: str
    semestre: str
    groupe: Optional[str] = None
    date_naissance: Optional[date] = None


class Note(BaseModel):
    """Grade model."""
    etudiant_id: str
    module: str
    note: float
    coefficient: float
    date_evaluation: Optional[date] = None


class Absence(BaseModel):
    """Absence model."""
    etudiant_id: str
    date: date
    module: Optional[str] = None
    justifiee: bool = False
    motif: Optional[str] = None


class ModuleStats(BaseModel):
    """Module statistics."""
    code: str
    nom: str
    moyenne: float
    mediane: float
    ecart_type: float
    taux_reussite: float
    nb_etudiants: int
    nb_notes: int


class SemestreStats(BaseModel):
    """Semester statistics."""
    code: str
    nom: str
    annee: str
    nb_etudiants: int
    moyenne_generale: float
    taux_reussite: float
    taux_absenteisme: float


class ScolariteIndicators(BaseModel):
    """Aggregated scolarité indicators."""
    total_etudiants: int
    etudiants_par_formation: dict[str, int]
    etudiants_par_semestre: dict[str, int]
    moyenne_generale: float
    taux_reussite_global: float  # Traditional: % of grades >= 10/20
    taux_validation_apc: Optional[float] = None  # APC/BUT: % of students with >50% competencies validated
    taux_absenteisme: float
    modules_stats: list[ModuleStats]
    semestres_stats: list[SemestreStats]
    evolution_effectifs: dict[str, int]  # année -> effectif
