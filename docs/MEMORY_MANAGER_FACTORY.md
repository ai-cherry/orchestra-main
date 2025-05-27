# Memory Manager Factory

This document explains the new memory management components introduced in Phase 3 of the memory management consolidation plan.

## Overview

The memory management system has been enhanced with the following features:

1. **Hierarchical Configuration System**: A Pydantic-based configuration system that supports environment variable overrides, default values, and validation.
2. **Unified Factory**: A factory class for creating memory manager instances based on configuration.
3. **Capability Discovery**: A system for detecting available services and features.
4. **Telemetry Integration**: Support for distributed tracing, metrics, and structured logging.

These enhancements improve the maintainability, flexibility, and observability of the memory management system.

## Configuration System

The configuration system is based on Pydantic models, which provide validation, serialization, and deserialization capabilities. The main configuration classes are:

- `MemoryConfig`: Root configuration for the memory system
- `MongoDB
- `RedisConfig`: Configuration for Redis backend
- `InMemoryConfig`: Configuration for in-memory backend
- `VectorSearchConfig`: Configuration for vector search
- `TelemetryConfig`: Configuration for telemetry

### Example: Creating a Configuration

```python
from packages.shared.src.memory.config import (
    MemoryConfig,
    MemoryBackendType,
    MongoDB
    VectorSearchConfig,
    VectorSearchType
)

# Create configuration
config = MemoryConfig(
    backend=MemoryBackendType.MongoDB
    MongoDB
        namespace="example",
        connection_pool_size=5
    ),
    vector_search=VectorSearchConfig(
        provider=VectorSearchType.IN_MEMORY
    )
)
```

### Environment Variables

The configuration system supports environment variables for common settings:

- `MEMORY_BACKEND`: Memory backend to use (MongoDB
- `GOOGLE_CLOUD_PROJECT`: - `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account credentials file
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `REDIS_PASSWORD`: Redis password
- `VECTOR_SEARCH_PROVIDER`: Vector search provider to use (in_memory, vertex)
- `VECTOR_SEARCH_INDEX_ENDPOINT_ID`: Vector Search index endpoint ID
- `VECTOR_SEARCH_INDEX_ID`: Vector Search index ID

### Example: Loading Configuration from Environment Variables

```python
from packages.shared.src.memory.config import MemoryConfig

# Set environment variables
import os
os.environ["MEMORY_BACKEND"] = "MongoDB
os.environ["VECTOR_SEARCH_PROVIDER"] = "in_memory"

# Load configuration from environment variables
config = MemoryConfig.from_env()
```

## Memory Manager Factory

The `MemoryManagerFactory` class provides methods for creating memory manager instances based on configuration. It supports different types of memory managers and implements capability discovery to detect available services.

### Example: Creating a Memory Manager

```python
from packages.shared.src.memory.factory import MemoryManagerFactory
from packages.shared.src.memory.config import MemoryConfig

# Create configuration
config = MemoryConfig.from_env()

# Create memory manager
memory_manager = await MemoryManagerFactory.create_memory_manager(config)

# Use memory manager
try:
    # Add memory item
    item_id = await memory_manager.add_memory_item(memory_item)

    # Perform semantic search
    results = await memory_manager.semantic_search(
        user_id="user123",
        query_embedding=[0.1, 0.2, 0.3, ...],
        top_k=5
    )
finally:
    # Close memory manager
    await memory_manager.close()
```

### Capability Discovery

The `MemoryManagerFactory` class provides methods for detecting available services and features:

```python
from packages.shared.src.memory.factory import MemoryManagerFactory

# Get available backends
available_backends = MemoryManagerFactory.get_available_backends()
print(f"Available backends: {[b.value for b in available_backends]}")

# Get available vector search providers
available_providers = MemoryManagerFactory.get_available_vector_search_providers()
print(f"Available vector search providers: {[p.value for p in available_providers]}")

# Get detailed capabilities
capabilities = MemoryManagerFactory.detect_capabilities()
print(f"Capabilities: {capabilities}")
```

## Telemetry Integration

The telemetry integration provides support for distributed tracing, metrics, and structured logging. It uses OpenTelemetry for tracing and metrics, with fallbacks for when OpenTelemetry is not available.

### Example: Using Telemetry

```python
from packages.shared.src.memory.telemetry import (
    configure_telemetry,
    trace_operation,
    trace_context,
    log_operation
)
from packages.shared.src.memory.config import TelemetryConfig

# Configure telemetry
configure_telemetry(TelemetryConfig(enabled=True))

# Trace an operation using a decorator
@trace_operation("add_memory_item")
async def add_memory_item(memory_manager, item):
    item_id = await memory_manager.add_memory_item(item)
    log_operation(
        logging.INFO,
        f"Added memory item {item_id}",
        "add_memory_item",
        user_id=item.user_id,
        item_id=item_id
    )
    return item_id

# Trace an operation using a context manager
async def perform_search(memory_manager, user_id, query_embedding):
    with trace_context("semantic_search", attributes={"user_id": user_id}):
        results = await memory_manager.semantic_search(
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=5
        )
        log_operation(
            logging.INFO,
            f"Performed semantic search for user {user_id}",
            "semantic_search",
            user_id=user_id,
            result_count=len(results)
        )
        return results
```

## Complete Example

See the `examples/memory_management_example.py` script for a complete example of using the new memory management components.

## Next Steps

The next phase of the memory management consolidation plan is Phase 4: Complete Deprecation, which will involve:

1. Announcing deprecation with a clear timeline
2. Removing deprecated code paths after the transition period
3. Updating all documentation to reference only the new implementation
4. Conducting performance benchmarks to validate improvements
