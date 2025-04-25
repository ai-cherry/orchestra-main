"""
Tests for the interaction endpoints in the AI Orchestration System.

This module contains tests for the user interaction API endpoints,
focusing on the core functionality of the system.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from core.orchestrator.src.main import app
from packages.shared.src.models.base_models import MemoryItem
from tests.mocks.memory_fixtures import mock_memory_manager, get_memory_manager_stub


# Create test client
client = TestClient(app)


@pytest.mark.critical
def test_interact_basic():
    """Test basic interaction with default parameters."""
    # Send a simple interaction request
    response = client.post("/api/interact", json={
        "text": "Hello world",  # Using 'text' field
        # Default user_id="patrick" should be used
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields in response
    assert "response" in data
    assert "persona" in data
    assert data["persona"] == "Cherry"  # Default persona


@pytest.mark.critical
def test_interact_with_custom_user_id():
    """Test interaction with a custom user ID."""
    # Send interaction request with custom user ID
    response = client.post("/api/interact", json={
        "text": "Hello world",
        "user_id": "test_user"
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Check that response is successful
    assert "response" in data
    assert "persona" in data


@pytest.mark.parametrize("persona", ["cherry", "sophia", "gordon_gekko"])
def test_interact_with_different_personas(persona):
    """Test interaction with different personas."""
    # Send interaction request with specific persona
    response = client.post(f"/api/interact?persona={persona}", json={
        "text": "Hello, can you help me?",
        "user_id": "test_user"
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "persona" in data
    # Response should have the capitalized persona name
    assert data["persona"] == persona.capitalize() if persona != "gordon_gekko" else "Gordon Gekko"


@pytest.mark.critical
def test_memory_integration(mock_memory_manager):
    """Test that interaction properly uses memory manager."""
    # Need to patch both LLM and memory manager
    with patch("core.orchestrator.src.api.dependencies.memory.get_memory_manager", 
              return_value=mock_memory_manager), \
         patch("core.orchestrator.src.api.dependencies.llm.get_llm_client", 
              return_value=AsyncMock(generate_response=AsyncMock(return_value="Test response"))):
        
        # Send a request
        response = client.post("/api/interact", json={
            "text": "Test memory integration",
            "user_id": "memory_test_user"
        })
    
    # Verify request was successful
    assert response.status_code == 200
    
    # Verify memory manager was called correctly
    mock_memory_manager.get_conversation_history.assert_called_once()
    mock_memory_manager.add_memory_item.assert_called_once()
    
    # Verify the user_id was passed correctly
    args, kwargs = mock_memory_manager.get_conversation_history.call_args
    assert kwargs["user_id"] == "memory_test_user"


def test_error_handling_missing_persona():
    """Test error handling when an invalid persona is requested."""
    # Request invalid persona
    response = client.post("/api/interact?persona=nonexistent", json={
        "text": "Hello"
    })
    
    # Should still return 200 but with default persona
    assert response.status_code == 200
    data = response.json()
    assert "persona" in data
    assert data["persona"] == "Cherry"  # Falls back to default


def test_error_handling_llm_error(mock_llm_client):
    """Test error handling when LLM client raises an exception."""
    # Patch the LLM client to raise an exception
    mock_llm_client.generate_chat_completion.side_effect = Exception("LLM error")
    
    with patch("core.orchestrator.src.api.dependencies.llm.get_llm_client", 
               return_value=mock_llm_client):
        # Send a request
        response = client.post("/api/interact", json={
            "text": "Trigger an error"
        })
        
        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error" in data["detail"]


@pytest.mark.critical
def test_error_handling_llm_timeout(mock_llm_client):
    """Test error handling when LLM client times out."""
    # Import the specific timeout error
    from core.orchestrator.src.services.llm.exceptions import LLMProviderTimeoutError
    
    # Patch the LLM client to raise a timeout error
    mock_llm_client.generate_chat_completion.side_effect = LLMProviderTimeoutError(
        "Request timed out after 30 seconds"
    )
    
    with patch("core.orchestrator.src.api.dependencies.llm.get_llm_client", 
               return_value=mock_llm_client):
        # Send a request
        response = client.post("/api/interact", json={
            "text": "This request will time out",
            "user_id": "timeout_test_user"
        })
        
        # Should return 503 Service Unavailable for timeout
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "time" in data["detail"].lower()  # Expect "timeout" or "timed out" in the message


@pytest.mark.parametrize("user_id", ["patrick", "test_user_1", "test_user_2"])
def test_multiple_users(user_id):
    """Test interaction with multiple user IDs."""
    response = client.post("/api/interact", json={
        "text": "Hello from different user",
        "user_id": user_id
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "persona" in data


@pytest.mark.critical
def test_maintain_compatibility_no_user_id():
    """Test that endpoints still work without specifying user_id."""
    response = client.post("/api/interact", json={
        "text": "Hello without explicit user_id"
    })
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "persona" in data
