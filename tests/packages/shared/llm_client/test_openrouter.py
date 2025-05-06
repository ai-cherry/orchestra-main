"""
Tests for OpenRouter LLM client.

This module contains tests for the OpenRouterClient class, which provides 
an interface to the OpenRouter API for generating AI responses.
"""

import pytest
from unittest import mock
import asyncio
from typing import Dict, List, Any

# Import the client class from llm providers module
from core.orchestrator.src.services.llm.providers import OpenRouterProvider, LLMProviderConfig
from core.orchestrator.src.services.llm.exceptions import (
    LLMProviderError,
    LLMProviderAuthenticationError,
    LLMProviderConnectionError,
    LLMProviderRateLimitError,
    LLMProviderInvalidRequestError
)


@pytest.fixture
def provider_config():
    """Create a test configuration for the OpenRouterProvider."""
    return LLMProviderConfig(
        api_key="test-api-key",
        base_url="https://openrouter.ai/api/v1",
        default_model="test-model",
        request_timeout=5,
        max_retries=2,
        retry_delay=0.1,
        retry_max_delay=0.5
    )


@pytest.fixture
def mock_response():
    """Create a mock response similar to what the OpenAI API would return."""
    class MockChoice:
        def __init__(self, text, finish_reason="stop"):
            self.message = mock.MagicMock()
            self.message.content = text
            self.finish_reason = finish_reason
    
    class MockUsage:
        def __init__(self, prompt_tokens=10, completion_tokens=20):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.total_tokens = prompt_tokens + completion_tokens
    
    class MockResponse:
        def __init__(self, text="Test response", model="test-model"):
            self.choices = [MockChoice(text)]
            self.model = model
            self.usage = MockUsage()
    
    return MockResponse()


class TestOpenRouterClient:
    """Tests for the OpenRouterClient class."""
    
    def test_initialization(self, provider_config):
        """Test that the client initializes correctly."""
        # Create client
        provider = OpenRouterProvider(provider_config)
        
        # Assert client is initialized with correct config
        assert provider.config.api_key == "test-api-key"
        assert provider.config.base_url == "https://openrouter.ai/api/v1"
        assert provider.config.default_model == "test-model"
        assert provider.provider_name == "openrouter"
        assert provider.default_model == "test-model"
        assert not provider.is_initialized  # Not initialized until initialize() is called
        
        # Initialize provider
        provider.initialize()
        
        # Now it should be initialized
        assert provider.is_initialized
        
        # Close provider
        provider.close()
        
        # Should be closed now
        assert not provider.is_initialized
    
    @pytest.mark.asyncio
    async def test_generate_completion(self, provider_config, mock_response):
        """Test the generate_completion method."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Mock the chat completions API
        with mock.patch.object(provider._client.chat.completions, 'create', 
                               return_value=mock_response):
            # Call the method
            response = await provider.generate_completion(
                prompt="Test prompt",
                temperature=0.5,
                max_tokens=100
            )
            
            # Assert the response is processed correctly
            assert response["content"] == "Test response"
            assert response["model"] == "test-model"
            assert response["provider"] == "openrouter"
            assert response["usage"]["prompt_tokens"] == 10
            assert response["usage"]["completion_tokens"] == 20
            assert response["usage"]["total_tokens"] == 30
            assert response["finish_reason"] == "stop"
            assert "response_time_ms" in response
    
    @pytest.mark.asyncio
    async def test_generate_chat_completion(self, provider_config, mock_response):
        """Test the generate_chat_completion method."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Mock the chat completions API
        with mock.patch.object(provider._client.chat.completions, 'create', 
                               return_value=mock_response):
            # Call the method
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, world!"}
            ]
            
            response = await provider.generate_chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            # Assert the response is processed correctly
            assert response["content"] == "Test response"
            assert response["model"] == "test-model"
            assert response["provider"] == "openrouter"
            assert response["usage"]["total_tokens"] == 30
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, provider_config):
        """Test handling of authentication errors."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Mock authentication error
        from openai import AuthenticationError
        with mock.patch.object(
            provider._client.chat.completions, 'create', 
            side_effect=AuthenticationError("Invalid API key")
        ):
            # Check that the provider correctly wraps the error
            with pytest.raises(LLMProviderAuthenticationError):
                await provider.generate_chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )
    
    @pytest.mark.asyncio
    async def test_connection_error(self, provider_config):
        """Test handling of connection errors."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Mock connection error
        from openai import APIConnectionError
        with mock.patch.object(
            provider._client.chat.completions, 'create', 
            side_effect=APIConnectionError("Connection failed")
        ):
            # Check that the provider correctly wraps the error
            with pytest.raises(LLMProviderConnectionError):
                await provider.generate_chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, provider_config):
        """Test handling of rate limit errors."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Set retryable errors to exclude rate limit errors to prevent retry attempts
        provider.config.retryable_errors = set()
        
        # Mock rate limit error
        from openai import RateLimitError
        with mock.patch.object(
            provider._client.chat.completions, 'create', 
            side_effect=RateLimitError("Rate limit exceeded")
        ):
            # Check that the provider correctly wraps the error
            with pytest.raises(LLMProviderRateLimitError):
                await provider.generate_chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )
    
    @pytest.mark.asyncio
    async def test_invalid_request_error(self, provider_config):
        """Test handling of invalid request errors."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Test with invalid messages
        with pytest.raises(LLMProviderInvalidRequestError):
            await provider.generate_chat_completion(
                messages=[]  # Empty list is invalid
            )
        
        with pytest.raises(LLMProviderInvalidRequestError):
            await provider.generate_chat_completion(
                messages=[{"invalid": "message format"}]  # Missing role/content
            )
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, provider_config, mock_response):
        """Test that the retry mechanism works correctly."""
        provider = OpenRouterProvider(provider_config)
        provider.initialize()
        
        # Mock a rate limit error that should be retried
        from openai import RateLimitError
        
        # Create a side effect that fails on first call but succeeds on second call
        side_effect = [
            RateLimitError("Rate limit exceeded"),
            mock_response
        ]
        
        with mock.patch.object(
            provider._client.chat.completions, 'create', 
            side_effect=side_effect
        ):
            # Ensure retries for rate limit errors
            provider.config.retryable_errors = {"rate_limit_error"}
            
            # Call should succeed after retry
            response = await provider.generate_chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            # Assert the response after retry is processed correctly
            assert response["content"] == "Test response"
            assert response["provider"] == "openrouter"
