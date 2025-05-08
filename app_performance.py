"""
Performance-optimized FastAPI application for the Orchestra project.

This module provides a FastAPI application with performance monitoring
and simplified memory management.
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime
import time
import psutil
import os
import logging
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager

from mcp_server.managers.performance_memory_manager import PerformanceMemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("orchestra-api")

# Performance metrics
request_times = []
request_count = 0
start_time = time.time()

# Create memory manager instance
memory_manager = PerformanceMemoryManager()

# Define Pydantic models for request validation
class MemoryContent(BaseModel):
    """Model for memory content data."""
    content: Dict[str, Any] = Field(..., description="The content to store")
    tool_name: str = Field(default="api", description="The name of the tool")
    ttl_seconds: int = Field(default=3600, description="Time-to-live in seconds")
    
    @validator('ttl_seconds')
    def validate_ttl(cls, v):
        """Validate TTL is positive."""
        if v <= 0:
            raise ValueError("TTL must be positive")
        return v

class SearchParams(BaseModel):
    """Model for search parameters."""
    query: str = Field(..., description="The search query")
    limit: int = Field(default=10, description="Maximum number of results to return")
    
    @validator('limit')
    def validate_limit(cls, v):
        """Validate limit is positive."""
        if v <= 0:
            raise ValueError("Limit must be positive")
        if v > 100:
            return 100  # Cap at 100 to prevent excessive resource usage
        return v

class ErrorResponse(BaseModel):
    """Model for error responses."""
    success: bool = Field(default=False)
    error: str = Field(...)
    details: Optional[Dict[str, Any]] = Field(default=None)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    # Initialize memory manager
    logger.info("Initializing memory manager")
    try:
        success = await memory_manager.initialize()
        if not success:
            logger.error("Failed to initialize memory manager")
    except Exception as e:
        logger.error(f"Error initializing memory manager: {e}")
    
    yield
    
    # Clean up resources
    logger.info("Shutting down")


app = FastAPI(
    title="Orchestra API",
    description="Performance-optimized API for the Orchestra project",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handler for custom error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error=exc.detail,
            details=getattr(exc, "details", None)
        ).dict()
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to track request processing time."""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Store metrics (keep only last 1000 requests)
        global request_times, request_count
        request_times.append(process_time)
        if len(request_times) > 1000:
            request_times.pop(0)
        request_count += 1
        
        return response
    except Exception as e:
        logger.error(f"Unhandled exception in request: {e}")
        process_time = time.time() - start_time
        
        # Still record the time for failed requests
        request_times.append(process_time)
        if len(request_times) > 1000:
            request_times.pop(0)
        request_count += 1
        
        # Return a proper error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Internal server error",
                details={"message": str(e)}
            ).dict()
        )

# Dependency to get memory manager
async def get_memory_manager():
    """Dependency to get the memory manager instance."""
    return memory_manager

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Orchestra API"}

@app.get("/metrics")
async def get_metrics():
    """Get performance metrics."""
    try:
        # Calculate metrics
        avg_request_time = sum(request_times) / len(request_times) if request_times else 0
        max_request_time = max(request_times) if request_times else 0
        min_request_time = min(request_times) if request_times else 0
        
        # System metrics
        memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        cpu_percent = psutil.Process(os.getpid()).cpu_percent(interval=0.1)
        uptime = time.time() - start_time
        
        return {
            "success": True,
            "requests": {
                "total": request_count,
                "average_time": avg_request_time,
                "max_time": max_request_time,
                "min_time": min_request_time,
            },
            "system": {
                "memory_usage_mb": memory_usage,
                "cpu_percent": cpu_percent,
                "uptime_seconds": uptime,
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get metrics"
        )

@app.get("/health")
async def health_check(memory_manager: PerformanceMemoryManager = Depends(get_memory_manager)):
    """Health check endpoint."""
    try:
        memory_health = await memory_manager.health_check()
        return {
            "success": True,
            "status": memory_health.get("status", "unknown"),
            "memory": memory_health,
            "uptime_seconds": time.time() - start_time,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "uptime_seconds": time.time() - start_time,
        }

@app.post("/memory/{key}")
async def store_memory(
    key: str,
    content_data: MemoryContent,
    memory_manager: PerformanceMemoryManager = Depends(get_memory_manager)
):
    """Store content in memory."""
    if not key or len(key) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key"
        )
        
    try:
        success = await memory_manager.store(
            key,
            content_data.content,
            content_data.tool_name,
            content_data.ttl_seconds
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store content"
            )
            
        return {"success": success, "key": key}
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error storing memory: {str(e)}"
        )

@app.get("/memory/{key}")
async def get_memory(
    key: str,
    memory_manager: PerformanceMemoryManager = Depends(get_memory_manager)
):
    """Retrieve content from memory."""
    if not key or len(key) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key"
        )
        
    try:
        content = await memory_manager.retrieve(key)
        if content is None:
            return {"success": True, "found": False, "key": key}
        return {"success": True, "found": True, "key": key, "content": content}
    except Exception as e:
        logger.error(f"Error retrieving memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving memory: {str(e)}"
        )

@app.delete("/memory/{key}")
async def delete_memory(
    key: str,
    memory_manager: PerformanceMemoryManager = Depends(get_memory_manager)
):
    """Delete content from memory."""
    if not key or len(key) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key"
        )
        
    try:
        success = await memory_manager.delete(key)
        return {"success": success, "key": key}
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting memory: {str(e)}"
        )

@app.get("/memory/search")
async def search_memory(
    params: SearchParams = Depends(),
    memory_manager: PerformanceMemoryManager = Depends(get_memory_manager)
):
    """Search memory content."""
    try:
        results = await memory_manager.search(params.query, params.limit)
        return {
            "success": True,
            "query": params.query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching memory: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)