"""
Phidata Chat Endpoint for AI Orchestration System.

This module provides API endpoints for integrating with the Phidata Agent UI,
supporting the /phidata/chat endpoint to process chat requests with proper markdown
formatting and structured output handling.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from packages.ingestion.src.api.chat_integration import (
    get_ingestion_middleware,
    process_phidata_message,
    IngestionChatMiddleware,
)
from pydantic import BaseModel, Field

from core.orchestrator.src.api.dependencies.llm import get_llm_client
from core.orchestrator.src.api.dependencies.memory import get_memory_manager
from core.orchestrator.src.agents.agent_registry import get_agent_registry
from core.orchestrator.src.api.utils.format_structured_output import (
    format_structured_output_as_markdown,
)
from packages.shared.src.llm_client.interface import LLMClient
from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class PhidataRequest(BaseModel):
    """
    Request model for Phidata chat endpoint.

    This model captures the structure expected by the Phidata Agent UI.
    It includes the message content as well as session and user identification.
    """

    message: str = Field(..., min_length=1, description="User's message text")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")

    # Optional fields
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="List of tools to use")


class PhidataResponse(BaseModel):
    """
    Response model for Phidata chat endpoint.

    This model defines the structure expected by the Phidata Agent UI
    for responses from the API. Includes support for markdown content and
    tool call visibility control.
    """

    response_content: str = Field(..., description="Assistant's response text (markdown supported)")
    response_type: str = Field("text", description="Type of response (text, image, etc.)")
    content_format: str = Field("markdown", description="Format of response content (markdown, plain, etc.)")

    # Optional fields
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    agent_name: Optional[str] = Field(None, description="Agent name for display")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="List of tool calls made during processing")
    timestamp: Optional[str] = Field(None, description="Response timestamp")


@router.post("/phidata/chat", response_model=PhidataResponse, tags=["phidata"])
async def phidata_chat(
    request: PhidataRequest,
    req: Request,
    memory: MemoryManager = Depends(get_memory_manager),
    llm_client: Optional[LLMClient] = Depends(get_llm_client),
    ingestion_middleware: Optional[IngestionChatMiddleware] = Depends(get_ingestion_middleware),
) -> PhidataResponse:
    """
    Process a Phidata chat request with markdown formatting support.

    This endpoint receives input from the Phidata Agent UI, processes it through
    the appropriate agent, and returns a well-formatted markdown response suitable
    for display in the UI. Supports:

    1. Markdown formatting for all text responses
    2. Structured output formatting for data like movie scripts, analysis results, etc.
    3. Tool call visibility control
    4. Session management for conversation persistence

    Args:
        request: The Phidata chat request
        req: The HTTP request object
        memory: Memory manager for conversation history
        llm_client: LLM client for generating responses

    Returns:
        A PhidataResponse containing the agent's well-formatted response

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Get agent registry
        agent_registry = get_agent_registry()

        logger.info(
            f"Processing Phidata chat request for user_id: {request.user_id}, " f"session_id: {request.session_id}"
        )

        # Determine the agent type to use
        agent_type = request.agent_id if request.agent_id else None

        # Get conversation history
        history_items = await memory.get_conversation_history_async(
            user_id=request.user_id, session_id=request.session_id, limit=10
        )

        # Create agent context
        from core.orchestrator.src.agents.agent_base import AgentContext
        from core.orchestrator.src.config.loader import load_persona_configs

        # Get the default persona if persona middleware didn't set one
        personas = load_persona_configs()
        default_persona = next(iter(personas.values())) if personas else None

        # Get active persona from request state or use default
        persona_config = getattr(req.state, "active_persona", default_persona)
        if not persona_config:
            raise HTTPException(status_code=500, detail="No persona configuration available")

        # Check if the message is an ingestion command
        ingestion_response = None
        if ingestion_middleware:
            ingestion_response = await process_phidata_message(
                message=request.message,
                user_id=request.user_id,
                session_id=request.session_id,
                middleware=ingestion_middleware,
            )

        # Update metadata with ingestion task info if present
        request_metadata = request.metadata or {}
        if ingestion_response:
            request_metadata.update({"ingestion_task": ingestion_response})

        # Create agent context
        context = AgentContext(
            user_input=request.message,
            user_id=request.user_id,
            persona=persona_config,
            conversation_history=history_items,
            session_id=request.session_id,
            interaction_id=str(request.session_id),
            metadata=request_metadata,
        )

        # Get appropriate agent
        try:
            agent = agent_registry.get_agent(agent_type)
            logger.info(f"Using agent type: {agent_type or 'default'}")
        except KeyError:
            agent = agent_registry.select_agent_for_context(context)
            logger.info(f"Selected agent based on context: {agent.agent_type}")

        # Process with agent
        try:
            agent_response = await agent.process(context)
        except Exception as e:
            logger.error(f"Agent processing failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

        # Create memory item for the response
        memory_item = MemoryItem(
            user_id=request.user_id,
            session_id=request.session_id,
            item_type="message",
            persona_active=persona_config.name,
            text_content=agent_response.text,
            timestamp=datetime.utcnow(),
            metadata={
                "source": "agent",
                "agent_type": agent.agent_type,
                "confidence": agent_response.confidence,
            },
        )

        # Save to memory
        await memory.add_memory_item_async(memory_item)

        # Extract tool calls and settings
        tool_calls = agent_response.metadata.get("tool_calls")
        show_tool_calls = True  # Default to showing tool calls in development

        # Check if agent has specific show_tool_calls setting
        if hasattr(agent, "settings") and isinstance(agent.settings, dict):
            show_tool_calls = agent.settings.get("show_tool_calls", True)

        # Handle structured output if present
        response_content = agent_response.text
        content_format = "markdown"  # Default to markdown

        # Check if response is a structured output that should be formatted
        if isinstance(agent_response.text, dict) or (
            agent_response.metadata
            and agent_response.metadata.get("content_type") in ["application/json", "structured"]
        ):
            # This appears to be a structured output, format it as markdown
            output_type = agent_response.metadata.get("output_type") if agent_response.metadata else None
            response_content = format_structured_output_as_markdown(agent_response.text, output_type)
            logger.info(f"Formatted structured output as markdown for response (type: {output_type})")

        # If this was an ingestion command, augment the agent response
        # with information about the ingestion task
        response_metadata = agent_response.metadata or {}
        if ingestion_response:
            response_metadata["ingestion_task"] = ingestion_response

            # If we have an ingestion message, we may want to append it to the response
            if "message" in ingestion_response:
                # Add a note about the ingestion task to the response
                ingestion_msg = f"\n\n---\n**File Ingestion:** {ingestion_response['message']}"
                response_content = response_content + ingestion_msg

        # Get agent name for UI display
        agent_name = agent.name if hasattr(agent, "name") else agent.agent_type

        # Create response with proper markdown formatting
        response = PhidataResponse(
            response_content=response_content,
            response_type="text",  # Default to text
            content_format=content_format,  # Set format to markdown
            session_id=request.session_id,
            user_id=request.user_id,
            agent_id=agent.agent_type,
            agent_name=agent_name,
            metadata=response_metadata,
            # Only include tool calls if show_tool_calls is enabled
            tool_calls=tool_calls if show_tool_calls else None,
            timestamp=datetime.utcnow().isoformat(),
        )

        return response

    except Exception as e:
        logger.error(f"Phidata chat processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process Phidata chat: {str(e)}")
