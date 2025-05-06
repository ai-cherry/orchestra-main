"""
PromptBuilder module for the AI Orchestration System.

This module provides functionality for dynamically constructing prompts
based on persona traits, memory context, and specific requirements.
"""

from .prompt_builder import PromptBuilder, PromptFormat
from .formatters import (
    PromptFormatter,
    TraitBasedFormatter,
    ToneFormatter,
    MemoryContextFormatter,
    get_formatter_for_persona,
)
from .templates import (
    PromptTemplate,
    TemplateLibrary,
    get_template_library,
    get_template_for_persona,
)
from .traits_processor import (
    TraitsProcessor,
    get_traits_processor,
    process_persona_traits,
)

__all__ = [
    # Main components
    "PromptBuilder",
    "PromptFormat",
    # Formatters
    "PromptFormatter",
    "TraitBasedFormatter",
    "ToneFormatter",
    "MemoryContextFormatter",
    "get_formatter_for_persona",
    # Templates
    "PromptTemplate",
    "TemplateLibrary",
    "get_template_library",
    "get_template_for_persona",
    # Traits processing
    "TraitsProcessor",
    "get_traits_processor",
    "process_persona_traits",
]
