"""
Persona dependency for AI Orchestration System.

This module provides the dependency injection function for the persona management,
supporting the middleware that loads the active persona configuration.
"""

import logging
from typing import Dict, Optional

from fastapi import Depends, Request

from core.orchestrator.src.config.settings import Settings, get_settings
from packages.shared.src.models.base_models import PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)

# Global persona cache
_personas_cache = {}

def load_personas(settings: Settings) -> Dict[str, PersonaConfig]:
    """
    Load available personas from configuration.

    Args:
        settings: Application settings

    Returns:
        Dictionary of persona configurations mapped by lowercase name
    """
    global _personas_cache

    # Return cached personas if available
    if _personas_cache:
        return _personas_cache

    # Default personas if none are configured
    default_personas = {
        "cherry": PersonaConfig(name="Cherry", description="A helpful and friendly AI assistant."),
        "sophia": PersonaConfig(
            name="Sophia",
            description="A thoughtful AI assistant focused on detailed analysis.",
        ),
        "gordon_gekko": PersonaConfig(
            name="Gordon Gekko",
            description="A business-focused AI assistant inspired by the Wall Street character.",
        ),
    }

    # Use settings personas if available, otherwise use defaults
    # In a real implementation, this would load from a configuration file or database
    personas = default_personas

    # Cache the result
    _personas_cache = personas

    return personas

def get_persona_config(
    request: Request,
    persona_name: Optional[str] = None,
    settings: Settings = Depends(get_settings),
) -> PersonaConfig:
    """
    Get the persona configuration for the specified name.

    This function is used by the middleware to set the active persona
    on the request state.

    Args:
        request: The HTTP request
        persona_name: Optional persona name to load, defaults to "cherry"
        settings: Application settings

    Returns:
        The persona configuration

    Raises:
        HTTPException: If the persona is not found
    """
    # Load available personas
    personas = load_personas(settings)

    # Use default persona if none specified
    if not persona_name:
        persona_name = "cherry"

    # Normalize persona name
    persona_name = persona_name.lower()

    # Get persona configuration
    persona_config = personas.get(persona_name)

    # Fall back to default if persona not found
    if not persona_config:
        logger.warning(f"Persona '{persona_name}' not found, using default")
        persona_config = personas["cherry"]

    return persona_config
