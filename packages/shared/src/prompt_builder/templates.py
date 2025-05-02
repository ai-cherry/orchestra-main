"""
Prompt templates for the AI Orchestration System.

This module provides template definitions and management for different
persona types and use cases.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from functools import lru_cache

from packages.shared.src.models.base_models import PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


class PromptTemplate:
    """
    Base class for prompt templates.

    Templates define the structure and content of prompts for specific
    personas or use cases.
    """

    def __init__(self, template_id: str, template_text: str):
        """
        Initialize a prompt template.

        Args:
            template_id: Unique identifier for the template
            template_text: Template text with placeholders
        """
        self.template_id = template_id
        self.template_text = template_text

    def render(self, context: Dict[str, Any]) -> str:
        """
        Render the template with the given context.

        Args:
            context: Dictionary of values to fill in the template

        Returns:
            The rendered template text
        """
        try:
            return self.template_text.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context key in template: {e}")
            return self.template_text  # Return unformatted template as fallback
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return self.template_text


class TemplateLibrary:
    """
    Library of prompt templates.

    This class manages a collection of templates that can be used for
    different personas and use cases.
    """

    def __init__(self):
        """Initialize the template library."""
        self._templates: Dict[str, PromptTemplate] = {}
        self._template_definitions: Dict[str, Callable[[], PromptTemplate]] = {}
        self._initialize_template_definitions()

    @lru_cache(maxsize=32)
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID, lazily loading it if not already instantiated.
        
        Args:
            template_id: The template identifier
            
        Returns:
            The template, or None if not found
        """
        if template_id in self._template_definitions and template_id not in self._templates:
            self._templates[template_id] = self._template_definitions[template_id]()
        return self._templates.get(template_id)

    def add_template(self, template: PromptTemplate) -> None:
        """
        Add a template to the library.

        Args:
            template: The template to add
        """
        self._templates[template.template_id] = template

    def get_template_for_persona(self, persona: PersonaConfig) -> PromptTemplate:
        """
        Get the most appropriate template for the given persona.

        Args:
            persona: The persona configuration

        Returns:
            The best matching template
        """
        # Check if there's a template with the same ID as the persona name
        persona_id = persona.name.lower().replace(" ", "_")
        template = self.get_template(persona_id)
        if template:
            return template

        # Try to match based on persona traits or metadata
        if persona.traits:
            if "efficiency" in persona.traits and persona.traits["efficiency"] >= 0.7:
                template = self.get_template("efficient")
                if template:
                    return template

            if (
                "assertiveness" in persona.traits
                and persona.traits["assertiveness"] >= 0.7
            ):
                template = self.get_template("assertive")
                if template:
                    return template

        # Try to match based on persona description
        if (
            "cheerful" in persona.description.lower()
            or "energetic" in persona.description.lower()
        ):
            template = self.get_template("cheerful")
            if template:
                return template

        if (
            "wise" in persona.description.lower()
            or "thoughtful" in persona.description.lower()
        ):
            template = self.get_template("wise")
            if template:
                return template

        # Default to generic template
        return self.get_template("generic") or PromptTemplate(
            "fallback", "You are {name}, {description}."
        )

    def _initialize_template_definitions(self) -> None:
        """Initialize the library with template definitions for lazy loading."""
        # Generic template
        self._template_definitions['generic'] = lambda: PromptTemplate(
            "generic",
            "You are {name}, {description}. Respond to user queries in a helpful and informative manner."
        )
        
        # Persona-specific templates
        self._template_definitions['cherry'] = lambda: PromptTemplate(
            "cherry",
            "You are Cherry, a cheerful and energetic assistant. Your responses should be upbeat, positive, and enthusiastic. Use exclamation marks and show excitement about helping the user!"
        )
        
        self._template_definitions['sophia'] = lambda: PromptTemplate(
            "sophia",
            "You are Sophia, a wise and thoughtful assistant. Your responses should be considered, insightful, and show depth of thought. Take time to reflect on questions and provide nuanced perspectives."
        )
        
        self._template_definitions['gordon_gekko'] = lambda: PromptTemplate(
            "gordon_gekko",
            "You are Gordon Gekko, a ruthless efficiency expert who is blunt and results-obsessed. Be direct, skip pleasantries, and focus relentlessly on effectiveness and performance. Your goal is to push the user to succeed with tough love and brutal honesty."
        )
        
        # Trait-based templates
        self._template_definitions['efficient'] = lambda: PromptTemplate(
            "efficient",
            "You are {name}, {description}. Your communication style is highly efficient. Keep responses concise and direct, avoiding unnecessary elaboration. Focus on delivering value quickly and clearly."
        )
        
        self._template_definitions['assertive'] = lambda: PromptTemplate(
            "assertive",
            "You are {name}, {description}. Your communication style is confident and assertive. Make strong statements, give clear guidance, and don't hedge your advice. Be direct and authoritative when answering questions."
        )
        
        self._template_definitions['cheerful'] = lambda: PromptTemplate(
            "cheerful",
            "You are {name}, {description}. Your communication style is cheerful and upbeat. Use positive language, express enthusiasm, and maintain an energetic tone throughout your responses."
        )
        
        self._template_definitions['wise'] = lambda: PromptTemplate(
            "wise",
            "You are {name}, {description}. Your communication style reflects wisdom and thoughtfulness. Consider different perspectives, show depth in your analysis, and provide insights that demonstrate careful consideration."
        )


# Global instance for easy access
template_library = TemplateLibrary()


def get_template_library() -> TemplateLibrary:
    """
    Get the global template library instance.

    Returns:
        The template library
    """
    return template_library


def get_template_for_persona(persona: PersonaConfig) -> PromptTemplate:
    """
    Get the most appropriate template for the given persona.

    Args:
        persona: The persona configuration

    Returns:
        The best matching template
    """
    return template_library.get_template_for_persona(persona)
