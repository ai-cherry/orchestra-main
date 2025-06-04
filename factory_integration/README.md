# Factory AI Integration - Phase 3.3: Context Management

This module implements the unified context management system for Factory AI integration, providing bidirectional synchronization between Factory AI and MCP memory stores with a high-performance multi-layer caching system.

## Overview

The context management system consists of two main components:

1. **UnifiedContextManager** (`context_manager.py`) - Manages context synchronization between Factory AI and MCP
2. **CacheManager** (`cache_manager.py`) - Implements a three-layer caching system for optimal performance

## Architecture

### Context Management
- **PostgreSQL** for metadata storage and versioning
- **Weaviate** for vector embeddings and semantic search
- **Bidirectional sync** between Factory AI and MCP contexts
- **Version history** with configurable retention
- **Conflict resolution** strategies for concurrent updates

### Caching Layers
1. **L1 Cache** - Ultra-fast in-memory LRU cache
2. **L2 Cache** - Distributed Redis cache for shared state
3. **L3 Cache** - Persistent PostgreSQL cache for long-term storage

## Installation

1. Install dependencies:
```bash
pip install asyncpg aioredis weaviate-client pydantic numpy
```

2. Set up PostgreSQL schema:
```bash
psql -U your_user -d your_database -f schema.sql
```

3. Configure Weaviate:
```python
import weaviate

client = weaviate.Client("http://localhost:8080")
client.schema.create_class({
    "class": "FactoryContext",
    "vectorizer": "none",
    "properties": [
        {"name": "contextId", "dataType": ["string"]},
        {"name": "content", "dataType": ["text"]},
        {"name": "metadata", "dataType": ["object"]},
        {"name": "timestamp", "dataType": ["date"]}
    ]
})
```

## Configuration

Edit `config/context.yaml` to configure:
- Database connections
- Cache settings
- Sync intervals
- Performance targets

## Usage

### Basic Context Management

```python
import asyncio
import asyncpg
from weaviate import Client
from factory_integration.context_manager import UnifiedContextManager
from factory_integration.cache_manager import create_cache_manager

async def main():
    # Set up database pool
    db_pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database="cherry_ai",
        user="your_user",
        password="your_password"
    )
    
    # Set up Weaviate client
    weaviate_client = Client("http://localhost:8080")
    
    # Create cache manager
    cache_config = {
        "l1": {"max_size": 1000, "ttl": 300},
        "l2": {"redis_url": "redis://localhost:6379", "ttl": 3600},
        "l3": {"db_pool": db_pool, "cleanup_interval": 86400}
    }
    cache_manager = await create_cache_manager(cache_config)
    
    # Create context manager
    async with UnifiedContextManager(
        db_pool=db_pool,
        weaviate_client=weaviate_client,
        cache_manager=cache_manager
    ) as context_manager:
        
        # Store context
        await context_manager.store_context(
            context_id="ctx_123",
            data={"user": "john", "action": "query"},
            source="factory"
        )
        
        # Retrieve context
        context = await context_manager.get_context("ctx_123")
        print(f"Context: {context}")
        
        # Search similar contexts
        embeddings = [0.1] * 1536  # Your embeddings here
        similar = await context_manager.search_similar_contexts(
            query_embeddings=embeddings,
            limit=5,
            threshold=0.8
        )
        
        # Get metrics
        metrics = await context_manager.get_metrics()
        print(f"Cache hit rate: {metrics['cache']['hit_rate']}%")
    
    # Cleanup
    await cache_manager.stop()
    await db_pool.close()

asyncio.run(main())
```

### Advanced Features

#### Context Merging
```python
# Merge multiple contexts
merged_id = await context_manager.merge_contexts(
    context_ids=["ctx_1", "ctx_2", "ctx_3"],
    merge_strategy="union"  # or "latest", "intersection"
)
```

#### Bidirectional Sync
```python
# Sync from Factory AI to MCP
factory_context = {"id": "factory_123", "data": {...}}
await context_manager.sync_with_factory(factory_context)

# Sync from MCP to Factory AI
factory_format = await context_manager.sync_to_factory("mcp_123")
```

#### Cache Warming
```python
# Pre-populate cache with frequently accessed keys
await cache_manager.warm_cache(["ctx_hot_1", "ctx_hot_2"])
```

## Performance Targets

- **Cache Hit Rate**: 85% (monitored and reported)
- **Sync Latency**: <100ms
- **Context Size Limit**: 10MB per context
- **Version Retention**: 100 versions per context

## Testing

Run the test suite:
```bash
pytest factory_integration/tests/ -v --cov=factory_integration --cov-report=html
```

Test coverage targets:
- Unit tests: 80% minimum
- Integration tests: Cover all database operations
- Performance tests: Validate cache hit rates and latency

## Monitoring

The system provides comprehensive metrics:

```python
metrics = await context_manager.get_metrics()
# Returns:
# {
#     "contexts": {
#         "total": 1000,
#         "versions": 5000,
#         "avg_versions_per_context": 5.0
#     },
#     "cache": {
#         "overall": {"hit_rate": 87.5, ...},
#         "l1": {"size": 800, "hit_rate": 65.0, ...},
#         "l2": {"hit_rate": 20.0, ...},
#         "l3": {"hit_rate": 2.5, ...}
#     },
#     "sync": {
#         "interval": 5,
#         "running": true
#     }
# }
```

## Database Schema

The system uses three main tables:
- `factory_context_metadata` - Context metadata and current version
- `factory_context_versions` - Version history
- `factory_cache_entries` - L3 cache storage

See `schema.sql` for complete schema definition.

## Error Handling

The system implements comprehensive error handling:
- Connection failures are logged and retried
- Cache misses fall through to next layer
- Sync errors don't block operations
- Size limits are enforced with clear errors

## Next Steps

After Phase 3.3 is complete:
1. Phase 3.4: API Gateway Implementation
2. Phase 3.5: Workflow Integration
3. Phase 4: Quality Review

## Contributing

When contributing to this module:
1. Follow PEP 8 and use Black for formatting
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation
5. Ensure 85% cache hit rate is maintained

## License

This module is part of the Cherry AI system and follows the same license terms.