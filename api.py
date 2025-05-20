"""
AI Orchestra Agent Orchestration API

This module implements the FastAPI endpoints for interacting with the 
AI Orchestra agent orchestration system.
"""

import logging
import os
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.shared.src.agent_orchestration import AgentOrchestrator
from packages.shared.src.models.base_models import AgentMessage

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Orchestra API",
    description="API for the AI Orchestra agent orchestration system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator instance
orchestrator = None


# Request and response models
class UserMessageRequest(BaseModel):
    """Request model for user messages."""

    message: str
    user_id: str
    session_id: Optional[str] = None


class UserMessageResponse(BaseModel):
    """Response model for user messages."""

    message: str
    session_id: str
    domain: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global orchestrator

    logger.info("Initializing AI Orchestra API...")

    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    success = await orchestrator.initialize()

    if not success:
        logger.error("Failed to initialize orchestrator")
        # Continue startup but with degraded functionality
    else:
        logger.info("Orchestrator initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down AI Orchestra API...")
    # Any cleanup code would go here


# Dependency for getting the orchestrator
async def get_orchestrator():
    """Get the orchestrator instance."""
    if orchestrator is None or not hasattr(orchestrator, "gateway"):
        # Lazily initialize if needed
        global orchestrator
        orchestrator = AgentOrchestrator()
        await orchestrator.initialize()

    return orchestrator


# API endpoints
@app.post("/api/message", response_model=UserMessageResponse)
async def process_message(
    request: UserMessageRequest,
    background_tasks: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
):
    """Process a user message and return a response."""
    try:
        # Process the message
        response = await orchestrator.process_user_message(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
        )

        return UserMessageResponse(**response)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}",
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    if orchestrator is None or not hasattr(orchestrator, "gateway"):
        return {
            "status": "degraded",
            "message": "Orchestrator not initialized",
        }

    return {
        "status": "healthy",
        "version": "1.0.0",
    }


# Run the API server with uvicorn
if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Run the server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
