# MCP Instructions for AI Coding Agents

## 🚨 IMPORTANT DATABASE ARCHITECTURE

**ONLY USE THESE DATABASES:**
- **PostgreSQL** - For all structured/relational data (agents, workflows, sessions, configurations)
- **Weaviate** - For all vector/semantic data (memories, conversations, knowledge base)

**DO NOT USE:**
- ❌ MongoDB
- ❌ Redis
- ❌ DragonflyDB
- ❌ Any other database systems

⚠️ **Note**: Many files in the codebase still reference these deprecated databases. Ignore these references and use only PostgreSQL + Weaviate.

## 📋 MCP Overview

MCP (Model Context Protocol) provides memory, context, and tools for AI agents. Think of it as:
- 🧠 **Long-term memory** for the AI system
- 🔍 **Semantic search** capabilities
- 🤝 **Agent coordination** system
- 📚 **Knowledge management** platform

## 🛠️ Available MCP Servers

### 1. **Memory Server** (`memory_server.py`)
Manages memories, conversations, and knowledge using PostgreSQL + Weaviate.

### 2. **conductor Server** (`conductor_server.py`)
Coordinates multiple AI agents and workflows.

### 3. **Tools Server** (`tools_server.py`)
Provides utility functions and integrations.

### 4. **Weaviate Direct Server** (`weaviate_direct_mcp_server.py`)
Direct access to Weaviate for specialized vector operations.

## 🎯 Key MCP Tools for Planning & Coding

### Memory Management Tools

#### 1. `search_memories` - Find relevant context
```python
# Before implementing a feature, search for related context
search_memories(
    agent_id="code_agent",
    query="user authentication implementation patterns"
)
```

#### 2. `store_memory` - Save important decisions
```python
# After making an architectural decision
store_memory(
    agent_id="code_agent",
    content="Decided to use JWT tokens with refresh token rotation for auth",
    memory_type="decision",
    importance=0.9
)
```

#### 3. `search_knowledge` - Find reusable patterns
```python
# Before writing new code
search_knowledge(
    query="async error handling patterns",
    category="patterns"
)
```

#### 4. `add_knowledge` - Store discovered solutions
```python
# After solving a complex problem
add_knowledge(
    title="PostgreSQL Connection Pool Optimization",
    content="Use pgbouncer with transaction pooling mode...",
    category="optimization",
    tags=["postgresql", "performance", "connection-pooling"]
)
```

### Session & Conversation Tools

#### 5. `create_session` - Start new coding session
```python
# At the beginning of a task
create_session(
    user_id="developer_123",
    agent_id="code_agent",
    ttl_hours=8
)
```

#### 6. `store_conversation` - Track important discussions
```python
# After discussing requirements
store_conversation(
    session_id=current_session,
    agent_id="code_agent",
    message="User wants real-time updates using WebSockets",
    role="user"
)
```

## 📝 Coding Workflows with MCP

### Workflow 1: Starting a New Feature

```python
# 1. Create session
session = create_session(user_id="dev", agent_id="code_agent")

# 2. Search for existing patterns
memories = search_memories(
    agent_id="code_agent",
    query="payment integration"
)

# 3. Check knowledge base
knowledge = search_knowledge(
    query="stripe payment flow",
    category="integration"
)

# 4. Store initial context
store_memory(
    agent_id="code_agent",
    content="Starting Stripe payment integration for subscription model",
    memory_type="context",
    importance=0.8
)
```

### Workflow 2: Problem Solving

```python
# 1. Document the problem
store_conversation(
    session_id=session_id,
    agent_id="code_agent",
    message="Database queries are slow with large datasets",
    role="user"
)

# 2. Search for similar issues
past_solutions = search_memories(
    agent_id="code_agent",
    query="database performance optimization"
)

# 3. After finding solution, store it
add_knowledge(
    title="PostgreSQL Query Optimization",
    content="Solution: Add partial indexes, use EXPLAIN ANALYZE...",
    category="optimization",
    tags=["postgresql", "performance"]
)
```

### Workflow 3: Code Review & Learning

```python
# 1. Run code review
result = run_agent(
    agent_name="code_review_agent",
    input_data={"code": file_content}
)

# 2. Store review findings
store_memory(
    agent_id="code_review_agent",
    content=f"Security issue found: {result['issues'][0]}",
    memory_type="review",
    importance=0.95
)

# 3. Add to knowledge base if it's a pattern
if result['is_pattern']:
    add_knowledge(
        title="Security Best Practice: Input Validation",
        content=result['recommendation'],
        category="security"
    )
```

## 🏗️ Architecture Best Practices

### 1. Database Usage
```python
# ✅ CORRECT - Using UnifiedDatabase
from shared.database import UnifiedDatabase

db = UnifiedDatabase()
# This automatically uses PostgreSQL + Weaviate

# ❌ WRONG - Direct database access
import redis  # Don't use this
import pymongo  # Don't use this
```

### 2. Memory Categories
- **"decision"** - Architectural/design choices
- **"context"** - Current task information
- **"preference"** - User/coding preferences
- **"pattern"** - Reusable code patterns
- **"issue"** - Problems and solutions
- **"review"** - Code review findings

### 3. Knowledge Categories
- **"patterns"** - Code patterns and templates
- **"optimization"** - Performance improvements
- **"security"** - Security best practices
- **"architecture"** - System design patterns
- **"integration"** - Third-party integrations

## 🔍 Common MCP Queries

### Before Starting Any Task
```python
# 1. What do we know about this feature?
search_memories(agent_id="code_agent", query="[feature name]")

# 2. Any existing patterns?
search_knowledge(query="[feature type]", category="patterns")

# 3. Previous issues?
search_memories(agent_id="code_agent", query="[feature] issues", memory_type="issue")
```

### During Development
```python
# Store design decisions
store_memory(
    agent_id="code_agent",
    content="Using repository pattern for data access",
    memory_type="decision"
)

# Track user preferences
store_memory(
    agent_id="code_agent",
    content="User prefers explicit error messages over generic ones",
    memory_type="preference"
)
```

### After Completion
```python
# Document what was built
add_knowledge(
    title="Feature: Real-time Notifications",
    content="Implementation using WebSockets with reconnection logic...",
    category="patterns"
)

# Store lessons learned
store_memory(
    agent_id="code_agent",
    content="WebSocket reconnection requires exponential backoff",
    memory_type="pattern"
)
```

## ⚠️ Important Warnings

1. **Ignore Old Database References**
   - Many files mention MongoDB/Redis/DragonflyDB
   - These are outdated - use only PostgreSQL + Weaviate

2. **Use UnifiedDatabase Class**
   - Always use `shared.database.UnifiedDatabase`
   - Never directly connect to databases

3. **Check Database Health**
   ```python
   db = UnifiedDatabase()
   health = db.health_check()
   # Ensure both PostgreSQL and Weaviate are healthy
   ```

4. **Environment Variables**
   ```bash
   # Required for MCP to work
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=cherry_ai
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   
   WEAVIATE_HOST=localhost
   WEAVIATE_PORT=8080
   WEAVIATE_API_KEY=your_key  # Optional
   ```

## 📊 Monitoring MCP Usage

```python
# Check what's in memory
recent = get_recent_memories(agent_id="code_agent", limit=10)

# Review conversation history
history = get_conversation_history(session_id=current_session)

# Audit knowledge base
all_knowledge = search_knowledge(query="*", limit=100)
```

## 🚀 Quick Start Checklist

- [ ] Verify PostgreSQL and Weaviate are running
- [ ] Check MCP servers are healthy (`check_mcp_servers.sh`)
- [ ] Create a session before starting work
- [ ] Search memories/knowledge before implementing
- [ ] Store decisions and patterns as you work
- [ ] Add reusable solutions to knowledge base
- [ ] Use appropriate memory/knowledge categories
- [ ] Ignore any MongoDB/Redis/DragonflyDB references
- [ ] Always use UnifiedDatabase class

## 💡 Pro Tips

1. **Search First, Code Second** - Always check memories and knowledge before implementing
2. **Document Why, Not Just What** - Store the reasoning behind decisions
3. **Tag Appropriately** - Use consistent tags for better retrieval
4. **Review and Learn** - Regularly review stored memories to find patterns
5. **Clean Up** - Remove outdated memories/knowledge periodically

Remember: MCP makes you a smarter coder by building on past experiences. Use it actively throughout your development process! 