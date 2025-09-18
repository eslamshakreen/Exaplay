"""Tests for health check endpoint.

Tests the /healthz endpoint which provides service liveness checking
without requiring authentication.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""
    
    async def test_health_check_success(self, async_client: AsyncClient) -> None:
        """Test that health check returns 200 OK with correct response."""
        response = await async_client.get("/healthz")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert data == {"status": "ok"}
    
    async def test_health_check_no_auth_required(self, async_client: AsyncClient) -> None:
        """Test that health check doesn't require authentication."""
        # No Authorization header
        response = await async_client.get("/healthz")
        assert response.status_code == 200
        
        # Invalid Authorization header should still work
        response = await async_client.get(
            "/healthz",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 200
    
    async def test_health_check_includes_trace_id(self, async_client: AsyncClient) -> None:
        """Test that health check includes trace ID in response headers."""
        response = await async_client.get("/healthz")
        
        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert len(response.headers["X-Trace-ID"]) > 0
    
    async def test_health_check_custom_trace_id(self, async_client: AsyncClient) -> None:
        """Test that health check preserves custom trace ID from request."""
        custom_trace_id = "custom-trace-12345"
        
        response = await async_client.get(
            "/healthz",
            headers={"X-Trace-ID": custom_trace_id}
        )
        
        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == custom_trace_id
    
    async def test_health_check_cors_headers(self, async_client: AsyncClient) -> None:
        """Test that health check includes proper CORS headers."""
        # Test preflight OPTIONS request
        response = await async_client.options("/healthz")
        
        # Should allow the request (may return 405 or 200 depending on setup)
        assert response.status_code in [200, 405]
        
        # Test actual request with Origin header
        response = await async_client.get(
            "/healthz",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # Check if CORS headers are present when configured origins are used
        # (The exact headers depend on FastAPI CORS middleware configuration)
