"""
Portkey integration for Phidata/Agno LLM models.

This module provides helper functions to integrate Portkey with Phidata/Agno LLM models,
enabling the use of Portkey's routing, observability, and fallback capabilities.
"""

import os
import logging
from typing import Dict, Any, Optional, Union, Type, TypeVar

import portkey_ai
from core.orchestrator.src.config.settings import Settings
from .config import get_provider_config, LLMProviderConfig

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for model classes
T = TypeVar("T")


def create_portkey_headers(
    api_key: str,
    provider: str,
    virtual_key: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Create headers for Portkey API with proper authentication.

    Args:
        api_key: Portkey API key
        provider: Provider name (e.g., 'openai', 'anthropic')
        virtual_key: Optional Portkey virtual key
        trace_id: Optional trace ID for request tracking

    Returns:
        Dictionary of headers for Portkey API
    """
    header_kwargs = {
        "api_key": api_key,
        "provider": provider,
    }

    # Add virtual key if available
    if virtual_key:
        header_kwargs["virtual_key"] = virtual_key

    # Add trace ID if available
    if trace_id:
        header_kwargs["trace_id"] = trace_id

    try:
        return portkey_ai.createHeaders(**header_kwargs)
    except Exception as e:
        logger.error(f"Error creating Portkey headers: {e}")
        # Return basic headers as fallback
        return {
            "x-portkey-api-key": api_key,
            "x-portkey-provider": provider,
            **({"x-portkey-virtual-key": virtual_key} if virtual_key else {}),
            **({"x-portkey-trace-id": trace_id} if trace_id else {}),
        }


def configure_phidata_model(model_class: Type[T], config: LLMProviderConfig) -> T:
    """
    Configure a Phidata/Agno model with Portkey integration.

    Args:
        model_class: The Phidata/Agno model class
        config: Provider configuration

    Returns:
        Configured Phidata/Agno model instance
    """
    # Create headers with Portkey authentication
    headers = create_portkey_headers(
        api_key=config.api_key, provider=config.provider, virtual_key=config.virtual_key
    )

    # Common initialization parameters
    model_args = {"base_url": config.base_url, "default_headers": headers}

    # Add any provider-specific parameters
    model_args.update(config.extra_params)

    # Initialize and return the model
    try:
        return model_class(**model_args)
    except Exception as e:
        logger.error(f"Error initializing {model_class.__name__}: {e}")
        raise


def configure_model_from_settings(
    model_class: Type[T], settings: Settings, provider: str
) -> T:
    """
    Configure a model using application settings.

    Args:
        model_class: The model class to instantiate
        settings: Application settings
        provider: Provider name

    Returns:
        Configured model instance
    """
    # Get provider configuration
    config = get_provider_config(settings, provider)

    # Configure and return the model
    return configure_phidata_model(model_class, config)
