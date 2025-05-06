"""
Enhanced Persona Manager for AI Orchestration System.

This module provides an extension to the base PersonaManager with support
for template-based persona definitions and response formatting.
"""

import logging
import string
from typing import Dict, List, Optional, Any, Union, Callable

from core.orchestrator.src.personas.loader import PersonaManager
from core.orchestrator.src.config.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class PersonaTemplate:
    """
    Persona template for formatting responses.

    This class handles template parsing and application for persona-specific
    response formatting, supporting both simple string templates and
    more complex formatting patterns.
    """

    def __init__(self, template: str):
        """
        Initialize a persona template.

        Args:
            template: The template string with {input} placeholder
        """
        self.template = template
        self._validate_template()

    def _validate_template(self) -> None:
        """
        Validate the template format.

        Raises:
            ValueError: If the template is invalid
        """
        if not self.template:
            raise ValueError("Template cannot be empty")

        if "{input}" not in self.template:
            raise ValueError("Template must contain {input} placeholder")

    def format(self, input_text: str, **kwargs: Any) -> str:
        """
        Format input text using the template.

        Args:
            input_text: The input text to format
            **kwargs: Additional format variables

        Returns:
            The formatted text
        """
        # Combine input with additional kwargs
        format_vars = {"input": input_text, **kwargs}

        try:
            # Use string.format to apply the template
            return self.template.format(**format_vars)
        except KeyError as e:
            logger.warning(f"Missing format variable in template: {e}")
            # Fallback: just substitute input if other vars are missing
            return self.template.replace("{input}", input_text)
        except Exception as e:
            logger.error(f"Error formatting template: {e}")
            # Last resort fallback
            return input_text


class EnhancedPersonaConfig:
    """
    Enhanced persona configuration with template support.

    This class extends the base PersonaConfig with additional fields
    and functionality for template-based response formatting.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        prompt_template: Optional[str] = None,
        background: str = "",
        interaction_style: str = "helpful",
        traits: Union[List[str], Dict[str, int]] = None,
        preferred_agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an enhanced persona configuration.

        Args:
            name: The name of the persona
            description: Brief description of the persona
            prompt_template: Template for formatting responses
            background: Detailed background/history
            interaction_style: Style descriptor
            traits: List of traits or trait score mapping
            preferred_agent_type: The agent type best suited for this persona
            metadata: Additional metadata
        """
        self.name = name
        self.description = description
        self.background = background
        self.interaction_style = interaction_style

        # Convert list traits to dict if needed
        if traits is None:
            self.traits = []
        elif isinstance(traits, list):
            self.traits = traits
        else:
            # If traits is a dict, convert top traits to list
            self.traits = sorted(traits.keys(), key=lambda k: traits[k], reverse=True)
            self.trait_scores = traits

        # Template handling
        self.prompt_template = prompt_template or "Response: {input}"
        self._template = PersonaTemplate(self.prompt_template)

        # Agent type preference
        self.preferred_agent_type = preferred_agent_type

        # Additional metadata
        self.metadata = metadata or {}

    def format_response(self, response_text: str, **kwargs: Any) -> str:
        """
        Format a response according to the persona's template.

        Args:
            response_text: The raw response text
            **kwargs: Additional variables for template formatting

        Returns:
            The formatted response
        """
        return self._template.format(response_text, **kwargs)


class EnhancedPersonaManager(PersonaManager):
    """
    Enhanced manager for template-based personas.

    This class extends the base PersonaManager with support for template-based
    persona definitions and response formatting capabilities.
    """

    def __init__(
        self,
        config_path: str = None,
        auto_reload: bool = False,
        cache_ttl_seconds: int = 300,
    ):
        """
        Initialize the enhanced persona manager.

        Args:
            config_path: Path to the persona configuration YAML file
            auto_reload: Whether to automatically reload personas
            cache_ttl_seconds: Time-to-live for cached personas
        """
        # Initialize base manager
        super().__init__(config_path, auto_reload, cache_ttl_seconds)

        # Enhanced persona configurations
        self._enhanced_personas: Dict[str, EnhancedPersonaConfig] = {}

        # Agent type mappings
        self._agent_type_mappings: Dict[str, str] = {}

        # Load enhanced personas (performed lazily on first request)
        self._last_loaded = 0  # Force load on first access

        logger.info(
            "EnhancedPersonaManager initialized - personas will be loaded on first access"
        )

    def get_enhanced_persona(
        self, persona_id: Optional[str] = None
    ) -> EnhancedPersonaConfig:
        """
        Get an enhanced persona configuration by ID.

        Args:
            persona_id: The ID of the persona to get, or None for default

        Returns:
            The enhanced persona configuration

        Raises:
            KeyError: If the persona ID is not found
        """
        # Auto-reload if needed
        if self._auto_reload and self._config_path and self._should_reload():
            self._load_enhanced_personas()

        # Use default if no ID provided
        if persona_id is None:
            persona_id = self._default_id

        # Try to get the persona by ID
        if persona_id in self._enhanced_personas:
            return self._enhanced_personas[persona_id]

        # Try case-insensitive lookup by name
        persona_id_lower = persona_id.lower() if persona_id else ""
        for pid, persona in self._enhanced_personas.items():
            if persona.name.lower() == persona_id_lower:
                return persona

        # If not found in enhanced personas, try to adapt from base persona
        try:
            base_persona = self.get_persona(persona_id)

            # Convert base persona to enhanced
            enhanced = EnhancedPersonaConfig(
                name=base_persona.name,
                description=base_persona.background[:100],
                background=base_persona.background,
                interaction_style=base_persona.interaction_style,
                traits=base_persona.traits,
                # Default template
                prompt_template="Response: {input}",
            )

            # Cache for future use
            self._enhanced_personas[persona_id] = enhanced

            return enhanced
        except KeyError:
            # Create a simple default if nothing else works
            logger.warning(f"Creating basic default persona for '{persona_id}'")

            return EnhancedPersonaConfig(
                name=persona_id or "Default",
                description="Automatically generated persona",
                prompt_template="Response: {input}",
            )

    def format_response(
        self, persona_id: Optional[str], response_text: str, **kwargs: Any
    ) -> str:
        """
        Format a response according to a persona's template.

        Args:
            persona_id: The ID of the persona to use, or None for default
            response_text: The raw response text
            **kwargs: Additional variables for template formatting

        Returns:
            The formatted response
        """
        persona = self.get_enhanced_persona(persona_id)
        return persona.format_response(response_text, **kwargs)

    def get_preferred_agent_type(
        self, persona_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the preferred agent type for a persona.

        Args:
            persona_id: The ID of the persona, or None for default

        Returns:
            The preferred agent type, or None if not specified
        """
        persona = self.get_enhanced_persona(persona_id)
        return persona.preferred_agent_type

    def get_all_enhanced_personas(self) -> Dict[str, EnhancedPersonaConfig]:
        """
        Get all available enhanced personas.

        Returns:
            Dictionary mapping persona IDs to their enhanced configurations
        """
        # Auto-reload if needed
        if self._auto_reload and self._config_path and self._should_reload():
            self._load_enhanced_personas()

        # Return a copy to prevent modification
        return dict(self._enhanced_personas)

    def reload_personas(self) -> bool:
        """
        Force reload all personas from configuration.

        Returns:
            True if reload was successful
        """
        result = super().reload_personas()
        self._load_enhanced_personas(force=True)
        return result

    def _should_reload(self) -> bool:
        """
        Check if personas should be reloaded.

        Returns:
            True if reload is needed
        """
        import time

        return time.time() - self._last_loaded > self._cache_ttl_seconds

    def _load_enhanced_personas(self, force: bool = False) -> bool:
        """
        Load enhanced personas from configuration.

        Args:
            force: Whether to force reload

        Returns:
            True if load was successful
        """
        import yaml
        from pathlib import Path

        # Skip if not forced and cache is still valid
        if not force and not self._should_reload():
            return True

        # Start with empty enhanced personas
        enhanced_personas = {}

        # Try to load from config file if provided
        if self._config_path:
            try:
                # Get absolute path
                config_path = Path(self._config_path).resolve()

                # Check if file exists
                if not config_path.exists():
                    logger.warning(f"Persona config file not found: {config_path}")
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
                            # Check if persona has a prompt template
                            if "prompt_template" in persona_data:
                                # Create enhanced persona
                                persona = EnhancedPersonaConfig(**persona_data)

                                # Add to enhanced personas dictionary
                                enhanced_personas[persona_id] = persona

                                # Check for agent type mapping
                                if persona.preferred_agent_type:
                                    self._agent_type_mappings[persona_id] = (
                                        persona.preferred_agent_type
                                    )

                                logger.debug(f"Loaded enhanced persona: {persona.name}")
                        except Exception as e:
                            logger.error(
                                f"Failed to load enhanced persona {persona_id}: {e}"
                            )

                    logger.info(
                        f"Loaded {len(enhanced_personas)} enhanced personas from {config_path}"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to load enhanced personas from {self._config_path}: {e}"
                )
                return False

        # Update enhanced personas dictionary
        self._enhanced_personas = enhanced_personas

        # Create enhanced versions of base personas if they don't exist
        for persona_id, base_persona in self._personas.items():
            if persona_id not in self._enhanced_personas:
                try:
                    # Convert base persona to enhanced
                    enhanced = EnhancedPersonaConfig(
                        name=base_persona.name,
                        description=(
                            base_persona.background[:100]
                            if base_persona.background
                            else ""
                        ),
                        background=base_persona.background or "",
                        interaction_style=base_persona.interaction_style or "helpful",
                        traits=base_persona.traits or [],
                        # Default template
                        prompt_template="Response: {input}",
                    )

                    # Add to enhanced personas dictionary
                    self._enhanced_personas[persona_id] = enhanced
                except Exception as e:
                    logger.error(
                        f"Failed to convert base persona {persona_id} to enhanced: {e}"
                    )

        return True


# Global enhanced persona manager instance
_enhanced_persona_manager = None


def get_enhanced_persona_manager() -> EnhancedPersonaManager:
    """
    Get the global enhanced persona manager instance.

    This function provides a simple dependency injection mechanism
    for accessing the enhanced persona manager throughout the application.

    Returns:
        The global EnhancedPersonaManager instance
    """
    global _enhanced_persona_manager

    if _enhanced_persona_manager is None:
        # Get settings
        settings = get_settings()

        # Create manager with auto-reload in development
        auto_reload = settings.ENVIRONMENT == "development"
        config_path = settings.PERSONA_CONFIG_PATH
        cache_ttl = settings.CACHE_TTL_SECONDS

        _enhanced_persona_manager = EnhancedPersonaManager(
            config_path=config_path,
            auto_reload=auto_reload,
            cache_ttl_seconds=cache_ttl,
        )

    return _enhanced_persona_manager
