"""
Tests for persona loader middleware in the AI Orchestration System.

This module tests the middleware that identifies the correct persona based on
request parameters and handles invalid persona names.
"""

import pytest
from unittest import mock
from fastapi import FastAPI, Depends, Request
from starlette.testclient import TestClient

from core.orchestrator.src.api.middleware.persona_loader import (
    get_persona_configs,
    get_active_persona
)
from packages.shared.src.models.base_models import PersonaConfig


@pytest.fixture
def persona_configs():
    """Create sample persona configurations for testing."""
    return {
        "cherry": PersonaConfig(
            name="Cherry",
            description="A friendly assistant",
            prompt_template="You are Cherry, a helpful assistant."
        ),
        "gordon": PersonaConfig(
            name="Gordon",
            description="A technical expert",
            prompt_template="You are Gordon, a technical expert."
        )
    }


@pytest.fixture
def app(persona_configs):
    """Create a test FastAPI application with the persona loader dependency."""
    # Mock the get_persona_configs function
    mock_get_configs = mock.MagicMock(return_value=persona_configs)
    
    app = FastAPI()
    
    # Create test endpoints that use the persona loader
    @app.get("/test-persona")
    async def test_persona(persona: PersonaConfig = Depends(get_active_persona)):
        """Test endpoint that returns the active persona."""
        return {"name": persona.name, "description": persona.description}
    
    @app.get("/test-request-state")
    async def test_request_state(request: Request, persona: PersonaConfig = Depends(get_active_persona)):
        """Test endpoint that returns the persona from request state."""
        return {"state_persona_name": request.state.active_persona.name}
    
    # Replace the get_persona_configs dependency
    app.dependency_overrides[get_persona_configs] = mock_get_configs
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestPersonaLoader:
    """Tests for the persona loader functionality."""
    
    def test_get_active_persona_default(self, client):
        """Test that Cherry is used as the default persona when none is specified."""
        response = client.get("/test-persona")
        assert response.status_code == 200
        assert response.json() == {
            "name": "Cherry",
            "description": "A friendly assistant"
        }
    
    def test_get_active_persona_specified(self, client):
        """Test that the specified persona is used when a valid name is provided."""
        response = client.get("/test-persona?persona=gordon")
        assert response.status_code == 200
        assert response.json() == {
            "name": "Gordon",
            "description": "A technical expert"
        }
    
    def test_get_active_persona_fallback(self, client):
        """Test fallback to Cherry when an invalid persona name is provided."""
        response = client.get("/test-persona?persona=invalid")
        assert response.status_code == 200
        assert response.json() == {
            "name": "Cherry",
            "description": "A friendly assistant"
        }
    
    def test_attach_to_request_state(self, client):
        """Test that the persona is attached to request.state."""
        response = client.get("/test-request-state?persona=gordon")
        assert response.status_code == 200
        assert response.json() == {
            "state_persona_name": "Gordon"
        }
    
    @pytest.mark.parametrize("available_personas,persona_param,expected_error", [
        ({}, "cherry", True),  # No personas available at all
        ({"gordon": PersonaConfig(name="Gordon", description="Technical", prompt_template="Tech")},
         "cherry", True),  # Cherry not available
    ])
    def test_missing_personas(self, app, available_personas, persona_param, expected_error):
        """Test behavior when personas are missing."""
        # Override the get_persona_configs function to return custom available personas
        app.dependency_overrides[get_persona_configs] = lambda: available_personas
        
        client = TestClient(app)
        
        # Make the request
        response = client.get(f"/test-persona?persona={persona_param}")
        
        # If error expected, should return 500 Internal Server Error
        if expected_error:
            assert response.status_code == 500
        else:
            assert response.status_code == 200
    
    def test_direct_call(self, persona_configs):
        """Test direct call to get_active_persona function."""
        # Create mock request with persona parameter
        mock_request = mock.MagicMock()
        mock_request.query_params = {"persona": "gordon"}
        
        # Call the function directly
        persona = get_active_persona(mock_request, persona_configs)
        
        # Assert correct persona is returned
        assert persona.name == "Gordon"
        
        # Assert persona is attached to request state
        assert mock_request.state.active_persona == persona
    
    @mock.patch("core.orchestrator.src.api.middleware.persona_loader.load_persona_configs")
    def test_get_persona_configs(self, mock_load_configs):
        """Test the get_persona_configs function."""
        # Setup mock return value
        mock_configs = {
            "test": PersonaConfig(name="Test", description="Test", prompt_template="Test")
        }
        mock_load_configs.return_value = mock_configs
        
        # Call the function
        configs = get_persona_configs()
        
        # Assert that load_persona_configs was called
        mock_load_configs.assert_called_once()
        
        # Assert the correct configs are returned
        assert configs == mock_configs
