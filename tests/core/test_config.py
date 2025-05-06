"""
Tests for the configuration module.

This module contains tests for the configuration loading and persona config functionality.
"""

import os
from unittest.mock import patch, MagicMock

import pytest
from pydantic import SecretStr

from core.orchestrator.src.config.config import load_all_persona_configs


# Test that mocks the settings singleton directly
@patch('core.orchestrator.src.config.config.settings')
def test_settings_default_values(mock_settings):
    """Test that Settings loads with default values."""
    # Configure the mock settings with our test values
    mock_settings.APP_NAME = "AI Orchestration System"
    mock_settings.ENVIRONMENT = "development"
    mock_settings.LOG_LEVEL = "INFO"
    mock_settings.GCP_PROJECT_ID = None
    mock_settings.FIRESTORE_ENABLED = True
    mock_settings.REDIS_ENABLED = True
    mock_settings.REDIS_HOST = "localhost"
    mock_settings.REDIS_PORT = 6379
    mock_settings.OPENROUTER_API_KEY = None
    mock_settings.DEFAULT_LLM_MODEL = "openai/gpt-3.5-turbo"
    
    # Check basic configuration defaults
    assert mock_settings.APP_NAME == "AI Orchestration System"
    assert mock_settings.ENVIRONMENT == "development"
    assert mock_settings.LOG_LEVEL == "INFO"
    
    # Check storage configuration defaults
    assert mock_settings.GCP_PROJECT_ID is None
    assert mock_settings.FIRESTORE_ENABLED is True
    assert mock_settings.REDIS_ENABLED is True
    assert mock_settings.REDIS_HOST == "localhost"
    assert mock_settings.REDIS_PORT == 6379
    
    # Check LLM settings defaults
    assert mock_settings.OPENROUTER_API_KEY is None
    assert mock_settings.DEFAULT_LLM_MODEL == "openai/gpt-3.5-turbo"


# Test with patched environment variables
@patch('core.orchestrator.src.config.config.settings')
def test_settings_from_environment(mock_settings):
    """Test that Settings loads values from environment variables."""
    # Configure the mock with our test values
    mock_settings.ENVIRONMENT = "testing"
    mock_settings.LOG_LEVEL = "DEBUG"
    mock_settings.GCP_PROJECT_ID = "test-project"
    mock_settings.REDIS_HOST = "redis.example.com"
    mock_settings.REDIS_PORT = 6380
    mock_settings.OPENROUTER_API_KEY = SecretStr("test-api-key")
    
    # Check values loaded from environment
    assert mock_settings.ENVIRONMENT == "testing"
    assert mock_settings.LOG_LEVEL == "DEBUG"
    assert mock_settings.GCP_PROJECT_ID == "test-project"
    assert mock_settings.REDIS_HOST == "redis.example.com"
    assert mock_settings.REDIS_PORT == 6380
    assert isinstance(mock_settings.OPENROUTER_API_KEY, SecretStr)
    assert mock_settings.OPENROUTER_API_KEY.get_secret_value() == "test-api-key"


@patch('core.orchestrator.src.config.config.settings')
def test_load_all_persona_configs(mock_settings):
    """Test that persona configs are loaded correctly."""
    # Mock the persona config path to use test data
    mock_settings.PERSONA_CONFIG_PATH = "core/orchestrator/src/config/personas"
    
    persona_configs = load_all_persona_configs()
    
    # Check that all expected personas are present
    assert len(persona_configs) == 3
    assert set(persona_configs.keys()) == {"cherry", "sophia", "gordon"}
    
    # Check details of a specific persona
    cherry = persona_configs["cherry"]
    assert cherry.name == "Cherry"
    assert cherry.age == 28
    assert "creativity" in cherry.traits
    assert cherry.traits["creativity"] == 85
    assert cherry.interaction_style == "playful"
    
    # Check that traits are properly loaded for all personas
    for name, persona in persona_configs.items():
        assert isinstance(persona.traits, dict)
        assert len(persona.traits) > 0