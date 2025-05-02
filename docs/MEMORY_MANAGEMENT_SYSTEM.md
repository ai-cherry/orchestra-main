# Context-Aware Memory Management System

This document describes the enhanced memory management system implemented for the AI Orchestration System. The system optimizes memory usage while maintaining conversation context integrity through several integrated components.

## System Components

### 1. Tiered Storage Manager

The `TieredStorageManager` class provides automatic movement of data between hot, warm, and cold storage tiers based on access patterns.

- **Hot tier**: In-memory cache and Redis Memorystore for fastest access
- **Warm tier**: Firestore collection for standard access
- **Cold tier**: Firestore collection with compression for infrequently accessed data

```python
# Example initialization
tiered_storage = TieredStorageManager(
    base_memory_manager=base_memory,
    project_id="your-project-id",
    redis_host="your-redis-host",
    redis_port=6379,
    hot_tier_max_age_days=7,
    warm_tier_max_age_days=30
)
```

### 2. Redis LRU Cache

The `RedisLRUCache` class provides a Redis-backed Least Recently Used (LRU) cache implementation for the hot tier.

- Uses Redis Memorystore's built-in LRU eviction
- Automatically handles key expiration
- Tracks statistics like hit rates and eviction rates

```python
# Example initialization
redis_cache = RedisLRUCache(
    redis_host="your-redis-host",
    redis_port=6379,
    max_memory_mb=512,
    max_memory_policy="allkeys-lru"
)
```

### 3. Context Pruner

The `ContextPruner` class automatically prunes non-essential context from conversation history.

- Uses Gemini AI to generate summaries of older conversations
- Preserves important context items
- Provides token budget-based pruning

```python
# Example initialization
context_pruner = ContextPruner(
    max_context_items=15,
    max_context_tokens=4000,
    gemini_model="gemini-1.5-pro",
    gemini_project="your-project-id"
)
```

### 4. Memory Profiler

The `MemoryProfiler` class provides memory usage profiling and pressure monitoring.

- Integrates with Google Cloud Profiler for visualization
- Monitors memory usage, hit rates, eviction rates
- Provides alerts for memory pressure conditions

```python
# Example initialization
memory_profiler = MemoryProfiler(
    project_id="your-project-id",
    service_name="memory-service"
)
```

## Usage

See `examples/memory_management_integration.py` for a complete example of setting up and using the memory management system.

### Basic Setup

```python
# Initialize components
base_memory = YourBaseMemoryManager()
await base_memory.initialize()

redis_cache = RedisLRUCache(redis_host="localhost")
await redis_cache.connect()

tiered_storage = TieredStorageManager(
    base_memory_manager=base_memory,
    project_id="your-project-id",
    redis_host="localhost"
)
await tiered_storage.initialize()

context_pruner = ContextPruner(
    max_context_items=15,
    gemini_project="your-project-id"
)

memory_profiler = MemoryProfiler(project_id="your-project-id")
memory_profiler.set_tiered_storage(tiered_storage)
memory_profiler.set_redis_cache(redis_cache)
memory_profiler.start_profiling()
```

### Adding and Retrieving Items

```python
# Add a memory item
item = MemoryItem(
    user_id="user123",
    session_id="session456",
    content="This is a message",
    content_type="user_message"
)
item_id = await tiered_storage.add_memory_item(item)

# Retrieve item
retrieved_item = await tiered_storage.get_memory_item(item_id)

# Get conversation history
history = await tiered_storage.get_conversation_history(
    user_id="user123",
    session_id="session456"
)
```

### Pruning Context

```python
# Prune conversation history
pruned_history = await context_pruner.prune_conversation_history(
    history=history,
    user_id="user123",
    session_id="session456"
)

# Prune by token budget
pruned_history = await context_pruner.prune_by_token_budget(
    history=history,
    token_budget=4000
)
```

### Monitoring Memory Pressure

```python
# Check memory metrics
metrics = await memory_profiler.collect_metrics()

# Check for memory pressure
if memory_profiler.is_memory_pressure_detected():
    alerts = memory_profiler.get_alerts()
    print(f"Memory pressure alerts: {alerts}")
```

## Architecture

```
+-----------------+     +---------------+     +---------------+
| Base Memory     |<----| Tiered        |<----| Client        |
| (Persistent)    |     | Storage       |     | Applications  |
+-----------------+     +---------------+     +---------------+
                         |     |     |
                         v     v     v
                 +-------+  +------+  +-------+
                 | Hot   |  | Warm |  | Cold  |
                 | Tier  |  | Tier |  | Tier  |
                 | Redis |  | Fire |  | Fire  |
                 | Cache |  | store |  | store |
                 +-------+  +------+  +-------+
                     ^
                     |
         +-----------+-----------+
         |                       |
+----------------+    +------------------+
| Memory         |    | Context          |
| Profiler       |    | Pruner (Gemini)  |
+----------------+    +------------------+
```

## Configuration Options

### Tiered Storage Manager

- `hot_tier_max_age_days`: Maximum age for items in hot tier (default: 7 days)
- `warm_tier_max_age_days`: Maximum age for items in warm tier (default: 30 days)
- `min_access_count_hot`: Minimum access count to stay in hot tier (default: 5)
- `min_access_count_warm`: Minimum access count to stay in warm tier (default: 2)
- `enable_compression`: Whether to compress cold tier items (default: True)
- `tier_migration_interval`: Interval between tier migrations in seconds (default: 3600)

### Redis LRU Cache

- `max_memory_mb`: Maximum memory for Redis in MB (default: 512)
- `max_memory_policy`: Redis eviction policy (default: "allkeys-lru")
- `default_ttl`: Default TTL for cache entries in seconds (default: 86400)

### Context Pruner

- `max_context_items`: Maximum number of history items to keep before pruning (default: 15)
- `max_context_tokens`: Maximum token budget for context (default: 4000)
- `summarization_threshold`: Minimum number of items before summarization (default: 25)
- `summary_max_tokens`: Maximum token budget for summaries (default: 1000)

### Memory Profiler

- `profiling_interval`: Interval between profiling runs in seconds (default: 60)
- `alert_thresholds`: Thresholds for memory pressure alerts
