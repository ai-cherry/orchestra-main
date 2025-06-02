"""
Conversation Endpoints for AI Orchestration System.

This module provides API endpoints for managing conversations,
including starting/ending conversations and recording messages.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.orchestrator.src.services.conversation_service import get_conversation_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/conversations", tags=["conversations"])

class MessageInput(BaseModel):
    """Input model for adding a message to a conversation."""

    content: str = Field(..., min_length=1, description="Message content")
    is_user: bool = Field(
        True,
        description="Whether this is a user message (True) or system message (False)",
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the message")

class ConversationStartInput(BaseModel):
    """Input model for starting a conversation."""

    user_id: str = Field(..., description="User identifier")
    persona_name: Optional[str] = Field(None, description="Optional persona name to activate")

class ConversationEndInput(BaseModel):
    """Input model for ending a conversation."""

    user_id: str = Field(..., description="User identifier")

@router.post("/start", response_model=Dict[str, str])
async def start_conversation(
    input_data: ConversationStartInput,
) -> Dict[str, str]:
    """
    Start a new conversation session.

    Args:
        input_data: Contains user_id and optional persona_name

    Returns:
        Dictionary with the session_id and status

    Raises:
        HTTPException: If the operation fails
    """
    conversation_service = get_conversation_service()

    try:
        session_id = await conversation_service.start_conversation(
            user_id=input_data.user_id, persona_name=input_data.persona_name
        )
        return {"session_id": session_id, "status": "created"}
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/{session_id}/end", response_model=Dict[str, str])
async def end_conversation(
    session_id: str,
    input_data: ConversationEndInput,
) -> Dict[str, str]:
    """
    End an active conversation session.

    Args:
        session_id: The session ID to end
        input_data: Contains user_id

    Returns:
        Dictionary with the status

    Raises:
        HTTPException: If the conversation is not found
    """
    conversation_service = get_conversation_service()

    try:
        result = await conversation_service.end_conversation(user_id=input_data.user_id, session_id=session_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation not found for user {input_data.user_id}",
            )

        return {"session_id": session_id, "status": "ended"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

@router.post("/{session_id}/messages", response_model=Dict[str, str])
async def add_message(
    session_id: str,
    input_data: MessageInput,
    user_id: str = Query(..., description="User identifier"),
) -> Dict[str, str]:
    """
    Add a message to a conversation.

    Args:
        session_id: The session ID for the conversation
        input_data: Contains the message content, is_user flag, and optional metadata
        user_id: User identifier (from query parameter)

    Returns:
        Dictionary with the message_id and status

    Raises:
        HTTPException: If the operation fails
    """
    conversation_service = get_conversation_service()

    try:
        message_id = await conversation_service.record_message(
            user_id=user_id,
            content=input_data.content,
            is_user=input_data.is_user,
            metadata=input_data.metadata,
            session_id=session_id,
        )
        return {"message_id": message_id, "status": "added"}
    except Exception as e:
        logger.error(f"Failed to add message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

@router.get("/{session_id}/history", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    session_id: str,
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of messages to retrieve"),
    persona_name: Optional[str] = Query(None, description="Filter by persona name"),
) -> List[Dict[str, Any]]:
    """
    Get the history of a conversation.

    Args:
        session_id: The session ID to retrieve history for
        user_id: User identifier (from query parameter)
        limit: Maximum number of messages to retrieve
        persona_name: Optional filter by persona name

    Returns:
        List of conversation messages

    Raises:
        HTTPException: If the operation fails
    """
    conversation_service = get_conversation_service()

    try:
        history = await conversation_service.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            persona_name=persona_name,
        )
        return history
    except Exception as e:
        logger.error(f"Failed to retrieve conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation history: {str(e)}")

@router.get("/active", response_model=Dict[str, Any])
async def get_active_conversation(
    user_id: str = Query(..., description="User identifier"),
) -> Dict[str, Any]:
    """
    Get the currently active conversation for a user.

    Args:
        user_id: User identifier

    Returns:
        Active conversation state or empty dict if none

    Raises:
        HTTPException: If the operation fails
    """
    conversation_service = get_conversation_service()

    try:
        conversation = conversation_service.get_active_conversation(user_id)
        if conversation:
            return {
                "user_id": conversation.user_id,
                "session_id": conversation.session_id,
                "persona_active": conversation.persona_active,
                "start_time": conversation.start_time.isoformat(),
                "last_activity": conversation.last_activity.isoformat(),
                "turn_count": conversation.turn_count,
                "status": "active",
            }
        else:
            return {"status": "no_active_conversation"}
    except Exception as e:
        logger.error(f"Failed to get active conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get active conversation: {str(e)}")
