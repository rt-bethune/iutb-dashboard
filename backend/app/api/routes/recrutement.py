"""Recrutement API routes."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import Optional

from app.models.recrutement import RecrutementIndicators, VoeuStats
from app.adapters.parcoursup import MockParcoursupAdapter, ParcoursupAdapter
from app.services import cache, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Use mock adapter for development
_mock_adapter = MockParcoursupAdapter()
_file_adapter = ParcoursupAdapter()


@router.get("/indicators", response_model=RecrutementIndicators)
async def get_recrutement_indicators(
    annee: Optional[int] = Query(None, description="Année de recrutement"),
    refresh: bool = Query(False, description="Force cache refresh"),
):
    """
    Get aggregated recruitment indicators.
    
    Returns statistics about candidates, acceptance rates, origins, etc.
    """
    try:
        cache_key = CacheKeys.recrutement_indicators(annee)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, RecrutementIndicators)
            if cached:
                if annee:
                    cached.evolution = [v for v in cached.evolution if v.annee == annee]
                return cached
        
        # Fetch fresh data
        data = _mock_adapter.get_mock_data()
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_recrutement)
        
        if annee:
            # Filter evolution to specific year
            data.evolution = [v for v in data.evolution if v.annee == annee]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution", response_model=list[VoeuStats])
async def get_evolution():
    """
    Get recruitment evolution over multiple years.
    """
    data = _mock_adapter.get_mock_data()
    return data.evolution


@router.get("/par-bac")
async def get_repartition_bac(
    annee: Optional[int] = Query(None, description="Année"),
):
    """
    Get candidate distribution by bac type.
    """
    data = _mock_adapter.get_mock_data()
    return {
        "annee": annee or data.annee_courante,
        "repartition": data.par_type_bac,
        "total": sum(data.par_type_bac.values()),
    }


@router.get("/par-origine")
async def get_repartition_origine(
    annee: Optional[int] = Query(None, description="Année"),
):
    """
    Get candidate distribution by geographic origin.
    """
    data = _mock_adapter.get_mock_data()
    return {
        "annee": annee or data.annee_courante,
        "repartition": data.par_origine,
        "total": sum(data.par_origine.values()),
    }


@router.get("/top-lycees")
async def get_top_lycees(
    limit: int = Query(10, le=50, description="Number of results"),
):
    """
    Get top feeder high schools.
    """
    data = _mock_adapter.get_mock_data()
    return data.top_lycees[:limit]


@router.post("/import")
async def import_parcoursup_file(
    file: UploadFile = File(..., description="Parcoursup CSV export file"),
    annee: int = Query(..., description="Année de recrutement"),
):
    """
    Import Parcoursup CSV export file.
    
    Parses the file and returns recruitment indicators.
    """
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV"
        )
    
    try:
        content = await file.read()
        indicators = _file_adapter.parse_parcoursup_export(content, annee)
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors du parsing du fichier: {str(e)}"
        )
