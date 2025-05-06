"""
FastAPI application for AI Orchestration System.

This module provides the FastAPI application instance with registered routes
and middleware for the AI Orchestration System. It serves as a simplified
entrypoint for running the API directly from the api module.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import endpoints
from .endpoints import interaction
from .endpoints import health
from .endpoints import phidata_chat
from core.orchestrator.src.config.settings import get_settings
from core.orchestrator.src.config.loader import load_persona_configs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for application startup and shutdown.

    Args:
        app: The FastAPI application instance
    """
    # Load persona configurations
    try:
        personas = load_persona_configs()
        logger.info(f"Loaded {len(personas)} persona configurations")
    except Exception as e:
        logger.error(f"Failed to load persona configurations: {e}")
        
    # Initialize memory system
    from core.orchestrator.src.api.dependencies.memory import initialize_memory_manager
    try:
        await initialize_memory_manager()
        logger.info("Memory manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {e}")
    
    # Initialize Redis cache if available
    from core.orchestrator.src.api.dependencies.cache import initialize_redis_cache
    try:
        await initialize_redis_cache()
        logger.info("Redis cache initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis cache: {e}")

    # Log environment information
    logger.info(f"Running in environment: {settings.ENVIRONMENT}")
    if settings.get_gcp_project_id():
        logger.info(f"Connected to GCP project: {settings.get_gcp_project_id()}")
    
    logger.info("Application startup complete")
    
    # Yield control back to FastAPI
    yield

    # Shutdown operations
    logger.info("Application shutting down")
    
    # Close Redis cache
    from core.orchestrator.src.api.dependencies.cache import close_redis_cache
    try:
        await close_redis_cache()
        logger.info("Redis cache closed")
    except Exception as e:
        logger.error(f"Failed to close Redis cache: {e}")
    
    # Close memory system
    from core.orchestrator.src.api.dependencies.memory import close_memory_manager
    try:
        await close_memory_manager()
        logger.info("Memory manager closed")
    except Exception as e:
        logger.error(f"Failed to close memory manager: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Orchestration API",
    description="API for interacting with AI personas with memory",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - use settings.CORS_ORIGINS in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and use the persona middleware
from .middleware.persona_middleware import PersonaMiddleware

# Add persona middleware
app.add_middleware(PersonaMiddleware)

# Register API routes
app.include_router(health.router, prefix="/api")
app.include_router(interaction.router, prefix="/api")
app.include_router(phidata_chat.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start server
    uvicorn.run(
        "core.orchestrator.src.api.app:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
    )
