"""
Tests for the OpenRouterClient implementation.

This module contains tests for the OpenRouterClient class, which uses
the OpenAI SDK compatibility layer to interact with OpenRouter.
"""

import pytest
from unittest import mock
import os
import asyncio

from packages.shared.src.llm_client.openrouter_client import OpenRouterClient
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError


@pytest.fixture
def mock_settings():
    """Create a mock settings object with test values."""
    with mock.patch('core.orchestrator.src.config.settings.get_settings') as mock_get_settings:
        mock_settings = mock.Mock()
        mock_settings.OPENROUTER_API_KEY = "test-api-key"
        mock_settings.SITE_URL = "http://test-site.com"
        mock_settings.SITE_TITLE = "Test Site"
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client with predefined responses."""
    mock_client = mock.MagicMock()
    
    # Create a mock response for chat completions
    mock_message = mock.MagicMock()
    mock_message.content = "This is a test response"
    
    mock_choice = mock.MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    
    mock_completion = mock.MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "openai/gpt-3.5-turbo"
    mock_completion.usage.prompt_tokens = 10
    mock_completion.usage.completion_tokens = 20
    mock_completion.usage.total_tokens = 30
    
    # Set up the mock chat completions method
    mock_chat_completions = mock.MagicMock()
    mock_chat_completions.create = mock.AsyncMock(return_value=mock_completion)
    mock_client.chat.completions = mock_chat_completions
    
    return mock_client


class TestOpenRouterClient:
    """Tests for the OpenRouterClient."""
    
    def test_initialization(self, mock_settings):
        """Test client initialization with mock settings."""
        with mock.patch('openai.OpenAI') as mock_openai:
            # Initialize client
            client = OpenRouterClient()
            
            # Verify OpenAI was initialized correctly
            mock_openai.assert_called_once_with(
                base_url="https://openrouter.ai/api/v1",
                api_key="test-api-key",
                timeout=30.0
            )
            
            # Verify headers were set
            assert client.extra_headers["HTTP-Referer"] == "http://test-site.com"
            assert client.extra_headers["X-Title"] == "Test Site"
    
    def test_missing_api_key(self):
        """Test error handling when API key is missing."""
        with mock.patch('core.orchestrator.src.config.settings.get_settings') as mock_get_settings:
            # Create settings with missing API key
            mock_settings = mock.Mock()
            mock_settings.OPENROUTER_API_KEY = None
            mock_get_settings.return_value = mock_settings
            
            # Initialization should raise ValueError
            with pytest.raises(ValueError) as excinfo:
                OpenRouterClient()
            
            assert "OPENROUTER_API_KEY not found" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_settings, mock_openai_client):
        """Test generate_response method with mocked client."""
        with mock.patch.object(OpenAI, '__new__', return_value=mock_openai_client):
            # Initialize client
            client = OpenRouterClient()
            
            # Test generate_response
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, world!"}
            ]
            
            response = await client.generate_response(
                model="openai/gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )
            
            # Verify response
            assert response == "This is a test response"
            
            # Verify API was called with correct parameters
            mock_openai_client.chat.completions.create.assert_called_once()
            call_args = mock_openai_client.chat.completions.create.call_args[1]
            assert call_args["model"] == "openai/gpt-3.5-turbo"
            assert call_args["messages"] == messages
            assert call_args["temperature"] == 0.7
            assert call_args["extra_headers"] == client.extra_headers
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_settings, mock_openai_client):
        """Test error handling in generate_response."""
        with mock.patch.object(OpenAI, '__new__', return_value=mock_openai_client):
            client = OpenRouterClient()
            
            # Test authentication error
            mock_openai_client.chat.completions.create.side_effect = \
                APIConnectionError("Connection error")
            
            response = await client.generate_response(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            assert "Error: Could not connect to LLM provider" in response
            
            # Test rate limit error
            mock_openai_client.chat.completions.create.side_effect = \
                RateLimitError("Rate limit exceeded")
            
            response = await client.generate_response(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )
            
            assert "Error: Rate limit exceeded" in response
