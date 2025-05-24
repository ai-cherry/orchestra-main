"""
Main entry point for AI Orchestration System.

This module provides the FastAPI application and starts the web server. It also
initializes the unified service components and maintains backward compatibility
with existing components.
"""

# Use the new centralized logging setup
from core.logging_config import setup_logging, get_logger
import os

# Determine if running in production (Cloud Run) or development
is_production = os.environ.get("K_SERVICE") is not None
# Assuming settings.log_level is available, otherwise use a default
# from core.orchestrator.src.config.loader import get_settings # This will be loaded later
setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"), json_format=is_production)

logger = get_logger(__name__)  # Use the centralized get_logger

from core.orchestrator.src.api.middleware.persona_loader import get_active_persona
from core.orchestrator.src.api.dependencies.memory import (
    initialize_memory_manager,
    close_memory_manager,
    # Add the new hexagonal architecture components
    close_memory_service,
)
from core.orchestrator.src.agents.unified_agent_registry import get_agent_registry
from core.orchestrator.src.services.unified_event_bus import (
    get_event_bus,
    EventPriority,
)
from core.orchestrator.src.services.unified_registry import (
    Service,
    get_service_registry,
    register,
)
from packages.shared.src.models.base_models import PersonaConfig
from core.orchestrator.src.config.loader import get_settings, load_persona_configs
from core.orchestrator.src.api.endpoints import (
    health,
    interaction,
    llm_interaction,
    personas,
    agents,
    conversations,  # Add import for conversations endpoints
)
from core.orchestrator.src.agents.agent_registry import register_default_agents
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Check for mode settings from environment variables
use_recovery_mode_env = os.environ.get("USE_RECOVERY_MODE", "false").lower()
standard_mode_env = os.environ.get("STANDARD_MODE", "true").lower()

# OVERRIDE: Always force standard mode regardless of environment variables
use_recovery_mode_env = "false"
standard_mode_env = "true"

# Set mode based on environment variables - these variables can be patched at runtime
RECOVERY_MODE = False  # Hardcoded to False to ensure standard mode
STANDARD_MODE = True  # Hardcoded to True to ensure standard mode

# Log the current mode
print(f"🚀 Orchestra core starting in {'RECOVERY' if RECOVERY_MODE else 'STANDARD'} mode")
print(f"   Environment settings: USE_RECOVERY_MODE={use_recovery_mode_env}, STANDARD_MODE={standard_mode_env}")
print(f"   Active mode settings: RECOVERY_MODE={RECOVERY_MODE}, STANDARD_MODE={STANDARD_MODE}")

# Original components (maintained for backward compatibility)

# Unified components

# Memory management components

# Import memory service for hexagonal architecture
try:
    from packages.shared.src.memory.services.memory_service_factory import (
        MemoryServiceFactory,
    )
    from core.orchestrator.src.api.dependencies.memory import HEX_ARCH_AVAILABLE
except ImportError:
    HEX_ARCH_AVAILABLE = False

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
        logger.error(f"Failed to load persona configurations: {e}", exc_info=True)
        logger.warning("Application may run with incomplete or default persona configurations due to loading failure.")

    # Initialize legacy memory manager for backward compatibility
    try:
        logger.info("Initializing legacy memory manager")
        await initialize_memory_manager(settings)
    except Exception as e:
        logger.error(f"Failed to initialize legacy memory manager: {e}", exc_info=True)
        logger.warning("Legacy memory manager initialization failed; application may experience memory-related issues.")

    # Initialize memory service for hexagonal architecture if available
    if HEX_ARCH_AVAILABLE:
        try:
            logger.info("Initializing memory service with hexagonal architecture")
            # Memory service initialization happens lazily in the dependency
            # but we can log that it's available
            logger.info("Memory service with hexagonal architecture is available")
        except Exception as e:
            logger.error(
                f"Failed to initialize memory service with hexagonal architecture: {e}",
                exc_info=True,
            )
            logger.warning("Hexagonal memory service initialization failed; falling back to legacy if available.")
    else:
        logger.warning("Hexagonal architecture components are not available")

    # Initialize services
    initialize_services(test_mode=getattr(settings, "TEST_MODE", False))

    # Register default agents
    try:
        logger.info("Registering default agents")
        register_default_agents()
        logger.info("Default agents registered successfully")
    except Exception as e:
        logger.error(f"Failed to register default agents: {e}", exc_info=True)
        logger.warning("Default agent registration failed; some functionalities may be unavailable.")

    # Yield control back to FastAPI
    yield

    # Shutdown operations
    logger.info("Application shutting down")

    # Close memory services
    try:
        logger.info("Closing legacy memory manager")
        await close_memory_manager()
    except Exception as e:
        logger.error(f"Error closing legacy memory manager: {e}")

    # Close hexagonal architecture memory service if available
    if HEX_ARCH_AVAILABLE:
        try:
            logger.info("Closing memory service with hexagonal architecture")
            await close_memory_service()
        except Exception as e:
            logger.error(f"Error closing memory service with hexagonal architecture: {e}")

    # Close other services
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
            logger.warning(f"Failed to initialize LLM providers: {e}", exc_info=True)
            logger.error("LLM providers initialization failed; AI functionalities may be limited or unavailable.")

    # Initialize the LLM agent and register it with the unified registry (skip in test mode)
    if not test_mode:
        try:
            from core.orchestrator.src.agents.llm_agent import LLMAgent

            llm_agent = LLMAgent()
            register(llm_agent)
        except Exception as e:
            logger.warning(f"Failed to initialize LLM agent: {e}", exc_info=True)
            logger.error("LLM agent initialization failed; related functionalities will not work.")

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

# Register API routes
# Use settings.API_PREFIX if available
app.include_router(health.router, prefix="/api")
app.include_router(interaction.router, prefix="/api")
app.include_router(llm_interaction.router, prefix="/api")
app.include_router(personas.router, prefix="/api/personas")
app.include_router(agents.router, prefix="/api/agents")
# Add conversations router
app.include_router(conversations.router, prefix="/api/conversations")


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
