"""Administration API routes."""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
from datetime import datetime
import uuid

from app.models.admin import (
    DataSourceConfig,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceType,
    DataSourceStatus,
    SystemSettings,
    ScheduledJob,
    CacheStats,
    SyncResult,
    ActivityLog,
    AdminDashboard,
)
from app.services import cache, scheduler, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# In-memory storage for demo (use database in production)
_data_sources: dict[str, DataSourceConfig] = {}
_system_settings = SystemSettings()
_activity_logs: list[ActivityLog] = []
_sync_results: list[SyncResult] = []


def _init_default_sources():
    """Initialize default data sources."""
    if not _data_sources:
        defaults = [
            DataSourceConfig(
                id="scodoc-1",
                name="ScoDoc Principal",
                type=DataSourceType.SCODOC,
                status=DataSourceStatus.ACTIVE,
                description="API ScoDoc pour les données de scolarité",
                base_url=settings.scodoc_base_url,
                enabled=True,
                auto_sync=True,
                sync_interval_hours=1,
            ),
            DataSourceConfig(
                id="parcoursup-1",
                name="Parcoursup",
                type=DataSourceType.PARCOURSUP,
                status=DataSourceStatus.ACTIVE,
                description="Import des fichiers CSV Parcoursup",
                enabled=True,
                auto_sync=False,
            ),
            DataSourceConfig(
                id="excel-budget",
                name="Budget Excel",
                type=DataSourceType.EXCEL,
                status=DataSourceStatus.ACTIVE,
                description="Fichiers Excel pour le suivi budgétaire",
                enabled=True,
                auto_sync=False,
            ),
            DataSourceConfig(
                id="excel-edt",
                name="EDT Excel",
                type=DataSourceType.EXCEL,
                status=DataSourceStatus.ACTIVE,
                description="Fichiers Excel pour les emplois du temps",
                enabled=True,
                auto_sync=False,
            ),
        ]
        for source in defaults:
            _data_sources[source.id] = source


_init_default_sources()


def _add_log(action: str, details: str = None, status: str = "info", source: str = None):
    """Add activity log."""
    log = ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        action=action,
        details=details,
        status=status,
        source=source,
    )
    _activity_logs.insert(0, log)
    # Keep only last 100 logs
    if len(_activity_logs) > 100:
        _activity_logs.pop()


# ============== Dashboard Admin ==============

@router.get(
    "/dashboard",
    response_model=AdminDashboard,
    summary="Vue d'ensemble administration",
)
async def get_admin_dashboard():
    """
    Récupère la vue d'ensemble de l'administration.
    
    Inclut les statistiques des sources, du cache et des jobs.
    """
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
        total_sources=len(_data_sources),
        active_sources=sum(1 for s in _data_sources.values() if s.status == DataSourceStatus.ACTIVE),
        sources_in_error=sum(1 for s in _data_sources.values() if s.status == DataSourceStatus.ERROR),
        cache_stats=cache_stats,
        scheduled_jobs=len(jobs),
        jobs_running=0,
        recent_syncs=_sync_results[:5],
        recent_logs=_activity_logs[:10],
    )


# ============== Data Sources ==============

@router.get(
    "/sources",
    response_model=list[DataSourceConfig],
    summary="Liste des sources de données",
)
async def list_data_sources(
    type: Optional[DataSourceType] = Query(None, description="Filtrer par type"),
    enabled: Optional[bool] = Query(None, description="Filtrer par statut actif"),
):
    """Récupère la liste des sources de données configurées."""
    sources = list(_data_sources.values())
    
    if type:
        sources = [s for s in sources if s.type == type]
    if enabled is not None:
        sources = [s for s in sources if s.enabled == enabled]
    
    return sources


@router.get(
    "/sources/{source_id}",
    response_model=DataSourceConfig,
    summary="Détails d'une source",
)
async def get_data_source(source_id: str):
    """Récupère les détails d'une source de données."""
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return _data_sources[source_id]


@router.post(
    "/sources",
    response_model=DataSourceConfig,
    summary="Créer une source",
)
async def create_data_source(data: DataSourceCreate):
    """Crée une nouvelle source de données."""
    source_id = f"{data.type.value}-{uuid.uuid4().hex[:8]}"
    
    source = DataSourceConfig(
        id=source_id,
        name=data.name,
        type=data.type,
        status=DataSourceStatus.CONFIGURING,
        description=data.description,
        base_url=data.base_url,
        username=data.username,
        enabled=data.enabled,
        auto_sync=data.auto_sync,
        sync_interval_hours=data.sync_interval_hours,
    )
    
    _data_sources[source_id] = source
    _add_log("Source créée", f"Source {data.name} ({data.type.value})", "success")
    
    return source


@router.put(
    "/sources/{source_id}",
    response_model=DataSourceConfig,
    summary="Modifier une source",
)
async def update_data_source(source_id: str, data: DataSourceUpdate):
    """Met à jour une source de données."""
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    source = _data_sources[source_id]
    update_data = data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field != "password":  # Don't expose password
            setattr(source, field, value)
    
    _add_log("Source modifiée", f"Source {source.name} mise à jour", "info", source_id)
    
    return source


@router.delete(
    "/sources/{source_id}",
    summary="Supprimer une source",
)
async def delete_data_source(source_id: str):
    """Supprime une source de données."""
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    source = _data_sources.pop(source_id)
    _add_log("Source supprimée", f"Source {source.name} supprimée", "warning", source_id)
    
    return {"message": "Source supprimée", "id": source_id}


@router.post(
    "/sources/{source_id}/sync",
    response_model=SyncResult,
    summary="Synchroniser une source",
)
async def sync_data_source(source_id: str, background_tasks: BackgroundTasks):
    """Déclenche une synchronisation manuelle d'une source."""
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    source = _data_sources[source_id]
    start_time = datetime.now()
    
    # Simulate sync (in production, call actual adapter)
    try:
        # Mock sync result
        result = SyncResult(
            source_id=source_id,
            source_name=source.name,
            success=True,
            records_synced=150,
            duration_seconds=2.5,
        )
        
        source.last_sync = datetime.now()
        source.status = DataSourceStatus.ACTIVE
        source.records_count = 150
        
        _sync_results.insert(0, result)
        if len(_sync_results) > 50:
            _sync_results.pop()
        
        _add_log("Synchronisation", f"Source {source.name} synchronisée (150 enregistrements)", "success", source_id)
        
        return result
    except Exception as e:
        source.status = DataSourceStatus.ERROR
        source.last_error = str(e)
        
        result = SyncResult(
            source_id=source_id,
            source_name=source.name,
            success=False,
            error=str(e),
        )
        _sync_results.insert(0, result)
        _add_log("Erreur sync", f"Échec sync {source.name}: {str(e)}", "error", source_id)
        
        return result


@router.post(
    "/sources/{source_id}/test",
    summary="Tester la connexion",
)
async def test_data_source_connection(source_id: str):
    """Teste la connexion à une source de données."""
    if source_id not in _data_sources:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    source = _data_sources[source_id]
    
    # Simulate connection test
    return {
        "source_id": source_id,
        "source_name": source.name,
        "connection_ok": True,
        "latency_ms": 45,
        "message": "Connexion réussie",
    }


# ============== Settings ==============

@router.get(
    "/settings",
    response_model=SystemSettings,
    summary="Paramètres système",
)
async def get_system_settings():
    """Récupère les paramètres système du dashboard."""
    return _system_settings


@router.put(
    "/settings",
    response_model=SystemSettings,
    summary="Modifier les paramètres",
)
async def update_system_settings(data: SystemSettings):
    """Met à jour les paramètres système."""
    global _system_settings
    _system_settings = data
    _add_log("Paramètres modifiés", "Paramètres système mis à jour", "info")
    return _system_settings


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
        _add_log("Cache vidé", f"Cache {domain} vidé ({deleted} clés)", "warning")
        return {"message": f"Cache {domain} vidé", "keys_deleted": deleted}
    else:
        deleted = await cache.delete_pattern("*")
        _add_log("Cache vidé", f"Tout le cache vidé ({deleted} clés)", "warning")
        return {"message": "Tout le cache a été vidé", "keys_deleted": deleted}


# ============== Jobs ==============

@router.get(
    "/jobs",
    response_model=list[ScheduledJob],
    summary="Jobs planifiés",
)
async def list_scheduled_jobs():
    """Récupère la liste des jobs planifiés."""
    jobs_raw = scheduler.get_jobs() if settings.cache_enabled else []
    
    jobs = []
    for job in jobs_raw:
        jobs.append(ScheduledJob(
            id=job["id"],
            name=job["name"],
            next_run=datetime.fromisoformat(job["next_run"]) if job["next_run"] else None,
            enabled=True,
            schedule="Voir configuration",
        ))
    
    return jobs


@router.post(
    "/jobs/{job_id}/run",
    summary="Exécuter un job",
)
async def run_job_now(job_id: str):
    """Exécute un job planifié immédiatement."""
    try:
        await scheduler.run_job_now(job_id)
        _add_log("Job exécuté", f"Job {job_id} exécuté manuellement", "success")
        return {"message": f"Job {job_id} exécuté", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Logs ==============

@router.get(
    "/logs",
    response_model=list[ActivityLog],
    summary="Logs d'activité",
)
async def get_activity_logs(
    limit: int = Query(50, le=100, description="Nombre de logs à retourner"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
):
    """Récupère les logs d'activité."""
    logs = _activity_logs[:limit]
    
    if status:
        logs = [l for l in logs if l.status == status]
    
    return logs
