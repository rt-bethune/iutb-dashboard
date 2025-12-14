"""Scolarité API routes."""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
import logging

from app.models.scolarite import ScolariteIndicators, Etudiant, ModuleStats
from app.adapters.scodoc import ScoDocAdapter, MockScoDocAdapter
from app.api.deps import DepartmentDep, get_scodoc_adapter_for_department
from app.services import cache, CacheKeys
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _get_adapter(department: str):
    """Get the appropriate ScoDoc adapter based on configuration."""
    if all([settings.scodoc_base_url, settings.scodoc_username, 
            settings.scodoc_password]):
        logger.info(f"Using real ScoDoc adapter for department {department}")
        return get_scodoc_adapter_for_department(department)
    else:
        logger.info("Using mock ScoDoc adapter (credentials not configured)")
        return MockScoDocAdapter()


@router.get(
    "/indicators", 
    response_model=ScolariteIndicators,
    summary="Indicateurs scolarité",
    response_description="Indicateurs agrégés de scolarité"
)
async def get_scolarite_indicators(
    department: DepartmentDep,
    annee: Optional[str] = Query(None, description="Année universitaire (ex: 2024-2025)", example="2024-2025"),
    refresh: bool = Query(False, description="Force le rafraîchissement du cache"),
):
    """
    Récupère les indicateurs agrégés de scolarité.
    
    **Données retournées :**
    - Nombre total d'étudiants
    - Moyenne générale
    - Taux de réussite global
    - Taux d'absentéisme
    - Statistiques par module et par semestre
    - Évolution des effectifs
    
    **Cache :** Données mises en cache pendant 1 heure.
    Utilisez `refresh=true` pour forcer la mise à jour.
    """
    adapter = _get_adapter(department)
    try:
        cache_key = CacheKeys.scolarite_indicators(annee, department)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, ScolariteIndicators)
            if cached:
                return cached
        
        # Fetch fresh data
        data = await adapter.get_data(annee=annee)
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_scolarite)
        
        return data
    except Exception as e:
        logger.error(f"Error fetching scolarite indicators for {department}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()


@router.get(
    "/etudiants", 
    response_model=list[Etudiant],
    summary="Liste des étudiants",
    response_description="Liste des étudiants avec filtres optionnels"
)
async def get_etudiants(
    department: DepartmentDep,
    formation: Optional[str] = Query(None, description="Filtrer par formation", example="BUT RT"),
    semestre: Optional[str] = Query(None, description="Filtrer par semestre", example="S1"),
    limit: int = Query(100, le=500, ge=1, description="Nombre maximum de résultats"),
):
    """
    Récupère la liste des étudiants.
    
    **Filtres disponibles :**
    - `formation` : Nom de la formation (ex: "BUT RT", "LP Cyber")
    - `semestre` : Semestre (ex: "S1", "S2", ...)
    - `limit` : Limite le nombre de résultats (max 500)
    """
    adapter = _get_adapter(department)
    try:
        # Try to get real students from ScoDoc
        if isinstance(adapter, ScoDocAdapter):
            etudiants = await adapter.get_etudiants()
        else:
            # Mock data
            etudiants = [
                Etudiant(
                    id=str(i),
                    nom=f"Nom{i}",
                    prenom=f"Prénom{i}",
                    email=f"etudiant{i}@example.com",
                    formation=f"BUT {department}",
                    semestre=f"S{(i % 6) + 1}",
                    groupe=f"G{(i % 4) + 1}",
                )
                for i in range(1, limit + 1)
            ]
        
        # Apply filters
        if formation:
            etudiants = [e for e in etudiants if formation.lower() in (e.formation or "").lower()]
        if semestre:
            etudiants = [e for e in etudiants if e.semestre == semestre]
        
        return etudiants[:limit]
    except Exception as e:
        logger.error(f"Error fetching etudiants for {department}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()


@router.get(
    "/modules", 
    response_model=list[ModuleStats],
    summary="Statistiques par module",
    response_description="Liste des statistiques par module"
)
async def get_modules_stats(
    department: DepartmentDep,
    semestre: Optional[str] = Query(None, description="Filtrer par semestre", example="S1"),
):
    """
    Récupère les statistiques par module.
    
    **Données par module :**
    - Code et nom du module
    - Moyenne de la classe
    - Taux de réussite
    - Nombre d'étudiants
    - Écart-type, note min/max
    """
    adapter = _get_adapter(department)
    try:
        # Get from indicators
        indicators = await adapter.get_data()
        modules = indicators.modules_stats
        
        if semestre:
            # Filter by semester prefix (e.g., "S1" modules start with "R1")
            modules = [m for m in modules if m.code.startswith(f"R{semestre[-1]}")]
        
        return modules
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()


@router.get(
    "/effectifs",
    summary="Évolution des effectifs",
    response_description="Données d'évolution des effectifs"
)
async def get_effectifs_evolution(
    department: DepartmentDep,
):
    """
    Récupère l'évolution des effectifs sur plusieurs années.
    
    **Données retournées :**
    - `evolution` : Effectifs par année
    - `par_formation` : Répartition par formation
    - `par_semestre` : Répartition par semestre
    """
    adapter = _get_adapter(department)
    try:
        indicators = await adapter.get_data()
        return {
            "evolution": indicators.evolution_effectifs,
            "par_formation": indicators.etudiants_par_formation,
            "par_semestre": indicators.etudiants_par_semestre,
        }
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()


@router.get(
    "/reussite",
    summary="Taux de réussite",
    response_description="Taux de réussite par semestre et module"
)
async def get_taux_reussite(
    department: DepartmentDep,
    annee: Optional[str] = Query(None, description="Année universitaire", example="2024-2025"),
):
    """
    Récupère les taux de réussite détaillés.
    
    **Données retournées :**
    - `global` : Taux de réussite global
    - `par_semestre` : Taux par semestre
    - `par_module` : Taux par module
    """
    adapter = _get_adapter(department)
    try:
        indicators = await adapter.get_data()
        
        return {
            "global": indicators.taux_reussite_global,
            "par_semestre": {
                s.code: s.taux_reussite for s in indicators.semestres_stats
            },
            "par_module": {
                m.code: m.taux_reussite for m in indicators.modules_stats
            },
        }
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()


@router.get(
    "/health",
    summary="État de la connexion ScoDoc",
    response_description="Vérifie la connexion à l'API ScoDoc"
)
async def check_scodoc_health(
    department: DepartmentDep,
):
    """
    Vérifie l'état de la connexion à l'API ScoDoc.
    
    **Retourne :**
    - `status` : "ok" si connecté, "error" sinon
    - `source` : "scodoc" ou "mock"
    - `department` : Département configuré
    - `message` : Message d'erreur si applicable
    """
    adapter = _get_adapter(department)
    try:
        is_real = isinstance(adapter, ScoDocAdapter)
        
        if is_real:
            health_ok = await adapter.health_check()
            return {
                "status": "ok" if health_ok else "error",
                "source": "scodoc",
                "department": department,
                "base_url": settings.scodoc_base_url,
                "message": f"Connecté à ScoDoc ({department})" if health_ok else "Échec de connexion à ScoDoc"
            }
        else:
            return {
                "status": "ok",
                "source": "mock",
                "department": department,
                "message": "Utilisation des données de démonstration (ScoDoc non configuré)"
            }
    except Exception as e:
        return {
            "status": "error",
            "source": "unknown",
            "department": department,
            "message": str(e)
        }
    finally:
        if hasattr(adapter, 'close'):
            await adapter.close()
