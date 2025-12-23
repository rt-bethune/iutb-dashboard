"""Modèles APC (Approche Par Compétences) - Simplifié avec UEs."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class NiveauCompetence(BaseModel):
    """Niveau d'acquisition d'une compétence (ex: niveau 1/2/3)."""

    niveau: int = Field(ge=1, description="Niveau (1..3)")
    nom: str
    description: Optional[str] = None


class Competence(BaseModel):
    """Compétence du référentiel APC."""

    code: str
    nom: str
    description: Optional[str] = None
    niveaux: list[NiveauCompetence] = []


class UEValidation(BaseModel):
    """Validation d'une UE par étudiant."""

    ue_code: str = Field(description="Code UE (ex: UE31, UE32)")
    ue_titre: str = Field(default="", description="Titre/nom de l'UE")
    moyenne: Optional[float] = Field(default=None, description="Moyenne /20")
    valide: bool = Field(default=False, description="True si moyenne >= 10")
    semestre: Optional[str] = Field(default=None, description="Semestre (S1..S6)")


class UEEtudiant(BaseModel):
    """Synthèse des UEs pour un étudiant."""

    etudiant_id: str
    nom: str
    prenom: str
    formation: Optional[str] = None
    semestre: Optional[str] = None
    parcours: Optional[str] = Field(default=None, description="Parcours (ex: Cybersécurité, DevCloud)")

    nb_ues: int = 0
    nb_ues_validees: int = 0
    taux_validation: float = Field(default=0.0, ge=0.0, le=1.0, description="Ratio 0..1")
    valide: bool = Field(default=False, description="True si >50% des UEs validées")
    moyenne_generale: Optional[float] = Field(default=None, description="Moyenne générale /20")

    ue_validations: list[UEValidation] = []


class UEStats(BaseModel):
    """Statistiques agrégées par UE (cohorte)."""

    total_etudiants: int = 0
    taux_validation_global: float = Field(default=0.0, ge=0.0, le=1.0, description="Ratio 0..1")
    par_ue: dict[str, float] = Field(default_factory=dict, description="UE code -> ratio validé (0..1)")
    moyenne_par_ue: dict[str, float] = Field(default_factory=dict, description="UE code -> moyenne /20")
    distribution_taux_validation: dict[str, int] = Field(default_factory=dict, description="Buckets -> effectif")
    parcours_disponibles: list[str] = Field(default_factory=list, description="Liste des parcours disponibles")
