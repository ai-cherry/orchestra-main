"""
Conversation API endpoints for Orchestra AI.

This module provides endpoints for conversational interactions.
"""

import logging

from fastapi import APIRouter, HTTPException

from core.api.models.requests import ConversationRequest
from core.api.models.responses import ConversationResponse
from core.business.workflows.base import get_workflow_engine
from core.services.agents.base import AgentCapability, get_agent_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversation", tags=["conversation"])

@router.post("/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest) -> ConversationResponse:
    """
    Handle a conversational interaction.

    This endpoint processes user messages through the conversation workflow,
    maintaining context and using appropriate personas.
    """
    try:
        # Get workflow engine
        workflow_engine = get_workflow_engine()

        # Execute conversation workflow
        context = await workflow_engine.execute_workflow(
            workflow_name="conversation_workflow",
            inputs={
                "user_id": request.user_id,
                "user_input": request.message,
                "context": request.context or {},
                "persona_id": request.persona_id,
            },
        )

        # Extract results
        response_text = context.outputs.get("response", "I'm sorry, I couldn't generate a response.")
        intent = context.outputs.get("intent")

        return ConversationResponse(
            success=True,
            response=response_text,
            intent=intent,
            persona_used=request.persona_id,
            conversation_id=str(context.workflow_id),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent-chat", response_model=ConversationResponse)
async def agent_chat(request: ConversationRequest) -> ConversationResponse:
    """
    Chat directly with a conversational agent.

    This endpoint sends messages directly to a conversational agent
    without going through the workflow engine.
    """
    try:
        # Get agent manager
        agent_manager = get_agent_manager()

        # Find a conversational agent
        conv_agents = agent_manager.find_agents_by_capability(AgentCapability.CONVERSATION)

        if not conv_agents:
            raise HTTPException(status_code=503, detail="No conversational agents available")

        # Use the first available agent
        agent = conv_agents[0]

        # Send message to agent
        from core.services.agents.base import AgentMessage

        message = AgentMessage(
            sender_id=request.user_id,
            content=request.message,
            metadata={
                "type": "conversation",
                "context": request.context,
                "persona_id": request.persona_id,
            },
        )

        # Process message
        response_message = await agent.process_message(message)

        if not response_message:
            raise HTTPException(status_code=500, detail="Agent did not return a response")

        return ConversationResponse(
            success=True,
            response=response_message.content,
            persona_used=request.persona_id,
            conversation_id=str(message.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_conversation_history(user_id: str, limit: int = 10) -> dict:
    """
    Get conversation history for a user.

    Args:
        user_id: User ID to get history for
        limit: Maximum number of conversations to return

    Returns:
        Dictionary containing conversation history
    """
    try:
        from core.services.memory.unified_memory import get_memory_service

        memory_service = get_memory_service()

        # Search for user's conversations
        conversations = await memory_service.search(
            query=f"user:{user_id}",
            limit=limit,
            metadata_filter={"type": "interaction"},
        )

        return {
            "success": True,
            "user_id": user_id,
            "conversations": conversations,
            "count": len(conversations),
        }

    except Exception as e:
        logger.error(f"Error getting conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
