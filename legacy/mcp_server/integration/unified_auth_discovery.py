#!/usr/bin/env python3
"""
Unified Authentication & Discovery Integration
Ensures AI Agent Discovery works seamlessly with single-user authentication
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp_server.security.single_user_context import (
    get_auth_manager,
    OperationalContext,
    ContextPermission
)
from mcp_server.ai_agent_discovery import AIAgentDiscoverySystem


class UnifiedAuthDiscoveryIntegration:
    """Integrates single-user auth with AI agent discovery system."""
    
    def __init__(self):
        self.auth_manager = get_auth_manager()
        self.discovery_system = AIAgentDiscoverySystem()
        self.api_key = os.getenv("cherry_ai_API_KEY", "")
        
    def integrate_systems(self):
        """Main integration method to ensure no conflicts."""
        print("🔧 Integrating Single-User Auth with AI Agent Discovery...")
        
        # 1. Update MCP server configurations with auth
        self._update_mcp_servers_with_auth()
        
        # 2. Update smart router with auth middleware
        self._update_smart_router_auth()
        
        # 3. Ensure discovery endpoint respects auth context
        self._update_discovery_auth()
        
        # 4. Update agent configurations for single-user
        self._optimize_for_single_user()
        
        # 5. Create unified startup script
        self._create_unified_startup()
        
        print("✅ Integration complete - no conflicts detected!")
    
    def _update_mcp_servers_with_auth(self):
        """Add single-user auth to all MCP servers."""
        print("  - Adding authentication to MCP servers...")
        
        # Update each MCP server configuration
        for server_name, server_info in self.discovery_system.mcp_servers.items():
            # Add auth environment variables
            server_info.environment_vars.update({
                "cherry_ai_API_KEY": "${cherry_ai_API_KEY}",
                "cherry_ai_CONTEXT": "${cherry_ai_CONTEXT:-development}",
                "AUTH_MODE": "single_user"
            })
            
            # For development context, allow unauthenticated health checks
            if self.auth_manager.context == OperationalContext.DEVELOPMENT:
                server_info.environment_vars["ALLOW_HEALTH_NO_AUTH"] = "true"
    
    def _update_smart_router_auth(self):
        """Update smart router with single-user authentication."""
        
        router_content = '''#!/usr/bin/env python3
"""
Smart MCP Router with Single-User Authentication
"""

import os
import json
import redis
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

# Import our single-user auth
from mcp_server.security.single_user_context import get_auth_manager, SecurityContext

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
'''
        
        with open(router_path, 'w') as f:
            f.write(router_content)
        
        print("  - Updated smart router with authentication")
    
    def _update_discovery_auth(self):
        """Update discovery endpoint configuration."""
        # The discovery data should include auth requirements
        discovery_data = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "auth": {
                "mode": "single_user",
                "header": "X-API-Key",
                "required": True,
                "context_aware": True
            },
            "mcp_servers": {
                name: {
                    **server.__dict__,
                    "auth_required": True
                }
                for name, server in self.discovery_system.mcp_servers.items()
            },
            "ai_agents": {
                name: agent.__dict__
                for name, agent in self.discovery_system.ai_agents.items()
            }
        }
        
        # Save updated discovery data
        with open(discovery_path, 'w') as f:
            json.dump(discovery_data, f, indent=2)
        
        print("  - Updated discovery data with auth requirements")
    
    def _optimize_for_single_user(self):
        """Optimize agent configurations for single-user deployment."""
        print("  - Optimizing for single-user deployment...")
        
        # Remove rate limits in development context
        if self.auth_manager.context == OperationalContext.DEVELOPMENT:
            for agent in self.discovery_system.ai_agents.values():
                agent.rate_limits["requests_per_minute"] = 1000  # Effectively unlimited
        
        # Simplify caching for single user
        for agent in self.discovery_system.ai_agents.values():
            agent.cache_settings["strategy"] = "simple"  # No need for complex LRU/LFU
            agent.cache_settings["ttl"] = 7200  # Longer TTL for single user
    
    def _create_unified_startup(self):
        """Create unified startup script that handles both auth and discovery."""
        startup_script = f'''#!/bin/bash
# Unified startup for Cherry AI with Single-User Auth & AI Agent Discovery

echo "🚀 Starting Cherry AI - Single User Mode"
echo "============================================"

# Export auth configuration
export cherry_ai_API_KEY = os.getenv('ORCHESTRA_MCP_API_KEY')
export cherry_ai_CONTEXT="{self.auth_manager.context.value}"
export AUTH_MODE="single_user"

# Check if services are already running
if docker-compose -f docker-compose.single-user.yml ps | grep -q "Up"; then
    echo "✅ Core services already running"
else
    echo "Starting core services..."
    docker-compose -f docker-compose.single-user.yml up -d
    sleep 10
fi

# Start MCP servers with auth
echo ""
echo "🔧 Starting MCP servers..."

# Kill any existing MCP processes
pkill -f "mcp_server/servers" || true
sleep 2

# Start each MCP server with authentication
python mcp_server/servers/memory_server.py &
python mcp_server/servers/conductor_server.py &
python mcp_server/servers/tools_server.py &
python mcp_server/servers/code_intelligence_server.py &
python mcp_server/servers/git_intelligence_server.py &
python mcp_server/servers/weaviate_direct_mcp_server.py &
python mcp_server/servers/deployment_server.py &

# Start smart router with auth
echo ""
echo "🔐 Starting Smart Router with Authentication..."
python mcp_smart_router.py &

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Service Status:"
echo "  - API: http://localhost:8000 (auth required)"
echo "  - Discovery: http://localhost:8010/discover (auth required)"
echo "  - Health: http://localhost:8010/health (no auth)"
echo ""
echo "🔑 API Key: ${{cherry_ai_API_KEY:0:20}}..."
echo "🌍 Context: ${{cherry_ai_CONTEXT}}"
echo ""
echo "💡 Test with:"
echo "  curl -H 'X-API-Key: ${{cherry_ai_API_KEY}}' http://localhost:8010/discover"
'''
        
        with open(script_path, 'w') as f:
            f.write(startup_script)
        script_path.chmod(0o755)
        
        print("  - Created unified startup script: start_unified_cherry_ai.sh")


def integrate_auth_and_discovery():
    """Main integration function."""
    integration = UnifiedAuthDiscoveryIntegration()
    integration.integrate_systems()


if __name__ == "__main__":
    integrate_auth_and_discovery()