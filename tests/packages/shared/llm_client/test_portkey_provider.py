"""
Tests for the PortkeyProvider implementation.

This module contains tests for the PortkeyProvider class, which leverages
Portkey's API to handle LLM requests with retry logic and fallback capabilities.
"""

import pytest
from unittest import mock
import asyncio
from typing import Dict, List, Any

from core.orchestrator.src.services.llm.providers import (
    PortkeyProvider, 
    LLMProviderConfig,
    LLMProviderRateLimitError,
    LLMProviderConnectionError,
    LLMProviderTimeoutError
)
from openai import APITimeoutError, APIConnectionError, RateLimitError


@pytest.fixture
def mock_settings():
    """Create a mock settings object with test values."""
    with mock.patch('core.orchestrator.src.config.settings.get_settings') as mock_get_settings:
        mock_settings = mock.Mock()
        mock_settings.PORTKEY_API_KEY = "test-portkey-key"
        mock_settings.TRACE_ID = "test-trace-id"
        mock_settings.VIRTUAL_KEY = "test-virtual-key"
        
        # Add fallback configuration
        mock_settings.get_portkey_fallbacks = mock.Mock(return_value=[
            {"provider": "openai", "model": "gpt-3.5-turbo"},
            {"provider": "groq", "model": "llama-3-8b-8192"}
        ])
        
        mock_get_settings.return_value = mock_settings
        yield mock_settings


@pytest.fixture
def mock_portkey_client():
    """Create a mock Portkey client with predefined responses."""
    mock_client = mock.MagicMock()
    
    # Create a mock response for chat completions
    mock_message = mock.MagicMock()
    mock_message.content = "This is a test response from Portkey"
    
    mock_choice = mock.MagicMock()
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    
    mock_completion = mock.MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "gpt-4o"
    mock_completion.usage.prompt_tokens = 15
    mock_completion.usage.completion_tokens = 25
    mock_completion.usage.total_tokens = 40
    
    # Set up the mock chat completions method
    mock_chat_completions = mock.MagicMock()
    mock_chat_completions.create = mock.AsyncMock(return_value=mock_completion)
    
    # Set up the options method with a return for chat.completions
    mock_client_with_options = mock.MagicMock()
    mock_client_with_options.chat.completions = mock_chat_completions
    mock_client.with_options = mock.MagicMock(return_value=mock_client_with_options)
    
    return mock_client


class TestPortkeyProvider:
    """Tests for the PortkeyProvider."""
    
    def test_initialization(self, mock_settings):
        """Test provider initialization with mock settings."""
        with mock.patch('portkey.Portkey') as mock_portkey:
            # Create a configuration
            config = LLMProviderConfig(
                api_key="test-api-key",
                base_url="",
                default_model="gpt-4o",
                max_retries=3
            )
            
            # Initialize provider with fallback config
            fallback_config = [
                {"provider": "openai", "model": "gpt-3.5-turbo"},
                {"provider": "groq", "model": "llama-3-8b-8192"}
            ]
            provider = PortkeyProvider(config, fallback_config=fallback_config)
            provider.initialize()
            
            # Verify Portkey was initialized correctly
            mock_portkey.assert_called_once()
            call_args = mock_portkey.call_args[1]
            assert call_args["api_key"] == "test-api-key"
            assert call_args["retry"] == {"attempts": 3}
            assert call_args["fallbacks"] == fallback_config
            assert call_args["strategy"] == {"mode": "fallback"}
    
    def test_provider_properties(self, mock_settings):
        """Test provider properties."""
        with mock.patch('portkey.Portkey'):
            config = LLMProviderConfig(
                api_key="test-api-key",
                base_url="",
                default_model="gpt-4o"
            )
            provider = PortkeyProvider(config)
            
            assert provider.provider_name == "portkey"
            assert provider.default_model == "gpt-4o"
    
    @pytest.mark.asyncio
    async def test_generate_chat_completion(self, mock_settings, mock_portkey_client):
        """Test generate_chat_completion method with mocked client."""
        with mock.patch('portkey.Portkey', return_value=mock_portkey_client):
            # Set up mock settings with PORTKEY_CONFIG_ID
            mock_settings.PORTKEY_CONFIG_ID = "test-config-id"
            
            config = LLMProviderConfig(
                api_key="test-api-key",
                base_url="",
                default_model="gpt-4o"
            )
            provider = PortkeyProvider(config)
            provider.initialize()
            
            # Test generate_chat_completion
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, Portkey!"}
            ]
            
            response = await provider.generate_chat_completion(
                messages=messages,
                model="gpt-4o",
                temperature=0.7
            )
            
            # Verify response
            assert response["content"] == "This is a test response from Portkey"
            assert response["model"] == "gpt-4o"
            assert response["provider"] == "portkey"
            assert response["usage"]["total_tokens"] == 40
            
            # Verify the model header was applied correctly
            mock_portkey_client.with_options.assert_called_once()
            first_with_options_args = mock_portkey_client.with_options.call_args[1]
            assert first_with_options_args["default_headers"] == {"model": "gpt-4o"}
            
            # Verify the config ID was applied correctly in the chained with_options call
            mock_client_with_model = mock_portkey_client.with_options.return_value
            mock_client_with_model.with_options.assert_called_once()
            second_with_options_args = mock_client_with_model.with_options.call_args[1]
            assert second_with_options_args["config"] == "test-config-id"
            
            # Verify chat.completions.create was called with correct parameters
            mock_client_with_config = mock_client_with_model.with_options.return_value
            mock_client_with_config.chat.completions.create.assert_called_once()
            call_args = mock_client_with_config.chat.completions.create.call_args[1]
            assert call_args["model"] == "gpt-4o"
            assert call_args["messages"] == messages
            assert call_args["temperature"] == 0.7
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_settings):
        """Test retry logic for transient errors."""
        with mock.patch('portkey.Portkey') as mock_portkey:
            # Create a mock client that fails with connection errors twice, then succeeds
            mock_client_with_options = mock.MagicMock()
            mock_client = mock.MagicMock()
            mock_client.with_options.return_value = mock_client_with_options
            
            # Set up mock chat completions that fails twice with connection errors
            mock_chat_completions = mock.MagicMock()
            
            # Create a successful response for the third attempt
            mock_message = mock.MagicMock()
            mock_message.content = "Success after retries"
            
            mock_choice = mock.MagicMock()
            mock_choice.message = mock_message
            mock_choice.finish_reason = "stop"
            
            mock_completion = mock.MagicMock()
            mock_completion.choices = [mock_choice]
            mock_completion.model = "gpt-4o"
            mock_completion.usage.prompt_tokens = 10
            mock_completion.usage.completion_tokens = 20
            mock_completion.usage.total_tokens = 30
            
            # Mock side effects: first 2 calls fail, 3rd succeeds
            side_effects = [
                APIConnectionError("Connection error 1"),
                APITimeoutError("Timeout error"),
                mock_completion
            ]
            
            mock_chat_completions.create = mock.AsyncMock(side_effect=side_effects)
            mock_client_with_options.chat.completions = mock_chat_completions
            
            mock_portkey.return_value = mock_client
            
            # Initialize provider
            config = LLMProviderConfig(
                api_key="test-api-key",
                base_url="",
                default_model="gpt-4o",
                max_retries=3,
                retry_delay=0.01,  # Use small values for fast tests
                retry_max_delay=0.05
            )
            provider = PortkeyProvider(config)
            provider.initialize()
            
            # Test generate_chat_completion with retries
            messages = [{"role": "user", "content": "Test retry logic"}]
            
            # Should eventually succeed after retries
            response = await provider.generate_chat_completion(
                messages=messages,
                model="gpt-4o"
            )
            
            # Verify response
            assert response["content"] == "Success after retries"
            
            # Verify that create was called 3 times (2 failures + 1 success)
            assert mock_client_with_options.chat.completions.create.call_count == 3
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, mock_settings):
        """Test handling of rate limit errors."""
        with mock.patch('portkey.Portkey') as mock_portkey:
            # Create a mock client that fails with a rate limit error
            mock_client_with_options = mock.MagicMock()
            mock_client = mock.MagicMock()
            mock_client.with_options.return_value = mock_client_with_options
            
            # Set up mock chat completions that fails with rate limit error
            mock_chat_completions = mock.MagicMock()
            mock_chat_completions.create = mock.AsyncMock(side_effect=RateLimitError("Rate limit exceeded"))
            mock_client_with_options.chat.completions = mock_chat_completions
            
            mock_portkey.return_value = mock_client
            
            # Initialize provider
            config = LLMProviderConfig(
                api_key="test-api-key",
                base_url="",
                default_model="gpt-4o",
                max_retries=3
            )
            provider = PortkeyProvider(config)
            provider.initialize()
            
            # Test generate_chat_completion with rate limit error
            messages = [{"role": "user", "content": "Test rate limit error"}]
            
            # Should return a user-friendly error message
            response = await provider.generate_chat_completion(
                messages=messages,
                model="gpt-4o"
            )
            
            # Rate limit errors shouldn't be retried, so create should be called only once
            assert mock_client_with_options.chat.completions.create.call_count == 1
            
            # Verify user-friendly error message is included
            assert "too many requests" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_fallback_configuration(self, mock_settings, mock_portkey_client):
        """Test that fallback configuration is properly set up."""
        with mock.patch('portkey.Portkey', return_value=mock_portkey_client):
            config = LLMProviderConfig(
                api_key="test-api-key",
                base_url="",
                default_model="gpt-4o"
            )
            
            # Create fallback configuration
            fallback_config = [
                {"provider": "openai", "model": "gpt-3.5-turbo"},
                {"provider": "groq", "model": "llama-3-8b-8192"}
            ]
            
            provider = PortkeyProvider(config, fallback_config=fallback_config)
            provider.initialize()
            
            # Verify Portkey was initialized with fallback configuration
            mock_portkey_client.assert_called_with(
                api_key="test-api-key",
                fallbacks=fallback_config,
                strategy={"mode": "fallback"},
                retry={"attempts": 3}
            )
            
            # Generate a response
            messages = [{"role": "user", "content": "Test fallback configuration"}]
            response = await provider.generate_chat_completion(messages=messages)
            
            # Verify response
            assert response["content"] == "This is a test response from Portkey"
