"""Administration models."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """Types de sources de données."""
    SCODOC = "scodoc"
    PARCOURSUP = "parcoursup"
    EXCEL = "excel"
    APOGEE = "apogee"


class DataSourceStatus(str, Enum):
    """Statut d'une source de données."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"


class DataSourceConfig(BaseModel):
    """Configuration d'une source de données."""
    id: str
    name: str
    type: DataSourceType
    status: DataSourceStatus = DataSourceStatus.INACTIVE
    description: Optional[str] = None
    
    # Configuration spécifique
    base_url: Optional[str] = None
    username: Optional[str] = None
    # password non exposé
    
    # Métadonnées
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    records_count: Optional[int] = None
    
    # Paramètres
    enabled: bool = True
    auto_sync: bool = True
    sync_interval_hours: int = 1


class DataSourceCreate(BaseModel):
    """Création d'une source de données."""
    name: str
    type: DataSourceType
    description: Optional[str] = None
    base_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: bool = True
    auto_sync: bool = True
    sync_interval_hours: int = 1


class DataSourceUpdate(BaseModel):
    """Mise à jour d'une source de données."""
    name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enabled: Optional[bool] = None
    auto_sync: Optional[bool] = None
    sync_interval_hours: Optional[int] = None


class SystemSettings(BaseModel):
    """Paramètres système du dashboard."""
    # Général
    dashboard_title: str = "Dashboard Département"
    department_name: str = "Département RT"
    academic_year: str = "2024-2025"
    
    # Cache
    cache_enabled: bool = True
    cache_ttl_default: int = 3600
    
    # Affichage
    default_chart_type: str = "bar"
    items_per_page: int = 25
    date_format: str = "DD/MM/YYYY"
    
    # Notifications
    email_notifications: bool = False
    notification_email: Optional[str] = None


class ScheduledJob(BaseModel):
    """Job planifié."""
    id: str
    name: str
    description: Optional[str] = None
    schedule: str  # Cron expression ou interval
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    enabled: bool = True


class CacheStats(BaseModel):
    """Statistiques du cache."""
    connected: bool
    keys: int = 0
    hits: int = 0
    misses: int = 0
    memory_used: str = "N/A"
    hit_rate: float = 0.0


class SyncResult(BaseModel):
    """Résultat d'une synchronisation."""
    source_id: str
    source_name: str
    success: bool
    records_synced: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ActivityLog(BaseModel):
    """Log d'activité."""
    id: str
    timestamp: datetime
    action: str
    user: Optional[str] = None
    details: Optional[str] = None
    source: Optional[str] = None
    status: str = "info"  # info, warning, error, success


class AdminDashboard(BaseModel):
    """Vue d'ensemble admin."""
    # Sources
    total_sources: int = 0
    active_sources: int = 0
    sources_in_error: int = 0
    
    # Cache
    cache_stats: CacheStats
    
    # Jobs
    scheduled_jobs: int = 0
    jobs_running: int = 0
    
    # Dernières activités
    recent_syncs: list[SyncResult] = []
    recent_logs: list[ActivityLog] = []
