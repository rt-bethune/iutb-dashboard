"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import get_settings
from app.api.routes import scolarite, recrutement, budget, edt, upload, admin
from app.api.routes import budget_admin, recrutement_admin
from app.services import cache, scheduler
from app.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    init_db()  # Initialize database tables
    await cache.connect()
    if settings.cache_enabled:
        scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()
    await cache.disconnect()


# OpenAPI customization
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="""
## API Dashboard Département

API d'agrégation de données pour le dashboard du département d'enseignement.

### Sources de données
- **ScoDoc** : Données de scolarité (étudiants, notes, absences)
- **Parcoursup** : Données de recrutement (candidatures, admissions)
- **Excel/CSV** : Données budget et emploi du temps

### Fonctionnalités
- 📊 Indicateurs agrégés par domaine (Scolarité, Recrutement, Budget, EDT)
- 🔄 Cache Redis avec refresh automatique
- 📁 Import de fichiers Excel/CSV
- 📈 Évolutions historiques

### Authentification
L'API utilise des tokens JWT pour l'authentification (en développement).

### Cache
Les données sont mises en cache avec différents TTL :
- Scolarité : 1 heure
- Recrutement : 24 heures
- Budget : 24 heures
- EDT : 1 heure

Utilisez le paramètre `?refresh=true` pour forcer un rafraîchissement du cache.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Scolarité",
                "description": "Gestion des données de scolarité : étudiants, notes, réussite, absences",
            },
            {
                "name": "Recrutement",
                "description": "Données Parcoursup : candidatures, admissions, origines des candidats",
            },
            {
                "name": "Budget",
                "description": "Suivi budgétaire : allocations, dépenses, taux d'exécution",
            },
            {
                "name": "EDT",
                "description": "Emploi du temps : charges enseignants, occupation salles, heures",
            },
            {
                "name": "Upload",
                "description": "Import de fichiers Excel et CSV",
            },
            {
                "name": "Administration",
                "description": "Gestion des sources de données, cache, jobs et paramètres système",
            },
        ],
    )
    
    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "Support API",
        "email": "support@departement.fr",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Serveur de développement"},
        {"url": "https://api.departement.fr", "description": "Serveur de production"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API d'agrégation pour le dashboard du département",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.openapi = custom_openapi

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    scolarite.router,
    prefix=f"{settings.api_prefix}/scolarite",
    tags=["Scolarité"],
)
app.include_router(
    recrutement.router,
    prefix=f"{settings.api_prefix}/recrutement",
    tags=["Recrutement"],
)
app.include_router(
    budget.router,
    prefix=f"{settings.api_prefix}/budget",
    tags=["Budget"],
)
app.include_router(
    edt.router,
    prefix=f"{settings.api_prefix}/edt",
    tags=["EDT"],
)
app.include_router(
    upload.router,
    prefix=f"{settings.api_prefix}/upload",
    tags=["Upload"],
)
app.include_router(
    admin.router,
    prefix=f"{settings.api_prefix}/admin",
    tags=["Administration"],
)
app.include_router(
    budget_admin.router,
    prefix=f"{settings.api_prefix}/admin/budget",
    tags=["Admin Budget"],
)
app.include_router(
    recrutement_admin.router,
    prefix=f"{settings.api_prefix}/admin/recrutement",
    tags=["Admin Recrutement"],
)


@app.get("/", tags=["Health"], summary="Root endpoint")
async def root():
    """
    Root endpoint - retourne les informations de base de l'API.
    
    Utilisé pour vérifier que l'API est accessible.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """
    Endpoint de santé détaillé.
    
    Retourne:
    - Status de l'API
    - État du cache Redis
    - Liste des jobs planifiés
    """
    cache_stats = await cache.get_stats()
    return {
        "status": "healthy",
        "cache": cache_stats,
        "scheduler_jobs": scheduler.get_jobs() if settings.cache_enabled else [],
    }

