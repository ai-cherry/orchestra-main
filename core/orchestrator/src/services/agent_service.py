"""
Agent Service for AI Orchestration System.

This module provides services for working with agents in the orchestration system,
including functionality to instantiate and manage agents.
"""

import logging
from typing import Dict, Optional, Any

# Import base agent class and concrete implementations
from packages.agents.base import BaseAgent
from packages.agents.runtime.web_scraper import WebScraperRuntimeAgent

# Configure logging
logger = logging.getLogger(__name__)


def get_agent_instance(
    agent_name: str,
    config: Optional[Dict[str, Any]] = None,
    persona: Optional[Dict[str, Any]] = None,
    memory_manager=None,
) -> Optional[BaseAgent]:
    """
    Get an instance of an agent based on the agent name.

    Args:
        agent_name: Name of the agent to instantiate
        config: Optional configuration dictionary for the agent
        persona: Optional persona configuration for the agent
        memory_manager: Optional memory manager for storing agent data

    Returns:
        An instance of the requested agent, or None if no matching agent is found

    Raises:
        ValueError: If the agent name is invalid
    """
    config = config or {}
    persona = persona or {}

    logger.info(f"Instantiating agent: {agent_name}")

    # Use a simple if/elif structure to map agent names to their implementations
    if agent_name == "web_scraper":
        logger.info("Creating WebScraperRuntimeAgent instance")
        return WebScraperRuntimeAgent(
            config=config, persona=persona, memory_manager=memory_manager
        )

    # If we get here, no matching agent was found
    logger.warning(f"No agent implementation found for: {agent_name}")
    raise ValueError(f"Unknown agent type: {agent_name}")
