"""Pydantic schemas for Budget CRUD operations."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class CategorieDepense(str, Enum):
    """Expense categories."""
    FONCTIONNEMENT = "fonctionnement"
    INVESTISSEMENT = "investissement"
    MISSIONS = "missions"
    FOURNITURES = "fournitures"
    MAINTENANCE = "maintenance"
    FORMATION = "formation"
    AUTRE = "autre"


# ==================== LIGNE BUDGET ====================

class LigneBudgetBase(BaseModel):
    """Base schema for budget line."""
    categorie: CategorieDepense
    budget_initial: float = Field(ge=0)
    budget_modifie: Optional[float] = None
    engage: float = Field(default=0, ge=0)
    paye: float = Field(default=0, ge=0)


class LigneBudgetCreate(LigneBudgetBase):
    """Schema for creating a budget line."""
    pass


class LigneBudgetUpdate(BaseModel):
    """Schema for updating a budget line."""
    budget_initial: Optional[float] = Field(None, ge=0)
    budget_modifie: Optional[float] = Field(None, ge=0)
    engage: Optional[float] = Field(None, ge=0)
    paye: Optional[float] = Field(None, ge=0)


class LigneBudgetResponse(LigneBudgetBase):
    """Response schema for budget line."""
    id: int
    disponible: float
    
    class Config:
        from_attributes = True


# ==================== DEPENSE ====================

class DepenseBase(BaseModel):
    """Base schema for expense."""
    libelle: str = Field(min_length=1, max_length=255)
    montant: float = Field(gt=0)
    categorie: CategorieDepense
    date_depense: date
    fournisseur: Optional[str] = None
    numero_commande: Optional[str] = None
    statut: str = Field(default="engagee", pattern="^(prevue|engagee|payee)$")


class DepenseCreate(DepenseBase):
    """Schema for creating an expense."""
    pass


class DepenseUpdate(BaseModel):
    """Schema for updating an expense."""
    libelle: Optional[str] = Field(None, min_length=1, max_length=255)
    montant: Optional[float] = Field(None, gt=0)
    categorie: Optional[CategorieDepense] = None
    date_depense: Optional[date] = None
    fournisseur: Optional[str] = None
    numero_commande: Optional[str] = None
    statut: Optional[str] = Field(None, pattern="^(prevue|engagee|payee)$")


class DepenseResponse(DepenseBase):
    """Response schema for expense."""
    id: int
    
    class Config:
        from_attributes = True


# ==================== BUDGET ANNUEL ====================

class BudgetAnnuelBase(BaseModel):
    """Base schema for annual budget."""
    annee: int = Field(ge=2000, le=2100)
    budget_total: float = Field(default=0, ge=0)
    previsionnel: float = Field(default=0, ge=0)


class BudgetAnnuelCreate(BudgetAnnuelBase):
    """Schema for creating annual budget."""
    lignes: Optional[list[LigneBudgetCreate]] = None


class BudgetAnnuelUpdate(BaseModel):
    """Schema for updating annual budget."""
    budget_total: Optional[float] = Field(None, ge=0)
    previsionnel: Optional[float] = Field(None, ge=0)


class BudgetAnnuelResponse(BudgetAnnuelBase):
    """Response schema for annual budget."""
    id: int
    date_creation: date
    date_modification: date
    lignes: list[LigneBudgetResponse] = []
    
    # Calculated fields
    total_engage: float = 0
    total_paye: float = 0
    total_disponible: float = 0
    taux_execution: float = 0
    taux_engagement: float = 0
    
    class Config:
        from_attributes = True


class BudgetAnnuelSummary(BaseModel):
    """Summary schema for annual budget (for lists)."""
    id: int
    annee: int
    budget_total: float
    total_engage: float
    total_paye: float
    taux_execution: float
    
    class Config:
        from_attributes = True


# ==================== IMPORT ====================

class ImportResult(BaseModel):
    """Result of file import operation."""
    success: bool
    message: str
    annee: int
    lignes_importees: int = 0
    depenses_importees: int = 0
    erreurs: list[str] = []
