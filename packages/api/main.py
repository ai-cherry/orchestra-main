"""
Main FastAPI application for AI Orchestra project.

This module initializes the FastAPI application and includes all routes.
"""

import logging
import os
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .dependencies import get_vertex_client
from .models import HealthResponse, VertexModel, VertexPredictionRequest, VertexPredictionResponse
from .routes import router as api_router

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Orchestra API",
    description="API for AI Orchestra project using Vertex AI",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api")

@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns basic API information.
    
    Returns:
        Dict[str, str]: Basic API information
    """
    return {
        "name": "AI Orchestra API",
        "version": "0.1.0",
        "status": "active",
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint to verify API is running correctly.
    
    Args:
        settings: Application settings
        
    Returns:
        HealthResponse: Health status information
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.environment,
        gcp_project=settings.project_id,
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.
    
    Args:
        request: The request that caused the exception
        exc: The unhandled exception
        
    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("packages.api.main:app", host="0.0.0.0", port=8080, reload=True)