"""Scolarité API routes."""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Any, Optional
import logging

from app.models.competences import (
    Competence,
    UEEtudiant,
    UEStats,
    NiveauCompetence,
    UEValidation,
)
from app.models.scolarite import ScolariteIndicators, Etudiant, ModuleStats
from app.models.db_models import UserDB
from app.adapters.scodoc import ScoDocAdapter, MockScoDocAdapter
from app.api.deps import (
    DepartmentDep, get_scodoc_adapter_for_department,
    require_view_scolarite, require_edit_scolarite, require_import
)
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


def _get_mock_competences() -> list[Competence]:
    return [
        Competence(
            code="C1",
            nom="Administrer",
            description="Administrer les réseaux et l'internet",
            niveaux=[
                NiveauCompetence(niveau=1, nom="Niveau 1"),
                NiveauCompetence(niveau=2, nom="Niveau 2"),
                NiveauCompetence(niveau=3, nom="Niveau 3"),
            ],
        ),
        Competence(
            code="C2",
            nom="Connecter",
            description="Connecter les entreprises et les usagers",
            niveaux=[
                NiveauCompetence(niveau=1, nom="Niveau 1"),
                NiveauCompetence(niveau=2, nom="Niveau 2"),
                NiveauCompetence(niveau=3, nom="Niveau 3"),
            ],
        ),
        Competence(
            code="C3",
            nom="Programmer",
            description="Créer des outils et applications informatiques",
            niveaux=[
                NiveauCompetence(niveau=1, nom="Niveau 1"),
                NiveauCompetence(niveau=2, nom="Niveau 2"),
                NiveauCompetence(niveau=3, nom="Niveau 3"),
            ],
        ),
    ]


def _parse_referentiel_competences(raw: Any) -> list[Competence]:
    if not raw:
        return []

    data: Any = raw
    if isinstance(raw, dict):
        data = raw.get("competences") or raw.get("data") or raw.get("referentiel") or []

    if not isinstance(data, list):
        return []

    competences: list[Competence] = []
    for item in data:
        if not isinstance(item, dict):
            continue

        code = str(item.get("code") or item.get("acronyme") or item.get("id") or "").strip()
        nom = str(item.get("nom") or item.get("libelle") or item.get("titre") or code).strip()
        description = item.get("description") if isinstance(item.get("description"), str) else None

        if not code:
            code = nom or "UNKNOWN"
        if not nom:
            nom = code

        niveaux: list[NiveauCompetence] = []
        raw_niveaux = item.get("niveaux") or item.get("levels") or []
        if isinstance(raw_niveaux, list):
            for niv in raw_niveaux:
                if not isinstance(niv, dict):
                    continue
                niveau_val = niv.get("niveau") or niv.get("level") or niv.get("id")
                try:
                    niveau_int = int(niveau_val)
                except (TypeError, ValueError):
                    continue
                niveaux.append(
                    NiveauCompetence(
                        niveau=niveau_int,
                        nom=str(niv.get("nom") or niv.get("libelle") or niv.get("titre") or f"Niveau {niveau_int}"),
                        description=niv.get("description") if isinstance(niv.get("description"), str) else None,
                    )
                )

        competences.append(
            Competence(
                code=code,
                nom=nom,
                description=description,
                niveaux=niveaux,
            )
        )

    return competences


def _bucket_taux(taux: float) -> str:
    if taux < 0.25:
        return "0-25%"
    if taux < 0.50:
        return "25-50%"
    if taux < 0.75:
        return "50-75%"
    return "75-100%"


def _parse_semestre_num(semestre: Optional[str]) -> Optional[int]:
    if not semestre:
        return None
    digits = "".join(ch for ch in str(semestre) if ch.isdigit())
    try:
        return int(digits) if digits else None
    except ValueError:
        return None


def _annee_from_semestre(semestre_num: Optional[int]) -> Optional[int]:
    if not semestre_num:
        return None
    return (semestre_num + 1) // 2


def _mock_competence_etudiant(etudiant_id: str, *, niveau: Optional[int] = None) -> UEEtudiant:
    """Generate mock UE data for a student."""
    from app.models.competences import UEValidation
    
    annee = niveau or 1
    seed = sum(ord(c) for c in etudiant_id)

    ue_validations = []
    nb_valid = 0
    # Generate 3 UEs per semester
    for idx in range(1, 4):
        moyenne = 8.0 + ((seed + idx * 5) % 90) / 10.0
        valide = moyenne >= 10.0
        if valide:
            nb_valid += 1
        ue_validations.append(
            UEValidation(
                ue_code=f"UE{annee * 2}{idx}",
                ue_titre=f"Unité d'enseignement {idx}",
                moyenne=round(moyenne, 2),
                valide=valide,
                semestre=f"S{annee * 2}",
            )
        )

    nb_ues = len(ue_validations)
    taux = (nb_valid / nb_ues) if nb_ues else 0.0
    moy_gen = sum(v.moyenne for v in ue_validations if v.moyenne) / nb_ues if nb_ues else None

    return UEEtudiant(
        etudiant_id=etudiant_id,
        nom=f"Nom{etudiant_id}",
        prenom=f"Prénom{etudiant_id}",
        formation="BUT RT",
        semestre=f"S{annee * 2}",
        nb_ues=nb_ues,
        nb_ues_validees=nb_valid,
        taux_validation=round(taux, 3),
        valide=taux > 0.5,
        moyenne_generale=round(moy_gen, 2) if moy_gen else None,
        ue_validations=ue_validations,
    )


def _mock_competences_etudiants(limit: int, *, niveau: Optional[int] = None) -> list[UEEtudiant]:
    results = []
    for i in range(1, limit + 1):
        detail = _mock_competence_etudiant(str(i), niveau=niveau)
        results.append(detail.model_copy(update={"ue_validations": []}))
    return results


async def _fetch_ue_data_from_scodoc(
    adapter: ScoDocAdapter,
    niveau: Optional[int] = None,
    *,
    include_ue_validations: bool = False,
) -> list[UEEtudiant]:
    """
    Fetch UE data from ScoDoc using the efficient resultats endpoint.
    
    SIMPLIFIED: Uses UEs directly from formsemestre_resultats without
    trying to map to competences.
    
    Args:
        adapter: ScoDocAdapter instance (must be authenticated)
        niveau: Optional BUT year (1-3) to filter by
        include_ue_validations: If True, include detailed UE validations per student
    
    Returns:
        List of UEEtudiant (UEEtudiant) with UE data
    """
    from app.models.competences import UEValidation
    
    # Get current semesters
    formsemestres_courants = await adapter.get_formsemestres_courants()
    semestre_by_formsemestre_id: dict[int, int] = {}
    
    for sem in formsemestres_courants:
        fs_id = sem.get("formsemestre_id") or sem.get("id")
        sem_id = sem.get("semestre_id") or sem.get("numero") or sem.get("sem_id")
        try:
            fs_int = int(fs_id) if fs_id is not None else None
            sem_int = int(sem_id) if sem_id is not None else None
        except (TypeError, ValueError):
            continue
        if fs_int and sem_int:
            semestre_by_formsemestre_id[fs_int] = sem_int
    
    # Determine target semester(s) based on niveau
    if niveau:
        # S1-S2 = BUT1, S3-S4 = BUT2, S5-S6 = BUT3
        target_semesters = {niveau * 2 - 1, niveau * 2}
    else:
        target_semesters = set(semestre_by_formsemestre_id.values())
    
    # Collect programme UEs for proper naming
    programme_ues_by_fs: dict[int, list[dict]] = {}
    
    for sem in formsemestres_courants:
        fs_id = sem.get("formsemestre_id") or sem.get("id")
        if not fs_id:
            continue
        try:
            programme = await adapter.get_formsemestre_programme(int(fs_id))
        except (TypeError, ValueError):
            continue
        
        if programme:
            ues = programme.get('ues', [])
            if isinstance(ues, list):
                programme_ues_by_fs[int(fs_id)] = ues

    # EFFICIENT: Fetch resultats for each semester (1 API call per semester)
    # Aggregate students across semesters
    all_students: dict[str, dict[str, Any]] = {}
    
    for fs_id, sem_id in semestre_by_formsemestre_id.items():
        if sem_id not in target_semesters:
            continue
        
        logger.info(f"Fetching resultats for formsemestre {fs_id} (S{sem_id})")
        
        # Fetch partitions for parcours extraction
        partitions = await adapter.get_formsemestre_partitions(fs_id)
        
        # Get programme UEs for this semester
        programme_ues = programme_ues_by_fs.get(fs_id, [])
        
        # Build UE id -> info map
        ue_id_to_info: dict[str, dict[str, str]] = {}
        for ue in programme_ues:
            ue_id = str(ue.get('id') or ue.get('ue_id') or '')
            if ue_id:
                ue_id_to_info[ue_id] = {
                    'acronyme': ue.get('acronyme', ''),
                    'titre': ue.get('titre', ''),
                }
        
        # Find parcours partition
        parcours_partition_id: Optional[str] = None
        if partitions and isinstance(partitions, dict):
            for part_id, part_data in partitions.items():
                if isinstance(part_data, dict):
                    part_name = part_data.get('partition_name') or part_data.get('name') or ''
                    if 'parcours' in part_name.lower():
                        parcours_partition_id = str(part_id)
                        break
        
        resultats = await adapter.get_formsemestre_resultats_list(fs_id)
        
        for etud_result in resultats:
            if not isinstance(etud_result, dict):
                continue
            
            etudid = str(etud_result.get('etudid', ''))
            if not etudid:
                continue
            
            # Skip non-inscrit students
            etat = etud_result.get('etat')
            if etat and etat != 'I':
                continue
            
            nom = etud_result.get('nom_disp') or etud_result.get('nom') or ''
            prenom = etud_result.get('prenom', '')
            
            # Extract parcours
            parcours = None
            if parcours_partition_id:
                parcours = etud_result.get(f'part_{parcours_partition_id}')
            if not parcours:
                for key, value in etud_result.items():
                    if key.startswith('part_') and isinstance(value, str):
                        import re
                        if len(value) > 3 and not re.match(r'^[A-Z]\d+$', value):
                            parcours = value
                            break
            
            # Initialize student if not exists
            if etudid not in all_students:
                all_students[etudid] = {
                    'etudid': etudid,
                    'nom': nom,
                    'prenom': prenom,
                    'parcours': parcours,
                    'semestre': f"S{sem_id}",
                    'ue_validations': [],
                    'moy_gen': None,
                }
            
            # Update parcours if found
            if parcours and not all_students[etudid]['parcours']:
                all_students[etudid]['parcours'] = parcours
            
            # Get general average
            moy_gen = etud_result.get('moy_gen') or etud_result.get('moyenne_gen')
            if moy_gen and moy_gen != '~':
                try:
                    all_students[etudid]['moy_gen'] = float(str(moy_gen).replace(',', '.'))
                except (ValueError, TypeError):
                    pass
            
            # Extract UE averages
            for key, value in etud_result.items():
                if not key.startswith('moy_ue_'):
                    continue
                
                ue_id = key[7:]  # Remove 'moy_ue_'
                
                if value == '~' or value is None:
                    continue
                
                try:
                    moyenne = float(str(value).replace(',', '.'))
                except (ValueError, TypeError):
                    continue
                
                ue_info = ue_id_to_info.get(ue_id, {})
                ue_code = ue_info.get('acronyme', '') or f"UE{ue_id}"
                ue_titre = ue_info.get('titre', '')
                
                all_students[etudid]['ue_validations'].append(
                    UEValidation(
                        ue_code=ue_code,
                        ue_titre=ue_titre,
                        moyenne=moyenne,
                        valide=moyenne >= 10.0,
                        semestre=f"S{sem_id}",
                    )
                )
        
        logger.info(f"  -> {len([e for e in all_students.values() if e.get('ue_validations')])} students with UEs")
    
    # Build results
    results: list[UEEtudiant] = []
    
    for etudid, data in all_students.items():
        ue_validations = data.get('ue_validations', [])
        if not ue_validations:
            continue
        
        nb_ues = len(ue_validations)
        nb_ues_validees = sum(1 for v in ue_validations if v.valide)
        taux = (nb_ues_validees / nb_ues) if nb_ues else 0.0
        
        results.append(
            UEEtudiant(
                etudiant_id=etudid,
                nom=data['nom'],
                prenom=data['prenom'],
                formation="",
                semestre=data.get('semestre'),
                parcours=data.get('parcours'),
                nb_ues=nb_ues,
                nb_ues_validees=nb_ues_validees,
                taux_validation=round(taux, 3),
                valide=taux > 0.5,
                moyenne_generale=data.get('moy_gen'),
                ue_validations=ue_validations if include_ue_validations else [],
            )
        )
    
    return results


# Alias for backward compatibility
_fetch_competences_data_from_scodoc = _fetch_ue_data_from_scodoc



@router.get(
    "/indicators", 
    response_model=ScolariteIndicators,
    summary="Indicateurs scolarité",
    response_description="Indicateurs agrégés de scolarité"
)
async def get_scolarite_indicators(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
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
    user: UserDB = Depends(require_view_scolarite),
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
    user: UserDB = Depends(require_view_scolarite),
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
    user: UserDB = Depends(require_view_scolarite),
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
    user: UserDB = Depends(require_view_scolarite),
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
    "/competences",
    response_model=list[Competence],
    summary="Référentiel APC",
    response_description="Liste des compétences (APC)",
)
async def get_competences(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
):
    """Retourne le référentiel de compétences ScoDoc (APC)."""
    adapter = _get_adapter(department)
    try:
        if isinstance(adapter, ScoDocAdapter):
            raw = await adapter.get_referentiel_competences()
            parsed = _parse_referentiel_competences(raw)
            if parsed:
                return parsed
        return _get_mock_competences()
    except Exception as e:
        logger.error(f"Error fetching competences for {department}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()


@router.get(
    "/competences/etudiants",
    response_model=list[UEEtudiant],
    summary="APC - Synthèse étudiants",
    response_description="Synthèse de validation des compétences par étudiant",
)
async def get_competences_etudiants(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    niveau: Optional[int] = Query(None, ge=1, le=3, description="Année de BUT (1..3)"),
    parcours: Optional[str] = Query(None, description="Filtrer par parcours (ex: Cybersécurité, DevCloud)"),
    refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
):
    """Retourne une synthèse APC par étudiant (tous étudiants).
    
    OPTIMIZED: Uses formsemestre_resultats endpoint (1 API call per semester)
    instead of fetching individual bulletins (N API calls per student).
    """
    # Try to get from cache first
    cache_key = CacheKeys.competences_etudiants(department, niveau, parcours)
    if not refresh and cache.is_connected:
        cached = await cache.get_list(cache_key, UEEtudiant)
        if cached is not None:
            logger.debug(f"Cache hit for competences_etudiants: {cache_key}")
            return cached
    
    adapter = _get_adapter(department)
    try:
        if not isinstance(adapter, ScoDocAdapter):
            return _mock_competences_etudiants(50, niveau=niveau)  # 50 mock students

        # Use shared helper (without RCUE details for list view)
        results = await _fetch_competences_data_from_scodoc(
            adapter, niveau, include_ue_validations=False
        )

        # Filter by parcours if specified
        if parcours and results:
            parcours_lower = parcours.lower().strip()
            results = [r for r in results if r.parcours and parcours_lower in r.parcours.lower()]

        # Cache results
        if cache.is_connected and results:
            await cache.set_list(cache_key, results, CacheKeys.TTL_MEDIUM)
        
        return results
    except Exception as e:
        logger.error(f"Error fetching competences etudiants for {department}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()


@router.get(
    "/etudiants/{etudiant_id}/competences",
    response_model=UEEtudiant,
    summary="APC - Détail étudiant",
    response_description="Validation des UEs d'un étudiant",
)
async def get_etudiant_competences(
    department: DepartmentDep,
    etudiant_id: str = Path(..., description="Identifiant étudiant ScoDoc (etudid)"),
    user: UserDB = Depends(require_view_scolarite),
    niveau: Optional[int] = Query(None, ge=1, le=3, description="Année de BUT (1..3)"),
    refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
):
    """Retourne le détail des UEs d'un étudiant.
    
    SIMPLIFIED: Uses formsemestre_resultats to get UE averages directly.
    """
    # Try to get from cache first
    cache_key = CacheKeys.competence_etudiant(department, etudiant_id, niveau)
    if not refresh and cache.is_connected:
        cached = await cache.get(cache_key, UEEtudiant)
        if cached is not None:
            logger.debug(f"Cache hit for competence_etudiant: {cache_key}")
            return cached
    
    adapter = _get_adapter(department)
    try:
        if not isinstance(adapter, ScoDocAdapter):
            return _mock_competence_etudiant(etudiant_id, niveau=niveau)

        from app.models.competences import UEValidation
        
        # Get student info
        etud_raw = await adapter._api_get(f"/api/etudiant/etudid/{etudiant_id}", tolerate_404=True)
        if not etud_raw:
            etud_raw = await adapter._api_get(f"/api/etudiant/{etudiant_id}", tolerate_404=True)

        nom = ""
        prenom = ""
        if isinstance(etud_raw, dict):
            nom = str(
                etud_raw.get("nom")
                or etud_raw.get("nom_disp")
                or etud_raw.get("nom_short")
                or etud_raw.get("nom_usuel")
                or ""
            ).strip()
            prenom = str(etud_raw.get("prenom") or etud_raw.get("prenom_usuel") or "").strip()
        
        formation = None
        if isinstance(etud_raw, dict):
            formation = etud_raw.get("formation_acronyme") or etud_raw.get("formation")

        # Get current semesters
        formsemestres_courants = await adapter.get_formsemestres_courants()
        semestre_by_formsemestre_id: dict[int, int] = {}
        
        for sem in formsemestres_courants:
            fs_id = sem.get("formsemestre_id") or sem.get("id")
            sem_id = sem.get("semestre_id") or sem.get("numero") or sem.get("sem_id")
            try:
                fs_int = int(fs_id) if fs_id is not None else None
                sem_int = int(sem_id) if sem_id is not None else None
            except (TypeError, ValueError):
                continue
            if fs_int and sem_int:
                semestre_by_formsemestre_id[fs_int] = sem_int

        # Determine target semesters
        if niveau:
            target_semesters = {niveau * 2 - 1, niveau * 2}
        else:
            target_semesters = set(semestre_by_formsemestre_id.values())

        # Collect UE data for this student
        ue_validations: list[UEValidation] = []
        etud_parcours: Optional[str] = None
        student_semestre: Optional[str] = None
        moy_gen: Optional[float] = None
        
        # Get programme UEs for naming
        programme_ues_by_fs: dict[int, list[dict]] = {}
        for sem in formsemestres_courants:
            fs_id = sem.get("formsemestre_id") or sem.get("id")
            if not fs_id:
                continue
            try:
                programme = await adapter.get_formsemestre_programme(int(fs_id))
            except (TypeError, ValueError):
                continue
            if programme:
                ues = programme.get('ues', [])
                if isinstance(ues, list):
                    programme_ues_by_fs[int(fs_id)] = ues

        for fs_id, sem_id in semestre_by_formsemestre_id.items():
            if sem_id not in target_semesters:
                continue
            
            # Fetch partitions for parcours
            partitions = await adapter.get_formsemestre_partitions(fs_id)
            
            # Build UE id -> info map
            ue_id_to_info: dict[str, dict[str, str]] = {}
            for ue in programme_ues_by_fs.get(fs_id, []):
                ue_id = str(ue.get('id') or ue.get('ue_id') or '')
                if ue_id:
                    ue_id_to_info[ue_id] = {
                        'acronyme': ue.get('acronyme', ''),
                        'titre': ue.get('titre', ''),
                    }
            
            # Find parcours partition
            parcours_partition_id: Optional[str] = None
            if partitions and isinstance(partitions, dict):
                for part_id, part_data in partitions.items():
                    if isinstance(part_data, dict):
                        part_name = part_data.get('partition_name') or part_data.get('name') or ''
                        if 'parcours' in part_name.lower():
                            parcours_partition_id = str(part_id)
                            break
            
            resultats = await adapter.get_formsemestre_resultats_list(fs_id)
            
            for etud_result in resultats:
                if not isinstance(etud_result, dict):
                    continue
                
                result_etudid = str(etud_result.get('etudid', ''))
                if result_etudid != etudiant_id:
                    continue
                
                # Found the student
                student_semestre = f"S{sem_id}"
                
                # Extract parcours
                if not etud_parcours and parcours_partition_id:
                    etud_parcours = etud_result.get(f'part_{parcours_partition_id}')
                if not etud_parcours:
                    for key, value in etud_result.items():
                        if key.startswith('part_') and isinstance(value, str):
                            import re
                            if len(value) > 3 and not re.match(r'^[A-Z]\d+$', value):
                                etud_parcours = value
                                break
                
                # Get general average
                result_moy_gen = etud_result.get('moy_gen') or etud_result.get('moyenne_gen')
                if result_moy_gen and result_moy_gen != '~':
                    try:
                        moy_gen = float(str(result_moy_gen).replace(',', '.'))
                    except (ValueError, TypeError):
                        pass
                
                # Extract UE averages
                for key, value in etud_result.items():
                    if not key.startswith('moy_ue_'):
                        continue
                    
                    ue_id = key[7:]  # Remove 'moy_ue_'
                    
                    if value == '~' or value is None:
                        continue
                    
                    try:
                        moyenne = float(str(value).replace(',', '.'))
                    except (ValueError, TypeError):
                        continue
                    
                    ue_info = ue_id_to_info.get(ue_id, {})
                    ue_code = ue_info.get('acronyme', '') or f"UE{ue_id}"
                    ue_titre = ue_info.get('titre', '')
                    
                    ue_validations.append(
                        UEValidation(
                            ue_code=ue_code,
                            ue_titre=ue_titre,
                            moyenne=moyenne,
                            valide=moyenne >= 10.0,
                            semestre=f"S{sem_id}",
                        )
                    )
                break  # Found the student, stop searching

        nb_ues = len(ue_validations)
        nb_ues_validees = sum(1 for v in ue_validations if v.valide)
        taux = (nb_ues_validees / nb_ues) if nb_ues else 0.0

        result = UEEtudiant(
            etudiant_id=etudiant_id,
            nom=nom or f"Etudiant {etudiant_id}",
            prenom=prenom or "",
            formation=formation,
            semestre=student_semestre,
            parcours=etud_parcours,
            nb_ues=nb_ues,
            nb_ues_validees=nb_ues_validees,
            taux_validation=round(taux, 3),
            valide=taux > 0.5,
            moyenne_generale=round(moy_gen, 2) if moy_gen else None,
            ue_validations=ue_validations,
        )
        
        # Cache result
        if cache.is_connected:
            await cache.set(cache_key, result, CacheKeys.TTL_STUDENT)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching UEs for student {etudiant_id} ({department}): {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()


@router.get(
    "/competences/parcours",
    response_model=list[str],
    summary="APC - Parcours disponibles",
    response_description="Liste des parcours disponibles pour le département",
)
async def get_competences_parcours(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    niveau: Optional[int] = Query(None, ge=1, le=3, description="Filtrer par année de BUT (1..3)"),
    refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
):
    """
    Retourne la liste des parcours disponibles pour le département.
    
    Cette endpoint est rapide car elle ne nécessite pas de charger tous les étudiants.
    Elle récupère les parcours directement depuis les partitions ScoDoc.
    """
    # Try cache first
    cache_key = CacheKeys.competences_parcours(department, niveau)
    if not refresh and cache.is_connected:
        cached = await cache.get_raw(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for parcours: {cache_key}")
            return cached
    
    adapter = _get_adapter(department)
    try:
        if not isinstance(adapter, ScoDocAdapter):
            result = ["Cybersécurité", "DevCloud", "ROM"]  # Mock parcours
            if cache.is_connected:
                await cache.set_raw(cache_key, result, CacheKeys.TTL_LONG)
            return result
        
        formsemestres_courants = await adapter.get_formsemestres_courants()
        parcours_set: set[str] = set()
        
        for sem in formsemestres_courants:
            fs_id = sem.get("formsemestre_id") or sem.get("id")
            sem_id = sem.get("semestre_id") or sem.get("numero") or sem.get("sem_id")
            
            try:
                fs_int = int(fs_id) if fs_id is not None else None
                sem_int = int(sem_id) if sem_id is not None else None
            except (TypeError, ValueError):
                continue
            
            if not fs_int:
                continue
            
            # Filter by niveau if specified
            if niveau:
                if sem_int:
                    annee = (sem_int + 1) // 2
                    if annee != niveau:
                        continue
            
            # Get parcours for this semester
            sem_parcours = await adapter.get_available_parcours(fs_int)
            parcours_set.update(sem_parcours)
        
        result = sorted(list(parcours_set))
        
        # Cache result (long TTL - parcours don't change often)
        if cache.is_connected:
            await cache.set_raw(cache_key, result, CacheKeys.TTL_LONG)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching parcours for {department}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()


@router.get(
    "/competences/stats",
    response_model=UEStats,
    summary="APC - Statistiques UE",
    response_description="Statistiques de validation des UEs",
)
async def get_competences_stats(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    niveau: Optional[int] = Query(None, ge=1, le=3, description="Année de BUT (1..3)"),
    parcours: Optional[str] = Query(None, description="Filtrer par parcours (ex: Cybersécurité, DevCloud)"),
    refresh: bool = Query(False, description="Forcer le rafraîchissement du cache"),
):
    """Retourne des statistiques de validation des UEs (tous étudiants du département).
    
    SIMPLIFIED: Uses UE data directly from formsemestre_resultats.
    """
    # Try to get from cache first
    cache_key = CacheKeys.competences_stats(department, niveau, parcours)
    if not refresh and cache.is_connected:
        cached = await cache.get(cache_key, UEStats)
        if cached is not None:
            logger.debug(f"Cache hit for competences_stats: {cache_key}")
            return cached
    
    adapter = _get_adapter(department)
    try:
        etudiants: list[UEEtudiant] = []
        
        if not isinstance(adapter, ScoDocAdapter):
            etudiants = [_mock_competence_etudiant(str(i), niveau=niveau) for i in range(1, 51)]  # 50 mock students
        else:
            # Use shared helper (with UE details needed for stats calculation)
            etudiants = await _fetch_ue_data_from_scodoc(
                adapter, niveau, include_ue_validations=True
            )

        # Filter by parcours if specified
        if parcours and etudiants:
            parcours_lower = parcours.lower().strip()
            etudiants = [e for e in etudiants if e.parcours and parcours_lower in e.parcours.lower()]

        total = len(etudiants)
        if total == 0:
            return UEStats()

        nb_etudiants_valides = sum(1 for e in etudiants if e.valide)
        distribution: dict[str, int] = {}
        par_ue_total: dict[str, int] = {}
        par_ue_valid: dict[str, int] = {}
        par_ue_moy_sum: dict[str, float] = {}
        par_ue_moy_count: dict[str, int] = {}

        for e in etudiants:
            distribution[_bucket_taux(e.taux_validation)] = distribution.get(_bucket_taux(e.taux_validation), 0) + 1
            for v in e.ue_validations:
                key = v.ue_code
                par_ue_total[key] = par_ue_total.get(key, 0) + 1
                if v.valide:
                    par_ue_valid[key] = par_ue_valid.get(key, 0) + 1
                if v.moyenne is not None:
                    par_ue_moy_sum[key] = par_ue_moy_sum.get(key, 0.0) + float(v.moyenne)
                    par_ue_moy_count[key] = par_ue_moy_count.get(key, 0) + 1

        par_ue = {
            key: round(par_ue_valid.get(key, 0) / par_ue_total[key], 3) if par_ue_total.get(key) else 0.0
            for key in par_ue_total.keys()
        }
        moyenne_par_ue = {
            key: round(par_ue_moy_sum.get(key, 0.0) / par_ue_moy_count[key], 2) if par_ue_moy_count.get(key) else 0.0
            for key in par_ue_total.keys()
        }

        result = UEStats(
            total_etudiants=total,
            taux_validation_global=round(nb_etudiants_valides / total, 3),
            par_ue=par_ue,
            moyenne_par_ue=moyenne_par_ue,
            distribution_taux_validation=distribution,
        )
        
        # Cache result
        if cache.is_connected:
            await cache.set(cache_key, result, CacheKeys.TTL_MEDIUM)
        
        return result
    except Exception as e:
        logger.error(f"Error fetching competences stats for {department}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()


@router.get(
    "/health",
    summary="État de la connexion ScoDoc",
    response_description="Vérifie la connexion à l'API ScoDoc"
)
async def check_scodoc_health(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
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


@router.get(
    "/debug/bulletin/{etudiant_id}",
    summary="[DEBUG] Structure bulletin ScoDoc",
    response_description="Retourne la structure brute d'un bulletin pour debug",
)
async def debug_bulletin(
    department: DepartmentDep,
    etudiant_id: str = Path(..., description="Identifiant étudiant ScoDoc"),
    user: UserDB = Depends(require_view_scolarite),
):
    """[DEBUG] Retourne la structure brute du bulletin pour comprendre le format ScoDoc."""
    adapter = _get_adapter(department)
    try:
        if not isinstance(adapter, ScoDocAdapter):
            return {"error": "Requires ScoDoc adapter"}
        
        # Get current semesters
        formsemestres = await adapter.get_formsemestres_courants()
        if not formsemestres:
            return {"error": "No current semesters found", "formsemestres": []}
        
        # Try to get a bulletin
        results = []
        for sem in formsemestres[:2]:  # First 2 semesters
            fs_id = sem.get("formsemestre_id") or sem.get("id")
            if not fs_id:
                continue
            
            bulletin = await adapter.get_bulletin_etudiant(etudiant_id, int(fs_id))
            if bulletin:
                # Extract UE structure
                ues_raw = bulletin.get("ues", {})
                ues_summary = {}
                for ue_code, ue_data in ues_raw.items() if isinstance(ues_raw, dict) else []:
                    ues_summary[ue_code] = {
                        "keys": list(ue_data.keys()) if isinstance(ue_data, dict) else "not_dict",
                        "moyenne": ue_data.get("moyenne") if isinstance(ue_data, dict) else None,
                        "titre": ue_data.get("titre") if isinstance(ue_data, dict) else None,
                        "competence": ue_data.get("competence") if isinstance(ue_data, dict) else None,
                    }
                
                results.append({
                    "formsemestre_id": fs_id,
                    "semestre_info": bulletin.get("semestre"),
                    "ues_keys": list(ues_raw.keys()) if isinstance(ues_raw, dict) else [],
                    "ues_summary": ues_summary,
                    "top_level_keys": list(bulletin.keys()),
                })
        
        # Also fetch referentiel
        referentiel = await adapter.get_referentiel_competences()
        
        return {
            "etudiant_id": etudiant_id,
            "department": department,
            "bulletins_found": len(results),
            "bulletins": results,
            "referentiel_found": referentiel is not None,
            "referentiel_type": type(referentiel).__name__ if referentiel else None,
            "referentiel_keys": list(referentiel.keys()) if isinstance(referentiel, dict) else None,
        }
    except Exception as e:
        logger.error(f"Debug bulletin error: {e}")
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()
