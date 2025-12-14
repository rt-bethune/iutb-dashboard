"""Recrutement/Parcoursup Admin API routes with CRUD operations."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.crud import recrutement_crud
from app.api.deps import DepartmentDep
from app.schemas.recrutement import (
    CampagneCreate,
    CampagneUpdate,
    CampagneResponse,
    CampagneSummary,
    CandidatCreate,
    CandidatUpdate,
    CandidatResponse,
    CandidatBulkCreate,
    ParcoursupStats,
    ParcoursupStatsInput,
    EvolutionRecrutement,
    ImportParcoursupResult,
)
from app.models.recrutement import RecrutementIndicators, VoeuStats, LyceeStats
from app.models.db_models import CampagneRecrutement

router = APIRouter()


# ==================== CAMPAGNES ====================

@router.get("/campagnes", response_model=list[CampagneSummary])
async def list_campagnes(
    department: DepartmentDep,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
):
    """List all recruitment campaigns."""
    campagnes = recrutement_crud.get_all_campagnes(db, department, skip=skip, limit=limit)
    result = []
    for c in campagnes:
        stats = recrutement_crud.get_parcoursup_stats(db, department, c.annee)
        nb_candidats = stats.nb_voeux if stats else 0
        nb_confirmes = stats.nb_confirmes if stats else 0
        taux = nb_confirmes / c.nb_places if c.nb_places > 0 else 0
        
        result.append(CampagneSummary(
            id=c.id,
            annee=c.annee,
            nb_places=c.nb_places,
            nb_candidats=nb_candidats,
            nb_confirmes=nb_confirmes,
            taux_remplissage=round(taux, 2),
        ))
    return result


@router.get("/campagne/{annee}", response_model=CampagneResponse)
async def get_campagne(
    department: DepartmentDep,
    annee: int,
    db: Session = Depends(get_db),
):
    """Get campaign details for a specific year."""
    campagne = recrutement_crud.get_campagne(db, department, annee)
    if not campagne:
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    
    return CampagneResponse(
        id=campagne.id,
        annee=campagne.annee,
        nb_places=campagne.nb_places,
        date_debut=campagne.date_debut,
        date_fin=campagne.date_fin,
        rang_dernier_appele=campagne.rang_dernier_appele,
        date_creation=campagne.date_creation,
        date_modification=campagne.date_modification,
        nb_candidats=stats.nb_voeux if stats else 0,
        nb_acceptes=stats.nb_acceptes if stats else 0,
        nb_confirmes=stats.nb_confirmes if stats else 0,
        taux_acceptation=stats.taux_acceptation if stats else 0,
        taux_confirmation=stats.taux_confirmation if stats else 0,
    )


@router.post("/campagne", response_model=CampagneResponse)
async def create_campagne(
    department: DepartmentDep,
    campagne: CampagneCreate,
    db: Session = Depends(get_db),
):
    """Create a new recruitment campaign."""
    existing = recrutement_crud.get_campagne(db, department, campagne.annee)
    if existing:
        raise HTTPException(status_code=400, detail=f"Campagne {campagne.annee} existe déjà")
    
    db_campagne = recrutement_crud.create_campagne(db, department, campagne)
    return await get_campagne(department, db_campagne.annee, db)


@router.put("/campagne/{annee}", response_model=CampagneResponse)
async def update_campagne(
    department: DepartmentDep,
    annee: int,
    campagne: CampagneUpdate,
    db: Session = Depends(get_db),
):
    """Update a campaign."""
    db_campagne = recrutement_crud.update_campagne(db, department, annee, campagne)
    if not db_campagne:
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    return await get_campagne(department, annee, db)


@router.delete("/campagne/{annee}")
async def delete_campagne(
    department: DepartmentDep,
    annee: int,
    db: Session = Depends(get_db),
):
    """Delete a campaign and all its candidates."""
    if not recrutement_crud.delete_campagne(db, department, annee):
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    return {"message": f"Campagne {annee} supprimée"}


# ==================== CANDIDATS ====================

@router.get("/campagne/{annee}/candidats", response_model=list[CandidatResponse])
async def list_candidats(
    department: DepartmentDep,
    annee: int,
    statut: Optional[str] = Query(None, pattern="^(en_attente|propose|accepte|refuse|confirme|desiste)$"),
    type_bac: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """List candidates for a campaign."""
    campagne = recrutement_crud.get_campagne(db, department, annee)
    if not campagne:
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    
    candidats = recrutement_crud.get_candidats(
        db, campagne.id,
        statut=statut,
        type_bac=type_bac,
        skip=skip,
        limit=limit
    )
    
    return [CandidatResponse.model_validate(c) for c in candidats]


@router.post("/campagne/{annee}/candidat", response_model=CandidatResponse)
async def create_candidat(
    department: DepartmentDep,
    annee: int,
    candidat: CandidatCreate,
    db: Session = Depends(get_db),
):
    """Add a candidate to a campaign."""
    campagne = recrutement_crud.get_or_create_campagne(db, department, annee)
    db_candidat = recrutement_crud.create_candidat(db, campagne.id, candidat)
    return CandidatResponse.model_validate(db_candidat)


@router.post("/campagne/{annee}/candidats/bulk", response_model=dict)
async def create_candidats_bulk(
    department: DepartmentDep,
    annee: int,
    data: CandidatBulkCreate,
    db: Session = Depends(get_db),
):
    """Add multiple candidates to a campaign."""
    campagne = recrutement_crud.get_or_create_campagne(db, department, annee)
    candidats = recrutement_crud.create_candidats_bulk(db, campagne.id, data.candidats)
    return {"message": f"{len(candidats)} candidats créés", "count": len(candidats)}


@router.get("/candidat/{candidat_id}", response_model=CandidatResponse)
async def get_candidat(
    department: DepartmentDep,
    candidat_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific candidate."""
    candidat = recrutement_crud.get_candidat(db, candidat_id)
    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return CandidatResponse.model_validate(candidat)


@router.put("/candidat/{candidat_id}", response_model=CandidatResponse)
async def update_candidat(
    department: DepartmentDep,
    candidat_id: int,
    candidat: CandidatUpdate,
    db: Session = Depends(get_db),
):
    """Update a candidate."""
    db_candidat = recrutement_crud.update_candidat(db, candidat_id, candidat)
    if not db_candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return CandidatResponse.model_validate(db_candidat)


@router.delete("/candidat/{candidat_id}")
async def delete_candidat(
    department: DepartmentDep,
    candidat_id: int,
    db: Session = Depends(get_db),
):
    """Delete a candidate."""
    if not recrutement_crud.delete_candidat(db, candidat_id):
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return {"message": "Candidat supprimé"}


# ==================== IMPORT ====================

@router.post("/import/csv", response_model=ImportParcoursupResult)
async def import_parcoursup_csv(
    department: DepartmentDep,
    file: UploadFile = File(..., description="Parcoursup CSV export file"),
    annee: int = Query(..., description="Année de recrutement"),
    db: Session = Depends(get_db),
):
    """
    Import Parcoursup data from CSV file.
    
    Accepts standard Parcoursup export format with ; separator.
    """
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV"
        )
    
    content = await file.read()
    result = recrutement_crud.import_parcoursup_from_csv(db, department, content, annee)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@router.post("/import/excel", response_model=ImportParcoursupResult)
async def import_parcoursup_excel(
    department: DepartmentDep,
    file: UploadFile = File(..., description="Parcoursup Excel file"),
    annee: int = Query(..., description="Année de recrutement"),
    db: Session = Depends(get_db),
):
    """
    Import Parcoursup data from Excel file.
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    result = recrutement_crud.import_parcoursup_from_excel(db, department, content, annee)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


# ==================== STATISTICS ====================

@router.post("/stats/{annee}", response_model=ParcoursupStats)
async def save_stats_direct(
    department: DepartmentDep,
    annee: int,
    stats_input: ParcoursupStatsInput,
    db: Session = Depends(get_db),
):
    """
    Save Parcoursup statistics directly without creating individual candidates.
    This is useful for quick entry of aggregate data.
    """
    recrutement_crud.save_direct_stats(
        db, 
        department,
        annee,
        nb_voeux=stats_input.nb_voeux,
        nb_acceptes=stats_input.nb_acceptes,
        nb_confirmes=stats_input.nb_confirmes,
        nb_refuses=stats_input.nb_refuses,
        nb_desistes=stats_input.nb_desistes,
        par_type_bac=stats_input.par_type_bac,
        par_mention=stats_input.par_mention,
        par_origine=stats_input.par_origine,
        par_lycees=stats_input.par_lycees,
    )
    
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    return stats


@router.get("/stats/{annee}", response_model=ParcoursupStats)
async def get_stats(
    department: DepartmentDep,
    annee: int,
    db: Session = Depends(get_db),
):
    """Get Parcoursup statistics for a year."""
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Pas de données pour {annee}")
    return stats


@router.get("/evolution", response_model=dict)
async def get_evolution(
    department: DepartmentDep,
    limit: int = Query(5, le=10),
    db: Session = Depends(get_db),
):
    """Get recruitment evolution over years."""
    return recrutement_crud.get_evolution_recrutement(db, department, limit=limit)


# ==================== INDICATORS (pour dashboard) ====================

@router.get("/indicators", response_model=RecrutementIndicators)
async def get_recrutement_indicators(
    department: DepartmentDep,
    annee: Optional[int] = Query(None, description="Année de recrutement"),
    db: Session = Depends(get_db),
):
    """
    Get recruitment indicators for dashboard.
    Returns data from database or empty/default if no data.
    Falls back to the latest available year if current year has no data.
    """
    if annee is None:
        annee = date.today().year
    
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    
    # If no stats for current year, try to get the latest available
    if not stats or stats.nb_voeux == 0:
        latest_campagne = db.query(CampagneRecrutement).filter(
            CampagneRecrutement.department == department
        ).order_by(CampagneRecrutement.annee.desc()).first()
        if latest_campagne:
            stats = recrutement_crud.get_parcoursup_stats(db, department, latest_campagne.annee)
            if stats:
                annee = latest_campagne.annee
    
    if not stats or stats.nb_voeux == 0:
        # Return empty indicators
        return RecrutementIndicators(
            annee_courante=annee,
            total_candidats=0,
            candidats_acceptes=0,
            candidats_confirmes=0,
            taux_acceptation=0,
            taux_confirmation=0,
            par_type_bac={},
            par_origine={},
            par_mention={},
            evolution=[],
            top_lycees=[],
        )
    
    # Get evolution data
    evolution_data = recrutement_crud.get_evolution_recrutement(db, department)
    evolution = []
    for i, year in enumerate(evolution_data.get("annees", [])):
        evolution.append(VoeuStats(
            annee=year,
            nb_voeux=evolution_data.get("nb_voeux", [])[i] if i < len(evolution_data.get("nb_voeux", [])) else 0,
            nb_acceptes=0,  # Not tracked in evolution
            nb_confirmes=evolution_data.get("nb_confirmes", [])[i] if i < len(evolution_data.get("nb_confirmes", [])) else 0,
            nb_refuses=0,
            nb_desistes=0,
        ))
    
    # Convert top_lycees to LyceeStats
    top_lycees = [
        LyceeStats(lycee=l["lycee"], count=l["count"])
        for l in stats.top_lycees
    ]
    
    return RecrutementIndicators(
        annee_courante=annee,
        total_candidats=stats.nb_voeux,
        candidats_acceptes=stats.nb_acceptes,
        candidats_confirmes=stats.nb_confirmes,
        taux_acceptation=stats.taux_acceptation,
        taux_confirmation=stats.taux_confirmation,
        par_type_bac=stats.par_type_bac,
        par_origine=stats.par_origine,
        par_mention=stats.par_mention,
        evolution=evolution,
        top_lycees=top_lycees,
    )
