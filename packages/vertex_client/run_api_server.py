#!/usr/bin/env python3
"""
Run the Vertex AI Agent Manager API server.

This script launches the FastAPI server for the Vertex AI Agent Manager.
"""

import argparse
import logging

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the API server."""
    parser = argparse.ArgumentParser(description="Vertex AI Agent Manager API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logger.info(
        f"Starting Vertex AI Agent Manager API server on {args.host}:{args.port}"
    )

    # Import the API module

    # Run the server
    uvicorn.run(
        "packages.vertex_client.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
