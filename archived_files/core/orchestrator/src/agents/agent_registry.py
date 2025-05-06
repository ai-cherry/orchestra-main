"""
Agent Registry for AI Orchestration System.

This module provides a registry for agent implementations, allowing dynamic
selection of agents based on context.
"""

import logging
from typing import Dict, List, Optional, Any, Callable, Type
import random

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse

# Configure logging
logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for agent implementations.

    This class maintains a registry of agent implementations and provides
    mechanisms for selecting appropriate agents based on context.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, Agent] = {}
        self._agent_types: Dict[str, Type[Agent]] = {}
        self._default_agent_type = "simple_text"

        logger.info("AgentRegistry initialized")

    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent instance.

        Args:
            agent: Agent instance to register
        """
        agent_type = agent.agent_type
        self._agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type}")

    def register_agent_type(self, agent_type: str, agent_class: Type[Agent]) -> None:
        """
        Register an agent type.

        Args:
            agent_type: Type identifier
            agent_class: Agent class
        """
        self._agent_types[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")

    def set_default_agent_type(self, agent_type: str) -> None:
        """
        Set the default agent type.

        Args:
            agent_type: Default agent type
        """
        if agent_type in self._agent_types or agent_type in self._agents:
            self._default_agent_type = agent_type
            logger.info(f"Set default agent type: {agent_type}")
        else:
            logger.warning(
                f"Unknown agent type '{agent_type}' cannot be set as default"
            )

    def get_agent(self, agent_type: Optional[str] = None) -> Agent:
        """
        Get an agent instance by type.

        Args:
            agent_type: Type of agent to get, or None for default

        Returns:
            Agent instance

        Raises:
            KeyError: If the agent type is not registered
        """
        # Use default if not specified
        if agent_type is None:
            agent_type = self._default_agent_type

        # Return existing instance if available
        if agent_type in self._agents:
            return self._agents[agent_type]

        # Create new instance if type is registered
        if agent_type in self._agent_types:
            agent = self._agent_types[agent_type]()
            self._agents[agent_type] = agent
            return agent

        # Raise error if not found
        raise KeyError(f"Agent type '{agent_type}' not registered")

    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context.

        This method examines the context and selects the agent best suited
        for handling it. If multiple agents are suitable, one is chosen
        based on heuristics.

        Args:
            context: Agent context

        Returns:
            Selected agent instance

        Raises:
            RuntimeError: If no agents are registered
        """
        if not self._agents and not self._agent_types:
            raise RuntimeError("No agents registered")

        # ENHANCE: Implement more sophisticated selection logic based on context

        # For now, use default agent type
        try:
            return self.get_agent(self._default_agent_type)
        except KeyError:
            # Fall back to any registered agent if default not available
            if self._agents:
                agent_type = next(iter(self._agents))
                logger.warning(f"Default agent not available, using {agent_type}")
                return self._agents[agent_type]

            # Fall back to creating first registered type
            if self._agent_types:
                agent_type = next(iter(self._agent_types))
                logger.warning(f"No agent instances available, creating {agent_type}")
                agent = self._agent_types[agent_type]()
                self._agents[agent_type] = agent
                return agent

            raise RuntimeError("No agent types registered")


# Global agent registry instance
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    This function provides a simple dependency injection mechanism
    for accessing the agent registry throughout the application.

    Returns:
        The global AgentRegistry instance
    """
    global _agent_registry

    if _agent_registry is None:
        _agent_registry = AgentRegistry()

    return _agent_registry


def register_default_agents():
    """
    Register default agents in the registry.

    This function registers the standard agent implementations that
    should be available by default.
    """
    from core.orchestrator.src.agents.agent_base import Agent
    from core.orchestrator.src.agents.persona_agent import PersonaAgent
    from core.orchestrator.src.agents.llm_agent import LLMAgent

    registry = get_agent_registry()

    # Register agent types
    registry.register_agent_type("simple_text", PersonaAgent)
    registry.register_agent_type("llm_agent", LLMAgent)

    # Create and register default instances
    registry.register_agent(PersonaAgent())
    registry.register_agent(LLMAgent())

    # Set default agent type
    from core.orchestrator.src.config.config import get_settings

    settings = get_settings()
    default_agent_type = getattr(settings, "DEFAULT_AGENT_TYPE", "simple_text")
    registry.set_default_agent_type(default_agent_type)

    logger.info("Registered default agents")
