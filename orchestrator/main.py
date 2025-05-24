"""
Main entry point for AI Orchestration System.

This module provides the FastAPI application and starts the web server.
It uses standard Python import paths for better maintainability.
"""

import logging
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Read mode from environment variables
use_recovery_mode_env = os.environ.get("USE_RECOVERY_MODE", "false").lower()
standard_mode_env = os.environ.get("STANDARD_MODE", "true").lower()

# Set mode based on environment variables
RECOVERY_MODE = use_recovery_mode_env == "true"
STANDARD_MODE = standard_mode_env == "true"

# Log the selected mode
print(f"🔧 Starting Orchestra in {'RECOVERY' if RECOVERY_MODE else 'STANDARD'} mode")
print(f"   Environment settings: USE_RECOVERY_MODE={use_recovery_mode_env}, STANDARD_MODE={standard_mode_env}")

# Debug: Print all environment variables to help diagnose issues
print("===== DEBUG: Environment Variables at Startup =====")
for key, value in sorted(os.environ.items()):
    if key in ["PYTHONPATH", "USE_RECOVERY_MODE", "STANDARD_MODE", "ENVIRONMENT"]:
        print(f"{key}={value}")
print("===== DEBUG: Python Path =====")
for path in sys.path:
    print(path)
print("===== DEBUG: End Environment Info =====")

# Import GCP configuration and memory manager
from config.gcp_config import get_gcp_config, get_memory_manager_config
from packages.shared.src.memory.memory_manager import MemoryManagerFactory

# Log the mode we're starting in
logger.info(f"Starting with RECOVERY_MODE={RECOVERY_MODE}, STANDARD_MODE={STANDARD_MODE}")
print(f"Starting with RECOVERY_MODE={RECOVERY_MODE}, STANDARD_MODE={STANDARD_MODE}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Orchestration System",
    description="AI Orchestration System with personas and memory",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory manager instance
memory_manager = None

# Initialize system components

# Short-term memory store (in-memory)
SHORT_TERM_MEMORY_SIZE = 5  # Maximum number of recent messages to store
short_term_memory = []


@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    logger.info("Initializing system components...")

    # Initialize GCP configuration
    gcp_config = get_gcp_config()
    environment = os.environ.get("ENVIRONMENT", "development")
    logger.info(f"Starting in {environment} environment")

    # Initialize memory manager
    global memory_manager
    try:
        memory_config = get_memory_manager_config()
        memory_manager = MemoryManagerFactory.create(**memory_config)
        logger.info(f"Memory manager initialized: {memory_config['memory_type']}")
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {e}")
        if environment in ["production", "staging"]:
            # In production environments, fail if memory manager can't be initialized
            raise
        else:
            # In development, fall back to in-memory storage
            logger.warning("Falling back to in-memory storage")
            memory_manager = MemoryManagerFactory.create("in-memory")

    # Register default agents
    from core.orchestrator.src.agents.agent_registry import register_default_agents

    register_default_agents()

    logger.info("System initialization complete")
    logger.info(f"Starting API in {'STANDARD' if STANDARD_MODE else 'RECOVERY'} MODE in {environment} environment")


# Shutdown cleanup


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down system components...")


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    environment = os.environ.get("ENVIRONMENT", "development")
    return {
        "status": "Service is healthy",
        "mode": "standard" if STANDARD_MODE else "recovery",
        "environment": environment,
        "recovery_mode": RECOVERY_MODE,
    }


@app.post("/interact")
async def interact(user_input: dict):
    """
    Process a user interaction and generate a response.

    Args:
        user_input: The user's input message

    Returns:
        A response message
    """
    try:
        text = user_input.get("text", "")
        logger.info(f"Received user input: {text}")

        # Use agent registry to process input
        from core.orchestrator.src.agents.agent_registry import get_all_agents

        agents = get_all_agents()
        if not agents:
            return {"response": "No agents are currently available. Please try again later."}

        agent = agents[0]  # Use the first registered agent
        response = await agent.process(text)

        # Store interaction in memory if memory manager is available
        if memory_manager:
            from packages.shared.src.models.base_models import MemoryItem

            try:
                memory_item = MemoryItem(
                    content=text,
                    response=response,
                    metadata={"source": "user_interaction"},
                )
                await memory_manager.store(memory_item)
            except Exception as e:
                logger.error(f"Failed to store memory: {e}")

        # Store interaction in short-term memory
        try:
            memory_item = MemoryItem(content=text, response=response, metadata={"source": "user_interaction"})
            short_term_memory.insert(0, memory_item)  # Add to the beginning
            if len(short_term_memory) > SHORT_TERM_MEMORY_SIZE:
                short_term_memory.pop()  # Remove the oldest item
        except Exception as e:
            logger.error(f"Failed to store short-term memory: {e}")

        return {"response": response}

    except Exception as e:
        logger.error(f"Interaction failed: {e}")
        return {"response": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))

    # Start server
    uvicorn.run("core.orchestrator.src.main:app", host="0.0.0.0", port=port, reload=True)
