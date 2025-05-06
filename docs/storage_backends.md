# Storage Backends Documentation

This document provides information about the storage backends implemented in the Orchestra system, focusing on the Firestore and Redis implementations for production use.

## Overview

The Orchestra system now supports persistent storage through Google Cloud Firestore and caching through Redis. This implementation provides:

- **Persistent Storage**: All conversations and agent data are stored persistently in Firestore
- **Caching Layer**: Recent conversations and session data are cached in Redis for faster access
- **Fallback Mechanism**: System continues to work with degraded performance if Redis is unavailable
- **Environment-based Configuration**: Different storage implementations are used based on the environment (development, testing, staging, production)

## Architecture

The storage implementation follows a tiered architecture:

1. **Memory Manager Interface**: Defined in `packages/shared/src/memory/memory_manager.py`
2. **Concrete Implementations**:
   - `FirestoreMemoryManager`: Implements persistent storage using Google Cloud Firestore
   - `RedisClient`: Provides caching functionality using Redis
   - `ConcreteMemoryManager`: Combines Firestore and Redis for optimal performance
   - `MemoryManagerStub`: In-memory implementation for development and testing

3. **Dependency Injection**: The appropriate implementation is selected based on the environment in `core/orchestrator/src/api/dependencies/memory.py`

## Configuration

### Environment Variables

The storage backends can be configured using the following environment variables:

```
# Environment setting
APP_ENV=development  # Options: development, test, staging, production

# Google Cloud Platform settings
GCP_PROJECT_ID=your-gcp-project-id
GCP_SA_KEY_JSON=    # JSON string containing service account credentials
GCP_SA_KEY_PATH=    # Path to service account key file

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CACHE_TTL=3600      # Cache TTL in seconds (default: 1 hour)
```

These variables should be set in your `.env` file or as environment variables in your deployment environment.

### Authentication Priority

For GCP authentication, the system tries different methods in the following order:

1. `GCP_SA_KEY_JSON` environment variable (preferred)
2. `GCP_SA_KEY_PATH` environment variable
3. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
4. Application Default Credentials

## Usage

The storage backends are automatically used by the system based on the environment. However, you can also use them directly in your code:

```python
# Using FirestoreMemoryManager
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager

firestore = FirestoreMemoryManager(project_id="your-project-id")
firestore.initialize()

# Store a memory item
memory_item = MemoryItem(...)
item_id = await firestore.add_memory_item(memory_item)

# Using RedisClient
from packages.shared.src.storage.redis.redis_client import RedisClient

redis = RedisClient(host="localhost", port=6379)
redis.initialize()

# Cache data
await redis.set("key", data, ttl=3600)
```

## Collection Schema

### Firestore Collections

- `memory_items`: Stores MemoryItem objects
  - Key fields: `user_id`, `session_id`, `item_type`, `timestamp`
  
- `agent_data`: Stores AgentData objects
  - Key fields: `agent_id`, `data_type`, `timestamp`

- `user_sessions`: Stores user session data
  - Key fields: `user_id`, `session_id`

## Error Handling

The storage implementations include comprehensive error handling:

- **ConnectionError**: Raised when connection to the storage backend fails
- **StorageError**: Raised when a storage operation fails
- **ValidationError**: Raised when validation of data fails

The `ConcreteMemoryManager` will automatically fall back to using just Firestore if Redis is unavailable.

## Health Monitoring

The system includes a health check endpoint at `/api/health` that provides status information about the storage backends. This endpoint can be used to monitor the health of the system.

Example response:

```json
{
  "status": "ok",
  "environment": "production",
  "version": "1.0.0",
  "components": {
    "app": true,
    "storage_firestore": true,
    "storage_redis": true
  },
  "details": {}
}
```

## Testing

Integration tests for the storage backends are included in `tests/integration/test_storage.py`. These tests can be run using the `run_integration_tests.sh` script.

To run the tests with real GCP and Redis services:

1. Set the required environment variables
2. Run the script:

```bash
./run_integration_tests.sh
```

## Performance Considerations

- **Caching**: The system uses Redis to cache conversation history and session data to improve performance. The cache TTL is configurable.
- **Batch Operations**: Firestore batch operations are used for bulk operations to reduce latency.
- **Index Requirements**: The following Firestore indexes are recommended:
  - `memory_items`: Composite index on `user_id`, `item_type`, and `timestamp` (descending)
  - `memory_items`: Composite index on `user_id`, `session_id`, and `timestamp` (descending)

## Security Considerations

- The service account used for Firestore should have the minimal required permissions (Firestore read/write).
- Ensure Redis is properly secured with authentication and network restrictions.
- Do not store sensitive information in the `metadata` field of memory items without encryption.
