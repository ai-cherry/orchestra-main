"""
Interaction Endpoints for AI Orchestration System.

This module provides API endpoints for user interactions with the system,
allowing conversations with AI personas while storing conversation history.
This implementation follows the hexagonal architecture pattern by
separating API concerns from business logic.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core.orchestrator.src.api.dependencies.llm import get_llm_client
from core.orchestrator.src.api.dependencies.memory import (
    get_memory_manager,
    get_memory_service,
)
from core.orchestrator.src.services.interaction_service import InteractionService
from core.orchestrator.src.config.settings import get_settings
from packages.shared.src.llm_client.interface import LLMClient
from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.memory.services.memory_service import MemoryService
from packages.shared.src.memory.services.memory_service_factory import (
    MemoryServiceFactory,
)
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Commented out due to Pylance error - verify module path or availability
# from infra.modules.advanced-monitoring.auto_instrumentation import api_endpoint, llm_call

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class UserInput(BaseModel):
    """User input model for interaction endpoint."""

    text: str = Field(..., min_length=1, description="User's message text")
    user_id: Optional[str] = Field(None, description="User identifier")


# Dependency for getting the interaction service
async def get_interaction_service(
    memory: MemoryManager = Depends(get_memory_manager),
    llm_client: LLMClient = Depends(get_llm_client),
) -> InteractionService:
    """
    Get the interaction service for processing user interactions.

    This function serves as a FastAPI dependency that creates an instance of
    the InteractionService using the necessary dependencies.

    Args:
        memory: The memory manager from the dependency injection system
        llm_client: The LLM client from the dependency injection system

    Returns:
        An initialized interaction service
    """
    settings = get_settings()

    # Use the memory service directly from the factory via dependency injection
    memory_service = await get_memory_service()

    # Use the primary model if available, otherwise fall back to the legacy model setting
    model_to_use = getattr(settings, "DEFAULT_LLM_MODEL_PRIMARY", settings.DEFAULT_LLM_MODEL)

    # Create and return the interaction service
    return InteractionService(
        memory_service=memory_service,
        llm_client=llm_client,
        default_model=model_to_use,
    )


@router.post("/interact", response_model=Dict[str, str], tags=["interaction"])
@api_endpoint(name="interact_endpoint", error_threshold_ms=2000, track_request_body=True)
async def interact(
    user_input: UserInput,
    request: Request,
    interaction_service: InteractionService = Depends(get_interaction_service),
) -> Dict[str, str]:
    """
    Process a user interaction.

    This endpoint receives user input, delegates processing to the interaction service,
    and returns the system's response. The business logic is handled by the service,
    keeping the API layer focused on HTTP concerns.

    Args:
        user_input: The user's input message
        request: The HTTP request object
        interaction_service: Service for handling user interactions

    Returns:
        A dictionary containing the response text and persona information

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Use default user_id if not provided
        if user_input.user_id is None:
            user_input.user_id = "patrick"  # For backward compatibility
            logger.warning("No user_id provided, using default: 'patrick'")

        # Retrieve active persona from request state
        persona_config = request.state.active_persona

        # Extract session ID and request ID from request state if available
        session_id = str(request.state.session_id) if hasattr(request.state, "session_id") else None
        request_id = getattr(request.state, "request_id", None)

        # Delegate to the interaction service
        response_text, persona_name = await interaction_service.process_interaction(
            user_id=user_input.user_id,
            user_message=user_input.text,
            persona_config=persona_config,
            session_id=session_id,
            request_id=request_id,
        )

        # Return response
        return {"response": response_text, "persona": persona_name}

    except Exception as e:
        logger.error(
            "Error processing interaction",
            exc_info=True,
            extra={"error_message": str(e), "endpoint_path": "interaction_endpoint_placeholder"},
        )
        logger.warning("Interaction processing failure may impact user experience or conversation continuity.")
        raise HTTPException(status_code=500, detail=f"Failed to process interaction: {str(e)}")
