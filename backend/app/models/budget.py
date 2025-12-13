"""Budget models."""

from pydantic import BaseModel
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


class Depense(BaseModel):
    """Expense model."""
    id: str
    libelle: str
    montant: float
    categorie: CategorieDepense
    date: date
    fournisseur: Optional[str] = None
    numero_commande: Optional[str] = None
    statut: str = "engagee"  # "prevue", "engagee", "payee"


class LigneBudget(BaseModel):
    """Budget line model."""
    categorie: CategorieDepense
    budget_initial: float
    budget_modifie: float
    engage: float
    paye: float
    disponible: float


class BudgetIndicators(BaseModel):
    """Aggregated budget indicators."""
    annee: int
    
    # Totaux
    budget_total: float
    total_engage: float
    total_paye: float
    total_disponible: float
    
    # Taux
    taux_execution: float
    taux_engagement: float
    
    # Par catégorie
    par_categorie: list[LigneBudget]
    
    # Évolution mensuelle
    evolution_mensuelle: dict[str, float]  # "2024-01" -> montant
    
    # Top dépenses
    top_depenses: list[Depense]
    
    # Prévisionnel vs réalisé
    previsionnel: float
    realise: float
