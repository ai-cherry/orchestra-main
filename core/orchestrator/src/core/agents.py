"""
Agents module for AI Orchestration System.

This module provides the base agent functionality and agent registry,
which are core components of the AI orchestration system.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from core.orchestrator.src.core.memory import MemoryItem
from core.orchestrator.src.core.personas import PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """
    Context provided to agents for processing.

    This class encapsulates all the information an agent needs to
    process a user request and generate a response.
    """

    user_input: str
    user_id: str
    persona: PersonaConfig
    conversation_history: List[MemoryItem] = field(default_factory=list)
    session_id: Optional[str] = None
    interaction_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """
    Response from an agent's processing.

    This class encapsulates the output from an agent, including
    the response text and metadata about the processing.
    """

    text: str
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class Agent(ABC):
    """
    Abstract base class for all agents.

    This class defines the interface that all agents must implement,
    including the core processing logic.
    """

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a user request and generate a response.

        Args:
            context: The context for processing

        Returns:
            The agent's response
        """

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """
        Get the agent's type identifier.

        Returns:
            The agent type string
        """

    @property
    def capabilities(self) -> List[str]:
        """
        Get the agent's capabilities.

        Returns:
            List of capability strings
        """
        return []


class SimpleTextAgent(Agent):
    """
    Simple text-based agent.

    This agent provides basic text processing capabilities and
    serves as a fallback when more specialized agents are not available.
    """

    @property
    def agent_type(self) -> str:
        """Get the agent type."""
        return "simple_text"

    @property
    def capabilities(self) -> List[str]:
        """Get the agent's capabilities."""
        return ["text_generation", "conversation"]

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a user request."""
        # In a real implementation, this would call an AI model
        # For demo purposes, we'll just return a simple response
        persona = context.persona
        name = persona.name

        response_text = f"As {name}, I acknowledge your message: '{context.user_input}'"

        return AgentResponse(
            text=response_text, confidence=0.8, metadata={"agent_type": self.agent_type}
        )


class PersonaAwareAgent(SimpleTextAgent):
    """
    Agent with enhanced persona awareness.

    This agent extends the simple text agent with improved
    persona-specific processing capabilities.
    """

    @property
    def agent_type(self) -> str:
        """Get the agent type."""
        return "persona_aware"

    @property
    def capabilities(self) -> List[str]:
        """Get the agent's capabilities."""
        return super().capabilities + ["persona_customization"]

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a user request with persona awareness."""
        # In a real implementation, this would include persona-specific logic
        # For now, we'll extend the simple agent with persona traits

        persona = context.persona
        traits_str = ", ".join(persona.traits[:3]) if persona.traits else "helpful"

        response_text = (
            f"As {persona.name}, I'm being {traits_str} in my response to: "
            f"'{context.user_input}'"
        )

        return AgentResponse(
            text=response_text,
            confidence=0.9,
            metadata={"agent_type": self.agent_type, "persona_traits": persona.traits},
        )


class AgentRegistry:
    """
    Registry for agent types.

    This class manages the available agent types and provides
    methods for registering and retrieving agents.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agent_types: Dict[str, Type[Agent]] = {}
        self._agent_instances: Dict[str, Agent] = {}

    def register_agent_type(self, agent_class: Type[Agent]) -> None:
        """
        Register an agent type.

        Args:
            agent_class: The agent class to register
        """
        # Create an instance to get the type
        instance = agent_class()
        agent_type = instance.agent_type

        self._agent_types[agent_type] = agent_class
        self._agent_instances[agent_type] = instance

        logger.info(f"Registered agent type: {agent_type}")

    def get_agent(self, agent_type: str) -> Agent:
        """
        Get an agent by type.

        Args:
            agent_type: The type of agent to get

        Returns:
            The agent instance

        Raises:
            KeyError: If the agent type is not registered
        """
        if agent_type not in self._agent_instances:
            if agent_type in self._agent_types:
                # Lazy initialization
                self._agent_instances[agent_type] = self._agent_types[agent_type]()
            else:
                raise KeyError(f"Agent type '{agent_type}' not registered")

        return self._agent_instances[agent_type]

    def get_agent_types(self) -> List[str]:
        """
        Get all registered agent types.

        Returns:
            List of agent type strings
        """
        return list(self._agent_types.keys())

    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context.

        Args:
            context: The agent context

        Returns:
            The selected agent instance

        Raises:
            RuntimeError: If no suitable agent is found
        """
        # In a real implementation, this would use more sophisticated logic
        # For now, we'll prefer persona-aware agents if available

        if "persona_aware" in self._agent_types:
            return self.get_agent("persona_aware")

        # Fall back to simple text agent
        if "simple_text" in self._agent_types:
            return self.get_agent("simple_text")

        # If nothing else, use the first registered agent
        if self._agent_types:
            return self.get_agent(next(iter(self._agent_types.keys())))

        raise RuntimeError("No agents registered in registry")


# Global agent registry instance
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Returns:
        The agent registry instance
    """
    global _agent_registry

    if _agent_registry is None:
        _agent_registry = AgentRegistry()

        # Register default agent types
        _agent_registry.register_agent_type(SimpleTextAgent)
        _agent_registry.register_agent_type(PersonaAwareAgent)

    return _agent_registry
