# Database Consolidation Plan - Orchestra AI

## Current State Analysis

The codebase currently uses multiple database systems:
- **MongoDB** - Persistent memory, agent data, workflow history
- **DragonflyDB** - Redis-compatible cache layer
- **Weaviate** - Vector search and embeddings
- **PostgreSQL** - Infrastructure data (mentioned but underutilized)
- **Redis** - Caching (some references)

## Target State: PostgreSQL + Weaviate

### 1. PostgreSQL (Relational Data)
**Purpose**: All structured, relational data
- Agent configurations and metadata
- Workflow definitions and history
- Audit logs and system events
- User management and authentication
- Session management
- API keys and access control
- System configuration

**Features to leverage**:
- JSONB columns for flexible schema
- pgvector extension for embeddings (backup to Weaviate)
- Full-text search capabilities
- ACID compliance for critical data
- Built-in caching with proper indexes

### 2. Weaviate (Vector & Semantic Data)
**Purpose**: All vector operations and semantic search
- Agent memory embeddings
- Document embeddings
- Semantic search operations
- Context retrieval
- Knowledge base storage
- Conversation history vectors

**Features to leverage**:
- Native vector search
- Hybrid search (vector + keyword)
- Automatic schema inference
- GraphQL API
- Real-time updates

## Migration Strategy

### Phase 1: Database Mapping
Map current database usage to new structure:

#### MongoDB → PostgreSQL
- `agents` collection → `agents` table
- `workflows` collection → `workflows` table  
- `audit_logs` collection → `audit_logs` table
- `memory_snapshots` collection → `memory_snapshots` table with JSONB
- `sessions` collection → `sessions` table

#### DragonflyDB/Redis → PostgreSQL + Weaviate
- Short-term cache → PostgreSQL with TTL columns or in-memory caching
- Session data → PostgreSQL `sessions` table
- Temporary data → Application-level caching (Python functools.lru_cache)

### Phase 2: Schema Design

```sql
-- PostgreSQL Schema
CREATE SCHEMA IF NOT EXISTS orchestra;

-- Agents table
CREATE TABLE orchestra.agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    capabilities JSONB,
    autonomy_level INTEGER,
    model_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflows table
CREATE TABLE orchestra.workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    definition JSONB NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory snapshots table
CREATE TABLE orchestra.memory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES orchestra.agents(id),
    snapshot_data JSONB,
    vector_ids TEXT[], -- References to Weaviate vectors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE orchestra.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    actor VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (replacing Redis session storage)
CREATE TABLE orchestra.sessions (
    id VARCHAR(255) PRIMARY KEY,
    data JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_agents_name ON orchestra.agents(name);
CREATE INDEX idx_workflows_status ON orchestra.workflows(status);
CREATE INDEX idx_audit_logs_event_type ON orchestra.audit_logs(event_type);
CREATE INDEX idx_sessions_expires ON orchestra.sessions(expires_at);
```

### Phase 3: Weaviate Schema

```python
# Weaviate Collections
MEMORY_COLLECTION = {
    "class": "AgentMemory",
    "properties": [
        {"name": "agent_id", "dataType": ["text"]},
        {"name": "content", "dataType": ["text"]},
        {"name": "context", "dataType": ["text"]},
        {"name": "timestamp", "dataType": ["date"]},
        {"name": "memory_type", "dataType": ["text"]},
        {"name": "metadata", "dataType": ["object"]}
    ]
}

KNOWLEDGE_COLLECTION = {
    "class": "Knowledge",
    "properties": [
        {"name": "title", "dataType": ["text"]},
        {"name": "content", "dataType": ["text"]},
        {"name": "source", "dataType": ["text"]},
        {"name": "tags", "dataType": ["text[]"]},
        {"name": "created_at", "dataType": ["date"]}
    ]
}
```

## Implementation Steps

### 1. Update Environment Configuration
- Remove MongoDB, DragonflyDB environment variables
- Add PostgreSQL connection settings
- Ensure Weaviate configuration is complete

### 2. Create Database Abstraction Layer
- Implement `shared/database/postgresql_client.py`
- Implement `shared/database/weaviate_client.py`
- Create unified interface for both databases

### 3. Update MCP Servers
- Consolidate memory_server.py to use PostgreSQL + Weaviate
- Remove dragonfly_server.py
- Update orchestrator_server.py to use new database layer

### 4. Migration Scripts
- Create data migration scripts from MongoDB to PostgreSQL
- Create vector migration from any existing vector stores to Weaviate

### 5. Update Application Code
- Replace MongoDB queries with PostgreSQL
- Replace cache operations with appropriate PostgreSQL or app-level caching
- Ensure all vector operations use Weaviate

## Benefits of Consolidation

1. **Simplified Infrastructure**: Only 2 databases to manage
2. **Cost Efficiency**: Fewer services to run and maintain
3. **Better Performance**: PostgreSQL can handle caching needs with proper indexing
4. **Consistency**: Clear separation between relational and vector data
5. **GCP-Ready**: Both PostgreSQL (Cloud SQL) and Weaviate can run on GCP

## Rollback Plan

1. Keep MongoDB data exports before migration
2. Implement feature flags for gradual rollout
3. Run parallel systems during transition
4. Maintain backward compatibility in APIs

## Timeline

- Week 1: Database schema design and abstraction layer
- Week 2: MCP server updates and migration scripts
- Week 3: Application code updates
- Week 4: Testing and validation
- Week 5: Production migration

## Success Criteria

1. All data successfully migrated
2. No performance degradation
3. Simplified deployment process
4. Reduced operational complexity
5. All tests passing with new database layer 