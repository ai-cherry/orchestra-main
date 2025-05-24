"""
Orchestrator module for AI Orchestration System.

This module provides the orchestration layer that ties together the memory,
personas, and agents components to handle user interactions.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
import uuid
from datetime import datetime

from core.orchestrator.src.core.memory import (
    MemoryItem,
    MemoryManager,
    get_memory_manager,
)
from core.orchestrator.src.core.personas import (
    PersonaConfig,
    PersonaManager,
    get_persona_manager,
)
from core.orchestrator.src.core.agents import (
    Agent,
    AgentContext,
    AgentResponse,
    get_agent_registry,
)

# Configure logging
logger = logging.getLogger(__name__)


class InteractionResult:
    """
    Result of an interaction processing.

    This class encapsulates the result of processing a user interaction,
    including the response message and metadata.
    """

    def __init__(
        self,
        message: str,
        persona_id: str,
        persona_name: str,
        session_id: str,
        interaction_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an interaction result.

        Args:
            message: The response message
            persona_id: The ID of the persona used
            persona_name: The name of the persona used
            session_id: The session ID
            interaction_id: The interaction ID
            metadata: Optional metadata
        """
        self.message = message
        self.persona_id = persona_id
        self.persona_name = persona_name
        self.session_id = session_id
        self.interaction_id = interaction_id
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}


class EventEmitter:
    """
    Simple event emitter for orchestrator events.

    This class provides a basic publish-subscribe mechanism for
    handling events within the orchestrator.
    """

    def __init__(self):
        """Initialize the event emitter."""
        self._handlers: Dict[str, List[callable]] = {}

    def subscribe(self, event: str, handler: callable) -> None:
        """
        Subscribe to an event.

        Args:
            event: The event to subscribe to
            handler: The handler function
        """
        if event not in self._handlers:
            self._handlers[event] = []

        self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: callable) -> None:
        """
        Unsubscribe from an event.

        Args:
            event: The event to unsubscribe from
            handler: The handler function
        """
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h != handler]

    def publish(self, event: str, data: Any = None) -> None:
        """
        Publish an event.

        Args:
            event: The event to publish
            data: The event data
        """
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event}: {e}")


class Orchestrator:
    """
    Main orchestrator for AI interactions.

    This class coordinates the memory, personas, and agents components
    to process user interactions and generate responses.
    """

    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        persona_manager: Optional[PersonaManager] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            memory_manager: Optional memory manager
            persona_manager: Optional persona manager
        """
        self._memory_manager = memory_manager or get_memory_manager()
        self._persona_manager = persona_manager or get_persona_manager()
        self._agent_registry = get_agent_registry()
        self._events = EventEmitter()

        logger.info("Orchestrator initialized")

    def subscribe(self, event: str, handler: callable) -> None:
        """
        Subscribe to an orchestrator event.

        Args:
            event: The event to subscribe to
            handler: The handler function
        """
        self._events.subscribe(event, handler)

    def unsubscribe(self, event: str, handler: callable) -> None:
        """
        Unsubscribe from an orchestrator event.

        Args:
            event: The event to unsubscribe from
            handler: The handler function
        """
        self._events.unsubscribe(event, handler)

    async def process_interaction(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> InteractionResult:
        """
        Process a user interaction and generate a response.

        Args:
            user_input: The user's input message
            user_id: The ID of the user
            session_id: Optional session ID for conversation continuity
            persona_id: Optional ID of persona to use
            context: Additional context for the interaction

        Returns:
            The interaction result
        """
        # Generate IDs if not provided
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        interaction_id = f"interaction_{uuid.uuid4().hex}"
        context = context or {}

        try:
            # Get persona
            persona = self._persona_manager.get_persona(persona_id)
            logger.info(f"Using persona {persona.name} for interaction {interaction_id}")

            # Publish interaction started event
            self._events.publish(
                "interaction_started",
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                    "persona_id": persona_id,
                    "persona_name": persona.name,
                },
            )

            # Store user message in memory
            user_memory_id = self._memory_manager.add_memory(
                user_id=user_id,
                content=user_input,
                session_id=session_id,
                item_type="conversation",
                metadata={
                    "source": "user",
                    "interaction_id": interaction_id,
                    **context,
                },
            )

            # Get conversation history
            conversation_history = self._memory_manager.get_conversation_history(user_id=user_id, session_id=session_id)

            # Create agent context
            agent_context = AgentContext(
                user_input=user_input,
                user_id=user_id,
                persona=persona,
                conversation_history=conversation_history,
                session_id=session_id,
                interaction_id=interaction_id,
                metadata=context,
            )

            # Select and execute agent
            agent = self._select_agent_for_context(agent_context)

            # Process with agent
            agent_response = await agent.process(agent_context)

            # Format response according to persona
            formatted_response = self._persona_manager.format_response(agent_response.text, persona_id)

            # Store response in memory
            response_metadata = {
                "source": "system",
                "interaction_id": interaction_id,
                "agent_type": agent.agent_type,
                "confidence": agent_response.confidence,
            }

            # Add agent response metadata if available
            if agent_response.metadata:
                response_metadata.update(agent_response.metadata)

            # Add context metadata
            response_metadata.update(context)

            response_memory_id = self._memory_manager.add_memory(
                user_id=user_id,
                content=formatted_response,
                session_id=session_id,
                item_type="conversation",
                metadata=response_metadata,
            )

            # Create result metadata
            result_metadata = {
                "agent_type": agent.agent_type,
                "confidence": agent_response.confidence,
                "user_memory_id": user_memory_id,
                "response_memory_id": response_memory_id,
            }

            # Add agent response metadata if available
            if agent_response.metadata:
                result_metadata.update(agent_response.metadata)

            # Create result
            result = InteractionResult(
                message=formatted_response,
                persona_id=persona_id or "default",
                persona_name=persona.name,
                session_id=session_id,
                interaction_id=interaction_id,
                metadata=result_metadata,
            )

            # Create event data
            complete_event_data = {
                "user_id": user_id,
                "session_id": session_id,
                "interaction_id": interaction_id,
                "persona_name": persona.name,
                "user_memory_id": user_memory_id,
                "response_memory_id": response_memory_id,
                "result": result,
            }

            # Publish interaction complete event
            self._events.publish("interaction_complete", complete_event_data)

            return result
        except Exception as e:
            logger.error(f"Error processing interaction: {e}", exc_info=True)

            # Publish interaction error event
            self._events.publish(
                "interaction_error",
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "interaction_id": interaction_id,
                    "persona_id": persona_id,
                    "error": str(e),
                },
            )

            # Create fallback result
            fallback_message = "I'm sorry, but I encountered an error processing your request."
            result = InteractionResult(
                message=fallback_message,
                persona_id=persona_id or "default",
                persona_name="System",
                session_id=session_id,
                interaction_id=interaction_id,
                metadata={"error": str(e)},
            )

            return result

    def _select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context.

        Args:
            context: The agent context

        Returns:
            The selected agent
        """
        # Use the agent registry to select an agent
        return self._agent_registry.select_agent_for_context(context)


# Global orchestrator instance
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    """
    Get the global orchestrator instance.

    Returns:
        The orchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = Orchestrator()

    return _orchestrator
