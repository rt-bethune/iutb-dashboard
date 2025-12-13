"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Dept Dashboard API"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API
    api_prefix: str = "/api"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # ScoDoc Configuration
    scodoc_base_url: Optional[str] = None
    scodoc_username: Optional[str] = None
    scodoc_password: Optional[str] = None
    scodoc_department: Optional[str] = None
    
    # Database (optional - for caching)
    database_url: Optional[str] = None
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    cache_enabled: bool = True
    
    # Cache TTL (en secondes)
    cache_ttl_scolarite: int = 3600      # 1 heure
    cache_ttl_recrutement: int = 86400   # 24 heures
    cache_ttl_budget: int = 86400        # 24 heures
    cache_ttl_edt: int = 3600            # 1 heure
    
    # JWT Auth
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
