"""
Example tests using test mode and mocks for AI Orchestration System.

This module demonstrates how to effectively test the orchestration system
with proper isolation using the test_support utilities.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from core.orchestrator.src.main import app, create_app
from core.orchestrator.src.config.test_support import (
    test_mode,
    register_test_mock,
    clear_test_mocks
)
from core.orchestrator.src.services.memory_service import get_memory_service
from core.orchestrator.src.services.llm.providers import get_llm_provider


# Create properly configured test client with test mode
def get_test_client():
    """Get a FastAPI test client with test mode enabled."""
    with test_mode(enable=True):
        # Create app in test mode
        test_app = create_app(test_mode=True)
        return TestClient(test_app)


@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Automatically clean up test environment after each test."""
    yield
    clear_test_mocks()


@pytest.fixture
def mocked_memory_service():
    """Fixture that provides a mocked memory service."""
    # Create mock memory service
    mock_service = MagicMock()
    
    # Configure mock to return empty history
    mock_service.get_conversation_history.return_value = []
    
    # Configure mock to do nothing when adding memory
    mock_service.add_memory_item.return_value = None
    
    # Register the mock
    register_test_mock("memory_service", mock_service)
    
    return mock_service


@pytest.fixture
def mocked_llm_provider():
    """Fixture that provides a mocked LLM provider."""
    # Create async mock for LLM provider
    mock_provider = AsyncMock()
    
    # Configure mock to return a simple response
    mock_provider.generate_chat_completion.return_value = {
        "content": "This is a test response from the mocked LLM provider",
        "model": "test-model",
        "provider": "test-provider",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20
        }
    }
    
    # Register the mock
    register_test_mock("llm_provider", mock_provider)
    
    return mock_provider


def test_interact_with_mocked_services(mocked_memory_service, mocked_llm_provider):
    """Test interaction with mocked services."""
    # Enter test mode context
    with test_mode(enable=True):
        # Create test client
        client = get_test_client()
        
        # Send interaction request
        response = client.post("/interact", json={
            "user_id": "test_user", 
            "message": "Hello from test"
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify that the mocked memory service was called
        mocked_memory_service.get_conversation_history.assert_called_once()
        assert mocked_memory_service.add_memory_item.call_count >= 1
        
        # If using the LLM provider directly, verify it was called
        # This may not be called if using a different agent
        # mocked_llm_provider.generate_chat_completion.assert_called_once()


def test_override_settings():
    """Test overriding settings in test mode."""
    # Use test_mode with custom overrides
    with test_mode(enable=True, overrides={
        "DEBUG": True,
        "CONVERSATION_HISTORY_LIMIT": 5  # Limit history for testing
    }):
        # Get settings inside test mode
        from core.orchestrator.src.config.config import get_settings
        settings = get_settings()
        
        # Verify overrides are applied
        assert settings.DEBUG is True
        assert settings.CONVERSATION_HISTORY_LIMIT == 5
        assert settings.TEST_MODE is True  # Test mode flag is set


def test_interaction_endpoint_isolation():
    """
    Test interaction endpoint with service isolation.
    
    This test demonstrates a more realistic API test where
    we verify the endpoint behavior without testing the
    underlying components in detail.
    """
    # Create mocks for services
    memory_mock = MagicMock()
    memory_mock.get_conversation_history.return_value = []
    register_test_mock("memory_service", memory_mock)
    
    agent_orchestrator_mock = AsyncMock()
    agent_orchestrator_mock.process_interaction.return_value = {
        "message": "Test response",
        "persona_id": "test-persona",
        "persona_name": "Test Persona",
        "session_id": "test-session-123",
        "interaction_id": "test-interaction-123",
        "timestamp": "2025-04-20T12:00:00Z"
    }
    register_test_mock("agent_orchestrator", agent_orchestrator_mock)
    
    # Test the endpoint
    with test_mode(enable=True):
        client = get_test_client()
        
        response = client.post("/interact", json={
            "user_id": "test_user",
            "message": "Hello",
            "metadata": {"test_key": "test_value"}
        })
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test response"
        assert data["persona_id"] == "test-persona"
        
        # Verify orchestrator was called with correct parameters
        agent_orchestrator_mock.process_interaction.assert_called_once()
        call_args = agent_orchestrator_mock.process_interaction.call_args[1]
        assert call_args["user_input"] == "Hello"
        assert call_args["user_id"] == "test_user"
        assert "test_key" in call_args["context"]["client_metadata"]
