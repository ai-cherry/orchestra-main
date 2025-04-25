"""
LLM client dependency for AI Orchestration System.

This module provides the dependency injection function for the LLM client.
"""

import logging
import os
from functools import lru_cache

from packages.shared.src.llm_client.interface import LLMClient
from core.orchestrator.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


@lru_cache()
def get_llm_client() -> LLMClient:
    """
    Get the LLM client instance.
    
    Returns an initialized LLM client, using the PortkeyClient if available,
    or falling back to a MockPortkeyClient for development environments.
    
    Returns:
        An initialized LLM client
    """
    settings = get_settings()
    
    # Try to load the real Portkey client first
    try:
        # Import separately to catch import errors specifically
        from packages.shared.src.llm_client.portkey_client import PortkeyClient
        
        logger.info("Using real PortkeyClient")
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
