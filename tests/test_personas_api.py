"""
Test module for the Personas API endpoints.

This module provides test cases for the personas API functionality,
including CRUD operations on persona configurations.
"""

import os
import tempfile
import pytest
import yaml
from fastapi.testclient import TestClient

from core.orchestrator.src.main import app
from core.orchestrator.src.config.config import settings


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def temp_persona_dir():
    """Create a temporary directory for persona configs during tests."""
    # Create a temporary directory
    original_path = settings.PERSONA_CONFIG_PATH
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Set the persona config path to the temporary directory
        settings.PERSONA_CONFIG_PATH = tmp_dir
        
        # Create some test persona files
        test_personas = {
            "test1": {
                "name": "Test1",
                "age": 30,
                "background": "Test background 1",
                "traits": {"trait1": 80, "trait2": 60},
                "interaction_style": "test_style1"
            },
            "test2": {
                "name": "Test2",
                "age": 40,
                "background": "Test background 2",
                "traits": {"trait3": 70, "trait4": 90},
                "interaction_style": "test_style2"
            }
        }
        
        # Write test personas to YAML files
        for name, config in test_personas.items():
            file_path = os.path.join(tmp_dir, f"{name}.yaml")
            with open(file_path, "w") as f:
                yaml.dump(config, f)
        
        yield
        
        # Restore the original persona config path
        settings.PERSONA_CONFIG_PATH = original_path


def test_get_personas(client, temp_persona_dir):
    """Test the GET /api/personas/ endpoint."""
    response = client.get("/api/personas/")
    assert response.status_code == 200
    personas = response.json()
    assert isinstance(personas, list)
    assert "test1" in personas
    assert "test2" in personas


def test_get_persona(client, temp_persona_dir):
    """Test the GET /api/personas/{name} endpoint."""
    # Test getting an existing persona
    response = client.get("/api/personas/test1")
    assert response.status_code == 200
    persona = response.json()
    assert persona["name"] == "Test1"
    assert persona["age"] == 30
    
    # Test getting a non-existent persona
    response = client.get("/api/personas/nonexistent")
    assert response.status_code == 404


def test_create_persona(client, temp_persona_dir):
    """Test the POST /api/personas/ endpoint."""
    # Test creating a new persona
    new_persona = {
        "name": "NewPersona",
        "age": 25,
        "background": "New test background",
        "traits": {"creativity": 85, "logic": 75},
        "interaction_style": "balanced"
    }
    
    response = client.post("/api/personas/", json=new_persona)
    assert response.status_code == 201
    result = response.json()
    assert result["status"] == "success"
    
    # Verify the persona was created by getting it
    response = client.get("/api/personas/newpersona")
    assert response.status_code == 200
    persona = response.json()
    assert persona["name"] == "NewPersona"
    
    # Test creating a persona with a name that already exists
    response = client.post("/api/personas/", json=new_persona)
    assert response.status_code == 409


def test_update_persona(client, temp_persona_dir):
    """Test the POST /api/personas/{name}/update endpoint."""
    # Get the existing persona
    response = client.get("/api/personas/test1")
    persona = response.json()
    
    # Update some values
    persona["age"] = 35
    persona["traits"]["trait1"] = 90
    
    # Send the update
    response = client.post("/api/personas/test1/update", json=persona)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    
    # Verify the update took effect
    response = client.get("/api/personas/test1")
    updated_persona = response.json()
    assert updated_persona["age"] == 35
    assert updated_persona["traits"]["trait1"] == 90
    
    # Test updating a non-existent persona
    response = client.post("/api/personas/nonexistent/update", json=persona)
    assert response.status_code == 404


def test_delete_persona(client, temp_persona_dir):
    """Test the DELETE /api/personas/{name} endpoint."""
    # Test deleting an existing persona
    response = client.delete("/api/personas/test1")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    
    # Verify the persona was deleted
    response = client.get("/api/personas/test1")
    assert response.status_code == 404
    
    # Test deleting a non-existent persona
    response = client.delete("/api/personas/nonexistent")
    assert response.status_code == 404
