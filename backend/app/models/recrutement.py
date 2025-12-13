"""Recrutement models."""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class Candidat(BaseModel):
    """Candidate model."""
    id: str
    nom: str
    prenom: str
    email: Optional[str] = None
    type_bac: str
    mention_bac: Optional[str] = None
    annee_bac: int
    origine_geo: str  # département ou pays
    lycee: Optional[str] = None
    statut: str  # "en_attente", "accepte", "refuse", "confirme", "desiste"


class VoeuStats(BaseModel):
    """Wish statistics per year."""
    annee: int
    nb_voeux: int
    nb_acceptes: int
    nb_confirmes: int
    nb_refuses: int
    nb_desistes: int
    rang_dernier_appele: Optional[int] = None


class LyceeStats(BaseModel):
    """Top lycée statistics."""
    lycee: str
    count: int


class RecrutementIndicators(BaseModel):
    """Aggregated recruitment indicators."""
    annee_courante: int
    total_candidats: int
    candidats_acceptes: int
    candidats_confirmes: int
    taux_acceptation: float
    taux_confirmation: float
    
    # Répartition par type de bac
    par_type_bac: dict[str, int]
    
    # Répartition géographique
    par_origine: dict[str, int]
    
    # Répartition par mention
    par_mention: dict[str, int]
    
    # Évolution sur plusieurs années
    evolution: list[VoeuStats]
    
    # Top lycées d'origine
    top_lycees: list[LyceeStats]
