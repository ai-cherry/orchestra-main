"""
Tests for LLM Provider Error Handling.

This module contains tests for the error handling capabilities
of the LLM providers and agents in the AI Orchestration System.
"""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from core.orchestrator.src.services.llm.providers import OpenRouterProvider, LLMProviderConfig
from core.orchestrator.src.services.llm.exceptions import (
    LLMProviderError,
    LLMProviderAuthenticationError,
    LLMProviderConnectionError,
    LLMProviderRateLimitError,
    LLMProviderInvalidRequestError
)
from core.orchestrator.src.agents.llm_agent import LLMAgent
from core.orchestrator.src.agents.agent_base import AgentContext
from packages.shared.src.models.base_models import PersonaConfig


# Mock persona for testing
TEST_PERSONA = PersonaConfig(
    id="test-persona",
    name="Test Persona",
    description="A persona for testing error handling in LLMs.",
    background="A test persona for error handling",
    interaction_style="Helpful and concise",
    traits={"adaptability": 80, "resilience": 100}
)


class TestLLMProviderErrorHandling:
    """Test error handling in LLM providers."""
    
    @pytest.fixture
    def provider_config(self):
        """Create a test provider configuration."""
        return LLMProviderConfig(
            api_key="test-api-key",
            base_url="https://api.test.com",
            default_model="test-model",
            request_timeout=5,
            max_retries=2
        )
    
    @pytest.mark.asyncio
    @patch("core.orchestrator.src.services.llm.providers.AsyncOpenAI")
    async def test_authentication_error(self, mock_openai, provider_config):
        """Test handling of authentication errors."""
        # Setup mock to raise authentication error
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create error response that mimics OpenAI's error format
        auth_error = Exception("Invalid API key")
        mock_client.chat.completions.create.side_effect = auth_error
        
        # Create provider and test
        provider = OpenRouterProvider(provider_config)
        
        with pytest.raises(LLMProviderAuthenticationError):
            await provider.generate_chat_completion(
                messages=[{"role": "user", "content": "Test message"}]
            )
    
    @pytest.mark.asyncio
    @patch("core.orchestrator.src.services.llm.providers.AsyncOpenAI")
    async def test_rate_limit_error(self, mock_openai, provider_config):
        """Test handling of rate limit errors."""
        # Setup mock to raise rate limit error
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Create error response that mimics OpenAI's error format
        rate_limit_error = Exception("Rate limit exceeded")
        mock_client.chat.completions.create.side_effect = rate_limit_error
        
        # Create provider and test
        provider = OpenRouterProvider(provider_config)
        
        with pytest.raises(LLMProviderError):
            await provider.generate_chat_completion(
                messages=[{"role": "user", "content": "Test message"}]
            )


class TestLLMAgentErrorHandling:
    """Test error handling in the LLM agent."""
    
    @pytest.fixture
    def agent_context(self):
        """Create a test agent context."""
        return AgentContext(
            user_input="Test message",
            persona=TEST_PERSONA,
            conversation_history=[],
            metadata={}
        )
    
    @pytest.mark.asyncio
    @patch("core.orchestrator.src.agents.llm_agent.get_llm_provider")
    async def test_provider_authentication_error(self, mock_get_provider, agent_context):
        """Test agent graceful handling of authentication errors."""
        # Setup mock to raise authentication error
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate_chat_completion.side_effect = LLMProviderAuthenticationError("Invalid API key")
        
        # Create agent and test
        agent = LLMAgent()
        response = await agent.process(agent_context)
        
        # Verify response contains error information but still returns something to the user
        assert response.text
        assert response.confidence < 0.5  # Lower confidence for error responses
        assert response.metadata.get("error") == "authentication_error"
        assert response.metadata.get("fallback") is True
    
    @pytest.mark.asyncio
    @patch("core.orchestrator.src.agents.llm_agent.get_llm_provider")
    async def test_provider_connection_error(self, mock_get_provider, agent_context):
        """Test agent graceful handling of connection errors."""
        # Setup mock to raise connection error
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate_chat_completion.side_effect = LLMProviderConnectionError("Connection failed")
        
        # Create agent and test
        agent = LLMAgent()
        response = await agent.process(agent_context)
        
        # Verify response contains error information but still returns something to the user
        assert response.text
        assert response.confidence < 0.5  # Lower confidence for error responses
        assert response.metadata.get("error") == "connection_error"
        assert response.metadata.get("fallback") is True
    
    @pytest.mark.asyncio
    @patch("core.orchestrator.src.agents.llm_agent.get_llm_provider")
    async def test_provider_invalid_request(self, mock_get_provider, agent_context):
        """Test agent graceful handling of invalid request errors."""
        # Setup mock to raise invalid request error
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.generate_chat_completion.side_effect = LLMProviderInvalidRequestError("Invalid request")
        
        # Create agent and test
        agent = LLMAgent()
        response = await agent.process(agent_context)
        
        # Verify response contains error information but still returns something to the user
        assert response.text
        assert response.confidence < 0.5  # Lower confidence for error responses
        assert response.metadata.get("error") == "invalid_request_error"
        assert response.metadata.get("fallback") is True
        
        # Verify persona name is included in the response
        assert TEST_PERSONA.name in response.text
