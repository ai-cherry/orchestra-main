#!/usr/bin/env python3
"""
AI Agent Discovery & Integration System
Automatically configures MCP server access for all AI agents in the cherry_ai ecosystem.
"""

import asyncio
import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import psycopg2

# Import resilient Redis client
from core.redis import ResilientRedisClient, RedisConfig


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    name: str
    type: str  # "code", "git", "tools", "memory", etc.
    port: int
    capabilities: List[str]
    description: str
    priority: int  # Lower = higher priority
    health_endpoint: str
    environment_vars: Dict[str, str]


@dataclass
class AIAgentConfig:
    """Configuration for an AI agent."""
    name: str
    type: str  # "roo", "factory", "claude", "openai", "cursor"
    mcp_servers: List[str]  # Which MCP servers this agent should use
    routing_rules: Dict[str, str]  # Request type -> MCP server mapping
    cache_settings: Dict[str, Any]
    rate_limits: Dict[str, int]
    auto_configure: bool = True


class AIAgentDiscoverySystem:
    """Central system for AI agent discovery and MCP server integration."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.redis_client = None
        self.mcp_servers: Dict[str, MCPServerInfo] = {}
        self.ai_agents: Dict[str, AIAgentConfig] = {}
        self._initialize_redis()
        self._load_mcp_servers()
        self._load_ai_agents()

    def _initialize_redis(self):
        """Initialize resilient Redis connection for caching and coordination."""
        try:
            # Use resilient Redis client with automatic fallback
            redis_config = RedisConfig.from_env()
            self.redis_client = ResilientRedisClient(redis_config)
            print(f"✅ Resilient Redis client initialized (mode: {redis_config.mode})")
        except Exception as e:
            print(f"⚠️  Redis initialization error: {e}")
            # Create a minimal fallback client
            self.redis_client = None

    def _load_mcp_servers(self):
        """Load and register all available MCP servers."""
        self.mcp_servers = {
            "memory": MCPServerInfo(
                name="memory",
                type="memory",
                port=8003,
                capabilities=["context_storage", "vector_search", "memory_management"],
                description="Memory and context management with PostgreSQL + Weaviate",
                priority=1,
                health_endpoint="/health",
                environment_vars={"POSTGRES_URL": "postgresql://postgres:postgres@postgres:5432/cherry_ai"}
            ),
            "conductor": MCPServerInfo(
                name="conductor",
                type="coordination",
                port=8002,
                capabilities=["workflow_management", "task_coordination", "agent_coordination"],
                description="Agent coordination and workflow management",
                priority=1,
                health_endpoint="/health",
                environment_vars={"API_URL": "http://api:8080"}
            ),
            "tools": MCPServerInfo(
                name="tools",
                type="tools",
                port=8006,
                capabilities=["tool_discovery", "tool_execution", "postgres_query", "cache_operations"],
                description="Tool registry and execution with PostgreSQL/Redis/Weaviate tools",
                priority=2,
                health_endpoint="/health",
                environment_vars={}
            ),
            "code-intelligence": MCPServerInfo(
                name="code-intelligence",
                type="code",
                port=8007,
                capabilities=["ast_analysis", "function_search", "complexity_analysis", "code_smells"],
                description="Advanced code analysis and intelligence",
                priority=2,
                health_endpoint="/health",
                environment_vars={}
            ),
            "git-intelligence": MCPServerInfo(
                name="git-intelligence",
                type="git",
                port=8008,
                capabilities=["git_history", "blame_analysis", "hotspot_detection", "contributor_stats"],
                description="Git history and change analysis",
                priority=3,
                health_endpoint="/health",
                environment_vars={}
            ),
            "weaviate": MCPServerInfo(
                name="weaviate",
                type="vector",
                port=8001,
                capabilities=["vector_search", "semantic_search", "embedding_storage"],
                description="Vector database operations",
                priority=2,
                health_endpoint="/health",
                environment_vars={"WEAVIATE_URL": "http://weaviate:8080"}
            ),
            "deployment": MCPServerInfo(
                name="deployment",
                type="deployment",
                port=8005,
                capabilities=["vultr_deployment", "infrastructure_management"],
                description="Deployment and infrastructure management",
                priority=3,
                health_endpoint="/health",
                environment_vars={"VULTR_API_KEY": "${VULTR_API_KEY}"}
            )
        }

    def _load_ai_agents(self):
        """Load and configure AI agent settings."""
        self.ai_agents = {
            "roo": AIAgentConfig(
                name="roo",
                type="roo",
                mcp_servers=["memory", "conductor", "tools", "code-intelligence", "git-intelligence"],
                routing_rules={
                    "code_analysis": "code-intelligence",
                    "git_operations": "git-intelligence", 
                    "context_retrieval": "memory",
                    "tool_execution": "tools",
                    "workflow_management": "conductor"
                },
                cache_settings={"ttl": 3600, "strategy": "lru"},
                rate_limits={"requests_per_minute": 120}
            ),
            "factory-architect": AIAgentConfig(
                name="factory-architect",
                type="factory",
                mcp_servers=["conductor", "memory", "code-intelligence", "deployment"],
                routing_rules={
                    "system_design": "conductor",
                    "architecture_planning": "memory",
                    "code_structure": "code-intelligence",
                    "deployment_planning": "deployment"
                },
                cache_settings={"ttl": 7200, "strategy": "lfu"},
                rate_limits={"requests_per_minute": 60}
            ),
            "factory-code": AIAgentConfig(
                name="factory-code",
                type="factory",
                mcp_servers=["code-intelligence", "git-intelligence", "tools", "memory"],
                routing_rules={
                    "code_generation": "code-intelligence",
                    "refactoring": "code-intelligence",
                    "optimization": "tools",
                    "code_context": "git-intelligence"
                },
                cache_settings={"ttl": 1800, "strategy": "lru"},
                rate_limits={"requests_per_minute": 100}
            ),
            "factory-debug": AIAgentConfig(
                name="factory-debug",
                type="factory",
                mcp_servers=["tools", "code-intelligence", "git-intelligence", "memory"],
                routing_rules={
                    "error_analysis": "code-intelligence",
                    "debugging": "tools",
                    "performance_profiling": "tools",
                    "error_history": "git-intelligence"
                },
                cache_settings={"ttl": 900, "strategy": "lru"},
                rate_limits={"requests_per_minute": 80}
            ),
            "claude": AIAgentConfig(
                name="claude",
                type="claude",
                mcp_servers=["memory", "code-intelligence", "git-intelligence", "tools"],
                routing_rules={
                    "general_coding": "code-intelligence",
                    "context_understanding": "memory",
                    "change_analysis": "git-intelligence",
                    "tool_usage": "tools"
                },
                cache_settings={"ttl": 3600, "strategy": "lru"},
                rate_limits={"requests_per_minute": 150}
            ),
            "cursor": AIAgentConfig(
                name="cursor",
                type="cursor",
                mcp_servers=["code-intelligence", "git-intelligence", "tools", "memory"],
                routing_rules={
                    "code_completion": "code-intelligence",
                    "file_history": "git-intelligence",
                    "quick_tools": "tools",
                    "project_context": "memory"
                },
                cache_settings={"ttl": 1800, "strategy": "lru"},
                rate_limits={"requests_per_minute": 200}
            ),
            "openai": AIAgentConfig(
                name="openai",
                type="openai",
                mcp_servers=["tools", "memory", "code-intelligence"],
                routing_rules={
                    "general_assistance": "tools",
                    "context_retrieval": "memory",
                    "code_help": "code-intelligence"
                },
                cache_settings={"ttl": 3600, "strategy": "lru"},
                rate_limits={"requests_per_minute": 100}
            )
        }

    async def generate_configurations(self):
        """Generate configuration files for all AI agents."""
        print("🔧 Generating AI agent configurations...")
        
        # Update Roo configuration
        await self._update_roo_config()
        
        # Update Factory AI configuration  
        await self._update_factory_config()
        
        # Generate Cursor configuration
        await self._update_cursor_config()
        
        # Generate Claude configuration
        await self._generate_claude_config()
        
        # Generate OpenAI configuration
        await self._generate_openai_config()
        
        # Create unified discovery endpoint
        await self._create_discovery_endpoint()

    async def _update_roo_config(self):
        """Update Roo MCP configuration with enhanced servers."""
        roo_config = {
            "mcpServers": {},
            "servers": [],
            "routing": self.ai_agents["roo"].routing_rules,
            "cache": self.ai_agents["roo"].cache_settings,
            "rate_limits": self.ai_agents["roo"].rate_limits
        }
        
        for server_name in self.ai_agents["roo"].mcp_servers:
            server = self.mcp_servers[server_name]
            roo_config["mcpServers"][server_name] = {
                "command": "python",
                "args": [f"${{workspaceFolder}}/mcp_server/servers/{server_name.replace('-', '_')}_server.py"],
                "env": {
                    "REDIS_URL": "${REDIS_URL:-redis://redis:6379}",
                    **server.environment_vars
                },
                "alwaysAllow": [f"{capability}" for capability in server.capabilities]
            }
            
            roo_config["servers"].append({
                "name": server_name,
                "port": server.port,
                "capabilities": server.capabilities,
                "description": server.description,
                "priority": server.priority,
                "health_endpoint": server.health_endpoint
            })
        
        # Write updated config
        config_path = self.project_root / ".roo" / "mcp.json"
        with open(config_path, 'w') as f:
            json.dump(roo_config, f, indent=2)
        
        print("✅ Updated Roo MCP configuration")

    async def _update_factory_config(self):
        """Update Factory AI configuration with MCP server mappings."""
        config_path = self.project_root / ".factory" / "config.yaml"
        
        # Load existing config
        with open(config_path, 'r') as f:
            factory_config = yaml.safe_load(f)
        
        # Add MCP integration section
        factory_config["mcp_integration"] = {
            "enabled": True,
            "discovery_endpoint": "http://localhost:8010/discover",
            "servers": {}
        }
        
        # Map each Factory AI droid to appropriate MCP servers
        for agent_name, agent_config in self.ai_agents.items():
            if agent_config.type == "factory":
                factory_config["mcp_integration"]["servers"][agent_name] = {
                    "mcp_servers": agent_config.mcp_servers,
                    "routing_rules": agent_config.routing_rules,
                    "cache_settings": agent_config.cache_settings,
                    "rate_limits": agent_config.rate_limits
                }
        
        # Write updated config
        with open(config_path, 'w') as f:
            yaml.dump(factory_config, f, default_flow_style=False, indent=2)
        
        print("✅ Updated Factory AI configuration")

    async def _update_cursor_config(self):
        """Update Cursor MCP configuration."""
        cursor_config = {
            "mcp-servers": {}
        }
        
        for server_name in self.ai_agents["cursor"].mcp_servers:
            server = self.mcp_servers[server_name]
            cursor_config["mcp-servers"][server_name] = {
                "command": "python",
                "args": [f"mcp_server/servers/{server_name.replace('-', '_')}_server.py"],
                "env": {
                    "REDIS_URL": "${REDIS_URL:-redis://redis:6379}",
                    f"MCP_{server_name.upper().replace('-', '_')}_PORT": f"${{MCP_{server_name.upper().replace('-', '_')}_PORT:-{server.port}}}",
                    **server.environment_vars
                }
            }
        
        # Write to Cursor config
        config_path = self.project_root / ".cursor" / "mcp.json"
        with open(config_path, 'w') as f:
            json.dump(cursor_config, f, indent=2)
        
        print("✅ Updated Cursor MCP configuration")

    async def _generate_claude_config(self):
        """Generate Claude MCP configuration."""
        claude_config = {
            "version": "1.0.0",
            "mcp_servers": {},
            "routing": self.ai_agents["claude"].routing_rules,
            "cache": self.ai_agents["claude"].cache_settings
        }
        
        for server_name in self.ai_agents["claude"].mcp_servers:
            server = self.mcp_servers[server_name]
            claude_config["mcp_servers"][server_name] = {
                "endpoint": f"http://localhost:{server.port}",
                "capabilities": server.capabilities,
                "description": server.description,
                "priority": server.priority
            }
        
        # Write Claude config
        config_path = self.project_root / "claude_mcp_config.json"
        with open(config_path, 'w') as f:
            json.dump(claude_config, f, indent=2)
        
        print("✅ Generated Claude MCP configuration")

    async def _generate_openai_config(self):
        """Generate OpenAI MCP configuration."""
        openai_config = {
            "version": "1.0.0",
            "mcp_integration": {
                "enabled": True,
                "servers": {},
                "routing": self.ai_agents["openai"].routing_rules
            }
        }
        
        for server_name in self.ai_agents["openai"].mcp_servers:
            server = self.mcp_servers[server_name]
            openai_config["mcp_integration"]["servers"][server_name] = {
                "endpoint": f"http://localhost:{server.port}",
                "capabilities": server.capabilities,
                "auth_required": False
            }
        
        # Write OpenAI config  
        config_path = self.project_root / "openai_mcp_config.json"
        with open(config_path, 'w') as f:
            json.dump(openai_config, f, indent=2)
        
        print("✅ Generated OpenAI MCP configuration")

    async def _create_discovery_endpoint(self):
        """Create a discovery endpoint for AI agents to find MCP servers."""
        discovery_data = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "mcp_servers": {name: asdict(server) for name, server in self.mcp_servers.items()},
            "ai_agents": {name: asdict(agent) for name, agent in self.ai_agents.items()},
            "endpoints": {
                "discovery": "http://localhost:8010/discover",
                "health": "http://localhost:8010/health",
                "metrics": "http://localhost:8010/metrics"
            }
        }
        
        # Try to cache in Redis with resilient client
        if self.redis_client:
            try:
                await self.redis_client.set(
                    "mcp:discovery",
                    json.dumps(discovery_data),
                    ex=3600  # 1 hour TTL
                )
                print("✅ Cached discovery data in Redis")
            except Exception as e:
                print(f"⚠️  Redis cache failed: {e}")
        
        # Write to file as backup
        discovery_path = self.project_root / "mcp_discovery.json"
        with open(discovery_path, 'w') as f:
            json.dump(discovery_data, f, indent=2)
        
        print("✅ Created MCP discovery endpoint")

    async def create_smart_routing_system(self):
        """Create intelligent routing system for AI agents."""
        routing_script = '''#!/usr/bin/env python3
"""
Smart MCP Router - Intelligent routing for AI agents
"""

import asyncio
import json
import redis
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MCP Smart Router", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

redis_client = redis.from_url("redis://redis:6379", decode_responses=True)

@app.get("/discover")
async def discover_mcp_servers():
    """Discover available MCP servers."""
    try:
        discovery_data = redis_client.get("mcp:discovery")
        if discovery_data:
            return json.loads(discovery_data)
        return {"error": "Discovery data not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route")
async def route_request(request: Dict[str, Any]):
    """Intelligently route requests to appropriate MCP servers."""
    agent_type = request.get("agent_type")
    request_type = request.get("request_type")
    
    # Load routing rules from cache
    routing_key = f"mcp:routing:{agent_type}"
    routing_rules = redis_client.hgetall(routing_key)
    
    if request_type in routing_rules:
        target_server = routing_rules[request_type]
        return {"target_server": target_server, "endpoint": f"http://localhost:800{target_server[-1]}"}
    
    # Fallback to default server
    return {"target_server": "tools", "endpoint": "http://localhost:8006"}

@app.get("/health")
async def health_check():
    """Health check for the router."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
'''
        
        router_path = self.project_root / "mcp_smart_router.py"
        with open(router_path, 'w') as f:
            f.write(routing_script)
        
        print("✅ Created smart routing system")

    async def create_automation_scripts(self):
        """Create automation scripts for different AI agents."""
        
        # Auto-start script for all MCP servers
        start_script = '''#!/bin/bash
# Auto-start all MCP servers for AI agents

echo "🚀 Starting MCP servers for AI agents..."

# Start MCP servers in background
python mcp_server/servers/memory_server.py &
python mcp_server/servers/conductor_server.py &
python mcp_server/servers/tools_server.py &
python mcp_server/servers/code_intelligence_server.py &
python mcp_server/servers/git_intelligence_server.py &
python mcp_server/servers/weaviate_direct_mcp_server.py &
python mcp_server/servers/deployment_server.py &

# Start smart router
python mcp_smart_router.py &

echo "✅ All MCP servers started"
echo "🔗 Discovery endpoint: http://localhost:8010/discover"
'''
        
        script_path = self.project_root / "start_mcp_agents.sh"
        with open(script_path, 'w') as f:
            f.write(start_script)
        script_path.chmod(0o755)
        
        # Agent validation script
        validation_script = '''#!/usr/bin/env python3
"""
Validate AI Agent MCP Integration
"""

import asyncio
import aiohttp
import json

async def validate_mcp_integration():
    """Validate that all AI agents can connect to MCP servers."""
    
    print("🔍 Validating AI Agent MCP Integration...")
    
    # Check discovery endpoint
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8010/discover") as resp:
                if resp.status == 200:
                    discovery = await resp.json()
                    print(f"✅ Discovery endpoint working ({len(discovery.get('mcp_servers', {}))} servers)")
                else:
                    print("❌ Discovery endpoint failed")
        except Exception as e:
            print(f"❌ Discovery endpoint error: {e}")
    
    # Check individual MCP servers
    servers = [8001, 8002, 8003, 8005, 8006, 8007, 8008]
    for port in servers:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/health", timeout=5) as resp:
                    if resp.status == 200:
                        print(f"✅ MCP server on port {port} healthy")
                    else:
                        print(f"⚠️  MCP server on port {port} status: {resp.status}")
        except Exception:
            print(f"❌ MCP server on port {port} unreachable")

if __name__ == "__main__":
    asyncio.run(validate_mcp_integration())
'''
        
        validation_path = self.project_root / "scripts" / "validate_ai_agents.py"
        with open(validation_path, 'w') as f:
            f.write(validation_script)
        
        print("✅ Created automation scripts")

    async def setup_ai_agent_integration(self):
        """Complete setup of AI agent integration."""
        print("🤖 Setting up AI Agent Integration System...")
        
        await self.generate_configurations()
        await self.create_smart_routing_system() 
        await self.create_automation_scripts()
        
        # Cache routing rules in Redis with resilient client
        if self.redis_client:
            try:
                for agent_name, agent_config in self.ai_agents.items():
                    routing_key = f"mcp:routing:{agent_name}"
                    await self.redis_client.hset(routing_key, mapping=agent_config.routing_rules)
                    await self.redis_client.expire(routing_key, 86400)  # 24 hours
                print("✅ Cached routing rules in Redis")
            except Exception as e:
                print(f"⚠️  Redis routing cache failed: {e}")
        
        print("\n" + "="*50)
        print("🎉 AI Agent Integration Complete!")
        print("="*50)
        print("📋 What's been configured:")
        print("   ✅ Roo AI: Enhanced MCP access")
        print("   ✅ Factory AI Droids: Intelligent routing")
        print("   ✅ Cursor: Advanced coding context")
        print("   ✅ Claude: Comprehensive tool access")
        print("   ✅ OpenAI: Smart integration")
        print("   ✅ Smart Router: Intelligent request routing")
        print("   ✅ Discovery Endpoint: Auto-configuration")
        print("\n🚀 Start all services: ./start_mcp_agents.sh")
        print("🔍 Validate setup: python scripts/validate_ai_agents.py")
        print("🌐 Discovery URL: http://localhost:8010/discover")


async def main():
    """Main setup function."""
    system = AIAgentDiscoverySystem()
    await system.setup_ai_agent_integration()


if __name__ == "__main__":
    asyncio.run(main()) 