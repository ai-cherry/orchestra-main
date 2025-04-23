"""
Tests for the interaction API endpoints of the AI Orchestration System.

This module contains tests for endpoints that process user interactions and commands.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from core.orchestrator.src.main import app


@pytest.fixture
def client():
    """
    Create a TestClient instance for testing API endpoints.
    
    Returns:
        TestClient: A test client instance for the FastAPI app
    """
    return TestClient(app)


@pytest.fixture
def mock_llm_client():
    """
    Create a mock LLM client for testing.
    
    Returns:
        MagicMock: A mock LLM client with predefined responses
    """
    mock_client = MagicMock()
    mock_client.generate_chat_completion.return_value = {
        "content": "This is a test response",
        "model": "test-model",
        "provider": "test-provider",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }
    return mock_client


@pytest.mark.asyncio
async def test_interact_endpoint_valid_request(client, mock_llm_client):
    """
    Test that the interact endpoint accepts a valid request and returns a response.
    
    The interact endpoint should return a 200 status code and include
    the expected response structure with a 'response' field.
    """
    # Mock the dependencies
    with patch('core.orchestrator.src.api.dependencies.llm.get_llm_client', return_value=mock_llm_client):
        # Create a valid request body
        interact_request = {
            "text": "Hello, how are you?"
        }
        
        # Make POST request to interact endpoint
        response = client.post("/api/interact", json=interact_request)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify response structure
        response_json = response.json()
        assert "response" in response_json
        assert "persona" in response_json
        
        # Optional: Verify response matches mock
        assert response_json["response"] == "This is a test response"


@pytest.mark.asyncio
async def test_interact_endpoint_invalid_request(client):
    """
    Test that the interact endpoint rejects an invalid request.
    
    The interact endpoint should return a 422 status code when the
    request body is missing required fields or has invalid types.
    """
    # Create an invalid request (missing required text field)
    invalid_request = {}
    
    # Make POST request to interact endpoint
    response = client.post("/api/interact", json=invalid_request)
    
    # Verify response status is 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Verify error details are included
    response_json = response.json()
    assert "detail" in response_json


def test_command_endpoint_valid_request(client):
    """
    Test that the command endpoint accepts a valid request and returns success.
    
    The command endpoint should return a 200 status code and include
    the expected response structure with a 'response' field.
    """
    # Create a valid request body
    command_request = {
        "input_text": "Test command"
    }
    
    # Make POST request to command endpoint
    response = client.post("/api/command", json=command_request)
    
    # Verify response
    assert response.status_code == 200
    
    # Verify response structure
    response_json = response.json()
    assert "response" in response_json
    assert "persona_used" in response_json
    
    # Optional: Verify response content matches expected format
    assert response_json["response"] == f"Received command: {command_request['input_text']}"


def test_command_endpoint_invalid_request(client):
    """
    Test that the command endpoint rejects an invalid request.
    
    The command endpoint should return a 422 status code when the
    request body is missing required fields or has invalid types.
    """
    # Create an invalid request (missing required input_text field)
    invalid_request = {}
    
    # Make POST request to command endpoint
    response = client.post("/api/command", json=invalid_request)
    
    # Verify response status is 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Verify error details are included
    response_json = response.json()
    assert "detail" in response_json
