"""Budget Admin API routes with CRUD operations."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.crud import budget_crud
from app.api.deps import DepartmentDep
from app.schemas.budget import (
    BudgetAnnuelCreate,
    BudgetAnnuelUpdate,
    BudgetAnnuelResponse,
    BudgetAnnuelSummary,
    LigneBudgetCreate,
    LigneBudgetUpdate,
    LigneBudgetResponse,
    DepenseCreate,
    DepenseUpdate,
    DepenseResponse,
    ImportResult,
    CategorieDepense,
)
from app.models.budget import BudgetIndicators, LigneBudget, Depense
from app.models.budget import CategorieDepense as CategorieDepenseEnum

router = APIRouter()


# ==================== BUDGET ANNUEL ====================

@router.get("/years", response_model=list[BudgetAnnuelSummary])
async def list_budget_years(
    department: DepartmentDep,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
):
    """List all budget years."""
    budgets = budget_crud.get_all_budgets(db, department, skip=skip, limit=limit)
    result = []
    for b in budgets:
        stats = budget_crud.get_budget_stats(db, department, b.annee)
        result.append(BudgetAnnuelSummary(
            id=b.id,
            annee=b.annee,
            budget_total=stats.get("budget_total", 0),
            total_engage=stats.get("total_engage", 0),
            total_paye=stats.get("total_paye", 0),
            taux_execution=stats.get("taux_execution", 0),
        ))
    return result


@router.get("/year/{annee}", response_model=BudgetAnnuelResponse)
async def get_budget_year(
    department: DepartmentDep,
    annee: int,
    db: Session = Depends(get_db),
):
    """Get budget details for a specific year."""
    budget = budget_crud.get_budget_annuel(db, department, annee)
    if not budget:
        raise HTTPException(status_code=404, detail=f"Budget {annee} non trouvé")
    
    stats = budget_crud.get_budget_stats(db, department, annee)
    
    lignes = [
        LigneBudgetResponse(
            id=l.id,
            categorie=CategorieDepense(l.categorie),
            budget_initial=l.budget_initial,
            budget_modifie=l.budget_modifie,
            engage=l.engage,
            paye=l.paye,
            disponible=l.budget_modifie - l.engage,
        )
        for l in budget.lignes
    ]
    
    return BudgetAnnuelResponse(
        id=budget.id,
        annee=budget.annee,
        budget_total=budget.budget_total,
        previsionnel=budget.previsionnel,
        date_creation=budget.date_creation,
        date_modification=budget.date_modification,
        lignes=lignes,
        total_engage=stats.get("total_engage", 0),
        total_paye=stats.get("total_paye", 0),
        total_disponible=stats.get("total_disponible", 0),
        taux_execution=stats.get("taux_execution", 0),
        taux_engagement=stats.get("taux_engagement", 0),
    )


@router.post("/year", response_model=BudgetAnnuelResponse)
async def create_budget_year(
    department: DepartmentDep,
    budget: BudgetAnnuelCreate,
    db: Session = Depends(get_db),
):
    """Create a new budget year."""
    existing = budget_crud.get_budget_annuel(db, department, budget.annee)
    if existing:
        raise HTTPException(status_code=400, detail=f"Budget {budget.annee} existe déjà")
    
    db_budget = budget_crud.create_budget_annuel(db, department, budget)
    return await get_budget_year(department, db_budget.annee, db)


@router.put("/year/{annee}", response_model=BudgetAnnuelResponse)
async def update_budget_year(
    department: DepartmentDep,
    annee: int,
    budget: BudgetAnnuelUpdate,
    db: Session = Depends(get_db),
):
    """Update a budget year."""
    db_budget = budget_crud.update_budget_annuel(db, department, annee, budget)
    if not db_budget:
        raise HTTPException(status_code=404, detail=f"Budget {annee} non trouvé")
    return await get_budget_year(department, annee, db)


@router.delete("/year/{annee}")
async def delete_budget_year(
    department: DepartmentDep,
    annee: int,
    db: Session = Depends(get_db),
):
    """Delete a budget year and all related data."""
    if not budget_crud.delete_budget_annuel(db, department, annee):
        raise HTTPException(status_code=404, detail=f"Budget {annee} non trouvé")
    return {"message": f"Budget {annee} supprimé"}


# ==================== LIGNES BUDGET ====================

@router.post("/year/{annee}/ligne", response_model=LigneBudgetResponse)
async def create_ligne_budget(
    department: DepartmentDep,
    annee: int,
    ligne: LigneBudgetCreate,
    db: Session = Depends(get_db),
):
    """Add a budget line to a year."""
    budget = budget_crud.get_or_create_budget_annuel(db, department, annee)
    
    # Check if category already exists
    existing = budget_crud.get_ligne_by_categorie(db, budget.id, ligne.categorie.value)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Catégorie {ligne.categorie.value} existe déjà pour {annee}"
        )
    
    db_ligne = budget_crud.create_ligne_budget(db, budget.id, ligne)
    return LigneBudgetResponse(
        id=db_ligne.id,
        categorie=CategorieDepense(db_ligne.categorie),
        budget_initial=db_ligne.budget_initial,
        budget_modifie=db_ligne.budget_modifie,
        engage=db_ligne.engage,
        paye=db_ligne.paye,
        disponible=db_ligne.budget_modifie - db_ligne.engage,
    )


@router.put("/ligne/{ligne_id}", response_model=LigneBudgetResponse)
async def update_ligne_budget(
    department: DepartmentDep,
    ligne_id: int,
    ligne: LigneBudgetUpdate,
    db: Session = Depends(get_db),
):
    """Update a budget line."""
    db_ligne = budget_crud.update_ligne_budget(db, ligne_id, ligne)
    if not db_ligne:
        raise HTTPException(status_code=404, detail="Ligne budget non trouvée")
    
    return LigneBudgetResponse(
        id=db_ligne.id,
        categorie=CategorieDepense(db_ligne.categorie),
        budget_initial=db_ligne.budget_initial,
        budget_modifie=db_ligne.budget_modifie,
        engage=db_ligne.engage,
        paye=db_ligne.paye,
        disponible=db_ligne.budget_modifie - db_ligne.engage,
    )


@router.delete("/ligne/{ligne_id}")
async def delete_ligne_budget(
    department: DepartmentDep,
    ligne_id: int,
    db: Session = Depends(get_db),
):
    """Delete a budget line."""
    if not budget_crud.delete_ligne_budget(db, ligne_id):
        raise HTTPException(status_code=404, detail="Ligne budget non trouvée")
    return {"message": "Ligne budget supprimée"}


# ==================== DEPENSES ====================

@router.get("/year/{annee}/depenses", response_model=list[DepenseResponse])
async def list_depenses(
    department: DepartmentDep,
    annee: int,
    categorie: Optional[CategorieDepense] = None,
    statut: Optional[str] = Query(None, pattern="^(prevue|engagee|payee)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """List expenses for a year."""
    budget = budget_crud.get_budget_annuel(db, department, annee)
    if not budget:
        raise HTTPException(status_code=404, detail=f"Budget {annee} non trouvé")
    
    depenses = budget_crud.get_depenses(
        db, budget.id, 
        categorie=categorie.value if categorie else None,
        statut=statut,
        skip=skip, 
        limit=limit
    )
    
    return [
        DepenseResponse(
            id=d.id,
            libelle=d.libelle,
            montant=d.montant,
            categorie=CategorieDepense(d.categorie),
            date_depense=d.date_depense,
            fournisseur=d.fournisseur,
            numero_commande=d.numero_commande,
            statut=d.statut,
        )
        for d in depenses
    ]


@router.post("/year/{annee}/depense", response_model=DepenseResponse)
async def create_depense(
    department: DepartmentDep,
    annee: int,
    depense: DepenseCreate,
    db: Session = Depends(get_db),
):
    """Create a new expense."""
    budget = budget_crud.get_or_create_budget_annuel(db, department, annee)
    db_depense = budget_crud.create_depense(db, budget.id, depense)
    
    return DepenseResponse(
        id=db_depense.id,
        libelle=db_depense.libelle,
        montant=db_depense.montant,
        categorie=CategorieDepense(db_depense.categorie),
        date_depense=db_depense.date_depense,
        fournisseur=db_depense.fournisseur,
        numero_commande=db_depense.numero_commande,
        statut=db_depense.statut,
    )


@router.put("/depense/{depense_id}", response_model=DepenseResponse)
async def update_depense(
    department: DepartmentDep,
    depense_id: int,
    depense: DepenseUpdate,
    db: Session = Depends(get_db),
):
    """Update an expense."""
    db_depense = budget_crud.update_depense(db, depense_id, depense)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Dépense non trouvée")
    
    return DepenseResponse(
        id=db_depense.id,
        libelle=db_depense.libelle,
        montant=db_depense.montant,
        categorie=CategorieDepense(db_depense.categorie),
        date_depense=db_depense.date_depense,
        fournisseur=db_depense.fournisseur,
        numero_commande=db_depense.numero_commande,
        statut=db_depense.statut,
    )


@router.delete("/depense/{depense_id}")
async def delete_depense(
    department: DepartmentDep,
    depense_id: int,
    db: Session = Depends(get_db),
):
    """Delete an expense."""
    if not budget_crud.delete_depense(db, depense_id):
        raise HTTPException(status_code=404, detail="Dépense non trouvée")
    return {"message": "Dépense supprimée"}


# ==================== IMPORT ====================

@router.post("/import", response_model=ImportResult)
async def import_budget_file(
    department: DepartmentDep,
    file: UploadFile = File(..., description="Budget Excel file"),
    annee: int = Query(..., description="Année budgétaire"),
    db: Session = Depends(get_db),
):
    """
    Import budget from Excel file.
    
    Expected columns: Catégorie, Budget Initial, Budget Modifié, Engagé, Payé
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    result = budget_crud.import_budget_from_excel(db, department, content, annee)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


# ==================== INDICATORS (pour dashboard) ====================

@router.get("/indicators", response_model=BudgetIndicators)
async def get_budget_indicators(
    department: DepartmentDep,
    annee: Optional[int] = Query(None, description="Année budgétaire"),
    db: Session = Depends(get_db),
):
    """
    Get budget indicators for dashboard.
    Returns data from database or empty/default if no data.
    If no year specified, uses the most recent budget year.
    """
    budget = None
    
    if annee is not None:
        budget = budget_crud.get_budget_annuel(db, department, annee)
    else:
        # Try current year first, then get latest available
        budget = budget_crud.get_budget_annuel(db, department, date.today().year)
        if not budget:
            budget = budget_crud.get_latest_budget(db, department)
    
    if not budget:
        # Return empty indicators
        return BudgetIndicators(
            annee=annee or date.today().year,
            budget_total=0,
            total_engage=0,
            total_paye=0,
            total_disponible=0,
            taux_execution=0,
            taux_engagement=0,
            par_categorie=[],
            evolution_mensuelle={},
            top_depenses=[],
            previsionnel=0,
            realise=0,
        )
    
    annee = budget.annee
    stats = budget_crud.get_budget_stats(db, department, annee)
    evolution = budget_crud.get_evolution_mensuelle(db, budget.id)
    
    # Get top expenses
    depenses_db = budget_crud.get_depenses(db, budget.id, limit=10)
    top_depenses = [
        Depense(
            id=str(d.id),
            libelle=d.libelle,
            montant=d.montant,
            categorie=CategorieDepenseEnum(d.categorie),
            date=d.date_depense,
            fournisseur=d.fournisseur,
            numero_commande=d.numero_commande,
            statut=d.statut,
        )
        for d in sorted(depenses_db, key=lambda x: x.montant, reverse=True)[:10]
    ]
    
    # Build par_categorie
    par_categorie = [
        LigneBudget(
            categorie=CategorieDepenseEnum(l.categorie),
            budget_initial=l.budget_initial,
            budget_modifie=l.budget_modifie,
            engage=l.engage,
            paye=l.paye,
            disponible=l.budget_modifie - l.engage,
        )
        for l in budget.lignes
    ]
    
    return BudgetIndicators(
        annee=annee,
        budget_total=stats.get("budget_total", 0),
        total_engage=stats.get("total_engage", 0),
        total_paye=stats.get("total_paye", 0),
        total_disponible=stats.get("total_disponible", 0),
        taux_execution=stats.get("taux_execution", 0),
        taux_engagement=stats.get("taux_engagement", 0),
        par_categorie=par_categorie,
        evolution_mensuelle=evolution,
        top_depenses=top_depenses,
        previsionnel=budget.previsionnel,
        realise=stats.get("total_paye", 0),
    )
