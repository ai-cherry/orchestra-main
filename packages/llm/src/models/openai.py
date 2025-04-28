"""
OpenAI model implementation with Portkey integration.

This module provides factory functions for creating OpenAI models via Phidata/Agno
with Portkey integration for routing, observability, and fallbacks.
"""

import logging
from typing import Optional, Dict, Any

from agno.models.openai import OpenAIChat
from core.orchestrator.src.config.settings import Settings

from ..portkey_integration import configure_model_from_settings
from ..config import get_model_name_for_provider

# Configure logging
logger = logging.getLogger(__name__)


def create_openai_model(
    settings: Settings,
    model_name: Optional[str] = None,
    **kwargs
) -> OpenAIChat:
    """
    Create OpenAI model with Portkey integration.
    
    Args:
        settings: Application settings
        model_name: Optional model name override
        **kwargs: Additional model-specific parameters
        
    Returns:
        Configured OpenAI model
    """
    provider = "openai"
    
    try:
        # Instantiate the model with Portkey configuration
        model = configure_model_from_settings(OpenAIChat, settings, provider)
        
        # Determine model name to use (if provided or use default from settings)
        effective_model = model_name
        if not effective_model:
            effective_model = settings.DEFAULT_LLM_MODEL_FALLBACK_OPENAI or "gpt-4o"
        
        # Format the model name for OpenAI
        formatted_model = get_model_name_for_provider(effective_model, provider)
        
        # Set default parameters
        model.model = formatted_model
                
        # Set additional parameters if provided
        for key, value in kwargs.items():
            setattr(model, key, value)
        
        logger.info(f"Successfully configured OpenAI model: {formatted_model} with Portkey integration")
        return model
        
    except Exception as e:
        logger.error(f"Error creating OpenAI model: {e}")
        raise
