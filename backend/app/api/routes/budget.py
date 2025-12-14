"""Budget API routes."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.budget import BudgetIndicators, LigneBudget, Depense, CategorieDepense
from app.models.db_models import UserDB, BudgetAnnuel, LigneBudgetDB, DepenseDB
from app.adapters.excel import ExcelAdapter
from app.api.deps import (
    DepartmentDep,
    require_view_budget, require_edit_budget, require_import
)
from app.services import cache, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

_file_adapter = ExcelAdapter()


def get_budget_from_db(db: Session, department: str, annee: Optional[int] = None) -> Optional[BudgetIndicators]:
    """Fetch budget data from database."""
    year = annee or date.today().year
    
    budget = db.query(BudgetAnnuel).filter(
        BudgetAnnuel.department == department,
        BudgetAnnuel.annee == year
    ).first()
    
    if not budget:
        return None
    
    # Get budget lines
    lignes = db.query(LigneBudgetDB).filter(
        LigneBudgetDB.budget_annuel_id == budget.id
    ).all()
    
    # Get expenses
    depenses = db.query(DepenseDB).filter(
        DepenseDB.budget_annuel_id == budget.id
    ).order_by(DepenseDB.montant.desc()).limit(20).all()
    
    # Calculate totals
    total_engage = sum(l.engage for l in lignes)
    total_paye = sum(l.paye for l in lignes)
    budget_total = sum(l.budget_initial for l in lignes)
    
    # Build evolution mensuelle from expenses
    evolution = {}
    for dep in db.query(DepenseDB).filter(DepenseDB.budget_annuel_id == budget.id).all():
        month_key = dep.date_depense.strftime("%Y-%m")
        evolution[month_key] = evolution.get(month_key, 0) + dep.montant
    
    return BudgetIndicators(
        annee=year,
        budget_total=budget_total,
        total_engage=total_engage,
        total_paye=total_paye,
        total_disponible=budget_total - total_engage,
        taux_execution=total_paye / budget_total if budget_total > 0 else 0,
        taux_engagement=total_engage / budget_total if budget_total > 0 else 0,
        par_categorie=[
            LigneBudget(
                categorie=CategorieDepense(l.categorie) if l.categorie in [c.value for c in CategorieDepense] else CategorieDepense.AUTRE,
                budget_initial=l.budget_initial,
                budget_modifie=l.budget_modifie,
                engage=l.engage,
                paye=l.paye,
                disponible=l.budget_modifie - l.engage,
            )
            for l in lignes
        ],
        evolution_mensuelle=dict(sorted(evolution.items())),
        top_depenses=[
            Depense(
                id=str(d.id),
                libelle=d.libelle,
                montant=d.montant,
                categorie=CategorieDepense(d.categorie) if d.categorie in [c.value for c in CategorieDepense] else CategorieDepense.AUTRE,
                date=d.date_depense,
                fournisseur=d.fournisseur,
                numero_commande=d.numero_commande,
                statut=d.statut,
            )
            for d in depenses
        ],
        previsionnel=budget.previsionnel,
        realise=total_paye,
    )


@router.get("/indicators", response_model=BudgetIndicators)
async def get_budget_indicators(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_budget),
    annee: Optional[int] = Query(None, description="Année budgétaire"),
    refresh: bool = Query(False, description="Force cache refresh"),
    db: Session = Depends(get_db),
):
    """
    Get aggregated budget indicators.
    
    Returns totals, execution rates, and breakdown by category.
    """
    try:
        cache_key = CacheKeys.budget_indicators(annee, department)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, BudgetIndicators)
            if cached:
                return cached
        
        # Fetch from database
        data = get_budget_from_db(db, department, annee)
        
        if not data:
            raise HTTPException(
                status_code=404, 
                detail=f"Aucune donnée budget pour {department} en {annee or date.today().year}"
            )
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_budget)
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/par-categorie")
async def get_budget_par_categorie(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_budget),
    annee: Optional[int] = Query(None, description="Année budgétaire"),
    db: Session = Depends(get_db),
):
    """
    Get budget breakdown by category.
    """
    data = get_budget_from_db(db, department, annee)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée budget trouvée")
    
    return {
        "annee": data.annee,
        "categories": [
            {
                "categorie": ligne.categorie.value,
                "budget_initial": ligne.budget_initial,
                "budget_modifie": ligne.budget_modifie,
                "engage": ligne.engage,
                "paye": ligne.paye,
                "disponible": ligne.disponible,
                "taux_execution": ligne.paye / ligne.budget_initial if ligne.budget_initial > 0 else 0,
            }
            for ligne in data.par_categorie
        ],
    }


@router.get("/evolution")
async def get_budget_evolution(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_budget),
    annee: Optional[int] = Query(None, description="Année budgétaire"),
    db: Session = Depends(get_db),
):
    """
    Get monthly budget evolution.
    """
    data = get_budget_from_db(db, department, annee)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée budget trouvée")
    
    return {
        "annee": data.annee,
        "evolution_mensuelle": data.evolution_mensuelle,
        "cumul": _calculate_cumul(data.evolution_mensuelle),
    }


@router.get("/execution")
async def get_taux_execution(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_budget),
    db: Session = Depends(get_db),
):
    """
    Get budget execution rates.
    """
    data = get_budget_from_db(db, department)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée budget trouvée")
    
    return {
        "taux_execution": data.taux_execution,
        "taux_engagement": data.taux_engagement,
        "budget_total": data.budget_total,
        "engage": data.total_engage,
        "paye": data.total_paye,
        "disponible": data.total_disponible,
    }


@router.get("/top-depenses")
async def get_top_depenses(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_budget),
    limit: int = Query(10, le=50, description="Number of results"),
    categorie: Optional[CategorieDepense] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
):
    """
    Get top expenses.
    """
    data = get_budget_from_db(db, department)
    if not data:
        raise HTTPException(status_code=404, detail="Aucune donnée budget trouvée")
    
    depenses = data.top_depenses
    
    if categorie:
        depenses = [d for d in depenses if d.categorie == categorie]
    
    return depenses[:limit]


@router.post("/import")
async def import_budget_file(
    department: DepartmentDep,
    user: UserDB = Depends(require_import),
    file: UploadFile = File(..., description="Budget Excel file"),
    annee: int = Query(..., description="Année budgétaire"),
):
    """
    Import budget Excel file.
    
    Expected columns: Catégorie, Budget Initial, Budget Modifié, Engagé, Payé
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        indicators = _file_adapter.parse_budget_file(content)
        indicators.annee = annee
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors du parsing du fichier: {str(e)}"
        )


def _calculate_cumul(evolution: dict[str, float]) -> dict[str, float]:
    """Calculate cumulative sum from monthly evolution."""
    cumul = {}
    total = 0
    for month in sorted(evolution.keys()):
        total += evolution[month]
        cumul[month] = total
    return cumul
