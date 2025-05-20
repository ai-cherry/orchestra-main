"""
Conversation Service for AI Orchestration System.

This module provides orchestration of conversation flows, history management,
and integration with the memory system for conversation persistence.
"""

import logging
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Any

from core.orchestrator.src.config.config import settings
from core.orchestrator.src.services.event_bus import get_event_bus

# Updated import to use new memory manager
from core.orchestrator.src.services.memory_service import get_memory_manager
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Handle both pydantic v1 and v2
try:
    from pydantic.v1 import BaseModel  # For pydantic v2
except ImportError:
    from pydantic import BaseModel  # For pydantic v1

# Configure logging
logger = logging.getLogger(__name__)


class ConversationState(BaseModel):
    """
    Represents the state of an active conversation.

    This model tracks the current state of a conversation session including
    the associated user, session identifier, and statistics.
    """

    user_id: str
    session_id: str
    persona_active: Optional[str] = None
    start_time: datetime = datetime.utcnow()
    last_activity: datetime = datetime.utcnow()
    turn_count: int = 0


class ConversationService:
    """
    Service for conversation operations in the orchestration system.

    This class provides conversation state management, history retrieval,
    and handles the lifecycle of conversations between users and AI agents.
    """

    def __init__(self):
        """Initialize the conversation service."""
        self._event_bus = get_event_bus()
        self._memory_manager = (
            get_memory_manager()
        )  # Updated to use the new memory manager
        self._active_conversations = {}  # user_id -> ConversationState
        logger.info("ConversationService initialized")

    async def start_conversation(
        self, user_id: str, persona_name: Optional[str] = None
    ) -> str:
        """
        Start a new conversation session.

        Args:
            user_id: The user ID starting the conversation
            persona_name: Optional persona to activate for this conversation

        Returns:
            The new session ID
        """
        session_id = str(uuid.uuid4())

        # Store conversation start in memory
        conversation_start = MemoryItem(
            user_id=user_id,
            item_type="conversation_event",
            content={
                "event_type": "conversation_started",
                "persona_name": persona_name,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        try:
            # Directly await the async method
            await self._memory_manager.add_memory_item(conversation_start)
        except Exception as e:
            logger.error(f"Failed to store conversation start: {e}")

        # Track active conversation
        self._active_conversations[user_id] = ConversationState(
            user_id=user_id,
            session_id=session_id,
            persona_active=persona_name,
            start_time=datetime.utcnow(),
            turn_count=0,
        )

        # Publish event using async method
        try:
            await self._event_bus.publish_async(
                "conversation_started",
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "persona_name": persona_name,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish conversation_started event: {e}")
            # Non-critical, continue execution

        return session_id

    async def end_conversation(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """
        End an active conversation session.

        Args:
            user_id: The user ID to end conversation for
            session_id: Optional specific session to end, otherwise ends active session

        Returns:
            True if conversation was found and ended, False otherwise
        """
        # Retrieve the active conversation if session_id is not specified
        conversation = self._active_conversations.get(user_id)

        if not conversation:
            logger.warning(f"No active conversation found for user: {user_id}")
            return False

        # Check if specific session_id matches
        if session_id and conversation.session_id != session_id:
            logger.warning(f"Session ID mismatch for user {user_id}")
            return False

        # Store conversation end in memory
        conversation_end = MemoryItem(
            user_id=user_id,
            item_type="conversation_event",
            content={
                "event_type": "conversation_ended",
                "persona_name": conversation.persona_active,
                "session_id": conversation.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": (
                    datetime.utcnow() - conversation.start_time
                ).total_seconds(),
                "turn_count": conversation.turn_count,
                "success_status": True,  # Added field to indicate normal conversation end
            },
        )

        try:
            # Directly await the async method
            await self._memory_manager.add_memory_item(conversation_end)
        except Exception as e:
            logger.error(
                f"Failed to store conversation end for user {user_id}, session {conversation.session_id}: {str(e)}",
                exc_info=True,
            )

        # Remove from active conversations
        del self._active_conversations[user_id]

        # Publish event using async method
        try:
            await self._event_bus.publish_async(
                "conversation_ended",
                {
                    "user_id": user_id,
                    "session_id": conversation.session_id,
                    "persona_name": conversation.persona_active,
                    "turn_count": conversation.turn_count,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish conversation_ended event: {e}")
            # Non-critical, continue execution

        return True

    def get_active_conversation(self, user_id: str) -> Optional[ConversationState]:
        """
        Get the currently active conversation for a user.

        Args:
            user_id: The user ID to get active conversation for

        Returns:
            The active conversation state or None if no active conversation
        """
        return self._active_conversations.get(user_id)

    async def record_message(
        self,
        user_id: str,
        content: str,
        is_user: bool,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Record a message in the conversation.

        Args:
            user_id: The user ID the message belongs to
            content: The message content
            is_user: True if this is a user message, False for AI responses
            metadata: Optional metadata for the message
            session_id: Optional session ID, uses active session if not provided

        Returns:
            The ID of the recorded message
        """
        conversation = self._active_conversations.get(user_id)

        # Use provided session_id or get from active conversation
        if session_id is None and conversation:
            session_id = conversation.session_id

        # Create memory item for the message
        message_item = MemoryItem(
            user_id=user_id,
            item_type="conversation_message",
            content={
                "message": content,
                "is_user": is_user,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
            },
        )

        # Add metadata if provided
        if metadata:
            message_item.content["metadata"] = metadata

        # Add persona context if available
        if conversation and conversation.persona_active:
            message_item.content["persona_name"] = conversation.persona_active

        # Store in memory using async method
        try:
            # Directly await the async method
            message_id = await self._memory_manager.add_memory_item(message_item)
        except Exception as e:
            logger.error(f"Failed to store conversation message: {e}")
            message_id = str(uuid.uuid4())  # Generate a fallback ID

        # Update turn count if this is an active conversation
        if conversation:
            if is_user:
                conversation.turn_count += 1
            conversation.last_activity = datetime.utcnow()

        # Publish event using async method
        try:
            await self._event_bus.publish_async(
                "conversation_message_added",
                {
                    "user_id": user_id,
                    "message_id": message_id,
                    "is_user": is_user,
                    "session_id": session_id,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish conversation_message_added event: {e}")
            # Non-critical, continue execution

        return message_id

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        persona_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get formatted conversation history.

        This method retrieves conversation history from memory and formats it
        as a structured conversation with user/assistant turns.

        Args:
            user_id: The user ID to get history for
            session_id: Optional specific session ID to retrieve
            limit: Maximum number of messages to retrieve
            persona_name: Optional persona to filter by

        Returns:
            List of conversation messages as structured dictionaries
        """
        # Create filters dictionary for persona_name if provided
        filters = None
        if persona_name:
            filters = {"persona_name": persona_name}

        try:
            # Directly await the async method
            raw_items = await self._memory_manager.get_conversation_history(
                user_id=user_id,
                session_id=session_id,
                limit=limit,
                filters=filters,
            )
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            raw_items = []  # Return empty list on error

        # Format the items in a conversation-friendly structure
        formatted_messages = []
        for item in raw_items:
            if item.item_type != "conversation_message":
                continue  # Skip non-message items

            message = {
                "id": item.id,
                "role": "user" if item.content.get("is_user") else "assistant",
                "content": item.content.get("message", ""),
                "timestamp": item.content.get("timestamp"),
            }

            # Add metadata if available
            if "metadata" in item.content:
                message["metadata"] = item.content["metadata"]

            formatted_messages.append(message)

        return formatted_messages

    async def add_memory_item_async(self, item: MemoryItem) -> str:
        """
        Add a memory item and publish an event asynchronously.

        This is the async variant for memory operations, suitable for
        use with asynchronous handlers and flows.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        return await self._memory_manager.add_memory_item(item)


@lru_cache()
def get_conversation_service() -> ConversationService:
    """
    Get a configured conversation service instance.

    This function provides dependency injection for the conversation service.
    It uses lru_cache to ensure only one instance is created.

    Returns:
        A configured conversation service instance
    """
    return ConversationService()
