# Phase 3.3: Context Management Implementation Tasks

## Overview
With the MCP adapters complete, we now need to implement the unified context management system that will synchronize state between Factory AI and our existing infrastructure.

## Task 3.3.1: Unified Context Manager

### Requirements
Create a comprehensive context management system that bridges Factory AI context with MCP memory stores.

### Implementation Location
`factory_integration/context_manager.py`

### Key Features

1. **Context Synchronization**
   ```python
   class UnifiedContextManager:
       """Manages context for both Roo and Factory AI systems."""
       
       def __init__(self):
           self.factory_context = FactoryContext()
           self.mcp_memory = MemoryStore()
           self.sync_interval = 5  # seconds
           self.version_history = []
   ```

2. **PostgreSQL Integration**
   - Store context metadata
   - Version tracking
   - Audit trail
   - Query optimization with indexes

3. **Weaviate Vector Store**
   - Semantic context search
   - Code embeddings (1536 dimensions)
   - Context similarity matching
   - Automatic pruning of old contexts

4. **Bidirectional Sync**
   - MCP → Factory AI context updates
   - Factory AI → MCP memory updates
   - Conflict resolution strategies
   - Atomic operations

## Task 3.3.2: Multi-Layer Caching System

### Requirements
Implement a high-performance caching layer to achieve the 85% cache hit rate target.

### Implementation Location
`factory_integration/cache_manager.py`

### Cache Layers

1. **L1: In-Memory Cache**
   ```python
   class L1Cache:
       """Ultra-fast in-memory cache with LRU eviction."""
       def __init__(self, max_size: int = 1000):
           self.cache = OrderedDict()
           self.max_size = max_size
           self.hits = 0
           self.misses = 0
   ```

2. **L2: Redis Cache**
   ```python
   class L2Cache:
       """Distributed Redis cache for shared state."""
       def __init__(self, redis_url: str):
           self.redis = aioredis.from_url(redis_url)
           self.ttl = 3600  # 1 hour default
   ```

3. **L3: PostgreSQL Cache**
   ```python
   class L3Cache:
       """Persistent cache in PostgreSQL for long-term storage."""
       def __init__(self, db_pool: asyncpg.Pool):
           self.db_pool = db_pool
   ```

### Cache Strategy
- **Write-through**: Updates go to all layers
- **Read-through**: Check L1 → L2 → L3 → Source
- **Cache warming**: Preload frequently accessed data
- **Invalidation**: Smart invalidation based on context changes

## Implementation Details

### 1. Context Manager Schema (PostgreSQL)
```sql
-- Context metadata table
CREATE TABLE factory_context_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(255) UNIQUE NOT NULL,
    parent_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    source VARCHAR(50) NOT NULL, -- 'factory' or 'mcp'
    data JSONB NOT NULL,
    embeddings VECTOR(1536), -- For Weaviate sync
    INDEX idx_context_parent (parent_id),
    INDEX idx_context_updated (updated_at),
    INDEX idx_context_source (source)
);

-- Context version history
CREATE TABLE factory_context_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_id VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL,
    data JSONB NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_type VARCHAR(50), -- 'create', 'update', 'merge'
    UNIQUE(context_id, version),
    FOREIGN KEY (context_id) REFERENCES factory_context_metadata(context_id)
);

-- Cache entries table
CREATE TABLE factory_cache_entries (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cache_expires (expires_at),
    INDEX idx_cache_accessed (last_accessed)
);
```

### 2. Weaviate Schema
```python
# Weaviate class for context embeddings
context_class = {
    "class": "FactoryContext",
    "description": "Factory AI context with embeddings",
    "vectorizer": "none",  # We provide our own embeddings
    "properties": [
        {
            "name": "contextId",
            "dataType": ["string"],
            "description": "Unique context identifier"
        },
        {
            "name": "content",
            "dataType": ["text"],
            "description": "Context content for search"
        },
        {
            "name": "metadata",
            "dataType": ["object"],
            "description": "Context metadata"
        },
        {
            "name": "timestamp",
            "dataType": ["date"],
            "description": "Context creation time"
        }
    ]
}
```

### 3. Performance Optimizations

1. **Connection Pooling**
   - PostgreSQL: asyncpg pool (min=10, max=50)
   - Redis: connection pool with health checks
   - Weaviate: batch operations for efficiency

2. **Async Operations**
   - All I/O operations are async
   - Concurrent context updates
   - Background sync tasks

3. **Monitoring**
   - Cache hit/miss rates
   - Sync latency metrics
   - Context size tracking
   - Memory usage monitoring

## Testing Requirements

1. **Unit Tests**
   - Context CRUD operations
   - Cache layer functionality
   - Sync mechanisms

2. **Integration Tests**
   - PostgreSQL integration
   - Redis caching
   - Weaviate vector operations

3. **Performance Tests**
   - Cache hit rate validation (target: 85%)
   - Sync latency (target: <100ms)
   - Concurrent operation handling

## Success Criteria
- ✓ Unified context manager operational
- ✓ All three cache layers implemented
- ✓ PostgreSQL schema deployed
- ✓ Weaviate integration working
- ✓ 85% cache hit rate achieved
- ✓ Bidirectional sync functional
- ✓ Version history maintained

## Configuration
```yaml
# factory_integration/config/context.yaml
context_management:
  sync_interval: 5  # seconds
  max_context_size: 10485760  # 10MB
  version_retention: 100  # Keep last 100 versions
  
cache:
  l1:
    max_size: 1000
    ttl: 300  # 5 minutes
  l2:
    redis_url: "redis://localhost:6379/0"
    ttl: 3600  # 1 hour
  l3:
    cleanup_interval: 86400  # Daily cleanup
    
postgresql:
  host: localhost
  port: 5432
  database: orchestra
  pool_size: 20
  
weaviate:
  url: "http://localhost:8080"
  batch_size: 100
  timeout: 30
```

## Next Steps
After completing context management:
1. Phase 3.4: API Gateway Implementation
2. Phase 3.5: Workflow Integration
3. Phase 4: Quality Review