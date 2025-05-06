"""
Tests for the personas API endpoints of the AI Orchestration System.

This module contains tests for endpoints that manage and interact with personas.
"""

import pytest
from fastapi.testclient import TestClient
from unittest import mock

from core.orchestrator.src.main import app
from packages.shared.src.models.core_models import PersonaConfig


@pytest.fixture
def client():
    """
    Create a TestClient instance for testing API endpoints.
    
    Returns:
        TestClient: A test client instance for the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
def mock_persona_configs():
    """
    Create mock persona configurations for testing.
    
    Returns:
        dict: A dictionary mapping persona names to their configurations
    """
    personas = {
        "cherry": PersonaConfig(
            name="Cherry",
            age=35,
            background="AI assistant",
            traits={"helpful": 90},
            interaction_style="friendly"
        ),
        "sophia": PersonaConfig(
            name="Sophia",
            age=28,
            background="Data scientist",
            traits={"analytical": 95},
            interaction_style="precise"
        ),
        "gordon": PersonaConfig(
            name="Gordon Gekko",
            age=50,
            background="Finance",
            traits={"ambitious": 100},
            interaction_style="assertive"
        )
    }
    return personas


@pytest.fixture
def patch_load_all_persona_configs(monkeypatch, mock_persona_configs):
    """
    Patch the load_all_persona_configs function to return mock data.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
        mock_persona_configs: The mock persona configs fixture
    """
    def mock_load_all_persona_configs():
        return mock_persona_configs
    
    monkeypatch.setattr(
        "core.orchestrator.src.api.endpoints.personas.load_all_persona_configs",
        mock_load_all_persona_configs
    )


def test_get_all_personas(client, patch_load_all_persona_configs):
    """
    Test that GET /api/personas returns all persona names.
    
    The endpoint should return a 200 status code and a list containing
    the names of all available personas.
    """
    response = client.get("/api/personas")
    
    assert response.status_code == 200
    
    # The response should be a list of persona names
    personas = response.json()
    assert isinstance(personas, list)
    assert set(personas) == {"cherry", "sophia", "gordon"}


def test_get_persona_valid(client, patch_load_all_persona_configs, mock_persona_configs):
    """
    Test that GET /api/personas/{name} returns the correct persona config.
    
    The endpoint should return a 200 status code and the persona configuration
    when a valid persona name is provided.
    """
    # Test getting the Cherry persona
    response = client.get("/api/personas/cherry")
    
    assert response.status_code == 200
    
    # The response should match the mock config
    persona_config = response.json()
    assert persona_config["name"] == "Cherry"
    assert persona_config["age"] == 35
    assert persona_config["background"] == "AI assistant"
    assert persona_config["traits"] == {"helpful": 90}
    assert persona_config["interaction_style"] == "friendly"


def test_get_persona_invalid(client, patch_load_all_persona_configs):
    """
    Test that GET /api/personas/{name} returns 404 for invalid persona.
    
    The endpoint should return a 404 status code when an invalid
    persona name is provided.
    """
    response = client.get("/api/personas/invalidPersona")
    
    assert response.status_code == 404
    
    # Should include an error detail
    error_detail = response.json().get("detail")
    assert "not found" in error_detail.lower()


def test_update_persona(client, patch_load_all_persona_configs):
    """
    Test that POST /api/personas/{name}/update updates a persona correctly.
    
    The endpoint should return a 200 status code when a valid update
    is submitted for an existing persona.
    """
    # Mock the open function to prevent actual file writes
    with mock.patch("builtins.open", mock.mock_open()), \
         mock.patch("yaml.dump"):
        
        # Create updated persona config
        updated_config = {
            "name": "Cherry",
            "age": 36,  # Updated age
            "background": "Enhanced AI assistant",  # Updated background
            "traits": {"helpful": 95},  # Updated traits
            "interaction_style": "super friendly"  # Updated style
        }
        
        # Send update request
        response = client.post("/api/personas/cherry/update", json=updated_config)
        
        # Verify response
        assert response.status_code == 200
        
        # Should include success message
        response_data = response.json()
        assert response_data["status"] == "success"
        assert "updated successfully" in response_data["message"]
