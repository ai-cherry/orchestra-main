"""
Main FastAPI application for Cherry AI with single-user authentication
Clean, performant, and optimized for solo developer deployment
"""

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from contextlib import asynccontextmanager

from mcp_server.security.auth_middleware import (
    AuthenticationMiddleware,
    get_security_context,
    require_permission,
    require_context
)
from mcp_server.security.single_user_context import (
    OperationalContext,
    ContextPermission,
    SecurityContext
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.getenv("cherry_ai_CONTEXT") != "development" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting Cherry AI in {os.getenv('cherry_ai_CONTEXT', 'development')} context")
    
    # Initialize resources
    from mcp_server.storage.async_memory_store import AsyncMemoryStore
    app.state.memory_store = AsyncMemoryStore()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cherry AI")
    if hasattr(app.state, 'memory_store'):
        await app.state.memory_store.close()

# Create FastAPI app
app = FastAPI(
    title="Cherry AI",
    description="AI coordination System - Single User Deployment",
    version="1.0.0",
    lifespan=lifespan
)

# Add authentication middleware
app.add_middleware(AuthenticationMiddleware)

# Add CORS middleware for development
if os.getenv("cherry_ai_CONTEXT", "development") == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cherry_ai-ai",
        "context": os.getenv("cherry_ai_CONTEXT", "development")
    }

# API info endpoint
@app.get("/api/v1/info")
async def api_info(context: SecurityContext = Depends(get_security_context)):
    """Get API information"""
    return {
        "version": "1.0.0",
        "context": context.context,
        "permissions": list(context.permissions),
        "request_count": context.request_count
    }

# Workflow endpoints
@app.post("/api/v1/workflows")
async def create_workflow(
    request: Request,
    context: SecurityContext = Depends(require_permission(ContextPermission.EXECUTE_WORKFLOWS))
):
    """Create a new workflow"""
    data = await request.json()
    
    # In development mode, add debug info
    if context.context == OperationalContext.DEVELOPMENT:
        data["_debug"] = {
            "context": context.context,
            "auth_time_ms": getattr(request.state, "auth_time", 0) * 1000
        }
    
    # Store workflow
    workflow_id = f"wf_{context.request_count}_{hash(str(data))}"
    memory_store = request.app.state.memory_store
    await memory_store.store(workflow_id, data)
    
    return {
        "workflow_id": workflow_id,
        "status": "created",
        "context": context.context
    }

@app.get("/api/v1/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    request: Request,
    context: SecurityContext = Depends(require_permission(ContextPermission.READ_DATA))
):
    """Get workflow details"""
    memory_store = request.app.state.memory_store
    workflow = await memory_store.retrieve(workflow_id)
    
    if not workflow:
        return JSONResponse(
            status_code=404,
            content={"error": "Workflow not found"}
        )
    
    return workflow

# Agent management endpoints
@app.post("/api/v1/agents")
async def create_agent(
    request: Request,
    context: SecurityContext = Depends(require_permission(ContextPermission.MODIFY_AGENTS))
):
    """Create a new agent"""
    data = await request.json()
    
    # Validate agent configuration
    required_fields = ["name", "type", "capabilities"]
    for field in required_fields:
        if field not in data:
            return JSONResponse(
                status_code=400,
                content={"error": f"Missing required field: {field}"}
            )
    
    # Store agent configuration
    agent_id = f"agent_{data['name']}_{hash(str(data))}"
    memory_store = request.app.state.memory_store
    await memory_store.store(f"agents/{agent_id}", data)
    
    return {
        "agent_id": agent_id,
        "name": data["name"],
        "type": data["type"],
        "status": "created"
    }

# System configuration (maintenance mode only)
@app.put("/api/v1/system/config")
async def update_system_config(
    request: Request,
    context: SecurityContext = Depends(require_context(
        OperationalContext.MAINTENANCE,
        OperationalContext.DEVELOPMENT
    ))
):
    """Update system configuration"""
    config = await request.json()
    
    # Store configuration
    memory_store = request.app.state.memory_store
    await memory_store.store("system/config", config)
    
    return {
        "status": "updated",
        "context": context.context,
        "message": "System configuration updated"
    }

# Metrics endpoint
@app.get("/api/v1/metrics")
async def get_metrics(
    context: SecurityContext = Depends(require_permission(ContextPermission.MONITOR_METRICS))
):
    """Get system metrics"""
    return {
        "context": context.context,
        "metrics": {
            "requests_total": context.request_count,
            "last_request": context.last_used.isoformat(),
            "uptime_seconds": (context.last_used - context.created_at).total_seconds()
        }
    }

# Debug endpoint (development only)
@app.get("/api/v1/debug")
async def debug_info(
    request: Request,
    context: SecurityContext = Depends(require_context(OperationalContext.DEVELOPMENT))
):
    """Debug information (development mode only)"""
    return {
        "context": context.context,
        "permissions": list(context.permissions),
        "environment": {
            "cherry_ai_context": os.getenv("cherry_ai_CONTEXT"),
            "api_key_set": bool(os.getenv("cherry_ai_API_KEY")),
            "debug_mode": logging.getLogger().level == logging.DEBUG
        },
        "request_info": {
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers),
            "auth_time_ms": getattr(request.state, "auth_time", 0) * 1000
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "path": request.url.path,
            "message": "The requested resource was not found"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal error: {exc}")
    
    # In development, include error details
    content = {"error": "Internal server error"}
    if os.getenv("cherry_ai_CONTEXT") == "development":
        content["details"] = str(exc)
    
    return JSONResponse(
        status_code=500,
        content=content
    )

if __name__ == "__main__":
    import uvicorn
    
    # Determine port and host based on context
    context = os.getenv("cherry_ai_CONTEXT", "development")
    
    config = {
        "development": {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": True,
            "log_level": "debug"
        },
        "production": {
            "host": "0.0.0.0",
            "port": 8000,
            "reload": False,
            "log_level": "info",
            "workers": 4
        },
        "testing": {
            "host": "127.0.0.1",
            "port": 8001,
            "reload": False,
            "log_level": "warning"
        }
    }
    
    run_config = config.get(context, config["development"])
    
    uvicorn.run(
        "mcp_server.api.main:app",
        **run_config
    )