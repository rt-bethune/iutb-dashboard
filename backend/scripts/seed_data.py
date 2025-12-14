#!/usr/bin/env python3
"""
Seed script for populating the database with test data.

Usage:
    cd backend
    python -m scripts.seed_data

Or with explicit venv:
    source venv/bin/activate
    python -m scripts.seed_data
"""

import sys
import os
import json
import random
from datetime import date, timedelta

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.db_models import (
    DEPARTMENTS,
    BudgetAnnuel, LigneBudgetDB, DepenseDB,
    CampagneRecrutement, CandidatDB, StatistiquesParcoursup,
    EdtAnnuel, EnseignantChargeDB, SalleOccupationDB,
)


# ==================== CONFIGURATION ====================

CURRENT_YEAR = 2024
YEARS_TO_SEED = [2022, 2023, 2024]
ANNEES_UNIVERSITAIRES = ["2022-2023", "2023-2024", "2024-2025"]

# Department-specific configurations (realistic data)
DEPT_CONFIG = {
    "RT": {
        "nom_complet": "Réseaux & Télécommunications",
        "nb_places": 84,
        "budget_base": 120000,
        "nb_enseignants": 12,
        "salles": ["RT-TD1", "RT-TD2", "RT-TP1", "RT-TP2", "RT-TP3", "RT-Projet"],
    },
    "GEII": {
        "nom_complet": "Génie Électrique et Informatique Industrielle",
        "nb_places": 72,
        "budget_base": 150000,
        "nb_enseignants": 14,
        "salles": ["GEII-TD1", "GEII-TD2", "GEII-TP1", "GEII-TP2", "GEII-Labo"],
    },
    "GCCD": {
        "nom_complet": "Génie Civil - Construction Durable",
        "nb_places": 56,
        "budget_base": 100000,
        "nb_enseignants": 10,
        "salles": ["GCCD-TD1", "GCCD-TD2", "GCCD-TP1", "GCCD-Atelier"],
    },
    "GMP": {
        "nom_complet": "Génie Mécanique et Productique",
        "nb_places": 64,
        "budget_base": 180000,
        "nb_enseignants": 11,
        "salles": ["GMP-TD1", "GMP-TD2", "GMP-TP1", "GMP-Atelier1", "GMP-Atelier2"],
    },
    "QLIO": {
        "nom_complet": "Qualité, Logistique Industrielle et Organisation",
        "nb_places": 48,
        "budget_base": 80000,
        "nb_enseignants": 8,
        "salles": ["QLIO-TD1", "QLIO-TD2", "QLIO-TP1"],
    },
    "CHIMIE": {
        "nom_complet": "Chimie",
        "nb_places": 52,
        "budget_base": 200000,
        "nb_enseignants": 10,
        "salles": ["CHIM-TD1", "CHIM-TP1", "CHIM-TP2", "CHIM-Labo1", "CHIM-Labo2"],
    },
}

CATEGORIES_BUDGET = [
    "fonctionnement",
    "investissement",
    "missions",
    "fournitures",
    "maintenance",
    "formation",
]

TYPES_BAC = ["Général", "Technologique", "Professionnel"]
MENTIONS_BAC = ["Très Bien", "Bien", "Assez Bien", "Passable", None]
STATUTS_CANDIDAT = ["confirme", "accepte", "refuse", "desiste", "en_attente"]

DEPARTEMENTS_ORIGINE = [
    "Nord", "Pas-de-Calais", "Somme", "Aisne", "Oise",
    "Seine-Maritime", "Ardennes", "Marne", "Paris", "Autre"
]

LYCEES = [
    "Lycée Faidherbe", "Lycée Jean Bart", "Lycée Gambetta",
    "Lycée Pasteur", "Lycée Voltaire", "Lycée Carnot",
    "Lycée Colbert", "Lycée Baggio", "Lycée Châtelet",
    "Lycée Saint-Paul", "Lycée privé Saint-Jacques",
]

PRENOMS = [
    "Lucas", "Emma", "Hugo", "Chloé", "Nathan", "Léa", "Maxime", "Manon",
    "Thomas", "Camille", "Mathis", "Sarah", "Enzo", "Julie", "Louis", "Laura",
]

NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Petit", "Durand",
    "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia",
]

STATUTS_ENSEIGNANT = ["permanent", "vacataire", "contractuel", "PRAG", "MCF"]


def clear_database(db: Session):
    """Clear all seeded tables."""
    print("🗑️  Clearing existing data...")
    
    # Delete in order due to foreign keys
    db.query(DepenseDB).delete()
    db.query(LigneBudgetDB).delete()
    db.query(BudgetAnnuel).delete()
    
    db.query(CandidatDB).delete()
    db.query(StatistiquesParcoursup).delete()
    db.query(CampagneRecrutement).delete()
    
    db.query(EnseignantChargeDB).delete()
    db.query(SalleOccupationDB).delete()
    db.query(EdtAnnuel).delete()
    
    db.commit()
    print("✅ Database cleared")


def seed_budget(db: Session, department: str, annee: int, config: dict):
    """Seed budget data for a department and year."""
    # Variation par année
    year_factor = 1 + (annee - 2022) * 0.03  # +3% par an
    budget_total = config["budget_base"] * year_factor
    
    # Create budget annuel
    budget = BudgetAnnuel(
        department=department,
        annee=annee,
        budget_total=budget_total,
        previsionnel=budget_total * 0.95,
    )
    db.add(budget)
    db.flush()  # Get ID
    
    # Create lignes budget
    repartition = {
        "fonctionnement": 0.30,
        "investissement": 0.25,
        "missions": 0.10,
        "fournitures": 0.15,
        "maintenance": 0.12,
        "formation": 0.08,
    }
    
    for categorie, ratio in repartition.items():
        budget_initial = budget_total * ratio
        # Variation aléatoire pour budget modifié
        budget_modifie = budget_initial * random.uniform(0.95, 1.05)
        # Engagement et paiement dépendent de l'avancement de l'année
        if annee < CURRENT_YEAR:
            # Années passées : presque tout engagé/payé
            engage = budget_modifie * random.uniform(0.90, 0.98)
            paye = engage * random.uniform(0.85, 0.95)
        else:
            # Année en cours : partiellement engagé
            engage = budget_modifie * random.uniform(0.50, 0.70)
            paye = engage * random.uniform(0.60, 0.80)
        
        ligne = LigneBudgetDB(
            budget_annuel_id=budget.id,
            categorie=categorie,
            budget_initial=round(budget_initial, 2),
            budget_modifie=round(budget_modifie, 2),
            engage=round(engage, 2),
            paye=round(paye, 2),
        )
        db.add(ligne)
    
    # Create some depenses
    fournisseurs = ["Amazon", "LDLC", "Darty Pro", "Manutan", "Lyreco", "RS Components"]
    nb_depenses = random.randint(15, 30)
    
    for i in range(nb_depenses):
        categorie = random.choice(CATEGORIES_BUDGET)
        montant = random.uniform(50, 5000)
        jour = random.randint(1, 28)
        mois = random.randint(1, 12 if annee < CURRENT_YEAR else 12)
        
        statut = "payee" if annee < CURRENT_YEAR else random.choice(["prevue", "engagee", "payee"])
        
        depense = DepenseDB(
            budget_annuel_id=budget.id,
            libelle=f"Dépense {department} - {categorie} #{i+1}",
            montant=round(montant, 2),
            categorie=categorie,
            date_depense=date(annee, mois, jour),
            fournisseur=random.choice(fournisseurs),
            numero_commande=f"CMD-{annee}-{department}-{i+1:04d}",
            statut=statut,
        )
        db.add(depense)
    
    return budget


def seed_recrutement(db: Session, department: str, annee: int, config: dict):
    """Seed recruitment/Parcoursup data for a department and year."""
    nb_places = config["nb_places"]
    
    # Nombre de voeux (plus que les places disponibles)
    nb_voeux = int(nb_places * random.uniform(3.5, 5.0))
    
    # Create campagne
    campagne = CampagneRecrutement(
        department=department,
        annee=annee,
        nb_places=nb_places,
        date_debut=date(annee, 1, 20),
        date_fin=date(annee, 9, 15),
        rang_dernier_appele=int(nb_places * random.uniform(1.5, 2.0)),
    )
    db.add(campagne)
    db.flush()
    
    # Répartition par type de bac selon département
    if department in ["RT", "GEII"]:
        type_bac_weights = [0.45, 0.45, 0.10]  # Plus de techno
    elif department == "CHIMIE":
        type_bac_weights = [0.60, 0.30, 0.10]  # Plus de général
    else:
        type_bac_weights = [0.40, 0.45, 0.15]
    
    # Counters for stats
    stats_type_bac = {}
    stats_mention = {}
    stats_origine = {}
    stats_lycees = {}
    nb_acceptes = 0
    nb_confirmes = 0
    nb_refuses = 0
    nb_desistes = 0
    
    # Generate candidats
    for i in range(nb_voeux):
        type_bac = random.choices(TYPES_BAC, weights=type_bac_weights)[0]
        mention = random.choice(MENTIONS_BAC)
        dept_origine = random.choices(
            DEPARTEMENTS_ORIGINE,
            weights=[0.30, 0.25, 0.10, 0.08, 0.07, 0.05, 0.05, 0.04, 0.03, 0.03]
        )[0]
        lycee = random.choice(LYCEES)
        
        # Statut basé sur le rang
        rang = i + 1
        if rang <= nb_places:
            statut = random.choices(
                ["confirme", "accepte", "desiste"],
                weights=[0.70, 0.20, 0.10]
            )[0]
        elif rang <= nb_places * 1.5:
            statut = random.choices(
                ["confirme", "accepte", "refuse", "desiste", "en_attente"],
                weights=[0.30, 0.20, 0.25, 0.15, 0.10]
            )[0]
        else:
            statut = random.choices(
                ["refuse", "en_attente", "desiste"],
                weights=[0.60, 0.25, 0.15]
            )[0]
        
        candidat = CandidatDB(
            campagne_id=campagne.id,
            numero_candidat=f"PS{annee}{department[:2]}{i+1:05d}",
            nom=random.choice(NOMS),
            prenom=random.choice(PRENOMS),
            type_bac=type_bac,
            serie_bac="STI2D" if type_bac == "Technologique" else None,
            mention_bac=mention,
            annee_bac=annee,
            departement_origine=dept_origine,
            pays_origine="France",
            lycee=lycee,
            rang_voeu=random.randint(1, 10),
            rang_appel=rang,
            statut=statut,
        )
        db.add(candidat)
        
        # Update stats
        stats_type_bac[type_bac] = stats_type_bac.get(type_bac, 0) + 1
        if mention:
            stats_mention[mention] = stats_mention.get(mention, 0) + 1
        stats_origine[dept_origine] = stats_origine.get(dept_origine, 0) + 1
        stats_lycees[lycee] = stats_lycees.get(lycee, 0) + 1
        
        if statut in ["accepte", "confirme"]:
            nb_acceptes += 1
        if statut == "confirme":
            nb_confirmes += 1
        if statut == "refuse":
            nb_refuses += 1
        if statut == "desiste":
            nb_desistes += 1
    
    # Create stats record
    stats = StatistiquesParcoursup(
        department=department,
        annee=annee,
        nb_voeux=nb_voeux,
        nb_acceptes=nb_acceptes,
        nb_confirmes=nb_confirmes,
        nb_refuses=nb_refuses,
        nb_desistes=nb_desistes,
        par_type_bac=json.dumps(stats_type_bac),
        par_mention=json.dumps(stats_mention),
        par_origine=json.dumps(stats_origine),
        par_lycees=json.dumps(stats_lycees),
    )
    db.add(stats)
    
    return campagne


def seed_edt(db: Session, department: str, annee_univ: str, config: dict):
    """Seed EDT (schedule) data for a department and academic year."""
    # Extract first year from "2024-2025"
    annee = int(annee_univ.split("-")[0])
    
    # Create EDT annuel
    heures_prevues = config["nb_enseignants"] * 192 * 1.2  # 192h service + 20% vacataires
    heures_effectuees = heures_prevues * random.uniform(0.85, 1.05)
    
    edt = EdtAnnuel(
        department=department,
        annee=annee_univ,
        heures_prevues_total=round(heures_prevues, 1),
        heures_effectuees_total=round(heures_effectuees, 1),
    )
    db.add(edt)
    db.flush()
    
    # Create enseignants
    for i in range(config["nb_enseignants"]):
        statut = random.choices(
            STATUTS_ENSEIGNANT,
            weights=[0.50, 0.20, 0.10, 0.10, 0.10]
        )[0]
        
        if statut in ["PRAG", "permanent"]:
            heures_service = 384
        elif statut == "MCF":
            heures_service = 192
        else:
            heures_service = random.randint(50, 150)
        
        heures_cm = random.uniform(0, heures_service * 0.2)
        heures_td = random.uniform(heures_service * 0.3, heures_service * 0.5)
        heures_tp = heures_service - heures_cm * 1.5 - heures_td  # Reste en TP
        heures_total = heures_cm * 1.5 + heures_td + heures_tp * 0.67  # Équivalent TD
        heures_comp = max(0, heures_total - heures_service)
        
        enseignant = EnseignantChargeDB(
            edt_annuel_id=edt.id,
            nom=random.choice(NOMS),
            prenom=random.choice(PRENOMS),
            statut=statut,
            heures_service=heures_service,
            heures_cm=round(heures_cm, 1),
            heures_td=round(heures_td, 1),
            heures_tp=round(max(0, heures_tp), 1),
            heures_total=round(heures_total, 1),
            heures_complementaires=round(heures_comp, 1),
        )
        db.add(enseignant)
    
    # Create salles
    for salle_nom in config["salles"]:
        type_salle = "TP" if "TP" in salle_nom or "Labo" in salle_nom or "Atelier" in salle_nom else "TD"
        capacite = 30 if type_salle == "TD" else 15
        
        # Heures disponibles : 35h/semaine * 30 semaines
        heures_dispo = 35 * 30
        taux = random.uniform(0.50, 0.85)
        heures_occupees = heures_dispo * taux
        
        salle = SalleOccupationDB(
            edt_annuel_id=edt.id,
            nom_salle=salle_nom,
            type_salle=type_salle,
            capacite=capacite,
            heures_occupees=round(heures_occupees, 1),
            heures_disponibles=round(heures_dispo, 1),
            taux_occupation=round(taux * 100, 1),
        )
        db.add(salle)
    
    return edt


def seed_all(db: Session, clear_first: bool = True):
    """Seed all test data."""
    print("🌱 Starting database seeding...")
    print(f"   Departments: {', '.join(DEPARTMENTS)}")
    print(f"   Years: {', '.join(map(str, YEARS_TO_SEED))}")
    print()
    
    if clear_first:
        clear_database(db)
    
    # Seed data for each department and year
    for dept in DEPARTMENTS:
        config = DEPT_CONFIG[dept]
        print(f"📁 Seeding {dept} ({config['nom_complet']})...")
        
        for annee in YEARS_TO_SEED:
            # Budget
            seed_budget(db, dept, annee, config)
            
            # Recrutement
            seed_recrutement(db, dept, annee, config)
        
        # EDT (années universitaires)
        for annee_univ in ANNEES_UNIVERSITAIRES:
            seed_edt(db, dept, annee_univ, config)
        
        db.commit()
        print(f"   ✅ {dept} seeded successfully")
    
    print()
    print("🎉 Database seeding completed!")
    print_stats(db)


def print_stats(db: Session):
    """Print statistics about seeded data."""
    print("\n📊 Seeding Statistics:")
    print("-" * 50)
    
    for dept in DEPARTMENTS:
        budgets = db.query(BudgetAnnuel).filter(BudgetAnnuel.department == dept).count()
        campagnes = db.query(CampagneRecrutement).filter(CampagneRecrutement.department == dept).count()
        candidats = db.query(CandidatDB).join(CampagneRecrutement).filter(
            CampagneRecrutement.department == dept
        ).count()
        edts = db.query(EdtAnnuel).filter(EdtAnnuel.department == dept).count()
        
        print(f"\n{dept}:")
        print(f"  - Budgets: {budgets} years")
        print(f"  - Campagnes: {campagnes} years ({candidats} candidats)")
        print(f"  - EDT: {edts} years")
    
    print("-" * 50)
    total_budgets = db.query(BudgetAnnuel).count()
    total_candidats = db.query(CandidatDB).count()
    total_enseignants = db.query(EnseignantChargeDB).count()
    print(f"\nTotal: {total_budgets} budgets, {total_candidats} candidats, {total_enseignants} enseignants")


def main():
    """Main entry point."""
    print("=" * 60)
    print("  Dept-Dashboard Database Seeder")
    print("=" * 60)
    print()
    
    # Create tables if they don't exist
    print("📦 Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables ready")
    print()
    
    # Create session and seed
    db = SessionLocal()
    try:
        seed_all(db, clear_first=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
