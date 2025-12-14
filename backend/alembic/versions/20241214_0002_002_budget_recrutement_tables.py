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
