"""SQLAlchemy database models for Budget, EDT and Recrutement.

All domain-specific data (budget, recrutement, EDT) is scoped by department.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, UniqueConstraint, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import date, datetime
import enum

from app.database import Base


# ==================== DEPARTMENTS ====================

DEPARTMENTS = ["RT", "GEII", "GCCD", "GMP", "QLIO", "CHIMIE"]


# ==================== PERMISSIONS ====================

class PermissionType(str, enum.Enum):
    """Permission types."""
    VIEW = "view"           # Can view data
    EDIT = "edit"           # Can edit data
    ADMIN = "admin"         # Full admin access
    IMPORT = "import"       # Can import data
    EXPORT = "export"       # Can export data


class UserDB(Base):
    """User account linked to CAS authentication."""
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    cas_login = Column(String(100), unique=True, index=True, nullable=False)  # CAS username
    email = Column(String(255), nullable=True)
    nom = Column(String(100), nullable=True)
    prenom = Column(String(100), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=False)  # Must be validated by admin
    is_superadmin = Column(Boolean, default=False)  # Global admin (all departments)
    
    # Timestamps
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_derniere_connexion = Column(DateTime, nullable=True)
    date_validation = Column(DateTime, nullable=True)
    validated_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Relations
    permissions = relationship("UserPermissionDB", back_populates="user", cascade="all, delete-orphan", foreign_keys="[UserPermissionDB.user_id]")


class UserPermissionDB(Base):
    """Department-scoped permissions for users."""
    __tablename__ = "user_permission"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    department = Column(String(20), index=True, nullable=False)  # RT, GEII, etc.
    
    # Permissions by domain
    can_view_scolarite = Column(Boolean, default=True)
    can_edit_scolarite = Column(Boolean, default=False)
    can_view_recrutement = Column(Boolean, default=True)
    can_edit_recrutement = Column(Boolean, default=False)
    can_view_budget = Column(Boolean, default=False)
    can_edit_budget = Column(Boolean, default=False)
    can_view_edt = Column(Boolean, default=True)
    can_edit_edt = Column(Boolean, default=False)
    can_import = Column(Boolean, default=False)
    can_export = Column(Boolean, default=True)
    is_dept_admin = Column(Boolean, default=False)  # Admin for this department
    
    date_creation = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    
    # Unique constraint: one permission set per user per department
    __table_args__ = (UniqueConstraint('user_id', 'department', name='uq_user_dept_permission'),)
    
    # Relations
    user = relationship("UserDB", back_populates="permissions", foreign_keys=[user_id])


# ==================== BUDGET MODELS ====================

class CategorieDepenseDB(str, enum.Enum):
    """Expense categories enum."""
    FONCTIONNEMENT = "fonctionnement"
    INVESTISSEMENT = "investissement"
    MISSIONS = "missions"
    FOURNITURES = "fournitures"
    MAINTENANCE = "maintenance"
    FORMATION = "formation"
    AUTRE = "autre"


class BudgetAnnuel(Base):
    """Annual budget configuration per department."""
    __tablename__ = "budget_annuel"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(20), index=True, nullable=False)  # RT, GEII, etc.
    annee = Column(Integer, index=True, nullable=False)
    budget_total = Column(Float, default=0)
    previsionnel = Column(Float, default=0)
    date_creation = Column(Date, default=date.today)
    date_modification = Column(Date, default=date.today, onupdate=date.today)
    
    # Unique constraint: one budget per department per year
    __table_args__ = (UniqueConstraint('department', 'annee', name='uq_budget_dept_annee'),)
    
    # Relations
    lignes = relationship("LigneBudgetDB", back_populates="budget_annuel", cascade="all, delete-orphan")
    depenses = relationship("DepenseDB", back_populates="budget_annuel", cascade="all, delete-orphan")


class LigneBudgetDB(Base):
    """Budget line by category."""
    __tablename__ = "ligne_budget"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_annuel_id = Column(Integer, ForeignKey("budget_annuel.id"), nullable=False)
    categorie = Column(String(50), nullable=False)
    budget_initial = Column(Float, default=0)
    budget_modifie = Column(Float, default=0)
    engage = Column(Float, default=0)
    paye = Column(Float, default=0)
    
    # Relation
    budget_annuel = relationship("BudgetAnnuel", back_populates="lignes")
    
    @property
    def disponible(self) -> float:
        return self.budget_modifie - self.engage


class DepenseDB(Base):
    """Individual expense."""
    __tablename__ = "depense"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_annuel_id = Column(Integer, ForeignKey("budget_annuel.id"), nullable=False)
    libelle = Column(String(255), nullable=False)
    montant = Column(Float, nullable=False)
    categorie = Column(String(50), nullable=False)
    date_depense = Column(Date, nullable=False)
    fournisseur = Column(String(255), nullable=True)
    numero_commande = Column(String(100), nullable=True)
    statut = Column(String(50), default="engagee")  # prevue, engagee, payee
    
    # Relation
    budget_annuel = relationship("BudgetAnnuel", back_populates="depenses")


# ==================== RECRUTEMENT/PARCOURSUP MODELS ====================

class CampagneRecrutement(Base):
    """Recruitment campaign (one per year per department)."""
    __tablename__ = "campagne_recrutement"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(20), index=True, nullable=False)  # RT, GEII, etc.
    annee = Column(Integer, index=True, nullable=False)
    nb_places = Column(Integer, default=0)
    date_debut = Column(Date, nullable=True)
    date_fin = Column(Date, nullable=True)
    rang_dernier_appele = Column(Integer, nullable=True)
    date_creation = Column(Date, default=date.today)
    date_modification = Column(Date, default=date.today, onupdate=date.today)
    
    # Unique constraint: one campaign per department per year
    __table_args__ = (UniqueConstraint('department', 'annee', name='uq_campagne_dept_annee'),)
    
    # Relations
    candidats = relationship("CandidatDB", back_populates="campagne", cascade="all, delete-orphan")


class CandidatDB(Base):
    """Parcoursup candidate."""
    __tablename__ = "candidat"
    
    id = Column(Integer, primary_key=True, index=True)
    campagne_id = Column(Integer, ForeignKey("campagne_recrutement.id"), nullable=False)
    
    # Identité (anonymisé si nécessaire)
    numero_candidat = Column(String(50), nullable=True)  # Numéro Parcoursup
    nom = Column(String(100), nullable=True)
    prenom = Column(String(100), nullable=True)
    
    # Bac
    type_bac = Column(String(50), nullable=False)  # Général, Techno, Pro
    serie_bac = Column(String(50), nullable=True)  # STI2D, etc.
    mention_bac = Column(String(50), nullable=True)  # TB, B, AB, P
    annee_bac = Column(Integer, nullable=True)
    
    # Origine
    departement_origine = Column(String(100), nullable=True)
    pays_origine = Column(String(100), default="France")
    lycee = Column(String(255), nullable=True)
    code_lycee = Column(String(20), nullable=True)
    
    # Voeu
    rang_voeu = Column(Integer, nullable=True)
    rang_appel = Column(Integer, nullable=True)
    
    # Statut
    statut = Column(String(50), default="en_attente")
    # en_attente, propose, accepte, refuse, confirme, desiste
    
    date_reponse = Column(Date, nullable=True)
    
    # Relation
    campagne = relationship("CampagneRecrutement", back_populates="candidats")


class StatistiquesParcoursup(Base):
    """Aggregated yearly stats per department (for quick access)."""
    __tablename__ = "stats_parcoursup"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(20), index=True, nullable=False)  # RT, GEII, etc.
    annee = Column(Integer, index=True, nullable=False)
    
    # Totaux
    nb_voeux = Column(Integer, default=0)
    nb_acceptes = Column(Integer, default=0)
    nb_confirmes = Column(Integer, default=0)
    nb_refuses = Column(Integer, default=0)
    nb_desistes = Column(Integer, default=0)
    
    # Répartitions (stockées en JSON string)
    par_type_bac = Column(Text, nullable=True)  # JSON
    par_mention = Column(Text, nullable=True)  # JSON
    par_origine = Column(Text, nullable=True)  # JSON
    par_lycees = Column(Text, nullable=True)  # JSON - {"Lycée X": 10, ...}
    
    date_mise_a_jour = Column(Date, default=date.today)
    
    # Unique constraint: one stats record per department per year
    __table_args__ = (UniqueConstraint('department', 'annee', name='uq_stats_dept_annee'),)


# ==================== EDT MODELS ====================

class EdtAnnuel(Base):
    """Annual EDT/schedule data per department."""
    __tablename__ = "edt_annuel"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(20), index=True, nullable=False)
    annee = Column(String(20), index=True, nullable=False)  # "2024-2025"
    heures_prevues_total = Column(Float, default=0)
    heures_effectuees_total = Column(Float, default=0)
    date_creation = Column(Date, default=date.today)
    date_modification = Column(Date, default=date.today, onupdate=date.today)
    
    __table_args__ = (UniqueConstraint('department', 'annee', name='uq_edt_dept_annee'),)
    
    # Relations
    enseignants = relationship("EnseignantChargeDB", back_populates="edt_annuel", cascade="all, delete-orphan")
    salles = relationship("SalleOccupationDB", back_populates="edt_annuel", cascade="all, delete-orphan")


class EnseignantChargeDB(Base):
    """Teacher workload per year."""
    __tablename__ = "enseignant_charge"
    
    id = Column(Integer, primary_key=True, index=True)
    edt_annuel_id = Column(Integer, ForeignKey("edt_annuel.id"), nullable=False)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=True)
    statut = Column(String(50), default="permanent")  # permanent, vacataire, contractuel
    heures_service = Column(Float, default=192)  # Heures dues (192h pour MCF, 384h pour PRAG)
    heures_cm = Column(Float, default=0)
    heures_td = Column(Float, default=0)
    heures_tp = Column(Float, default=0)
    heures_total = Column(Float, default=0)  # CM + TD + TP en équivalent TD
    heures_complementaires = Column(Float, default=0)
    
    edt_annuel = relationship("EdtAnnuel", back_populates="enseignants")


class SalleOccupationDB(Base):
    """Room occupancy stats per year."""
    __tablename__ = "salle_occupation"
    
    id = Column(Integer, primary_key=True, index=True)
    edt_annuel_id = Column(Integer, ForeignKey("edt_annuel.id"), nullable=False)
    nom_salle = Column(String(50), nullable=False)
    type_salle = Column(String(50), default="TD")  # Amphi, TD, TP, Labo
    capacite = Column(Integer, default=30)
    heures_occupees = Column(Float, default=0)
    heures_disponibles = Column(Float, default=0)
    taux_occupation = Column(Float, default=0)  # pourcentage
    
    edt_annuel = relationship("EdtAnnuel", back_populates="salles")


# ==================== SYSTEM SETTINGS ====================

class SystemSettingsDB(Base):
    """System settings stored in database."""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    date_modification = Column(Date, default=date.today, onupdate=date.today)


class DataSourceDB(Base):
    """Data source configuration stored in database."""
    __tablename__ = "data_source"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g. 'scodoc-1'
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # scodoc, parcoursup, excel, apogee
    status = Column(String(50), default="inactive")  # active, inactive, error, configuring
    description = Column(String(255), nullable=True)
    base_url = Column(String(255), nullable=True)
    username = Column(String(100), nullable=True)
    password_encrypted = Column(String(255), nullable=True)  # Store encrypted
    enabled = Column(Integer, default=1)  # SQLite doesn't have boolean
    auto_sync = Column(Integer, default=1)
    sync_interval_hours = Column(Integer, default=1)
    last_sync = Column(Date, nullable=True)
    last_error = Column(Text, nullable=True)
    records_count = Column(Integer, default=0)
    date_creation = Column(Date, default=date.today)
    date_modification = Column(Date, default=date.today, onupdate=date.today)
