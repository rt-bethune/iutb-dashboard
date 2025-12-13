"""CRUD operations package."""

from app.crud import budget as budget_crud
from app.crud import recrutement as recrutement_crud
from app.crud import admin as admin_crud

__all__ = ["budget_crud", "recrutement_crud", "admin_crud"]
