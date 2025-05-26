"""
Main FastAPI application.
"""

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.routers import agents, gemini, memory, system

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Redis client with performance-optimized settings
redis_client = (
    Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,  # Reduced timeout for faster connections
        socket_timeout=2,  # Reduced socket timeout
        retry_on_timeout=True,
        health_check_interval=15,  # More frequent health checks
        max_connections=20,  # Increased connection pool size
        auto_close_connection_pool=False,  # Keep pool alive for better performance
    )
    if hasattr(settings, "REDIS_URL") and settings.REDIS_URL
    else None
)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor and log request performance.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log performance metrics."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log request performance
        logger.info(
            f"Request {request.method} {request.url.path} completed in {process_time:.4f}s "
            f"with status {response.status_code}"
        )

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        return response


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    app = FastAPI(
        title="AI Orchestra Admin API",
        description="Backend API for the AI Orchestra Admin Interface",
        version="0.1.0",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add performance monitoring middleware
    app.add_middleware(PerformanceMonitoringMiddleware)

    # Include routers
    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])
    app.include_router(gemini.router, prefix="/api/v1", tags=["Gemini"])

    @app.get("/", tags=["Health"])
    async def health_check():
        """API health check endpoint."""
        return {"status": "ok", "message": "AI Orchestra Admin API is running"}

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        """
        Handle all unhandled exceptions with performance-optimized approach.

        Returns the actual exception details for faster debugging and troubleshooting.
        This improves development velocity and reduces time spent diagnosing issues.
        """
        # Log the exception with minimal overhead - skip full stack trace
        logger.error(f"Unhandled exception: {str(exc)}")

        # Return the actual error details for faster debugging
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": exc.__class__.__name__,
                "path": request.url.path,
            },
        )

    return app


app = create_application()
