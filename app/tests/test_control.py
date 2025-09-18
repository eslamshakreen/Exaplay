"""Tests for ExaPlay control endpoints.

Tests the play, pause, and stop endpoints for composition control,
including authentication, error handling, and ExaPlay integration.
"""

import pytest
from httpx import AsyncClient

from app.tests.conftest import APITestHelper


class TestControlEndpoints:
    """Test cases for composition control endpoints."""
    
    async def test_play_composition_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test successful play command."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.post(
            f"/compositions/{comp_name}/play",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["sent"] == f"play,{comp_name}"
        assert data["reply"] == "OK"
        assert "X-Trace-ID" in response.headers
    
    async def test_pause_composition_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test successful pause command."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.post(
            f"/compositions/{comp_name}/pause",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["sent"] == f"pause,{comp_name}"
        assert data["reply"] == "OK"
    
    async def test_stop_composition_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test successful stop command."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.post(
            f"/compositions/{comp_name}/stop",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["sent"] == f"stop,{comp_name}"
        assert data["reply"] == "OK"
    
    async def test_play_composition_requires_auth(
        self,
        async_client: AsyncClient,
        no_auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test that play endpoint requires authentication."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.post(
            f"/compositions/{comp_name}/play",
            headers=no_auth_headers
        )
        
        assert response.status_code == 401
        
        data = response.json()
        assert "error" in data
        assert "traceId" in data
    
    async def test_play_composition_invalid_auth(
        self,
        async_client: AsyncClient,
        invalid_auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test play endpoint with invalid authentication."""
        comp_name = sample_compositions["generic"]
        
        response = await async_client.post(
            f"/compositions/{comp_name}/play",
            headers=invalid_auth_headers
        )
        
        assert response.status_code == 403
        
        data = response.json()
        assert "error" in data
        assert "Invalid API key" in data["error"]
        assert "traceId" in data
    
    async def test_play_composition_empty_name(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ) -> None:
        """Test play endpoint with empty composition name."""
        response = await async_client.post(
            "/compositions//play",  # Empty name
            headers=auth_headers
        )
        
        # Should return 404 due to path not matching
        assert response.status_code == 404
    
    async def test_control_workflow_integration(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test complete control workflow: play -> pause -> stop."""
        comp_name = sample_compositions["generic"]
        
        # Start with play
        play_response = await api_helper.play_composition(comp_name)
        assert play_response["reply"] == "OK"
        
        # Check status after play
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "playing"
        
        # Pause the composition
        pause_response = await api_helper.client.post(
            f"/compositions/{comp_name}/pause",
            headers=api_helper.auth_headers
        )
        assert pause_response.status_code == 200
        
        # Check status after pause
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "paused"
        
        # Stop the composition
        stop_response = await api_helper.client.post(
            f"/compositions/{comp_name}/stop",
            headers=api_helper.auth_headers
        )
        assert stop_response.status_code == 200
        
        # Check status after stop
        status = await api_helper.get_status(comp_name)
        assert status["state"] == "stopped"
        assert status["time"] == 0.0
        assert status["frame"] == 0
    
    async def test_control_multiple_compositions(
        self,
        api_helper: APITestHelper,
        sample_compositions: dict
    ) -> None:
        """Test controlling multiple compositions independently."""
        comp1 = sample_compositions["generic"]
        comp2 = sample_compositions["timeline"]
        
        # Play both compositions
        await api_helper.play_composition(comp1)
        await api_helper.play_composition(comp2)
        
        # Check both are playing
        status1 = await api_helper.get_status(comp1)
        status2 = await api_helper.get_status(comp2)
        
        assert status1["state"] == "playing"
        assert status2["state"] == "playing"
        
        # Pause only first composition
        pause_response = await api_helper.client.post(
            f"/compositions/{comp1}/pause",
            headers=api_helper.auth_headers
        )
        assert pause_response.status_code == 200
        
        # Check states - comp1 paused, comp2 still playing
        status1 = await api_helper.get_status(comp1)
        status2 = await api_helper.get_status(comp2)
        
        assert status1["state"] == "paused"
        assert status2["state"] == "playing"
    
    async def test_control_special_characters_in_name(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ) -> None:
        """Test control endpoints with special characters in composition names."""
        # Test with URL-safe special characters
        special_name = "test-composition_123"
        
        response = await async_client.post(
            f"/compositions/{special_name}/play",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["sent"] == f"play,{special_name}"
        assert data["reply"] == "OK"
    
    async def test_control_endpoints_response_time(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_compositions: dict
    ) -> None:
        """Test that control endpoints respond within reasonable time."""
        import time
        
        comp_name = sample_compositions["generic"]
        
        start_time = time.time()
        response = await async_client.post(
            f"/compositions/{comp_name}/play",
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should respond within 1 second (mock server is local)
        response_time = end_time - start_time
        assert response_time < 1.0
