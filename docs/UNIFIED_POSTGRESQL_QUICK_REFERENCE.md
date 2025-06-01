# Unified PostgreSQL Enhanced - Quick Reference Guide

## Overview
The enhanced unified PostgreSQL system provides a complete, optimized database solution with all missing methods implemented through a clean mixin architecture.

## Key Components

### 1. Enhanced Connection Manager
```python
from shared.database.connection_manager_enhanced import get_connection_manager_enhanced

# Get singleton instance
manager = await get_connection_manager_enhanced()

# New methods available:
pool_stats = await manager.get_pool_stats()
extended_stats = await manager.get_extended_pool_stats()
await manager.adjust_pool_size(min_size=10, max_size=50)
diagnostics = await manager.get_connection_diagnostics()
```

### 2. Enhanced PostgreSQL Client
```python
from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced

# Get singleton instance
postgres = await get_unified_postgresql_enhanced()

# Cache operations (all missing methods now available)
items = await postgres.cache_get_by_tags(['important', 'user:123'])
values = await postgres.cache_get_many(['key1', 'key2', 'key3'])
await postgres.cache_set_many({'key1': 'val1', 'key2': 'val2'})
info = await postgres.cache_info()

# Session operations (all missing methods now available)
sessions = await postgres.session_list(user_id='user123', active=True)
await postgres.session_extend('session_id', 3600)
analytics = await postgres.session_analytics()
session = await postgres.session_get_by_token('token123')

# Memory snapshot operations (all missing methods now available)
snapshot_id = await postgres.memory_snapshot_create('agent123', memory_data)
snapshot = await postgres.memory_snapshot_get(snapshot_id)
snapshots = await postgres.memory_snapshot_list(agent_id='agent123')
results = await postgres.memory_snapshot_search('query text')
```

### 3. Unified Database Interface
```python
from shared.database.unified_db_v2 import get_unified_database

# Get singleton instance - automatically uses enhanced versions
db = await get_unified_database()

# All operations work seamlessly with enhancements
health = await db.health_check()
stats = await db.get_stats()
```

## Migration from Original System

The enhanced system is 100% backward compatible. To migrate:

1. **Update imports** (done automatically by apply_unified_enhancements.py):
   ```python
   # Old
   from shared.database.connection_manager import get_connection_manager
   
   # New (but aliased to maintain compatibility)
   from shared.database.connection_manager_enhanced import get_connection_manager_enhanced as get_connection_manager
   ```

2. **No code changes required** - All existing code continues to work

3. **New methods immediately available** - Start using enhanced features

## Performance Optimizations Applied

1. **Connection Pool Tuning**
   - Dynamic sizing based on system resources
   - Automatic idle connection cleanup
   - Connection health monitoring

2. **Query Optimizations**
   - Prepared statements for frequently used queries
   - Batch operations to reduce round trips
   - Optimized indexes on all lookup columns

3. **Cache Improvements**
   - GIN indexes for tag-based queries
   - Batch get/set operations
   - Automatic TTL management

4. **Session Management**
   - Efficient bulk operations
   - Background cleanup of expired sessions
   - Token-based quick lookups

## Monitoring and Diagnostics

### Real-time Dashboard
```bash
python3 monitoring/postgresql_performance_dashboard.py
```

### Quick Health Check
```python
db = await get_unified_database()
health = await db.health_check()
print(f"Status: {health['status']}")
print(f"Pool: {health['postgresql']['pool_stats']}")
```

### Performance Stats
```python
postgres = await get_unified_postgresql_enhanced()
stats = await postgres.get_comprehensive_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate']}%")
print(f"Active sessions: {stats['sessions']['active_count']}")
```

## Common Operations

### Batch Cache Operations
```python
# Set multiple values at once
await postgres.cache_set_many({
    'user:123:profile': user_profile,
    'user:123:settings': user_settings,
    'user:123:preferences': user_preferences
})

# Get multiple values at once
results = await postgres.cache_get_many([
    'user:123:profile',
    'user:123:settings',
    'user:123:preferences'
])
```

### Session Analytics
```python
# Get comprehensive session analytics
analytics = await postgres.session_analytics()
print(f"Total sessions: {analytics['total_sessions']}")
print(f"Active sessions: {analytics['active_sessions']}")
print(f"Average duration: {analytics['avg_duration_minutes']} minutes")
```

### Memory Snapshot Management
```python
# Create a snapshot
snapshot_id = await postgres.memory_snapshot_create(
    agent_id='agent123',
    memory_data={'conversation': [...], 'context': {...}}
)

# Search across snapshots
results = await postgres.memory_snapshot_search(
    query='previous discussion about API design',
    agent_id='agent123'
)
```

## Troubleshooting

### Connection Issues
```python
# Get detailed diagnostics
manager = await get_connection_manager_enhanced()
diagnostics = await manager.get_connection_diagnostics()
print(diagnostics)

# Get recommendations
recommendations = await manager.get_pool_recommendations()
for rec in recommendations:
    print(f"- {rec}")
```

### Performance Issues
```python
# Check pool utilization
stats = await manager.get_extended_pool_stats()
if stats['utilization'] > 0.8:
    print("High pool utilization - consider increasing pool size")
    await manager.adjust_pool_size(max_size=stats['max_size'] + 10)
```

## Environment Variables

```bash
# PostgreSQL connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestra
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Pool configuration (optional - auto-tuned by default)
POSTGRES_POOL_MIN_SIZE=5
POSTGRES_POOL_MAX_SIZE=20

# Performance tuning (optional)
POSTGRES_COMMAND_TIMEOUT=60
POSTGRES_POOL_RECYCLE=3600
```

## Summary

The enhanced unified PostgreSQL system provides:
- ✅ All missing methods implemented
- ✅ 100% backward compatibility
- ✅ Optimized performance
- ✅ Comprehensive monitoring
- ✅ Production-ready error handling
- ✅ Vultr deployment optimized

No code changes required - just enjoy the enhanced functionality!