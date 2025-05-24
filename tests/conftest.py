"""
Pytest configuration for AI Orchestration System.

This module provides fixtures and configuration for pytest tests.
"""

import logging
from unittest.mock import AsyncMock, patch

import pytest

from packages.shared.src.models.base_models import PersonaConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_persona_for_tests():
    """
    Fixture to mock the persona middleware for tests.

    This ensures that all requests in tests have a persona config
    attached to the request state, mimicking the behavior of the
    PersonaMiddleware in the actual application.
    """
    # Set up a default persona for all requests
    default_persona = PersonaConfig(name="Cherry", description="A helpful AI assistant.")

    # Patch the request state in test environment to include active_persona
    with patch(
        "starlette.requests.Request.state",
        new_callable=lambda: type("MockState", (), {"active_persona": default_persona, "_state": {}})(),
    ):
        yield default_persona


@pytest.fixture
def mock_llm_client():
    """
    Create a mock LLM client for testing.

    Returns:
        An AsyncMock that simulates the LLM client's behavior
    """
    # Create mock LLM client
    mock_client = AsyncMock()

    # Mock generate_response to return a simple response
    mock_client.generate_response.return_value = "This is a mock response from the LLM."

    # Mock generate_chat_completion (legacy method)
    mock_client.generate_chat_completion.return_value = {"choices": [{"message": {"content": "Mock response"}}]}

    return mock_client
