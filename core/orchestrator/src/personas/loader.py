"""
Persona loader module for AI Orchestration System.

This module provides functionality for loading and managing persona configurations
from YAML files. It ensures that personas are properly validated and accessible
throughout the application.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

import yaml

from packages.shared.src.models.base_models import PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)

# Default persona for fallback
DEFAULT_PERSONA = PersonaConfig(
    name="Default",
    description="A standard default persona.",  # Added missing description
    background="Default persona for when no specific persona is selected or available.",
    interaction_style="Helpful and informative",
    traits={"sarcasm": 10, "creativity": 50, "strategy": 50},
)

# Dictionary of fallback personas
FALLBACK_PERSONAS = {
    "default": DEFAULT_PERSONA,
    "cherry": PersonaConfig(
        name="Cherry",
        description="A cheerful and optimistic persona.",  # Added missing description
        background="Cheerful and optimistic persona with a focus on positive thinking.",
        interaction_style="Upbeat and encouraging",
        traits={"sarcasm": 5, "creativity": 80, "strategy": 40},
    ),
    "sage": PersonaConfig(
        name="Sage",
        description="A wise and thoughtful persona.",  # Added missing description
        background="Wise and thoughtful persona with a focus on careful analysis.",
        interaction_style="Deliberate and measured",
        traits={"sarcasm": 5, "creativity": 40, "strategy": 90},
    ),
    "wit": PersonaConfig(
        name="Wit",
        description="A clever and quick-witted persona.",  # Added missing description
        background="Clever and quick-witted persona with a sharp sense of humor.",
        interaction_style="Clever and playful",
        traits={"sarcasm": 70, "creativity": 85, "strategy": 60},
    ),
}


class PersonaManager:
    """
    Manager for loading and accessing persona configurations.

    This class handles loading persona definitions from configuration files,
    validating them, and providing access to them throughout the application.
    It supports automatic reloading of personas in development environments.
    """

    def __init__(
        self,
        config_path: str = None,
        auto_reload: bool = False,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize the persona manager.

        Args:
            config_path: Path to the persona configuration YAML file
            auto_reload: Whether to automatically reload personas when they expire
            cache_ttl_seconds: Time-to-live for cached personas in seconds
        """
        self._config_path = config_path
        self._personas: Dict[str, PersonaConfig] = {}
        self._default_id = "default"
        self._last_loaded = 0
        self._auto_reload = auto_reload
        self._cache_ttl_seconds = cache_ttl_seconds

        # Load personas immediately
        self._load_personas()

        logger.info(
            f"PersonaManager initialized with {len(self._personas)} personas, "
            f"default: {self._default_id}, auto_reload: {auto_reload}"
        )

    def get_persona(self, persona_id: Optional[str] = None) -> PersonaConfig:
        """
        Get a persona by ID.

        Args:
            persona_id: The ID of the persona to get, or None for default

        Returns:
            The persona configuration

        Raises:
            KeyError: If the persona ID is not found and no default is available
        """
        # Auto-reload if needed
        if (
            self._auto_reload
            and self._config_path
            and time.time() - self._last_loaded > self._cache_ttl_seconds
        ):
            self._load_personas()

        # Use default if no ID provided
        if persona_id is None:
            persona_id = self._default_id

        # Try to get the persona by ID
        if persona_id in self._personas:
            return self._personas[persona_id]

        # Try case-insensitive lookup by name
        persona_id_lower = persona_id.lower()
        for pid, persona in self._personas.items():
            if persona.name.lower() == persona_id_lower:
                return persona

        # Fall back to default
        if self._default_id in self._personas:
            logger.warning(
                f"Persona '{persona_id}' not found, using default: {self._default_id}"
            )
            return self._personas[self._default_id]

        # If still not found, use fallback
        if "default" in FALLBACK_PERSONAS:
            logger.warning("No personas available, using fallback: default")
            return FALLBACK_PERSONAS["default"]

        # If all else fails, raise an error
        raise KeyError(f"Persona '{persona_id}' not found and no default available")

    def get_all_personas(self) -> Dict[str, PersonaConfig]:
        """
        Get all available personas.

        Returns:
            Dictionary mapping persona IDs to their configurations
        """
        # Auto-reload if needed
        if (
            self._auto_reload
            and self._config_path
            and time.time() - self._last_loaded > self._cache_ttl_seconds
        ):
            self._load_personas()

        # Return a copy to prevent modification
        return dict(self._personas)

    def get_default_persona_id(self) -> str:
        """
        Get the default persona ID.

        Returns:
            The ID of the default persona
        """
        return self._default_id

    def reload_personas(self) -> bool:
        """
        Force reload personas from configuration.

        Returns:
            True if reload was successful, False otherwise
        """
        return self._load_personas(force=True)

    def _load_personas(self, force: bool = False) -> bool:
        """
        Load personas from configuration.

        Args:
            force: Whether to force reload even if the cache is still valid

        Returns:
            True if load was successful, False otherwise
        """
        # Skip if not forced and cache is still valid
        if (
            not force
            and self._last_loaded > 0
            and time.time() - self._last_loaded <= self._cache_ttl_seconds
        ):
            return True

        # Start with fallback personas
        personas_dict = dict(FALLBACK_PERSONAS)

        # Try to load from config file if provided
        if self._config_path:
            try:
                # Get absolute path
                config_path = Path(self._config_path).resolve()

                # Check if file exists
                if not config_path.exists():
                    logger.warning(f"Persona config file not found: {config_path}")
                    self._last_loaded = time.time()
                    return False

                # Load and parse YAML
                with open(config_path, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}

                # Extract personas section
                yaml_personas = yaml_data.get("personas", {})

                if not yaml_personas:
                    logger.warning(f"No personas found in config file: {config_path}")
                else:
                    # Parse each persona
                    for persona_id, persona_data in yaml_personas.items():
                        try:
                            # Create and validate the persona
                            persona = PersonaConfig(**persona_data)

                            # Add to personas dictionary
                            personas_dict[persona_id] = persona
                            logger.debug(f"Loaded persona: {persona.name}")
                        except Exception as e:
                            logger.error(f"Failed to load persona {persona_id}: {e}")

                    # Get default persona ID
                    default_id = yaml_data.get("default_persona_id", "default")
                    if default_id in personas_dict:
                        self._default_id = default_id

                    logger.info(
                        f"Loaded {len(yaml_personas)} personas from {config_path}"
                    )
            except Exception as e:
                logger.error(f"Failed to load personas from {self._config_path}: {e}")
                self._last_loaded = time.time()
                return False

        # Update personas dictionary
        self._personas = personas_dict
        self._last_loaded = time.time()

        # Ensure default persona exists
        if self._default_id not in self._personas and self._personas:
            # Pick first persona as default
            self._default_id = next(iter(self._personas))
            logger.warning(
                f"Default persona ID not found, using {self._default_id} as default"
            )

        return True
