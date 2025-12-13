"""Pydantic schemas for Recrutement/Parcoursup CRUD operations."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ==================== CANDIDAT ====================

class CandidatBase(BaseModel):
    """Base schema for candidate."""
    numero_candidat: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    type_bac: str = Field(min_length=1, max_length=50)
    serie_bac: Optional[str] = None
    mention_bac: Optional[str] = None
    annee_bac: Optional[int] = Field(None, ge=2000, le=2100)
    departement_origine: Optional[str] = None
    pays_origine: str = "France"
    lycee: Optional[str] = None
    code_lycee: Optional[str] = None
    rang_voeu: Optional[int] = Field(None, ge=1)
    rang_appel: Optional[int] = Field(None, ge=1)
    statut: str = Field(default="en_attente", pattern="^(en_attente|propose|accepte|refuse|confirme|desiste)$")
    date_reponse: Optional[date] = None


class CandidatCreate(CandidatBase):
    """Schema for creating a candidate."""
    pass


class CandidatUpdate(BaseModel):
    """Schema for updating a candidate."""
    type_bac: Optional[str] = Field(None, min_length=1, max_length=50)
    serie_bac: Optional[str] = None
    mention_bac: Optional[str] = None
    annee_bac: Optional[int] = Field(None, ge=2000, le=2100)
    departement_origine: Optional[str] = None
    pays_origine: Optional[str] = None
    lycee: Optional[str] = None
    rang_voeu: Optional[int] = Field(None, ge=1)
    rang_appel: Optional[int] = Field(None, ge=1)
    statut: Optional[str] = Field(None, pattern="^(en_attente|propose|accepte|refuse|confirme|desiste)$")
    date_reponse: Optional[date] = None


class CandidatResponse(CandidatBase):
    """Response schema for candidate."""
    id: int
    campagne_id: int
    
    class Config:
        from_attributes = True


class CandidatBulkCreate(BaseModel):
    """Schema for bulk creating candidates."""
    candidats: list[CandidatCreate]


# ==================== CAMPAGNE RECRUTEMENT ====================

class CampagneBase(BaseModel):
    """Base schema for recruitment campaign."""
    annee: int = Field(ge=2000, le=2100)
    nb_places: int = Field(default=0, ge=0)
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    rang_dernier_appele: Optional[int] = Field(None, ge=1)


class CampagneCreate(CampagneBase):
    """Schema for creating a campaign."""
    pass


class CampagneUpdate(BaseModel):
    """Schema for updating a campaign."""
    nb_places: Optional[int] = Field(None, ge=0)
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    rang_dernier_appele: Optional[int] = Field(None, ge=1)


class CampagneResponse(CampagneBase):
    """Response schema for campaign."""
    id: int
    date_creation: date
    date_modification: date
    
    # Stats calculées
    nb_candidats: int = 0
    nb_acceptes: int = 0
    nb_confirmes: int = 0
    taux_acceptation: float = 0
    taux_confirmation: float = 0
    
    class Config:
        from_attributes = True


class CampagneSummary(BaseModel):
    """Summary for campaign list."""
    id: int
    annee: int
    nb_places: int
    nb_candidats: int
    nb_confirmes: int
    taux_remplissage: float
    
    class Config:
        from_attributes = True


# ==================== STATISTIQUES ====================

class ParcoursupStatsInput(BaseModel):
    """Input schema for direct statistics entry."""
    nb_voeux: int = Field(ge=0, description="Nombre total de vœux")
    nb_acceptes: int = Field(ge=0, description="Nombre d'acceptés")
    nb_confirmes: int = Field(ge=0, description="Nombre de confirmés")
    nb_refuses: int = Field(default=0, ge=0, description="Nombre de refusés")
    nb_desistes: int = Field(default=0, ge=0, description="Nombre de désistés")
    par_type_bac: Optional[dict[str, int]] = Field(default=None, description="Répartition par type de bac")
    par_mention: Optional[dict[str, int]] = Field(default=None, description="Répartition par mention")
    par_origine: Optional[dict[str, int]] = Field(default=None, description="Répartition géographique")
    par_lycees: Optional[dict[str, int]] = Field(default=None, description="Répartition par lycée")


class ParcoursupStats(BaseModel):
    """Aggregated Parcoursup statistics."""
    annee: int
    nb_voeux: int
    nb_acceptes: int
    nb_confirmes: int
    nb_refuses: int
    nb_desistes: int
    taux_acceptation: float
    taux_confirmation: float
    par_type_bac: dict[str, int]
    par_mention: dict[str, int]
    par_origine: dict[str, int]
    top_lycees: list[dict]


class EvolutionRecrutement(BaseModel):
    """Evolution over years."""
    annees: list[int]
    nb_voeux: list[int]
    nb_confirmes: list[int]
    taux_remplissage: list[float]


# ==================== IMPORT ====================

class ImportParcoursupResult(BaseModel):
    """Result of Parcoursup file import."""
    success: bool
    message: str
    annee: int
    candidats_importes: int = 0
    candidats_mis_a_jour: int = 0
    erreurs: list[str] = []
