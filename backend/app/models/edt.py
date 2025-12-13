"""EDT (Emploi du Temps) models."""

from pydantic import BaseModel
from typing import Optional
from datetime import date, time
from enum import Enum


class TypeCours(str, Enum):
    """Course types."""
    CM = "CM"
    TD = "TD"
    TP = "TP"
    PROJET = "Projet"
    EXAMEN = "Examen"
    AUTRE = "Autre"


class Cours(BaseModel):
    """Course session model."""
    id: str
    module: str
    type: TypeCours
    enseignant: str
    salle: str
    date: date
    heure_debut: time
    heure_fin: time
    groupe: Optional[str] = None
    duree_heures: float


class ChargeEnseignant(BaseModel):
    """Teacher workload model."""
    enseignant: str
    heures_cm: float
    heures_td: float
    heures_tp: float
    heures_projet: float
    total_heures: float
    heures_statutaires: float
    heures_complementaires: float


class OccupationSalle(BaseModel):
    """Room occupation model."""
    salle: str
    capacite: int
    heures_occupees: float
    heures_disponibles: float
    taux_occupation: float


class EDTIndicators(BaseModel):
    """Aggregated EDT indicators."""
    periode_debut: date
    periode_fin: date
    
    # Totaux
    total_heures: float
    heures_cm: float
    heures_td: float
    heures_tp: float
    
    # Par type
    repartition_types: dict[str, float]
    
    # Charges enseignants
    charges_enseignants: list[ChargeEnseignant]
    total_heures_complementaires: float
    
    # Occupation salles
    occupation_salles: list[OccupationSalle]
    taux_occupation_moyen: float
    
    # Par module
    heures_par_module: dict[str, float]
    
    # Évolution hebdomadaire
    evolution_hebdo: dict[str, float]  # "2024-W01" -> heures
