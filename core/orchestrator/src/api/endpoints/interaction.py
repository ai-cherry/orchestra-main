"""
Interaction Endpoints for AI Orchestration System.

This module provides API endpoints for user interactions with the system,
allowing conversations with AI personas while storing conversation history.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core.orchestrator.src.api.dependencies.llm import get_llm_client
from core.orchestrator.src.api.dependencies.memory import get_memory_manager
from core.orchestrator.src.config.settings import get_settings
from packages.shared.src.llm_client.interface import LLMClient
from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class UserInput(BaseModel):
    """User input model for interaction endpoint."""
    
    text: str = Field(..., min_length=1, description="User's message text")
    user_id: Optional[str] = Field(None, description="User identifier")


@router.post("/interact", response_model=Dict[str, str], tags=["interaction"])
async def interact(
    user_input: UserInput,
    request: Request,
    memory: MemoryManager = Depends(get_memory_manager),
    llm_client: LLMClient = Depends(get_llm_client),
) -> Dict[str, str]:
    """
    Process a user interaction.
    
    This endpoint receives user input, processes it through the LLM with
    the active persona, and returns the system's response while storing
    the conversation in memory.
    
    Args:
        user_input: The user's input message
        request: The HTTP request object
        memory: Memory manager for conversation history
        llm_client: LLM client for generating responses
        
    Returns:
        A dictionary containing the response text and persona information
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        # Get settings
        settings = get_settings()
        
        # Use default user_id if not provided
        if user_input.user_id is None:
            user_input.user_id = "patrick"  # For backward compatibility
            logger.warning("No user_id provided, using default: 'patrick'")
        
        # Retrieve active persona from request state
        persona_config = request.state.active_persona
        
        # Log the interaction
        logger.info(
            f"Processing interaction with persona: {persona_config.name} for user: {user_input.user_id}"
        )
        
        # Get conversation history
        history_items = await memory.get_conversation_history(user_id=user_input.user_id, limit=10)
        
        # Format history for LLM
        formatted_history = []
        for item in history_items:
            if item.persona_active == persona_config.name:
                formatted_history.append({
                    "role": "assistant",
                    "content": item.text_content
                })
            else:
                formatted_history.append({
                    "role": "user",
                    "content": item.text_content
                })
        
        # Construct system prompt using persona_config
        system_message = {
            "role": "system",
            "content": f"You are {persona_config.name}. {persona_config.description}"
        }
        
        # Add current user message
        user_message = {
            "role": "user",
            "content": user_input.text
        }
        
        # Combine messages
        messages = [system_message] + formatted_history + [user_message]
        
        # Call LLM
        try:
            # Use the primary model if available, otherwise fall back to the legacy model setting
            model_to_use = getattr(settings, "DEFAULT_LLM_MODEL_PRIMARY", settings.DEFAULT_LLM_MODEL)
            
            logger.info(f"Calling LLM with model: {model_to_use}")
            llm_response_text = await llm_client.generate_response(
                model=model_to_use,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                user_id=user_input.user_id,
                active_persona_name=persona_config.name
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate response: {str(e)}"
            )
        
        # Create memory item for the response
        memory_item = MemoryItem(
            user_id=user_input.user_id,
            session_id=str(request.state.session_id) if hasattr(request.state, "session_id") else None,
            item_type="message",
            persona_active=persona_config.name,
            text_content=llm_response_text,
            timestamp=datetime.utcnow(),
            metadata={
                "source": "llm",
                "model": model_to_use,  # Store the actual model used
                "request_id": getattr(request.state, "request_id", None)
            }
        )
        
        # Save to memory
        await memory.add_memory_item(memory_item)
        
        # Return response
        return {
            "response": llm_response_text,
            "persona": persona_config.name
        }
    
    except Exception as e:
        logger.error(f"Interaction processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process interaction: {str(e)}"
        )
