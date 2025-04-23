"""
Tests for the simplified FastAPI endpoints in recovery mode.

This module tests the basic API functionality for the simplified endpoints.
"""

from fastapi.testclient import TestClient
from core.orchestrator.src.main_simple import app

client = TestClient(app)


def test_health_check():
    """Test that the health endpoint returns the expected response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "I'm alive, Patrick!"}


def test_interact():
    """Test that the interact endpoint accepts input and returns a response."""
    response = client.post("/interact", json={"text": "Hello"})
    assert response.status_code == 200
    assert response.json() == {"response": "Orchestrator is listening..."}