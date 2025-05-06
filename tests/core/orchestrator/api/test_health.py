"""
Tests for the health check API endpoints of the AI Orchestration System.

This module contains tests for health check endpoints that monitor system status.
"""

import pytest
from fastapi.testclient import TestClient

from core.orchestrator.src.main import app


@pytest.fixture
def client():
    """
    Create a TestClient instance for testing API endpoints.
    
    Returns:
        TestClient: A test client instance for the FastAPI app
    """
    return TestClient(app)


def test_health_endpoint(client):
    """
    Test that the health endpoint returns success status and correct response.
    
    The health endpoint should return a 200 status code and a JSON response
    with a 'status' field indicating the system is healthy.
    """
    # Make GET request to health endpoint
    response = client.get("/api/health")
    
    # Verify response
    assert response.status_code == 200
    assert response.json() == {"status": "I'm alive, Patrick!"}
