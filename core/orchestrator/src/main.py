"""
Main entry point for AI Orchestration System.

This module provides the FastAPI application and starts the web server. It also
initializes the unified service components and maintains backward compatibility
with existing components.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Original components (maintained for backward compatibility)
from core.orchestrator.src.agents.agent_registry import register_default_agents
from core.orchestrator.src.api.endpoints import (
    health,
    interaction,
    llm_interaction,
    personas,
    agents,
    conversations,  # Add import for conversations endpoints
)
from core.orchestrator.src.config.loader import get_settings, load_persona_configs
from packages.shared.src.models.base_models import PersonaConfig

# Unified components
from core.orchestrator.src.services.unified_registry import (
    Service,
    get_service_registry,
    register,
)
from core.orchestrator.src.services.unified_event_bus import (
    get_event_bus,
    EventPriority,
)
from core.orchestrator.src.agents.unified_agent_registry import get_agent_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Load configurations at module level
settings = get_settings()
persona_configs: Dict[str, PersonaConfig] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event handler for application startup and shutdown.

    Args:
        app: The FastAPI application instance
    """
    # Load persona configurations
    global persona_configs
    try:
        persona_configs = load_persona_configs()
        logger.info(f"Loaded {len(persona_configs)} persona configurations")
    except Exception as e:
        logger.error(f"Failed to load persona configurations: {e}")

    # Initialize services
    initialize_services(test_mode=getattr(settings, "TEST_MODE", False))

    # Register default agents
    try:
        logger.info("Registering default agents")
        register_default_agents()
        logger.info("Default agents registered successfully")
    except Exception as e:
        logger.error(f"Failed to register default agents: {e}")

    # Yield control back to FastAPI
    yield

    # Shutdown operations
    logger.info("Application shutting down")
    get_service_registry().close_all()


def initialize_services(test_mode: bool = False) -> None:
    """
    Initialize and register unified services.

    This function sets up all the core services using the unified
    components, providing a cleaner architecture with better
    dependency management.

    Args:
        test_mode: If True, skip initialization of external services and use mocks
    """
    # Get the service registry
    registry = get_service_registry()

    # Register the event bus as a service (it's also self-registering)
    event_bus = get_event_bus()
    register(event_bus)

    # Register the agent registry as a service
    agent_registry = get_agent_registry()
    register(agent_registry)

    # Initialize LLM providers (skip in test mode unless explicitly mocked)
    if not test_mode:
        try:
            from core.orchestrator.src.services.llm.providers import (
                initialize_llm_providers,
            )

            initialize_llm_providers()
        except Exception as e:
            logger.warning(f"Failed to initialize LLM providers: {e}")

    # Initialize the LLM agent and register it with the unified registry (skip in test mode)
    if not test_mode:
        try:
            from core.orchestrator.src.agents.llm_agent import LLMAgent

            llm_agent = LLMAgent()
            register(llm_agent)
        except Exception as e:
            logger.warning(f"Failed to initialize LLM agent: {e}")

    # Initialize all registered services
    registry.initialize_all()

    logger.info(f"Unified services initialized {'(test mode)' if test_mode else ''}")


# Create FastAPI app
app = FastAPI(
    title=settings.ENVIRONMENT,
    description="AI Orchestration System with personas and memory",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use settings.CORS_ORIGINS if available
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and use the persona loader middleware
from core.orchestrator.src.api.middleware.persona_loader import get_active_persona

# Register API routes
app.include_router(health.router, prefix="/api")  # Use settings.API_PREFIX if available
app.include_router(interaction.router, prefix="/api")
app.include_router(llm_interaction.router, prefix="/api")
app.include_router(personas.router, prefix="/api/personas")
app.include_router(agents.router, prefix="/api/agents")
app.include_router(conversations.router, prefix="/api/conversations")  # Add conversations router


if __name__ == "__main__":
    import uvicorn
    import asyncio

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Start server
    uvicorn.run(
        "core.orchestrator.src.main:app",
        host="0.0.0.0",
        port=port,
        reload=get_settings().DEBUG,
    )
