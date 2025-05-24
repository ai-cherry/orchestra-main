#!/usr/bin/env python3
"""
MCP Gateway - Unified interface for all MCP servers
Provides health monitoring, routing, and error handling
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
request_count = Counter('mcp_gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('mcp_gateway_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_servers = Gauge('mcp_gateway_active_servers', 'Number of active MCP servers')
error_count = Counter('mcp_gateway_errors_total', 'Total errors', ['server', 'error_type'])

# Initialize FastAPI app
app = FastAPI(
    title="MCP Gateway",
    description="Unified interface for AI Orchestra MCP servers",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP Server registry
MCP_SERVERS = {
    "cloud-run": {
        "url": "http://localhost:8001",
        "name": "Cloud Run MCP Server",
        "health": "/health",
        "capabilities": ["deploy", "update", "status", "list", "logs", "scale"]
    },
    "secrets": {
        "url": "http://localhost:8002",
        "name": "Secrets Manager MCP Server",
        "health": "/health",
        "capabilities": ["get", "create", "update", "list", "versions"]
    },
    "memory": {
        "url": "http://localhost:8003",
        "name": "Memory Management MCP Server",
        "health": "/health",
        "capabilities": ["store", "retrieve", "query", "consolidate", "sync"]
    },
    "orchestrator": {
        "url": "http://localhost:8004",
        "name": "Orchestrator MCP Server",
        "health": "/health",
        "capabilities": ["switchMode", "runWorkflow", "getStatus", "executeTask"]
    }
}

# Health check cache
health_cache: Dict[str, Dict[str, Any]] = {}
HEALTH_CHECK_INTERVAL = 30  # seconds


class ServerHealth(BaseModel):
    """Health status of an MCP server"""
    name: str
    url: str
    healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class GatewayStatus(BaseModel):
    """Overall gateway status"""
    healthy: bool
    servers: Dict[str, ServerHealth]
    total_servers: int
    healthy_servers: int
    timestamp: datetime


class MCPRequest(BaseModel):
    """Generic MCP request model"""
    server: str = Field(..., description="Target MCP server")
    action: str = Field(..., description="Action to perform")
    params: Dict[str, Any] = Field(default={}, description="Parameters for the action")


async def check_server_health(server_id: str, server_info: Dict[str, Any]) -> ServerHealth:
    """Check health of a single MCP server"""
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{server_info['url']}{server_info['health']}")
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ServerHealth(
                    name=server_info['name'],
                    url=server_info['url'],
                    healthy=True,
                    last_check=datetime.utcnow(),
                    response_time_ms=response_time_ms
                )
            else:
                return ServerHealth(
                    name=server_info['name'],
                    url=server_info['url'],
                    healthy=False,
                    last_check=datetime.utcnow(),
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}"
                )
                
    except Exception as e:
        logger.error(f"Health check failed for {server_id}: {e}")
        error_count.labels(server=server_id, error_type=type(e).__name__).inc()
        
        return ServerHealth(
            name=server_info['name'],
            url=server_info['url'],
            healthy=False,
            last_check=datetime.utcnow(),
            error=str(e)
        )


async def periodic_health_check():
    """Periodically check health of all MCP servers"""
    while True:
        try:
            for server_id, server_info in MCP_SERVERS.items():
                health = await check_server_health(server_id, server_info)
                health_cache[server_id] = health.dict()
            
            # Update active servers metric
            healthy_count = sum(1 for h in health_cache.values() if h.get('healthy', False))
            active_servers.set(healthy_count)
            
        except Exception as e:
            logger.error(f"Error in periodic health check: {e}")
        
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)


@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup"""
    logger.info("Starting MCP Gateway...")
    
    # Start periodic health check
    asyncio.create_task(periodic_health_check())
    
    # Initial health check
    for server_id, server_info in MCP_SERVERS.items():
        health = await check_server_health(server_id, server_info)
        health_cache[server_id] = health.dict()
    
    logger.info("MCP Gateway started successfully")


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


@app.get("/")
async def root():
    """Gateway information"""
    return {
        "service": "MCP Gateway",
        "version": "2.0.0",
        "description": "Unified interface for AI Orchestra MCP servers",
        "servers": list(MCP_SERVERS.keys()),
        "endpoints": {
            "/health": "Overall system health",
            "/status": "Detailed server status",
            "/metrics": "Prometheus metrics",
            "/mcp/execute": "Execute MCP action",
            "/mcp/tools": "List available tools",
            "/mcp/{server}/proxy": "Proxy requests to specific server"
        }
    }


@app.get("/health")
async def health_check():
    """Overall gateway health check"""
    healthy_count = sum(1 for h in health_cache.values() if h.get('healthy', False))
    total_count = len(MCP_SERVERS)
    
    # Gateway is healthy if at least 50% of servers are healthy
    is_healthy = healthy_count >= (total_count / 2)
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "healthy_servers": healthy_count,
        "total_servers": total_count,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status", response_model=GatewayStatus)
async def detailed_status():
    """Detailed status of all MCP servers"""
    servers = {}
    
    for server_id in MCP_SERVERS:
        if server_id in health_cache:
            servers[server_id] = ServerHealth(**health_cache[server_id])
        else:
            # If not in cache, check now
            health = await check_server_health(server_id, MCP_SERVERS[server_id])
            servers[server_id] = health
            health_cache[server_id] = health.dict()
    
    healthy_count = sum(1 for s in servers.values() if s.healthy)
    
    return GatewayStatus(
        healthy=healthy_count == len(servers),
        servers=servers,
        total_servers=len(servers),
        healthy_servers=healthy_count,
        timestamp=datetime.utcnow()
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


@app.post("/mcp/execute")
async def execute_mcp_action(request: MCPRequest):
    """Execute an action on a specific MCP server"""
    if request.server not in MCP_SERVERS:
        raise HTTPException(status_code=404, detail=f"Unknown server: {request.server}")
    
    server_info = MCP_SERVERS[request.server]
    
    # Check if server is healthy
    if request.server in health_cache and not health_cache[request.server].get('healthy', False):
        raise HTTPException(
            status_code=503,
            detail=f"Server {request.server} is not healthy"
        )
    
    try:
        # Route request to appropriate server
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{server_info['url']}/mcp/{request.action}",
                json=request.params
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
            
            return response.json()
            
    except httpx.TimeoutException:
        error_count.labels(server=request.server, error_type="timeout").inc()
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        error_count.labels(server=request.server, error_type="error").inc()
        logger.error(f"Error executing action on {request.server}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/tools")
async def list_all_tools():
    """List all available MCP tools across all servers"""
    tools = {}
    
    for server_id, server_info in MCP_SERVERS.items():
        # Skip unhealthy servers
        if server_id in health_cache and not health_cache[server_id].get('healthy', False):
            continue
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{server_info['url']}/mcp/tools")
                if response.status_code == 200:
                    tools[server_id] = {
                        "server": server_info['name'],
                        "tools": response.json()
                    }
        except Exception as e:
            logger.warning(f"Failed to get tools from {server_id}: {e}")
    
    return tools


@app.api_route("/mcp/{server}/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(server: str, path: str, request: Request):
    """Proxy requests to specific MCP server"""
    if server not in MCP_SERVERS:
        raise HTTPException(status_code=404, detail=f"Unknown server: {server}")
    
    server_info = MCP_SERVERS[server]
    target_url = f"{server_info['url']}/{path}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                content=await request.body(),
                headers=dict(request.headers)
            )
            
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except Exception as e:
        logger.error(f"Proxy error for {server}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_count.labels(server="gateway", error_type=type(exc).__name__).inc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )