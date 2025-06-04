# AI Coding Agent Guide for cherry_ai

## Overview
This guide helps AI coding agents understand and work with the cherry_ai multi-agent system, which uses PostgreSQL for relational data and Weaviate for vector/semantic operations.

## System Architecture

### Core Components
1. **Agent System** (`agent/`)
   - FastAPI-based REST API
   - Agent templates and configurations
   - Natural language processing
   - Workflow coordination

2. **MCP Servers** (`mcp_server/`)
   - conductor: Agent coordination
   - Memory: PostgreSQL/Weaviate operations
   - Tools: Tool discovery and execution

3. **Database Layer** (`shared/database/`)
   - PostgreSQL: Structured data, configurations, sessions
   - Weaviate: Vector storage, semantic search, memories

## Database Architecture

### PostgreSQL (Relational Data)
```sql
-- Main tables in cherry_ai schema:
- agents: Agent configurations and metadata
- workflows: Workflow definitions and status
- sessions: User sessions (replaces Redis)
- audit_logs: System events and tracking
- api_keys: Authentication and permissions
- memory_snapshots: References to Weaviate vectors
```

### Weaviate (Vector & Semantic Data)
```python
# Collections:
- AgentMemory: Agent memories with embeddings
- Knowledge: Knowledge base for RAG
- Conversation: Conversation history
- Document: Document storage for semantic search
```

## Development Guidelines

### 1. Database Operations
```python
# Use the unified database interface
from shared.database import UnifiedDatabase

db = UnifiedDatabase()

# Create agent with memory
agent = db.create_agent(
    name="research_agent",
    description="Research specialist",
    capabilities={"web_search": True},
    initial_memory="I am a research agent"
)

# Store interaction
db.store_agent_interaction(
    agent_id=agent["id"],
    user_input="Find information about AI",
    agent_response="I'll search for AI information",
    session_id=session_id
)

# Search memories
results = db.search_agent_context(
    agent_id=agent["id"],
    query="previous research"
)
```

### 2. MCP Server Integration
```python
# Memory operations via MCP
tools = [
    "store_memory",        # Store in Weaviate
    "search_memories",     # Semantic search
    "get_recent_memories", # Time-based retrieval
    "store_conversation",  # Conversation tracking
    "add_knowledge",       # Knowledge base
    "search_knowledge"     # RAG operations
]
```

### 3. Agent Implementation
```python
# Agent template structure
class AgentTemplate:
    name: str
    capabilities: Dict[str, Any]
    model_config: Dict[str, Any]
    
    async def process(self, input_data):
        # 1. Retrieve context from Weaviate
        context = await self.get_relevant_context(input_data)
        
        # 2. Process with LLM
        response = await self.llm_process(input_data, context)
        
        # 3. Store interaction
        await self.store_interaction(input_data, response)
        
        return response
```

## Testing

### Database Testing
```bash
# Test PostgreSQL connection
python shared/database/postgresql_client.py

# Test Weaviate connection  
python shared/database/weaviate_client.py

# Test unified interface
python -c "from shared.database import UnifiedDatabase; db = UnifiedDatabase(); print(db.health_check())"
```

### Schema Verification
```bash
# Setup schema
python scripts/setup_postgres_schema.py

# Verify schema
python scripts/setup_postgres_schema.py --verify-only
```

## Common Patterns

### 1. Session Management
```python
# Create session (PostgreSQL)
session = db.create_session(
    session_id=session_id,
    user_id=user_id,
    agent_id=agent_id,
    ttl_hours=24
)

# Get session with history
session_data = db.get_session_with_history(session_id)
```

### 2. Memory Retrieval
```python
# Semantic search (Weaviate)
memories = db.weaviate.search_memories(
    agent_id=agent_id,
    query="previous conversations about AI",
    limit=10
)

# Recent memories
recent = db.weaviate.get_recent_memories(
    agent_id=agent_id,
    limit=20
)
```

### 3. Knowledge Management
```python
# Add to knowledge base
knowledge_id = db.add_to_knowledge_base(
    title="AI Best Practices",
    content="...",
    category="technology",
    tags=["AI", "best-practices"]
)

# Search knowledge
results = db.search_knowledge(
    query="best practices",
    category="technology"
)
```

## Environment Setup

### Required Environment Variables
```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cherry_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=optional_api_key

# API
API_URL=http://localhost:8080
API_KEY=your_api_key
```

## Best Practices

1. **Use PostgreSQL for**:
   - Configuration data
   - State management
   - Audit trails
   - Session data
   - Structured queries

2. **Use Weaviate for**:
   - Memory storage
   - Semantic search
   - Context retrieval
   - Document embeddings
   - Conversation history

3. **Performance Tips**:
   - Use connection pooling (built-in)
   - Batch operations when possible
   - Cache frequently accessed data
   - Index PostgreSQL queries properly

4. **Error Handling**:
   - Always check database health on startup
   - Handle connection failures gracefully
   - Log all database errors
   - Implement retry logic for transient failures

## Troubleshooting

### Common Issues

1. **PostgreSQL Connection Failed**
   - Check credentials in .env
   - Ensure PostgreSQL is running
   - Verify network connectivity

2. **Weaviate Not Responding**
   - Check Weaviate service status
   - Verify API key if secured
   - Check collection schemas exist

3. **Schema Issues**
   - Run schema setup script
   - Check for migration errors
   - Verify table permissions

### Debug Commands
```bash
# Check PostgreSQL
psql -U postgres -d cherry_ai -c "\dt cherry_ai.*"

# Check Weaviate
curl http://localhost:8080/v1/meta

# Test connections
python -m shared.database.postgresql_client
python -m shared.database.weaviate_client
``` 