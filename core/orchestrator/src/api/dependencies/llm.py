"""
LLM client dependency for AI Orchestration System.

This module provides the dependency injection function for the LLM client.
"""

import logging

from packages.shared.src.llm_client.interface import LLMClient
from packages.shared.src.llm_client.portkey_client import PortkeyClient
from core.orchestrator.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


def get_llm_client() -> LLMClient:
    """
    Get the LLM client instance.
    
    Returns:
        An initialized LLM client
    """
    settings = get_settings()
    logger.debug("Initializing PortkeyClient with settings")
    return PortkeyClient(settings)
