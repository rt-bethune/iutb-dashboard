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
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cas_login', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('nom', sa.String(length=100), nullable=True),
        sa.Column('prenom', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cas_login')
    )
    op.create_index(op.f('ix_users_cas_login'), 'users', ['cas_login'], unique=True)

    # Create user_permissions table
    op.create_table(
        'user_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('department', sa.String(length=10), nullable=False),
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
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'department', name='uq_user_department')
    )
    op.create_index(op.f('ix_user_permissions_user_id'), 'user_permissions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_permissions_department'), 'user_permissions', ['department'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_permissions_department'), table_name='user_permissions')
    op.drop_index(op.f('ix_user_permissions_user_id'), table_name='user_permissions')
    op.drop_table('user_permissions')
    op.drop_index(op.f('ix_users_cas_login'), table_name='users')
    op.drop_table('users')
