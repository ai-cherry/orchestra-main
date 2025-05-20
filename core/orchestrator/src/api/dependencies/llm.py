"""
LLM client dependency for AI Orchestration System.

This module provides the dependency injection function for the LLM client,
supporting both traditional LangChain-based clients and Phidata/Agno models
with Portkey integration.
"""

import logging
import os
from functools import lru_cache
from typing import Union, Any, Optional

from packages.shared.src.llm_client.interface import LLMClient
from core.orchestrator.src.config.settings import get_settings, Settings

# Configure logging
logger = logging.getLogger(__name__)


@lru_cache()
def get_llm_client() -> Any:  # Return type could be LLMClient or an Agno model
    """
    Get the LLM client instance.

    Returns an initialized LLM model, using the Phidata/Agno implementation with
    Portkey integration if available, or falling back to the legacy PortkeyClient.

    Returns:
        An initialized LLM client or model
    """
    settings = get_settings()
    use_phidata_models = use_phidata_implementation(settings)

    if use_phidata_models:
        logger.info("Using Phidata/Agno LLM models with Portkey integration")
        return get_phidata_llm_model(settings)

    # Legacy path - try to load the real Portkey client first
    try:
        # Import separately to catch import errors specifically
        from packages.shared.src.llm_client.portkey_client import PortkeyClient

        logger.info("Using legacy PortkeyClient")
        return PortkeyClient(settings)

    except ImportError as e:
        # Fall back to mock client if the real client can't be loaded
        logger.warning(f"Failed to import PortkeyClient: {e}")
        logger.info("Falling back to MockPortkeyClient")

        from packages.shared.src.llm_client.mock_portkey_client import MockPortkeyClient

        return MockPortkeyClient(settings)

    except Exception as e:
        # Handle other initialization errors
        logger.error(f"Error initializing PortkeyClient: {e}")
        logger.info("Falling back to MockPortkeyClient")

        from packages.shared.src.llm_client.mock_portkey_client import MockPortkeyClient

        return MockPortkeyClient(settings)


def use_phidata_implementation(settings: Settings) -> bool:
    """
    Determine whether to use the Phidata/Agno implementation.

    This can be controlled through environment variables or settings.

    Args:
        settings: Application settings

    Returns:
        Boolean indicating whether to use Phidata implementation
    """
    # Check if an environment variable is set to disable Phidata implementation
    if os.environ.get("USE_LEGACY_LLM_CLIENT", "").lower() in ("true", "1", "yes"):
        return False

    # Check if required packages are available
    try:
        import agno
        import portkey_ai

        return True
    except ImportError:
        logger.warning("Phidata/Agno packages not available, using legacy LLM client")
        return False


def get_phidata_llm_model(settings: Settings) -> Any:
    """
    Get a Phidata/Agno LLM model instance with Portkey integration.

    Args:
        settings: Application settings

    Returns:
        An initialized Phidata/Agno LLM model
    """
    # Determine which provider to use based on settings
    provider = getattr(settings, "PREFERRED_LLM_PROVIDER", "openrouter").lower()

    try:
        if provider == "openai":
            from packages.llm.src.models.openai import create_openai_model

            return create_openai_model(settings)

        elif provider == "anthropic":
            from packages.llm.src.models.anthropic import create_anthropic_model

            return create_anthropic_model(settings)

        elif provider == "openrouter" or provider == "":
            from packages.llm.src.models.openrouter import create_openrouter_model

            return create_openrouter_model(settings)

        else:
            # Default to OpenRouter for unknown providers
            logger.warning(f"Unknown provider '{provider}', defaulting to OpenRouter")
            from packages.llm.src.models.openrouter import create_openrouter_model

            return create_openrouter_model(settings)

    except Exception as e:
        logger.error(f"Error initializing Phidata/Agno model: {e}")
        logger.info("Falling back to legacy PortkeyClient")

        # Fall back to legacy client
        from packages.shared.src.llm_client.portkey_client import PortkeyClient

        return PortkeyClient(settings)
