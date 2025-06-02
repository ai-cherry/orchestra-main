"""
Persona loading middleware for AI Orchestration System.

This module provides middleware or dependency for handling persona context in requests.
"""

import logging
from typing import Dict

from fastapi import Depends, Request

from core.orchestrator.src.config.loader import force_reload_personas, load_persona_configs
from packages.shared.src.models.base_models import PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)

def get_persona_configs(force_refresh: bool = False) -> Dict[str, PersonaConfig]:
    """
    Get all available persona configurations.

    Args:
        force_refresh: If True, force reload persona configs from disk

    Returns:
        Dict[str, PersonaConfig]: Dictionary of persona configurations
    """
    return load_persona_configs(force_refresh=force_refresh)

def reload_personas() -> Dict[str, PersonaConfig]:
    """
    Force reload persona configurations from disk.

    This function can be used by API endpoints to refresh persona
    configurations without restarting the application.

    Returns:
        Dict[str, PersonaConfig]: Refreshed dictionary of persona configurations
    """
    return force_reload_personas()

async def get_active_persona(
    request: Request,
    persona_configs: Dict[str, PersonaConfig] = Depends(get_persona_configs),
) -> PersonaConfig:
    """
    Get the active persona configuration based on request parameters.

    This dependency extracts the persona name from request parameters,
    retrieves the corresponding PersonaConfig, and attaches it to
    request.state.active_persona. If the persona name is invalid,
    it falls back to the default 'cherry' persona or creates an emergency persona.

    Args:
        request: The FastAPI request object
        persona_configs: Dictionary of available persona configurations

    Returns:
        PersonaConfig: The active persona configuration

    Raises:
        HTTPException: If no valid persona could be loaded (critical system error)
    """
    # Get persona name from query parameters, default to "cherry"
    persona_name = request.query_params.get("persona", "cherry")

    # Try to get the requested persona
    active_persona = persona_configs.get(persona_name)

    # If requested persona doesn't exist, try to use "cherry" as fallback
    if not active_persona and persona_name != "cherry":
        logger.warning(f"Persona '{persona_name}' not found, falling back to 'cherry'")
        active_persona = persona_configs.get("cherry")

    # If cherry is also missing, create an emergency persona
    if not active_persona:
        logger.error("No valid persona found, creating emergency fallback persona")
        # Create an emergency fallback persona
        active_persona = PersonaConfig(
            name="Emergency Assistant",
            description="Emergency fallback assistant",
            prompt_template="You are an emergency fallback assistant. The system encountered an issue loading the requested persona. Please assist the user while notifying them of this issue.",
            traits={"helpfulness": 0.9, "reliability": 0.9},
            metadata={"emergency_fallback": True},
        )

        # Try to reload personas in case it's a temporary issue
        try:
            logger.info("Attempting to reload personas")
            refreshed_configs = reload_personas()
            # Check if we now have the requested persona or at least cherry
            if persona_name in refreshed_configs:
                active_persona = refreshed_configs[persona_name]
                logger.info(f"Successfully loaded '{persona_name}' on reload")
            elif "cherry" in refreshed_configs:
                active_persona = refreshed_configs["cherry"]
                logger.info("Successfully loaded 'cherry' as fallback on reload")
        except Exception as e:
            logger.error(f"Failed to reload personas: {e}")

    # Track which persona was actually used
    request.state.requested_persona = persona_name
    request.state.active_persona = active_persona

    # Log persona selection result
    if persona_name != active_persona.name.lower():
        logger.info(f"Using '{active_persona.name}' instead of requested '{persona_name}'")
    else:
        logger.debug(f"Using requested persona '{persona_name}'")

    return active_persona
