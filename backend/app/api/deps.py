"""Common dependencies for API routes."""

from typing import Annotated
from functools import lru_cache

from fastapi import Depends

from app.config import Settings, get_settings
from app.adapters.scodoc import ScoDocAdapter
from app.adapters.excel import ExcelAdapter
from app.adapters.parcoursup import ParcoursupAdapter


# Settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def get_scodoc_adapter() -> ScoDocAdapter:
    """Get ScoDoc adapter instance."""
    settings = get_settings()
    return ScoDocAdapter(
        base_url=settings.scodoc_base_url,
        username=settings.scodoc_username,
        password=settings.scodoc_password,
        department=settings.scodoc_department,
    )


@lru_cache
def get_excel_adapter() -> ExcelAdapter:
    """Get Excel adapter instance."""
    return ExcelAdapter()


@lru_cache
def get_parcoursup_adapter() -> ParcoursupAdapter:
    """Get Parcoursup adapter instance."""
    return ParcoursupAdapter()


# Adapter dependencies
ScoDocDep = Annotated[ScoDocAdapter, Depends(get_scodoc_adapter)]
ExcelDep = Annotated[ExcelAdapter, Depends(get_excel_adapter)]
ParcoursupDep = Annotated[ParcoursupAdapter, Depends(get_parcoursup_adapter)]
