"""
Mock Portkey LLM client implementation for testing and development.

This module provides a mock client that simulates the behavior of the Portkey client
without requiring the actual Portkey package to be installed or configured.
"""

from typing import Dict, List, Any, Optional, Union
import logging
import asyncio

from core.orchestrator.src.config.settings import Settings, get_settings
from .interface import LLMClient

# Configure logging
logger = logging.getLogger(__name__)


class MockPortkeyResponse:
    """Mock response object to simulate Portkey API responses."""

    def __init__(self, content: str) -> None:
        self.content = content


class MockPortkeyChoice:
    """Mock choice object to simulate Portkey API responses."""

    def __init__(self, content: str) -> None:
        self.message = MockPortkeyResponse(content)


class MockPortkeyCompletion:
    """Mock completion object to simulate Portkey API responses."""

    def __init__(self, content: str) -> None:
        self.choices = [MockPortkeyChoice(content)]


class MockPortkeyClientException(Exception):
    """Base exception for Mock Portkey client errors."""

    pass


class MockPortkeyClient(LLMClient):
    """
    Mock Portkey client implementation for testing and development.

    This client simulates the behavior of the Portkey client for the purpose
    of testing and development without requiring the actual Portkey package
    to be installed or configured.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Mock Portkey client.

        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.api_key = settings.PORTKEY_API_KEY or "mock_api_key"
        
        # Set up model fallbacks
        self.model_fallbacks = {
            "gpt-4-turbo": ["gpt-4", "gpt-3.5-turbo"],
            "gpt-4": ["gpt-3.5-turbo"],
            "claude-3-opus": ["claude-3-sonnet", "claude-2"],
            "claude-3-sonnet": ["claude-2", "gpt-3.5-turbo"]
        }
        
        logger.info(
            "Mock Portkey client initialized - This is a test implementation only!"
        )

    async def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        active_persona_name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a mock response based on the provided messages.

        Args:
            model: The model identifier to use for generation
            messages: A list of message dictionaries in the ChatML format
                     (each with 'role' and 'content' keys)
            user_id: Optional user ID for metadata.
            active_persona_name: Optional active persona name for metadata.
            **kwargs: Additional model-specific parameters (e.g., temperature, max_tokens)

        Returns:
            A mock generated text response
        """
        logger.debug(f"Mock generate_response called with model: {model}")
        
        # Extract user message for context
        user_message = "No user message provided"
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "No user message provided")
                break
        
        # Determine which persona is active
        persona = active_persona_name or "Assistant"
        
        # Generate a simple mock response
        await asyncio.sleep(1)  # Simulate API latency
        
        mock_responses = {
            "cherry": f"[Cherry] 💫 As your creative muse, I found your message about '{user_message[:20]}...' quite inspiring! Let me share a playful thought with you...",
            "sophia": f"[Sophia] 📊 Analyzing your message about '{user_message[:20]}...'. Here's my data-backed assessment...",
            "gordon_gekko": f"[Gordon Gekko] 💼 Listen up. Your message about '{user_message[:20]}...' shows potential, but here's what you need to do to win...",
            "default": f"[Assistant] I'm responding to your message about '{user_message[:20]}...' in test mode. This is a mock response from the development environment."
        }

        # For the mock response, return either a specific persona response or the default
        if active_persona_name and active_persona_name.lower() in mock_responses:
            response_key = active_persona_name.lower()
        else:
            response_key = "default"
            
        # Get the response for the selected persona or default
        mock_response = mock_responses.get(response_key, mock_responses["default"])

        logger.info(f"Generated mock response for persona: {persona}")
        return mock_response
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the mock Portkey client.

        Returns:
            Dict with health status information
        """
        return {
            "status": "healthy",
            "api_key_configured": bool(self.api_key),
            "mode": "mock",
            "warning": "This is a mock client for testing only!"
        }
