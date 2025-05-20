"""
AI Orchestra API - Main Application Entry Point
"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from typing import Callable, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai-orchestra")

# Create FastAPI application
app = FastAPI(
    title="AI Orchestra API",
    description="API for orchestrating AI models and workflows",
    version="0.1.0",
)

# Add GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable
) -> JSONResponse:
    """Middleware to track request processing time."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "AI Orchestra API",
        "version": "0.1.0",
        "description": "API for orchestrating AI models and workflows",
    }


# Include routers from other modules
# from .routers import models, agents, workflows
# app.include_router(models.router, prefix="/models", tags=["models"])
# app.include_router(agents.router, prefix="/agents", tags=["agents"])
# app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])


# Add graceful shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    """Handle graceful shutdown."""
    logger.info("Application shutdown initiated")
    # Add cleanup code here (e.g., close DB connections)
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
