"""Budget API routes."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import Optional

from app.models.budget import BudgetIndicators, CategorieDepense
from app.adapters.excel import MockExcelAdapter, ExcelAdapter
from app.api.deps import DepartmentDep
from app.services import cache, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Use mock adapter for development
_mock_adapter = MockExcelAdapter()
_file_adapter = ExcelAdapter()


@router.get("/indicators", response_model=BudgetIndicators)
async def get_budget_indicators(
    department: DepartmentDep,
    annee: Optional[int] = Query(None, description="Année budgétaire"),
    refresh: bool = Query(False, description="Force cache refresh"),
):
    """
    Get aggregated budget indicators.
    
    Returns totals, execution rates, and breakdown by category.
    """
    try:
        cache_key = CacheKeys.budget_indicators(annee, department)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, BudgetIndicators)
            if cached:
                return cached
        
        # Fetch fresh data
        data = _mock_adapter.get_mock_budget()
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_budget)
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/par-categorie")
async def get_budget_par_categorie(
    department: DepartmentDep,
    annee: Optional[int] = Query(None, description="Année budgétaire"),
):
    """
    Get budget breakdown by category.
    """
    data = _mock_adapter.get_mock_budget()
    return {
        "annee": annee or data.annee,
        "categories": [
            {
                "categorie": ligne.categorie.value,
                "budget_initial": ligne.budget_initial,
                "budget_modifie": ligne.budget_modifie,
                "engage": ligne.engage,
                "paye": ligne.paye,
                "disponible": ligne.disponible,
                "taux_execution": ligne.paye / ligne.budget_initial if ligne.budget_initial > 0 else 0,
            }
            for ligne in data.par_categorie
        ],
    }


@router.get("/evolution")
async def get_budget_evolution(
    department: DepartmentDep,
    annee: Optional[int] = Query(None, description="Année budgétaire"),
):
    """
    Get monthly budget evolution.
    """
    data = _mock_adapter.get_mock_budget()
    return {
        "annee": annee or data.annee,
        "evolution_mensuelle": data.evolution_mensuelle,
        "cumul": _calculate_cumul(data.evolution_mensuelle),
    }


@router.get("/execution")
async def get_taux_execution(
    department: DepartmentDep,
):
    """
    Get budget execution rates.
    """
    data = _mock_adapter.get_mock_budget()
    return {
        "taux_execution": data.taux_execution,
        "taux_engagement": data.taux_engagement,
        "budget_total": data.budget_total,
        "engage": data.total_engage,
        "paye": data.total_paye,
        "disponible": data.total_disponible,
    }


@router.get("/top-depenses")
async def get_top_depenses(
    department: DepartmentDep,
    limit: int = Query(10, le=50, description="Number of results"),
    categorie: Optional[CategorieDepense] = Query(None, description="Filter by category"),
):
    """
    Get top expenses.
    """
    data = _mock_adapter.get_mock_budget()
    depenses = data.top_depenses
    
    if categorie:
        depenses = [d for d in depenses if d.categorie == categorie]
    
    return depenses[:limit]


@router.post("/import")
async def import_budget_file(
    department: DepartmentDep,
    file: UploadFile = File(..., description="Budget Excel file"),
    annee: int = Query(..., description="Année budgétaire"),
):
    """
    Import budget Excel file.
    
    Expected columns: Catégorie, Budget Initial, Budget Modifié, Engagé, Payé
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        indicators = _file_adapter.parse_budget_file(content)
        indicators.annee = annee
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors du parsing du fichier: {str(e)}"
        )


def _calculate_cumul(evolution: dict[str, float]) -> dict[str, float]:
    """Calculate cumulative sum from monthly evolution."""
    cumul = {}
    total = 0
    for month in sorted(evolution.keys()):
        total += evolution[month]
        cumul[month] = total
    return cumul
