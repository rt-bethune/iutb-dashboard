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
