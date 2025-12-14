"""Common dependencies for API routes."""

from typing import Annotated
from functools import lru_cache
from enum import Enum

from fastapi import Depends, Path, HTTPException

from app.config import Settings, get_settings
from app.adapters.scodoc import ScoDocAdapter
from app.adapters.excel import ExcelAdapter
from app.adapters.parcoursup import ParcoursupAdapter


class Department(str, Enum):
    """Valid departments."""
    RT = "RT"
    GEII = "GEII"
    GCCD = "GCCD"
    GMP = "GMP"
    QLIO = "QLIO"
    CHIMIE = "CHIMIE"


VALID_DEPARTMENTS = [d.value for d in Department]


def validate_department(department: str) -> str:
    """Validate department code."""
    dept_upper = department.upper()
    if dept_upper not in VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Département invalide: {department}. Valeurs autorisées: {', '.join(VALID_DEPARTMENTS)}"
        )
    return dept_upper


# Department path parameter dependency
DepartmentDep = Annotated[str, Path(
    ..., 
    description="Code du département (RT, GEII, GCCD, GMP, QLIO, CHIMIE)",
    pattern="^(RT|GEII|GCCD|GMP|QLIO|CHIMIE)$",
    examples=["RT", "GEII"]
)]


# Settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_scodoc_adapter_for_department(department: str) -> ScoDocAdapter:
    """Get ScoDoc adapter instance for a specific department."""
    settings = get_settings()
    return ScoDocAdapter(
        base_url=settings.scodoc_base_url,
        username=settings.scodoc_username,
        password=settings.scodoc_password,
        department=department,  # Use the department from path
    )


@lru_cache
def get_scodoc_adapter() -> ScoDocAdapter:
    """Get ScoDoc adapter instance (deprecated - use get_scodoc_adapter_for_department)."""
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
