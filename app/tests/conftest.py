"""Pytest configuration and shared fixtures for ExaPlay API tests.

Provides common test fixtures including mock server, test client,
authentication, and environment setup.
"""

import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Set test environment variables before importing app modules
os.environ.update({
    "API_KEY": "test_api_key_12345678901234567890123456789012",
    "EXAPLAY_HOST": "127.0.0.1",
    "EXAPLAY_TCP_PORT": "17000",
    "EXAPLAY_OSC_ENABLE": "false",
    "LOG_LEVEL": "DEBUG",
    "LOG_FORMAT": "console",
    "CORS_ALLOW_ORIGINS": "http://localhost:3000",
})

from app.main import app
from app.tests.fixtures.mock_exaplay import MockExaPlayServer
from app.settings import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def mock_exaplay_server() -> AsyncGenerator[MockExaPlayServer, None]:
    """Provide a mock ExaPlay server for the entire test session.
    
    Yields:
        MockExaPlayServer: Running mock server instance
    """
    server = MockExaPlayServer(host="127.0.0.1", port=17000)
    await server.start()
    
    # Wait a moment for server to be ready
    await asyncio.sleep(0.1)
    
    try:
        yield server
    finally:
        await server.stop()


@pytest.fixture
def test_client(mock_exaplay_server: MockExaPlayServer) -> TestClient:
    """Provide a FastAPI test client with mock server running.
    
    Args:
        mock_exaplay_server: Mock server fixture
        
    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


@pytest.fixture
async def async_client(mock_exaplay_server: MockExaPlayServer) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing.
    
    Args:
        mock_exaplay_server: Mock server fixture
        
    Yields:
        AsyncClient: Configured async HTTP client
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> dict:
    """Provide authentication headers for API requests.
    
    Returns:
        dict: Headers with Bearer token authentication
    """
    return {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_auth_headers() -> dict:
    """Provide invalid authentication headers for testing auth failures.
    
    Returns:
        dict: Headers with invalid Bearer token
    """
    return {
        "Authorization": "Bearer invalid_token_12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def no_auth_headers() -> dict:
    """Provide headers without authentication for testing auth requirements.
    
    Returns:
        dict: Headers without Authorization
    """
    return {
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_compositions() -> dict:
    """Provide sample composition data for testing.
    
    Returns:
        dict: Sample composition names and expected behaviors
    """
    return {
        "timeline": "timeline1",
        "cuelist": "cuelist1", 
        "generic": "comp1",
        "show": "showA"
    }


@pytest.fixture
def sample_requests() -> dict:
    """Provide sample request payloads for testing.
    
    Returns:
        dict: Sample request bodies for various endpoints
    """
    return {
        "cuetime": {"seconds": 12.5},
        "cue": {"index": 3},
        "volume": {"value": 60},
        "raw_command": {"raw": "get:ver"}
    }


# Test utilities
class APITestHelper:
    """Helper class for common API test operations."""
    
    def __init__(self, client: AsyncClient, auth_headers: dict) -> None:
        """Initialize test helper.
        
        Args:
            client: HTTP client for requests
            auth_headers: Authentication headers
        """
        self.client = client
        self.auth_headers = auth_headers
    
    async def play_composition(self, name: str) -> dict:
        """Play a composition and return response data.
        
        Args:
            name: Composition name
            
        Returns:
            dict: Response JSON data
        """
        response = await self.client.post(
            f"/compositions/{name}/play",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        return response.json()
    
    async def get_status(self, name: str) -> dict:
        """Get composition status and return response data.
        
        Args:
            name: Composition name
            
        Returns:
            dict: Status response data
        """
        response = await self.client.get(
            f"/compositions/{name}/status",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        return response.json()
    
    async def set_volume(self, name: str, volume: int) -> dict:
        """Set composition volume and return response data.
        
        Args:
            name: Composition name
            volume: Volume level (0-100)
            
        Returns:
            dict: Response data
        """
        response = await self.client.post(
            f"/compositions/{name}/volume",
            json={"value": volume},
            headers=self.auth_headers
        )
        assert response.status_code == 200
        return response.json()
    
    async def get_volume(self, name: str) -> int:
        """Get composition volume level.
        
        Args:
            name: Composition name
            
        Returns:
            int: Current volume level
        """
        response = await self.client.get(
            f"/compositions/{name}/volume",
            headers=self.auth_headers
        )
        assert response.status_code == 200
        return response.json()["value"]


@pytest.fixture
async def api_helper(async_client: AsyncClient, auth_headers: dict) -> APITestHelper:
    """Provide API test helper instance.
    
    Args:
        async_client: Async HTTP client
        auth_headers: Authentication headers
        
    Returns:
        APITestHelper: Configured test helper
    """
    return APITestHelper(async_client, auth_headers)
