"""
Base Agent Orchestration Service for AI Orchestration System.

This module provides a base class for agent orchestrators to reduce code duplication
and standardize core functionality across different orchestrator implementations.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.orchestrator.src.agents.agent_base import AgentContext
from core.orchestrator.src.agents.simplified_agent_registry import get_simplified_agent_registry

# Import the settings instance directly
from core.orchestrator.src.config.config import settings
from core.services.events.event_bus import get_event_bus
from core.orchestrator.src.services.memory_service import get_memory_service
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)

class BaseOrchestrator(ABC):
    """
    Base class for agent orchestrators that standardizes common functionality.

    This abstract base class provides core functionality for:
    1. Common initialization and resource handling
    2. Memory interactions
    3. Event publishing
    4. Context retrieval

    Subclasses must implement specific persona management and agent execution logic.
    """

    def __init__(self):
        """Initialize common orchestrator components."""
        self._event_bus = get_event_bus()
        self._memory_service = get_memory_service()
        self._agent_registry = get_simplified_agent_registry()
        # Use the global settings instance directly
        self._settings = settings

        # Register with event bus
        self._event_bus.subscribe("persona_selected", self._on_persona_selected)

        logger.info(f"{self.__class__.__name__} initialized")

    def initialize(self) -> None:
        """Initialize the orchestrator resources."""
        # Subclasses can override to add specific initialization

    def close(self) -> None:
        """Close the orchestrator and release resources."""
        # Unsubscribe from events
        self._event_bus.unsubscribe("persona_selected", self._on_persona_selected)

        # Subclasses can override to add specific cleanup

    def _on_persona_selected(self, event_data: Dict[str, Any]) -> None:
        """
        Handle persona selection events.

        Args:
            event_data: Event data containing persona information
        """
        persona_name = event_data.get("name", "unknown")
        user_id = event_data.get("user_id", "unknown")

        logger.info(f"Persona selected for user {user_id}: {persona_name}")

    @abstractmethod
    async def process_interaction(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user interaction and generate a response.

        This abstract method must be implemented by subclasses to define
        the specific interaction flow for different orchestrator types.

        Args:
            user_input: The user's input message
            user_id: The ID of the user
            session_id: Optional session ID for conversation continuity
            persona_id: Optional ID of persona to use
            context: Additional context for the interaction

        Returns:
            Dict containing the response and metadata
        """

    async def _add_memory_async(self, item: MemoryItem) -> str:
        """
        Add a memory item asynchronously.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added memory item
        """
        # Use the memory service's async method if available
        if hasattr(self._memory_service, "add_memory_item_async"):
            return await self._memory_service.add_memory_item_async(item)

        # Fall back to synchronous add in executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._memory_service.add_memory_item, item)

    async def _retrieve_context(
        self, user_id: str, session_id: str, current_input: str, persona: PersonaConfig
    ) -> List[MemoryItem]:
        """
        Retrieve relevant context for the current interaction.

        This method combines:
        1. Recent conversation history
        2. Semantic search results if available
        3. Any persona-specific context

        Args:
            user_id: The ID of the user
            session_id: The session ID
            current_input: The current user input
            persona: The selected persona

        Returns:
            List of relevant memory items
        """
        # Get settings for context retrieval
        settings = self._settings
        history_limit = getattr(settings, "CONVERSATION_HISTORY_LIMIT", 10)

        # Use async version if available to avoid blocking
        if hasattr(self._memory_service, "get_conversation_history_async"):
            conversation_history = await self._memory_service.get_conversation_history_async(
                user_id=user_id, session_id=session_id, limit=history_limit
            )
        else:
            # Fall back to synchronous version in a thread pool
            loop = asyncio.get_running_loop()
            conversation_history = await loop.run_in_executor(
                None,
                lambda: self._memory_service.get_conversation_history(
                    user_id=user_id, session_id=session_id, limit=history_limit
                ),
            )

        # In a real implementation, we would:
        # 1. Generate an embedding for the current input
        # 2. Perform semantic search
        # 3. Merge and deduplicate results

        # For now, we'll just return the conversation history
        return conversation_history

    def _create_agent_context(
        self,
        user_input: str,
        user_id: str,
        persona: PersonaConfig,
        session_id: str,
        interaction_id: str,
        relevant_context: List[MemoryItem],
        context: Dict[str, Any],
        max_context_items: int = 20,
    ) -> AgentContext:
        """
        Create an agent context with all necessary information.

        Args:
            user_input: The user's input message
            user_id: The ID of the user
            persona: The selected persona
            session_id: The session ID
            interaction_id: The unique interaction ID
            relevant_context: Relevant context from memory
            context: Additional context for the interaction
            max_context_items: Maximum number of context items to include

        Returns:
            The agent context
        """
        # Keep conversation history small for performance
        filtered_context = relevant_context
        if len(filtered_context) > max_context_items:
            filtered_context = filtered_context[-max_context_items:]

        return AgentContext(
            user_input=user_input,
            user_id=user_id,
            persona=persona,
            conversation_history=filtered_context,
            session_id=session_id,
            interaction_id=interaction_id,
            metadata=context,
        )

    def _publish_interaction_complete(
        self,
        user_id: str,
        session_id: str,
        interaction_id: str,
        persona_name: str,
        user_memory_id: str,
        response_memory_id: str,
    ) -> None:
        """
        Publish an interaction_complete event.

        Args:
            user_id: The ID of the user
            session_id: The session ID
            interaction_id: The unique interaction ID
            persona_name: The name of the active persona
            user_memory_id: The ID of the user's memory item
            response_memory_id: The ID of the response memory item
        """
        self._event_bus.publish(
            "interaction_complete",
            {
                "user_id": user_id,
                "session_id": session_id,
                "interaction_id": interaction_id,
                "persona_name": persona_name,
                "user_memory_id": user_memory_id,
                "response_memory_id": response_memory_id,
            },
        )

    def _publish_interaction_error(
        self,
        user_id: str,
        session_id: str,
        interaction_id: str,
        error: str,
        persona_id: Optional[str] = None,
    ) -> None:
        """
        Publish an interaction_error event.

        Args:
            user_id: The ID of the user
            session_id: The session ID
            interaction_id: The unique interaction ID
            error: The error message
            persona_id: Optional ID of the persona
        """
        event_data = {
            "user_id": user_id,
            "session_id": session_id,
            "interaction_id": interaction_id,
            "error": error,
        }

        if persona_id:
            event_data["persona_id"] = persona_id

        self._event_bus.publish("interaction_error", event_data)
