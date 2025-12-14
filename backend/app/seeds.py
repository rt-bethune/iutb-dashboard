"""Database seeder for mock/demo data."""

import logging
import json
from datetime import date, timedelta
import random
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.db_models import (
    Base, UserDB, UserPermissionDB, DEPARTMENTS,
    BudgetAnnuel, LigneBudgetDB, DepenseDB,
    CampagneRecrutement, CandidatDB, StatistiquesParcoursup,
)

logger = logging.getLogger(__name__)

# Sample users with different roles
MOCK_USERS = [
    {
        "cas_login": "admin",
        "email": "admin@iut.fr",
        "nom": "Administrateur",
        "prenom": "Super",
        "is_active": True,
        "is_superadmin": True,
    },
    {
        "cas_login": "chef_rt",
        "email": "chef.rt@iut.fr",
        "nom": "Martin",
        "prenom": "Jean",
        "is_active": False,
        "is_superadmin": False,
    },
    {
        "cas_login": "chef_geii",
        "email": "chef.geii@iut.fr",
        "nom": "Dupont",
        "prenom": "Marie",
        "is_active": False,
        "is_superadmin": False,
    },
    {
        "cas_login": "enseignant_rt",
        "email": "enseignant.rt@iut.fr",
        "nom": "Bernard",
        "prenom": "Pierre",
        "is_active": False,
        "is_superadmin": False,
    },
    {
        "cas_login": "secretaire",
        "email": "secretaire@iut.fr",
        "nom": "Lefebvre",
        "prenom": "Sophie",
        "is_active": False,
        "is_superadmin": False,
    },
    {
        "cas_login": "pending_user",
        "email": "pending@iut.fr",
        "nom": "Nouveau",
        "prenom": "Utilisateur",
        "is_active": False,  # Not yet validated
        "is_superadmin": False,
    },
]

# Permissions for each user (user_index -> permissions)
MOCK_PERMISSIONS = {
    # chef_rt: Full admin for RT department
    1: [
        {
            "department": "RT",
            "is_dept_admin": True,
            "can_view_scolarite": True,
            "can_edit_scolarite": True,
            "can_view_recrutement": True,
            "can_edit_recrutement": True,
            "can_view_budget": True,
            "can_edit_budget": True,
            "can_view_edt": True,
            "can_edit_edt": True,
            "can_import": True,
            "can_export": True,
        },
    ],
    # chef_geii: Full admin for GEII department
    2: [
        {
            "department": "GEII",
            "is_dept_admin": True,
            "can_view_scolarite": True,
            "can_edit_scolarite": True,
            "can_view_recrutement": True,
            "can_edit_recrutement": True,
            "can_view_budget": True,
            "can_edit_budget": True,
            "can_view_edt": True,
            "can_edit_edt": True,
            "can_import": True,
            "can_export": True,
        },
    ],
    # enseignant_rt: View only for RT (typical teacher)
    3: [
        {
            "department": "RT",
            "is_dept_admin": False,
            "can_view_scolarite": True,
            "can_edit_scolarite": False,
            "can_view_recrutement": False,
            "can_edit_recrutement": False,
            "can_view_budget": False,
            "can_edit_budget": False,
            "can_view_edt": True,
            "can_edit_edt": False,
            "can_import": False,
            "can_export": True,
        },
    ],
    # secretaire: View scolarite/recrutement for multiple departments
    4: [
        {
            "department": "RT",
            "is_dept_admin": False,
            "can_view_scolarite": True,
            "can_edit_scolarite": True,
            "can_view_recrutement": True,
            "can_edit_recrutement": True,
            "can_view_budget": False,
            "can_edit_budget": False,
            "can_view_edt": False,
            "can_edit_edt": False,
            "can_import": True,
            "can_export": True,
        },
        {
            "department": "GEII",
            "is_dept_admin": False,
            "can_view_scolarite": True,
            "can_edit_scolarite": True,
            "can_view_recrutement": True,
            "can_edit_recrutement": True,
            "can_view_budget": False,
            "can_edit_budget": False,
            "can_view_edt": False,
            "can_edit_edt": False,
            "can_import": True,
            "can_export": True,
        },
    ],
}


def seed_database(db: Session, force: bool = False) -> dict:
    """
    Seed the database with mock data.
    
    Args:
        db: Database session
        force: If True, delete existing data before seeding
        
    Returns:
        Summary of seeded data
    """
    summary = {
        "users_created": 0, 
        "permissions_created": 0, 
        "budgets_created": 0,
        "depenses_created": 0,
        "campagnes_created": 0,
        "candidats_created": 0,
        "skipped": False
    }
    
    # Check if data already exists
    existing_users = db.query(UserDB).count()
    if existing_users > 0 and not force:
        logger.info(f"Database already has {existing_users} users. Use force=True to reseed.")
        summary["skipped"] = True
        return summary
    
    if force:
        logger.info("Force mode: Deleting existing data...")
        # Delete in correct order (foreign keys)
        db.query(CandidatDB).delete()
        db.query(StatistiquesParcoursup).delete()
        db.query(CampagneRecrutement).delete()
        db.query(DepenseDB).delete()
        db.query(LigneBudgetDB).delete()
        db.query(BudgetAnnuel).delete()
        db.query(UserPermissionDB).delete()
        db.query(UserDB).delete()
        db.commit()
    
    # Create users
    created_users = []
    for user_data in MOCK_USERS:
        user = UserDB(**user_data)
        db.add(user)
        created_users.append(user)
        summary["users_created"] += 1
    
    db.commit()  # Commit to get user IDs
    
    # Create permissions
    for user_index, permissions in MOCK_PERMISSIONS.items():
        user = created_users[user_index]
        for perm_data in permissions:
            perm = UserPermissionDB(user_id=user.id, **perm_data)
            db.add(perm)
            summary["permissions_created"] += 1
    
    db.commit()
    
    # Seed budget and recruitment data
    budget_result = seed_budget_data(db)
    summary["budgets_created"] = budget_result["budgets_created"]
    summary["depenses_created"] = budget_result["depenses_created"]
    
    recrutement_result = seed_recrutement_data(db)
    summary["campagnes_created"] = recrutement_result["campagnes_created"]
    summary["candidats_created"] = recrutement_result["candidats_created"]
    
    logger.info(f"Seeded {summary['users_created']} users, {summary['permissions_created']} permissions, "
                f"{summary['budgets_created']} budgets, {summary['campagnes_created']} campagnes")
    return summary


# ==================== BUDGET MOCK DATA ====================

BUDGET_CATEGORIES = [
    "fonctionnement", "investissement", "missions", 
    "fournitures", "maintenance", "formation"
]

FOURNISSEURS = [
    "Dell France", "Amazon Business", "LDLC Pro", "Boulanger Pro",
    "Fnac Pro", "Conrad", "RS Components", "Farnell", "Mouser",
    "Office Depot", "Staples", "Manutan", "Würth", "Legrand"
]

DEPENSES_LIBELLES = {
    "fonctionnement": [
        "Licences logicielles annuelles", "Abonnement Microsoft 365", 
        "Maintenance serveurs", "Consommables impression", "Petit matériel pédagogique"
    ],
    "investissement": [
        "Serveur Dell PowerEdge", "Switches Cisco", "Bornes WiFi Aruba",
        "PC portables étudiants", "Écrans interactifs", "Vidéoprojecteurs"
    ],
    "missions": [
        "Déplacement conférence", "Frais mission jury", "Visite entreprise",
        "Formation externe", "Participation salon"
    ],
    "fournitures": [
        "Câbles réseau Cat6", "Connecteurs RJ45", "Composants électroniques",
        "Raspberry Pi", "Arduino", "Matériel TP"
    ],
    "maintenance": [
        "Contrat maintenance climatisation", "Réparation équipements",
        "Remplacement pièces", "Maintenance préventive"
    ],
    "formation": [
        "Formation Cisco CCNA", "Certification AWS", "Formation sécurité",
        "MOOC et e-learning", "Conférences techniques"
    ]
}


def seed_budget_data(db: Session) -> dict:
    """Seed budget data for all departments."""
    result = {"budgets_created": 0, "depenses_created": 0}
    current_year = date.today().year
    
    # Department-specific budget multipliers (to vary data)
    dept_multipliers = {
        "RT": 1.0, "GEII": 1.2, "GCCD": 0.9, 
        "GMP": 1.1, "QLIO": 0.8, "CHIMIE": 1.3
    }
    
    for dept in DEPARTMENTS:
        multiplier = dept_multipliers.get(dept, 1.0)
        
        # Create budgets for current year and 2 previous years
        for year in range(current_year - 2, current_year + 1):
            budget = BudgetAnnuel(
                department=dept,
                annee=year,
                budget_total=int(150000 * multiplier * (1 + (year - current_year + 2) * 0.05)),
                previsionnel=int(145000 * multiplier * (1 + (year - current_year + 2) * 0.05)),
                date_creation=date(year, 1, 1),
            )
            db.add(budget)
            db.flush()  # Get the ID
            result["budgets_created"] += 1
            
            # Add budget lines per category
            total_budget = budget.budget_total
            remaining = total_budget
            
            for i, cat in enumerate(BUDGET_CATEGORIES):
                # Distribute budget across categories
                if i == len(BUDGET_CATEGORIES) - 1:
                    cat_budget = remaining
                else:
                    cat_budget = int(total_budget * random.uniform(0.1, 0.25))
                    remaining -= cat_budget
                
                # Calculate execution based on year
                if year < current_year:
                    # Past years: 80-95% execution
                    execution_rate = random.uniform(0.80, 0.95)
                else:
                    # Current year: 40-70% execution (in progress)
                    execution_rate = random.uniform(0.40, 0.70)
                
                engage = int(cat_budget * execution_rate * random.uniform(0.9, 1.0))
                paye = int(engage * random.uniform(0.7, 0.95))
                
                ligne = LigneBudgetDB(
                    budget_annuel_id=budget.id,
                    categorie=cat,
                    budget_initial=cat_budget,
                    budget_modifie=int(cat_budget * random.uniform(0.95, 1.05)),
                    engage=engage,
                    paye=paye,
                )
                db.add(ligne)
            
            # Add individual expenses
            num_depenses = random.randint(8, 15)
            for _ in range(num_depenses):
                cat = random.choice(BUDGET_CATEGORIES)
                libelles = DEPENSES_LIBELLES.get(cat, ["Dépense diverse"])
                
                # Random date within the year
                day_offset = random.randint(0, 300)
                expense_date = date(year, 1, 1) + timedelta(days=day_offset)
                if expense_date > date.today():
                    expense_date = date.today() - timedelta(days=random.randint(1, 30))
                
                depense = DepenseDB(
                    budget_annuel_id=budget.id,
                    libelle=random.choice(libelles),
                    montant=random.randint(500, 15000) * multiplier,
                    categorie=cat,
                    date_depense=expense_date,
                    fournisseur=random.choice(FOURNISSEURS),
                    numero_commande=f"CMD-{year}-{random.randint(1000, 9999)}",
                    statut=random.choice(["engagee", "payee", "payee", "payee"]),
                )
                db.add(depense)
                result["depenses_created"] += 1
    
    db.commit()
    return result


# ==================== RECRUTEMENT MOCK DATA ====================

TYPES_BAC = [
    ("Bac Général", 0.35),
    ("Bac Techno STI2D", 0.30),
    ("Bac Techno STMG", 0.12),
    ("Bac Pro SN", 0.15),
    ("Bac Pro MELEC", 0.05),
    ("Autre", 0.03),
]

MENTIONS_BAC = [
    ("Très Bien", 0.05),
    ("Bien", 0.15),
    ("Assez Bien", 0.35),
    ("Passable", 0.40),
    ("Non renseigné", 0.05),
]

DEPARTEMENTS_ORIGINE = [
    ("59 - Nord", 0.25),
    ("62 - Pas-de-Calais", 0.20),
    ("80 - Somme", 0.12),
    ("02 - Aisne", 0.10),
    ("60 - Oise", 0.08),
    ("76 - Seine-Maritime", 0.05),
    ("Autres", 0.20),
]

LYCEES = [
    "Lycée Baggio - Lille",
    "Lycée Colbert - Tourcoing", 
    "Lycée Branly - Boulogne",
    "Lycée Condorcet - Lens",
    "Lycée Baudelaire - Roubaix",
    "Lycée Faidherbe - Lille",
    "Lycée Carnot - Bruay",
    "Lycée Darchicourt - Hénin",
    "Lycée Robespierre - Arras",
    "Lycée Châtelet - Douai",
    "Lycée Wallon - Valenciennes",
    "Lycée Lavoisier - Auchel",
    "Lycée Senez - Hénin-Beaumont",
    "Lycée Pasteur - Hénin-Beaumont",
    "Lycée Cassin - Arras",
]

STATUTS_CANDIDAT = ["en_attente", "propose", "accepte", "refuse", "confirme", "desiste"]


def weighted_choice(choices):
    """Choose from a list of (value, weight) tuples."""
    values, weights = zip(*choices)
    return random.choices(values, weights=weights, k=1)[0]


def seed_recrutement_data(db: Session) -> dict:
    """Seed recruitment/Parcoursup data for all departments."""
    result = {"campagnes_created": 0, "candidats_created": 0, "stats_created": 0}
    current_year = date.today().year
    
    # Department-specific candidate counts
    dept_candidates = {
        "RT": 850, "GEII": 920, "GCCD": 650, 
        "GMP": 780, "QLIO": 450, "CHIMIE": 520
    }
    
    for dept in DEPARTMENTS:
        base_candidates = dept_candidates.get(dept, 600)
        
        # Create campaigns for last 4 years
        for year in range(current_year - 3, current_year + 1):
            # Slight yearly variation
            year_variation = 1 + (year - current_year + 3) * 0.03
            num_candidates = int(base_candidates * year_variation * random.uniform(0.95, 1.05))
            
            campagne = CampagneRecrutement(
                department=dept,
                annee=year,
                nb_places=random.randint(48, 60),
                date_debut=date(year, 1, 15),
                date_fin=date(year, 9, 15),
                rang_dernier_appele=random.randint(150, 220),
                date_creation=date(year, 1, 1),
            )
            db.add(campagne)
            db.flush()
            result["campagnes_created"] += 1
            
            # Stats counters
            stats_bac = {}
            stats_mention = {}
            stats_origine = {}
            stats_lycees = {}
            nb_acceptes = 0
            nb_confirmes = 0
            nb_refuses = 0
            nb_desistes = 0
            
            # Create candidates (sample, not all)
            sample_size = min(num_candidates, 200)  # Limit for performance
            
            for i in range(sample_size):
                type_bac = weighted_choice(TYPES_BAC)
                mention = weighted_choice(MENTIONS_BAC)
                origine = weighted_choice(DEPARTEMENTS_ORIGINE)
                lycee = random.choice(LYCEES)
                
                # Determine status based on position
                if i < campagne.nb_places:
                    # Top candidates
                    if random.random() < 0.85:
                        statut = "confirme"
                        nb_confirmes += 1
                    else:
                        statut = "desiste"
                        nb_desistes += 1
                elif i < campagne.rang_dernier_appele:
                    # Called but on waiting list
                    r = random.random()
                    if r < 0.4:
                        statut = "accepte"
                        nb_acceptes += 1
                    elif r < 0.6:
                        statut = "desiste"
                        nb_desistes += 1
                    else:
                        statut = "refuse"
                        nb_refuses += 1
                else:
                    # Not called
                    statut = "refuse"
                    nb_refuses += 1
                
                candidat = CandidatDB(
                    campagne_id=campagne.id,
                    numero_candidat=f"PSP{year}{random.randint(100000, 999999)}",
                    type_bac=type_bac,
                    serie_bac=type_bac.split(" ")[-1] if "Techno" in type_bac else None,
                    mention_bac=mention,
                    annee_bac=year,
                    departement_origine=origine,
                    lycee=lycee,
                    rang_voeu=random.randint(1, 10),
                    rang_appel=i + 1 if i < campagne.rang_dernier_appele else None,
                    statut=statut,
                )
                db.add(candidat)
                result["candidats_created"] += 1
                
                # Update stats
                stats_bac[type_bac] = stats_bac.get(type_bac, 0) + 1
                stats_mention[mention] = stats_mention.get(mention, 0) + 1
                stats_origine[origine] = stats_origine.get(origine, 0) + 1
                stats_lycees[lycee] = stats_lycees.get(lycee, 0) + 1
            
            # Scale up stats to match actual candidate count
            scale = num_candidates / sample_size
            
            # Create aggregated stats record
            stats = StatistiquesParcoursup(
                department=dept,
                annee=year,
                nb_voeux=num_candidates,
                nb_acceptes=int((nb_acceptes + nb_confirmes) * scale),
                nb_confirmes=int(nb_confirmes * scale),
                nb_refuses=int(nb_refuses * scale),
                nb_desistes=int(nb_desistes * scale),
                par_type_bac=json.dumps({k: int(v * scale) for k, v in stats_bac.items()}),
                par_mention=json.dumps({k: int(v * scale) for k, v in stats_mention.items()}),
                par_origine=json.dumps({k: int(v * scale) for k, v in stats_origine.items()}),
                par_lycees=json.dumps(dict(sorted(stats_lycees.items(), key=lambda x: -x[1])[:10])),
                date_mise_a_jour=date.today(),
            )
            db.add(stats)
            result["stats_created"] = result.get("stats_created", 0) + 1
    
    db.commit()
    return result


def run_seeder(force: bool = False):
    """Run the seeder as a standalone script."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        result = seed_database(db, force=force)
        if result["skipped"]:
            print("⏭️  Seeding skipped - database already has data. Use --force to reseed.")
        else:
            print(f"✅ Seeded successfully:")
            print(f"   - Users created: {result['users_created']}")
            print(f"   - Permissions created: {result['permissions_created']}")
            print(f"   - Budgets created: {result['budgets_created']}")
            print(f"   - Dépenses created: {result['depenses_created']}")
            print(f"   - Campagnes recrutement: {result['campagnes_created']}")
            print(f"   - Candidats created: {result['candidats_created']}")
            print()
            print("📋 Available test accounts:")
            print("   - admin          : Superadmin (all permissions)")
            print("   - chef_rt        : RT department admin")
            print("   - chef_geii      : GEII department admin")
            print("   - enseignant_rt  : RT teacher (view scolarite/edt only)")
            print("   - secretaire     : Secretary (scolarite/recrutement for RT & GEII)")
            print("   - pending_user   : Inactive account (pending validation)")
            print()
            print("📊 Mock data created for all departments:")
            print(f"   - {len(DEPARTMENTS)} departments: {', '.join(DEPARTMENTS)}")
            print("   - 3 years of budget data per department")
            print("   - 4 years of recruitment/Parcoursup data per department")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    run_seeder(force=force)
