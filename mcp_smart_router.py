#!/usr/bin/env python3
"""
Smart MCP Router with Single-User Authentication
"""

import os
import json
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

# Import our single-user auth
from mcp_server.security.single_user_context import get_auth_manager, SecurityContext, OperationalContext

app = FastAPI(title="MCP Smart Router", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# Auth setup
auth_manager = get_auth_manager()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Redis with fallback
try:
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
    redis_client.ping()
except:
    redis_client = None
    print("⚠️  Redis not available, using file-based fallback")

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
        # Try Redis first
        if redis_client:
            discovery_data = redis_client.get("mcp:discovery")
            if discovery_data:
                data = json.loads(discovery_data)
                # Filter based on context
                if context.context.value != "development":
                    # In production, limit discovery
                    data["mcp_servers"] = {
                        k: v for k, v in data["mcp_servers"].items()
                        if v["priority"] <= 2
                    }
                return data
        
        # Fallback to file
        discovery_file = Path("mcp_discovery.json")
        if discovery_file.exists():
            with open(discovery_file) as f:
                return json.load(f)
                
        return {"error": "Discovery data not available"}
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
    
    # Get routing rules
    if redis_client:
        routing_key = f"mcp:routing:{agent_type}"
        routing_rules = redis_client.hgetall(routing_key)
    else:
        # Fallback routing
        routing_rules = {
            "code_analysis": "code-intelligence",
            "git_operations": "git-intelligence",
            "context_retrieval": "memory",
            "tool_execution": "tools"
        }
    
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
        return {
            "target_server": target_server,
            "endpoint": f"http://localhost:{port}",
            "auth_required": True,
            "context": context.context.value
        }
    
    # Default fallback
    return {"target_server": "tools", "endpoint": "http://localhost:8006"}

@app.get("/health")
async def health_check():
    """Health check - no auth required."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "auth_mode": "single_user",
        "context": os.getenv("cherry_ai_CONTEXT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
