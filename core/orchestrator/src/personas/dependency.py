"""
Persona dependency module for AI Orchestration System.

This module provides dependency injection for persona management,
centralizing persona access throughout the application.
"""

import logging
from functools import lru_cache
from typing import Optional

# Import the settings instance directly
from core.orchestrator.src.config.config import settings
from core.orchestrator.src.personas.loader import PersonaManager

# Configure logging
logger = logging.getLogger(__name__)

@lru_cache()
def get_persona_manager() -> PersonaManager:
    """
    Get a configured persona manager instance.

    This function provides dependency injection for the persona manager,
    creating an instance with the appropriate configuration.
    It uses lru_cache to ensure only one instance is created.

    Returns:
        A configured PersonaManager instance
    """
    # Access the global settings instance directly
    # settings = get_settings() # Removed this line

    # Create and initialize the manager
    try:
        # Load configuration path from settings
        config_path = settings.PERSONA_CONFIG_PATH

        # Create manager with auto-reload in development
        auto_reload = settings.ENVIRONMENT == "development"
        cache_ttl = settings.CACHE_TTL_SECONDS

        logger.info(f"Initializing PersonaManager with config path: {config_path}")
        manager = PersonaManager(
            config_path=config_path,
            auto_reload=auto_reload,
            cache_ttl_seconds=cache_ttl,
        )

        return manager
    except Exception as e:
        logger.error(f"Failed to initialize PersonaManager: {e}")
        # Return a default manager as fallback
        logger.warning("Falling back to default PersonaManager")
        return PersonaManager()

def get_persona_by_id(persona_id: Optional[str] = None):
    """
    Get a persona by ID using dependency injection.

    This function is designed to be used as a FastAPI dependency.

    Args:
        persona_id: The ID of the persona to get, or None for default

    Returns:
        The persona configuration
    """
    # Get the manager
    manager = get_persona_manager()

    # Get the persona
    return manager.get_persona(persona_id)
