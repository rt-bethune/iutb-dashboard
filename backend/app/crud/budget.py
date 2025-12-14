"""CRUD operations for Budget (department-scoped)."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date
import io
import pandas as pd

from app.models.db_models import BudgetAnnuel, LigneBudgetDB, DepenseDB
from app.schemas.budget import (
    BudgetAnnuelCreate,
    BudgetAnnuelUpdate,
    LigneBudgetCreate,
    LigneBudgetUpdate,
    DepenseCreate,
    DepenseUpdate,
    ImportResult,
)


# ==================== BUDGET ANNUEL ====================

def get_budget_annuel(db: Session, department: str, annee: int) -> Optional[BudgetAnnuel]:
    """Get budget for a specific department and year."""
    return db.query(BudgetAnnuel).filter(
        BudgetAnnuel.department == department,
        BudgetAnnuel.annee == annee
    ).first()


def get_budget_annuel_by_id(db: Session, budget_id: int) -> Optional[BudgetAnnuel]:
    """Get budget by ID."""
    return db.query(BudgetAnnuel).filter(BudgetAnnuel.id == budget_id).first()


def get_latest_budget(db: Session, department: str) -> Optional[BudgetAnnuel]:
    """Get the most recent budget for a department."""
    return db.query(BudgetAnnuel).filter(
        BudgetAnnuel.department == department
    ).order_by(BudgetAnnuel.annee.desc()).first()


def get_all_budgets(db: Session, department: str, skip: int = 0, limit: int = 100) -> list[BudgetAnnuel]:
    """Get all budgets for a department."""
    return db.query(BudgetAnnuel).filter(
        BudgetAnnuel.department == department
    ).order_by(BudgetAnnuel.annee.desc()).offset(skip).limit(limit).all()


def create_budget_annuel(db: Session, department: str, budget: BudgetAnnuelCreate) -> BudgetAnnuel:
    """Create a new annual budget for a department."""
    db_budget = BudgetAnnuel(
        department=department,
        annee=budget.annee,
        budget_total=budget.budget_total,
        previsionnel=budget.previsionnel,
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    
    # Create initial budget lines if provided
    if budget.lignes:
        for ligne in budget.lignes:
            create_ligne_budget(db, db_budget.id, ligne)
    
    return db_budget


def update_budget_annuel(db: Session, department: str, annee: int, budget: BudgetAnnuelUpdate) -> Optional[BudgetAnnuel]:
    """Update an annual budget."""
    db_budget = get_budget_annuel(db, department, annee)
    if not db_budget:
        return None
    
    update_data = budget.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_budget, field, value)
    
    db_budget.date_modification = date.today()
    db.commit()
    db.refresh(db_budget)
    return db_budget


def delete_budget_annuel(db: Session, department: str, annee: int) -> bool:
    """Delete an annual budget and all related data."""
    db_budget = get_budget_annuel(db, department, annee)
    if not db_budget:
        return False
    
    db.delete(db_budget)
    db.commit()
    return True


def get_or_create_budget_annuel(db: Session, department: str, annee: int) -> BudgetAnnuel:
    """Get existing budget or create a new one."""
    budget = get_budget_annuel(db, department, annee)
    if not budget:
        budget = create_budget_annuel(db, department, BudgetAnnuelCreate(annee=annee))
    return budget


# ==================== LIGNE BUDGET ====================

def get_lignes_budget(db: Session, budget_id: int) -> list[LigneBudgetDB]:
    """Get all budget lines for a budget."""
    return db.query(LigneBudgetDB).filter(LigneBudgetDB.budget_annuel_id == budget_id).all()


def get_ligne_budget(db: Session, ligne_id: int) -> Optional[LigneBudgetDB]:
    """Get a specific budget line."""
    return db.query(LigneBudgetDB).filter(LigneBudgetDB.id == ligne_id).first()


def get_ligne_by_categorie(db: Session, budget_id: int, categorie: str) -> Optional[LigneBudgetDB]:
    """Get budget line by category."""
    return db.query(LigneBudgetDB).filter(
        LigneBudgetDB.budget_annuel_id == budget_id,
        LigneBudgetDB.categorie == categorie
    ).first()


def create_ligne_budget(db: Session, budget_id: int, ligne: LigneBudgetCreate) -> LigneBudgetDB:
    """Create a new budget line."""
    db_ligne = LigneBudgetDB(
        budget_annuel_id=budget_id,
        categorie=ligne.categorie.value,
        budget_initial=ligne.budget_initial,
        budget_modifie=ligne.budget_modifie or ligne.budget_initial,
        engage=ligne.engage,
        paye=ligne.paye,
    )
    db.add(db_ligne)
    db.commit()
    db.refresh(db_ligne)
    return db_ligne


def update_ligne_budget(db: Session, ligne_id: int, ligne: LigneBudgetUpdate) -> Optional[LigneBudgetDB]:
    """Update a budget line."""
    db_ligne = get_ligne_budget(db, ligne_id)
    if not db_ligne:
        return None
    
    update_data = ligne.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ligne, field, value)
    
    db.commit()
    db.refresh(db_ligne)
    return db_ligne


def delete_ligne_budget(db: Session, ligne_id: int) -> bool:
    """Delete a budget line."""
    db_ligne = get_ligne_budget(db, ligne_id)
    if not db_ligne:
        return False
    
    db.delete(db_ligne)
    db.commit()
    return True


# ==================== DEPENSE ====================

def get_depenses(
    db: Session,
    budget_id: int,
    categorie: Optional[str] = None,
    statut: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> list[DepenseDB]:
    """Get expenses with optional filters."""
    query = db.query(DepenseDB).filter(DepenseDB.budget_annuel_id == budget_id)
    
    if categorie:
        query = query.filter(DepenseDB.categorie == categorie)
    if statut:
        query = query.filter(DepenseDB.statut == statut)
    
    return query.order_by(DepenseDB.date_depense.desc()).offset(skip).limit(limit).all()


def get_depense(db: Session, depense_id: int) -> Optional[DepenseDB]:
    """Get a specific expense."""
    return db.query(DepenseDB).filter(DepenseDB.id == depense_id).first()


def create_depense(db: Session, budget_id: int, depense: DepenseCreate) -> DepenseDB:
    """Create a new expense."""
    db_depense = DepenseDB(
        budget_annuel_id=budget_id,
        libelle=depense.libelle,
        montant=depense.montant,
        categorie=depense.categorie.value,
        date_depense=depense.date_depense,
        fournisseur=depense.fournisseur,
        numero_commande=depense.numero_commande,
        statut=depense.statut,
    )
    db.add(db_depense)
    db.commit()
    db.refresh(db_depense)
    
    # Update budget line totals
    _update_ligne_from_depenses(db, budget_id, depense.categorie.value)
    
    return db_depense


def update_depense(db: Session, depense_id: int, depense: DepenseUpdate) -> Optional[DepenseDB]:
    """Update an expense."""
    db_depense = get_depense(db, depense_id)
    if not db_depense:
        return None
    
    old_categorie = db_depense.categorie
    old_budget_id = db_depense.budget_annuel_id
    
    update_data = depense.model_dump(exclude_unset=True)
    if "categorie" in update_data and update_data["categorie"]:
        update_data["categorie"] = update_data["categorie"].value
    
    for field, value in update_data.items():
        setattr(db_depense, field, value)
    
    db.commit()
    db.refresh(db_depense)
    
    # Update budget line totals
    _update_ligne_from_depenses(db, old_budget_id, old_categorie)
    if db_depense.categorie != old_categorie:
        _update_ligne_from_depenses(db, db_depense.budget_annuel_id, db_depense.categorie)
    
    return db_depense


def delete_depense(db: Session, depense_id: int) -> bool:
    """Delete an expense."""
    db_depense = get_depense(db, depense_id)
    if not db_depense:
        return False
    
    budget_id = db_depense.budget_annuel_id
    categorie = db_depense.categorie
    
    db.delete(db_depense)
    db.commit()
    
    # Update budget line totals
    _update_ligne_from_depenses(db, budget_id, categorie)
    
    return True


def _update_ligne_from_depenses(db: Session, budget_id: int, categorie: str):
    """Update budget line totals from expenses."""
    ligne = get_ligne_by_categorie(db, budget_id, categorie)
    if not ligne:
        return
    
    # Calculate totals from expenses
    result = db.query(
        func.sum(DepenseDB.montant).filter(DepenseDB.statut.in_(["engagee", "payee"])).label("engage"),
        func.sum(DepenseDB.montant).filter(DepenseDB.statut == "payee").label("paye"),
    ).filter(
        DepenseDB.budget_annuel_id == budget_id,
        DepenseDB.categorie == categorie
    ).first()
    
    ligne.engage = result.engage or 0
    ligne.paye = result.paye or 0
    db.commit()


# ==================== IMPORT EXCEL ====================

def import_budget_from_excel(db: Session, department: str, file_content: bytes, annee: int) -> ImportResult:
    """Import budget data from Excel file for a department."""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        df.columns = df.columns.str.lower().str.strip()
        
        # Get or create budget for the department and year
        budget = get_or_create_budget_annuel(db, department, annee)
        
        lignes_importees = 0
        depenses_importees = 0
        erreurs = []
        
        # Map category names
        cat_map = {
            "fonctionnement": "fonctionnement",
            "investissement": "investissement",
            "missions": "missions",
            "fournitures": "fournitures",
            "maintenance": "maintenance",
            "formation": "formation",
        }
        
        for idx, row in df.iterrows():
            try:
                cat_str = str(row.get("catégorie", row.get("categorie", "autre"))).lower().strip()
                categorie = cat_map.get(cat_str, "autre")
                
                budget_initial = float(row.get("budget initial", row.get("budget_initial", 0)) or 0)
                budget_modifie = float(row.get("budget modifié", row.get("budget_modifie", budget_initial)) or budget_initial)
                engage = float(row.get("engagé", row.get("engage", 0)) or 0)
                paye = float(row.get("payé", row.get("paye", 0)) or 0)
                
                # Check if ligne exists
                existing = get_ligne_by_categorie(db, budget.id, categorie)
                if existing:
                    existing.budget_initial = budget_initial
                    existing.budget_modifie = budget_modifie
                    existing.engage = engage
                    existing.paye = paye
                else:
                    db_ligne = LigneBudgetDB(
                        budget_annuel_id=budget.id,
                        categorie=categorie,
                        budget_initial=budget_initial,
                        budget_modifie=budget_modifie,
                        engage=engage,
                        paye=paye,
                    )
                    db.add(db_ligne)
                
                lignes_importees += 1
                
            except Exception as e:
                erreurs.append(f"Ligne {idx + 2}: {str(e)}")
        
        # Update budget total
        budget.budget_total = sum(l.budget_initial for l in budget.lignes)
        budget.date_modification = date.today()
        
        db.commit()
        
        return ImportResult(
            success=True,
            message=f"Import réussi pour l'année {annee}",
            annee=annee,
            lignes_importees=lignes_importees,
            depenses_importees=depenses_importees,
            erreurs=erreurs,
        )
        
    except Exception as e:
        db.rollback()
        return ImportResult(
            success=False,
            message=f"Erreur lors de l'import: {str(e)}",
            annee=annee,
            erreurs=[str(e)],
        )


# ==================== STATISTICS ====================

def get_budget_stats(db: Session, department: str, annee: int) -> dict:
    """Get budget statistics for a department and year."""
    budget = get_budget_annuel(db, department, annee)
    if not budget:
        return {}
    
    total_initial = sum(l.budget_initial for l in budget.lignes)
    total_modifie = sum(l.budget_modifie for l in budget.lignes)
    total_engage = sum(l.engage for l in budget.lignes)
    total_paye = sum(l.paye for l in budget.lignes)
    total_disponible = total_modifie - total_engage
    
    return {
        "annee": annee,
        "department": department,
        "budget_total": total_initial,
        "total_engage": total_engage,
        "total_paye": total_paye,
        "total_disponible": total_disponible,
        "taux_execution": total_paye / total_initial if total_initial > 0 else 0,
        "taux_engagement": total_engage / total_initial if total_initial > 0 else 0,
    }


def get_evolution_mensuelle(db: Session, budget_id: int) -> dict[str, float]:
    """Get monthly spending evolution (database agnostic)."""
    # Fetch all expenses and aggregate in Python (works with both SQLite and PostgreSQL)
    depenses = db.query(DepenseDB).filter(
        DepenseDB.budget_annuel_id == budget_id,
        DepenseDB.statut == "payee"
    ).all()
    
    evolution = {}
    for dep in depenses:
        mois = dep.date_depense.strftime("%Y-%m")
        evolution[mois] = evolution.get(mois, 0) + dep.montant
    
    return evolution
