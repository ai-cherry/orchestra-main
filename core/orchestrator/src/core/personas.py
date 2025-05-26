"""
Personas module for AI Orchestration System.

This module provides functionality for managing AI agent personas,
including loading persona configurations and formatting responses.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PersonaConfig:
    """
    Configuration for an AI persona.

    This class defines the parameters that shape an AI agent's
    persona, including its name, description, and prompt template.
    """

    name: str
    description: str = ""
    prompt_template: str = "{input}"
    background: str = ""
    interaction_style: str = "helpful"
    traits: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PersonaProcessor:
    """
    Processor for persona-specific operations.

    This class handles operations specific to a persona,
    such as applying templates to format responses.
    """

    def __init__(self, persona: PersonaConfig):
        """
        Initialize a persona processor.

        Args:
            persona: The persona configuration
        """
        self.persona = persona

    def format_response(self, response_text: str, **kwargs: Any) -> str:
        """
        Format a response according to the persona's template.

        Args:
            response_text: The raw response text
            **kwargs: Additional format variables

        Returns:
            The formatted response
        """
        # Combine response with additional kwargs
        format_vars = {"input": response_text, **kwargs}

        try:
            # Use string.format to apply the template
            return self.persona.prompt_template.format(**format_vars)
        except KeyError as e:
            logger.warning(f"Missing format variable in template: {e}")
            # Fallback to basic substitution
            return self.persona.prompt_template.replace("{input}", response_text)
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            # Last resort fallback
            return response_text


class PersonaLoader:
    """
    Loader for persona configurations.

    This class handles loading persona configurations from a YAML file
    and provides methods for accessing personas.
    """

    def __init__(self, config_path: str):
        """
        Initialize a persona loader.

        Args:
            config_path: Path to the persona configuration YAML file
        """
        self.config_path = config_path
        self.personas: Dict[str, PersonaConfig] = {}
        self.default_persona_id: str = "default"
        self._load_personas()

    def _load_personas(self) -> None:
        """Load personas from the configuration file."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Persona config file not found: {self.config_path}")
                self._create_default_persona()
                return

            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)

            if not config or not isinstance(config, dict):
                logger.warning(f"Invalid persona config file: {self.config_path}")
                self._create_default_persona()
                return

            # Get default persona ID
            self.default_persona_id = config.get("default_persona_id", "default")

            # Load personas
            persona_configs = config.get("personas", {})
            if not persona_configs:
                logger.warning(f"No personas found in config file: {self.config_path}")
                self._create_default_persona()
                return

            # Parse each persona
            for persona_id, persona_data in persona_configs.items():
                try:
                    # Extract traits list if present
                    traits = persona_data.get("traits", [])
                    if isinstance(traits, list):
                        persona_data["traits"] = traits
                    else:
                        persona_data["traits"] = []

                    # Create persona config
                    persona = PersonaConfig(**persona_data)
                    self.personas[persona_id] = persona
                    logger.debug(f"Loaded persona: {persona.name}")
                except Exception as e:
                    logger.error(f"Failed to load persona {persona_id}: {e}")

            logger.info(f"Loaded {len(self.personas)} personas from {self.config_path}")

            # Ensure default persona exists
            if self.default_persona_id not in self.personas:
                logger.warning(
                    f"Default persona '{self.default_persona_id}' not found, creating it"
                )
                self._create_default_persona()
        except Exception as e:
            logger.error(f"Failed to load personas from {self.config_path}: {e}")
            self._create_default_persona()

    def _create_default_persona(self) -> None:
        """Create a default persona if none exists."""
        self.default_persona_id = "default"
        self.personas[self.default_persona_id] = PersonaConfig(
            name="Assistant",
            description="A helpful, knowledgeable assistant",
            prompt_template="{input}",
            interaction_style="helpful",
            traits=["helpful", "knowledgeable"],
        )
        logger.info("Created default persona")

    def load_persona(self, persona_id: Optional[str] = None) -> PersonaConfig:
        """
        Load a persona by ID.

        Args:
            persona_id: The ID of the persona to load, or None for default

        Returns:
            The persona configuration
        """
        # Use default if no ID provided
        if persona_id is None:
            persona_id = self.default_persona_id

        # Try to get the persona by ID
        persona = self.personas.get(persona_id)
        if persona:
            return persona

        # Try case-insensitive lookup by name
        persona_id_lower = persona_id.lower() if persona_id else ""
        for pid, p in self.personas.items():
            if p.name.lower() == persona_id_lower:
                return p

        # Fall back to default
        logger.warning(f"Persona '{persona_id}' not found, using default")
        return self.personas[self.default_persona_id]

    def get_all_personas(self) -> Dict[str, PersonaConfig]:
        """
        Get all available personas.

        Returns:
            Dictionary mapping persona IDs to their configurations
        """
        return dict(self.personas)


class PersonaManager:
    """
    Manager for persona operations.

    This class provides a unified interface to persona operations,
    including loading, processing, and applying personas.
    """

    def __init__(self, config_path: str):
        """
        Initialize the persona manager.

        Args:
            config_path: Path to the persona configuration YAML file
        """
        self._loader = PersonaLoader(config_path)
        self._processors: Dict[str, PersonaProcessor] = {}
        logger.info(f"PersonaManager initialized with config: {config_path}")

    def get_persona(self, persona_id: Optional[str] = None) -> PersonaConfig:
        """
        Get a persona by ID.

        Args:
            persona_id: The ID of the persona to get, or None for default

        Returns:
            The persona configuration
        """
        return self._loader.load_persona(persona_id)

    def get_processor(self, persona_id: Optional[str] = None) -> PersonaProcessor:
        """
        Get a processor for a persona.

        Args:
            persona_id: The ID of the persona to get a processor for, or None for default

        Returns:
            A processor for the persona
        """
        # Get persona
        persona = self.get_persona(persona_id)

        # Create processor if needed
        if persona.name not in self._processors:
            self._processors[persona.name] = PersonaProcessor(persona)

        return self._processors[persona.name]

    def format_response(
        self, response_text: str, persona_id: Optional[str] = None, **kwargs: Any
    ) -> str:
        """
        Format a response according to a persona's template.

        Args:
            response_text: The raw response text
            persona_id: The ID of the persona to use, or None for default
            **kwargs: Additional format variables

        Returns:
            The formatted response
        """
        processor = self.get_processor(persona_id)
        return processor.format_response(response_text, **kwargs)

    def get_all_personas(self) -> Dict[str, PersonaConfig]:
        """
        Get all available personas.

        Returns:
            Dictionary mapping persona IDs to their configurations
        """
        return self._loader.get_all_personas()


# Global persona manager instance
_persona_manager = None


def get_persona_manager(config_path: Optional[str] = None) -> PersonaManager:
    """
    Get the global persona manager instance.

    Args:
        config_path: Optional path to the persona configuration YAML file

    Returns:
        The persona manager instance
    """
    global _persona_manager

    if _persona_manager is None:
        # Use provided config path or get from central settings
        if config_path is None:
            from core.orchestrator.src.config.config import get_settings

            config_path = get_settings().PERSONA_CONFIG_PATH

        _persona_manager = PersonaManager(config_path)

    return _persona_manager
