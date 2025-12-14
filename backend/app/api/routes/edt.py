"""EDT (Emploi du Temps) API routes."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import Optional
from datetime import date

from app.models.edt import EDTIndicators, ChargeEnseignant
from app.adapters.excel import MockExcelAdapter, ExcelAdapter
from app.api.deps import DepartmentDep
from app.services import cache, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Use mock adapter for development
_mock_adapter = MockExcelAdapter()
_file_adapter = ExcelAdapter()


@router.get("/indicators", response_model=EDTIndicators)
async def get_edt_indicators(
    department: DepartmentDep,
    annee: Optional[str] = Query(None, description="Année universitaire (ex: 2024-2025)"),
    refresh: bool = Query(False, description="Force cache refresh"),
):
    """
    Get aggregated EDT indicators.
    
    Returns workload statistics, room occupation, and hour distribution.
    """
    try:
        cache_key = CacheKeys.edt_indicators(annee, department)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, EDTIndicators)
            if cached:
                return cached
        
        # Fetch fresh data
        data = _mock_adapter.get_mock_edt()
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_edt)
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charges", response_model=list[ChargeEnseignant])
async def get_charges_enseignants(
    department: DepartmentDep,
    enseignant: Optional[str] = Query(None, description="Filter by teacher name"),
):
    """
    Get teacher workloads.
    
    Returns hours by type (CM/TD/TP) and complementary hours.
    """
    data = _mock_adapter.get_mock_edt()
    charges = data.charges_enseignants
    
    if enseignant:
        charges = [c for c in charges if enseignant.lower() in c.enseignant.lower()]
    
    return charges


@router.get("/occupation")
async def get_occupation_salles(
    department: DepartmentDep,
    salle: Optional[str] = Query(None, description="Filter by room"),
):
    """
    Get room occupation rates.
    """
    data = _mock_adapter.get_mock_edt()
    occupation = data.occupation_salles
    
    if salle:
        occupation = [o for o in occupation if salle.lower() in o.salle.lower()]
    
    return {
        "salles": occupation,
        "taux_moyen": data.taux_occupation_moyen,
    }


@router.get("/repartition")
async def get_repartition_heures(
    department: DepartmentDep,
):
    """
    Get hours distribution by type (CM/TD/TP).
    """
    data = _mock_adapter.get_mock_edt()
    total = data.total_heures
    
    return {
        "total": total,
        "cm": {"heures": data.heures_cm, "pourcentage": data.heures_cm / total if total > 0 else 0},
        "td": {"heures": data.heures_td, "pourcentage": data.heures_td / total if total > 0 else 0},
        "tp": {"heures": data.heures_tp, "pourcentage": data.heures_tp / total if total > 0 else 0},
    }


@router.get("/heures-complementaires")
async def get_heures_complementaires(
    department: DepartmentDep,
):
    """
    Get complementary hours summary.
    """
    data = _mock_adapter.get_mock_edt()
    
    # Teachers with complementary hours
    with_hc = [c for c in data.charges_enseignants if c.heures_complementaires > 0]
    
    return {
        "total": data.total_heures_complementaires,
        "enseignants": len(with_hc),
        "detail": [
            {"enseignant": c.enseignant, "heures": c.heures_complementaires}
            for c in sorted(with_hc, key=lambda x: -x.heures_complementaires)
        ],
    }


@router.get("/par-module")
async def get_heures_par_module(
    department: DepartmentDep,
):
    """
    Get hours by module.
    """
    data = _mock_adapter.get_mock_edt()
    return {
        "modules": [
            {"module": k, "heures": v}
            for k, v in sorted(data.heures_par_module.items(), key=lambda x: -x[1])
        ],
        "total": sum(data.heures_par_module.values()),
    }


@router.post("/import")
async def import_edt_file(
    department: DepartmentDep,
    file: UploadFile = File(..., description="EDT Excel file"),
    annee: Optional[str] = Query(None, description="Année universitaire"),
):
    """
    Import EDT Excel file.
    
    Expected columns: Enseignant, Module, Type (CM/TD/TP), Heures, Salle
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        indicators = _file_adapter.parse_edt_file(content)
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors du parsing du fichier: {str(e)}"
        )
