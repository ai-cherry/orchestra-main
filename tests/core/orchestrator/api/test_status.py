"""
Tests for the status API endpoints of the AI Orchestration System.

This module contains tests for endpoints that provide system status information.
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


def test_get_widgets(client):
    """
    Test that GET /api/status/widgets returns the correct widget data.
    
    The endpoint should return a 200 status code and a response that
    matches the hardcoded widget data structure.
    """
    response = client.get("/api/status/widgets")
    
    # Verify status code
    assert response.status_code == 200
    
    # Get the JSON response
    widgets_data = response.json()
    
    # Verify it's a list
    assert isinstance(widgets_data, list)
    
    # Verify each widget has the expected structure
    for widget in widgets_data:
        assert "id" in widget
        assert "name" in widget
        assert "type" in widget
        assert "status" in widget
        
        # Verify data types
        assert isinstance(widget["id"], str)
        assert isinstance(widget["name"], str)
        assert isinstance(widget["type"], str)
        assert isinstance(widget["status"], str)
