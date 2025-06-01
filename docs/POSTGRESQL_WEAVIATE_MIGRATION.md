# PostgreSQL & Weaviate Migration Guide

## Overview

This document outlines the complete migration from multiple data stores (Redis, MongoDB, DragonflyDB, Firestore) and cloud providers (GCP, AWS) to a simplified, high-performance stack using only PostgreSQL and Weaviate on Vultr.

## Architecture Changes

### Before (Complex Multi-Store)
```
┌─────────────────────────────────────────────────────────┐
│                   Orchestra AI                           │
├─────────────────────────────────────────────────────────┤
│  Cache Layer:     Redis/DragonflyDB                     │
│  Session Store:   Redis                                 │
│  Document Store:  MongoDB/Firestore                     │
│  Vector Store:    Weaviate                              │
│  Relational:      PostgreSQL                            │
│  Cloud:           GCP/AWS                               │
└─────────────────────────────────────────────────────────┘
```

### After (Simplified Two-Store)
```
┌─────────────────────────────────────────────────────────┐
│                   Orchestra AI                           │
├─────────────────────────────────────────────────────────┤
│  All Data:        PostgreSQL (with JSONB)               │
│  Vector Search:   Weaviate                              │
│  Infrastructure:  Vultr (single server)                 │
└─────────────────────────────────────────────────────────┘
```

## PostgreSQL Replacements

### 1. Cache Replacement
**File**: `shared/cache/postgresql_cache.py`

PostgreSQL-based caching with:
- JSONB storage for flexible data
- Automatic TTL expiration
- High-performance indexes
- Connection pooling
- Background cleanup tasks

**Usage Example**:
```python
from shared.cache.postgresql_cache import get_cache

# Get cache instance
cache = await get_cache("default", dsn=postgresql_dsn)

# Set value with TTL
await cache.set("key", {"data": "value"}, ttl=3600)

# Get value
value = await cache.get("key")

# Delete value
await cache.delete("key")
```

### 2. Session Storage Replacement
**File**: `shared/sessions/postgresql_sessions.py`

PostgreSQL-based sessions with:
- UUID-based session IDs
- User association
- Automatic expiration
- IP and user agent tracking
- Soft delete with cleanup

**Usage Example**:
```python
from shared.sessions.postgresql_sessions import get_session_store

# Get session store
store = await get_session_store(dsn=postgresql_dsn)

# Create session
session_id = await store.create_session(
    user_id="user123",
    data={"theme": "dark"},
    ttl=86400
)

# Get session
session = await store.get_session(session_id)

# Update session
await store.update_session(session_id, {"theme": "light"})
```

### 3. Document Storage (MongoDB Replacement)
PostgreSQL JSONB can replace MongoDB for document storage:

```sql
-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection TEXT NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_documents_collection ON documents(collection);
CREATE INDEX idx_documents_data_gin ON documents USING GIN(data);
CREATE INDEX idx_documents_metadata_gin ON documents USING GIN(metadata);
```

### 4. Queue/Task Management
PostgreSQL can handle task queues with SKIP LOCKED:

```sql
-- Task queue table
CREATE TABLE task_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error TEXT
);

-- Get next task (with row locking)
SELECT * FROM task_queue
WHERE status = 'pending'
ORDER BY priority DESC, created_at ASC
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

## Weaviate Usage

### Vector Storage
Weaviate handles all vector/embedding operations:

```python
import weaviate

# Initialize client
client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={"X-Weaviate-Api-Key": weaviate_api_key}
)

# Create schema
schema = {
    "class": "Memory",
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "metadata", "dataType": ["text"]},
        {"name": "timestamp", "dataType": ["date"]},
    ]
}
client.schema.create_class(schema)

# Add vector
client.data_object.create(
    data_object={
        "content": "Important memory content",
        "metadata": json.dumps({"user_id": "123"}),
        "timestamp": datetime.utcnow().isoformat()
    },
    class_name="Memory",
    vector=embedding_vector
)

# Search vectors
result = client.query.get("Memory", ["content", "metadata"]).with_near_vector({
    "vector": query_vector,
    "certainty": 0.7
}).with_limit(10).do()
```

## Migration Steps

### 1. Run Infrastructure Purge Script
```bash
cd /root/orchestra-main
python scripts/purge_unwanted_infrastructure.py
```

### 2. Update Environment Variables
Remove all Redis/MongoDB/GCP variables from `.env`:
```bash
# Remove these
REDIS_HOST=...
REDIS_PORT=...
MONGODB_URI=...
GCP_PROJECT_ID=...
DRAGONFLY_URI=...

# Keep only these
POSTGRES_DSN=postgresql://user:pass@localhost/orchestra
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=...
```

### 3. Update Database Schema
Run PostgreSQL migrations:
```sql
-- Cache table
CREATE SCHEMA IF NOT EXISTS cache;
CREATE TABLE cache.default_cache (...);

-- Sessions table  
CREATE SCHEMA IF NOT EXISTS sessions;
CREATE TABLE sessions.sessions (...);

-- Documents table
CREATE TABLE documents (...);

-- Task queue
CREATE TABLE task_queue (...);
```

### 4. Update Application Code
Replace all Redis/MongoDB imports:

```python
# OLD
import redis
from pymongo import MongoClient

# NEW
from shared.cache.postgresql_cache import get_cache
from shared.sessions.postgresql_sessions import get_session_store
```

### 5. Test Everything
```bash
# Run tests
python -m pytest tests/

# Check services
python scripts/check_services.py
```

## Performance Optimizations

### PostgreSQL Tuning
Add to `postgresql.conf`:
```ini
# Memory
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

# Connections
max_connections = 200
max_prepared_transactions = 100

# Performance
random_page_cost = 1.1
effective_io_concurrency = 200
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# Write performance
checkpoint_completion_target = 0.9
wal_buffers = 16MB
max_wal_size = 4GB
```

### Connection Pooling
All components use connection pooling:
```python
# PostgreSQL pool
pool = await asyncpg.create_pool(
    dsn,
    min_size=5,
    max_size=20,
    command_timeout=60
)
```

## Monitoring

### PostgreSQL Monitoring Queries
```sql
-- Cache hit ratio
SELECT 
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;

-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Weaviate Monitoring
```python
# Check Weaviate health
health = client.is_ready()

# Get node status
nodes = client.nodes.get()
```

## Troubleshooting

### Common Issues

1. **High memory usage**
   - Adjust PostgreSQL shared_buffers
   - Check for missing indexes
   - Review connection pool sizes

2. **Slow queries**
   - Run EXPLAIN ANALYZE on slow queries
   - Add appropriate indexes
   - Consider partitioning large tables

3. **Connection exhaustion**
   - Increase max_connections in PostgreSQL
   - Review connection pool settings
   - Check for connection leaks

## Benefits of This Architecture

1. **Simplicity**: Only two data stores to manage
2. **Performance**: PostgreSQL JSONB is extremely fast with proper indexes
3. **Reliability**: PostgreSQL's ACID guarantees
4. **Cost**: Single Vultr server, no cloud provider fees
5. **Maintenance**: Fewer moving parts, easier backups
6. **Flexibility**: JSONB supports any document structure

## Conclusion

This migration simplifies the Orchestra AI infrastructure while maintaining high performance. PostgreSQL with JSONB can handle caching, sessions, documents, and queues effectively, while Weaviate provides specialized vector search capabilities.