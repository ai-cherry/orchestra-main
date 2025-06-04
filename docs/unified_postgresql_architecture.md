# Unified PostgreSQL Architecture Documentation

## Overview

The unified PostgreSQL architecture eliminates all duplication in database connections, caching, and session management by providing a single, optimized interface for all database operations. This architecture prioritizes performance, stability, and simplicity.

## Architecture Components

### 1. Connection Manager (`shared/database/connection_manager.py`)

The foundation of the unified architecture - a singleton connection manager that provides:

- **Single Connection Pool**: One optimized asyncpg pool shared by all components
- **Performance Tuning**: PostgreSQL server settings optimized for performance
- **Health Monitoring**: Built-in health checks and pool statistics
- **Automatic Recovery**: Connection retry logic with exponential backoff

```python
from shared.database.connection_manager import get_connection_manager

# Get the singleton instance
manager = await get_connection_manager()

# Execute queries
result = await manager.fetch("SELECT * FROM agents WHERE status = $1", "active")

# Get pool statistics
stats = await manager.get_pool_stats()
print(f"Active connections: {stats['used_connections']}/{stats['total_connections']}")
```

### 2. Unified PostgreSQL Client (`shared/database/unified_postgresql.py`)

Combines all PostgreSQL functionality into a single client:

- **Cache Operations**: High-performance caching with TTL and tags
- **Session Management**: User and agent sessions with automatic expiration
- **Agent CRUD**: Complete agent lifecycle management
- **Workflow Management**: Workflow creation, updates, and execution tracking
- **Audit Logging**: Comprehensive audit trail for all operations
- **Memory Snapshots**: Agent memory state persistence

```python
from shared.database.unified_postgresql import get_unified_postgresql

# Get the singleton instance
client = await get_unified_postgresql()

# Cache operations
await client.cache_set("key", {"data": "value"}, ttl=3600, tags=["api", "user"])
value = await client.cache_get("key")

# Session management
session_id = await client.session_create(
    user_id="user123",
    agent_id="agent456",
    data={"context": "conversation"},
    ttl=86400
)

# Agent operations
agent_id = await client.agent_create(
    name="Assistant",
    type="chat",
    config={"model": "gpt-4"},
    capabilities=["chat", "code"],
    status="active"
)
```

### 3. Unified Database Interface (`shared/database/unified_db_v2.py`)

High-level interface combining PostgreSQL and Weaviate:

- **Automatic Caching**: Transparent caching layer for all operations
- **Parallel Search**: Search across multiple data types simultaneously
- **Performance Metrics**: Built-in performance tracking
- **Health Monitoring**: Combined health checks for all systems

```python
from shared.database.unified_db_v2 import get_unified_database

# Get the singleton instance
db = await get_unified_database()

# Create agent with automatic caching
agent_id = await db.create_agent(
    name="AI Assistant",
    type="assistant",
    config={"model": "gpt-4"},
    capabilities=["chat"],
    status="active"
)

# Search across all data types
results = await db.search("machine learning")
print(f"Found {len(results['agents'])} agents")
print(f"Found {len(results['workflows'])} workflows")

# Get performance metrics
metrics = await db.get_performance_metrics()
print(f"Cache hit rate: {metrics['cache']['hit_rate']:.2%}")
```

## Key Features

### 1. Zero Duplication

- **Single Connection Pool**: All components share one optimized connection pool
- **Unified Cache**: One cache implementation with consistent TTL and cleanup
- **Shared Sessions**: One session store for all user and agent sessions

### 2. Performance Optimizations

- **Connection Pooling**: Optimized pool size with min/max connections
- **PostgreSQL Tuning**: Server-side optimizations for performance
- **Async Throughout**: Full async/await support for maximum concurrency
- **Batch Operations**: Support for bulk inserts and updates
- **Prepared Statements**: Automatic statement preparation for repeated queries

### 3. Automatic Maintenance

- **Cache Cleanup**: Background task removes expired cache entries
- **Session Cleanup**: Automatic removal of expired sessions
- **Connection Health**: Periodic health checks ensure connection stability
- **Memory Management**: Efficient resource usage with connection recycling

## Migration Guide

### From Old Architecture to Unified

1. **Update Imports**:
```python
# Old
from shared.database.postgresql_client import PostgreSQLClient
from shared.cache.postgresql_cache import PostgreSQLCache
from shared.sessions.postgresql_sessions import PostgreSQLSessionStore

# New
from shared.database.unified_postgresql import get_unified_postgresql
from shared.database.unified_db_v2 import get_unified_database
```

2. **Update Instantiation**:
```python
# Old
client = PostgreSQLClient()
cache = PostgreSQLCache()
sessions = PostgreSQLSessionStore()

# New
client = await get_unified_postgresql()
db = await get_unified_database()
```

3. **Update Method Calls**:
```python
# Old
await cache.set("key", "value")
await sessions.create_session(user_id="123")

# New
await client.cache_set("key", "value", ttl=3600)
await client.session_create(user_id="123", data={})
```

### Running the Migration Script

```bash
# Run the automated migration
python scripts/migrate_to_unified_postgresql.py

# The script will:
# 1. Backup existing data
# 2. Migrate sessions and cache entries
# 3. Update code references
# 4. Remove deprecated tables
# 5. Validate the migration
```

## Performance Monitoring

### Real-time Dashboard

Monitor system performance with the included dashboard:

```bash
# Start the monitoring dashboard
python monitoring/postgresql_performance_dashboard.py

# Access at http://localhost:8000
```

The dashboard provides:
- Connection pool utilization
- Cache hit rates
- Operations per second
- Query performance metrics
- Table statistics
- Health status

### Programmatic Monitoring

```python
# Get connection pool stats
manager = await get_connection_manager()
stats = await manager.get_pool_stats()

# Get performance metrics
db = await get_unified_database()
metrics = await db.get_performance_metrics()

# Get health status
health = await db.health_check()
```

## Configuration

### Environment Variables

```bash
# PostgreSQL connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cherry_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Connection pool settings
POSTGRES_POOL_MIN_SIZE=5
POSTGRES_POOL_MAX_SIZE=20

# Cache settings
CACHE_DEFAULT_TTL=3600
CACHE_CLEANUP_INTERVAL=300

# Session settings
SESSION_DEFAULT_TTL=86400
SESSION_CLEANUP_INTERVAL=3600
```

### PostgreSQL Optimizations

The system automatically applies these optimizations:

```sql
-- Shared memory and buffers
shared_buffers = '256MB'
effective_cache_size = '1GB'
work_mem = '16MB'

-- Write performance
wal_buffers = '16MB'
checkpoint_completion_target = 0.9
max_wal_size = '1GB'

-- Query planning
random_page_cost = 1.1
effective_io_concurrency = 200

-- Connection handling
max_connections = 100
```

## Best Practices

### 1. Use Singleton Instances

Always use the provided getter functions:

```python
# Good
client = await get_unified_postgresql()

# Bad - creates duplicate connections
client = UnifiedPostgreSQL()  # Don't do this!
```

### 2. Handle Connections Properly

```python
# The system handles connections automatically
async def my_function():
    db = await get_unified_database()
    
    # Use the database
    result = await db.get_agent(agent_id)
    
    # No need to close - handled automatically
    return result
```

### 3. Use Appropriate TTLs

```python
# Short-lived data (API responses)
await client.cache_set("api_response", data, ttl=300)  # 5 minutes

# Session data
await client.session_create(user_id=user_id, data=data, ttl=86400)  # 24 hours

# Long-lived data (configurations)
await client.cache_set("config", data, ttl=604800)  # 7 days
```

### 4. Leverage Caching

```python
# The unified database automatically caches
agent = await db.get_agent(agent_id)  # First call - from database
agent = await db.get_agent(agent_id)  # Second call - from cache (faster)

# Invalidation happens automatically on updates
await db.update_agent(agent_id, status="inactive")  # Cache invalidated
```

### 5. Monitor Performance

```python
# Regular health checks
health = await db.health_check()
if health['status'] != 'healthy':
    logger.warning(f"System degraded: {health}")

# Track metrics
metrics = await db.get_performance_metrics()
logger.info(f"Cache hit rate: {metrics['cache']['hit_rate']:.2%}")
```

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
```python
# Check pool usage
stats = await manager.get_pool_stats()
if stats['used_connections'] == stats['total_connections']:
    logger.error("Connection pool exhausted!")
```

2. **Cache Misses**
```python
# Monitor cache performance
metrics = await db.get_performance_metrics()
if metrics['cache']['hit_rate'] < 0.8:
    logger.warning("Low cache hit rate - consider increasing TTLs")
```

3. **Slow Queries**
```python
# Use the dashboard to identify slow queries
# Or programmatically:
slow_queries = await client._connection_manager.fetch("""
    SELECT query, mean_exec_time 
    FROM pg_stat_statements 
    WHERE mean_exec_time > 100
    ORDER BY mean_exec_time DESC
    LIMIT 10
""")
```

### Debug Mode

Enable detailed logging:

```python
import logging

# Enable debug logging
logging.getLogger('shared.database').setLevel(logging.DEBUG)

# Now all database operations will be logged
db = await get_unified_database()
await db.create_agent(...)  # Detailed logs will appear
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/test_unified_postgresql.py -v

# Run specific test classes
pytest tests/test_unified_postgresql.py::TestConnectionManager -v
pytest tests/test_unified_postgresql.py::TestUnifiedPostgreSQL -v
pytest tests/test_unified_postgresql.py::TestUnifiedDatabase -v

# Run with coverage
pytest tests/test_unified_postgresql.py --cov=shared.database --cov-report=html
```

## Summary

The unified PostgreSQL architecture provides:

1. **Single source of truth** for all database operations
2. **Optimal performance** through shared connection pooling
3. **Automatic maintenance** with background cleanup tasks
4. **Comprehensive monitoring** with real-time dashboard
5. **Zero duplication** in code and resources

This architecture embodies the principles of simplicity, performance, and reliability, making it ideal for production deployment on Vultr servers.