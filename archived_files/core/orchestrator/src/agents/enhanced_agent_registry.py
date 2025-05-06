"""
Enhanced Agent Registry for AI Orchestration System.

This module provides an improved registry for managing and selecting AI agents
with better dependency management, lifecycle control, and dynamic agent resolution.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.services.enhanced_event_bus import (
    get_enhanced_event_bus,
    EventPriority,
    subscribe,
)
from core.orchestrator.src.services.enhanced_registry import Service

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar("T", bound=Agent)


class AgentCapability(Enum):
    """
    Capabilities that agents can provide.

    These capabilities are used for dynamic agent selection based on context.
    """

    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    CLASSIFICATION = "classification"
    CREATIVE_WRITING = "creative_writing"
    FACTUAL_RESPONSE = "factual_response"
    CODE_GENERATION = "code_generation"
    IMAGE_UNDERSTANDING = "image_understanding"
    MULTI_MODAL = "multi_modal"


class AgentInfo:
    """
    Container for agent information and metadata.

    This class stores information about registered agents, including
    the agent class, agent type name, capabilities, and priority.
    """

    def __init__(
        self,
        agent_class: Type[Agent],
        agent_type: str,
        capabilities: List[AgentCapability],
        priority: int = 0,
        factory: Optional[Callable[[], Agent]] = None,
        singleton: bool = True,
    ):
        """
        Initialize agent information.

        Args:
            agent_class: The agent class
            agent_type: The unique type identifier for this agent
            capabilities: List of capabilities this agent provides
            priority: Selection priority (higher values are preferred)
            factory: Optional factory function for creating agent instances
            singleton: Whether to reuse a single instance for all requests
        """
        self.agent_class = agent_class
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.priority = priority
        self.factory = factory
        self.singleton = singleton
        self._instance: Optional[Agent] = None

    def get_instance(self) -> Agent:
        """
        Get an agent instance.

        This returns the singleton instance if singleton mode is enabled,
        otherwise it creates a new instance each time.

        Returns:
            An agent instance
        """
        if self.singleton:
            if self._instance is None:
                self._instance = self._create_instance()
            return self._instance
        else:
            return self._create_instance()

    def _create_instance(self) -> Agent:
        """
        Create a new agent instance.

        This uses the factory function if provided, otherwise
        it creates a new instance of the agent class.

        Returns:
            A new agent instance
        """
        if self.factory:
            return self.factory()
        else:
            return self.agent_class()

    def supports_capability(self, capability: AgentCapability) -> bool:
        """
        Check if this agent supports a specific capability.

        Args:
            capability: The capability to check for

        Returns:
            True if the agent supports the capability, False otherwise
        """
        return capability in self.capabilities

    def reset(self) -> None:
        """
        Reset the agent instance.

        This clears the cached singleton instance, forcing a new
        instance to be created on the next get_instance() call.
        """
        self._instance = None


class EnhancedAgentRegistry(Service):
    """
    Enhanced registry for managing and selecting AI agents.

    This registry provides improved lifecycle management, dependency injection,
    and more sophisticated agent selection capabilities.
    """

    def __init__(self):
        """Initialize the enhanced agent registry."""
        self._agents: Dict[str, AgentInfo] = {}
        self._capabilities: Dict[AgentCapability, List[str]] = {
            capability: [] for capability in AgentCapability
        }
        self._default_agent_type: Optional[str] = None

        # Subscribe to relevant events
        self._event_bus = get_enhanced_event_bus()
        subscribe("agent_registered", self._on_agent_registered)

        logger.debug("EnhancedAgentRegistry initialized")

    def initialize(self) -> None:
        """Initialize the registry and its managed agents."""
        logger.info(f"Initializing agent registry with {len(self._agents)} agents")

        # Initialize any agents that need initialization
        for agent_type, agent_info in self._agents.items():
            try:
                # Get the instance to trigger initialization if needed
                instance = agent_info.get_instance()
                if hasattr(instance, "initialize") and callable(instance.initialize):
                    instance.initialize()
                    logger.debug(f"Initialized agent: {agent_type}")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_type}: {e}")

    async def initialize_async(self) -> None:
        """Initialize the registry and its managed agents asynchronously."""
        logger.info(
            f"Initializing agent registry asynchronously with {len(self._agents)} agents"
        )

        # For now, just call the synchronous version
        # In a real implementation, we would use async initialization
        self.initialize()

    def close(self) -> None:
        """Close all managed agents and release resources."""
        logger.info(f"Closing agent registry with {len(self._agents)} agents")

        # Close any agents that need cleanup
        for agent_type, agent_info in self._agents.items():
            if agent_info.singleton and agent_info._instance is not None:
                instance = agent_info._instance
                if hasattr(instance, "close") and callable(instance.close):
                    try:
                        instance.close()
                        logger.debug(f"Closed agent: {agent_type}")
                    except Exception as e:
                        logger.error(f"Error closing agent {agent_type}: {e}")

    async def close_async(self) -> None:
        """Close all managed agents asynchronously."""
        # For now, just call the synchronous version
        self.close()

    def register_agent(
        self,
        agent_class: Type[Agent],
        agent_type: str,
        capabilities: List[AgentCapability],
        priority: int = 0,
        factory: Optional[Callable[[], Agent]] = None,
        singleton: bool = True,
        is_default: bool = False,
    ) -> None:
        """
        Register an agent with the registry.

        Args:
            agent_class: The agent class
            agent_type: Unique type identifier for this agent
            capabilities: List of capabilities this agent provides
            priority: Selection priority (higher values are preferred)
            factory: Optional factory function for creating agent instances
            singleton: Whether to reuse a single instance for all requests
            is_default: Whether this agent should be the default

        Raises:
            ValueError: If an agent with the same type is already registered
        """
        if agent_type in self._agents:
            raise ValueError(f"Agent type '{agent_type}' is already registered")

        # Create agent info
        agent_info = AgentInfo(
            agent_class, agent_type, capabilities, priority, factory, singleton
        )

        # Register agent
        self._agents[agent_type] = agent_info

        # Register capabilities
        for capability in capabilities:
            self._capabilities[capability].append(agent_type)

            # Sort agents by priority for each capability
            self._capabilities[capability].sort(
                key=lambda t: self._agents[t].priority,
                reverse=True,  # Higher priority first
            )

        # Set as default if requested
        if is_default:
            self._default_agent_type = agent_type

        # Publish event
        self._event_bus.publish(
            "agent_registered",
            {
                "agent_type": agent_type,
                "capabilities": [c.value for c in capabilities],
                "priority": priority,
            },
        )

        logger.info(
            f"Registered agent: {agent_type} with capabilities {[c.value for c in capabilities]}"
        )

    def unregister_agent(self, agent_type: str) -> bool:
        """
        Unregister an agent from the registry.

        Args:
            agent_type: The unique type identifier of the agent to unregister

        Returns:
            True if the agent was found and unregistered, False otherwise
        """
        if agent_type not in self._agents:
            logger.warning(f"Cannot unregister agent: {agent_type} not found")
            return False

        # Get agent info
        agent_info = self._agents[agent_type]

        # Close agent if it's a singleton and has been instantiated
        if agent_info.singleton and agent_info._instance is not None:
            instance = agent_info._instance
            if hasattr(instance, "close") and callable(instance.close):
                try:
                    instance.close()
                    logger.debug(f"Closed agent: {agent_type}")
                except Exception as e:
                    logger.error(f"Error closing agent {agent_type}: {e}")

        # Remove from capabilities
        for capability, agents in self._capabilities.items():
            if agent_type in agents:
                agents.remove(agent_type)

        # Remove from agents dict
        del self._agents[agent_type]

        # Clear default if this was the default agent
        if self._default_agent_type == agent_type:
            self._default_agent_type = None

        # Publish event
        self._event_bus.publish("agent_unregistered", {"agent_type": agent_type})

        logger.info(f"Unregistered agent: {agent_type}")
        return True

    def get_agent(self, agent_type: str) -> Agent:
        """
        Get an agent by type.

        Args:
            agent_type: The unique type identifier of the agent

        Returns:
            An agent instance

        Raises:
            ValueError: If no agent with the specified type is registered
        """
        if agent_type not in self._agents:
            raise ValueError(f"Agent type '{agent_type}' is not registered")

        # Get agent info and instance
        agent_info = self._agents[agent_type]
        return agent_info.get_instance()

    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context.

        This method analyzes the context to determine which agent
        is best suited to handle it, based on:
        1. Content type and format
        2. User preferences
        3. Agent capabilities
        4. Previous interactions

        Args:
            context: The context to select an agent for

        Returns:
            The selected agent

        Raises:
            ValueError: If no suitable agent is found
        """
        # Determine required capabilities from context
        required_capabilities = self._determine_required_capabilities(context)

        # Find agents that support all required capabilities
        candidate_types = self._find_agents_with_capabilities(required_capabilities)

        # If a specific agent is requested by the context, try to use it
        requested_agent_type = context.metadata.get("requested_agent_type")
        if requested_agent_type and requested_agent_type in self._agents:
            # Verify it supports the required capabilities
            agent_info = self._agents[requested_agent_type]
            if all(
                agent_info.supports_capability(cap) for cap in required_capabilities
            ):
                logger.info(
                    f"Using specifically requested agent: {requested_agent_type}"
                )
                return agent_info.get_instance()
            else:
                logger.warning(
                    f"Requested agent {requested_agent_type} does not support "
                    f"required capabilities: {[c.value for c in required_capabilities]}"
                )

        # If we have candidate agents, select the highest priority one
        if candidate_types:
            selected_type = candidate_types[0]  # Already sorted by priority
            logger.info(
                f"Selected agent {selected_type} based on capabilities: {[c.value for c in required_capabilities]}"
            )
            return self._agents[selected_type].get_instance()

        # If no suitable agent is found, fall back to default
        if self._default_agent_type:
            logger.warning(
                f"No agent found supporting capabilities: {[c.value for c in required_capabilities]}. "
                f"Falling back to default: {self._default_agent_type}"
            )
            return self._agents[self._default_agent_type].get_instance()

        # If no default agent is set, raise an error
        raise ValueError(
            f"No agent found supporting capabilities: {[c.value for c in required_capabilities]} "
            f"and no default agent is configured"
        )

    def _determine_required_capabilities(
        self, context: AgentContext
    ) -> List[AgentCapability]:
        """
        Determine the capabilities required for a context.

        Args:
            context: The context to analyze

        Returns:
            List of required capabilities
        """
        # This is a simple implementation - in a real system this would
        # be more sophisticated, analyzing the content and history

        # By default, require text generation
        capabilities = [AgentCapability.TEXT_GENERATION]

        # Check for question answering
        if "?" in context.user_input:
            capabilities.append(AgentCapability.QUESTION_ANSWERING)

        # Check for code generation
        code_keywords = ["code", "function", "class", "programming", "script"]
        if any(keyword in context.user_input.lower() for keyword in code_keywords):
            capabilities.append(AgentCapability.CODE_GENERATION)

        # Check for creative writing
        creative_keywords = ["story", "poem", "creative", "imagine", "fiction"]
        if any(keyword in context.user_input.lower() for keyword in creative_keywords):
            capabilities.append(AgentCapability.CREATIVE_WRITING)

        # Check metadata for explicit capability requirements
        required_capabilities = context.metadata.get("required_capabilities", [])
        for capability_str in required_capabilities:
            try:
                # Convert string to enum
                capability = AgentCapability(capability_str)
                if capability not in capabilities:
                    capabilities.append(capability)
            except ValueError:
                logger.warning(
                    f"Unknown capability in context metadata: {capability_str}"
                )

        return capabilities

    def _find_agents_with_capabilities(
        self, capabilities: List[AgentCapability]
    ) -> List[str]:
        """
        Find agents that support all the specified capabilities.

        Args:
            capabilities: The capabilities that agents must support

        Returns:
            List of agent types sorted by priority (highest first)
        """
        # Start with all agent types
        candidate_types = list(self._agents.keys())

        # Filter by required capabilities
        for capability in capabilities:
            # Only keep agents that support this capability
            candidate_types = [
                agent_type
                for agent_type in candidate_types
                if self._agents[agent_type].supports_capability(capability)
            ]

        # Sort by priority (highest first)
        candidate_types.sort(key=lambda t: self._agents[t].priority, reverse=True)

        return candidate_types

    def _on_agent_registered(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent registration events.

        Args:
            event_data: Event data containing agent information
        """
        agent_type = event_data.get("agent_type", "unknown")
        capabilities = event_data.get("capabilities", [])
        logger.debug(
            f"Received agent registration event: {agent_type} with capabilities {capabilities}"
        )


class AgentFactory:
    """
    Factory for creating and configuring agents.

    This class simplifies the creation of agents with standard configurations
    and dependency injection.
    """

    @staticmethod
    def create_text_agent() -> Agent:
        """
        Create a standard text processing agent.

        Returns:
            A configured text agent
        """
        # In a real implementation, this would create and configure a text agent
        # For now, we'll just return a placeholder
        from core.orchestrator.src.agents.persona_agent import PersonaAgent

        return PersonaAgent()


# Global enhanced agent registry instance
_enhanced_agent_registry = None


def get_enhanced_agent_registry() -> EnhancedAgentRegistry:
    """
    Get the global enhanced agent registry instance.

    This function provides a simple dependency injection mechanism
    for accessing the enhanced agent registry throughout the application.

    Returns:
        The global EnhancedAgentRegistry instance
    """
    global _enhanced_agent_registry

    if _enhanced_agent_registry is None:
        _enhanced_agent_registry = EnhancedAgentRegistry()

    return _enhanced_agent_registry


# Helper functions for more ergonomic API
def register_agent(
    agent_class: Type[Agent],
    agent_type: str,
    capabilities: List[AgentCapability],
    priority: int = 0,
    factory: Optional[Callable[[], Agent]] = None,
    singleton: bool = True,
    is_default: bool = False,
) -> None:
    """
    Register an agent with the global registry.

    Args:
        agent_class: The agent class
        agent_type: Unique type identifier for this agent
        capabilities: List of capabilities this agent provides
        priority: Selection priority (higher values are preferred)
        factory: Optional factory function for creating agent instances
        singleton: Whether to reuse a single instance for all requests
        is_default: Whether this agent should be the default
    """
    get_enhanced_agent_registry().register_agent(
        agent_class, agent_type, capabilities, priority, factory, singleton, is_default
    )


def get_agent(agent_type: str) -> Agent:
    """
    Get an agent by type from the global registry.

    Args:
        agent_type: The unique type identifier of the agent

    Returns:
        An agent instance
    """
    return get_enhanced_agent_registry().get_agent(agent_type)


def select_agent_for_context(context: AgentContext) -> Agent:
    """
    Select an agent for a context using the global registry.

    Args:
        context: The context to select an agent for

    Returns:
        The selected agent
    """
    return get_enhanced_agent_registry().select_agent_for_context(context)
