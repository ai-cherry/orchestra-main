"""
Personas API endpoints for the AI Orchestration System.

This module provides API endpoints for managing and interacting with personas,
including listing available personas, retrieving persona details, and
updating persona configurations.
"""

import os

import yaml
from fastapi import APIRouter, Depends, HTTPException, status

from core.orchestrator.src.config.loader import force_reload_personas, load_persona_configs
from core.orchestrator.src.config.settings import Settings, get_settings
from packages.shared.src.models.base_models import PersonaConfig

router = APIRouter()


@router.get("/", response_model=list[str])
async def get_personas() -> list[str]:
    """
    List all available personas.

    Returns:
        List of persona names that are available in the system
    """
    personas = load_persona_configs()
    return list(personas.keys())


@router.get("/reload", response_model=dict)
async def reload_personas() -> dict:
    """
    Force reload all persona configurations from disk.

    This endpoint is useful when personas have been modified
    without restarting the server.

    Returns:
        Dictionary with reload status and list of loaded personas
    """
    try:
        personas = force_reload_personas()
        return {
            "status": "success",
            "message": f"Successfully reloaded {len(personas)} personas",
            "personas": list(personas.keys()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload personas: {str(e)}")


@router.get("/{name}", response_model=PersonaConfig)
async def get_persona(name: str) -> PersonaConfig:
    """
    Get details for a specific persona.

    Args:
        name: The name of the persona to retrieve

    Returns:
        The persona configuration for the specified name

    Raises:
        HTTPException: If the persona is not found (404)
    """
    personas = load_persona_configs()
    if name not in personas:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")
    return personas[name]


@router.post("/", status_code=201)
async def create_persona(persona_config: PersonaConfig, settings: Settings = Depends(get_settings)):
    """
    Create a new persona with the provided configuration.

    Args:
        persona_config: The configuration for the new persona

    Returns:
        A status message indicating whether the creation was successful

    Raises:
        HTTPException: If a persona with that name already exists (409) or if there's an error creating the file (500)
    """
    # Ensure the persona name is present
    if not persona_config.name:
        raise HTTPException(status_code=400, detail="Persona name is required")

    # Convert name to lowercase for the filename
    name_lower = persona_config.name.lower()

    # Check if the persona already exists
    personas = load_persona_configs()
    if name_lower in personas:
        raise HTTPException(status_code=409, detail=f"Persona '{persona_config.name}' already exists")

    # Get the persona file path
    persona_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "../../config/personas.yaml"))

    # Ensure the persona directory exists
    os.makedirs(persona_dir, exist_ok=True)

    yaml_path = os.path.join(persona_dir, "personas.yaml")

    try:
        # Load existing personas.yaml
        try:
            with open(yaml_path, "r") as file:
                existing_personas = yaml.safe_load(file) or {}
        except FileNotFoundError:
            existing_personas = {}

        # Add new persona
        existing_personas[name_lower] = persona_config.model_dump(exclude_none=True)

        # Write updated personas.yaml
        with open(yaml_path, "w") as file:
            yaml_content = yaml.dump(existing_personas, sort_keys=False)
            file.write(yaml_content)

        # Force reload personas
        force_reload_personas()

        return {
            "status": "success",
            "message": f"Persona '{persona_config.name}' has been created successfully",
            "persona": persona_config,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create persona '{persona_config.name}': {str(e)}",
        )


@router.post("/{name}/update", status_code=200)
async def update_persona(name: str, persona_config: PersonaConfig, settings: Settings = Depends(get_settings)):
    """
    Update a persona configuration by writing changes to the corresponding YAML file.

    Args:
        name: The name of the persona to update
        persona_config: The updated persona configuration

    Returns:
        A status message indicating whether the update was successful

    Raises:
        HTTPException: If the persona is not found (404) or if there's an error updating the file (500)
    """
    # Convert name to lowercase for consistency
    name_lower = name.lower()

    # Check if the persona exists
    personas = load_persona_configs()
    if name_lower not in personas:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    # Get the persona file path
    persona_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "../../config/personas.yaml"))
    yaml_path = os.path.join(persona_dir, "personas.yaml")

    # Ensure the persona name in the config matches the requested name
    persona_config.name = name

    try:
        # Load existing personas.yaml
        with open(yaml_path, "r") as file:
            existing_personas = yaml.safe_load(file) or {}

        # Update persona
        existing_personas[name_lower] = persona_config.model_dump(exclude_none=True)

        # Write updated personas.yaml
        with open(yaml_path, "w") as file:
            yaml_content = yaml.dump(existing_personas, sort_keys=False)
            file.write(yaml_content)

        # Force reload personas
        force_reload_personas()

        return {
            "status": "success",
            "message": f"Persona '{name}' has been updated successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update persona '{name}': {str(e)}")


@router.delete("/{name}", status_code=status.HTTP_200_OK)
async def delete_persona(name: str, settings: Settings = Depends(get_settings)):
    """
    Delete a persona configuration by removing it from the personas.yaml file.

    Args:
        name: The name of the persona to delete

    Returns:
        A status message indicating whether the deletion was successful

    Raises:
        HTTPException: If the persona is not found (404) or if there's an error deleting it (500)
    """
    # Convert name to lowercase for consistency
    name_lower = name.lower()

    # Check if the persona exists
    personas = load_persona_configs()
    if name_lower not in personas:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    # Get the persona file path
    persona_dir = os.path.dirname(os.path.join(os.path.dirname(__file__), "../../config/personas.yaml"))
    yaml_path = os.path.join(persona_dir, "personas.yaml")

    try:
        # Load existing personas.yaml
        with open(yaml_path, "r") as file:
            existing_personas = yaml.safe_load(file) or {}

        # Remove persona
        if name_lower in existing_personas:
            del existing_personas[name_lower]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Persona '{name}' not found in configuration file",
            )

        # Write updated personas.yaml
        with open(yaml_path, "w") as file:
            yaml_content = yaml.dump(existing_personas, sort_keys=False)
            file.write(yaml_content)

        # Force reload personas
        force_reload_personas()

        return {
            "status": "success",
            "message": f"Persona '{name}' has been deleted successfully",
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete persona '{name}': {str(e)}")
