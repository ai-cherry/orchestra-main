"""
Tests for the configuration module of the AI Orchestration System.

This module contains tests for configuration loading and validation functionality.
"""

import os
import pytest
from unittest import mock

from core.orchestrator.src.config.config import Settings, load_all_persona_configs


def test_settings_load_defaults():
    """Test that Settings loads default values correctly."""
    settings = Settings()
    assert settings.APP_NAME == "AI Orchestration System"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.LOG_LEVEL == "INFO"


def test_settings_from_env_vars(monkeypatch):
    """Test that settings loads from environment variables correctly."""
    # Set test environment variables
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Load settings with the modified environment
    settings = Settings()
    
    # Verify environment variables were applied
    assert settings.APP_NAME == "Test App"
    assert settings.ENVIRONMENT == "testing"
    assert settings.DEBUG is True
    assert settings.LOG_LEVEL == "DEBUG"


def test_load_all_persona_configs():
    """Test that persona configs are loaded correctly with expected keys."""
    # Mock the yaml loading to return predetermined data
    with mock.patch('yaml.safe_load') as mock_yaml_load, \
         mock.patch('os.path.exists', return_value=True), \
         mock.patch('os.listdir') as mock_listdir:
        
        # Setup the mock to return our test personas
        mock_listdir.return_value = ['cherry.yaml', 'sophia.yaml', 'gordon.yaml']
        
        # Define mock data for each persona file
        mock_yaml_data = {
            'cherry': {
                'name': 'Cherry',
                'age': 35,
                'background': 'AI assistant',
                'traits': {'helpful': 90},
                'interaction_style': 'friendly'
            },
            'sophia': {
                'name': 'Sophia',
                'age': 28,
                'background': 'Data scientist',
                'traits': {'analytical': 95},
                'interaction_style': 'precise'
            },
            'gordon': {
                'name': 'Gordon Gekko',
                'age': 50,
                'background': 'Finance',
                'traits': {'ambitious': 100},
                'interaction_style': 'assertive'
            }
        }
        
        # Configure the mock to return different data for each file
        def side_effect(file):
            filename = file.name.split('/')[-1]
            persona_name = filename.split('.')[0]
            return mock_yaml_data[persona_name]
        
        mock_yaml_load.side_effect = side_effect
        
        # Call the function
        persona_configs = load_all_persona_configs()
        
        # Verify the results
        assert len(persona_configs) == 3
        assert 'cherry' in persona_configs
        assert 'sophia' in persona_configs
        assert 'gordon' in persona_configs
        
        # Verify persona properties
        assert persona_configs['cherry'].name == 'Cherry'
        assert persona_configs['sophia'].name == 'Sophia'
        assert persona_configs['gordon'].name == 'Gordon Gekko'


def test_load_all_persona_configs_empty_directory():
    """Test that no personas are loaded when directory is empty."""
    with mock.patch('os.path.exists', return_value=True), \
         mock.patch('os.listdir', return_value=[]):
        
        persona_configs = load_all_persona_configs()
        assert len(persona_configs) == 0


def test_load_all_persona_configs_nonexistent_directory():
    """Test that no personas are loaded when directory doesn't exist."""
    with mock.patch('os.path.exists', return_value=False):
        persona_configs = load_all_persona_configs()
        assert len(persona_configs) == 0
