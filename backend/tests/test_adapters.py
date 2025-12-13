"""Tests for adapters."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.adapters.base import BaseAdapter, AdapterConfig
from app.adapters.scodoc import MockScoDocAdapter
from app.adapters.parcoursup import MockParcoursupAdapter, ParcoursupAdapter
from app.adapters.excel import MockExcelAdapter


class TestBaseAdapter:
    """Test base adapter class."""

    def test_adapter_config(self):
        """Test adapter configuration."""
        config = AdapterConfig(
            name="test",
            base_url="https://api.example.com",
            timeout=30
        )
        assert config.name == "test"
        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30


class TestMockScoDocAdapter:
    """Test mock ScoDoc adapter."""

    @pytest.fixture
    def adapter(self):
        return MockScoDocAdapter()

    @pytest.mark.asyncio
    async def test_get_data(self, adapter):
        """Test getting mock data."""
        data = await adapter.get_data()
        assert data.total_etudiants > 0
        assert data.moyenne_generale > 0
        assert len(data.modules_stats) > 0

    @pytest.mark.asyncio
    async def test_get_data_with_year(self, adapter):
        """Test getting data with year filter."""
        data = await adapter.get_data(annee="2024-2025")
        assert data is not None

    def test_mock_data_structure(self, adapter):
        """Test mock data has correct structure."""
        # Verify adapter returns expected fields
        import asyncio
        data = asyncio.get_event_loop().run_until_complete(adapter.get_data())
        
        assert hasattr(data, 'total_etudiants')
        assert hasattr(data, 'moyenne_generale')
        assert hasattr(data, 'taux_reussite_global')
        assert hasattr(data, 'modules_stats')
        assert hasattr(data, 'semestres_stats')


class TestMockParcoursupAdapter:
    """Test mock Parcoursup adapter."""

    @pytest.fixture
    def adapter(self):
        return MockParcoursupAdapter()

    def test_get_mock_data(self, adapter):
        """Test getting mock data."""
        data = adapter.get_mock_data()
        assert data.total_candidatures > 0
        assert data.total_admis > 0
        assert len(data.evolution) > 0
        assert len(data.top_lycees) > 0

    def test_top_lycees_structure(self, adapter):
        """Test top_lycees has correct structure."""
        data = adapter.get_mock_data()
        for lycee in data.top_lycees:
            assert hasattr(lycee, 'lycee')
            assert hasattr(lycee, 'count')
            assert isinstance(lycee.lycee, str)
            assert isinstance(lycee.count, int)


class TestParcoursupAdapter:
    """Test Parcoursup CSV adapter."""

    @pytest.fixture
    def adapter(self):
        return ParcoursupAdapter()

    def test_parse_empty_csv(self, adapter):
        """Test parsing empty CSV raises error."""
        with pytest.raises(Exception):
            adapter.parse_parcoursup_export(b"", 2024)

    def test_parse_invalid_csv(self, adapter):
        """Test parsing invalid CSV."""
        csv_content = b"invalid,csv,data\n1,2,3"
        with pytest.raises(Exception):
            adapter.parse_parcoursup_export(csv_content, 2024)


class TestMockExcelAdapter:
    """Test mock Excel adapter."""

    @pytest.fixture
    def adapter(self):
        return MockExcelAdapter()

    def test_get_mock_budget(self, adapter):
        """Test getting mock budget data."""
        data = adapter.get_mock_budget()
        assert data.budget_total > 0
        assert data.taux_execution >= 0
        assert len(data.par_categorie) > 0

    def test_get_mock_edt(self, adapter):
        """Test getting mock EDT data."""
        data = adapter.get_mock_edt()
        assert data.total_heures > 0
        assert data.nb_enseignants > 0
        assert len(data.charges_enseignants) > 0
        assert len(data.occupation_salles) > 0

    def test_budget_calculations(self, adapter):
        """Test budget calculations are consistent."""
        data = adapter.get_mock_budget()
        
        # Total should match sum of categories
        total_from_categories = sum(
            ligne.budget_initial for ligne in data.par_categorie
        )
        assert abs(data.budget_total - total_from_categories) < 1  # Allow small float diff

    def test_edt_hour_totals(self, adapter):
        """Test EDT hour totals are consistent."""
        data = adapter.get_mock_edt()
        
        # Total should be sum of CM + TD + TP
        expected_total = data.heures_cm + data.heures_td + data.heures_tp
        assert abs(data.total_heures - expected_total) < 1
