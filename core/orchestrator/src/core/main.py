"""
Main entry point for AI Orchestration System.

This module provides the main FastAPI application and API router setup,
integrating all core components.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.orchestrator.src.core.memory import get_memory_manager
from core.orchestrator.src.core.personas import get_persona_manager
from core.orchestrator.src.core.agents import get_agent_registry
from core.orchestrator.src.core.orchestrator import get_orchestrator, InteractionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# API Models


class InteractionRequest(BaseModel):
    """Request model for interaction API."""

    message: str = Field(..., description="The user's message")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(
        None, description="Session identifier for conversation continuity"
    )
    persona_id: Optional[str] = Field(
        None, description="Persona identifier to use for this interaction"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the interaction"
    )


class InteractionResponse(BaseModel):
    """Response model for interaction API."""

    message: str = Field(..., description="The response message")
    persona_id: str = Field(..., description="The persona identifier used")
    persona_name: str = Field(..., description="The persona name used")
    session_id: str = Field(..., description="The session identifier")
    interaction_id: str = Field(..., description="The interaction identifier")
    timestamp: str = Field(..., description="Timestamp of the interaction")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class PersonaInfo(BaseModel):
    """Persona information model."""

    id: str = Field(..., description="The persona identifier")
    name: str = Field(..., description="The persona name")
    description: str = Field(..., description="The persona description")
    traits: List[str] = Field(default_factory=list, description="The persona traits")


class PersonaListResponse(BaseModel):
    """Response model for persona listing API."""

    personas: Dict[str, PersonaInfo] = Field(
        ..., description="Dictionary of available personas"
    )
    default_persona_id: str = Field(..., description="The default persona identifier")


# App Factory


def create_app() -> FastAPI:
    """
    Create the FastAPI application.

    This function initializes the FastAPI app, sets up middleware,
    and registers the API routes.

    Returns:
        The FastAPI application
    """
    # Initialize core components
    get_memory_manager()  # Initialize memory manager
    persona_manager = get_persona_manager()
    get_agent_registry()  # Initialize agent registry
    orchestrator = get_orchestrator()

    # Create FastAPI app
    app = FastAPI(
        title="AI Orchestration System",
        description="API for AI orchestration with personas and memory",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Define routes

    @app.post("/api/interact", response_model=InteractionResponse)
    async def interact(request: InteractionRequest):
        """
        Process a user interaction and generate a response.

        Args:
            request: The interaction request

        Returns:
            The interaction response
        """
        try:
            result = await orchestrator.process_interaction(
                user_input=request.message,
                user_id=request.user_id,
                session_id=request.session_id,
                persona_id=request.persona_id,
                context=request.context,
            )

            return InteractionResponse(
                message=result.message,
                persona_id=result.persona_id,
                persona_name=result.persona_name,
                session_id=result.session_id,
                interaction_id=result.interaction_id,
                timestamp=result.timestamp.isoformat(),
                metadata=result.metadata,
            )
        except Exception as e:
            logger.error(f"Error processing interaction: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/personas", response_model=PersonaListResponse)
    async def list_personas():
        """
        List available personas.

        Returns:
            Dictionary of available personas
        """
        try:
            personas = persona_manager.get_all_personas()

            result = {}
            for persona_id, persona in personas.items():
                result[persona_id] = PersonaInfo(
                    id=persona_id,
                    name=persona.name,
                    description=persona.description,
                    traits=persona.traits,
                )

            return PersonaListResponse(
                personas=result,
                default_persona_id=persona_manager._loader.default_persona_id,
            )
        except Exception as e:
            logger.error(f"Error listing personas: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/health")
    async def health_check():
        """
        Health check endpoint.

        Returns:
            Health status
        """
        return {
            "status": "ok",
            "components": {"memory": "ok", "personas": "ok", "agents": "ok"},
        }

    return app


# Main entry point

app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
