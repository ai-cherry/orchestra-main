# MCP Usage Guide for AI Coders

## Overview
This guide helps AI coding assistants (like Claude in Cursor, GitHub Copilot, etc.) effectively use the cherry_ai MCP servers to provide better coding assistance.

## Quick Setup

### 1. Environment Setup
Ensure these environment variables are set in your `.env` file:
```bash
# PostgreSQL (Relational Data)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cherry_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Weaviate (Vector Storage)
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your_key  # Optional

# API Configuration
API_URL=http://localhost:8080
API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd
```

### 2. Start MCP Servers
```bash
# In separate terminals (or use screen/tmux)
python mcp_server/servers/conductor_server.py
python mcp_server/servers/memory_server.py
python mcp_server/servers/tools_server.py
python mcp_server/servers/weaviate_direct_mcp_server.py
```

### 3. Configure Cursor
Add to your Cursor's `.mcp.json`:
```json
{
  "mcpServers": {
    "cherry_ai-conductor": {
      "command": "python",
      "args": ["/root/cherry_ai-main/mcp_server/servers/conductor_server.py"]
    },
    "cherry_ai-memory": {
      "command": "python",
      "args": ["/root/cherry_ai-main/mcp_server/servers/memory_server.py"]
    },
    "cherry_ai-tools": {
      "command": "python",
      "args": ["/root/cherry_ai-main/mcp_server/servers/tools_server.py"]
    }
  }
}
```

## Available MCP Tools

### Memory Server Tools

#### 1. **store_memory**
Store important context about the current coding session:
```
Use: When you learn something important about the code or user preferences
Example: "User prefers functional programming style"
```

#### 2. **search_memories**
Find relevant past context:
```
Use: When you need to recall previous decisions or patterns
Example: Search for "database schema decisions"
```

#### 3. **store_conversation**
Track important coding discussions:
```
Use: After significant design decisions or problem solutions
Example: Store the reasoning behind architectural choices
```

#### 4. **add_knowledge**
Add reusable coding patterns or solutions:
```
Use: When you discover a useful pattern or solution
Example: Add a optimized database query pattern
```

#### 5. **search_knowledge**
Find existing solutions and patterns:
```
Use: Before implementing something new
Example: Search for "authentication patterns"
```

### conductor Server Tools

#### 1. **list_agents**
See available AI agents:
```
Use: To understand what specialized agents are available
Example: Find agents for code review, testing, or documentation
```

#### 2. **run_agent**
Execute a specialized agent:
```
Use: When you need specialized help (e.g., security review)
Example: Run security_agent on sensitive code
```

#### 3. **run_workflow**
Execute multi-step workflows:
```
Use: For complex tasks requiring multiple agents
Example: Code review → Test generation → Documentation
```

## Best Practices for AI Coders

### 1. Context Building
```
At session start:
1. Search memories for relevant project context
2. Check knowledge base for established patterns
3. Review recent conversation history
```

### 2. Progressive Enhancement
```
During coding:
1. Store important decisions as memories
2. Add discovered patterns to knowledge base
3. Track significant conversations
```

### 3. Memory Categories
```
Use appropriate memory types:
- "decision" - Architectural/design decisions
- "preference" - User coding preferences
- "pattern" - Discovered code patterns
- "issue" - Problems and their solutions
- "context" - Project-specific information
```

### 4. Knowledge Organization
```
Categorize knowledge appropriately:
- "patterns" - Reusable code patterns
- "solutions" - Problem solutions
- "architecture" - System design patterns
- "optimization" - Performance improvements
- "security" - Security best practices
```

## Example Workflows

### 1. Starting a New Feature
```python
# 1. Search for related context
memories = search_memories(
    agent_id="code_agent",
    query="authentication implementation"
)

# 2. Check knowledge base
knowledge = search_knowledge(
    query="jwt authentication",
    category="security"
)

# 3. Store session context
store_memory(
    agent_id="code_agent",
    content="Working on JWT authentication feature",
    memory_type="context",
    importance=0.8
)
```

### 2. Solving a Complex Problem
```python
# 1. Document the problem
store_conversation(
    session_id=current_session,
    message="User needs to optimize database queries for large datasets",
    role="user"
)

# 2. Search for similar solutions
solutions = search_knowledge(
    query="database query optimization",
    category="optimization"
)

# 3. Store the solution
add_knowledge(
    title="PostgreSQL Query Optimization for Large Datasets",
    content="Use partial indexes, query planning, connection pooling...",
    category="optimization",
    tags=["postgresql", "performance", "database"]
)
```

### 3. Code Review Workflow
```python
# 1. Run specialized agent
result = run_agent(
    agent_name="code_review_agent",
    input_data={
        "code": file_content,
        "focus_areas": ["security", "performance"]
    }
)

# 2. Store review findings
store_memory(
    agent_id="code_review_agent",
    content=f"Review findings: {result['issues']}",
    memory_type="review",
    importance=0.9
)
```

## Database Architecture Reference

### PostgreSQL (Structured Data)
- Agent configurations
- Workflow definitions
- Session management
- Audit logs
- API keys

### Weaviate (Vector/Semantic Data)
- Agent memories with embeddings
- Conversation history
- Knowledge base
- Document storage

## Troubleshooting

### Common Issues

1. **MCP Connection Failed**
```bash
# Check if servers are running
ps aux | grep mcp_server

# Check logs
tail -f /tmp/mcp_*.log
```

2. **Memory Storage Failed**
```bash
# Verify database connections
python scripts/test_database_consolidation.py

# Check Weaviate health
curl http://localhost:8080/v1/meta
```

3. **Tool Not Found**
```bash
# List available tools
curl http://localhost:8002/tools  # conductor
curl http://localhost:8003/tools  # Memory
```

## Tips for Effective Usage

1. **Always search before implementing** - Check memories and knowledge base first
2. **Store important decisions** - Document why, not just what
3. **Use semantic search** - Natural language queries work best
4. **Batch related operations** - Store conversation and memory together
5. **Tag appropriately** - Use consistent tags for better retrieval

## Integration with Cursor

### Example Cursor Commands
```
// Search for previous implementation
@cherry_ai search_memories "user authentication"

// Store important context
@cherry_ai store_memory "User prefers PostgreSQL over MySQL"

// Add reusable pattern
@cherry_ai add_knowledge "Async request handler pattern"

// Run specialized agent
@cherry_ai run_agent "test_generator" "Create unit tests for auth module"
```

## Monitoring and Metrics

Check system health:
```python
# Via MCP tool (if available)
system_stats = get_system_stats()

# Direct check
health = health_check()
```

This guide should help AI coders effectively use the cherry_ai MCP servers to provide better, more contextual coding assistance. 