"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from app.models.scolarite import (
    ScolariteIndicators,
    Etudiant,
    ModuleStats,
    SemestreStats
)
from app.models.recrutement import (
    RecrutementIndicators,
    VoeuStats,
    LyceeStats
)
from app.models.budget import (
    BudgetIndicators,
    LigneBudget,
    CategorieDepense
)
from app.models.edt import (
    EDTIndicators,
    ChargeEnseignant,
    OccupationSalle
)


class TestScolariteModels:
    """Test scolarité models."""

    def test_etudiant_valid(self):
        """Test creating a valid student."""
        etudiant = Etudiant(
            id="1",
            nom="Dupont",
            prenom="Jean",
            email="jean.dupont@example.com",
            formation="BUT RT",
            semestre="S1",
            groupe="G1"
        )
        assert etudiant.nom == "Dupont"
        assert etudiant.email == "jean.dupont@example.com"

    def test_etudiant_optional_fields(self):
        """Test student with optional fields."""
        etudiant = Etudiant(
            id="1",
            nom="Dupont",
            prenom="Jean",
            formation="BUT RT",
            semestre="S1"
        )
        assert etudiant.email is None
        assert etudiant.groupe is None

    def test_module_stats_valid(self):
        """Test creating valid module stats."""
        stats = ModuleStats(
            code="R101",
            nom="Initiation aux réseaux",
            moyenne=12.5,
            taux_reussite=0.85,
            nb_etudiants=120,
            ecart_type=2.3,
            note_min=4.0,
            note_max=18.5
        )
        assert stats.code == "R101"
        assert stats.taux_reussite == 0.85

    def test_module_stats_rate_bounds(self):
        """Test module stats rate validation."""
        # Rate should be between 0 and 1
        stats = ModuleStats(
            code="R101",
            nom="Test",
            moyenne=10.0,
            taux_reussite=1.0,  # Maximum valid
            nb_etudiants=50
        )
        assert stats.taux_reussite == 1.0


class TestRecrutementModels:
    """Test recrutement models."""

    def test_voeu_stats_valid(self):
        """Test creating valid voeu stats."""
        voeu = VoeuStats(
            annee=2024,
            voeux=1500,
            confirmes=800,
            admis=150,
            inscrits=140
        )
        assert voeu.annee == 2024
        assert voeu.voeux == 1500

    def test_lycee_stats_valid(self):
        """Test creating valid lycee stats."""
        lycee = LyceeStats(
            lycee="Lycée Victor Hugo",
            count=25
        )
        assert lycee.lycee == "Lycée Victor Hugo"
        assert lycee.count == 25

    def test_recrutement_indicators_valid(self):
        """Test creating valid recrutement indicators."""
        indicators = RecrutementIndicators(
            annee_courante=2024,
            total_candidatures=1500,
            total_admis=150,
            total_inscrits=140,
            taux_remplissage=0.93,
            capacite=150,
            rang_dernier_appele=850,
            evolution=[
                VoeuStats(annee=2023, voeux=1400, confirmes=750, admis=145, inscrits=138),
                VoeuStats(annee=2024, voeux=1500, confirmes=800, admis=150, inscrits=140),
            ],
            par_type_bac={"Général": 100, "Technologique": 50},
            par_origine={"Locale": 80, "Régionale": 60},
            top_lycees=[
                LyceeStats(lycee="Lycée A", count=15),
                LyceeStats(lycee="Lycée B", count=12),
            ]
        )
        assert indicators.total_candidatures == 1500
        assert len(indicators.evolution) == 2


class TestBudgetModels:
    """Test budget models."""

    def test_ligne_budget_valid(self):
        """Test creating valid budget line."""
        ligne = LigneBudget(
            categorie=CategorieDepense.FONCTIONNEMENT,
            libelle="Fournitures",
            budget_initial=10000.0,
            budget_modifie=10500.0,
            engage=8000.0,
            paye=7500.0
        )
        assert ligne.disponible == 2500.0  # 10500 - 8000

    def test_ligne_budget_computed_fields(self):
        """Test budget line computed fields."""
        ligne = LigneBudget(
            categorie=CategorieDepense.INVESTISSEMENT,
            libelle="Équipement",
            budget_initial=50000.0,
            budget_modifie=50000.0,
            engage=25000.0,
            paye=20000.0
        )
        assert ligne.disponible == 25000.0

    def test_categorie_depense_enum(self):
        """Test expense category enum values."""
        assert CategorieDepense.FONCTIONNEMENT.value == "Fonctionnement"
        assert CategorieDepense.INVESTISSEMENT.value == "Investissement"
        assert CategorieDepense.MISSIONS.value == "Missions"


class TestEDTModels:
    """Test EDT models."""

    def test_charge_enseignant_valid(self):
        """Test creating valid teacher workload."""
        charge = ChargeEnseignant(
            enseignant="Jean Dupont",
            statut="MCF",
            service_du=192,
            heures_cm=50.0,
            heures_td=100.0,
            heures_tp=60.0,
            total_heures=210.0,
            heures_complementaires=18.0
        )
        assert charge.enseignant == "Jean Dupont"
        assert charge.total_heures == 210.0

    def test_occupation_salle_valid(self):
        """Test creating valid room occupation."""
        occupation = OccupationSalle(
            salle="B201",
            capacite=30,
            heures_occupees=25.0,
            heures_disponibles=35.0,
            taux_occupation=0.71
        )
        assert occupation.salle == "B201"
        assert occupation.taux_occupation == 0.71

    def test_edt_indicators_valid(self):
        """Test creating valid EDT indicators."""
        indicators = EDTIndicators(
            annee="2024-2025",
            total_heures=5000.0,
            heures_cm=1000.0,
            heures_td=2000.0,
            heures_tp=2000.0,
            total_heures_complementaires=500.0,
            nb_enseignants=25,
            taux_occupation_moyen=0.75,
            charges_enseignants=[],
            occupation_salles=[],
            heures_par_module={}
        )
        assert indicators.total_heures == 5000.0
        assert indicators.nb_enseignants == 25
