"""CRUD operations for Admin settings and data sources."""

import json
from typing import Optional
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.models.db_models import SystemSettingsDB, DataSourceDB


# ==================== SYSTEM SETTINGS ====================

DEFAULT_SETTINGS = {
    "dashboard_title": ("Dashboard Département", "Titre affiché en haut du dashboard"),
    "department_name": ("Département RT", "Nom du département"),
    "academic_year": ("2024-2025", "Année universitaire en cours"),
    "cache_enabled": ("true", "Activer le cache Redis"),
    "cache_ttl_default": ("3600", "TTL du cache par défaut (secondes)"),
    "items_per_page": ("25", "Nombre d'éléments par page"),
    "default_chart_type": ("bar", "Type de graphique par défaut"),
    "date_format": ("DD/MM/YYYY", "Format de date"),
    "email_notifications": ("false", "Activer les notifications email"),
    "notification_email": ("", "Email pour les notifications"),
}


def init_default_settings(db: Session) -> None:
    """Initialize default settings if not present."""
    for key, (value, description) in DEFAULT_SETTINGS.items():
        existing = db.query(SystemSettingsDB).filter(SystemSettingsDB.key == key).first()
        if not existing:
            setting = SystemSettingsDB(key=key, value=value, description=description)
            db.add(setting)
    db.commit()


def get_setting(db: Session, key: str) -> Optional[str]:
    """Get a single setting value."""
    setting = db.query(SystemSettingsDB).filter(SystemSettingsDB.key == key).first()
    if setting:
        return setting.value
    # Return default if exists
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key][0]
    return None


def get_all_settings(db: Session) -> dict:
    """Get all settings as a dictionary."""
    # First ensure defaults are initialized
    init_default_settings(db)
    
    settings = db.query(SystemSettingsDB).all()
    result = {}
    for s in settings:
        # Convert boolean strings
        if s.value in ("true", "false"):
            result[s.key] = s.value == "true"
        elif s.value and s.value.isdigit():
            result[s.key] = int(s.value)
        else:
            result[s.key] = s.value
    return result


def update_setting(db: Session, key: str, value: str) -> SystemSettingsDB:
    """Update a single setting."""
    setting = db.query(SystemSettingsDB).filter(SystemSettingsDB.key == key).first()
    if setting:
        setting.value = value
        setting.date_modification = date.today()
    else:
        description = DEFAULT_SETTINGS.get(key, (None, None))[1]
        setting = SystemSettingsDB(key=key, value=value, description=description)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def update_all_settings(db: Session, settings_data: dict) -> dict:
    """Update multiple settings at once."""
    for key, value in settings_data.items():
        # Convert boolean/int to string for storage
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, int):
            value = str(value)
        update_setting(db, key, str(value) if value is not None else "")
    return get_all_settings(db)


# ==================== DATA SOURCES ====================

DEFAULT_SOURCES = [
    {
        "source_id": "scodoc-1",
        "name": "ScoDoc Principal",
        "type": "scodoc",
        "status": "inactive",
        "description": "API ScoDoc pour les données de scolarité",
        "enabled": 1,
        "auto_sync": 1,
        "sync_interval_hours": 1,
    },
    {
        "source_id": "parcoursup-1",
        "name": "Parcoursup",
        "type": "parcoursup",
        "status": "active",
        "description": "Import des fichiers CSV Parcoursup",
        "enabled": 1,
        "auto_sync": 0,
    },
    {
        "source_id": "excel-budget",
        "name": "Budget Excel",
        "type": "excel",
        "status": "active",
        "description": "Fichiers Excel pour le suivi budgétaire",
        "enabled": 1,
        "auto_sync": 0,
    },
    {
        "source_id": "excel-edt",
        "name": "EDT Excel",
        "type": "excel",
        "status": "inactive",
        "description": "Fichiers Excel pour les emplois du temps",
        "enabled": 1,
        "auto_sync": 0,
    },
]


def init_default_sources(db: Session) -> None:
    """Initialize default data sources if not present."""
    for src_data in DEFAULT_SOURCES:
        existing = db.query(DataSourceDB).filter(
            DataSourceDB.source_id == src_data["source_id"]
        ).first()
        if not existing:
            source = DataSourceDB(**src_data)
            db.add(source)
    db.commit()


def get_all_sources(db: Session, source_type: Optional[str] = None, enabled: Optional[bool] = None) -> list[DataSourceDB]:
    """Get all data sources with optional filters."""
    init_default_sources(db)
    
    query = db.query(DataSourceDB)
    if source_type:
        query = query.filter(DataSourceDB.type == source_type)
    if enabled is not None:
        query = query.filter(DataSourceDB.enabled == (1 if enabled else 0))
    return query.all()


def get_source(db: Session, source_id: str) -> Optional[DataSourceDB]:
    """Get a data source by ID."""
    return db.query(DataSourceDB).filter(DataSourceDB.source_id == source_id).first()


def create_source(db: Session, data: dict) -> DataSourceDB:
    """Create a new data source."""
    source = DataSourceDB(**data)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_source(db: Session, source_id: str, data: dict) -> Optional[DataSourceDB]:
    """Update a data source."""
    source = get_source(db, source_id)
    if not source:
        return None
    
    for key, value in data.items():
        if hasattr(source, key) and key != "id":
            setattr(source, key, value)
    
    source.date_modification = date.today()
    db.commit()
    db.refresh(source)
    return source


def delete_source(db: Session, source_id: str) -> bool:
    """Delete a data source."""
    source = get_source(db, source_id)
    if not source:
        return False
    db.delete(source)
    db.commit()
    return True


def update_source_sync_status(
    db: Session, 
    source_id: str, 
    success: bool, 
    records_count: int = 0, 
    error: Optional[str] = None
) -> Optional[DataSourceDB]:
    """Update source after sync attempt."""
    source = get_source(db, source_id)
    if not source:
        return None
    
    source.last_sync = date.today()
    source.status = "active" if success else "error"
    source.records_count = records_count
    source.last_error = error
    source.date_modification = date.today()
    
    db.commit()
    db.refresh(source)
    return source


def source_to_dict(source: DataSourceDB) -> dict:
    """Convert DataSourceDB to dictionary for API response."""
    return {
        "id": source.source_id,
        "name": source.name,
        "type": source.type,
        "status": source.status,
        "description": source.description,
        "base_url": source.base_url,
        "enabled": bool(source.enabled),
        "auto_sync": bool(source.auto_sync),
        "sync_interval_hours": source.sync_interval_hours,
        "last_sync": source.last_sync.isoformat() if source.last_sync else None,
        "last_error": source.last_error,
        "records_count": source.records_count,
    }
