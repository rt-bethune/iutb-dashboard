Project Root: /Users/lafifi/Codes/RT/Dept-Dashboard
Project Structure:
```
.
|-- .claude
    |-- skills
        |-- dept-dashboard
            |-- SKILL.md
            |-- assets
            |-- references
                |-- ARCHITECTURE.md
                |-- CONVENTIONS.md
                |-- PERMISSIONS.md
                |-- WORKFLOWS.md
            |-- scripts
                |-- seed_data.py
        |-- skill-creator
            |-- LICENSE.txt
            |-- SKILL.md
            |-- references
                |-- output-patterns.md
                |-- workflows.md
            |-- scripts
                |-- init_skill.py
                |-- package_skill.py
                |-- quick_validate.py
|-- .github
    |-- copilot-instructions.md
|-- .gitignore
|-- AGENTS.md
|-- DEPLOY.md
|-- DOCUMENTATION.md
|-- README.md
|-- backend
    |-- Dockerfile
    |-- alembic
        |-- env.py
        |-- script.py.mako
        |-- versions
            |-- 20241214_0001_001_initial_initial_migration_users_and_.py
            |-- 20241214_0002_002_budget_recrutement_tables.py
    |-- alembic.ini
    |-- app
        |-- __init__.py
        |-- adapters
            |-- __init__.py
            |-- base.py
            |-- cas.py
            |-- excel.py
            |-- parcoursup.py
            |-- scodoc.py
        |-- api
            |-- __init__.py
            |-- deps.py
            |-- routes
                |-- __init__.py
                |-- admin.py
                |-- alertes.py
                |-- auth.py
                |-- budget.py
                |-- budget_admin.py
                |-- edt.py
                |-- indicateurs.py
                |-- recrutement.py
                |-- recrutement_admin.py
                |-- scolarite.py
                |-- upload.py
                |-- users.py
        |-- config.py
        |-- crud
            |-- __init__.py
            |-- admin.py
            |-- budget.py
            |-- recrutement.py
        |-- database.py
        |-- main.py
        |-- models
            |-- __init__.py
            |-- admin.py
            |-- alertes.py
            |-- budget.py
            |-- db_models.py
            |-- edt.py
            |-- indicateurs.py
            |-- recrutement.py
            |-- scolarite.py
        |-- schemas
            |-- __init__.py
            |-- budget.py
            |-- recrutement.py
        |-- seeds.py
        |-- services
            |-- __init__.py
            |-- alertes_service.py
            |-- cache.py
            |-- indicateurs_service.py
            |-- scheduler.py
    |-- pytest.ini
    |-- requirements.txt
    |-- scripts
        |-- __init__.py
        |-- seed_data.py
    |-- tests
        |-- conftest.py
        |-- test_adapters.py
        |-- test_cache.py
        |-- test_models.py
        |-- test_routes.py
    |-- uploads
|-- certbot
    |-- www
|-- data
    |-- examples
|-- docker-compose.prod.yml
|-- docs
    |-- INDICATEURS.md
    |-- SCODOC_API.md
|-- frontend
    |-- Dockerfile
    |-- Dockerfile.prod
    |-- index.html
    |-- nginx.conf
    |-- package-lock.json
    |-- package.json
    |-- postcss.config.js
    |-- src
        |-- App.tsx
        |-- components
            |-- ChartContainer.tsx
            |-- DataTable.tsx
            |-- ExportButton.tsx
            |-- FileUpload.tsx
            |-- FilterBar.tsx
            |-- Layout.tsx
            |-- PermissionGate.tsx
            |-- ProgressBar.tsx
            |-- StatCard.tsx
        |-- contexts
            |-- AuthContext.tsx
            |-- DepartmentContext.tsx
        |-- index.css
        |-- main.tsx
        |-- pages
            |-- Admin.tsx
            |-- AdminBudget.tsx
            |-- AdminRecrutement.tsx
            |-- Alertes.tsx
            |-- AnalyseModules.tsx
            |-- Budget.tsx
            |-- Dashboard.tsx
            |-- EDT.tsx
            |-- EtudiantsListe.tsx
            |-- FicheEtudiant.tsx
            |-- Login.tsx
            |-- PendingValidation.tsx
            |-- Recrutement.tsx
            |-- Scolarite.tsx
            |-- Upload.tsx
            |-- UsersManagement.tsx
        |-- services
            |-- api.ts
        |-- types
            |-- index.ts
    |-- tailwind.config.js
    |-- tsconfig.json
    |-- tsconfig.node.json
    |-- vite.config.ts
|-- nginx
    |-- nginx.prod.conf
|-- plan.md
|-- screenshots

```

---
## File: backend/alembic/env.py

```py
"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import Base
from app.models import db_models  # noqa: F401 - Import models to register them

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get database URL from settings
settings = get_settings()
if settings.database_url:
    config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

```
---
## File: backend/alembic/script.py.mako

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```
---
## File: backend/alembic/versions/20241214_0001_001_initial_initial_migration_users_and_.py

```py
"""Initial migration - Users and Permissions

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cas_login', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('nom', sa.String(length=100), nullable=True),
        sa.Column('prenom', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('date_creation', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('date_derniere_connexion', sa.DateTime(), nullable=True),
        sa.Column('date_validation', sa.DateTime(), nullable=True),
        sa.Column('validated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['validated_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cas_login')
    )
    op.create_index(op.f('ix_user_cas_login'), 'user', ['cas_login'], unique=True)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)

    # Create user_permissions table
    op.create_table(
        'user_permission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(length=20), nullable=False),
        sa.Column('can_view_scolarite', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('can_edit_scolarite', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_view_recrutement', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('can_edit_recrutement', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_view_budget', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_edit_budget', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_view_edt', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('can_edit_edt', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_import', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('can_export', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_dept_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('date_creation', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['user.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'department', name='uq_user_dept_permission')
    )
    op.create_index(op.f('ix_user_permission_user_id'), 'user_permission', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_permission_department'), 'user_permission', ['department'], unique=False)
    op.create_index(op.f('ix_user_permission_id'), 'user_permission', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_permission_id'), table_name='user_permission')
    op.drop_index(op.f('ix_user_permission_department'), table_name='user_permission')
    op.drop_index(op.f('ix_user_permission_user_id'), table_name='user_permission')
    op.drop_table('user_permission')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_cas_login'), table_name='user')
    op.drop_table('user')

```
---
## File: backend/alembic/versions/20241214_0002_002_budget_recrutement_tables.py

```py
"""Budget and Recrutement tables

Revision ID: 002_budget_recrutement
Revises: 001_initial
Create Date: 2024-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_budget_recrutement'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== BUDGET TABLES ====================
    
    # Create budget_annuel table
    op.create_table(
        'budget_annuel',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(length=20), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('budget_total', sa.Float(), nullable=False, server_default='0'),
        sa.Column('previsionnel', sa.Float(), nullable=False, server_default='0'),
        sa.Column('date_creation', sa.Date(), nullable=True),
        sa.Column('date_modification', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('department', 'annee', name='uq_budget_dept_annee')
    )
    op.create_index('ix_budget_annuel_department', 'budget_annuel', ['department'], unique=False)
    op.create_index('ix_budget_annuel_annee', 'budget_annuel', ['annee'], unique=False)

    # Create ligne_budget table
    op.create_table(
        'ligne_budget',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('budget_annuel_id', sa.Integer(), nullable=False),
        sa.Column('categorie', sa.String(length=50), nullable=False),
        sa.Column('budget_initial', sa.Float(), nullable=False, server_default='0'),
        sa.Column('budget_modifie', sa.Float(), nullable=False, server_default='0'),
        sa.Column('engage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('paye', sa.Float(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['budget_annuel_id'], ['budget_annuel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ligne_budget_budget_annuel_id', 'ligne_budget', ['budget_annuel_id'], unique=False)

    # Create depense table
    op.create_table(
        'depense',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('budget_annuel_id', sa.Integer(), nullable=False),
        sa.Column('libelle', sa.String(length=255), nullable=False),
        sa.Column('montant', sa.Float(), nullable=False),
        sa.Column('categorie', sa.String(length=50), nullable=False),
        sa.Column('date_depense', sa.Date(), nullable=False),
        sa.Column('fournisseur', sa.String(length=255), nullable=True),
        sa.Column('numero_commande', sa.String(length=100), nullable=True),
        sa.Column('statut', sa.String(length=50), nullable=False, server_default='engagee'),
        sa.ForeignKeyConstraint(['budget_annuel_id'], ['budget_annuel.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_depense_budget_annuel_id', 'depense', ['budget_annuel_id'], unique=False)
    op.create_index('ix_depense_date', 'depense', ['date_depense'], unique=False)

    # ==================== RECRUTEMENT/PARCOURSUP TABLES ====================

    # Create campagne_recrutement table
    op.create_table(
        'campagne_recrutement',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(length=20), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('nb_places', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('date_debut', sa.Date(), nullable=True),
        sa.Column('date_fin', sa.Date(), nullable=True),
        sa.Column('rang_dernier_appele', sa.Integer(), nullable=True),
        sa.Column('date_creation', sa.Date(), nullable=True),
        sa.Column('date_modification', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('department', 'annee', name='uq_campagne_dept_annee')
    )
    op.create_index('ix_campagne_recrutement_department', 'campagne_recrutement', ['department'], unique=False)
    op.create_index('ix_campagne_recrutement_annee', 'campagne_recrutement', ['annee'], unique=False)

    # Create candidat table
    op.create_table(
        'candidat',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campagne_id', sa.Integer(), nullable=False),
        sa.Column('numero_candidat', sa.String(length=50), nullable=True),
        sa.Column('nom', sa.String(length=100), nullable=True),
        sa.Column('prenom', sa.String(length=100), nullable=True),
        sa.Column('type_bac', sa.String(length=50), nullable=False),
        sa.Column('serie_bac', sa.String(length=50), nullable=True),
        sa.Column('mention_bac', sa.String(length=50), nullable=True),
        sa.Column('annee_bac', sa.Integer(), nullable=True),
        sa.Column('departement_origine', sa.String(length=100), nullable=True),
        sa.Column('pays_origine', sa.String(length=100), nullable=True, server_default='France'),
        sa.Column('lycee', sa.String(length=255), nullable=True),
        sa.Column('code_lycee', sa.String(length=20), nullable=True),
        sa.Column('rang_voeu', sa.Integer(), nullable=True),
        sa.Column('rang_appel', sa.Integer(), nullable=True),
        sa.Column('statut', sa.String(length=50), nullable=False, server_default='en_attente'),
        sa.Column('date_reponse', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['campagne_id'], ['campagne_recrutement.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_candidat_campagne_id', 'candidat', ['campagne_id'], unique=False)
    op.create_index('ix_candidat_statut', 'candidat', ['statut'], unique=False)

    # Create stats_parcoursup table (aggregated stats for quick access)
    op.create_table(
        'stats_parcoursup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(length=20), nullable=False),
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('nb_voeux', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nb_acceptes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nb_confirmes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nb_refuses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nb_desistes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('par_type_bac', sa.Text(), nullable=True),
        sa.Column('par_mention', sa.Text(), nullable=True),
        sa.Column('par_origine', sa.Text(), nullable=True),
        sa.Column('par_lycees', sa.Text(), nullable=True),
        sa.Column('date_mise_a_jour', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('department', 'annee', name='uq_stats_dept_annee')
    )
    op.create_index('ix_stats_parcoursup_department', 'stats_parcoursup', ['department'], unique=False)
    op.create_index('ix_stats_parcoursup_annee', 'stats_parcoursup', ['annee'], unique=False)


def downgrade() -> None:
    # Drop recrutement tables
    op.drop_index('ix_stats_parcoursup_annee', table_name='stats_parcoursup')
    op.drop_index('ix_stats_parcoursup_department', table_name='stats_parcoursup')
    op.drop_table('stats_parcoursup')
    
    op.drop_index('ix_candidat_statut', table_name='candidat')
    op.drop_index('ix_candidat_campagne_id', table_name='candidat')
    op.drop_table('candidat')
    
    op.drop_index('ix_campagne_recrutement_annee', table_name='campagne_recrutement')
    op.drop_index('ix_campagne_recrutement_department', table_name='campagne_recrutement')
    op.drop_table('campagne_recrutement')
    
    # Drop budget tables
    op.drop_index('ix_depense_date', table_name='depense')
    op.drop_index('ix_depense_budget_annuel_id', table_name='depense')
    op.drop_table('depense')
    
    op.drop_index('ix_ligne_budget_budget_annuel_id', table_name='ligne_budget')
    op.drop_table('ligne_budget')
    
    op.drop_index('ix_budget_annuel_annee', table_name='budget_annuel')
    op.drop_index('ix_budget_annuel_department', table_name='budget_annuel')
    op.drop_table('budget_annuel')

```
---
## File: backend/app/__init__.py

```py
# Dept Dashboard Backend

```
---
## File: backend/app/adapters/__init__.py

```py
# Adapters

```
---
## File: backend/app/adapters/base.py

```py
"""Base adapter interface."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseAdapter(ABC, Generic[T]):
    """
    Abstract base class for all data source adapters.
    
    Each adapter must implement methods to:
    - Connect/authenticate to the data source
    - Fetch raw data
    - Transform data to internal models
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the data source."""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the data source is available/configured."""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate to the data source if required.
        Returns True if authentication successful or not required.
        """
        pass
    
    @abstractmethod
    async def fetch_raw(self, **kwargs) -> Any:
        """
        Fetch raw data from the source.
        Returns data in the source's native format.
        """
        pass
    
    @abstractmethod
    def transform(self, raw_data: Any) -> T:
        """
        Transform raw data to internal model format.
        """
        pass
    
    async def get_data(self, **kwargs) -> T:
        """
        Main method to fetch and transform data.
        Handles authentication if needed.
        """
        if not await self.is_available():
            raise RuntimeError(f"Data source {self.source_name} is not available")
        
        await self.authenticate()
        raw_data = await self.fetch_raw(**kwargs)
        return self.transform(raw_data)


class FileAdapter(BaseAdapter[T]):
    """
    Base class for file-based adapters (Excel, CSV).
    """
    
    async def is_available(self) -> bool:
        """File adapters are always available."""
        return True
    
    async def authenticate(self) -> bool:
        """File adapters don't need authentication."""
        return True
    
    @abstractmethod
    def parse_file(self, file_content: bytes, filename: str) -> Any:
        """Parse uploaded file content."""
        pass

```
---
## File: backend/app/adapters/cas.py

```py
"""CAS (Central Authentication Service) adapter.

Implements CAS protocol for university SSO authentication.
Example: https://sso.univ-artois.fr/cas/
"""

import httpx
from typing import Optional, Any
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class CASAdapter:
    """
    CAS Protocol adapter for university authentication.
    
    CAS Flow:
    1. User visits protected page
    2. Redirect to CAS login: {cas_url}/login?service={callback_url}
    3. User authenticates with CAS
    4. CAS redirects back with ticket: {callback_url}?ticket=xxx
    5. Server validates ticket: GET {cas_url}/serviceValidate?ticket=xxx&service={callback_url}
    6. CAS returns XML with user info
    """
    
    def __init__(
        self,
        cas_url: str,
        service_url: str,
    ):
        """
        Initialize CAS adapter.
        
        Args:
            cas_url: CAS server URL (e.g., https://sso.univ-artois.fr/cas)
            service_url: Our service callback URL
        """
        self.cas_url = cas_url.rstrip('/')
        self.service_url = service_url
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self.client
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    def get_login_url(self, return_url: Optional[str] = None) -> str:
        """
        Get CAS login URL for redirect.
        
        Args:
            return_url: Optional URL to return to after auth (encoded in service URL)
        
        Returns:
            Full CAS login URL with service parameter
        """
        service = self.service_url
        if return_url:
            service = f"{service}?return_url={return_url}"
        
        params = urlencode({'service': service})
        return f"{self.cas_url}/login?{params}"
    
    def get_logout_url(self, return_url: Optional[str] = None) -> str:
        """
        Get CAS logout URL.
        
        Args:
            return_url: Optional URL to redirect after logout
        
        Returns:
            CAS logout URL
        """
        if return_url:
            params = urlencode({'service': return_url})
            return f"{self.cas_url}/logout?{params}"
        return f"{self.cas_url}/logout"
    
    async def validate_ticket(self, ticket: str) -> Optional[dict[str, Any]]:
        """
        Validate CAS ticket and get user info.
        
        Args:
            ticket: CAS ticket from callback
        
        Returns:
            User info dict with 'user' key if valid, None if invalid
            {
                'user': 'username',
                'attributes': {
                    'email': 'user@example.com',
                    'displayName': 'John Doe',
                    ...
                }
            }
        """
        client = await self._get_client()
        
        # CAS 2.0/3.0 service validation endpoint
        validate_url = f"{self.cas_url}/serviceValidate"
        params = {
            'ticket': ticket,
            'service': self.service_url,
        }
        
        try:
            response = await client.get(validate_url, params=params)
            response.raise_for_status()
            
            return self._parse_cas_response(response.text)
            
        except httpx.HTTPError as e:
            logger.error(f"CAS validation error: {e}")
            return None
    
    def _parse_cas_response(self, xml_text: str) -> Optional[dict[str, Any]]:
        """
        Parse CAS XML response.
        
        CAS 2.0 success response:
        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationSuccess>
                <cas:user>username</cas:user>
                <cas:attributes>
                    <cas:email>user@example.com</cas:email>
                    <cas:displayName>John Doe</cas:displayName>
                </cas:attributes>
            </cas:authenticationSuccess>
        </cas:serviceResponse>
        
        CAS 2.0 failure response:
        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationFailure code="INVALID_TICKET">
                Ticket not recognized
            </cas:authenticationFailure>
        </cas:serviceResponse>
        """
        try:
            # Handle CAS namespace
            namespaces = {'cas': 'http://www.yale.edu/tp/cas'}
            root = ET.fromstring(xml_text)
            
            # Check for authentication failure
            failure = root.find('.//cas:authenticationFailure', namespaces)
            if failure is not None:
                code = failure.get('code', 'UNKNOWN')
                message = failure.text.strip() if failure.text else ''
                logger.warning(f"CAS authentication failed: {code} - {message}")
                return None
            
            # Check for authentication success
            success = root.find('.//cas:authenticationSuccess', namespaces)
            if success is None:
                logger.error("CAS response has no authenticationSuccess element")
                return None
            
            # Get username
            user_elem = success.find('cas:user', namespaces)
            if user_elem is None or not user_elem.text:
                logger.error("CAS response has no user element")
                return None
            
            result = {
                'user': user_elem.text.strip(),
                'attributes': {}
            }
            
            # Get attributes (CAS 3.0)
            attributes = success.find('cas:attributes', namespaces)
            if attributes is not None:
                for attr in attributes:
                    # Remove namespace prefix from tag
                    tag = attr.tag.split('}')[-1] if '}' in attr.tag else attr.tag
                    result['attributes'][tag] = attr.text.strip() if attr.text else ''
            
            logger.info(f"CAS authentication successful for user: {result['user']}")
            return result
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse CAS XML response: {e}")
            return None


class MockCASAdapter(CASAdapter):
    """Mock CAS adapter for development/testing."""
    
    def __init__(self, cas_url: str = "https://mock-cas.local", service_url: str = "http://localhost:8000"):
        super().__init__(cas_url, service_url)
        self._mock_users = {
            'admin': {'email': 'admin@univ.fr', 'displayName': 'Admin User', 'role': 'admin'},
            'teacher1': {'email': 'teacher1@univ.fr', 'displayName': 'Jean Dupont', 'role': 'teacher'},
            'teacher2': {'email': 'teacher2@univ.fr', 'displayName': 'Marie Martin', 'role': 'teacher'},
        }
    
    async def validate_ticket(self, ticket: str) -> Optional[dict[str, Any]]:
        """
        Mock ticket validation.
        
        Ticket format for mock: "mock-ticket-{username}"
        """
        if not ticket.startswith('mock-ticket-'):
            return None
        
        username = ticket.replace('mock-ticket-', '')
        
        if username in self._mock_users:
            return {
                'user': username,
                'attributes': self._mock_users[username]
            }
        
        # Accept any username for development
        return {
            'user': username,
            'attributes': {
                'email': f'{username}@univ.fr',
                'displayName': username.title(),
            }
        }


def get_cas_adapter(cas_url: str, service_url: str, use_mock: bool = False) -> CASAdapter:
    """
    Factory function to get CAS adapter.
    
    Args:
        cas_url: CAS server URL
        service_url: Our callback URL
        use_mock: Use mock adapter for development
    
    Returns:
        CAS adapter instance
    """
    if use_mock:
        return MockCASAdapter(cas_url, service_url)
    return CASAdapter(cas_url, service_url)

```
---
## File: backend/app/adapters/excel.py

```py
"""Excel file adapter."""

import io
from typing import Any, Optional
import pandas as pd
from datetime import date

from app.adapters.base import FileAdapter
from app.models.budget import (
    BudgetIndicators,
    LigneBudget,
    Depense,
    CategorieDepense,
)
from app.models.edt import (
    EDTIndicators,
    ChargeEnseignant,
    OccupationSalle,
    TypeCours,
)


class ExcelAdapter(FileAdapter[BudgetIndicators]):
    """
    Adapter for Excel files.
    Handles budget, EDT, and other Excel-based data sources.
    """
    
    @property
    def source_name(self) -> str:
        return "Excel"
    
    async def fetch_raw(self, **kwargs) -> Any:
        """Not used for file adapters - use parse_file instead."""
        return {}
    
    def transform(self, raw_data: Any) -> BudgetIndicators:
        """Transform parsed Excel data to indicators."""
        return raw_data
    
    def parse_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse Excel file to DataFrame."""
        return pd.read_excel(io.BytesIO(file_content))
    
    def parse_budget_file(self, file_content: bytes) -> BudgetIndicators:
        """
        Parse budget Excel file.
        
        Expected columns:
        - Catégorie
        - Budget Initial
        - Budget Modifié
        - Engagé
        - Payé
        """
        df = pd.read_excel(io.BytesIO(file_content))
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        lignes = []
        total_initial = 0
        total_engage = 0
        total_paye = 0
        
        for _, row in df.iterrows():
            cat_str = str(row.get("catégorie", row.get("categorie", "autre"))).lower()
            
            # Map to enum
            cat_map = {
                "fonctionnement": CategorieDepense.FONCTIONNEMENT,
                "investissement": CategorieDepense.INVESTISSEMENT,
                "missions": CategorieDepense.MISSIONS,
                "fournitures": CategorieDepense.FOURNITURES,
                "maintenance": CategorieDepense.MAINTENANCE,
                "formation": CategorieDepense.FORMATION,
            }
            categorie = cat_map.get(cat_str, CategorieDepense.AUTRE)
            
            budget_initial = float(row.get("budget initial", row.get("budget_initial", 0)) or 0)
            budget_modifie = float(row.get("budget modifié", row.get("budget_modifie", budget_initial)) or budget_initial)
            engage = float(row.get("engagé", row.get("engage", 0)) or 0)
            paye = float(row.get("payé", row.get("paye", 0)) or 0)
            disponible = budget_modifie - engage
            
            lignes.append(LigneBudget(
                categorie=categorie,
                budget_initial=budget_initial,
                budget_modifie=budget_modifie,
                engage=engage,
                paye=paye,
                disponible=disponible,
            ))
            
            total_initial += budget_initial
            total_engage += engage
            total_paye += paye
        
        total_disponible = total_initial - total_engage
        
        return BudgetIndicators(
            annee=date.today().year,
            budget_total=total_initial,
            total_engage=total_engage,
            total_paye=total_paye,
            total_disponible=total_disponible,
            taux_execution=total_paye / total_initial if total_initial > 0 else 0,
            taux_engagement=total_engage / total_initial if total_initial > 0 else 0,
            par_categorie=lignes,
            evolution_mensuelle={},
            top_depenses=[],
            previsionnel=total_initial,
            realise=total_paye,
        )
    
    def parse_edt_file(self, file_content: bytes) -> EDTIndicators:
        """
        Parse EDT Excel file.
        
        Expected columns:
        - Enseignant
        - Module
        - Type (CM/TD/TP)
        - Heures
        - Salle (optional)
        """
        df = pd.read_excel(io.BytesIO(file_content))
        df.columns = df.columns.str.lower().str.strip()
        
        # Calculate per teacher
        charges: dict[str, ChargeEnseignant] = {}
        heures_par_module: dict[str, float] = {}
        salles: dict[str, float] = {}
        
        total_cm = 0
        total_td = 0
        total_tp = 0
        
        for _, row in df.iterrows():
            enseignant = str(row.get("enseignant", "Inconnu"))
            module = str(row.get("module", ""))
            type_cours = str(row.get("type", "TD")).upper()
            heures = float(row.get("heures", 0) or 0)
            salle = str(row.get("salle", ""))
            
            # Update teacher charges
            if enseignant not in charges:
                charges[enseignant] = ChargeEnseignant(
                    enseignant=enseignant,
                    heures_cm=0, heures_td=0, heures_tp=0, heures_projet=0,
                    total_heures=0, heures_statutaires=192, heures_complementaires=0
                )
            
            charge = charges[enseignant]
            if type_cours == "CM":
                charge.heures_cm += heures
                total_cm += heures
            elif type_cours == "TD":
                charge.heures_td += heures
                total_td += heures
            elif type_cours == "TP":
                charge.heures_tp += heures
                total_tp += heures
            else:
                charge.heures_projet += heures
            
            charge.total_heures = (
                charge.heures_cm * 1.5 +  # CM compte 1.5x
                charge.heures_td +
                charge.heures_tp +
                charge.heures_projet
            )
            charge.heures_complementaires = max(0, charge.total_heures - charge.heures_statutaires)
            
            # Update module hours
            heures_par_module[module] = heures_par_module.get(module, 0) + heures
            
            # Update room occupation
            if salle:
                salles[salle] = salles.get(salle, 0) + heures
        
        # Build room occupation list
        occupation_salles = [
            OccupationSalle(
                salle=salle,
                capacite=30,  # Default capacity
                heures_occupees=heures,
                heures_disponibles=40 * 35,  # 40h/week * 35 weeks
                taux_occupation=heures / (40 * 35),
            )
            for salle, heures in salles.items()
        ]
        
        total_heures = total_cm + total_td + total_tp
        total_hc = sum(c.heures_complementaires for c in charges.values())
        
        return EDTIndicators(
            periode_debut=date(date.today().year, 9, 1),
            periode_fin=date(date.today().year + 1, 6, 30),
            total_heures=total_heures,
            heures_cm=total_cm,
            heures_td=total_td,
            heures_tp=total_tp,
            repartition_types={
                "CM": total_cm,
                "TD": total_td,
                "TP": total_tp,
            },
            charges_enseignants=list(charges.values()),
            total_heures_complementaires=total_hc,
            occupation_salles=occupation_salles,
            taux_occupation_moyen=sum(s.taux_occupation for s in occupation_salles) / len(occupation_salles) if occupation_salles else 0,
            heures_par_module=heures_par_module,
            evolution_hebdo={},
        )


# Mock Excel adapter for development
class MockExcelAdapter(FileAdapter[BudgetIndicators]):
    """Mock Excel adapter with sample data."""
    
    @property
    def source_name(self) -> str:
        return "Excel (Mock)"
    
    async def fetch_raw(self, **kwargs) -> Any:
        return {}
    
    def transform(self, raw_data: Any) -> BudgetIndicators:
        return self.get_mock_budget()
    
    def parse_file(self, file_content: bytes, filename: str) -> Any:
        return {}
    
    def get_mock_budget(self) -> BudgetIndicators:
        """Return mock budget data."""
        return BudgetIndicators(
            annee=2024,
            budget_total=150000,
            total_engage=95000,
            total_paye=72000,
            total_disponible=55000,
            taux_execution=0.48,
            taux_engagement=0.63,
            par_categorie=[
                LigneBudget(
                    categorie=CategorieDepense.FONCTIONNEMENT,
                    budget_initial=80000, budget_modifie=82000,
                    engage=55000, paye=45000, disponible=27000
                ),
                LigneBudget(
                    categorie=CategorieDepense.INVESTISSEMENT,
                    budget_initial=50000, budget_modifie=48000,
                    engage=30000, paye=20000, disponible=18000
                ),
                # LigneBudget(
                #     categorie=CategorieDepense.MISSIONS,
                #     budget_initial=20000, budget_modifie=20000,
                #     engage=10000, paye=7000, disponible=10000
                # ),
            ],
            evolution_mensuelle={
                "2024-09": 8000, "2024-10": 12000, "2024-11": 15000,
                "2024-12": 10000, "2025-01": 8000, "2025-02": 9000,
            },
            top_depenses=[
                Depense(id="1", libelle="Serveur Dell", montant=15000,
                       categorie=CategorieDepense.INVESTISSEMENT, date=date(2024, 10, 15)),
                Depense(id="2", libelle="Licences VMware", montant=8000,
                       categorie=CategorieDepense.FONCTIONNEMENT, date=date(2024, 9, 1)),
            ],
            previsionnel=150000,
            realise=72000,
        )
    
    def get_mock_edt(self) -> EDTIndicators:
        """Return mock EDT data."""
        return EDTIndicators(
            periode_debut=date(2024, 9, 1),
            periode_fin=date(2025, 6, 30),
            total_heures=2500,
            heures_cm=400,
            heures_td=1200,
            heures_tp=900,
            repartition_types={"CM": 400, "TD": 1200, "TP": 900},
            charges_enseignants=[
                ChargeEnseignant(
                    enseignant="Dupont Jean",
                    heures_cm=60, heures_td=100, heures_tp=40, heures_projet=20,
                    total_heures=250, heures_statutaires=192, heures_complementaires=58
                ),
                ChargeEnseignant(
                    enseignant="Martin Sophie",
                    heures_cm=40, heures_td=120, heures_tp=50, heures_projet=10,
                    total_heures=240, heures_statutaires=192, heures_complementaires=48
                ),
            ],
            total_heures_complementaires=320,
            occupation_salles=[
                OccupationSalle(salle="A101", capacite=30, heures_occupees=800,
                               heures_disponibles=1400, taux_occupation=0.57),
                OccupationSalle(salle="B202", capacite=24, heures_occupees=650,
                               heures_disponibles=1400, taux_occupation=0.46),
            ],
            taux_occupation_moyen=0.52,
            heures_par_module={"R101": 120, "R102": 100, "R103": 80},
            evolution_hebdo={},
        )

```
---
## File: backend/app/adapters/parcoursup.py

```py
"""Parcoursup CSV file adapter."""

import io
from typing import Any
import pandas as pd
from datetime import date

from app.adapters.base import FileAdapter
from app.models.recrutement import (
    RecrutementIndicators,
    Candidat,
    VoeuStats,
    LyceeStats,
)


class ParcoursupAdapter(FileAdapter[RecrutementIndicators]):
    """
    Adapter for Parcoursup CSV exports.
    
    Parcoursup provides CSV exports with candidate data.
    Format varies by year but typically includes:
    - Candidate info (anonymized)
    - Bac type and mention
    - Geographic origin
    - Application status
    """
    
    @property
    def source_name(self) -> str:
        return "Parcoursup"
    
    async def fetch_raw(self, **kwargs) -> Any:
        """Not used for file adapters."""
        return {}
    
    def transform(self, raw_data: Any) -> RecrutementIndicators:
        """Transform parsed data to indicators."""
        return raw_data
    
    def parse_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Parse Parcoursup CSV file."""
        # Try different encodings common in French exports
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                return pd.read_csv(
                    io.BytesIO(file_content),
                    delimiter=";",
                    encoding=encoding,
                )
            except UnicodeDecodeError:
                continue
        
        # Fallback
        return pd.read_csv(io.BytesIO(file_content), delimiter=";")
    
    def parse_parcoursup_export(self, file_content: bytes, annee: int = None) -> RecrutementIndicators:
        """
        Parse Parcoursup export file.
        
        Expected columns (may vary):
        - Série du Bac / Type Bac
        - Mention au Bac
        - Département (origine)
        - Statut / Réponse
        - Rang
        """
        df = self.parse_file(file_content, "parcoursup.csv")
        df.columns = df.columns.str.lower().str.strip()
        
        annee = annee or date.today().year
        total = len(df)
        
        # Detect column names (they vary by year)
        bac_col = self._find_column(df, ["série du bac", "type bac", "bac", "série"])
        mention_col = self._find_column(df, ["mention au bac", "mention", "mention bac"])
        dept_col = self._find_column(df, ["département", "dept", "origine"])
        statut_col = self._find_column(df, ["statut", "réponse", "decision", "état"])
        lycee_col = self._find_column(df, ["lycée", "etablissement", "lycee"])
        
        # Count by status
        acceptes = 0
        confirmes = 0
        refuses = 0
        
        if statut_col:
            statuts = df[statut_col].str.lower().fillna("")
            acceptes = statuts.str.contains("accepté|oui|admis", regex=True).sum()
            confirmes = statuts.str.contains("confirmé|inscrit|définitif", regex=True).sum()
            refuses = statuts.str.contains("refusé|non|rejeté", regex=True).sum()
        
        # Count by bac type
        par_bac: dict[str, int] = {}
        if bac_col:
            par_bac = df[bac_col].value_counts().to_dict()
        
        # Count by mention
        par_mention: dict[str, int] = {}
        if mention_col:
            par_mention = df[mention_col].value_counts().to_dict()
        
        # Count by origin
        par_origine: dict[str, int] = {}
        if dept_col:
            par_origine = df[dept_col].value_counts().head(20).to_dict()
        
        # Top lycées
        top_lycees = []
        if lycee_col:
            lycee_counts = df[lycee_col].value_counts().head(10)
            top_lycees = [LyceeStats(lycee=k, count=v) for k, v in lycee_counts.items()]
        
        return RecrutementIndicators(
            annee_courante=annee,
            total_candidats=total,
            candidats_acceptes=acceptes,
            candidats_confirmes=confirmes if confirmes > 0 else acceptes,
            taux_acceptation=acceptes / total if total > 0 else 0,
            taux_confirmation=confirmes / acceptes if acceptes > 0 else 0,
            par_type_bac=par_bac,
            par_origine=par_origine,
            par_mention=par_mention,
            evolution=[],
            top_lycees=top_lycees,
        )
    
    def _find_column(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Find a column by trying multiple possible names."""
        for col in df.columns:
            col_lower = col.lower()
            for candidate in candidates:
                if candidate in col_lower:
                    return col
        return None


# Mock adapter for development
class MockParcoursupAdapter(FileAdapter[RecrutementIndicators]):
    """Mock Parcoursup adapter with sample data."""
    
    @property
    def source_name(self) -> str:
        return "Parcoursup (Mock)"
    
    async def fetch_raw(self, **kwargs) -> Any:
        return {}
    
    def transform(self, raw_data: Any) -> RecrutementIndicators:
        return self.get_mock_data()
    
    def parse_file(self, file_content: bytes, filename: str) -> Any:
        return {}
    
    def get_mock_data(self) -> RecrutementIndicators:
        """Return mock recruitment data."""
        return RecrutementIndicators(
            annee_courante=2024,
            total_candidats=850,
            candidats_acceptes=180,
            candidats_confirmes=52,
            taux_acceptation=0.21,
            taux_confirmation=0.29,
            par_type_bac={
                "Bac Général": 320,
                "Bac Techno STI2D": 280,
                "Bac Techno STMG": 120,
                "Bac Pro SN": 90,
                "Autre": 40,
            },
            par_origine={
                "59 - Nord": 180,
                "62 - Pas-de-Calais": 150,
                "80 - Somme": 85,
                "02 - Aisne": 70,
                "60 - Oise": 65,
                "Autres": 300,
            },
            par_mention={
                "Très Bien": 45,
                "Bien": 120,
                "Assez Bien": 280,
                "Passable": 350,
                "Non renseigné": 55,
            },
            evolution=[
                VoeuStats(annee=2021, nb_voeux=720, nb_acceptes=150, 
                         nb_confirmes=48, nb_refuses=570, nb_desistes=30),
                VoeuStats(annee=2022, nb_voeux=780, nb_acceptes=165,
                         nb_confirmes=50, nb_refuses=615, nb_desistes=28),
                VoeuStats(annee=2023, nb_voeux=820, nb_acceptes=175,
                         nb_confirmes=51, nb_refuses=645, nb_desistes=32),
                VoeuStats(annee=2024, nb_voeux=850, nb_acceptes=180,
                         nb_confirmes=52, nb_refuses=670, nb_desistes=35),
            ],
            top_lycees=[
                LyceeStats(lycee="Lycée Baggio - Lille", count=25),
                LyceeStats(lycee="Lycée Colbert - Tourcoing", count=18),
                LyceeStats(lycee="Lycée Branly - Boulogne", count=15),
                LyceeStats(lycee="Lycée Condorcet - Lens", count=12),
                LyceeStats(lycee="Lycée Baudelaire - Roubaix", count=10),
            ],
        )

```
---
## File: backend/app/api/__init__.py

```py
# API Routes

```
---
## File: backend/app/api/deps.py

```py
"""Common dependencies for API routes."""

from typing import Annotated, Optional
from functools import lru_cache
from enum import Enum
import logging

from fastapi import Depends, Path, HTTPException, Header, Query
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.adapters.scodoc import ScoDocAdapter
from app.adapters.excel import ExcelAdapter
from app.adapters.parcoursup import ParcoursupAdapter
from app.database import get_db

logger = logging.getLogger(__name__)


class Department(str, Enum):
    """Valid departments."""
    RT = "RT"
    GEII = "GEII"
    GCCD = "GCCD"
    GMP = "GMP"
    QLIO = "QLIO"
    CHIMIE = "CHIMIE"


VALID_DEPARTMENTS = [d.value for d in Department]


def validate_department(department: str) -> str:
    """Validate department code."""
    dept_upper = department.upper()
    if dept_upper not in VALID_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Département invalide: {department}. Valeurs autorisées: {', '.join(VALID_DEPARTMENTS)}"
        )
    return dept_upper


# Department path parameter dependency
DepartmentDep = Annotated[str, Path(
    ..., 
    description="Code du département (RT, GEII, GCCD, GMP, QLIO, CHIMIE)",
    pattern="^(RT|GEII|GCCD|GMP|QLIO|CHIMIE)$",
    examples=["RT", "GEII"]
)]


# Settings dependency
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ==================== AUTHENTICATION DEPENDENCIES ====================

def get_token_from_header(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    token: Optional[str] = Query(None, description="JWT token (alternative to header)"),
) -> Optional[str]:
    """Extract JWT token from Authorization header or query param."""
    if authorization:
        # Bearer token
        if authorization.startswith("Bearer "):
            return authorization[7:]
        return authorization
    return token


def get_current_user(
    token: Optional[str] = Depends(get_token_from_header),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user from JWT token.
    Returns None if no token or invalid token (for optional auth).
    """
    if not token:
        return None
    
    # Import here to avoid circular imports
    from app.api.routes.auth import decode_access_token
    from app.models.db_models import UserDB
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user or not user.is_active:
        return None
    
    return user


def require_auth(
    token: Optional[str] = Depends(get_token_from_header),
    db: Session = Depends(get_db),
):
    """
    Require authenticated user. Raises 401 if not authenticated.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    from app.api.routes.auth import decode_access_token
    from app.models.db_models import UserDB
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not validated")
    
    return user


# Type alias for authenticated user dependency
from app.models.db_models import UserDB
AuthUserDep = Annotated[UserDB, Depends(require_auth)]
OptionalUserDep = Annotated[Optional[UserDB], Depends(get_current_user)]


# ==================== PERMISSION CHECKING ====================

def get_user_permission_for_department(user: UserDB, department: str, db: Session):
    """Get user's permission object for a specific department."""
    from app.models.db_models import UserPermissionDB
    
    return db.query(UserPermissionDB).filter(
        UserPermissionDB.user_id == user.id,
        UserPermissionDB.department == department.upper()
    ).first()


def check_permission(
    user: UserDB,
    department: str,
    domain: str,  # scolarite, recrutement, budget, edt
    action: str,  # view, edit
    db: Session,
) -> bool:
    """
    Check if user has permission for a specific action on a domain in a department.
    Superadmins have all permissions.
    """
    logger.info(f"Checking permission: user={user.cas_login}, dept={department}, domain={domain}, action={action}")
    
    if user.is_superadmin:
        logger.info(f"User {user.cas_login} is superadmin - access granted")
        return True
    
    perm = get_user_permission_for_department(user, department, db)
    if not perm:
        logger.info(f"No permission found for user {user.cas_login} in dept {department} - access denied")
        return False
    
    # Dept admins have all permissions for their department
    if perm.is_dept_admin:
        logger.info(f"User {user.cas_login} is dept_admin for {department} - access granted")
        return True
    
    # Check specific permission
    perm_field = f"can_{action}_{domain}"
    has_perm = getattr(perm, perm_field, False)
    logger.info(f"User {user.cas_login} permission {perm_field}={has_perm}")
    return has_perm


def check_import_permission(user: UserDB, department: str, db: Session) -> bool:
    """Check if user can import data for a department."""
    if user.is_superadmin:
        return True
    
    perm = get_user_permission_for_department(user, department, db)
    if not perm:
        return False
    
    return perm.is_dept_admin or perm.can_import


def check_export_permission(user: UserDB, department: str, db: Session) -> bool:
    """Check if user can export data for a department."""
    if user.is_superadmin:
        return True
    
    perm = get_user_permission_for_department(user, department, db)
    if not perm:
        return False
    
    return perm.is_dept_admin or perm.can_export


# ==================== PERMISSION DEPENDENCY FACTORIES ====================

class PermissionChecker:
    """
    Dependency factory for checking domain permissions.
    Usage: Depends(PermissionChecker("scolarite", "view"))
    """
    def __init__(self, domain: str, action: str):
        self.domain = domain
        self.action = action
    
    def __call__(
        self,
        department: DepartmentDep,
        user: UserDB = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> UserDB:
        if not check_permission(user, department, self.domain, self.action, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: cannot {self.action} {self.domain} for department {department}"
            )
        return user


class ImportPermissionChecker:
    """Dependency factory for checking import permission."""
    def __call__(
        self,
        department: DepartmentDep,
        user: UserDB = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> UserDB:
        if not check_import_permission(user, department, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: cannot import data for department {department}"
            )
        return user


class ExportPermissionChecker:
    """Dependency factory for checking export permission."""
    def __call__(
        self,
        department: DepartmentDep,
        user: UserDB = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> UserDB:
        if not check_export_permission(user, department, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: cannot export data for department {department}"
            )
        return user


# Pre-built permission checkers for common use cases
require_view_scolarite = PermissionChecker("scolarite", "view")
require_edit_scolarite = PermissionChecker("scolarite", "edit")
require_view_recrutement = PermissionChecker("recrutement", "view")
require_edit_recrutement = PermissionChecker("recrutement", "edit")
require_view_budget = PermissionChecker("budget", "view")
require_edit_budget = PermissionChecker("budget", "edit")
require_view_edt = PermissionChecker("edt", "view")
require_edit_edt = PermissionChecker("edt", "edit")
require_import = ImportPermissionChecker()
require_export = ExportPermissionChecker()


def get_scodoc_adapter_for_department(department: str) -> ScoDocAdapter:
    """Get ScoDoc adapter instance for a specific department."""
    settings = get_settings()
    return ScoDocAdapter(
        base_url=settings.scodoc_base_url,
        username=settings.scodoc_username,
        password=settings.scodoc_password,
        department=department,  # Use the department from path
    )


@lru_cache
def get_scodoc_adapter() -> ScoDocAdapter:
    """Get ScoDoc adapter instance (deprecated - use get_scodoc_adapter_for_department)."""
    settings = get_settings()
    return ScoDocAdapter(
        base_url=settings.scodoc_base_url,
        username=settings.scodoc_username,
        password=settings.scodoc_password,
        department=settings.scodoc_department,
    )


@lru_cache
def get_excel_adapter() -> ExcelAdapter:
    """Get Excel adapter instance."""
    return ExcelAdapter()


@lru_cache
def get_parcoursup_adapter() -> ParcoursupAdapter:
    """Get Parcoursup adapter instance."""
    return ParcoursupAdapter()


# Adapter dependencies
ScoDocDep = Annotated[ScoDocAdapter, Depends(get_scodoc_adapter)]
ExcelDep = Annotated[ExcelAdapter, Depends(get_excel_adapter)]
ParcoursupDep = Annotated[ParcoursupAdapter, Depends(get_parcoursup_adapter)]

```
---
## File: backend/app/api/routes/__init__.py

```py
# API Routes

```
---
## File: backend/app/api/routes/admin.py

```py
"""Administration API routes with database persistence.

Simplified admin module:
- Dashboard: Global stats overview
- Sources: CRUD for data source configuration (for future real integrations)
- Settings: System settings management
- Cache: Redis cache stats and clearing
- Jobs: APScheduler job listing and manual execution
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import admin_crud

from app.models.admin import (
    DataSourceConfig,
    DataSourceCreate,
    DataSourceUpdate,
    DataSourceType,
    SystemSettings,
    ScheduledJob,
    CacheStats,
    AdminDashboard,
)
from app.services import cache, scheduler
from app.config import get_settings

router = APIRouter()
settings = get_settings()


# ============== Dashboard Admin ==============

@router.get(
    "/dashboard",
    response_model=AdminDashboard,
    summary="Vue d'ensemble administration",
)
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Récupère la vue d'ensemble de l'administration.
    
    Inclut les statistiques des sources, du cache et des jobs.
    """
    # Get sources from DB
    sources = admin_crud.get_all_sources(db)
    
    cache_stats_raw = await cache.get_stats()
    cache_stats = CacheStats(
        connected=cache_stats_raw.get("connected", False),
        keys=cache_stats_raw.get("keys", 0),
        hits=cache_stats_raw.get("hits", 0),
        misses=cache_stats_raw.get("misses", 0),
        memory_used=cache_stats_raw.get("memory_used", "N/A"),
        hit_rate=(
            cache_stats_raw.get("hits", 0) / 
            max(cache_stats_raw.get("hits", 0) + cache_stats_raw.get("misses", 0), 1)
        ),
    )
    
    jobs = scheduler.get_jobs() if settings.cache_enabled else []
    
    return AdminDashboard(
        total_sources=len(sources),
        active_sources=sum(1 for s in sources if s.status == "active"),
        sources_in_error=sum(1 for s in sources if s.status == "error"),
        cache_stats=cache_stats,
        scheduled_jobs=len(jobs),
        jobs_running=0,
    )


# ============== Data Sources ==============

@router.get(
    "/sources",
    summary="Liste des sources de données",
)
async def list_data_sources(
    type: Optional[str] = Query(None, description="Filtrer par type"),
    enabled: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    db: Session = Depends(get_db),
):
    """Récupère la liste des sources de données configurées."""
    sources = admin_crud.get_all_sources(db, source_type=type, enabled=enabled)
    return [admin_crud.source_to_dict(s) for s in sources]


@router.get(
    "/sources/{source_id}",
    summary="Détails d'une source",
)
async def get_data_source(source_id: str, db: Session = Depends(get_db)):
    """Récupère les détails d'une source de données."""
    source = admin_crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return admin_crud.source_to_dict(source)


@router.post(
    "/sources",
    summary="Créer une source",
)
async def create_data_source(data: DataSourceCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle source de données."""
    source_id = f"{data.type.value}-{uuid.uuid4().hex[:8]}"
    
    source_data = {
        "source_id": source_id,
        "name": data.name,
        "type": data.type.value,
        "status": "inactive",
        "description": data.description,
        "base_url": data.base_url,
        "username": data.username,
        "enabled": 1 if data.enabled else 0,
        "auto_sync": 1 if data.auto_sync else 0,
        "sync_interval_hours": data.sync_interval_hours,
    }
    
    source = admin_crud.create_source(db, source_data)
    return admin_crud.source_to_dict(source)


@router.put(
    "/sources/{source_id}",
    summary="Modifier une source",
)
async def update_data_source(
    source_id: str, 
    data: DataSourceUpdate, 
    db: Session = Depends(get_db)
):
    """Met à jour une source de données."""
    source = admin_crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    update_data = data.model_dump(exclude_unset=True)
    # Convert booleans to int for SQLite
    if "enabled" in update_data:
        update_data["enabled"] = 1 if update_data["enabled"] else 0
    if "auto_sync" in update_data:
        update_data["auto_sync"] = 1 if update_data["auto_sync"] else 0
    
    updated = admin_crud.update_source(db, source_id, update_data)
    return admin_crud.source_to_dict(updated)


@router.delete(
    "/sources/{source_id}",
    summary="Supprimer une source",
)
async def delete_data_source(source_id: str, db: Session = Depends(get_db)):
    """Supprime une source de données."""
    source = admin_crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    
    admin_crud.delete_source(db, source_id)
    return {"message": "Source supprimée", "id": source_id}


# ============== Settings ==============

@router.get(
    "/settings",
    response_model=SystemSettings,
    summary="Paramètres système",
)
async def get_system_settings(db: Session = Depends(get_db)):
    """Récupère les paramètres système du dashboard."""
    settings_dict = admin_crud.get_all_settings(db)
    return SystemSettings(**settings_dict)


@router.put(
    "/settings",
    response_model=SystemSettings,
    summary="Modifier les paramètres",
)
async def update_system_settings(data: SystemSettings, db: Session = Depends(get_db)):
    """Met à jour les paramètres système."""
    settings_dict = data.model_dump()
    updated = admin_crud.update_all_settings(db, settings_dict)
    return SystemSettings(**updated)


# ============== Cache ==============

@router.get(
    "/cache/stats",
    response_model=CacheStats,
    summary="Statistiques du cache",
)
async def get_cache_stats():
    """Récupère les statistiques du cache Redis."""
    stats = await cache.get_stats()
    return CacheStats(
        connected=stats.get("connected", False),
        keys=stats.get("keys", 0),
        hits=stats.get("hits", 0),
        misses=stats.get("misses", 0),
        memory_used=stats.get("memory_used", "N/A"),
        hit_rate=(
            stats.get("hits", 0) / 
            max(stats.get("hits", 0) + stats.get("misses", 0), 1)
        ),
    )


@router.post(
    "/cache/clear",
    summary="Vider le cache",
)
async def clear_cache(
    domain: Optional[str] = Query(None, description="Domaine à vider (scolarite, recrutement, budget, edt)"),
):
    """Vide le cache (tout ou par domaine)."""
    if domain:
        pattern = f"{domain}:*"
        deleted = await cache.delete_pattern(pattern)
        return {"message": f"Cache {domain} vidé", "keys_deleted": deleted}
    else:
        deleted = await cache.delete_pattern("*")
        return {"message": "Tout le cache a été vidé", "keys_deleted": deleted}


@router.post(
    "/cache/warmup",
    summary="Pré-charger le cache",
)
async def warmup_cache(
    department: Optional[str] = Query(None, description="Département spécifique (RT, GEII, etc.) ou tous si non spécifié"),
    db: Session = Depends(get_db),
):
    """
    Pré-charge le cache avec les données de tous les dashboards.
    Appelle directement les services pour chaque département et met en cache les résultats.
    """
    import logging
    from app.api.deps import VALID_DEPARTMENTS, get_scodoc_adapter_for_department
    from app.services.cache import CacheKeys
    from app.services.indicateurs_service import IndicateursService
    from app.services.alertes_service import AlertesService
    # Import route helper functions for proper indicator building
    from app.api.routes.budget import get_budget_from_db
    from app.api.routes.recrutement import get_recrutement_from_db
    
    logger = logging.getLogger(__name__)
    
    departments = [department.upper()] if department else VALID_DEPARTMENTS
    results = {"departments": {}, "total_cached": 0, "errors": []}
    
    async def warmup_single_dept(dept: str):
        dept_results = {"cached": 0, "failed": []}
        adapter = None
        
        try:
            # Get adapter for this department
            adapter = get_scodoc_adapter_for_department(dept)
            
            # Sub-tasks for parallel execution
            async def task_scolarite():
                try:
                    data = await adapter.get_data()
                    if data:
                        await cache.set(CacheKeys.scolarite_indicators(None, dept), data, ttl=CacheKeys.TTL_LONG)
                        return 1
                except Exception as e:
                    dept_results["failed"].append({"endpoint": "scolarite/indicators", "error": str(e)})
                    logger.error(f"Failed to cache scolarite for {dept}: {e}")
                return 0

            async def task_recrutement():
                try:
                    indicators = get_recrutement_from_db(db, dept)
                    if indicators:
                        await cache.set(CacheKeys.recrutement_indicators(None, dept), indicators, ttl=CacheKeys.TTL_LONG)
                        return 1
                except Exception as e:
                    dept_results["failed"].append({"endpoint": "recrutement/indicators", "error": str(e)})
                return 0

            async def task_budget():
                try:
                    indicators = get_budget_from_db(db, dept)
                    if indicators:
                        await cache.set(CacheKeys.budget_indicators(None, dept), indicators, ttl=CacheKeys.TTL_LONG)
                        return 1
                except Exception as e:
                    dept_results["failed"].append({"endpoint": "budget/indicators", "error": str(e)})
                return 0

            async def task_indicateurs():
                cached_count = 0
                try:
                    service = IndicateursService(adapter)
                    
                    # Independent indicator tasks
                    async def sub_tableau():
                        res = await service.get_tableau_bord()
                        if res:
                            await cache.set(CacheKeys.indicateurs_tableau_bord(dept), res, ttl=CacheKeys.TTL_MEDIUM)
                            await cache.set(CacheKeys.indicateurs_tableau_bord(dept, annee="2024-2025"), res, ttl=CacheKeys.TTL_MEDIUM)
                            return 2
                        return 0
                    
                    async def sub_stats():
                        res = await service.get_statistiques_cohorte()
                        if res:
                            await cache.set(CacheKeys.indicateurs_statistiques(dept), res, ttl=CacheKeys.TTL_MEDIUM)
                            return 1
                        return 0
                    
                    async def sub_taux():
                        res = await service.get_taux_validation()
                        if res:
                            await cache.set(CacheKeys.indicateurs_taux_validation(dept), res, ttl=CacheKeys.TTL_MEDIUM)
                            return 1
                        return 0
                    
                    async def sub_mentions():
                        res = await service.get_mentions()
                        if res:
                            await cache.set(CacheKeys.indicateurs_mentions(dept), res, ttl=CacheKeys.TTL_MEDIUM)
                            return 1
                        return 0
                    
                    async def sub_modules():
                        res = await service.get_modules_analyse()
                        if res:
                            await cache.set_list(CacheKeys.indicateurs_modules(dept), res, ttl=CacheKeys.TTL_MEDIUM)
                            return 1
                        return 0
                    
                    async def sub_absences():
                        res = await service.get_analyse_absenteisme()
                        if res:
                            await cache.set(CacheKeys.indicateurs_absenteisme(dept), res, ttl=CacheKeys.TTL_MEDIUM)
                            return 1
                        return 0

                    async def sub_autres():
                        # These are mock/simple for now but good to parallelize
                        c = 0
                        res = await service.get_comparaison_interannuelle()
                        if res: await cache.set(CacheKeys.indicateurs_comparaison(dept), res, ttl=CacheKeys.TTL_LONG); c += 1
                        res = await service.get_analyse_type_bac()
                        if res: await cache.set(CacheKeys.indicateurs_type_bac(dept), res, ttl=CacheKeys.TTL_MEDIUM); c += 1
                        res = await service.get_analyse_boursiers()
                        if res: await cache.set(CacheKeys.indicateurs_boursiers(dept), res, ttl=CacheKeys.TTL_MEDIUM); c += 1
                        res = await service.get_indicateurs_predictifs()
                        if res: await cache.set(CacheKeys.indicateurs_predictifs(dept), res, ttl=CacheKeys.TTL_MEDIUM); c += 1
                        return c

                    sub_results = await asyncio.gather(
                        sub_tableau(), sub_stats(), sub_taux(), sub_mentions(), 
                        sub_modules(), sub_absences(), sub_autres()
                    )
                    cached_count = sum(sub_results)
                except Exception as e:
                    dept_results["failed"].append({"endpoint": "indicateurs/*", "error": str(e)})
                return cached_count

            async def task_alertes():
                cached_count = 0
                try:
                    alertes_service = AlertesService(adapter)
                    stats_alertes = await alertes_service.get_statistiques_alertes()
                    if stats_alertes:
                        await cache.set_raw(CacheKeys.alertes_stats(dept), stats_alertes, ttl=CacheKeys.TTL_SHORT)
                        cached_count += 1
                    
                    alertes_list = await alertes_service.get_all_alertes(limit=100)
                    if alertes_list:
                        await cache.set_raw(
                            CacheKeys.alertes_list(dept),
                            [a.model_dump(mode="json") for a in alertes_list],
                            ttl=CacheKeys.TTL_MEDIUM
                        )
                        cached_count += 1
                except Exception as e:
                    dept_results["failed"].append({"endpoint": "alertes/*", "error": str(e)})
                return cached_count

            # Run all high-level tasks in parallel
            task_results = await asyncio.gather(
                task_scolarite(), task_recrutement(), task_budget(), 
                task_indicateurs(), task_alertes()
            )
            dept_results["cached"] = sum(task_results)
            
        except Exception as e:
            logger.error(f"Critical failure warming up {dept}: {e}")
            dept_results["failed"].append({"endpoint": "all", "error": str(e)})
        finally:
            if adapter and hasattr(adapter, 'close'):
                await adapter.close()
        
        return dept, dept_results

    # Run all departments in parallel
    import asyncio
    all_dept_tasks = [warmup_single_dept(d) for d in departments]
    finished_tasks = await asyncio.gather(*all_dept_tasks)
    
    for dept, dept_results in finished_tasks:
        results["departments"][dept] = dept_results
        results["total_cached"] += dept_results["cached"]
        if dept_results["failed"]:
            results["errors"].extend([f"{dept}: {f}" for f in dept_results["failed"]])
    
    return {
        "message": f"Cache pré-chargé pour {len(departments)} département(s) en parallèle",
        "details": results
    }


# ============== Jobs ==============

@router.get(
    "/jobs",
    response_model=list[ScheduledJob],
    summary="Jobs planifiés",
)
async def list_scheduled_jobs():
    """Récupère la liste des jobs planifiés (APScheduler)."""
    jobs_raw = scheduler.get_jobs() if settings.cache_enabled else []
    
    jobs = []
    for job in jobs_raw:
        jobs.append(ScheduledJob(
            id=job["id"],
            name=job["name"],
            next_run=datetime.fromisoformat(job["next_run"]) if job.get("next_run") else None,
            enabled=True,
            schedule="Voir configuration",
        ))
    
    # If no jobs from scheduler, show default job list (what would run)
    if not jobs:
        default_jobs = [
            ScheduledJob(
                id="refresh_scolarite",
                name="Rafraîchir données scolarité",
                description="Synchronise les données depuis ScoDoc",
                schedule="Toutes les heures",
                enabled=settings.cache_enabled,
            ),
            ScheduledJob(
                id="refresh_budget",
                name="Rafraîchir données budget",
                description="Recalcule les indicateurs budget",
                schedule="Toutes les 6 heures",
                enabled=settings.cache_enabled,
            ),
            ScheduledJob(
                id="refresh_recrutement",
                name="Rafraîchir données recrutement",
                description="Recalcule les indicateurs recrutement",
                schedule="Toutes les 6 heures",
                enabled=settings.cache_enabled,
            ),
            ScheduledJob(
                id="cleanup_cache",
                name="Nettoyage du cache",
                description="Supprime les clés expirées",
                schedule="Quotidien à minuit",
                enabled=settings.cache_enabled,
            ),
        ]
        return default_jobs
    
    return jobs


@router.post(
    "/jobs/{job_id}/run",
    summary="Exécuter un job",
)
async def run_job_now(job_id: str):
    """Exécute un job planifié immédiatement."""
    try:
        await scheduler.run_job_now(job_id)
        return {"message": f"Job {job_id} exécuté", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Database Seeding ==============

@router.post(
    "/seed",
    summary="Seed database with mock data",
)
async def seed_database_endpoint(
    force: bool = Query(False, description="Force reseed (delete existing data)"),
    db: Session = Depends(get_db),
):
    """
    Seed the database with mock/demo data.
    
    Creates sample users with different permission levels:
    - admin: Superadmin with all permissions
    - chef_rt: RT department admin
    - chef_geii: GEII department admin  
    - enseignant_rt: RT teacher (view scolarite/edt only)
    - secretaire: Secretary (scolarite/recrutement for RT & GEII)
    - pending_user: Inactive account (pending validation)
    
    Also creates mock data for:
    - Budget: 3 years of budget data per department
    - Recrutement: 4 years of Parcoursup data per department
    
    Use force=true to delete existing data and reseed.
    """
    from app.seeds import seed_database
    
    result = seed_database(db, force=force)
    
    if result["skipped"]:
        return {
            "status": "skipped",
            "message": "Database already has data. Use force=true to reseed.",
        }
    
    return {
        "status": "success",
        "message": "Database seeded successfully",
        "data": {
            "users_created": result["users_created"],
            "permissions_created": result["permissions_created"],
            "budgets_created": result["budgets_created"],
            "depenses_created": result["depenses_created"],
            "campagnes_created": result["campagnes_created"],
            "candidats_created": result["candidats_created"],
        },
        "test_accounts": [
            {"login": "admin", "role": "Superadmin (all permissions)"},
            {"login": "chef_rt", "role": "RT department admin"},
            {"login": "chef_geii", "role": "GEII department admin"},
            {"login": "enseignant_rt", "role": "RT teacher (view scolarite/edt only)"},
            {"login": "secretaire", "role": "Secretary (scolarite/recrutement for RT & GEII)"},
            {"login": "pending_user", "role": "Inactive account (pending validation)"},
        ],
    }

```
---
## File: backend/app/api/routes/alertes.py

```py
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
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
    search: Optional[str] = Query(None, description="Recherche par nom/prénom"),
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
        formation=formation,
        modalite=modalite,
        search=search,
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
    semestre: Optional[str] = Query(None, description="Filtrer par semestre"),
    formation: Optional[str] = Query(None, description="Filtrer par formation"),
    modalite: Optional[str] = Query(None, description="Filtrer par modalité (FI/FA)"),
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
    
    stats = await service.get_statistiques_alertes(
        semestre=semestre,
        formation=formation,
        modalite=modalite
    )
    
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

```
---
## File: backend/app/api/routes/auth.py

```py
"""Authentication API routes - CAS login/logout and JWT tokens."""

from fastapi import APIRouter, HTTPException, Depends, Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging

from app.database import get_db
from app.config import get_settings
from app.adapters.cas import get_cas_adapter
from app.models.db_models import UserDB, UserPermissionDB, DEPARTMENTS

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ==================== JWT UTILITIES ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== USER HELPERS ====================

def get_or_create_user(db: Session, cas_login: str, attributes: dict) -> UserDB:
    """Get existing user or create new one from CAS data."""
    user = db.query(UserDB).filter(UserDB.cas_login == cas_login).first()
    
    if user:
        # Update last login
        user.date_derniere_connexion = datetime.utcnow()
        # Update info from CAS if available
        if attributes.get('email'):
            user.email = attributes['email']
        if attributes.get('displayName'):
            parts = attributes['displayName'].split(' ', 1)
            user.prenom = parts[0] if parts else ''
            user.nom = parts[1] if len(parts) > 1 else ''
        db.commit()
        return user
    
    # Create new user (not active by default - must be validated by admin)
    new_user = UserDB(
        cas_login=cas_login,
        email=attributes.get('email'),
        prenom=attributes.get('displayName', '').split(' ')[0] if attributes.get('displayName') else None,
        nom=' '.join(attributes.get('displayName', '').split(' ')[1:]) if attributes.get('displayName') else None,
        is_active=False,  # Must be validated by admin
        is_superadmin=False,
        date_derniere_connexion=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"Created new user: {cas_login} (pending validation)")
    return new_user


def get_user_permissions(db: Session, user: UserDB) -> dict:
    """Get user's permissions structured by department."""
    perms = db.query(UserPermissionDB).filter(UserPermissionDB.user_id == user.id).all()
    
    permissions = {}
    for perm in perms:
        permissions[perm.department] = {
            'can_view_scolarite': perm.can_view_scolarite,
            'can_edit_scolarite': perm.can_edit_scolarite,
            'can_view_recrutement': perm.can_view_recrutement,
            'can_edit_recrutement': perm.can_edit_recrutement,
            'can_view_budget': perm.can_view_budget,
            'can_edit_budget': perm.can_edit_budget,
            'can_view_edt': perm.can_view_edt,
            'can_edit_edt': perm.can_edit_edt,
            'can_import': perm.can_import,
            'can_export': perm.can_export,
            'is_dept_admin': perm.is_dept_admin,
        }
    
    return permissions


def serialize_user(user: UserDB, permissions: dict) -> dict:
    """Serialize user for API response."""
    return {
        'id': user.id,
        'cas_login': user.cas_login,
        'email': user.email,
        'nom': user.nom,
        'prenom': user.prenom,
        'is_active': user.is_active,
        'is_superadmin': user.is_superadmin,
        'date_creation': user.date_creation.isoformat() if user.date_creation else None,
        'date_derniere_connexion': user.date_derniere_connexion.isoformat() if user.date_derniere_connexion else None,
        'permissions': permissions,
    }


# ==================== AUTH ROUTES ====================

@router.get("/login")
async def login_redirect(return_url: Optional[str] = Query(None)):
    """
    Redirect to CAS login page.
    
    After successful CAS login, user will be redirected back to /auth/cas/callback
    """
    cas = get_cas_adapter(
        cas_url=settings.cas_server_url,
        service_url=settings.cas_service_url,
        use_mock=settings.cas_use_mock,
    )
    
    login_url = cas.get_login_url(return_url)
    return RedirectResponse(url=login_url)


@router.get("/cas/callback")
async def cas_callback(
    ticket: Optional[str] = Query(None),
    return_url: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    CAS callback endpoint - validates ticket and creates session.
    
    CAS redirects here with a ticket parameter after successful login.
    """
    if not ticket:
        raise HTTPException(status_code=400, detail="No ticket provided")
    
    cas = get_cas_adapter(
        cas_url=settings.cas_server_url,
        service_url=settings.cas_service_url,
        use_mock=settings.cas_use_mock,
    )
    
    try:
        # Validate ticket with CAS server
        user_info = await cas.validate_ticket(ticket)
        
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid CAS ticket")
        
        cas_login = user_info['user']
        attributes = user_info.get('attributes', {})
        
        # Get or create user in database
        user = get_or_create_user(db, cas_login, attributes)
        
        # Check if user is validated
        if not user.is_active:
            # Redirect to pending page
            redirect_url = f"{settings.frontend_url}/auth/pending"
            return RedirectResponse(url=redirect_url)
        
        # Create JWT token
        permissions = get_user_permissions(db, user)
        token_data = {
            'sub': str(user.id),
            'cas_login': user.cas_login,
            'is_superadmin': user.is_superadmin,
        }
        token = create_access_token(token_data)
        
        # Redirect to frontend with token
        redirect_url = return_url or settings.frontend_url
        redirect_url = f"{redirect_url}?token={token}"
        
        return RedirectResponse(url=redirect_url)
        
    finally:
        await cas.close()


@router.get("/logout")
async def logout(return_url: Optional[str] = Query(None)):
    """
    Logout - redirect to CAS logout.
    """
    cas = get_cas_adapter(
        cas_url=settings.cas_server_url,
        service_url=settings.cas_service_url,
        use_mock=settings.cas_use_mock,
    )
    
    redirect = return_url or settings.frontend_url
    logout_url = cas.get_logout_url(redirect)
    return RedirectResponse(url=logout_url)


@router.get("/me")
async def get_current_user(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user info.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not validated")
    
    permissions = get_user_permissions(db, user)
    return serialize_user(user, permissions)


@router.post("/validate-token")
async def validate_token(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """
    Validate JWT token and return basic user info.
    """
    payload = decode_access_token(token)
    if not payload:
        return {"valid": False, "error": "Invalid or expired token"}
    
    user_id = int(payload.get('sub'))
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user:
        return {"valid": False, "error": "User not found"}
    
    if not user.is_active:
        return {"valid": False, "error": "Account not validated", "pending": True}
    
    return {
        "valid": True,
        "user_id": user.id,
        "cas_login": user.cas_login,
        "is_superadmin": user.is_superadmin,
    }


# ==================== DEV/MOCK ROUTES ====================

@router.post("/dev/login")
async def dev_login(
    username: str = Query(..., description="Username for mock login"),
    db: Session = Depends(get_db),
):
    """
    Development-only: Direct login without CAS.
    Only available when cas_use_mock is True.
    """
    if not settings.cas_use_mock:
        raise HTTPException(status_code=403, detail="Dev login not available in production")
    
    # Create mock CAS attributes
    attributes = {
        'email': f'{username.replace(" ", ".").lower()}@univ.fr',
        'displayName': username.replace('.', ' ').title(),
    }
    
    # Get or create user
    user = get_or_create_user(db, username, attributes)
    
    # For dev, auto-activate and make superadmin if first user
    if not user.is_active:
        user_count = db.query(UserDB).count()
        if user_count == 1:
            # First user becomes superadmin
            user.is_active = True
            user.is_superadmin = True
            user.date_validation = datetime.utcnow()
            db.commit()
            logger.info(f"Auto-activated first user as superadmin: {username}")
        else:
            return {
                "error": "Account pending validation",
                "pending": True,
                "user_id": user.id,
            }
    
    # Create JWT token
    permissions = get_user_permissions(db, user)
    token_data = {
        'sub': str(user.id),
        'cas_login': user.cas_login,
        'is_superadmin': user.is_superadmin,
    }
    token = create_access_token(token_data)
    
    return {
        "token": token,
        "user": serialize_user(user, permissions),
    }

```
---
## File: backend/app/api/routes/budget.py

```py
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

```
---
## File: backend/app/api/routes/budget_admin.py

```py
"""Budget Admin API routes with CRUD operations."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.crud import budget_crud
from app.api.deps import (
    DepartmentDep,
    require_view_budget, require_edit_budget, require_import
)
from app.models.db_models import UserDB
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
    user: UserDB = Depends(require_view_budget),
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
    user: UserDB = Depends(require_view_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_view_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_edit_budget),
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
    user: UserDB = Depends(require_import),
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
    user: UserDB = Depends(require_view_budget),
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

```
---
## File: backend/app/api/routes/edt.py

```py
"""EDT (Emploi du Temps) API routes."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from typing import Optional
from datetime import date

from app.models.edt import EDTIndicators, ChargeEnseignant
from app.models.db_models import UserDB
from app.adapters.excel import MockExcelAdapter, ExcelAdapter
from app.api.deps import (
    DepartmentDep,
    require_view_edt, require_edit_edt, require_import
)
from app.services import cache, CacheKeys
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Use mock adapter for development
_mock_adapter = MockExcelAdapter()
_file_adapter = ExcelAdapter()


@router.get("/indicators", response_model=EDTIndicators)
async def get_edt_indicators(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_edt),
    annee: Optional[str] = Query(None, description="Année universitaire (ex: 2024-2025)"),
    refresh: bool = Query(False, description="Force cache refresh"),
):
    """
    Get aggregated EDT indicators.
    
    Returns workload statistics, room occupation, and hour distribution.
    """
    try:
        cache_key = CacheKeys.edt_indicators(annee, department)
        
        # Try cache first (unless refresh requested)
        if not refresh:
            cached = await cache.get(cache_key, EDTIndicators)
            if cached:
                return cached
        
        # Fetch fresh data
        data = _mock_adapter.get_mock_edt()
        
        # Store in cache
        await cache.set(cache_key, data, settings.cache_ttl_edt)
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charges", response_model=list[ChargeEnseignant])
async def get_charges_enseignants(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_edt),
    enseignant: Optional[str] = Query(None, description="Filter by teacher name"),
):
    """
    Get teacher workloads.
    
    Returns hours by type (CM/TD/TP) and complementary hours.
    """
    data = _mock_adapter.get_mock_edt()
    charges = data.charges_enseignants
    
    if enseignant:
        charges = [c for c in charges if enseignant.lower() in c.enseignant.lower()]
    
    return charges


@router.get("/occupation")
async def get_occupation_salles(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_edt),
    salle: Optional[str] = Query(None, description="Filter by room"),
):
    """
    Get room occupation rates.
    """
    data = _mock_adapter.get_mock_edt()
    occupation = data.occupation_salles
    
    if salle:
        occupation = [o for o in occupation if salle.lower() in o.salle.lower()]
    
    return {
        "salles": occupation,
        "taux_moyen": data.taux_occupation_moyen,
    }


@router.get("/repartition")
async def get_repartition_heures(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_edt),
):
    """
    Get hours distribution by type (CM/TD/TP).
    """
    data = _mock_adapter.get_mock_edt()
    total = data.total_heures
    
    return {
        "total": total,
        "cm": {"heures": data.heures_cm, "pourcentage": data.heures_cm / total if total > 0 else 0},
        "td": {"heures": data.heures_td, "pourcentage": data.heures_td / total if total > 0 else 0},
        "tp": {"heures": data.heures_tp, "pourcentage": data.heures_tp / total if total > 0 else 0},
    }


@router.get("/heures-complementaires")
async def get_heures_complementaires(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_edt),
):
    """
    Get complementary hours summary.
    """
    data = _mock_adapter.get_mock_edt()
    
    # Teachers with complementary hours
    with_hc = [c for c in data.charges_enseignants if c.heures_complementaires > 0]
    
    return {
        "total": data.total_heures_complementaires,
        "enseignants": len(with_hc),
        "detail": [
            {"enseignant": c.enseignant, "heures": c.heures_complementaires}
            for c in sorted(with_hc, key=lambda x: -x.heures_complementaires)
        ],
    }


@router.get("/par-module")
async def get_heures_par_module(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_edt),
):
    """
    Get hours by module.
    """
    data = _mock_adapter.get_mock_edt()
    return {
        "modules": [
            {"module": k, "heures": v}
            for k, v in sorted(data.heures_par_module.items(), key=lambda x: -x[1])
        ],
        "total": sum(data.heures_par_module.values()),
    }


@router.post("/import")
async def import_edt_file(
    department: DepartmentDep,
    user: UserDB = Depends(require_import),
    file: UploadFile = File(..., description="EDT Excel file"),
    annee: Optional[str] = Query(None, description="Année universitaire"),
):
    """
    Import EDT Excel file.
    
    Expected columns: Enseignant, Module, Type (CM/TD/TP), Heures, Salle
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    try:
        content = await file.read()
        indicators = _file_adapter.parse_edt_file(content)
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors du parsing du fichier: {str(e)}"
        )

```
---
## File: backend/app/api/routes/indicateurs.py

```py
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
    cache_key = CacheKeys.indicateurs_tableau_bord(department, annee, semestre)
    
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
    cache_key = CacheKeys.indicateurs_statistiques(department, semestre)
    
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
    cache_key = CacheKeys.indicateurs_taux_validation(department, semestre)
    
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
    cache_key = CacheKeys.indicateurs_mentions(department, semestre)
    
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
    cache_key = CacheKeys.indicateurs_modules(department, semestre, tri)
    
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
    cache_key = CacheKeys.indicateurs_absenteisme(department, semestre)
    
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
    cache_key = CacheKeys.indicateurs_type_bac(department, semestre)
    
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
    cache_key = CacheKeys.indicateurs_boursiers(department, semestre)
    
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
    cache_key = CacheKeys.indicateurs_predictifs(department, semestre)
    
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

```
---
## File: backend/app/api/routes/recrutement_admin.py

```py
"""Recrutement/Parcoursup Admin API routes with CRUD operations."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.crud import recrutement_crud
from app.api.deps import (
    DepartmentDep,
    require_view_recrutement, require_edit_recrutement, require_import
)
from app.models.db_models import UserDB
from app.schemas.recrutement import (
    CampagneCreate,
    CampagneUpdate,
    CampagneResponse,
    CampagneSummary,
    CandidatCreate,
    CandidatUpdate,
    CandidatResponse,
    CandidatBulkCreate,
    ParcoursupStats,
    ParcoursupStatsInput,
    EvolutionRecrutement,
    ImportParcoursupResult,
)
from app.models.recrutement import RecrutementIndicators, VoeuStats, LyceeStats
from app.models.db_models import CampagneRecrutement

router = APIRouter()


# ==================== CAMPAGNES ====================

@router.get("/campagnes", response_model=list[CampagneSummary])
async def list_campagnes(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
):
    """List all recruitment campaigns."""
    campagnes = recrutement_crud.get_all_campagnes(db, department, skip=skip, limit=limit)
    result = []
    for c in campagnes:
        stats = recrutement_crud.get_parcoursup_stats(db, department, c.annee)
        nb_candidats = stats.nb_voeux if stats else 0
        nb_confirmes = stats.nb_confirmes if stats else 0
        taux = nb_confirmes / c.nb_places if c.nb_places > 0 else 0
        
        result.append(CampagneSummary(
            id=c.id,
            annee=c.annee,
            nb_places=c.nb_places,
            nb_candidats=nb_candidats,
            nb_confirmes=nb_confirmes,
            taux_remplissage=round(taux, 2),
        ))
    return result


@router.get("/campagne/{annee}", response_model=CampagneResponse)
async def get_campagne(
    department: DepartmentDep,
    annee: int,
    user: UserDB = Depends(require_view_recrutement),
    db: Session = Depends(get_db),
):
    """Get campaign details for a specific year."""
    campagne = recrutement_crud.get_campagne(db, department, annee)
    if not campagne:
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    
    return CampagneResponse(
        id=campagne.id,
        annee=campagne.annee,
        nb_places=campagne.nb_places,
        date_debut=campagne.date_debut,
        date_fin=campagne.date_fin,
        rang_dernier_appele=campagne.rang_dernier_appele,
        date_creation=campagne.date_creation,
        date_modification=campagne.date_modification,
        nb_candidats=stats.nb_voeux if stats else 0,
        nb_acceptes=stats.nb_acceptes if stats else 0,
        nb_confirmes=stats.nb_confirmes if stats else 0,
        taux_acceptation=stats.taux_acceptation if stats else 0,
        taux_confirmation=stats.taux_confirmation if stats else 0,
    )


@router.post("/campagne", response_model=CampagneResponse)
async def create_campagne(
    department: DepartmentDep,
    campagne: CampagneCreate,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Create a new recruitment campaign."""
    existing = recrutement_crud.get_campagne(db, department, campagne.annee)
    if existing:
        raise HTTPException(status_code=400, detail=f"Campagne {campagne.annee} existe déjà")
    
    db_campagne = recrutement_crud.create_campagne(db, department, campagne)
    return await get_campagne(department, db_campagne.annee, db)


@router.put("/campagne/{annee}", response_model=CampagneResponse)
async def update_campagne(
    department: DepartmentDep,
    annee: int,
    campagne: CampagneUpdate,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Update a campaign."""
    db_campagne = recrutement_crud.update_campagne(db, department, annee, campagne)
    if not db_campagne:
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    return await get_campagne(department, annee, db)


@router.delete("/campagne/{annee}")
async def delete_campagne(
    department: DepartmentDep,
    annee: int,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Delete a campaign and all its candidates."""
    if not recrutement_crud.delete_campagne(db, department, annee):
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    return {"message": f"Campagne {annee} supprimée"}


# ==================== CANDIDATS ====================

@router.get("/campagne/{annee}/candidats", response_model=list[CandidatResponse])
async def list_candidats(
    department: DepartmentDep,
    annee: int,
    user: UserDB = Depends(require_view_recrutement),
    statut: Optional[str] = Query(None, pattern="^(en_attente|propose|accepte|refuse|confirme|desiste)$"),
    type_bac: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    """List candidates for a campaign."""
    campagne = recrutement_crud.get_campagne(db, department, annee)
    if not campagne:
        raise HTTPException(status_code=404, detail=f"Campagne {annee} non trouvée")
    
    candidats = recrutement_crud.get_candidats(
        db, campagne.id,
        statut=statut,
        type_bac=type_bac,
        skip=skip,
        limit=limit
    )
    
    return [CandidatResponse.model_validate(c) for c in candidats]


@router.post("/campagne/{annee}/candidat", response_model=CandidatResponse)
async def create_candidat(
    department: DepartmentDep,
    annee: int,
    candidat: CandidatCreate,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Add a candidate to a campaign."""
    campagne = recrutement_crud.get_or_create_campagne(db, department, annee)
    db_candidat = recrutement_crud.create_candidat(db, campagne.id, candidat)
    return CandidatResponse.model_validate(db_candidat)


@router.post("/campagne/{annee}/candidats/bulk", response_model=dict)
async def create_candidats_bulk(
    department: DepartmentDep,
    annee: int,
    data: CandidatBulkCreate,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Add multiple candidates to a campaign."""
    campagne = recrutement_crud.get_or_create_campagne(db, department, annee)
    candidats = recrutement_crud.create_candidats_bulk(db, campagne.id, data.candidats)
    return {"message": f"{len(candidats)} candidats créés", "count": len(candidats)}


@router.get("/candidat/{candidat_id}", response_model=CandidatResponse)
async def get_candidat(
    department: DepartmentDep,
    candidat_id: int,
    user: UserDB = Depends(require_view_recrutement),
    db: Session = Depends(get_db),
):
    """Get a specific candidate."""
    candidat = recrutement_crud.get_candidat(db, candidat_id)
    if not candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return CandidatResponse.model_validate(candidat)


@router.put("/candidat/{candidat_id}", response_model=CandidatResponse)
async def update_candidat(
    department: DepartmentDep,
    candidat_id: int,
    candidat: CandidatUpdate,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Update a candidate."""
    db_candidat = recrutement_crud.update_candidat(db, candidat_id, candidat)
    if not db_candidat:
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return CandidatResponse.model_validate(db_candidat)


@router.delete("/candidat/{candidat_id}")
async def delete_candidat(
    department: DepartmentDep,
    candidat_id: int,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """Delete a candidate."""
    if not recrutement_crud.delete_candidat(db, candidat_id):
        raise HTTPException(status_code=404, detail="Candidat non trouvé")
    return {"message": "Candidat supprimé"}


# ==================== IMPORT ====================

@router.post("/import/csv", response_model=ImportParcoursupResult)
async def import_parcoursup_csv(
    department: DepartmentDep,
    user: UserDB = Depends(require_import),
    file: UploadFile = File(..., description="Parcoursup CSV export file"),
    annee: int = Query(..., description="Année de recrutement"),
    db: Session = Depends(get_db),
):
    """
    Import Parcoursup data from CSV file.
    
    Accepts standard Parcoursup export format with ; separator.
    """
    if not file.filename.endswith((".csv", ".CSV")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV"
        )
    
    content = await file.read()
    result = recrutement_crud.import_parcoursup_from_csv(db, department, content, annee)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


@router.post("/import/excel", response_model=ImportParcoursupResult)
async def import_parcoursup_excel(
    department: DepartmentDep,
    user: UserDB = Depends(require_import),
    file: UploadFile = File(..., description="Parcoursup Excel file"),
    annee: int = Query(..., description="Année de recrutement"),
    db: Session = Depends(get_db),
):
    """
    Import Parcoursup data from Excel file.
    """
    if not file.filename.endswith((".xlsx", ".xls", ".XLSX", ".XLS")):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format Excel (.xlsx ou .xls)"
        )
    
    content = await file.read()
    result = recrutement_crud.import_parcoursup_from_excel(db, department, content, annee)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return result


# ==================== STATISTICS ====================

@router.post("/stats/{annee}", response_model=ParcoursupStats)
async def save_stats_direct(
    department: DepartmentDep,
    annee: int,
    stats_input: ParcoursupStatsInput,
    user: UserDB = Depends(require_edit_recrutement),
    db: Session = Depends(get_db),
):
    """
    Save Parcoursup statistics directly without creating individual candidates.
    This is useful for quick entry of aggregate data.
    """
    recrutement_crud.save_direct_stats(
        db, 
        department,
        annee,
        nb_voeux=stats_input.nb_voeux,
        nb_acceptes=stats_input.nb_acceptes,
        nb_confirmes=stats_input.nb_confirmes,
        nb_refuses=stats_input.nb_refuses,
        nb_desistes=stats_input.nb_desistes,
        par_type_bac=stats_input.par_type_bac,
        par_mention=stats_input.par_mention,
        par_origine=stats_input.par_origine,
        par_lycees=stats_input.par_lycees,
    )
    
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    return stats


@router.get("/stats/{annee}", response_model=ParcoursupStats)
async def get_stats(
    department: DepartmentDep,
    annee: int,
    user: UserDB = Depends(require_view_recrutement),
    db: Session = Depends(get_db),
):
    """Get Parcoursup statistics for a year."""
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Pas de données pour {annee}")
    return stats


@router.get("/evolution", response_model=dict)
async def get_evolution(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    limit: int = Query(5, le=10),
    db: Session = Depends(get_db),
):
    """Get recruitment evolution over years."""
    return recrutement_crud.get_evolution_recrutement(db, department, limit=limit)


# ==================== INDICATORS (pour dashboard) ====================

@router.get("/indicators", response_model=RecrutementIndicators)
async def get_recrutement_indicators(
    department: DepartmentDep,
    user: UserDB = Depends(require_view_recrutement),
    annee: Optional[int] = Query(None, description="Année de recrutement"),
    db: Session = Depends(get_db),
):
    """
    Get recruitment indicators for dashboard.
    Returns data from database or empty/default if no data.
    Falls back to the latest available year if current year has no data.
    """
    if annee is None:
        annee = date.today().year
    
    stats = recrutement_crud.get_parcoursup_stats(db, department, annee)
    
    # If no stats for current year, try to get the latest available
    if not stats or stats.nb_voeux == 0:
        latest_campagne = db.query(CampagneRecrutement).filter(
            CampagneRecrutement.department == department
        ).order_by(CampagneRecrutement.annee.desc()).first()
        if latest_campagne:
            stats = recrutement_crud.get_parcoursup_stats(db, department, latest_campagne.annee)
            if stats:
                annee = latest_campagne.annee
    
    if not stats or stats.nb_voeux == 0:
        # Return empty indicators
        return RecrutementIndicators(
            annee_courante=annee,
            total_candidats=0,
            candidats_acceptes=0,
            candidats_confirmes=0,
            taux_acceptation=0,
            taux_confirmation=0,
            par_type_bac={},
            par_origine={},
            par_mention={},
            evolution=[],
            top_lycees=[],
        )
    
    # Get evolution data
    evolution_data = recrutement_crud.get_evolution_recrutement(db, department)
    evolution = []
    for i, year in enumerate(evolution_data.get("annees", [])):
        evolution.append(VoeuStats(
            annee=year,
            nb_voeux=evolution_data.get("nb_voeux", [])[i] if i < len(evolution_data.get("nb_voeux", [])) else 0,
            nb_acceptes=0,  # Not tracked in evolution
            nb_confirmes=evolution_data.get("nb_confirmes", [])[i] if i < len(evolution_data.get("nb_confirmes", [])) else 0,
            nb_refuses=0,
            nb_desistes=0,
        ))
    
    # Convert top_lycees to LyceeStats
    top_lycees = [
        LyceeStats(lycee=l["lycee"], count=l["count"])
        for l in stats.top_lycees
    ]
    
    return RecrutementIndicators(
        annee_courante=annee,
        total_candidats=stats.nb_voeux,
        candidats_acceptes=stats.nb_acceptes,
        candidats_confirmes=stats.nb_confirmes,
        taux_acceptation=stats.taux_acceptation,
        taux_confirmation=stats.taux_confirmation,
        par_type_bac=stats.par_type_bac,
        par_origine=stats.par_origine,
        par_mention=stats.par_mention,
        evolution=evolution,
        top_lycees=top_lycees,
    )

```
---
## File: backend/app/api/routes/scolarite.py

```py
"""Scolarité API routes."""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional
import logging

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

```
---
## File: backend/app/api/routes/upload.py

```py
"""File upload routes."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import os
from datetime import datetime

from app.api.deps import DepartmentDep
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/file")
async def upload_file(
    department: DepartmentDep,
    file: UploadFile = File(..., description="File to upload"),
    type: str = Form(..., description="Type of data: budget, edt, parcoursup, etudiants, notes, other"),
    description: Optional[str] = Form(None, description="File description"),
):
    """
    Upload a data file.
    
    Supported types:
    - budget: Excel file with budget data
    - edt: Excel file with schedule data
    - parcoursup: CSV file with Parcoursup export
    - etudiants: CSV/Excel file with student list
    - notes: CSV/Excel file with grades
    - other: Any other file
    """
    # Validate file type
    allowed_extensions = {
        "budget": [".xlsx", ".xls", ".csv"],
        "edt": [".xlsx", ".xls", ".csv"],
        "parcoursup": [".csv"],
        "etudiants": [".csv", ".xlsx", ".xls"],
        "notes": [".csv", ".xlsx", ".xls"],
        "other": [".xlsx", ".xls", ".csv", ".pdf"],
    }
    
    if type not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Type inconnu: {type}. Types acceptés: {list(allowed_extensions.keys())}"
        )
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions[type]:
        raise HTTPException(
            status_code=400,
            detail=f"Extension {ext} non acceptée pour le type {type}. Extensions acceptées: {allowed_extensions[type]}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Taille max: {settings.max_upload_size / 1024 / 1024}MB"
        )
    
    # Create upload directory if needed (scoped by department)
    upload_dir = os.path.join(settings.upload_dir, department, type)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, safe_filename)
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(content)
    
    return {
        "success": True,
        "filename": safe_filename,
        "type": type,
        "department": department,
        "size": len(content),
        "path": filepath,
    }


@router.get("/files")
async def list_uploaded_files(
    department: DepartmentDep,
    type: Optional[str] = None,
):
    """
    List uploaded files for a department.
    """
    files = []
    base_dir = os.path.join(settings.upload_dir, department)
    
    if not os.path.exists(base_dir):
        return {"files": []}
    
    types_to_scan = [type] if type else os.listdir(base_dir)
    
    for data_type in types_to_scan:
        type_dir = os.path.join(base_dir, data_type)
        if os.path.isdir(type_dir):
            for filename in os.listdir(type_dir):
                filepath = os.path.join(type_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "type": data_type,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
    
    return {"files": sorted(files, key=lambda x: x["modified"], reverse=True)}


@router.delete("/file/{type}/{filename}")
async def delete_file(department: DepartmentDep, type: str, filename: str):
    """
    Delete an uploaded file.
    """
    filepath = os.path.join(settings.upload_dir, department, type, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    try:
        os.remove(filepath)
        return {"success": True, "message": f"Fichier {filename} supprimé"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@router.get("/download/{type}/{filename}")
async def download_file(department: DepartmentDep, type: str, filename: str):
    """
    Download an uploaded file.
    """
    from fastapi.responses import FileResponse
    
    filepath = os.path.join(settings.upload_dir, department, type, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type='application/octet-stream'
    )

```
---
## File: backend/app/config.py

```py
"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Dept Dashboard API"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # API
    api_prefix: str = "/api"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # ScoDoc Configuration
    scodoc_base_url: Optional[str] = None
    scodoc_username: Optional[str] = None
    scodoc_password: Optional[str] = None
    scodoc_department: Optional[str] = None
    
    # Database
    database_url: Optional[str] = None  # If None, uses SQLite
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    cache_enabled: bool = True
    
    # Cache TTL (en secondes)
    cache_ttl_scolarite: int = 3600      # 1 heure
    cache_ttl_recrutement: int = 86400   # 24 heures
    cache_ttl_budget: int = 86400        # 24 heures
    cache_ttl_edt: int = 3600            # 1 heure
    
    # JWT Auth
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 hours
    
    # CAS Configuration
    cas_server_url: str = "https://sso.univ-artois.fr/cas"
    cas_service_url: str = "http://localhost:8000/api/auth/cas/callback"
    cas_use_mock: bool = True  # Set to False in production
    
    # Frontend URL (for redirects)
    frontend_url: str = "http://localhost:5173"
    
    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is changed in production."""
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        allow_insecure = os.getenv('ALLOW_INSECURE', 'false').lower() == 'true'
        if not debug and not allow_insecure:
            if v == "your-secret-key-change-in-production":
                raise ValueError(
                    "SECRET_KEY must be changed in production! "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            if len(v) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
        return v
    
    @field_validator('cas_use_mock')
    @classmethod
    def validate_cas_mock(cls, v: bool) -> bool:
        """Warn if CAS mock is enabled in production."""
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        allow_insecure = os.getenv('ALLOW_INSECURE', 'false').lower() == 'true'
        if not debug and not allow_insecure and v:
            raise ValueError(
                "CAS_USE_MOCK must be False in production! "
                "Set ALLOW_INSECURE=true for local Docker testing."
            )
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

```
---
## File: backend/app/database.py

```py
"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from app.config import get_settings

settings = get_settings()

# Database configuration
if settings.database_url:
    # Production: Use PostgreSQL or other database from DATABASE_URL
    DATABASE_URL = settings.database_url
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=5,
        max_overflow=10,
        echo=settings.debug,
    )
else:
    # Development: Use SQLite
    DATABASE_DIR = Path(__file__).parent.parent / "data"
    DATABASE_DIR.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///{DATABASE_DIR}/dashboard.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite
        echo=settings.debug,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from app.models import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)

```
---
## File: backend/app/main.py

```py
"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import get_settings
from app.api.routes import scolarite, recrutement, budget, edt, upload, admin
from app.api.routes import budget_admin, recrutement_admin, auth, users
from app.api.routes import alertes, indicateurs
from app.services import cache, scheduler
from app.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    init_db()  # Initialize database tables
    await cache.connect()
    if settings.cache_enabled:
        scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()
    await cache.disconnect()


# OpenAPI customization
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="""
## API Dashboard Département

API d'agrégation de données pour le dashboard du département d'enseignement.

### Sources de données
- **ScoDoc** : Données de scolarité (étudiants, notes, absences)
- **Parcoursup** : Données de recrutement (candidatures, admissions)
- **Excel/CSV** : Données budget et emploi du temps

### Fonctionnalités
- 📊 Indicateurs agrégés par domaine (Scolarité, Recrutement, Budget, EDT)
- 🔄 Cache Redis avec refresh automatique
- 📁 Import de fichiers Excel/CSV
- 📈 Évolutions historiques

### Authentification
L'API utilise des tokens JWT pour l'authentification (en développement).

### Cache
Les données sont mises en cache avec différents TTL :
- Scolarité : 1 heure
- Recrutement : 24 heures
- Budget : 24 heures
- EDT : 1 heure

Utilisez le paramètre `?refresh=true` pour forcer un rafraîchissement du cache.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Scolarité",
                "description": "Gestion des données de scolarité : étudiants, notes, réussite, absences",
            },
            {
                "name": "Recrutement",
                "description": "Données Parcoursup : candidatures, admissions, origines des candidats",
            },
            {
                "name": "Budget",
                "description": "Suivi budgétaire : allocations, dépenses, taux d'exécution",
            },
            {
                "name": "Alertes étudiants",
                "description": "Alertes, suivi individuel et détection précoce des difficultés",
            },
            {
                "name": "Indicateurs cohorte",
                "description": "Statistiques avancées de cohorte, analyses par type de bac, comparaisons interannuelles",
            },
            {
                "name": "EDT",
                "description": "Emploi du temps : charges enseignants, occupation salles, heures",
            },
            {
                "name": "Upload",
                "description": "Import de fichiers Excel et CSV",
            },
            {
                "name": "Administration",
                "description": "Gestion des sources de données, cache, jobs et paramètres système",
            },
        ],
    )
    
    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "Support API",
        "email": "support@departement.fr",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    # Add servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Serveur de développement"},
        {"url": "https://api.departement.fr", "description": "Serveur de production"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API d'agrégation pour le dashboard du département",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.openapi = custom_openapi

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with department prefix
# Department-scoped routes: /api/{department}/...
app.include_router(
    scolarite.router,
    prefix=f"{settings.api_prefix}/{{department}}/scolarite",
    tags=["Scolarité"],
)
app.include_router(
    recrutement.router,
    prefix=f"{settings.api_prefix}/{{department}}/recrutement",
    tags=["Recrutement"],
)
app.include_router(
    budget.router,
    prefix=f"{settings.api_prefix}/{{department}}/budget",
    tags=["Budget"],
)
app.include_router(
    edt.router,
    prefix=f"{settings.api_prefix}/{{department}}/edt",
    tags=["EDT"],
)
app.include_router(
    upload.router,
    prefix=f"{settings.api_prefix}/{{department}}/upload",
    tags=["Upload"],
)

# Alertes et suivi individuel
app.include_router(
    alertes.router,
    prefix=f"{settings.api_prefix}/{{department}}",
    tags=["Alertes étudiants"],
)

# Indicateurs de cohorte et statistiques avancées
app.include_router(
    indicateurs.router,
    prefix=f"{settings.api_prefix}/{{department}}",
    tags=["Indicateurs cohorte"],
)

# Department-scoped admin routes for budget and recrutement
app.include_router(
    budget_admin.router,
    prefix=f"{settings.api_prefix}/{{department}}/admin/budget",
    tags=["Admin Budget"],
)
app.include_router(
    recrutement_admin.router,
    prefix=f"{settings.api_prefix}/{{department}}/admin/recrutement",
    tags=["Admin Recrutement"],
)

# Global admin routes (not department-scoped): sources, settings, cache, jobs, logs
app.include_router(
    admin.router,
    prefix=f"{settings.api_prefix}/admin",
    tags=["Administration"],
)

# Authentication routes
app.include_router(
    auth.router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["Authentication"],
)

# User management routes (admin)
app.include_router(
    users.router,
    prefix=f"{settings.api_prefix}/admin/users",
    tags=["User Management"],
)


@app.get("/", tags=["Health"], summary="Root endpoint")
async def root():
    """
    Root endpoint - retourne les informations de base de l'API.
    
    Utilisé pour vérifier que l'API est accessible.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/api/departments", tags=["Health"], summary="Liste des départements")
async def get_departments():
    """
    Liste des départements disponibles.
    
    Retourne la liste des codes de départements supportés.
    """
    return {
        "departments": ["RT", "GEII", "GCCD", "GMP", "QLIO", "CHIMIE"],
        "default": "RT",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """
    Endpoint de santé détaillé.
    
    Retourne:
    - Status de l'API
    - État du cache Redis
    - Liste des jobs planifiés
    """
    cache_stats = await cache.get_stats()
    return {
        "status": "healthy",
        "cache": cache_stats,
        "scheduler_jobs": scheduler.get_jobs() if settings.cache_enabled else [],
    }


```
---
## File: backend/app/seeds.py

```py
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

```
---
