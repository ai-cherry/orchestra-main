"""
"""
is_production = os.environ.get("K_SERVICE") is not None
# Assuming settings.log_level is available, otherwise use a default
# from core.conductor.src.config.loader import get_settings # This will be loaded later
setup_logging(level=os.environ.get("LOG_LEVEL", "INFO"), json_format=is_production)

logger = get_logger(__name__)  # Use the centralized get_logger

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.conductor.src.agents.simplified_agent_registry import register_default_agents, get_simplified_agent_registry
from core.conductor.src.api.dependencies.memory import (  # Add the new hexagonal architecture components
    close_memory_manager,
    close_memory_service,
    initialize_memory_manager,
)
from core.conductor.src.api.endpoints import health, auth

# Commented out heavy endpoints to minimize dependencies during initial startup
# from core.conductor.src.api.endpoints import interaction, llm_interaction, personas, agents, query_agent

from core.conductor.src.config.loader import get_settings, load_persona_configs
from core.conductor.src.services.unified_event_bus import get_event_bus
from core.conductor.src.services.unified_registry import get_service_registry, register
from packages.shared.src.models.base_models import PersonaConfig

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
print(f"🚀 cherry_ai core starting in {'RECOVERY' if RECOVERY_MODE else 'STANDARD'} mode")
print(f"   Environment settings: USE_RECOVERY_MODE={use_recovery_mode_env}, STANDARD_MODE={standard_mode_env}")
print(f"   Active mode settings: RECOVERY_MODE={RECOVERY_MODE}, STANDARD_MODE={STANDARD_MODE}")

# Original components (maintained for backward compatibility)

# Unified components

# Memory management components

# Import memory service for hexagonal architecture
try:

    pass
    from core.conductor.src.api.dependencies.memory import HEX_ARCH_AVAILABLE
except Exception:

    pass
    HEX_ARCH_AVAILABLE = False

# Load configurations at module level
settings = get_settings()
persona_configs: Dict[str, PersonaConfig] = {}

try:


    pass
    from core.conductor.src.api.endpoints import conversations
    _HAS_CONVERSATIONS = True
except Exception:

    pass
    logger.warning("conversations endpoint not available; skipping conversations routes")
    _HAS_CONVERSATIONS = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    """
        logger.info(f"Loaded {len(persona_configs)} persona configurations")
    except Exception:

        pass
        logger.error(f"Failed to load persona configurations: {e}", exc_info=True)
        logger.warning("Application may run with incomplete or default persona configurations due to loading failure.")


    # Initialize memory service for hexagonal architecture if available
    if HEX_ARCH_AVAILABLE:
        try:

            pass
            logger.info("Initializing memory service with hexagonal architecture")
            # Memory service initialization happens lazily in the dependency
            # but we can log that it's available
            logger.info("Memory service with hexagonal architecture is available")
        except Exception:

            pass
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

        pass
        logger.info("Registering default agents")
        register_default_agents()
        logger.info("Default agents registered successfully")
    except Exception:

        pass
        logger.error(f"Failed to register default agents: {e}", exc_info=True)
        logger.warning("Default agent registration failed; some functionalities may be unavailable.")

    # Yield control back to FastAPI
    yield

    # Shutdown operations
    logger.info("Application shutting down")

    # Close memory services
    try:

        pass
        # Close hexagonal architecture memory service if available
        if HEX_ARCH_AVAILABLE:
            try:

                pass
                logger.info("Closing memory service with hexagonal architecture")
                await close_memory_service()
            except Exception:

                pass
                logger.error(f"Error closing memory service with hexagonal architecture: {e}")
    except Exception:

        pass
        logger.error(f"Error during memory service cleanup: {e}")

    # Close other services
    get_service_registry().close_all()

def initialize_services(test_mode: bool = False) -> None:
    """
    """
            logger.warning(f"Failed to initialize LLM providers: {e}", exc_info=True)
            logger.error("LLM providers initialization failed; AI functionalities may be limited or unavailable.")

    # Initialize the LLM agent and register it with the unified registry (skip in test mode)
    if not test_mode:
        try:

            pass
            from core.conductor.src.agents.llm_agent import LLMAgent

            llm_agent = LLMAgent()
            register(llm_agent)
        except Exception:

            pass
            logger.warning(f"Failed to initialize LLM agent: {e}", exc_info=True)
            logger.error("LLM agent initialization failed; related functionalities will not work.")

    # Initialize all registered services
    registry.initialize_all()

    logger.info(f"Unified services initialized {'(test mode)' if test_mode else ''}")

# Create FastAPI app
app = FastAPI(
    title=settings.ENVIRONMENT,
    description="AI coordination System with personas and memory",
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
app.include_router(auth.router, prefix="/api")
# Query agent endpoint
# app.include_router(agents.router, prefix="/api/agents")
# Add conversations router
if _HAS_CONVERSATIONS:
    # app.include_router(conversations.router, prefix="/api/conversations")
    pass

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Start server
    uvicorn.run(
        "core.conductor.src.main:app",
        host="0.0.0.0",
        port=port,
        reload=get_settings().DEBUG,
    )
