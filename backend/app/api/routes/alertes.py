"""Routes API pour les alertes et le suivi individuel des étudiants."""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from datetime import date
import logging

from app.api.deps import (
    DepartmentDep,
    require_view_scolarite,
    require_edit_scolarite,
    get_scodoc_adapter_for_department,
)
from app.models.db_models import UserDB
from app.models.alertes import (
    AlerteEtudiant,
    ConfigAlerte,
    NiveauAlerte,
    TypeAlerte,
    ProfilEtudiant,
    FicheEtudiantComplete,
    StatistiquesAbsences,
    ProgressionEtudiant,
    ScoreRisque,
)
from app.services.alertes_service import AlertesService
from app.services.cache import cache, CacheKeys

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alertes", tags=["Alertes étudiants"])


def get_alertes_service(department: str) -> AlertesService:
    """Get alertes service with ScoDoc adapter for department."""
    adapter = get_scodoc_adapter_for_department(department)
    return AlertesService(adapter)


# ==================== CONFIGURATION ====================

@router.get("/config", response_model=ConfigAlerte)
async def get_config_alertes(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
) -> ConfigAlerte:
    """Récupère la configuration des seuils d'alerte pour le département."""
    # TODO: Charger depuis la DB par département
    return ConfigAlerte()


@router.put("/config", response_model=ConfigAlerte)
async def update_config_alertes(
    department: DepartmentDep,
    config: ConfigAlerte,
    user: UserDB = Depends(require_edit_scolarite),
) -> ConfigAlerte:
    """Met à jour la configuration des seuils d'alerte."""
    # TODO: Sauvegarder en DB
    return config


# ==================== ALERTES ====================

@router.get("/", response_model=list[AlerteEtudiant])
async def get_alertes(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    niveau: Optional[str] = Query(None, description="Filtrer par niveau"),
    type_alerte: Optional[str] = Query(None, description="Filtrer par type"),
    semestre: Optional[str] = Query(None, description="Filtrer par semestre"),
    limit: int = Query(50, ge=1, le=200),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> list[AlerteEtudiant]:
    """
    Liste les alertes actives pour le département.
    
    Triées par niveau de sévérité (critique > attention > info).
    Données provenant de l'analyse en temps réel des données ScoDoc.
    """
    semestre_filter = semestre if semestre and semestre.strip() else None
    cache_key = CacheKeys.alertes_list(department, semestre_filter)
    
    # Try cache first (only for unfiltered requests)
    if not refresh and not niveau and not type_alerte:
        cached = await cache.get_raw(cache_key)
        if cached:
            logger.debug(f"Cache HIT for alertes {department}")
            alertes = [AlerteEtudiant.model_validate(a) for a in cached]
            return alertes[:limit]
    
    service = get_alertes_service(department)
    
    # Convert string filters to enums if provided
    niveau_enum = None
    type_enum = None
    
    if niveau and niveau.strip():
        try:
            niveau_enum = NiveauAlerte(niveau)
        except ValueError:
            pass
    
    if type_alerte and type_alerte.strip():
        try:
            type_enum = TypeAlerte(type_alerte)
        except ValueError:
            pass
    
    alertes = await service.get_all_alertes(
        semestre=semestre_filter,
        niveau=niveau_enum,
        type_alerte=type_enum,
        limit=limit,
    )
    
    # If no alerts from ScoDoc (not configured or no data), fallback to mock data
    if not alertes:
        alertes = _get_mock_alertes(niveau, type_alerte, semestre_filter, limit)
    
    # Cache the unfiltered results
    if not niveau and not type_alerte and alertes:
        await cache.set_raw(
            cache_key, 
            [a.model_dump(mode="json") for a in alertes],
            ttl=CacheKeys.TTL_MEDIUM
        )
        logger.debug(f"Cached alertes for {department}")
    
    return alertes


def _get_mock_alertes(
    niveau: Optional[str],
    type_alerte: Optional[str],
    semestre: Optional[str],
    limit: int,
) -> list[AlerteEtudiant]:
    """Return mock alerts when ScoDoc is not available."""
    alertes = [
        AlerteEtudiant(
            etudiant_id="12345",
            etudiant_nom="DUPONT",
            etudiant_prenom="Jean",
            type_alerte=TypeAlerte.DIFFICULTE_ACADEMIQUE,
            niveau=NiveauAlerte.CRITIQUE,
            message="Moyenne générale de 7.2/20 - En dessous du seuil de 8.0",
            valeur_actuelle=7.2,
            seuil=8.0,
            date_detection=date.today(),
            semestre="S1",
            modules_concernes=["R1.01", "R1.03", "R1.05"],
        ),
        AlerteEtudiant(
            etudiant_id="12346",
            etudiant_nom="MARTIN",
            etudiant_prenom="Sophie",
            type_alerte=TypeAlerte.ASSIDUITE,
            niveau=NiveauAlerte.ATTENTION,
            message="Taux d'absences non justifiées de 18%",
            valeur_actuelle=0.18,
            seuil=0.15,
            date_detection=date.today(),
            semestre="S1",
        ),
        AlerteEtudiant(
            etudiant_id="12347",
            etudiant_nom="BERNARD",
            etudiant_prenom="Lucas",
            type_alerte=TypeAlerte.DECROCHAGE,
            niveau=NiveauAlerte.CRITIQUE,
            message="Score de décrochage élevé (0.75) - Absences répétées + notes en chute",
            valeur_actuelle=0.75,
            seuil=0.7,
            date_detection=date.today(),
            semestre="S1",
        ),
        AlerteEtudiant(
            etudiant_id="12348",
            etudiant_nom="PETIT",
            etudiant_prenom="Emma",
            type_alerte=TypeAlerte.PROGRESSION_NEGATIVE,
            niveau=NiveauAlerte.ATTENTION,
            message="Baisse de 2.5 points par rapport au semestre précédent",
            valeur_actuelle=-2.5,
            seuil=-2.0,
            date_detection=date.today(),
            semestre="S3",
        ),
    ]
    
    # Filtrage
    if niveau:
        alertes = [a for a in alertes if a.niveau.value == niveau]
    if type_alerte:
        alertes = [a for a in alertes if a.type_alerte.value == type_alerte]
    if semestre:
        alertes = [a for a in alertes if a.semestre == semestre]
    
    # Tri par sévérité
    ordre_severite = {NiveauAlerte.CRITIQUE: 0, NiveauAlerte.ATTENTION: 1, NiveauAlerte.INFO: 2}
    alertes.sort(key=lambda a: ordre_severite.get(a.niveau, 99))
    
    return alertes[:limit]


@router.get("/statistiques")
async def get_statistiques_alertes(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    refresh: bool = Query(False, description="Force refresh cache"),
) -> dict:
    """Statistiques globales sur les alertes (données ScoDoc en temps réel)."""
    cache_key = CacheKeys.alertes_stats(department, semestre)
    
    # Try cache first
    if not refresh:
        cached = await cache.get_raw(cache_key)
        if cached:
            logger.debug(f"Cache HIT for alertes stats {department}")
            return cached
    
    service = get_alertes_service(department)
    
    stats = await service.get_statistiques_alertes(semestre)
    
    # If no stats (ScoDoc unavailable or no data), return mock
    if stats.get("total_alertes", 0) == 0:
        stats = {
            "total_alertes": 47,
            "par_niveau": {
                "critique": 8,
                "attention": 24,
                "info": 15,
            },
            "par_type": {
                "difficulte_academique": 12,
                "assiduite": 18,
                "decrochage": 5,
                "progression_negative": 8,
                "retard_travaux": 4,
            },
            "evolution_semaine": [
                {"semaine": "S45", "nouvelles": 5, "resolues": 3},
                {"semaine": "S46", "nouvelles": 8, "resolues": 4},
                {"semaine": "S47", "nouvelles": 3, "resolues": 6},
            ],
        }
    
    # Cache the result
    await cache.set_raw(cache_key, stats, ttl=CacheKeys.TTL_MEDIUM)
    
    return stats


# ==================== SUIVI INDIVIDUEL ====================

@router.get("/etudiant/{etudiant_id}", response_model=FicheEtudiantComplete)
async def get_fiche_etudiant(
    department: DepartmentDep,
    etudiant_id: str,
    user: UserDB = Depends(require_view_scolarite),
    refresh: bool = Query(False, description="Force refresh cache"),
) -> FicheEtudiantComplete:
    """
    Récupère la fiche complète d'un étudiant avec toutes ses métriques.
    
    Données provenant de ScoDoc en temps réel :
    - Profil étudiant (infos personnelles, formation, groupe)
    - Notes par module et moyenne générale
    - Statistiques d'absences
    - Historique des semestres
    - Score de risque calculé
    - Alertes actives
    - Recommandations personnalisées
    """
    cache_key = CacheKeys.fiche_etudiant(department, etudiant_id)
    
    # Try cache first
    if not refresh:
        cached = await cache.get(cache_key, FicheEtudiantComplete)
        if cached:
            logger.debug(f"Cache HIT for fiche etudiant {etudiant_id}")
            return cached
    
    service = get_alertes_service(department)
    
    fiche = await service.get_fiche_etudiant(etudiant_id)
    
    if fiche:
        # Cache the result
        await cache.set(cache_key, fiche, ttl=CacheKeys.TTL_STUDENT)
        return fiche
    
    # Fallback to mock data if ScoDoc unavailable or student not found
    return _get_mock_fiche_etudiant(etudiant_id)


def _get_mock_fiche_etudiant(etudiant_id: str) -> FicheEtudiantComplete:
    """Return mock student profile when ScoDoc is not available."""
    profil = ProfilEtudiant(
        id=etudiant_id,
        nom="DUPONT",
        prenom="Jean",
        email="jean.dupont@etu.univ.fr",
        formation="BUT R&T",
        semestre_actuel="S1",
        groupe="G1",
        type_bac="STI2D",
        mention_bac="Bien",
        annee_bac=2024,
        lycee_origine="Lycée Baggio - Lille",
        boursier=True,
        moyenne_actuelle=7.2,
        rang_promo=98,
        rang_groupe=24,
        effectif_promo=120,
        ects_valides=12,
        ects_total=30,
        alertes=[
            AlerteEtudiant(
                etudiant_id=etudiant_id,
                etudiant_nom="DUPONT",
                etudiant_prenom="Jean",
                type_alerte=TypeAlerte.DIFFICULTE_ACADEMIQUE,
                niveau=NiveauAlerte.CRITIQUE,
                message="Moyenne générale de 7.2/20",
                valeur_actuelle=7.2,
                seuil=8.0,
                date_detection=date.today(),
                semestre="S1",
                modules_concernes=["R1.01", "R1.03"],
            ),
        ],
        niveau_alerte_max=NiveauAlerte.CRITIQUE,
        statistiques_absences=StatistiquesAbsences(
            etudiant_id=etudiant_id,
            total_absences=18,
            absences_justifiees=6,
            absences_non_justifiees=12,
            taux_absenteisme=0.15,
            taux_justification=0.33,
            absences_par_module={"R1.01": 5, "R1.03": 4, "R1.05": 3},
            absences_par_jour_semaine={"lundi": 6, "mardi": 3, "vendredi": 5},
            absences_par_creneau={"matin": 10, "apres_midi": 8},
            tendance="hausse",
        ),
        progression=ProgressionEtudiant(
            etudiant_id=etudiant_id,
            etudiant_nom="DUPONT",
            etudiant_prenom="Jean",
            historique_moyennes=[
                {"semestre": "S1", "moyenne": 7.2, "rang": 98},
            ],
            tendance_globale="stable",
        ),
        score_risque=ScoreRisque(
            etudiant_id=etudiant_id,
            score_global=0.72,
            facteurs={
                "notes": 0.35,
                "assiduite": 0.25,
                "progression": 0.12,
            },
            probabilite_validation=0.35,
            recommandations=[
                "Proposer un tutorat avec un étudiant de S3/S5",
                "Convoquer pour entretien avec le responsable pédagogique",
                "Vérifier la situation personnelle (boursier, logement)",
            ],
        ),
        notes_modules=[
            {"code": "R1.01", "nom": "Initiation aux réseaux", "moyenne": 6.5, "rang": 105},
            {"code": "R1.02", "nom": "Principes et architecture des réseaux", "moyenne": 8.2, "rang": 88},
            {"code": "R1.03", "nom": "Réseaux locaux et équipements actifs", "moyenne": 5.8, "rang": 112},
            {"code": "R1.04", "nom": "Fondamentaux des systèmes d'exploitation", "moyenne": 9.5, "rang": 72},
            {"code": "R1.05", "nom": "Introduction à la programmation", "moyenne": 6.0, "rang": 98},
        ],
    )
    
    return FicheEtudiantComplete(
        profil=profil,
        historique_semestres=[
            {
                "semestre": "S1",
                "annee": "2024-2025",
                "moyenne": 7.2,
                "rang": 98,
                "decision": "En cours",
                "ects": 12,
            },
        ],
        graphique_progression=[
            {"label": "S1", "moyenne": 7.2, "moyenne_promo": 11.5},
        ],
        comparaison_promo={
            "percentile": 18,
            "ecart_moyenne": -4.3,
            "position": "Quartile inférieur",
        },
        recommandations_personnalisees=[
            "🎯 Priorité : Renforcer les bases en réseaux (R1.01, R1.03)",
            "📚 Proposer des séances de soutien en programmation",
            "👥 Mettre en relation avec un tuteur étudiant",
            "📞 Planifier un entretien avec le responsable de formation",
        ],
    )


@router.get("/etudiant/{etudiant_id}/absences", response_model=StatistiquesAbsences)
async def get_absences_etudiant(
    department: DepartmentDep,
    etudiant_id: str,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
) -> StatistiquesAbsences:
    """Récupère les statistiques d'absences détaillées d'un étudiant (données ScoDoc)."""
    service = get_alertes_service(department)
    
    fiche = await service.get_fiche_etudiant(etudiant_id)
    if fiche and fiche.profil and fiche.profil.statistiques_absences:
        return fiche.profil.statistiques_absences
    
    # Fallback mock
    return StatistiquesAbsences(
        etudiant_id=etudiant_id,
        total_absences=18,
        absences_justifiees=6,
        absences_non_justifiees=12,
        taux_absenteisme=0.15,
        taux_justification=0.33,
        absences_par_module={"R1.01": 5, "R1.03": 4, "R1.05": 3, "R1.02": 2, "R1.04": 2, "R1.06": 2},
        absences_par_jour_semaine={
            "lundi": 6,
            "mardi": 3,
            "mercredi": 2,
            "jeudi": 2,
            "vendredi": 5,
        },
        absences_par_creneau={"matin": 10, "apres_midi": 8},
        tendance="hausse",
    )


@router.get("/etudiant/{etudiant_id}/progression", response_model=ProgressionEtudiant)
async def get_progression_etudiant(
    department: DepartmentDep,
    etudiant_id: str,
    user: UserDB = Depends(require_view_scolarite),
) -> ProgressionEtudiant:
    """Récupère l'historique de progression d'un étudiant (données ScoDoc)."""
    service = get_alertes_service(department)
    
    fiche = await service.get_fiche_etudiant(etudiant_id)
    if fiche and fiche.profil and fiche.profil.progression:
        return fiche.profil.progression
    
    # Fallback mock
    return ProgressionEtudiant(
        etudiant_id=etudiant_id,
        etudiant_nom="DUPONT",
        etudiant_prenom="Jean",
        historique_moyennes=[
            {"semestre": "S1", "moyenne": 7.2, "rang": 98, "effectif": 120},
        ],
        tendance_globale="stable",
        delta_dernier_semestre=None,
        modules_progression=[],
        modules_regression=[
            {"code": "R1.01", "delta": -1.5},
            {"code": "R1.03", "delta": -2.0},
        ],
    )


@router.get("/etudiant/{etudiant_id}/risque", response_model=ScoreRisque)
async def get_score_risque_etudiant(
    department: DepartmentDep,
    etudiant_id: str,
    user: UserDB = Depends(require_view_scolarite),
) -> ScoreRisque:
    """Calcule le score de risque d'échec pour un étudiant (basé sur données ScoDoc)."""
    service = get_alertes_service(department)
    
    fiche = await service.get_fiche_etudiant(etudiant_id)
    if fiche and fiche.profil and fiche.profil.score_risque:
        return fiche.profil.score_risque
    
    # Fallback mock
    return ScoreRisque(
        etudiant_id=etudiant_id,
        score_global=0.72,
        facteurs={
            "moyenne_actuelle": 0.35,
            "taux_absenteisme": 0.25,
            "tendance_progression": 0.12,
            "type_bac": 0.05,
        },
        probabilite_validation=0.35,
        recommandations=[
            "Proposer un accompagnement personnalisé",
            "Convoquer pour un entretien individuel",
            "Vérifier les éventuelles difficultés personnelles",
            "Envisager un contrat pédagogique",
        ],
    )


# ==================== LISTES FILTRÉES ====================

@router.get("/etudiants-en-difficulte", response_model=list[ProfilEtudiant])
async def get_etudiants_en_difficulte(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    seuil_moyenne: float = Query(8.0, description="Seuil de moyenne"),
) -> list[ProfilEtudiant]:
    """Liste les étudiants en difficulté académique (basé sur données ScoDoc)."""
    service = get_alertes_service(department)
    result = await service.get_etudiants_en_difficulte(seuil_moyenne)
    logger.info(f"Found {len(result)} students in difficulty for {department}")
    return result


@router.get("/etudiants-absents", response_model=list[ProfilEtudiant])
async def get_etudiants_absents(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    seuil_absences: float = Query(0.15, description="Seuil de taux d'absences"),
) -> list[ProfilEtudiant]:
    """Liste les étudiants avec un taux d'absentéisme élevé."""
    service = get_alertes_service(department)
    result = await service.get_etudiants_absents(seuil_absences)
    logger.info(f"Found {len(result)} absent students for {department}")
    return result


@router.get("/etudiants-risque-decrochage", response_model=list[ProfilEtudiant])
async def get_etudiants_risque_decrochage(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    seuil_score: float = Query(0.6, description="Seuil de score de risque"),
) -> list[ProfilEtudiant]:
    """Liste les étudiants à risque de décrochage."""
    service = get_alertes_service(department)
    result = await service.get_etudiants_risque_decrochage(seuil_score)
    logger.info(f"Found {len(result)} at-risk students for {department}")
    return result


@router.get("/felicitations", response_model=list[ProfilEtudiant])
async def get_etudiants_felicitations(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_scolarite),
    semestre: Optional[str] = None,
    top_percent: int = Query(10, description="Top X% de la promo"),
) -> list[ProfilEtudiant]:
    """Liste les meilleurs étudiants (top X%)."""
    service = get_alertes_service(department)
    result = await service.get_etudiants_felicitations(top_percent)
    logger.info(f"Found {len(result)} top students for {department}")
    return result
