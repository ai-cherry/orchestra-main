"""
PromptBuilder dependency for the AI Orchestration System.

This module provides FastAPI dependencies for the PromptBuilder
which is responsible for creating dynamic, persona-specific prompts.
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import Depends

from packages.shared.src.models.base_models import MemoryItem, PersonaConfig
from packages.shared.src.prompt_builder import PromptBuilder, PromptFormat

# Configure logging
logger = logging.getLogger(__name__)


@lru_cache()
def get_prompt_builder() -> PromptBuilder:
    """
    Get a PromptBuilder instance.

    Returns a cached instance of the PromptBuilder for efficient access.

    Returns:
        PromptBuilder: A PromptBuilder instance
    """
    logger.debug("Creating PromptBuilder instance")
    return PromptBuilder()


def build_prompt_for_persona(
    persona: PersonaConfig,
    user_input: str,
    history_items: Optional[list[MemoryItem]] = None,
    additional_context: Optional[Dict[str, Any]] = None,
    builder: PromptBuilder = Depends(get_prompt_builder),
) -> list[Dict[str, str]]:
    """
    Build a prompt for the given persona.

    This function creates a complete prompt based on the persona configuration,
    including its traits, conversation history, and the current user input.

    Args:
        persona: The persona configuration to use
        user_input: The current user input
        history_items: Previous conversation history items (optional)
        additional_context: Any additional context to include (optional)
        builder: PromptBuilder instance (injected dependency)

    Returns:
        The constructed prompt in chat format (list of message dictionaries)
    """
    logger.debug(f"Building prompt for persona: {persona.name}")

    # Use PromptBuilder to create a prompt
    prompt = builder.build_prompt(
        persona=persona,
        user_input=user_input,
        history_items=history_items,
        format=PromptFormat.CHAT,
        additional_context=additional_context,
    )

    return prompt
