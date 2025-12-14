"""Recrutement API routes."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from typing import Optional
from datetime import date
import json
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.recrutement import RecrutementIndicators, VoeuStats, LyceeStats
from app.models.db_models import UserDB, CampagneRecrutement, CandidatDB, StatistiquesParcoursup
from app.adapters.parcoursup import ParcoursupAdapter
from app.api.deps import (
    DepartmentDep,
    require_view_recrutement, require_edit_recrutement, require_import
)
from app.services import cache, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

_file_adapter = ParcoursupAdapter()


def get_recrutement_from_db(db: Session, department: str, annee: Optional[int] = None) -> Optional[RecrutementIndicators]:
    """Fetch recruitment data from database."""
    year = annee or date.today().year
    
    # Get aggregated stats
    stats = db.query(StatistiquesParcoursup).filter(
        StatistiquesParcoursup.department == department,
        StatistiquesParcoursup.annee == year
    ).first()
    
    if not stats:
        return None
    
    # Get evolution (all years)
    all_stats = db.query(StatistiquesParcoursup).filter(
        StatistiquesParcoursup.department == department
    ).order_by(StatistiquesParcoursup.annee).all()
    
    evolution = [
        VoeuStats(
            annee=s.annee,
            nb_voeux=s.nb_voeux,
            nb_acceptes=s.nb_acceptes,
            nb_confirmes=s.nb_confirmes,
            nb_refuses=s.nb_refuses,
            nb_desistes=s.nb_desistes,
        )
        for s in all_stats
    ]
    
    # Parse JSON fields
    par_type_bac = json.loads(stats.par_type_bac) if stats.par_type_bac else {}
    par_mention = json.loads(stats.par_mention) if stats.par_mention else {}
    par_origine = json.loads(stats.par_origine) if stats.par_origine else {}
    par_lycees = json.loads(stats.par_lycees) if stats.par_lycees else {}
    
    # Build top lycees
    top_lycees = [
        LyceeStats(lycee=k, count=v) 
        for k, v in sorted(par_lycees.items(), key=lambda x: -x[1])[:10]
    ]
    
    return RecrutementIndicators(
        annee_courante=year,
        total_candidats=stats.nb_voeux,
        candidats_acceptes=stats.nb_acceptes,
        candidats_confirmes=stats.nb_confirmes,
        taux_acceptation=stats.nb_acceptes / stats.nb_voeux if stats.nb_voeux > 0 else 0,
        taux_confirmation=stats.nb_confirmes / stats.nb_acceptes if stats.nb_acceptes > 0 else 0,
        par_type_bac=par_type_bac,
        par_origine=par_origine,
        par_mention=par_mention,
        evolution=evolution,
        top_lycees=top_lycees,
    )


@router.get("/indicators", response_model=RecrutementIndicators)
async def get_recrutement_indicators(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    annee: Optional[int] = Query(None, description="Année de recrutement"),
    refresh: bool = Query(False, description="Force cache refresh"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated recruitment indicators.
    
    Returns statistics about candidates, acceptance rates, origins, etc.
    """
    try:
        cache_key = CacheKeys.recrutement_indicators(annee, department)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, RecrutementIndicators)
            if cached:
                if annee:
                    cached.evolution = [v for v in cached.evolution if v.annee == annee]
                return cached
        
        # Fetch from database
        data = get_recrutement_from_db(db, department, annee)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée recrutement pour {department} en {annee or date.today().year}"
            )
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_recrutement)
        
        if annee:
            # Filter evolution to specific year
            data.evolution = [v for v in data.evolution if v.annee == annee]
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution", response_model=list[VoeuStats])
async def get_evolution(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    db: Session = Depends(get_db),
):
    """
    Get recruitment evolution over multiple years.
    """
    all_stats = db.query(StatistiquesParcoursup).filter(
        StatistiquesParcoursup.department == department
    ).order_by(StatistiquesParcoursup.annee).all()
    
    return [
        VoeuStats(
            annee=s.annee,
            nb_voeux=s.nb_voeux,
            nb_acceptes=s.nb_acceptes,
            nb_confirmes=s.nb_confirmes,
            nb_refuses=s.nb_refuses,
            nb_desistes=s.nb_desistes,
        )
        for s in all_stats
    ]


@router.get("/par-bac")
async def get_repartition_bac(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    annee: Optional[int] = Query(None, description="Année"),
    db: Session = Depends(get_db),
):
    """
    Get candidate distribution by bac type.
    """
    data = get_recrutement_from_db(db, department, annee)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée recrutement trouvée")
    
    return {
        "annee": data.annee_courante,
        "repartition": data.par_type_bac,
        "total": sum(data.par_type_bac.values()),
    }


@router.get("/par-origine")
async def get_repartition_origine(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    annee: Optional[int] = Query(None, description="Année"),
    db: Session = Depends(get_db),
):
    """
    Get candidate distribution by geographic origin.
    """
    data = get_recrutement_from_db(db, department, annee)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée recrutement trouvée")
    
    return {
        "annee": data.annee_courante,
        "repartition": data.par_origine,
        "total": sum(data.par_origine.values()),
    }


@router.get("/top-lycees")
async def get_top_lycees(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    limit: int = Query(10, le=50, description="Number of results"),
    db: Session = Depends(get_db),
):
    """
    Get top feeder high schools.
    """
    data = get_recrutement_from_db(db, department)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée recrutement trouvée")
    
    return data.top_lycees[:limit]


@router.post("/import")
async def import_parcoursup_file(
    department: DepartmentDep,
    user: UserDB = Depends(require_import),
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
