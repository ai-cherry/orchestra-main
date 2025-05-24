"""
Main entry point for the AI Orchestra Admin API.
"""

import logging

import uvicorn

from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    """
    Run the application locally for development.
    """
    uvicorn.run(
        "app.application:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
