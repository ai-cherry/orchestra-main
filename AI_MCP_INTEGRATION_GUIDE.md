# 🚀 AI Coding Helpers MCP Integration Guide

**Ensuring All AI Services Leverage MCP for Optimal Contextualization**

## Executive Summary

This guide ensures that all your AI coding helpers (Roo, Cursor, Factory AI, Claude, and OpenAI) are properly configured to leverage the Model Context Protocol (MCP) server infrastructure for the best possible AI coding experience with comprehensive contextualization.

## ✅ Current Integration Status

Based on latest verification, here's your current setup:

### 🖥️ MCP Servers Configured
- **Memory Server** (Port 8003): Context storage, vector search, memory management
- **Conductor Server** (Port 8002): Agent coordination and workflow management  
- **Tools Server** (Port 8006): Tool discovery and execution with database operations
- **Code Intelligence Server** (Port 8007): AST analysis, function search, complexity analysis
- **Git Intelligence Server** (Port 8008): Git history and change analysis
- **Weaviate Direct Server** (Port 8001): Direct vector database operations
- **Deployment Server** (Port 8005): Infrastructure deployment operations

### 🤖 AI Services Integration Status
- ✅ **Claude**: Fully configured via `claude_mcp_config.json`
- ✅ **OpenAI**: Fully configured via `openai_mcp_config.json`  
- ✅ **Cursor**: Fully configured via `.cursor/mcp.json`
- ✅ **Roo**: Fully configured via `.roo/mcp.json`
- ✅ **Factory AI**: Configured via `.factory-ai-config`

## 🏗️ Infrastructure Requirements

### Database Stack (✅ Currently Running)
```bash
# PostgreSQL - Primary relational database
docker ps | grep postgres
# Status: ✅ HEALTHY - Port 5432

# Weaviate - Vector database for embeddings
docker ps | grep weaviate  
# Status: ✅ RUNNING - Port 8080

# Redis - Caching and session management
docker ps | grep redis
# Status: ✅ HEALTHY - Port 6379
```

## 🚀 Quick Start Commands

### 1. Verify Current Status
```bash
# Run comprehensive verification
python scripts/verify_ai_mcp_integration.py

# Quick health check only
python scripts/verify_ai_mcp_integration.py --health-check-only
```

### 2. Start All MCP Servers
```bash
# Method 1: Use the comprehensive startup script (recommended)
./start_comprehensive_ai_system.sh

# Method 2: Start MCP system only
./start_mcp_system.sh

# Method 3: Start for coding specifically
./scripts/start_mcp_for_coding.sh
```

### 3. Verify Everything is Running
```bash
# Check all ports are listening
lsof -i :8002,8003,8006,8007,8008 | grep LISTEN

# Check server health endpoints
curl http://localhost:8003/health  # Memory server
curl http://localhost:8002/health  # Conductor server  
curl http://localhost:8006/health  # Tools server
```

## 🔧 Configuration Details

### Claude Configuration (`claude_mcp_config.json`)
```json
{
  "version": "1.0.0",
  "mcp_servers": {
    "memory": {
      "endpoint": "http://localhost:8003",
      "capabilities": ["context_storage", "vector_search", "memory_management"],
      "priority": 1
    },
    "code-intelligence": {
      "endpoint": "http://localhost:8007", 
      "capabilities": ["ast_analysis", "function_search", "complexity_analysis"],
      "priority": 2
    },
    "git-intelligence": {
      "endpoint": "http://localhost:8008",
      "capabilities": ["git_history", "blame_analysis", "hotspot_detection"],
      "priority": 3
    }
  },
  "routing": {
    "general_coding": "code-intelligence",
    "context_understanding": "memory",
    "change_analysis": "git-intelligence"
  }
}
```

### Cursor Configuration (`.cursor/mcp.json`)
```json
{
  "mcp-servers": {
    "code-intelligence": {
      "command": "python",
      "args": ["mcp_server/servers/code_intelligence_server.py"],
      "env": {
        "REDIS_URL": "${REDIS_URL:-redis://redis:6379}",
        "MCP_CODE_INTELLIGENCE_PORT": "${MCP_CODE_INTELLIGENCE_PORT:-8007}"
      }
    },
    "memory": {
      "command": "python", 
      "args": ["mcp_server/servers/memory_server.py"],
      "env": {
        "REDIS_URL": "${REDIS_URL:-redis://redis:6379}",
        "MCP_MEMORY_PORT": "${MCP_MEMORY_PORT:-8003}"
      }
    }
  }
}
```

### Roo Configuration (`.roo/mcp.json`)
```json
{
  "mcpServers": {
    "memory": {
      "command": "python",
      "args": ["${workspaceFolder}/mcp_server/servers/memory_server.py"],
      "alwaysAllow": ["context_storage", "vector_search", "memory_management"]
    },
    "conductor": {
      "command": "python",
      "args": ["${workspaceFolder}/mcp_server/servers/conductor_server.py"],
      "alwaysAllow": ["workflow_management", "task_coordination"]
    }
  },
  "routing": {
    "code_analysis": "code-intelligence",
    "context_retrieval": "memory",
    "workflow_management": "conductor"
  }
}
```

## 🎯 Optimal Usage Patterns

### For AI Coding with Full Context
1. **Start with Memory Context**: All AI helpers can access your project's memory and context
2. **Leverage Code Intelligence**: Get AST analysis, complexity metrics, and code smells
3. **Use Git Intelligence**: Understand change patterns and code evolution
4. **Execute Tools**: Run database queries, cache operations, and tool discovery

### Routing Strategy
- **General Coding Questions** → Code Intelligence Server
- **Context Understanding** → Memory Server  
- **Change Analysis** → Git Intelligence Server
- **Tool Execution** → Tools Server
- **Workflow Management** → Conductor Server

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. MCP Servers Won't Start
```bash
# Check if ports are in use
lsof -i :8002,8003,8006,8007,8008

# Kill existing processes if needed
kill $(lsof -t -i:8003)  # Example for memory server

# Check logs
tail -f /tmp/mcp_memory.log
```

#### 2. Database Connection Issues
```bash
# Test PostgreSQL connection
python -c "from shared.database import UnifiedDatabase; db = UnifiedDatabase(); print(db.health_check())"

# Test Weaviate connection  
curl http://localhost:8080/v1/meta

# Test Redis connection
redis-cli ping
```

#### 3. AI Service Can't Connect
```bash
# Verify MCP server endpoints
curl http://localhost:8003/health
curl http://localhost:8002/health
curl http://localhost:8006/health

# Check configuration files exist
ls -la claude_mcp_config.json .cursor/mcp.json .roo/mcp.json
```

## 🚀 Performance Optimization

### Memory Server Optimization
- **Vector Search**: Optimized for semantic similarity
- **Context Caching**: Redis-backed for fast retrieval
- **PostgreSQL Queries**: Use EXPLAIN ANALYZE for optimization

### Code Intelligence Optimization  
- **AST Caching**: Parse results cached in Redis
- **Complexity Analysis**: Cached per file hash
- **Function Discovery**: Indexed search patterns

### Git Intelligence Optimization
- **History Caching**: Git blame and log results cached
- **Hotspot Detection**: Analyzed and cached results
- **Change Pattern Analysis**: Incremental updates

## 📊 Monitoring & Health Checks

### Automated Health Monitoring
```bash
# Continuous health monitoring
watch -n 30 'python scripts/verify_ai_mcp_integration.py --health-check-only'

# Log aggregation
tail -f /tmp/mcp_*.log | grep -E "(ERROR|WARN|health)"
```

### Performance Metrics
- **Response Times**: < 100ms for cached queries
- **Memory Usage**: Monitor via Redis INFO
- **Database Performance**: PostgreSQL slow query log
- **Vector Search**: Weaviate query performance

## 🎉 Success Indicators

When everything is working optimally, you should see:

1. ✅ All MCP servers responding to health checks
2. ✅ All AI services can route requests to appropriate servers
3. ✅ Context retrieval working across all AI helpers
4. ✅ Code intelligence providing rich analysis
5. ✅ Git history analysis available in real-time
6. ✅ Tool execution working seamlessly

## 🔄 Daily Workflow

### Starting Your AI-Enhanced Development Session
```bash
# 1. Start the comprehensive system
./start_comprehensive_ai_system.sh

# 2. Verify everything is running
python scripts/verify_ai_mcp_integration.py

# 3. Begin coding with enhanced AI assistance
# - Claude: Context-aware responses via memory server
# - Cursor: Code intelligence and AST analysis
# - Roo: Workflow management and coordination
# - OpenAI: Tool execution and general assistance
# - Factory AI: Automated development workflows
```

### Stopping the System
```bash
# Stop all MCP servers
./stop_mcp_system.sh

# Or stop individual servers
kill $(cat /tmp/mcp_memory.pid)
kill $(cat /tmp/mcp_conductor.pid)  
kill $(cat /tmp/mcp_tools.pid)
```

---

## 📝 Quick Reference

| AI Service | Config File | Primary MCP Servers | Key Capabilities |
|------------|-------------|-------------------|------------------|
| Claude | `claude_mcp_config.json` | memory, code-intelligence | Context understanding, code analysis |
| OpenAI | `openai_mcp_config.json` | tools, memory | Tool execution, general assistance |
| Cursor | `.cursor/mcp.json` | code-intelligence, memory | AST analysis, context storage |
| Roo | `.roo/mcp.json` | conductor, memory | Workflow management, coordination |
| Factory AI | `.factory-ai-config` | workspace-aware | Automated development workflows |

**🎯 Result**: All AI coding helpers now have access to comprehensive contextualization through the unified MCP server infrastructure, enabling optimal AI-assisted development with full project understanding.** 