"""Administration API routes with database persistence.

Simplified admin module:
- Dashboard: Global stats overview
- Sources: CRUD for data source configuration (for future real integrations)
- Settings: System settings management
- Cache: Redis cache stats and clearing
- Jobs: APScheduler job listing and manual execution
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import admin_crud

from app.models.admin import (
    DataSourceConfig,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceType,
    SystemSettings,
    ScheduledJob,
    CacheStats,
    AdminDashboard,
)
from app.services import cache, scheduler
from app.config import get_settings

router = APIRouter()
settings = get_settings()


# ============== Dashboard Admin ==============

@router.get(
    "/dashboard",
    response_model=AdminDashboard,
    summary="Vue d'ensemble administration",
)
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Récupère la vue d'ensemble de l'administration.
    
    Inclut les statistiques des sources, du cache et des jobs.
    """
    # Get sources from DB
    sources = admin_crud.get_all_sources(db)
    
    cache_stats_raw = await cache.get_stats()
    cache_stats = CacheStats(
        connected=cache_stats_raw.get("connected", False),
        keys=cache_stats_raw.get("keys", 0),
        hits=cache_stats_raw.get("hits", 0),
        misses=cache_stats_raw.get("misses", 0),
        memory_used=cache_stats_raw.get("memory_used", "N/A"),
        hit_rate=(
            cache_stats_raw.get("hits", 0) / 
            max(cache_stats_raw.get("hits", 0) + cache_stats_raw.get("misses", 0), 1)
        ),
    )
    
    jobs = scheduler.get_jobs() if settings.cache_enabled else []
    
    return AdminDashboard(
        total_sources=len(sources),
        active_sources=sum(1 for s in sources if s.status == "active"),
        sources_in_error=sum(1 for s in sources if s.status == "error"),
        cache_stats=cache_stats,
        scheduled_jobs=len(jobs),
        jobs_running=0,
    )


# ============== Data Sources ==============

@router.get(
    "/sources",
    summary="Liste des sources de données",
)
async def list_data_sources(
    type: Optional[str] = Query(None, description="Filtrer par type"),
    enabled: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    db: Session = Depends(get_db),
):
    """Récupère la liste des sources de données configurées."""
    sources = admin_crud.get_all_sources(db, source_type=type, enabled=enabled)
    return [admin_crud.source_to_dict(s) for s in sources]


@router.get(
    "/sources/{source_id}",
    summary="Détails d'une source",
)
async def get_data_source(source_id: str, db: Session = Depends(get_db)):
    """Récupère les détails d'une source de données."""
    source = admin_crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return admin_crud.source_to_dict(source)


@router.post(
    "/sources",
    summary="Créer une source",
)
async def create_data_source(data: DataSourceCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle source de données."""
    source_id = f"{data.type.value}-{uuid.uuid4().hex[:8]}"
    
    source_data = {
        "source_id": source_id,
        "name": data.name,
        "type": data.type.value,
        "status": "inactive",
        "description": data.description,
        "base_url": data.base_url,
        "username": data.username,
        "enabled": 1 if data.enabled else 0,
        "auto_sync": 1 if data.auto_sync else 0,
        "sync_interval_hours": data.sync_interval_hours,
    }
    
    source = admin_crud.create_source(db, source_data)
    return admin_crud.source_to_dict(source)


@router.put(
    "/sources/{source_id}",
    summary="Modifier une source",
)
async def update_data_source(
    source_id: str, 
    data: DataSourceUpdate, 
    db: Session = Depends(get_db)
):
    """Met à jour une source de données."""
    source = admin_crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    update_data = data.model_dump(exclude_unset=True)
    # Convert booleans to int for SQLite
    if "enabled" in update_data:
        update_data["enabled"] = 1 if update_data["enabled"] else 0
    if "auto_sync" in update_data:
        update_data["auto_sync"] = 1 if update_data["auto_sync"] else 0
    
    updated = admin_crud.update_source(db, source_id, update_data)
    return admin_crud.source_to_dict(updated)


@router.delete(
    "/sources/{source_id}",
    summary="Supprimer une source",
)
async def delete_data_source(source_id: str, db: Session = Depends(get_db)):
    """Supprime une source de données."""
    source = admin_crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    admin_crud.delete_source(db, source_id)
    return {"message": "Source supprimée", "id": source_id}


# ============== Settings ==============

@router.get(
    "/settings",
    response_model=SystemSettings,
    summary="Paramètres système",
)
async def get_system_settings(db: Session = Depends(get_db)):
    """Récupère les paramètres système du dashboard."""
    settings_dict = admin_crud.get_all_settings(db)
    return SystemSettings(**settings_dict)


@router.put(
    "/settings",
    response_model=SystemSettings,
    summary="Modifier les paramètres",
)
async def update_system_settings(data: SystemSettings, db: Session = Depends(get_db)):
    """Met à jour les paramètres système."""
    settings_dict = data.model_dump()
    updated = admin_crud.update_all_settings(db, settings_dict)
    return SystemSettings(**updated)


# ============== Cache ==============

@router.get(
    "/cache/stats",
    response_model=CacheStats,
    summary="Statistiques du cache",
)
async def get_cache_stats():
    """Récupère les statistiques du cache Redis."""
    stats = await cache.get_stats()
    return CacheStats(
        connected=stats.get("connected", False),
        keys=stats.get("keys", 0),
        hits=stats.get("hits", 0),
        misses=stats.get("misses", 0),
        memory_used=stats.get("memory_used", "N/A"),
        hit_rate=(
            stats.get("hits", 0) / 
            max(stats.get("hits", 0) + stats.get("misses", 0), 1)
        ),
    )


@router.post(
    "/cache/clear",
    summary="Vider le cache",
)
async def clear_cache(
    domain: Optional[str] = Query(None, description="Domaine à vider (scolarite, recrutement, budget, edt)"),
):
    """Vide le cache (tout ou par domaine)."""
    if domain:
        pattern = f"{domain}:*"
        deleted = await cache.delete_pattern(pattern)
        return {"message": f"Cache {domain} vidé", "keys_deleted": deleted}
    else:
        deleted = await cache.delete_pattern("*")
        return {"message": "Tout le cache a été vidé", "keys_deleted": deleted}


# ============== Jobs ==============

@router.get(
    "/jobs",
    response_model=list[ScheduledJob],
    summary="Jobs planifiés",
)
async def list_scheduled_jobs():
    """Récupère la liste des jobs planifiés (APScheduler)."""
    jobs_raw = scheduler.get_jobs() if settings.cache_enabled else []
    
    jobs = []
    for job in jobs_raw:
        jobs.append(ScheduledJob(
            id=job["id"],
            name=job["name"],
            next_run=datetime.fromisoformat(job["next_run"]) if job.get("next_run") else None,
            enabled=True,
            schedule="Voir configuration",
        ))
    
    # If no jobs from scheduler, show default job list (what would run)
    if not jobs:
        default_jobs = [
            ScheduledJob(
                id="refresh_scolarite",
                name="Rafraîchir données scolarité",
                description="Synchronise les données depuis ScoDoc",
                schedule="Toutes les heures",
                enabled=settings.cache_enabled,
            ),
            ScheduledJob(
                id="refresh_budget",
                name="Rafraîchir données budget",
                description="Recalcule les indicateurs budget",
                schedule="Toutes les 6 heures",
                enabled=settings.cache_enabled,
            ),
            ScheduledJob(
                id="refresh_recrutement",
                name="Rafraîchir données recrutement",
                description="Recalcule les indicateurs recrutement",
                schedule="Toutes les 6 heures",
                enabled=settings.cache_enabled,
            ),
            ScheduledJob(
                id="cleanup_cache",
                name="Nettoyage du cache",
                description="Supprime les clés expirées",
                schedule="Quotidien à minuit",
                enabled=settings.cache_enabled,
            ),
        ]
        return default_jobs
    
    return jobs


@router.post(
    "/jobs/{job_id}/run",
    summary="Exécuter un job",
)
async def run_job_now(job_id: str):
    """Exécute un job planifié immédiatement."""
    try:
        await scheduler.run_job_now(job_id)
        return {"message": f"Job {job_id} exécuté", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Database Seeding ==============

@router.post(
    "/seed",
    summary="Seed database with mock data",
)
async def seed_database_endpoint(
    force: bool = Query(False, description="Force reseed (delete existing data)"),
    db: Session = Depends(get_db),
):
    """
    Seed the database with mock/demo data.
    
    Creates sample users with different permission levels:
    - admin: Superadmin with all permissions
    - chef_rt: RT department admin
    - chef_geii: GEII department admin  
    - enseignant_rt: RT teacher (view scolarite/edt only)
    - secretaire: Secretary (scolarite/recrutement for RT & GEII)
    - pending_user: Inactive account (pending validation)
    
    Also creates mock data for:
    - Budget: 3 years of budget data per department
    - Recrutement: 4 years of Parcoursup data per department
    
    Use force=true to delete existing data and reseed.
    """
    from app.seeds import seed_database
    
    result = seed_database(db, force=force)
    
    if result["skipped"]:
        return {
            "status": "skipped",
            "message": "Database already has data. Use force=true to reseed.",
        }
    
    return {
        "status": "success",
        "message": "Database seeded successfully",
        "data": {
            "users_created": result["users_created"],
            "permissions_created": result["permissions_created"],
            "budgets_created": result["budgets_created"],
            "depenses_created": result["depenses_created"],
            "campagnes_created": result["campagnes_created"],
            "candidats_created": result["candidats_created"],
        },
        "test_accounts": [
            {"login": "admin", "role": "Superadmin (all permissions)"},
            {"login": "chef_rt", "role": "RT department admin"},
            {"login": "chef_geii", "role": "GEII department admin"},
            {"login": "enseignant_rt", "role": "RT teacher (view scolarite/edt only)"},
            {"login": "secretaire", "role": "Secretary (scolarite/recrutement for RT & GEII)"},
            {"login": "pending_user", "role": "Inactive account (pending validation)"},
        ],
    }
