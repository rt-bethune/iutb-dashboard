"""Tests for API routes."""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        """Test root endpoint returns app info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestScolariteRoutes:
    """Test scolarité API routes."""

    @pytest.mark.asyncio
    async def test_get_indicators(self, client: AsyncClient):
        """Test getting scolarité indicators."""
        response = await client.get("/api/scolarite/indicators")
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_etudiants" in data
        assert "moyenne_generale" in data
        assert "taux_reussite_global" in data
        assert "taux_absenteisme" in data
        assert "modules_stats" in data
        assert "semestres_stats" in data

    @pytest.mark.asyncio
    async def test_get_indicators_with_year(self, client: AsyncClient):
        """Test getting scolarité indicators with year filter."""
        response = await client.get("/api/scolarite/indicators?annee=2024-2025")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_etudiants(self, client: AsyncClient):
        """Test getting students list."""
        response = await client.get("/api/scolarite/etudiants")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "id" in data[0]
            assert "nom" in data[0]
            assert "prenom" in data[0]

    @pytest.mark.asyncio
    async def test_get_etudiants_with_filters(self, client: AsyncClient):
        """Test getting students with filters."""
        response = await client.get("/api/scolarite/etudiants?formation=BUT%20RT&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_get_modules(self, client: AsyncClient):
        """Test getting module statistics."""
        response = await client.get("/api/scolarite/modules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_effectifs(self, client: AsyncClient):
        """Test getting effectifs evolution."""
        response = await client.get("/api/scolarite/effectifs")
        assert response.status_code == 200
        data = response.json()
        assert "evolution" in data
        assert "par_formation" in data

    @pytest.mark.asyncio
    async def test_get_reussite(self, client: AsyncClient):
        """Test getting success rates."""
        response = await client.get("/api/scolarite/reussite")
        assert response.status_code == 200
        data = response.json()
        assert "global" in data
        assert "par_semestre" in data
        assert "par_module" in data


class TestRecrutementRoutes:
    """Test recrutement API routes."""

    @pytest.mark.asyncio
    async def test_get_indicators(self, client: AsyncClient):
        """Test getting recrutement indicators."""
        response = await client.get("/api/recrutement/indicators")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_candidatures" in data
        assert "total_admis" in data
        assert "taux_remplissage" in data
        assert "par_type_bac" in data

    @pytest.mark.asyncio
    async def test_get_evolution(self, client: AsyncClient):
        """Test getting recrutement evolution."""
        response = await client.get("/api/recrutement/evolution")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "annee" in data[0]
            assert "voeux" in data[0]

    @pytest.mark.asyncio
    async def test_get_par_bac(self, client: AsyncClient):
        """Test getting repartition by bac type."""
        response = await client.get("/api/recrutement/par-bac")
        assert response.status_code == 200
        data = response.json()
        assert "repartition" in data

    @pytest.mark.asyncio
    async def test_get_top_lycees(self, client: AsyncClient):
        """Test getting top feeder schools."""
        response = await client.get("/api/recrutement/top-lycees?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


class TestBudgetRoutes:
    """Test budget API routes."""

    @pytest.mark.asyncio
    async def test_get_indicators(self, client: AsyncClient):
        """Test getting budget indicators."""
        response = await client.get("/api/budget/indicators")
        assert response.status_code == 200
        data = response.json()
        
        assert "budget_total" in data
        assert "total_engage" in data
        assert "total_paye" in data
        assert "taux_execution" in data

    @pytest.mark.asyncio
    async def test_get_par_categorie(self, client: AsyncClient):
        """Test getting budget by category."""
        response = await client.get("/api/budget/par-categorie")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data

    @pytest.mark.asyncio
    async def test_get_evolution(self, client: AsyncClient):
        """Test getting budget evolution."""
        response = await client.get("/api/budget/evolution")
        assert response.status_code == 200
        data = response.json()
        assert "evolution_mensuelle" in data

    @pytest.mark.asyncio
    async def test_get_execution(self, client: AsyncClient):
        """Test getting execution rates."""
        response = await client.get("/api/budget/execution")
        assert response.status_code == 200
        data = response.json()
        assert "taux_execution" in data
        assert "taux_engagement" in data


class TestEDTRoutes:
    """Test EDT API routes."""

    @pytest.mark.asyncio
    async def test_get_indicators(self, client: AsyncClient):
        """Test getting EDT indicators."""
        response = await client.get("/api/edt/indicators")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_heures" in data
        assert "heures_cm" in data
        assert "heures_td" in data
        assert "heures_tp" in data

    @pytest.mark.asyncio
    async def test_get_charges(self, client: AsyncClient):
        """Test getting teacher workloads."""
        response = await client.get("/api/edt/charges")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "enseignant" in data[0]
            assert "total_heures" in data[0]

    @pytest.mark.asyncio
    async def test_get_occupation(self, client: AsyncClient):
        """Test getting room occupation."""
        response = await client.get("/api/edt/occupation")
        assert response.status_code == 200
        data = response.json()
        assert "salles" in data
        assert "taux_moyen" in data

    @pytest.mark.asyncio
    async def test_get_repartition(self, client: AsyncClient):
        """Test getting hours distribution."""
        response = await client.get("/api/edt/repartition")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "cm" in data
        assert "td" in data
        assert "tp" in data
