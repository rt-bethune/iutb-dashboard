"""Test configuration and fixtures."""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import app
from app.config import Settings, get_settings


# Override settings for testing
def get_test_settings() -> Settings:
    return Settings(
        app_name="Test Dashboard",
        cache_enabled=False,  # Disable cache for tests
        redis_url="redis://localhost:6379",
    )


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    app.dependency_overrides[get_settings] = get_test_settings
    yield get_test_settings()
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_cache():
    """Mock cache service."""
    with patch("app.services.cache.cache") as mock:
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.is_connected = False
        yield mock
