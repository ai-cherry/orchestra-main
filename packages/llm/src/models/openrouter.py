"""
OpenRouter model implementation with Portkey integration.

This module provides factory functions for creating OpenRouter models via Phidata/Agno
with Portkey integration for routing, observability, and fallbacks.
"""

import logging
from typing import Optional, Dict, Any

from agno.models.openrouter import OpenRouter
from core.orchestrator.src.config.settings import Settings

from ..portkey_integration import configure_model_from_settings
from ..config import get_model_name_for_provider

# Configure logging
logger = logging.getLogger(__name__)


def create_openrouter_model(
    settings: Settings, model_name: Optional[str] = None, **kwargs
) -> OpenRouter:
    """
    Create OpenRouter model with Portkey integration.

    Args:
        settings: Application settings
        model_name: Optional model name override
        **kwargs: Additional model-specific parameters

    Returns:
        Configured OpenRouter model
    """
    provider = "openrouter"

    try:
        # Instantiate the model with Portkey configuration
        model = configure_model_from_settings(OpenRouter, settings, provider)

        # Determine model name to use (if provided or use default from settings)
        effective_model = model_name
        if not effective_model:
            effective_model = settings.DEFAULT_LLM_MODEL_PRIMARY or "openai/gpt-4o"

        # Format the model name for OpenRouter (should already include provider prefix)
        formatted_model = effective_model
        if "/" not in formatted_model:
            # Use openai as default provider prefix for OpenRouter if not specified
            formatted_model = f"openai/{formatted_model}"

        # Set default parameters
        model.model = formatted_model

        # Pass through OpenRouter specific HTTP headers
        if hasattr(settings, "get_openrouter_headers"):
            openrouter_headers = settings.get_openrouter_headers()
            # Merge with existing headers if any
            if hasattr(model, "default_headers"):
                model.default_headers.update(openrouter_headers)
            else:
                model.default_headers = openrouter_headers

        # Set additional parameters if provided
        for key, value in kwargs.items():
            setattr(model, key, value)

        logger.info(
            f"Successfully configured OpenRouter model: {formatted_model} with Portkey integration"
        )
        return model

    except Exception as e:
        logger.error(f"Error creating OpenRouter model: {e}")
        raise
