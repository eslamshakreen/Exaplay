"""Tests for ExaPlay status and metadata endpoints.

Tests the status, version, and related endpoints for monitoring
ExaPlay server state and information.
"""

import pytest
from httpx import AsyncClient

from app.tests.conftest import APITestHelper


class TestStatusEndpoints:
    """Test cases for status monitoring endpoints."""
    
    async def test_get_version_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ) -> None:
        """Test successful version retrieval."""
        response = await async_client.get("/version", headers=auth_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "exaplayVersion" in data
        assert isinstance(data["exaplayVersion"], str)
        assert len(data["exaplayVersion"]) > 0
        
        # Mock server should return specific version
        assert data["exaplayVersion"] == "2.21.0.0"
    
    async def test_get_version_requires_auth(
        self,
        async_client: AsyncClient,
        no_auth_headers: dict
    ) -> None:
        """Test that version endpoint requires authentication."""
        response = await async_client.get("/version", headers=no_auth_headers)
        
        assert response.status_code == 401
        
        data = response.json()
        assert "error" in data
        assert "traceId" in data
    
    async def test_get_composition_status_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test successful composition status retrieval."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.get(
            f"/compositions/{comp_name}/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "state" in data
        assert "time" in data
        assert "frame" in data
        assert "clipIndex" in data
        assert "duration" in data
        
        # Validate data types
        assert data["state"] in ["stopped", "playing", "paused"]
        assert isinstance(data["time"], (int, float))
        assert isinstance(data["frame"], int)
        assert isinstance(data["clipIndex"], int)
        assert isinstance(data["duration"], (int, float))
        
        # Initial state should be stopped
        assert data["state"] == "stopped"
        assert data["time"] == 0.0
        assert data["frame"] == 0
    
    async def test_get_status_after_play(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test status changes after playing composition."""
        comp_name = sample_compositions["generic"]
        
        # Get initial status
        initial_status = await api_helper.get_status(comp_name)
        assert initial_status["state"] == "stopped"
        
        # Play composition
        await api_helper.play_composition(comp_name)
        
        # Get status after play
        playing_status = await api_helper.get_status(comp_name)
        assert playing_status["state"] == "playing"
        
        # State should have changed but other fields should be consistent
        assert playing_status["clipIndex"] == initial_status["clipIndex"]
        assert playing_status["duration"] == initial_status["duration"]
    
    async def test_get_status_cuelist_composition(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test status for cuelist composition shows clip index."""
        comp_name = sample_compositions["cuelist"]
        
        status = await api_helper.get_status(comp_name)
        
        # Cuelist should have valid clip index (1-based)
        assert status["clipIndex"] >= 1
        assert status["duration"] > 0
    
    async def test_get_status_timeline_composition(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test status for timeline composition."""
        comp_name = sample_compositions["timeline"]
        
        status = await api_helper.get_status(comp_name)
        
        # Timeline may have -1 clip index (no clips) or cue index
        assert isinstance(status["clipIndex"], int)
        assert status["duration"] > 0
    
    async def test_status_state_transitions(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test all status state transitions."""
        comp_name = sample_compositions["generic"]
        
        # Initial: stopped
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "stopped"
        
        # Play: stopped -> playing
        await api_helper.play_composition(comp_name)
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "playing"
        
        # Pause: playing -> paused
        await api_helper.client.post(
            f"/compositions/{comp_name}/pause",
            headers=api_helper.auth_headers
        )
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "paused"
        
        # Stop: paused -> stopped
        await api_helper.client.post(
            f"/compositions/{comp_name}/stop",
            headers=api_helper.auth_headers
        )
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "stopped"
        assert status["time"] == 0.0  # Time should reset
        assert status["frame"] == 0   # Frame should reset
    
    async def test_get_status_nonexistent_composition(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ) -> None:
        """Test status for non-existent composition creates it."""
        nonexistent_comp = "nonexistent_comp_12345"
        
        response = await async_client.get(
            f"/compositions/{nonexistent_comp}/status",
            headers=auth_headers
        )
        
        # Mock server creates new compositions on demand
        assert response.status_code == 200
        
        data = response.json()
        assert data["state"] == "stopped"
        assert data["time"] == 0.0
        assert data["frame"] == 0
    
    async def test_status_endpoint_requires_auth(
        self,
        async_client: AsyncClient,
        no_auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test that status endpoint requires authentication."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.get(
            f"/compositions/{comp_name}/status",
            headers=no_auth_headers
        )
        
        assert response.status_code == 401
    
    async def test_status_response_includes_trace_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test that status responses include trace ID."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.get(
            f"/compositions/{comp_name}/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert len(response.headers["X-Trace-ID"]) > 0
    
    async def test_status_data_consistency(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test that status data remains consistent across multiple requests."""
        comp_name = sample_compositions["generic"]
        
        # Get status multiple times
        status1 = await api_helper.get_status(comp_name)
        status2 = await api_helper.get_status(comp_name)
        status3 = await api_helper.get_status(comp_name)
        
        # Should be identical when no commands sent
        assert status1 == status2 == status3
        
        # Duration should be consistent
        assert status1["duration"] == status2["duration"] == status3["duration"]


class TestAPIRootEndpoint:
    """Test cases for the API root information endpoint."""
    
    async def test_api_root_info(self, async_client: AsyncClient) -> None:
        """Test API root endpoint returns correct information."""
        response = await async_client.get("/")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "docs" in data
        assert "openapi" in data
        assert "health" in data
        assert "exaplay" in data
        
        # Check ExaPlay connection info
        exaplay_info = data["exaplay"]
        assert "host" in exaplay_info
        assert "tcp_port" in exaplay_info
        assert "osc_enabled" in exaplay_info
        
        # Validate expected values
        assert data["docs"] == "/docs"
        assert data["openapi"] == "/openapi.json"
        assert data["health"] == "/healthz"
