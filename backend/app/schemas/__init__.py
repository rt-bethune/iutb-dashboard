"""Schemas package."""

from app.schemas.budget import (
    CategorieDepense,
    LigneBudgetCreate,
    LigneBudgetUpdate,
    LigneBudgetResponse,
    DepenseCreate,
    DepenseUpdate,
    DepenseResponse,
    BudgetAnnuelCreate,
    BudgetAnnuelUpdate,
    BudgetAnnuelResponse,
    BudgetAnnuelSummary,
    ImportResult,
)
from app.schemas.recrutement import (
    CandidatCreate,
    CandidatUpdate,
    CandidatResponse,
    CandidatBulkCreate,
    CampagneCreate,
    CampagneUpdate,
    CampagneResponse,
    CampagneSummary,
    ParcoursupStats,
    EvolutionRecrutement,
    ImportParcoursupResult,
)

__all__ = [
    # Budget
    "CategorieDepense",
    "LigneBudgetCreate",
    "LigneBudgetUpdate",
    "LigneBudgetResponse",
    "DepenseCreate",
    "DepenseUpdate",
    "DepenseResponse",
    "BudgetAnnuelCreate",
    "BudgetAnnuelUpdate",
    "BudgetAnnuelResponse",
    "BudgetAnnuelSummary",
    "ImportResult",
    # Recrutement
    "CandidatCreate",
    "CandidatUpdate",
    "CandidatResponse",
    "CandidatBulkCreate",
    "CampagneCreate",
    "CampagneUpdate",
    "CampagneResponse",
    "CampagneSummary",
    "ParcoursupStats",
    "EvolutionRecrutement",
    "ImportParcoursupResult",
]
