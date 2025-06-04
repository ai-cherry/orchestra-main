# MCP Quick Reference Card

## 🚨 Database Rules
- ✅ **USE**: PostgreSQL + Weaviate ONLY
- ❌ **IGNORE**: MongoDB, Redis, DragonflyDB references

## 🎯 Essential MCP Commands

### Before Coding
```python
# 1. Search existing knowledge
search_memories(agent_id="code_agent", query="feature_name")
search_knowledge(query="pattern_type", category="patterns")

# 2. Start session
session = create_session(user_id="dev", agent_id="code_agent")
```

### During Coding
```python
# Save decisions
store_memory(
    agent_id="code_agent",
    content="Decision: Use WebSockets for real-time",
    memory_type="decision",
    importance=0.8
)

# Track conversations
store_conversation(
    session_id=session_id,
    message="User wants feature X",
    role="user"
)
```

### After Coding
```python
# Save patterns
add_knowledge(
    title="WebSocket Implementation",
    content="Pattern details...",
    category="patterns",
    tags=["websocket", "realtime"]
)
```

## 📁 Memory Types
- `decision` - Architecture choices
- `context` - Current task info
- `preference` - User preferences
- `pattern` - Code patterns
- `issue` - Problems/solutions
- `review` - Code reviews

## 📚 Knowledge Categories
- `patterns` - Reusable code
- `optimization` - Performance
- `security` - Best practices
- `architecture` - Design patterns
- `integration` - 3rd party APIs

## 🔧 Database Access
```python
# ALWAYS use this:
from shared.database import UnifiedDatabase
db = UnifiedDatabase()

# NEVER use these:
# import redis ❌
# import pymongo ❌
# import dragonfly ❌
```

## 💡 Best Practices
1. **Search before implementing**
2. **Store WHY not just WHAT**
3. **Use consistent tags**
4. **Document patterns for reuse**
5. **Check health: `db.health_check()`**

## 🚀 Environment Variables
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cherry_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=xxx

WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
```

## ⚡ Common Workflows

### New Feature
```python
memories = search_memories(query="similar_feature")
knowledge = search_knowledge(query="pattern")
store_memory(content="Starting feature X")
```

### Bug Fix
```python
past_issues = search_memories(query="error_type", memory_type="issue")
# After fix:
add_knowledge(title="Fix for X", category="solutions")
```

### Code Review
```python
result = run_agent("code_review_agent", {"code": content})
store_memory(content=f"Review: {result}", memory_type="review")
```

**Remember**: MCP = Memory + Context + Patterns = Smarter Coding! 🧠 