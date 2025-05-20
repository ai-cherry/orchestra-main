"""
Anthropic model implementation with Portkey integration.

This module provides factory functions for creating Anthropic Claude models
via Phidata/Agno with Portkey integration for routing, observability, and fallbacks.
"""

import logging
from typing import Optional, Dict, Any

from agno.models.anthropic import Claude
from core.orchestrator.src.config.settings import Settings

from ..portkey_integration import configure_model_from_settings
from ..config import get_model_name_for_provider

# Configure logging
logger = logging.getLogger(__name__)


def create_anthropic_model(
    settings: Settings, model_name: Optional[str] = None, **kwargs
) -> Claude:
    """
    Create Anthropic Claude model with Portkey integration.

    Args:
        settings: Application settings
        model_name: Optional model name override
        **kwargs: Additional model-specific parameters

    Returns:
        Configured Anthropic Claude model
    """
    provider = "anthropic"

    try:
        # Instantiate the model with Portkey configuration
        model = configure_model_from_settings(Claude, settings, provider)

        # Determine model name to use (if provided or use default from settings)
        effective_model = model_name
        if not effective_model:
            effective_model = (
                settings.DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC
                or "claude-3-5-sonnet-20240620"
            )

        # Format the model name for Anthropic
        formatted_model = get_model_name_for_provider(effective_model, provider)

        # Set default parameters
        model.model = formatted_model

        # Anthropic-specific parameters
        model.max_tokens = kwargs.pop("max_tokens", 4096)

        # Set additional parameters if provided
        for key, value in kwargs.items():
            setattr(model, key, value)

        logger.info(
            f"Successfully configured Anthropic model: {formatted_model} with Portkey integration"
        )
        return model

    except Exception as e:
        logger.error(f"Error creating Anthropic model: {e}")
        raise
