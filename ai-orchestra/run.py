#!/usr/bin/env python3
"""
Entry point for the AI Orchestra application.

This script runs the FastAPI application using uvicorn.
"""

import argparse
import logging
import sys
from typing import Dict, Any

import uvicorn

from ai_orchestra.core.config import settings
from ai_orchestra.utils.logging import configure_logging, log_event

# Configure logging
configure_logging(level=settings.log_level, json_logs=True)
logger = logging.getLogger("ai_orchestra.run")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run the AI Orchestra API")
    
    parser.add_argument(
        "--host",
        type=str,
        default=settings.api.host,
        help=f"Host to bind to (default: {settings.api.host})",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.api.port,
        help=f"Port to bind to (default: {settings.api.port})",
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Logging level (default: {settings.log_level})",
    )
    
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Output logs in JSON format",
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    args = parse_args()
    
    # Configure logging with command line arguments
    configure_logging(level=args.log_level, json_logs=args.json_logs)
    
    # Log startup
    log_event(logger, "application", "starting", {
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
    })
    
    # Run the application
    try:
        uvicorn.run(
            "ai_orchestra.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level.lower(),
        )
        return 0
    except Exception as e:
        log_event(logger, "application", "error", {
            "error_type": type(e).__name__,
            "error_message": str(e),
        })
        return 1


if __name__ == "__main__":
    sys.exit(main())