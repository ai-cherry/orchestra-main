"""
Tests for configuration loader functionality.

These tests focus on the loader module that handles configuration loading,
particularly for persona configurations.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from core.orchestrator.src.config.loader import load_persona_configs, create_default_persona_configs


def test_create_default_persona_configs():
    """Test that default persona configs are created correctly."""
    # Get default personas
    persona_configs = create_default_persona_configs()
    
    # Check that we have the expected number of personas
    assert len(persona_configs) == 3
    
    # Check that each expected persona exists
    assert "cherry" in persona_configs
    assert "sophia" in persona_configs
    assert "gordon_gekko" in persona_configs
    
    # Verify Gordon Gekko has the expected traits
    gekko = persona_configs["gordon_gekko"]
    assert gekko.name == "Gordon Gekko"
    assert "Ruthless Efficiency Expert" in gekko.description
    assert "no-nonsense" in gekko.prompt_template
    assert gekko.traits.get("efficiency") == 0.9
    assert gekko.traits.get("assertiveness") == 0.8
    assert gekko.traits.get("pragmatism") == 0.7


@pytest.mark.critical
def test_load_persona_configs_with_missing_file():
    """Test that load_persona_configs falls back to defaults when file is missing."""
    # Mock the open function to raise FileNotFoundError
    with patch("builtins.open", side_effect=FileNotFoundError):
        # Call the function
        persona_configs = load_persona_configs()
        
        # Check that we got default configs
        assert len(persona_configs) == 3
        assert "cherry" in persona_configs
        assert "sophia" in persona_configs
        assert "gordon_gekko" in persona_configs


def test_load_persona_configs_with_invalid_yaml():
    """Test that load_persona_configs falls back to defaults when YAML is invalid."""
    # Mock open to return a file-like object with invalid YAML
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
        # Mock yaml.safe_load to raise YAMLError
        with patch("yaml.safe_load", side_effect=Exception("Invalid YAML")):
            # Call the function
            persona_configs = load_persona_configs()
            
            # Check that we got default configs
            assert len(persona_configs) == 3
            assert "cherry" in persona_configs


def test_load_persona_configs_with_empty_yaml():
    """Test that load_persona_configs falls back to defaults when YAML is empty."""
    # Mock open to return a file-like object with empty content
    with patch("builtins.open", mock_open(read_data="")):
        # Mock yaml.safe_load to return None (empty file)
        with patch("yaml.safe_load", return_value=None):
            # Call the function
            persona_configs = load_persona_configs()
            
            # Check that we got default configs
            assert len(persona_configs) == 3
            assert "cherry" in persona_configs


def test_load_persona_configs_with_valid_yaml():
    """Test that load_persona_configs properly loads valid YAML."""
    # Define test YAML content
    yaml_content = """
    personas:
      test_persona:
        name: "Test Persona"
        description: "A test persona"
        base_prompt_template: "You are a test: {input}"
        traits:
          test_trait: 0.5
    """
    
    # Mock open to return file-like object with test content
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        # Call the function with patched yaml.safe_load to return expected dict
        with patch("yaml.safe_load", return_value={"test_persona": {
            "name": "Test Persona",
            "description": "A test persona",
            "base_prompt_template": "You are a test: {input}",
            "traits": {"test_trait": 0.5}
        }}):
            # Call the function
            persona_configs = load_persona_configs()
            
            # Check that we got the expected persona
            assert "test_persona" in persona_configs
            assert persona_configs["test_persona"].name == "Test Persona"
            assert persona_configs["test_persona"].traits.get("test_trait") == 0.5
