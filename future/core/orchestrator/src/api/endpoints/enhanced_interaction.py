"""
DEPRECATED: This file is deprecated and will be removed in a future release.

This legacy file has been replaced by a newer implementation with improved architecture 
and error handling. Please consult the project documentation for the recommended 
replacement module.

Example migration:
from enhanced_interaction import * # Old
# Change to:
# Import the appropriate replacement module
"""

"""
Enhanced Interaction Endpoints for AI Orchestration System.

This module provides enhanced API endpoints for user interactions,
leveraging the template-based persona system for more personalized responses.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator

from core.orchestrator.src.config.config import get_settings
from core.orchestrator.src.personas.enhanced_persona_manager import get_enhanced_persona_manager
from core.orchestrator.src.services.enhanced_agent_orchestrator import get_enhanced_agent_orchestrator

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class EnhancedInteractionRequest(BaseModel):
    """
    Enhanced interaction request model with template-based persona support.
    
    This model defines the structure for interaction requests
    and includes validation for the request parameters.
    """
    
    message: str = Field(..., min_length=1, max_length=4000, description="User's message")
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")
    persona_id: Optional[str] = Field(None, description="Persona identifier to use for this interaction")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the interaction")
    
    @validator("message")
    def message_not_empty(cls, v):
        """Validate that the message is not empty."""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v


class EnhancedInteractionResponse(BaseModel):
    """
    Enhanced interaction response model with template information.
    
    This model defines the structure for interaction responses
    and includes template information for enhanced personas.
    """
    
    message: str = Field(..., description="Response message")
    persona_id: str = Field(..., description="Persona identifier used")
    persona_name: str = Field(..., description="Name of the persona used")
    session_id: str = Field(..., description="Session identifier")
    interaction_id: str = Field(..., description="Unique identifier for this interaction")
    timestamp: datetime = Field(..., description="Timestamp of the response")
    conversation_context: Dict[str, Any] = Field({}, description="Additional context about the conversation")
    template_used: Optional[str] = Field(None, description="Template format used for the response")


@router.post("/interact", response_model=EnhancedInteractionResponse, tags=["interaction"])
async def enhanced_interact(
    request: Request,
    interaction: EnhancedInteractionRequest = Body(...),
    settings = Depends(get_settings)
):
    """
    Process a user interaction with enhanced persona capabilities.
    
    This endpoint receives user input and persona preferences,
    processes it through the enhanced agent orchestrator with template-based
    persona formatting, and returns the system's response.
    
    Args:
        request: The HTTP request
        interaction: The interaction request data
        settings: Application settings
        
    Returns:
        The system's response
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        # Extract request data
        user_input = interaction.message
        user_id = interaction.user_id
        session_id = interaction.session_id
        persona_id = interaction.persona_id
        context = interaction.context or {}
        
        # Add request information to context
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            context["request_id"] = request_id
        
        # Log interaction
        logger.info(
            f"Processing enhanced interaction: user_id={user_id}, "
            f"persona_id={persona_id or 'default'}, session_id={session_id or 'new'}"
        )
        
        # Get enhanced orchestrator
        orchestrator = get_enhanced_agent_orchestrator()
        
        # Process interaction
        result = await orchestrator.process_interaction(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            persona_id=persona_id,
            context=context
        )
        
        # Get enhanced persona manager to retrieve template information
        persona_manager = get_enhanced_persona_manager()
        enhanced_persona = persona_manager.get_enhanced_persona(persona_id)
        
        # Add template information to result
        result["template_used"] = enhanced_persona.prompt_template
        
        return result
    except Exception as e:
        logger.error(f"Enhanced interaction processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process interaction: {str(e)}"
        )


@router.get("/personas", response_model=Dict[str, Dict[str, Any]], tags=["personas"])
async def list_enhanced_personas():
    """
    List all available enhanced personas.
    
    This endpoint returns information about all available personas,
    including their templates and traits.
    
    Returns:
        Dictionary mapping persona IDs to their configuration
    """
    try:
        # Get enhanced persona manager
        persona_manager = get_enhanced_persona_manager()
        
        # Get all enhanced personas
        personas = persona_manager.get_all_enhanced_personas()
        
        # Convert to dictionary format
        persona_dict = {}
        for persona_id, persona in personas.items():
            persona_dict[persona_id] = {
                "name": persona.name,
                "description": persona.description,
                "prompt_template": persona.prompt_template,
                "interaction_style": persona.interaction_style,
                "traits": persona.traits,
                "preferred_agent_type": persona.preferred_agent_type
            }
        
        return persona_dict
    except Exception as e:
        logger.error(f"Failed to list enhanced personas: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list personas: {str(e)}"
        )
