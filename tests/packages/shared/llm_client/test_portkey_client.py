"""
Tests for the PortkeyClient implementation.

This module tests the PortkeyClient class which implements a multi-service strategy
with OpenRouter as primary provider and direct LLM services as fallbacks.
"""

import pytest
from unittest import mock
import asyncio
from typing import Dict, List, Any, Optional

from packages.shared.src.llm_client.portkey_client import PortkeyClient, PortkeyClientException
from core.orchestrator.src.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create a mock settings object with test values for multi-service strategy."""
    mock_settings = mock.Mock(spec=Settings)
    
    # API key
    mock_settings.PORTKEY_API_KEY = "test-portkey-key"
    mock_settings.TRACE_ID = "test-trace-id"
    
    # Model settings
    mock_settings.DEFAULT_LLM_MODEL_PRIMARY = "openai/gpt-4o"
    mock_settings.DEFAULT_LLM_MODEL_FALLBACK_OPENAI = "gpt-4o"
    mock_settings.DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC = "claude-3-5-sonnet-20240620"
    mock_settings.DEFAULT_LLM_MODEL = "openai/gpt-3.5-turbo"  # Legacy setting

    # Virtual keys for different providers
    mock_settings.PORTKEY_VIRTUAL_KEY_OPENROUTER = "vk_openrouter_123"
    mock_settings.PORTKEY_VIRTUAL_KEY_OPENAI = "vk_openai_456"
    mock_settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC = "vk_anthropic_789"
    
    # Add other virtual keys as None to avoid AttributeError
    mock_settings.PORTKEY_VIRTUAL_KEY_MISTRAL = None
    mock_settings.PORTKEY_VIRTUAL_KEY_HUGGINGFACE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_COHERE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_PERPLEXITY = None
    mock_settings.PORTKEY_VIRTUAL_KEY_DEEPSEEK = None
    mock_settings.PORTKEY_VIRTUAL_KEY_CODESTRAL = None
    mock_settings.PORTKEY_VIRTUAL_KEY_CODY = None
    mock_settings.PORTKEY_VIRTUAL_KEY_CONTINUE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_GROK = None
    mock_settings.PORTKEY_VIRTUAL_KEY_GOOGLE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_AZURE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_AWS = None
    mock_settings.PORTKEY_VIRTUAL_KEY_PINECONE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_WEAVIATE = None
    mock_settings.PORTKEY_VIRTUAL_KEY_ELEVENLABS = None
    
    # Legacy virtual key (should not be used if provider keys exist)
    mock_settings.VIRTUAL_KEY = "legacy_virtual_key"
    
    # Gateway config ID (optional)
    mock_settings.PORTKEY_CONFIG_ID = None  # We'll test both with and without this
    
    # Caching settings
    mock_settings.PORTKEY_CACHE_ENABLED = True
    mock_settings.LLM_SEMANTIC_CACHE_ENABLED = True
    mock_settings.LLM_SEMANTIC_CACHE_THRESHOLD = 0.85
    mock_settings.LLM_SEMANTIC_CACHE_TTL = 3600
    
    # Helper method mock
    mock_settings._get_portkey_api_key = mock.Mock(return_value="test-portkey-key")
    
    return mock_settings


@pytest.fixture
def mock_portkey():
    """Create a mock Portkey class."""
    with mock.patch('packages.shared.src.llm_client.portkey_client.Portkey') as mock_portkey_class:
        # Create a mock instance
        mock_instance = mock.MagicMock()
        mock_portkey_class.return_value = mock_instance
        
        # Create a mock response for chat completions
        mock_message = mock.MagicMock()
        mock_message.content = "This is a test response from Portkey"
        
        mock_choice = mock.MagicMock()
        mock_choice.message = mock_message
        
        mock_completion = mock.MagicMock()
        mock_completion.choices = [mock_choice]
        
        # Set up the mock chat completions
        mock_chat = mock.MagicMock()
        mock_chat.completions.create = mock.AsyncMock(return_value=mock_completion)
        mock_instance.chat = mock_chat
        
        # Set up the with_options method
        mock_instance.with_options.return_value = mock_instance
        
        yield mock_portkey_class


class TestPortkeyClient:
    """Tests for the PortkeyClient."""
    
    def test_initialization_with_fallback_strategy(self, mock_settings, mock_portkey):
        """Test initialization with fallback strategy using multiple virtual keys."""
        # Initialize client
        client = PortkeyClient(mock_settings)
        
        # Verify Portkey was initialized with the correct parameters
        mock_portkey.assert_called_once()
        init_args = mock_portkey.call_args[1]
        
        # Check the base parameters
        assert init_args["api_key"] == "test-portkey-key"
        assert init_args["trace_id"] == "test-trace-id"
        
        # Check the strategy configuration
        assert init_args["strategy"]["mode"] == "fallback"
        assert init_args["strategy"]["on_status_codes"] == [429, 500, 503]
        
        # Check the targets configuration
        targets = init_args["targets"]
        assert len(targets) == 3
        
        # Check OpenRouter is the primary target
        assert targets[0]["provider"] == "openrouter"
        assert targets[0]["virtual_key"] == "vk_openrouter_123"
        
        # Check OpenAI is the first fallback
        assert targets[1]["provider"] == "openai"
        assert targets[1]["virtual_key"] == "vk_openai_456"
        assert targets[1]["override_params"]["model"] == "gpt-4o"
        
        # Check Anthropic is the second fallback
        assert targets[2]["provider"] == "anthropic"
        assert targets[2]["virtual_key"] == "vk_anthropic_789"
        assert targets[2]["override_params"]["model"] == "claude-3-5-sonnet-20240620"
        
        # Check retry configuration
        assert init_args["retry"]["attempts"] == 3
        
        # Check cache configuration
        assert init_args["cache"]["mode"] == "semantic"
        assert init_args["cache"]["fallback"] == "openai"
        assert init_args["cache"]["threshold"] == 0.85
        assert init_args["cache"]["ttl"] == 3600
    
    def test_initialization_with_config_id(self, mock_settings, mock_portkey):
        """Test initialization using a Portkey Config ID."""
        # Set a config ID in settings
        mock_settings.PORTKEY_CONFIG_ID = "test-config-id"
        
        # Initialize client
        client = PortkeyClient(mock_settings)
        
        # Verify Portkey was initialized with the config ID
        mock_portkey.assert_called_once()
        init_args = mock_portkey.call_args[1]
        
        # Should use config ID approach over dynamic targets
        assert init_args["api_key"] == "test-portkey-key"
        assert init_args["trace_id"] == "test-trace-id"
        assert init_args["config"] == "test-config-id"
        
        # Should not have targets, strategy or retry
        assert "targets" not in init_args
        assert "strategy" not in init_args
        assert "retry" not in init_args
    
    def test_initialization_with_single_target(self, mock_settings, mock_portkey):
        """Test initialization with only one target (OpenRouter)."""
        # Remove the fallback virtual keys
        mock_settings.PORTKEY_VIRTUAL_KEY_OPENAI = None
        mock_settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC = None
        
        # Initialize client
        client = PortkeyClient(mock_settings)
        
        # Verify Portkey was initialized correctly for a single target
        mock_portkey.assert_called_once()
        init_args = mock_portkey.call_args[1]
        
        # Should not use fallback strategy with only one target
        assert init_args["api_key"] == "test-portkey-key"
        assert init_args["trace_id"] == "test-trace-id"
        assert init_args["provider"] == "openrouter"
        assert init_args["virtual_key"] == "vk_openrouter_123"
        
        # Should not have targets, strategy, or retry
        assert "targets" not in init_args
        assert "strategy" not in init_args
        assert "retry" not in init_args
    
    def test_initialization_with_no_targets(self, mock_settings, mock_portkey):
        """Test initialization with no virtual keys configured."""
        # Remove all virtual keys
        mock_settings.PORTKEY_VIRTUAL_KEY_OPENROUTER = None
        mock_settings.PORTKEY_VIRTUAL_KEY_OPENAI = None
        mock_settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC = None
        
        # Initialize client
        client = PortkeyClient(mock_settings)
        
        # Verify Portkey was initialized with just basic parameters
        mock_portkey.assert_called_once()
        init_args = mock_portkey.call_args[1]
        
        # Should use the legacy virtual key as fallback
        assert init_args["api_key"] == "test-portkey-key"
        assert init_args["trace_id"] == "test-trace-id"
        assert init_args["virtual_key"] == "legacy_virtual_key"
        
        # Should not have targets, strategy, or retry
        assert "targets" not in init_args
        assert "strategy" not in init_args
        assert "retry" not in init_args
    
    def test_initialization_with_no_api_key(self, mock_settings, mock_portkey):
        """Test initialization with no API key raises an exception."""
        # Set API key to None
        mock_settings.PORTKEY_API_KEY = None
        
        # Patch the _get_portkey_api_key method in the PortkeyClient class
        with mock.patch('packages.shared.src.llm_client.portkey_client.PortkeyClient._get_portkey_api_key', return_value=None):
            # Attempting to initialize should raise an exception
            with pytest.raises(PortkeyClientException):
                client = PortkeyClient(mock_settings)
    
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_settings, mock_portkey):
        """Test generate_response method."""
        # Initialize client
        client = PortkeyClient(mock_settings)
        
        # Test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, Portkey!"}
        ]
        
        # Call generate_response
        response = await client.generate_response(
            model="openai/gpt-4o",
            messages=messages,
            temperature=0.7,
            user_id="test-user",
            active_persona_name="test-persona"
        )
        
        # Verify the response
        assert response == "This is a test response from Portkey"
        
        # Verify the Portkey API was called correctly
        mock_instance = mock_portkey.return_value
        mock_instance.chat.completions.create.assert_called_once()
        
        # Check the arguments
        call_args = mock_instance.chat.completions.create.call_args[1]
        assert call_args["model"] == "openai/gpt-4o"
        assert call_args["messages"] == messages
        assert call_args["temperature"] == 0.7
        assert call_args["metadata"]["user_id"] == "test-user"
        assert call_args["metadata"]["active_persona"] == "test-persona"
        assert call_args["metadata"]["trace_source"] == "orchestra_main_api"
    
    @pytest.mark.asyncio
    async def test_provider_detection_from_model(self, mock_settings, mock_portkey):
        """Test that the correct provider is detected from the model name."""
        # Initialize client
        client = PortkeyClient(mock_settings)
        
        # Test with different model names
        assert client._get_provider_from_model("gpt-4o") == "openai"
        assert client._get_provider_from_model("claude-3-5-sonnet") == "anthropic"
        assert client._get_provider_from_model("mistral-large") == "mistral"
        assert client._get_provider_from_model("openai/gpt-4") == "openai"
        assert client._get_provider_from_model("anthropic/claude-3-opus") == "anthropic"
        assert client._get_provider_from_model("unknown-model") == "openrouter"
