"""
Tests for the health endpoint of the AI Orchestration System API.

This module contains tests for the health check endpoint that provides
information about the operational status of the service.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from core.orchestrator.src.api.endpoints.health import router as health_router


@pytest.fixture
def app():
    """Create a test FastAPI application with the health router mounted."""
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health endpoint."""
    
    def test_health_check(self, client):
        """Test that the health check endpoint returns the expected response."""
        # Make request to the health endpoint
        response = client.get("/health")
        
        # Assert the response status code is 200 OK
        assert response.status_code == 200
        
        # Assert the response body contains the expected JSON data
        assert response.json() == {"status": "healthy"}
    
    def test_health_check_head_method(self, client):
        """Test that the health check endpoint responds to HEAD requests."""
        # Make a HEAD request to the health endpoint
        response = client.head("/health")
        
        # Assert the response status code is 200 OK
        assert response.status_code == 200
        
        # HEAD responses don't have a body, so we just check the status code
