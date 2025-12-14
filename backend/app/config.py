"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from functools import lru_cache
import os


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
    
    # Database
    database_url: Optional[str] = None  # If None, uses SQLite
    
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
    access_token_expire_minutes: int = 480  # 8 hours
    
    # CAS Configuration
    cas_server_url: str = "https://sso.univ-artois.fr/cas"
    cas_service_url: str = "http://localhost:8000/api/auth/cas/callback"
    cas_use_mock: bool = True  # Set to False in production
    
    # Frontend URL (for redirects)
    frontend_url: str = "http://localhost:5173"
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is changed in production."""
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        allow_insecure = os.getenv('ALLOW_INSECURE', 'false').lower() == 'true'
        if not debug and not allow_insecure:
            if v == "your-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed in production! "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v
    
    @field_validator('cas_use_mock')
    @classmethod
    def validate_cas_mock(cls, v: bool) -> bool:
        """Warn if CAS mock is enabled in production."""
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        allow_insecure = os.getenv('ALLOW_INSECURE', 'false').lower() == 'true'
        if not debug and not allow_insecure and v:
            raise ValueError(
                "CAS_USE_MOCK must be False in production! "
                "Set ALLOW_INSECURE=true for local Docker testing."
            )
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
