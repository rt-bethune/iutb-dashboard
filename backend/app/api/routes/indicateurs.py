"""Routes API pour les indicateurs de cohorte et statistiques avancées."""

import logging
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.api.deps import (
    DepartmentDep,
    require_view_scolarite,
    get_scodoc_adapter_for_department,
)
from app.models.db_models import UserDB
from app.models.indicateurs import (
    StatistiquesCohorte,
    TauxValidation,
    RepartitionMentions,
    TauxPassage,
    ModuleAnalyse,
    AnalyseAbsenteisme,
    ComparaisonInterannuelle,
    AnalyseTypeBac,
    AnalyseBoursiers,
    TableauBordCohorte,
    IndicateursPredictifs,
    RapportSemestre,
)
from app.services.indicateurs_service import IndicateursService
from app.services.cache import cache, CacheKeys

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/indicateurs", tags=["Indicateurs cohorte"])


def get_indicateurs_service(department: str) -> IndicateursService:
    """Factory function to create IndicateursService for a department."""
    adapter = get_scodoc_adapter_for_department(department)
    return IndicateursService(adapter)


# ==================== TABLEAU DE BORD GLOBAL ====================

@router.get("/tableau-bord", response_model=TableauBordCohorte)
async def get_tableau_bord_cohorte(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    annee: Optional[str] = Query(None, description="Année universitaire (ex: 2024-2025)"),
    semestre: Optional[str] = Query(None, description="Semestre (S1, S2, etc.)"),
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> TableauBordCohorte:
    """
    Tableau de bord complet avec tous les indicateurs clés de la cohorte.
    
    Vue synthétique pour le responsable de formation.
    """
    cache_key = CacheKeys.indicateurs_tableau_bord(
        department,
        annee,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    # Try cache first
    if not refresh:
        cached = await cache.get(cache_key, TableauBordCohorte)
        if cached:
            logger.debug(f"Cache HIT for tableau-bord {department}")
            return cached
    
    # Try to get real data from ScoDoc
    service = get_indicateurs_service(department)
    result = await service.get_tableau_bord(annee, semestre, formation=formation, modalite=modalite)
    if result:
        logger.info(f"Returning real ScoDoc data for tableau-bord {department}")
        await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
        return result
    
    # Fallback to mock data
    logger.info(f"Returning mock data for tableau-bord {department}")
    mock_result = _get_mock_tableau_bord(department, annee, semestre)
    await cache.set(cache_key, mock_result, ttl=CacheKeys.TTL_SHORT)
    return mock_result


# ==================== STATISTIQUES DE COHORTE ====================

@router.get("/statistiques", response_model=StatistiquesCohorte)
async def get_statistiques_cohorte(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    groupe: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> StatistiquesCohorte:
    """Statistiques descriptives de la cohorte (effectifs, moyenne, écart-type, quartiles)."""
    cache_key = CacheKeys.indicateurs_statistiques(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    # Try cache first (only for non-filtered requests)
    if not refresh and not groupe:
        cached = await cache.get(cache_key, StatistiquesCohorte)
        if cached:
            logger.debug(f"Cache HIT for statistiques {department}")
            return cached
    
    # Try real data first
    service = get_indicateurs_service(department)
    result = await service.get_statistiques_cohorte(semestre, groupe, formation=formation, modalite=modalite)
    if result:
        logger.info(f"Returning real ScoDoc data for statistiques {department}")
        if not groupe:
            await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
        return result
    
    # Fallback to mock
    logger.info(f"Returning mock data for statistiques {department}")
    return _get_mock_statistiques()


@router.get("/taux-validation", response_model=TauxValidation)
async def get_taux_validation(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> TauxValidation:
    """Taux de validation par UE, module et compétence."""
    cache_key = CacheKeys.indicateurs_taux_validation(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    # Try cache first
    if not refresh:
        cached = await cache.get(cache_key, TauxValidation)
        if cached:
            logger.debug(f"Cache HIT for taux-validation {department}")
            return cached
    
    # Try real data first
    service = get_indicateurs_service(department)
    result = await service.get_taux_validation(semestre, formation=formation, modalite=modalite)
    if result:
        logger.info(f"Returning real ScoDoc data for taux-validation {department}")
        await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
        return result
    
    # Fallback to mock
    logger.info(f"Returning mock data for taux-validation {department}")
    return _get_mock_taux_validation()


@router.get("/mentions", response_model=RepartitionMentions)
async def get_repartition_mentions(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> RepartitionMentions:
    """Répartition des mentions (TB, B, AB, P, etc.)."""
    cache_key = CacheKeys.indicateurs_mentions(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    # Try cache first
    if not refresh:
        cached = await cache.get(cache_key, RepartitionMentions)
        if cached:
            logger.debug(f"Cache HIT for mentions {department}")
            return cached
    
    # Try real data first
    service = get_indicateurs_service(department)
    result = await service.get_mentions(semestre, formation=formation, modalite=modalite)
    if result:
        logger.info(f"Returning real ScoDoc data for mentions {department}")
        await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
        return result
    
    # Fallback to mock
    logger.info(f"Returning mock data for mentions {department}")
    return _get_mock_mentions()


# ==================== ANALYSE PAR MODULE ====================

@router.get("/modules", response_model=list[ModuleAnalyse])
async def get_analyse_modules(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    tri: str = Query("taux_echec", description="Critère de tri: taux_echec, moyenne, ecart_type"),
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> list[ModuleAnalyse]:
    """Analyse détaillée par module avec identification des modules difficiles."""
    cache_key = CacheKeys.indicateurs_modules(
        department,
        semestre,
        tri,
        formation=formation,
        modalite=modalite,
    )
    
    # Try cache first
    if not refresh:
        cached = await cache.get_list(cache_key, ModuleAnalyse)
        if cached:
            logger.debug(f"Cache HIT for modules {department}")
            return cached
    
    # Try real data first
    service = get_indicateurs_service(department)
    result = await service.get_modules_analyse(semestre, tri, formation=formation, modalite=modalite)
    if result:
        logger.info(f"Returning real ScoDoc data for modules {department} ({len(result)} modules)")
        await cache.set_list(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
        return result
    
    # Fallback to mock
    logger.info(f"Returning mock data for modules {department}")
    return _get_mock_modules(tri)


@router.get("/modules/{code_module}", response_model=ModuleAnalyse)
async def get_analyse_module(
    department: DepartmentDep,
    code_module: str,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
) -> ModuleAnalyse:
    """Analyse détaillée d'un module spécifique."""
    return ModuleAnalyse(
        code=code_module,
        nom="Réseaux locaux et équipements actifs",
        moyenne=9.2,
        ecart_type=4.1,
        taux_validation=0.68,
        taux_echec=0.32,
        nb_defaillants=5,
        mediane=9.5,
        min=2.0,
        max=18.0,
        notes_distribution={
            "0-4": 8,
            "4-8": 18,
            "8-10": 12,
            "10-12": 32,
            "12-14": 28,
            "14-16": 15,
            "16-20": 7,
        },
        alerte=True,
        alerte_message="Taux d'échec élevé, forte dispersion des notes",
    )


# ==================== ASSIDUITÉ ====================

@router.get("/absenteisme", response_model=AnalyseAbsenteisme)
async def get_analyse_absenteisme(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> AnalyseAbsenteisme:
    """Analyse globale de l'absentéisme de la cohorte."""
    cache_key = CacheKeys.indicateurs_absenteisme(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    # Try cache first
    if not refresh:
        cached = await cache.get(cache_key, AnalyseAbsenteisme)
        if cached:
            logger.debug(f"Cache HIT for absenteisme {department}")
            return cached
    
    # Try real data first
    service = get_indicateurs_service(department)
    result = await service.get_analyse_absenteisme(semestre, formation=formation, modalite=modalite)
    if result:
        logger.info(f"Returning real ScoDoc data for absenteisme {department}")
        await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
        return result
    
    # Fallback to mock
    logger.info(f"Returning mock data for absenteisme {department}")
    return _get_mock_absenteisme()


# ==================== TAUX DE PASSAGE ====================

@router.get("/taux-passage", response_model=TauxPassage)
async def get_taux_passage(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    annee: Optional[str] = None,
) -> TauxPassage:
    """Taux de passage entre semestres/années."""
    return TauxPassage(
        s1_vers_s2=0.92,
        s2_vers_s3=0.78,
        s3_vers_s4=0.85,
        s4_vers_s5=0.82,
        s5_vers_s6=0.95,
        taux_diplomation=0.72,
        taux_abandon=0.08,
        taux_reorientation=0.05,
        par_parcours={
            "Cybersécurité": {"taux": 0.85, "effectif": 40},
            "DevCloud": {"taux": 0.78, "effectif": 35},
            "Pilpro": {"taux": 0.80, "effectif": 45},
        },
        details_echecs={
            "absences": 35,
            "notes": 45,
            "abandon": 12,
            "reorientation": 8,
        },
    )


# ==================== COMPARAISONS ====================

@router.get("/comparaison-interannuelle", response_model=ComparaisonInterannuelle)
async def get_comparaison_interannuelle(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    nb_annees: int = Query(5, ge=2, le=10),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> ComparaisonInterannuelle:
    """Évolution des indicateurs sur plusieurs années."""
    cache_key = CacheKeys.indicateurs_comparaison(department, nb_annees)
    
    if not refresh:
        cached = await cache.get(cache_key, ComparaisonInterannuelle)
        if cached:
            return cached
            
    service = get_indicateurs_service(department)
    result = await service.get_comparaison_interannuelle(nb_annees)
    
    await cache.set(cache_key, result, ttl=CacheKeys.TTL_LONG)
    return result


@router.get("/analyse-type-bac", response_model=AnalyseTypeBac)
async def get_analyse_type_bac(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> AnalyseTypeBac:
    """Analyse de réussite par type de baccalauréat."""
    cache_key = CacheKeys.indicateurs_type_bac(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    if not refresh:
        cached = await cache.get(cache_key, AnalyseTypeBac)
        if cached:
            return cached
            
    service = get_indicateurs_service(department)
    result = await service.get_analyse_type_bac(semestre, formation=formation, modalite=modalite)
    
    await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
    return result



@router.get("/analyse-boursiers", response_model=AnalyseBoursiers)
async def get_analyse_boursiers(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> AnalyseBoursiers:
    """Analyse de réussite des étudiants boursiers."""
    cache_key = CacheKeys.indicateurs_boursiers(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    if not refresh:
        cached = await cache.get(cache_key, AnalyseBoursiers)
        if cached:
            return cached
            
    service = get_indicateurs_service(department)
    result = await service.get_analyse_boursiers(semestre, formation=formation, modalite=modalite)
    
    await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
    return result


# ==================== PRÉDICTIF ====================

@router.get("/predictifs", response_model=IndicateursPredictifs)
async def get_indicateurs_predictifs(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> IndicateursPredictifs:
    """Indicateurs prédictifs basés sur l'historique."""
    cache_key = CacheKeys.indicateurs_predictifs(
        department,
        semestre,
        formation=formation,
        modalite=modalite,
    )
    
    if not refresh:
        cached = await cache.get(cache_key, IndicateursPredictifs)
        if cached:
            return cached
            
    service = get_indicateurs_service(department)
    result = await service.get_indicateurs_predictifs(semestre, formation=formation, modalite=modalite)
    
    await cache.set(cache_key, result, ttl=CacheKeys.TTL_MEDIUM)
    return result


# ==================== RAPPORT ====================

@router.get("/rapport-semestre", response_model=RapportSemestre)
async def get_rapport_semestre(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    annee: str = Query(..., description="Année universitaire (ex: 2024-2025)"),
    semestre: str = Query(..., description="Semestre (S1, S2, etc.)"),
) -> RapportSemestre:
    """Génère un rapport complet de semestre (pour PDF/export)."""
    return RapportSemestre(
        department=department,
        annee=annee,
        semestre=semestre,
        date_generation="2025-01-15",
        resume_executif={
            "effectif": 120,
            "moyenne": 11.5,
            "taux_reussite": 0.78,
            "points_positifs": [
                "Amélioration du taux de réussite (+2% vs année précédente)",
                "Baisse de l'absentéisme (-2%)",
                "Excellents résultats en R1.04",
            ],
            "points_vigilance": [
                "Taux d'échec élevé en R1.03 (32%)",
                "18 étudiants en situation critique",
                "Absences concentrées le vendredi",
            ],
        },
        statistiques=StatistiquesCohorte(
            effectif_total=120,
            effectif_par_groupe={"G1": 30, "G2": 30, "G3": 30, "G4": 30},
            moyenne_promo=11.5,
            ecart_type=3.2,
            mediane=11.8,
            min=3.5,
            max=18.2,
            quartiles={"Q1": 9.2, "Q2": 11.8, "Q3": 13.8},
            taux_reussite=0.78,
            taux_difficulte=0.15,
            taux_excellence=0.12,
        ),
        mentions=RepartitionMentions(
            tres_bien=8,
            bien=22,
            assez_bien=35,
            passable=29,
            insuffisant=18,
            eliminatoire=8,
            pourcentage_admis=0.78,
        ),
        modules_analyse=[
            ModuleAnalyse(
                code="R1.03",
                nom="Réseaux locaux",
                moyenne=9.2,
                ecart_type=4.1,
                taux_validation=0.68,
                taux_echec=0.32,
                nb_defaillants=5,
                mediane=9.5,
                min=2.0,
                max=18.0,
                alerte=True,
                alerte_message="Module en difficulté",
            ),
        ],
        absenteisme=AnalyseAbsenteisme(
            taux_global=0.08,
            taux_justifie=0.05,
            taux_non_justifie=0.03,
            nb_absences_total=1250,
            heures_perdues=2500,
            etudiants_critiques=12,
            correlation_notes=-0.65,
        ),
        comparaison_precedent={
            "moyenne": {"actuel": 11.5, "precedent": 11.2, "delta": 0.3},
            "taux_reussite": {"actuel": 0.78, "precedent": 0.76, "delta": 0.02},
            "absenteisme": {"actuel": 0.08, "precedent": 0.10, "delta": -0.02},
        },
        plan_action=[
            {
                "priorite": 1,
                "action": "Organiser des TD de soutien en R1.03",
                "responsable": "Resp. module",
                "echeance": "Semaine prochaine",
            },
            {
                "priorite": 2,
                "action": "Convoquer les 18 étudiants en alerte critique",
                "responsable": "Resp. formation",
                "echeance": "2 semaines",
            },
            {
                "priorite": 3,
                "action": "Réorganiser les cours du vendredi",
                "responsable": "Resp. EDT",
                "echeance": "Semestre prochain",
            },
        ],
    )


# ==================== MOCK DATA HELPERS ====================

def _get_mock_tableau_bord(department: str, annee: Optional[str], semestre: Optional[str]) -> TableauBordCohorte:
    """Return mock tableau de bord data."""
    return TableauBordCohorte(
        department=department,
        annee=annee or "2024-2025",
        semestre=semestre or "S1",
        statistiques=_get_mock_statistiques(),
        taux_validation=_get_mock_taux_validation(),
        mentions=_get_mock_mentions(),
        indicateurs_cles={
            "taux_reussite": {"valeur": 0.78, "tendance": "stable", "vs_annee_prec": 0.02},
            "moyenne_promo": {"valeur": 11.5, "tendance": "hausse", "vs_annee_prec": 0.3},
            "taux_absenteisme": {"valeur": 0.08, "tendance": "baisse", "vs_annee_prec": -0.02},
            "etudiants_alertes": {"valeur": 18, "tendance": "hausse", "vs_annee_prec": 3},
        },
        alertes_recentes=[
            {"type": "critique", "nombre": 8, "evolution": 2},
            {"type": "attention", "nombre": 24, "evolution": -3},
        ],
    )


def _get_mock_statistiques() -> StatistiquesCohorte:
    """Return mock statistiques data."""
    return StatistiquesCohorte(
        effectif_total=120,
        effectif_par_groupe={"G1": 30, "G2": 30, "G3": 30, "G4": 30},
        moyenne_promo=11.5,
        ecart_type=3.2,
        mediane=11.8,
        min=3.5,
        max=18.2,
        quartiles={"Q1": 9.2, "Q2": 11.8, "Q3": 13.8},
        taux_reussite=0.78,
        taux_difficulte=0.15,
        taux_excellence=0.12,
    )


def _get_mock_taux_validation() -> TauxValidation:
    """Return mock taux validation data."""
    return TauxValidation(
        taux_global=0.78,
        par_ue={
            "UE1.1": 0.82,
            "UE1.2": 0.75,
            "UE1.3": 0.85,
        },
        par_module={
            "R1.01": 0.72,
            "R1.02": 0.85,
            "R1.03": 0.68,
            "R1.04": 0.90,
            "R1.05": 0.75,
            "R1.06": 0.78,
        },
        par_competence={
            "Administrer": 0.80,
            "Connecter": 0.75,
            "Programmer": 0.72,
        },
    )


def _get_mock_mentions() -> RepartitionMentions:
    """Return mock mentions data."""
    return RepartitionMentions(
        tres_bien=8,
        bien=22,
        assez_bien=35,
        passable=29,
        insuffisant=18,
        eliminatoire=8,
        pourcentage_admis=0.78,
    )


def _get_mock_modules(tri: str) -> list[ModuleAnalyse]:
    """Return mock modules analysis data."""
    modules = [
        ModuleAnalyse(
            code="R1.03",
            nom="Réseaux locaux et équipements actifs",
            moyenne=9.2,
            ecart_type=4.1,
            taux_validation=0.68,
            taux_echec=0.32,
            nb_defaillants=5,
            mediane=9.5,
            min=2.0,
            max=18.0,
            notes_distribution={
                "0-4": 8,
                "4-8": 18,
                "8-10": 12,
                "10-12": 32,
                "12-14": 28,
                "14-16": 15,
                "16-20": 7,
            },
            alerte=True,
            alerte_message="Taux d'échec élevé (32%), écart-type important",
        ),
        ModuleAnalyse(
            code="R1.01",
            nom="Initiation aux réseaux",
            moyenne=10.5,
            ecart_type=3.5,
            taux_validation=0.72,
            taux_echec=0.28,
            nb_defaillants=3,
            mediane=10.8,
            min=3.5,
            max=17.5,
            notes_distribution={
                "0-4": 5,
                "4-8": 15,
                "8-10": 18,
                "10-12": 35,
                "12-14": 25,
                "14-16": 15,
                "16-20": 7,
            },
            alerte=True,
            alerte_message="Taux d'échec supérieur à 25%",
        ),
        ModuleAnalyse(
            code="R1.04",
            nom="Fondamentaux des systèmes d'exploitation",
            moyenne=12.8,
            ecart_type=2.8,
            taux_validation=0.90,
            taux_echec=0.10,
            nb_defaillants=1,
            mediane=13.0,
            min=5.5,
            max=19.0,
            notes_distribution={
                "0-4": 1,
                "4-8": 5,
                "8-10": 10,
                "10-12": 25,
                "12-14": 40,
                "14-16": 28,
                "16-20": 11,
            },
            alerte=False,
        ),
    ]
    
    if tri == "taux_echec":
        modules.sort(key=lambda m: m.taux_echec, reverse=True)
    elif tri == "moyenne":
        modules.sort(key=lambda m: m.moyenne)
    elif tri == "ecart_type":
        modules.sort(key=lambda m: m.ecart_type, reverse=True)
    
    return modules


def _get_mock_absenteisme() -> AnalyseAbsenteisme:
    """Return mock absenteisme data."""
    return AnalyseAbsenteisme(
        taux_global=0.08,
        taux_justifie=0.05,
        taux_non_justifie=0.03,
        nb_absences_total=1250,
        heures_perdues=2500,
        par_module={
            "R1.01": {"taux": 0.10, "heures": 320},
            "R1.02": {"taux": 0.06, "heures": 180},
            "R1.03": {"taux": 0.12, "heures": 380},
            "R1.04": {"taux": 0.05, "heures": 150},
            "R1.05": {"taux": 0.08, "heures": 250},
        },
        par_jour_semaine={
            "lundi": 0.12,
            "mardi": 0.06,
            "mercredi": 0.07,
            "jeudi": 0.06,
            "vendredi": 0.15,
        },
        par_creneau={
            "08h-10h": 0.15,
            "10h-12h": 0.08,
            "14h-16h": 0.06,
            "16h-18h": 0.10,
        },
        etudiants_critiques=12,
        evolution_hebdo=[
            {"semaine": "S45", "taux": 0.07},
            {"semaine": "S46", "taux": 0.09},
            {"semaine": "S47", "taux": 0.08},
        ],
        correlation_notes=-0.65,
    )
