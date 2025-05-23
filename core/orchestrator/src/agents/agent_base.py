"""
Base Agent Interface for AI Orchestration System.

This module defines the base classes and interfaces for implementing different
types of AI agents within the orchestration system.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


class AgentContext:
    """
    Container for context information provided to an agent.

    This class encapsulates all the context that an agent needs to
    generate an appropriate response, including user input, conversation
    history, and persona-specific information.
    """

    def __init__(
        self,
        user_input: str,
        user_id: str,
        persona: PersonaConfig,
        conversation_history: List[MemoryItem] = None,
        session_id: Optional[str] = None,
        interaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize agent context.

        Args:
            user_input: The user's input message
            user_id: The ID of the user
            persona: The selected persona configuration
            conversation_history: Previous conversation items
            session_id: The session ID for this conversation
            interaction_id: The unique interaction ID
            metadata: Additional context metadata
        """
        self.user_input = user_input
        self.user_id = user_id
        self.persona = persona
        self.conversation_history = conversation_history or []
        self.session_id = session_id
        self.interaction_id = interaction_id
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    @property
    def recent_messages(self) -> List[Dict[str, Any]]:
        """
        Get recent messages in a simplified format.

        Returns:
            List of recent messages as dictionaries
        """
        messages = []

        for item in self.conversation_history:
            is_user = item.metadata.get("source") == "user"
            messages.append(
                {
                    "role": "user" if is_user else "assistant",
                    "content": item.text_content,
                    "timestamp": item.timestamp,
                }
            )

        # Add the current user input
        messages.append({"role": "user", "content": self.user_input, "timestamp": self.timestamp})

        return messages


class AgentResponse:
    """
    Container for the response generated by an agent.

    This class encapsulates the output from an agent, including the
    response text, confidence score, and any additional metadata.
    """

    def __init__(
        self,
        text: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an agent response.

        Args:
            text: The text response from the agent
            confidence: Confidence score (0-1) for the response
            metadata: Additional metadata about the response
        """
        self.text = text
        self.confidence = min(max(confidence, 0.0), 1.0)  # Ensure between 0 and 1
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary.

        Returns:
            Dictionary representation of the response
        """
        return {
            "text": self.text,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class Agent(ABC):
    """
    Abstract base class for all agents.

    This class defines the interface that all agent implementations
    must adhere to, ensuring consistent behavior across different types.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an agent.

        Args:
            config: Optional configuration for the agent
        """
        self.config = config or {}

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input and generate a response.

        This is the main method that must be implemented by all agents.
        It takes the context of the interaction and returns a response.

        Args:
            context: The context for this interaction

        Returns:
            The agent's response

        Raises:
            ValueError: If the input is invalid
            RuntimeError: If processing fails
        """

    @abstractmethod
    def can_handle(self, context: AgentContext) -> float:
        """
        Determine if this agent can handle the given context.

        This method allows the orchestrator to select the most
        appropriate agent for a given interaction.

        Args:
            context: The context for this interaction

        Returns:
            A score between 0 and 1 indicating how well this agent can handle the context
        """

    def initialize(self) -> None:
        """
        Initialize the agent.

        This method is called when the agent is first created.
        Override this to perform any necessary setup.
        """

    def close(self) -> None:
        """
        Close the agent and release resources.

        This method is called when the agent is no longer needed.
        Override this to perform any necessary cleanup.
        """


class SimpleTextAgent(Agent):
    """
    A simple text-based agent that provides basic responses.

    This agent serves as a demonstration of the Agent interface
    and provides simple responses based on persona traits. In a
    real implementation, this would likely use an LLM or other
    sophisticated text generation.
    """

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input and generate a simple text response.

        Args:
            context: The context for this interaction

        Returns:
            A simple text response
        """
        persona = context.persona
        user_input = context.user_input

        # Extract persona traits for response generation
        traits = persona.traits[:3] if persona.traits else ["helpful"]
        traits_str = ", ".join(traits)

        # Create a simple response based on the persona
        response_text = (
            f"I've received your message: '{user_input}'. "
            f"As {persona.name}, who is {persona.interaction_style} and {traits_str}, "
            f"I'd respond based on my expertise and character."
        )

        # In a real implementation, this would use:
        # - NLP to understand the user's intent
        # - An LLM to generate a contextually appropriate response
        # - Tools and knowledge retrieval for enhanced capabilities

        return AgentResponse(
            text=response_text,
            confidence=0.8,
            metadata={
                "agent_type": "SimpleTextAgent",
                "persona_traits_used": traits,
                "response_type": "text_only",
            },
        )

    def can_handle(self, context: AgentContext) -> float:
        """
        This agent can handle any basic text interaction.

        In a real system with multiple agents, this would be more
        sophisticated, perhaps using intent detection to determine
        if this agent is appropriate.

        Args:
            context: The context for this interaction

        Returns:
            A score between 0 and 1
        """
        # This simple agent always returns a moderate score
        # A more sophisticated agent would analyze the input
        # to determine how well it can handle the request
        return 0.7


# Agent factory function
def create_agent(agent_type: str, config: Optional[Dict[str, Any]] = None) -> Agent:
    """
    Create an agent of the specified type.

    This factory function allows for the dynamic creation of
    different agent types based on configuration.

    Args:
        agent_type: The type of agent to create
        config: Optional configuration for the agent

    Returns:
        An initialized agent instance

    Raises:
        ValueError: If the agent type is unknown
    """
    config = config or {}

    if agent_type == "simple_text":
        return SimpleTextAgent(config)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
