"""
Simplified main entry point for AI Orchestration System.

This is a recovery mode version that implements the bare minimum endpoints
without complex dependencies.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.

    Returns:
        A dictionary with status message for Patrick
    """
    return {"status": "I'm alive, Patrick!"}


@app.post("/interact")
async def interact(user_input: dict):
    """
    Process a user interaction and generate a response.

    Args:
        user_input: The user's input message

    Returns:
        A simple response message
    """
    try:
        text = user_input.get("text", "")
        logger.info(f"Received user input: {text}")

        # Return a simple response for now
        return {"response": "Orchestrator is listening..."}

    except Exception as e:
        logger.error(f"Interaction failed: {e}")
        # Return a simple error response rather than raising an exception
        return {"response": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    import uvicorn

    # Start server
    uvicorn.run("core.orchestrator.src.main_simple:app", host="0.0.0.0", port=8000, reload=True)
