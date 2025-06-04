#!/usr/bin/env python3
"""
Smart MCP Router with Single-User Authentication and Resilient Redis
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

# Import our single-user auth
from mcp_server.security.single_user_context import get_auth_manager, SecurityContext, OperationalContext

# Import resilient Redis client
from core.redis import ResilientRedisClient, RedisConfig, RedisHealthMonitor

app = FastAPI(title="MCP Smart Router", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# Auth setup
auth_manager = get_auth_manager()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize resilient Redis client
redis_config = RedisConfig.from_env()
redis_client = ResilientRedisClient(redis_config)
redis_monitor = RedisHealthMonitor(redis_client)

# Start health monitoring
async def start_monitoring():
    """Start Redis health monitoring."""
    asyncio.create_task(redis_monitor.start_monitoring())

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await start_monitoring()
    print(f"✅ MCP Smart Router started with resilient Redis (mode: {redis_config.mode})")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await redis_monitor.stop_monitoring()
    await redis_client.close()

def get_current_context(api_key: Optional[str] = Depends(api_key_header)) -> SecurityContext:
    """Get current security context."""
    try:
        return auth_manager.authenticate(api_key)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/discover")
async def discover_mcp_servers(context: SecurityContext = Depends(get_current_context)):
    """Discover available MCP servers based on context."""
    try:
        # Try Redis with automatic fallback
        discovery_data = await redis_client.get("mcp:discovery")
        if discovery_data:
            data = json.loads(discovery_data) if isinstance(discovery_data, str) else discovery_data
            # Filter based on context
            if context.context.value != "development":
                # In production, limit discovery
                data["mcp_servers"] = {
                    k: v for k, v in data["mcp_servers"].items()
                    if v.get("priority", 3) <= 2
                }
            return data
        
        # If no data in Redis/fallback, try file
        discovery_file = Path("mcp_discovery.json")
        if discovery_file.exists():
            with open(discovery_file) as f:
                data = json.load(f)
                # Cache in Redis for next time
                await redis_client.set("mcp:discovery", json.dumps(data), ex=300)
                return data
                
        return {"error": "Discovery data not available", "fallback": redis_client.is_fallback_active()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route")
async def route_request(
    request: Dict[str, Any],
    context: SecurityContext = Depends(get_current_context)
):
    """Route requests based on agent type and context."""
    agent_type = request.get("agent_type")
    request_type = request.get("request_type")
    
    # Check permissions based on context
    if context.context == OperationalContext.MAINTENANCE:
        # In maintenance mode, only allow read operations
        if request_type not in ["context_retrieval", "git_operations"]:
            raise HTTPException(status_code=403, detail="Operation not allowed in maintenance mode")
    
    # Get routing rules with automatic fallback
    routing_key = f"mcp:routing:{agent_type}"
    routing_rules = await redis_client.hgetall(routing_key)
    
    # If no rules in Redis, use defaults
    if not routing_rules:
        routing_rules = {
            "code_analysis": "code-intelligence",
            "git_operations": "git-intelligence",
            "context_retrieval": "memory",
            "tool_execution": "tools"
        }
        # Cache defaults for next time
        await redis_client.hset(routing_key, mapping=routing_rules)
    
    if request_type in routing_rules:
        target_server = routing_rules[request_type]
        # Map server name to port
        port_map = {
            "memory": 8003,
            "conductor": 8002,
            "tools": 8006,
            "code-intelligence": 8007,
            "git-intelligence": 8008
        }
        port = port_map.get(target_server, 8006)
        
        # Track routing metrics
        await redis_client.incr(f"mcp:metrics:routing:{target_server}", ex=3600)
        
        return {
            "target_server": target_server,
            "endpoint": f"http://localhost:{port}",
            "auth_required": True,
            "context": context.context.value,
            "redis_status": "healthy" if not redis_client.is_fallback_active() else "fallback"
        }
    
    # Default fallback
    return {"target_server": "tools", "endpoint": "http://localhost:8006"}

@app.get("/health")
async def health_check():
    """Health check with Redis status - no auth required."""
    redis_health = await redis_monitor.get_health_status()
    
    return {
        "status": "healthy" if redis_health["status"] == "healthy" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "auth_mode": "single_user",
        "context": os.getenv("cherry_ai_CONTEXT", "development"),
        "redis": {
            "status": redis_health["status"],
            "mode": redis_config.mode,
            "fallback_active": redis_client.is_fallback_active(),
            "circuit_breaker": redis_health.get("circuit_breaker_state", "unknown"),
            "last_check": redis_health.get("last_check", "never")
        }
    }

@app.get("/metrics")
async def get_metrics(context: SecurityContext = Depends(get_current_context)):
    """Get routing metrics."""
    if context.context != OperationalContext.DEVELOPMENT:
        raise HTTPException(status_code=403, detail="Metrics only available in development")
    
    # Get all routing metrics
    metrics = {}
    pattern = "mcp:metrics:routing:*"
    keys = await redis_client.keys(pattern)
    
    for key in keys:
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        server_name = key.split(":")[-1]
        count = await redis_client.get(key)
        metrics[server_name] = int(count) if count else 0
    
    return {
        "routing_metrics": metrics,
        "redis_health": await redis_monitor.get_health_status(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
