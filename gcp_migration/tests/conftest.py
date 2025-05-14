"""
Pytest configuration file for AI Orchestra migration tests.

This file defines fixtures and configuration for the test suite.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import pytest
from google.cloud import aiplatform
from google.cloud.aiplatform import Model, Endpoint
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path so we can import migration modules
sys.path.insert(0, str(Path(__file__).parent.parent))


# Fixture for environment variables
@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for tests."""
    original_environ = os.environ.copy()
    os.environ["GCP_PROJECT_ID"] = "mock-project-id"
    os.environ["GCP_REGION"] = "us-central1"
    os.environ["MACHINE_TYPE"] = "n1-standard-4"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_environ)


# Mock for GCP Vertex AI Model class
@pytest.fixture
def mock_vertex_model():
    """Create a mock for the Vertex AI Model class."""
    with patch("google.cloud.aiplatform.Model", autospec=True) as mock_model:
        # Mock the upload method
        mock_model.upload = MagicMock()
        mock_model.upload.return_value = mock_model
        
        # Mock the deploy method
        mock_model.deploy = AsyncMock()
        mock_model.deploy.return_value = mock_model
        
        # Add name attribute
        mock_model.name = "projects/mock-project-id/locations/us-central1/models/mock-model-id"
        
        yield mock_model


# Mock for GCP Vertex AI Endpoint class
@pytest.fixture
def mock_vertex_endpoint():
    """Create a mock for the Vertex AI Endpoint class."""
    with patch("google.cloud.aiplatform.Endpoint", autospec=True) as mock_endpoint:
        # Mock the create method
        mock_endpoint.create = MagicMock()
        mock_endpoint.create.return_value = mock_endpoint
        
        # Mock the predict method
        mock_endpoint.predict = AsyncMock()
        mock_endpoint.predict.return_value = MagicMock(predictions=[
            {"confidence": 0.95, "class": "test_class"}
        ])
        
        # Add name attribute
        mock_endpoint.name = "projects/mock-project-id/locations/us-central1/endpoints/mock-endpoint-id"
        
        yield mock_endpoint


# Mock for GCP Vertex AI initialization
@pytest.fixture
def mock_vertex_init():
    """Mock the Vertex AI initialization."""
    with patch("google.cloud.aiplatform.init") as mock_init:
        yield mock_init


# Fixture for test model configuration
@pytest.fixture
def test_model_config():
    """Create a test model configuration."""
    return {
        "model_name": "test-model",
        "model_type": "custom-trained",
        "artifact_uri": "gs://test-bucket/model",
        "machine_type": "n1-standard-4",
        "min_replicas": 1,
        "max_replicas": 3,
        "metadata": {
            "framework": "tensorflow",
            "description": "Test model for unit tests"
        },
        "labels": {
            "environment": "test",
            "team": "ai-orchestra"
        }
    }


# Fixture for test model config file
@pytest.fixture
def test_model_config_file(test_model_config, tmp_path):
    """Create a temporary model configuration file."""
    import json
    
    # Create a temporary config file
    config_dir = tmp_path / "model_configs"
    config_dir.mkdir()
    config_file = config_dir / "test-model.json"
    
    # Write the config to the file
    with open(config_file, "w") as f:
        json.dump(test_model_config, f)
    
    yield str(config_file)


# Event loop fixture for asyncio testing
@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()