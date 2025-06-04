"""
Enhanced AI Cherry main application with performance and stability optimizations
"""

import os
import time
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import routers (assuming they exist)
try:
    from agent.app.routers import (
        admin_router, agents_router, workflows_router, resources_router,
        system_router, audit_router, automation_router, natural_language_router,
        intent_router, suggestions_router, llm_router, personas_admin_router,
        llm_admin_router, llm_coordination_router
    )
    ROUTERS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some routers not available: {e}")
    ROUTERS_AVAILABLE = False

# Import optimized MCP admin router
from agent.app.routers import mcp_admin

# Import performance and stability utilities
from core.utils.performance import performance_monitor_instance, default_cache
from core.utils.stability import health_checker, error_collector, StabilityError
from core.utils.optimization import resource_monitor, memory_optimizer, optimize_system_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with resource monitoring"""
    logger.info("Starting AI Cherry application with enhanced performance monitoring")
    
    # Start resource monitoring
    await resource_monitor.start_monitoring()
    
    # Register health checks
    health_checker.register_check("memory", check_memory_health)
    health_checker.register_check("cache", check_cache_health)
    health_checker.register_check("mcp_config", check_mcp_config_health)
    
    # Initial system optimization
    await optimize_system_resources()
    
    logger.info("Application startup completed")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down AI Cherry application")
    await resource_monitor.stop_monitoring()
    
    # Final optimization
    memory_optimizer.optimize_memory()
    
    logger.info("Application shutdown completed")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="AI Cherry API",
    version="1.1.0",
    description="Enhanced AI orchestration platform with performance optimizations",
    lifespan=lifespan
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with error handling
if ROUTERS_AVAILABLE:
    try:
        app.include_router(admin_router)
        app.include_router(agents_router)
        app.include_router(workflows_router)
        app.include_router(resources_router)
        app.include_router(system_router)
        app.include_router(audit_router)
        app.include_router(automation_router)
        app.include_router(natural_language_router)
        app.include_router(intent_router)
        app.include_router(suggestions_router)
        app.include_router(llm_router)
        app.include_router(personas_admin_router)
        app.include_router(llm_admin_router)
        app.include_router(llm_coordination_router)
    except Exception as e:
        logger.warning(f"Error including some routers: {e}")

# Always include the optimized MCP admin router
app.include_router(mcp_admin.router)


# Enhanced middleware for performance monitoring and error handling
@app.middleware("http")
async def enhanced_request_middleware(request: Request, call_next):
    """Enhanced middleware with performance monitoring and error handling"""
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"
    
    # Log request start
    logger.info(
        "request_started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = (time.time() - start_time) * 1000
        
        # Log successful request
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": f"{process_time:.2f}"
            }
        )
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Calculate error processing time
        process_time = (time.time() - start_time) * 1000
        
        # Record error
        error_collector.record_error(
            e,
            context={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": request.client.host if request.client else "unknown"
            },
            operation="http_request"
        )
        
        # Log error
        logger.error(
            "request_failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "latency_ms": f"{process_time:.2f}"
            },
            exc_info=True
        )
        
        # Return appropriate error response
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "type": "unexpected_error"
                }
            )


# Enhanced error handlers
@app.exception_handler(StabilityError)
async def stability_error_handler(request: Request, exc: StabilityError):
    """Handle stability-related errors"""
    return JSONResponse(
        status_code=503,
        content={
            "error": "Service temporarily unavailable",
            "detail": str(exc),
            "error_type": exc.error_type,
            "timestamp": exc.timestamp.isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    error_collector.record_error(
        exc,
        context={"path": str(request.url.path), "method": request.method},
        operation="exception_handler"
    )
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "type": "unhandled_exception"
        }
    )


# Request/Response models
class QueryRequest(BaseModel):
    prompt: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    resource_usage: dict
    cache_stats: dict


# Enhanced endpoints
@app.get("/health", response_model=HealthResponse)
@performance_monitor_instance.record
async def enhanced_health_check():
    """Enhanced health check with system metrics"""
    try:
        # Get current resource metrics
        current_metrics = resource_monitor.get_current_metrics()
        
        # Get cache statistics
        cache_stats = default_cache.stats()
        
        # Calculate uptime (approximate)
        uptime = time.time() - getattr(app.state, 'start_time', time.time())
        
        return HealthResponse(
            status="healthy",
            timestamp=current_metrics.timestamp.isoformat(),
            version="1.1.0",
            uptime_seconds=uptime,
            resource_usage={
                "cpu_percent": current_metrics.cpu_percent,
                "memory_mb": current_metrics.memory_mb,
                "memory_percent": current_metrics.memory_percent,
                "open_files": current_metrics.open_files
            },
            cache_stats=cache_stats
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Health check failed"
        )


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all system components"""
    try:
        health_results = await health_checker.run_all_checks()
        return health_results
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Detailed health check failed"
        )


@app.post("/query")
@performance_monitor_instance.record
async def process_query(query_request: QueryRequest):
    """Process a query prompt with enhanced error handling"""
    logger.info("query_endpoint_called", extra={"prompt_length": len(query_request.prompt)})

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("openai_api_key_not_found")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Configuration error",
                "detail": "OPENAI_API_KEY not configured",
                "type": "missing_api_key"
            }
        )

    # TODO: Implement actual OpenAI ChatCompletion call
    # For now, return enhanced mock response
    logger.info("openai_call_mocked")
    return {
        "response": f"Enhanced mock response to prompt: '{query_request.prompt[:100]}...' using API key ending with ...{api_key[-4:] if api_key else 'N/A'}",
        "metadata": {
            "processing_time_ms": 50,
            "model": "mock-gpt-3.5-turbo",
            "tokens_used": len(query_request.prompt.split())
        }
    }


# Performance and monitoring endpoints
@app.get("/admin/performance")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        resource_summary = resource_monitor.get_metrics_summary(hours=1)
        cache_stats = default_cache.stats()
        error_summary = error_collector.get_error_summary(hours=24)
        
        return {
            "resource_usage": resource_summary,
            "cache_performance": cache_stats,
            "error_analysis": error_summary,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@app.post("/admin/optimize")
async def trigger_optimization(background_tasks: BackgroundTasks):
    """Trigger system optimization"""
    try:
        background_tasks.add_task(optimize_system_resources)
        return {"message": "System optimization triggered"}
    except Exception as e:
        logger.error(f"Error triggering optimization: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger optimization")


@app.post("/admin/cache/clear")
async def clear_system_cache():
    """Clear system caches"""
    try:
        default_cache.clear()
        return {"message": "System cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# Health check functions for the health checker
async def check_memory_health():
    """Check memory health"""
    metrics = resource_monitor.get_current_metrics()
    if metrics.memory_percent > 90:
        raise Exception(f"High memory usage: {metrics.memory_percent:.1f}%")
    return {"memory_percent": metrics.memory_percent, "memory_mb": metrics.memory_mb}


async def check_cache_health():
    """Check cache health"""
    stats = default_cache.stats()
    return {"cache_entries": stats.get("total_entries", 0)}


async def check_mcp_config_health():
    """Check MCP configuration health"""
    try:
        from core.services.mcp_config_manager import OptimizedMCPConfigManager
        config_manager = OptimizedMCPConfigManager()
        configs = await config_manager.get_all_configs()
        return {"config_count": len(configs)}
    except Exception as e:
        raise Exception(f"MCP config check failed: {e}")


# Store start time for uptime calculation
@app.on_event("startup")
async def store_start_time():
    app.state.start_time = time.time()


if __name__ == "__main__":
    # Enhanced development server configuration
    logger.info("Starting AI Cherry development server with optimizations")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True,
        reload=False,  # Disable reload for better performance
        workers=1      # Single worker for development
    )

