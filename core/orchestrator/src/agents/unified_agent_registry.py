"""
Unified Agent Registry for AI Orchestration System.

This module provides a consolidated registry for managing AI agents with capability-based
selection, proper lifecycle management, and simplified dependency injection.
"""

import asyncio
import logging
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.services.unified_registry import Service, ServiceFactory

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic typing
T = TypeVar("T", bound=Agent)


class AgentCapability(Enum):
    """
    Capabilities that agents can provide.

    These capabilities are used for dynamic agent selection based on context.
    """

    TEXT_GENERATION = auto()
    QUESTION_ANSWERING = auto()
    SUMMARIZATION = auto()
    CLASSIFICATION = auto()
    CREATIVE_WRITING = auto()
    FACTUAL_RESPONSE = auto()
    CODE_GENERATION = auto()
    MULTI_MODAL = auto()
    GENERAL = auto()  # For basic agents that don't have specialized capabilities


class AgentInfo:
    """
    Container for agent information and metadata.

    This class stores information about registered agents, including
    the agent type, capabilities, and priority for selection.
    """

    def __init__(
        self,
        agent: Agent,
        agent_type: str,
        capabilities: List[AgentCapability],
        priority: int = 0,
    ):
        """
        Initialize agent information.

        Args:
            agent: The agent instance
            agent_type: The unique type identifier for this agent
            capabilities: List of capabilities this agent provides
            priority: Selection priority (higher values are preferred)
        """
        self.agent = agent
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.priority = priority

    def supports_capability(self, capability: AgentCapability) -> bool:
        """
        Check if this agent supports a specific capability.

        Args:
            capability: The capability to check for

        Returns:
            True if the agent supports the capability, False otherwise
        """
        return capability in self.capabilities


class AgentRegistry(Service):
    """
    Unified registry for managing and selecting AI agents.

    This registry provides capability-based agent selection, proper lifecycle
    management, and simplified dependency injection for agent access.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, AgentInfo] = {}  # By agent type
        self._capabilities: Dict[AgentCapability, List[str]] = {
            capability: [] for capability in AgentCapability
        }
        self._default_agent_type: Optional[str] = None
        logger.debug("AgentRegistry initialized")

    def initialize(self) -> None:
        """Initialize all registered agents."""
        logger.info(f"Initializing {len(self._agents)} agents")

        for agent_type, agent_info in self._agents.items():
            try:
                if hasattr(agent_info.agent, "initialize") and callable(
                    agent_info.agent.initialize
                ):
                    agent_info.agent.initialize()
                    logger.debug(f"Initialized agent: {agent_type}")
            except Exception as e:
                logger.error(f"Failed to initialize agent {agent_type}: {e}")

    async def initialize_async(self) -> None:
        """Initialize all registered agents asynchronously."""
        logger.info(f"Initializing {len(self._agents)} agents asynchronously")

        init_tasks = []
        for agent_type, agent_info in self._agents.items():
            task = self._safe_initialize_agent_async(agent_info.agent, agent_type)
            init_tasks.append(task)

        # Execute all initialization tasks concurrently
        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)

    async def _safe_initialize_agent_async(self, agent: Agent, agent_type: str) -> None:
        """
        Initialize an agent safely with async/sync fallback.

        Args:
            agent: The agent to initialize
            agent_type: The agent's type for logging
        """
        try:
            # First try async initialize if available
            if hasattr(agent, "initialize_async") and callable(agent.initialize_async):
                await agent.initialize_async()
                logger.debug(f"Initialized agent asynchronously: {agent_type}")
            # Fall back to sync initialize in a thread pool
            elif hasattr(agent, "initialize") and callable(agent.initialize):
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, agent.initialize)
                logger.debug(f"Initialized agent in thread pool: {agent_type}")
        except Exception as e:
            logger.error(f"Failed to initialize agent {agent_type}: {e}")

    def close(self) -> None:
        """Close all registered agents and release resources."""
        logger.info(f"Closing {len(self._agents)} agents")

        for agent_type, agent_info in self._agents.items():
            try:
                if hasattr(agent_info.agent, "close") and callable(
                    agent_info.agent.close
                ):
                    agent_info.agent.close()
                    logger.debug(f"Closed agent: {agent_type}")
            except Exception as e:
                logger.error(f"Error closing agent {agent_type}: {e}")

    async def close_async(self) -> None:
        """Close all registered agents asynchronously."""
        logger.info(f"Closing {len(self._agents)} agents asynchronously")

        close_tasks = []
        for agent_type, agent_info in self._agents.items():
            task = self._safe_close_agent_async(agent_info.agent, agent_type)
            close_tasks.append(task)

        # Execute all close tasks concurrently
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

    async def _safe_close_agent_async(self, agent: Agent, agent_type: str) -> None:
        """
        Close an agent safely with async/sync fallback.

        Args:
            agent: The agent to close
            agent_type: The agent's type for logging
        """
        try:
            # First try async close if available
            if hasattr(agent, "close_async") and callable(agent.close_async):
                await agent.close_async()
                logger.debug(f"Closed agent asynchronously: {agent_type}")
            # Fall back to sync close in a thread pool
            elif hasattr(agent, "close") and callable(agent.close):
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, agent.close)
                logger.debug(f"Closed agent in thread pool: {agent_type}")
        except Exception as e:
            logger.error(f"Failed to close agent {agent_type}: {e}")

    def register_agent(
        self,
        agent: Agent,
        agent_type: str,
        capabilities: List[AgentCapability],
        priority: int = 0,
        is_default: bool = False,
    ) -> Agent:
        """
        Register an agent with the registry.

        Args:
            agent: The agent to register
            agent_type: Unique type identifier for this agent
            capabilities: List of capabilities this agent provides
            priority: Selection priority (higher values are preferred)
            is_default: Whether this agent should be the default

        Returns:
            The registered agent (for chaining)

        Raises:
            ValueError: If an agent with the same type is already registered
        """
        if agent_type in self._agents:
            raise ValueError(f"Agent type '{agent_type}' is already registered")

        # Create agent info
        agent_info = AgentInfo(agent, agent_type, capabilities, priority)

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

        # Set as default if requested or if first agent
        if is_default or self._default_agent_type is None:
            self._default_agent_type = agent_type

        logger.info(
            f"Registered agent: {agent_type} with capabilities {[c.name for c in capabilities]}"
        )
        return agent

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

        # Close agent if it has a close method
        agent = agent_info.agent
        if hasattr(agent, "close") and callable(agent.close):
            try:
                agent.close()
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
            # Set a new default if possible
            if self._agents:
                self._default_agent_type = next(iter(self._agents.keys()))
            else:
                self._default_agent_type = None

        logger.info(f"Unregistered agent: {agent_type}")
        return True

    def get_agent(self, agent_type: str) -> Agent:
        """
        Get an agent by its type.

        Args:
            agent_type: The unique type identifier of the agent

        Returns:
            The agent instance

        Raises:
            ValueError: If no agent with the specified type is registered
        """
        if agent_type not in self._agents:
            raise ValueError(f"Agent type '{agent_type}' is not registered")

        return self._agents[agent_type].agent

    def get_agent_info(self, agent_type: str) -> AgentInfo:
        """
        Get agent information by type.

        Args:
            agent_type: The unique type identifier of the agent

        Returns:
            The agent information

        Raises:
            ValueError: If no agent with the specified type is registered
        """
        if agent_type not in self._agents:
            raise ValueError(f"Agent type '{agent_type}' is not registered")

        return self._agents[agent_type]

    def get_default_agent(self) -> Agent:
        """
        Get the default agent.

        Returns:
            The default agent instance

        Raises:
            ValueError: If no default agent is set
        """
        if self._default_agent_type is None:
            raise ValueError("No default agent is set")

        return self.get_agent(self._default_agent_type)

    def set_default_agent_type(self, agent_type: str) -> None:
        """
        Set the default agent type.

        Args:
            agent_type: Default agent type

        Raises:
            ValueError: If the agent type is not registered
        """
        if agent_type not in self._agents:
            raise ValueError(
                f"Cannot set default agent type: '{agent_type}' is not registered"
            )

        self._default_agent_type = agent_type
        logger.info(f"Set default agent type: {agent_type}")

    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context.

        This method analyzes the context to determine which agent
        is best suited to handle it, based on content analysis,
        required capabilities, and agent priorities.

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
                return agent_info.agent
            else:
                logger.warning(
                    f"Requested agent {requested_agent_type} does not support "
                    f"required capabilities: {[c.name for c in required_capabilities]}"
                )

        # If we have candidate agents, select the highest priority one
        if candidate_types:
            selected_type = candidate_types[0]  # Already sorted by priority
            logger.info(
                f"Selected agent {selected_type} based on capabilities: "
                f"{[c.name for c in required_capabilities]}"
            )
            return self._agents[selected_type].agent

        # Alternative selection: use agent confidence scores
        if not candidate_types:
            highest_confidence = -1.0
            best_agent_type = None

            # Ask each agent how confident it is in handling this context
            for agent_type, agent_info in self._agents.items():
                agent = agent_info.agent
                if hasattr(agent, "can_handle") and callable(agent.can_handle):
                    try:
                        confidence = agent.can_handle(context)
                        if confidence > highest_confidence:
                            highest_confidence = confidence
                            best_agent_type = agent_type
                    except Exception as e:
                        logger.warning(
                            f"Error checking agent {agent_type} confidence: {e}"
                        )

            # If we found a confident agent, use it
            if best_agent_type and highest_confidence > 0.5:
                logger.info(
                    f"Selected agent {best_agent_type} based on confidence: {highest_confidence}"
                )
                return self._agents[best_agent_type].agent

        # If no suitable agent is found, fall back to default
        if self._default_agent_type:
            logger.warning(
                f"No agent found supporting capabilities: {[c.name for c in required_capabilities]}. "
                f"Falling back to default: {self._default_agent_type}"
            )
            return self._agents[self._default_agent_type].agent

        # If no default agent is set, raise an error
        raise ValueError(
            f"No agent found supporting capabilities: {[c.name for c in required_capabilities]} "
            f"and no default agent is configured"
        )

    def _determine_required_capabilities(
        self, context: AgentContext
    ) -> List[AgentCapability]:
        """
        Analyze the context to determine what capabilities are required.

        Args:
            context: The context to analyze

        Returns:
            List of required capabilities
        """
        # Check metadata for explicit capability requirements
        explicit_capabilities = []
        required_capabilities_str = context.metadata.get("required_capabilities", [])
        if isinstance(required_capabilities_str, list):
            for capability_str in required_capabilities_str:
                try:
                    # Try to match by name
                    capability = next(
                        (
                            c
                            for c in AgentCapability
                            if c.name.lower() == capability_str.lower()
                        ),
                        None,
                    )
                    if capability and capability not in explicit_capabilities:
                        explicit_capabilities.append(capability)
                except Exception:
                    logger.warning(
                        f"Invalid capability in context metadata: {capability_str}"
                    )

        # If we have explicit capabilities, use those
        if explicit_capabilities:
            return explicit_capabilities

        # Otherwise, infer capabilities from context
        capabilities = [AgentCapability.GENERAL]  # Always include general capability

        # Simple heuristics - in a real system, this would be more sophisticated
        user_input = context.user_input.lower()

        # Detect question answering
        if "?" in user_input or any(
            w in user_input for w in ["who", "what", "when", "where", "why", "how"]
        ):
            capabilities.append(AgentCapability.QUESTION_ANSWERING)

        # Detect creative writing
        creative_keywords = ["story", "creative", "imagine", "fiction", "poem", "write"]
        if any(keyword in user_input for keyword in creative_keywords):
            capabilities.append(AgentCapability.CREATIVE_WRITING)

        # Detect code generation
        code_keywords = ["code", "function", "program", "script", "class", "implement"]
        if any(keyword in user_input for keyword in code_keywords):
            capabilities.append(AgentCapability.CODE_GENERATION)

        # Detect factual response
        factual_keywords = ["fact", "information", "data", "statistics", "research"]
        if any(keyword in user_input for keyword in factual_keywords):
            capabilities.append(AgentCapability.FACTUAL_RESPONSE)

        # Add text generation for longer responses
        if len(user_input.split()) > 10:
            capabilities.append(AgentCapability.TEXT_GENERATION)

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

    def get_agent_types(self) -> List[str]:
        """
        Get a list of all registered agent types.

        Returns:
            List of agent type identifiers
        """
        return list(self._agents.keys())

    def get_agent_count(self) -> int:
        """
        Get the number of registered agents.

        Returns:
            Number of registered agents
        """
        return len(self._agents)


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


# Helper functions for more ergonomic API
def register_agent(
    agent: Agent,
    agent_type: str,
    capabilities: List[AgentCapability],
    priority: int = 0,
    is_default: bool = False,
) -> Agent:
    """Register an agent with the global registry."""
    return get_agent_registry().register_agent(
        agent, agent_type, capabilities, priority, is_default
    )


def get_agent(agent_type: str) -> Agent:
    """Get an agent from the global registry by type."""
    return get_agent_registry().get_agent(agent_type)


def get_default_agent() -> Agent:
    """Get the default agent from the global registry."""
    return get_agent_registry().get_default_agent()


def select_agent_for_context(context: AgentContext) -> Agent:
    """Select an agent for a context using the global registry."""
    return get_agent_registry().select_agent_for_context(context)


def register_default_agents() -> None:
    """
    Register default agents in the registry.

    This function registers the standard agent implementations that
    should be available by default. It's typically called during
    application startup.
    """
    from core.orchestrator.src.agents.persona_agent import PersonaAwareAgent
    from core.orchestrator.src.agents.llm_agent import LLMAgent

    # Get registry instance
    get_agent_registry()

    # Register simple persona-aware agent
    persona_agent = PersonaAwareAgent()
    register_agent(
        persona_agent,
        "persona_agent",
        [
            AgentCapability.GENERAL,
            AgentCapability.TEXT_GENERATION,
            AgentCapability.QUESTION_ANSWERING,
        ],
        priority=50,
        is_default=True,
    )

    # Register LLM agent if available
    try:
        llm_agent = LLMAgent()
        register_agent(
            llm_agent,
            "llm_agent",
            [
                AgentCapability.GENERAL,
                AgentCapability.TEXT_GENERATION,
                AgentCapability.QUESTION_ANSWERING,
                AgentCapability.CREATIVE_WRITING,
                AgentCapability.FACTUAL_RESPONSE,
                AgentCapability.CODE_GENERATION,
            ],
            priority=75,
        )
    except Exception as e:
        logger.warning(f"Failed to register LLM agent: {e}")

    logger.info("Registered default agents")
