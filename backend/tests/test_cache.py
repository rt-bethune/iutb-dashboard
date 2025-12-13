"""Tests for cache service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import BaseModel

from app.services.cache import CacheService, CacheKeys


class SampleModel(BaseModel):
    """Sample model for testing."""
    name: str
    value: int


class TestCacheKeys:
    """Test cache key builders."""

    def test_scolarite_indicators_key(self):
        """Test scolarité indicators key generation."""
        assert CacheKeys.scolarite_indicators() == "scolarite:indicators:current"
        assert CacheKeys.scolarite_indicators("2024-2025") == "scolarite:indicators:2024-2025"

    def test_recrutement_indicators_key(self):
        """Test recrutement indicators key generation."""
        assert CacheKeys.recrutement_indicators() == "recrutement:indicators:current"
        assert CacheKeys.recrutement_indicators(2024) == "recrutement:indicators:2024"

    def test_budget_indicators_key(self):
        """Test budget indicators key generation."""
        assert CacheKeys.budget_indicators() == "budget:indicators:current"
        assert CacheKeys.budget_indicators(2024) == "budget:indicators:2024"

    def test_edt_indicators_key(self):
        """Test EDT indicators key generation."""
        assert CacheKeys.edt_indicators() == "edt:indicators:current"
        assert CacheKeys.edt_indicators("2024-2025") == "edt:indicators:2024-2025"

    def test_last_refresh_key(self):
        """Test last refresh timestamp key."""
        assert CacheKeys.last_refresh("scolarite") == "scolarite:last_refresh"
        assert CacheKeys.last_refresh("budget") == "budget:last_refresh"


class TestCacheService:
    """Test cache service."""

    @pytest.fixture
    def cache_service(self):
        """Create cache service instance."""
        return CacheService()

    def test_initial_state(self, cache_service):
        """Test cache service initial state."""
        assert cache_service._client is None
        assert cache_service._connected is False
        assert cache_service.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_disabled(self, cache_service):
        """Test connect when cache is disabled."""
        cache_service.settings.cache_enabled = False
        result = await cache_service.connect()
        assert result is False
        assert cache_service.is_connected is False

    @pytest.mark.asyncio
    async def test_get_not_connected(self, cache_service):
        """Test get when not connected returns None."""
        result = await cache_service.get("test_key", SampleModel)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_not_connected(self, cache_service):
        """Test set when not connected returns False."""
        model = SampleModel(name="test", value=42)
        result = await cache_service.set("test_key", model)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_not_connected(self, cache_service):
        """Test delete when not connected returns False."""
        result = await cache_service.delete("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_stats_not_connected(self, cache_service):
        """Test get_stats when not connected."""
        stats = await cache_service.get_stats()
        assert stats == {"connected": False}

    @pytest.mark.asyncio
    async def test_connect_success(self, cache_service):
        """Test successful connection to Redis."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        
        with patch("redis.asyncio.from_url", return_value=mock_client):
            cache_service.settings.cache_enabled = True
            result = await cache_service.connect()
            assert result is True
            assert cache_service.is_connected is True

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, cache_service):
        """Test cache hit returns deserialized model."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value='{"name": "test", "value": 42}')
        
        cache_service._client = mock_client
        cache_service._connected = True
        
        result = await cache_service.get("test_key", SampleModel)
        assert result is not None
        assert result.name == "test"
        assert result.value == 42

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache_service):
        """Test cache miss returns None."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        
        cache_service._client = mock_client
        cache_service._connected = True
        
        result = await cache_service.get("test_key", SampleModel)
        assert result is None

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache_service):
        """Test setting value with TTL."""
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock()
        
        cache_service._client = mock_client
        cache_service._connected = True
        
        model = SampleModel(name="test", value=42)
        result = await cache_service.set("test_key", model, ttl=3600)
        
        assert result is True
        mock_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_without_ttl(self, cache_service):
        """Test setting value without TTL."""
        mock_client = AsyncMock()
        mock_client.set = AsyncMock()
        
        cache_service._client = mock_client
        cache_service._connected = True
        
        model = SampleModel(name="test", value=42)
        result = await cache_service.set("test_key", model, ttl=None)
        
        assert result is True
        mock_client.set.assert_called_once()
