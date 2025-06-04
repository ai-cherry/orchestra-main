# MCP (Model Context Protocol) AI Integration Guide

## Overview
This guide details the integration of MCP servers with the Cherry AI system, using PostgreSQL for relational data and Weaviate for vector operations.

## Architecture

```
┌─────────────────────────────────────────┐
│           Cursor/Claude AI              │
│         (MCP Protocol Client)           │
└────────────────┬────────────────────────┘
                 │ stdio/pipes
┌────────────────┴────────────────────────┐
│            MCP Servers                  │
├─────────────────────────────────────────┤
│  • conductor (Agent coordination)    │
│  • Memory (PostgreSQL + Weaviate)       │
│  • Tools (Tool discovery/execution)     │
│  • Deployment (Infrastructure mgmt)     │
└────────────────┬────────────────────────┘
                 │
┌────────────────┴────────────────────────┐
│         Cherry AI System             │
├─────────────────────────────────────────┤
│  • PostgreSQL (Structured data)         │
│  • Weaviate (Vector search)             │
│  • FastAPI (REST API)                   │
│  • Agent System                         │
└─────────────────────────────────────────┘
```

## MCP Servers

### 1. conductor Server
**Purpose**: Agent coordination and workflow management

**Tools**:
- `list_agents` - List available agents
- `run_agent` - Execute agent with input
- `switch_mode` - Change coordination mode
- `run_workflow` - Execute multi-agent workflow

**Configuration**:
```json
{
  "conductor": {
    "command": "python",
    "args": ["mcp_server/servers/conductor_server.py"],
    "env": {
      "API_URL": "${API_URL:-http://localhost:8080}",
      "API_KEY": "${API_KEY}"
    }
  }
}
```

### 2. Memory Server
**Purpose**: Unified memory management using PostgreSQL and Weaviate

**Tools**:
- `store_memory` - Store agent memory in Weaviate
- `search_memories` - Semantic search for memories
- `get_recent_memories` - Retrieve recent memories
- `store_conversation` - Store conversation history
- `get_conversation_history` - Retrieve conversation
- `create_session` - Create new session (PostgreSQL)
- `add_knowledge` - Add to knowledge base
- `search_knowledge` - Search knowledge base

**Database Split**:
- **PostgreSQL**: Sessions, audit logs, configurations
- **Weaviate**: Memories, conversations, knowledge, embeddings

### 3. Tools Server
**Purpose**: Tool discovery and execution

**Features**:
- Rich tool metadata
- Input/output validation
- Error handling
- Tool categorization

### 4. Weaviate Direct Server
**Purpose**: Direct Weaviate operations for advanced vector search

**Tools**:
- Vector operations
- Collection management
- Hybrid search
- Schema operations

## Database Architecture

### PostgreSQL (Relational Data)
```sql
cherry_ai.agents          -- Agent configurations
cherry_ai.workflows       -- Workflow definitions
cherry_ai.sessions        -- User sessions
cherry_ai.audit_logs      -- System events
cherry_ai.api_keys        -- Authentication
cherry_ai.memory_snapshots -- Vector references
```

### Weaviate (Vector Data)
```python
AgentMemory     # Agent memories with embeddings
Knowledge       # Knowledge base
Conversation    # Conversation history
Document        # Document storage
```

## Integration Patterns

### 1. Agent Memory Storage
```python
# Via MCP
await mcp.call_tool("store_memory", {
    "agent_id": "agent-123",
    "content": "User prefers technical explanations",
    "memory_type": "preference",
    "importance": 0.8
})

# Direct via UnifiedDatabase
db.weaviate.store_memory(
    agent_id="agent-123",
    content="User prefers technical explanations",
    memory_type="preference"
)
```

### 2. Context Retrieval
```python
# Search memories
memories = await mcp.call_tool("search_memories", {
    "agent_id": "agent-123",
    "query": "user preferences",
    "limit": 5
})

# Get conversation context
history = await mcp.call_tool("get_conversation_history", {
    "session_id": session_id,
    "limit": 10
})
```

### 3. Session Management
```python
# Create session (PostgreSQL)
session = await mcp.call_tool("create_session", {
    "user_id": "user-123",
    "agent_id": "agent-456",
    "ttl_hours": 24
})

# Store interaction
await mcp.call_tool("store_conversation", {
    "session_id": session["id"],
    "agent_id": "agent-456",
    "message": "Hello, how can I help?",
    "role": "assistant"
})
```

## Setup Instructions

### 1. Environment Setup
```bash
# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=cherry_ai
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password

# Weaviate
export WEAVIATE_HOST=localhost
export WEAVIATE_PORT=8080
export WEAVIATE_API_KEY=your_key  # Optional

# API
export API_URL=http://localhost:8080
export API_KEY=your_api_key
```

### 2. Database Initialization
```bash
# Setup PostgreSQL schema
python scripts/setup_postgres_schema.py

# Verify setup
python scripts/setup_postgres_schema.py --verify-only
```

### 3. Start MCP Servers
```bash
# In separate terminals
python mcp_server/servers/conductor_server.py
python mcp_server/servers/memory_server.py
python mcp_server/servers/weaviate_direct_mcp_server.py
python mcp_server/servers/tools_server.py
```

### 4. Configure Cursor
Update `.mcp.json` in your Cursor configuration directory with the servers configuration.

## Best Practices

### 1. Memory Management
- Use PostgreSQL for structured queries and state
- Use Weaviate for semantic search and embeddings
- Store vector IDs in PostgreSQL for cross-referencing

### 2. Session Handling
- Create sessions in PostgreSQL with TTL
- Store conversation vectors in Weaviate
- Link via session_id

### 3. Performance
- Batch operations when possible
- Use connection pooling (built-in)
- Cache frequently accessed data
- Index PostgreSQL queries

### 4. Error Handling
```python
try:
    result = await mcp.call_tool("store_memory", {...})
except Exception as e:
    # Fallback to direct storage
    db.weaviate.store_memory(...)
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check database services are running
   - Verify credentials in environment
   - Test connections individually

2. **Schema Issues**
   - Run schema setup script
   - Check Weaviate collections exist
   - Verify PostgreSQL tables

3. **MCP Server Issues**
   - Check server logs
   - Verify Python environment
   - Test tools individually

### Debug Commands
```bash
# Test PostgreSQL
psql -U postgres -d cherry_ai -c "\dt cherry_ai.*"

# Test Weaviate
curl http://localhost:8080/v1/meta

# Test MCP tools
python -m mcp_server.servers.memory_server --test
```

## Advanced Usage

### Custom Tools
```python
@self.server.list_tools()
async def list_tools():
    return [{
        "name": "custom_analysis",
        "description": "Perform custom analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "analysis_type": {"type": "string"}
            }
        }
    }]
```

### Workflow Automation
```python
workflow = {
    "name": "research_workflow",
    "steps": [
        {"agent": "research_agent", "action": "search"},
        {"agent": "analysis_agent", "action": "analyze"},
        {"agent": "report_agent", "action": "summarize"}
    ]
}

result = await mcp.call_tool("run_workflow", {
    "workflow": workflow,
    "input": "AI trends 2024"
})
```

This architecture provides a clean separation of concerns with PostgreSQL handling all relational data and Weaviate managing all vector/semantic operations.
