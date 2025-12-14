"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from app.config import get_settings

settings = get_settings()

# Database configuration
if settings.database_url:
    # Production: Use PostgreSQL or other database from DATABASE_URL
    DATABASE_URL = settings.database_url
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=5,
        max_overflow=10,
        echo=settings.debug,
    )
else:
    # Development: Use SQLite
    DATABASE_DIR = Path(__file__).parent.parent / "data"
    DATABASE_DIR.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///{DATABASE_DIR}/dashboard.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite
        echo=settings.debug,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.models import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
