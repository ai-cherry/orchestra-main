# Redis Semantic Caching for Orchestra

This documentation explains how to use Redis-based semantic caching with Orchestra. Semantic caching enhances agent memory by efficiently storing and retrieving contextually similar content, significantly improving performance and reducing token consumption.

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting](#troubleshooting)

## Overview

The Redis semantic caching integration provides:

- Efficient vector similarity search using Redis
- LangChain compatibility for easy integration with LLM applications
- Intelligent caching with customizable similarity thresholds
- High-performance retrieval for agent memory systems

This implementation leverages Redis for real-time vector similarity search and LangChain's RedisSemanticCache for a standardized interface to semantic caching operations.

## Key Features

- **Vector Similarity Search**: Uses Redis vector indexing for fast semantic similarity lookups
- **Customizable Thresholds**: Configurable similarity threshold (default 0.85)
- **TTL Support**: Automatic time-based expiration of cached items
- **LangChain Integration**: Works seamlessly with LangChain's memory systems
- **High Performance**: Optimized for low-latency retrieval (<1ms target)

## Architecture

The implementation consists of three main components:

1. **RedisSemanticCacheProvider**: Orchestra's memory provider implementation
2. **SemanticCacher** (from redisvl): Core caching functionality
3. **RedisSemanticCache** (from LangChain): LangChain integration

```
┌─────────────────────┐     ┌─────────────────────┐
│  Orchestra Memory   │     │  LangChain Memory   │
│     Interface       │     │      Systems        │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
┌─────────▼───────────┐     ┌──────────▼──────────┐
│RedisSemanticCache-  │     │ RedisSemanticCache  │
│    Provider         │     │    (LangChain)      │
└─────────┬───────────┘     └──────────┬──────────┘
          │                            │
          └────────────┬───────────────┘
                       │
             ┌─────────▼─────────┐
             │   SemanticCacher  │
             │    (redisvl)      │
             └─────────┬─────────┘
                       │
                ┌──────▼──────┐
                │    Redis    │
                │   Database  │
                └─────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- Redis 5.0+ with RedisSearch module (Redis Stack recommended)
- Gemini API key for embeddings

### Setup

1. Run the setup script:

```bash
# Make the script executable if needed
chmod +x setup_semantic_cache.sh

# Run the setup script
./setup_semantic_cache.sh
```

This script will:

- Install required dependencies
- Configure Redis connection
- Create needed schema files
- Set environment variables

### Manual Installation

If you prefer manual installation:

```bash
# Install dependencies
pip install redisvl>=0.0.5 langchain-redis>=0.1.1 langchain-google-genai>=0.0.3

# Create agent_memory.yaml schema (as shown in this repo)
```

## Configuration

### Required Configuration

The core configuration is defined in the `agent_memory.yaml` file and through environment variables:

```yaml
# agent_memory.yaml schema file
index:
  name: "agent_memory"
  prefix: "memory:"
  fields:
    - name: "text_content"
      type: "text"
      weight: 1.0
    - name: "embedding"
      type: "vector"
      attrs:
        dim: 1536
        algorithm: "hnsw"
        distance_metric: "cosine"
        initial_size: 1000
```

### Environment Variables

```
# Required
REDIS_URL=redis://vertex-agent@cherry-ai-project
GEMINI_API_KEY=your_api_key_here
```

### SemanticCacher Configuration

```python
cacher = SemanticCacher(
    threshold=0.85,  # Similarity threshold
    ttl=3600,        # TTL in seconds (1 hour)
    index_schema="agent_memory.yaml",
    redis_url="redis://vertex-agent@cherry-ai-project"
)
```

### LangChain Integration

```python
langchain_cache = RedisSemanticCache(
    embeddings=GeminiEmbeddings(api_key="your_api_key_here"),
    redis_url="redis://vertex-agent@cherry-ai-project",
    name="agent_semantic_cache"
)
```

## Usage Examples

### Basic Usage with Orchestra

```python
from packages.shared.src.memory.redis_semantic_cacher import RedisSemanticCacheProvider
from packages.shared.src.models.base_models import MemoryItem

# Initialize the provider
provider_config = {
    "threshold": 0.85,
    "ttl": 3600,
    "index_schema": "agent_memory.yaml",
    "redis_url": "redis://vertex-agent@cherry-ai-project"
}

provider = RedisSemanticCacheProvider(config=provider_config)
await provider.initialize()

# Add a memory item
memory_item = MemoryItem(
    user_id="user123",
    session_id="session456",
    item_type="conversation",
    text_content="This is a test memory about AI orchestration",
    metadata={"source": "user"}
)

memory_id = await provider.add_memory(memory_item)

# Retrieve using semantic search
memories = await provider.get_memories(
    user_id="user123",
    session_id="session456",
    query="Tell me about orchestration",
    limit=5
)
```

### LangChain Integration Example

```python
from langchain_redis.cache import RedisSemanticCache
from langchain_google_genai import GoogleGenerativeAIEmbeddings as GeminiEmbeddings

# Initialize the cache
cache = RedisSemanticCache(
    embeddings=GeminiEmbeddings(api_key="your_api_key_here"),
    redis_url="redis://vertex-agent@cherry-ai-project",
    name="agent_semantic_cache"
)

# Check if a response is cached
result = cache.lookup("How does semantic caching work?")
if result:
    print(f"Found in cache: {result}")
else:
    # Generate response and update cache
    response = "Semantic caching works by storing vector embeddings..."
    cache.update("How does semantic caching work?", response)
```

### Direct SemanticCacher Usage

```python
from redisvl import SemanticCacher

# Initialize the cacher
cacher = SemanticCacher(
    threshold=0.85,
    ttl=3600,
    index_schema="agent_memory.yaml",
    redis_url="redis://vertex-agent@cherry-ai-project"
)

# Add an item
item_id = cacher.add_item(
    item_id="mem1",
    text_content="This is a test memory",
    metadata={"user_id": "user123"},
    embedding=None  # Will generate embedding automatically
)

# Search for similar items
results = cacher.search(
    query="Test memory",
    filters={"user_id": "user123"},
    top_k=5
)
```

## Performance Considerations

Redis semantic caching is optimized for performance, but consider these factors:

- **Memory Usage**: Vector indexes consume memory. Monitor Redis memory usage.
- **Similarity Threshold**: Lower thresholds (e.g., 0.8) increase recall but may reduce precision.
- **TTL Settings**: Balance between keeping context and memory consumption.
- **Index Algorithm**: HNSW provides logarithmic search complexity - efficient for large datasets.

### Performance Metrics

The implementation tracks key performance metrics:

- **Latency**: Target <1ms for retrieval operations
- **Hit Rate**: Target >85% for common queries
- **Memory Efficiency**: Automatic TTL expiration to optimize memory usage

## Troubleshooting

### Common Issues

1. **Connection Errors**:

   - Verify Redis URL is correct
   - Ensure Redis instance is running and accessible
   - Check network connectivity and firewall settings

2. **Schema Errors**:

   - Validate the YAML schema is correctly formatted
   - Ensure Redis has vector search capability
   - Check for proper field types in schema

3. **Empty Results**:
   - Check similarity threshold (may be too high)
   - Verify data has been properly added to cache
   - Confirm embeddings are being generated correctly

### Logging

Enable detailed logging to debug issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("redisvl")
```

## Advanced Configuration

### Fine-tuning the Vector Index

For larger deployments, consider tuning the HNSW parameters:

```yaml
attrs:
  dim: 1536
  algorithm: "hnsw"
  distance_metric: "cosine"
  initial_size: 1000
  m: 16 # Number of connections per node
  ef_construction: 200 # Effect on build-time quality
  ef_runtime: 100 # Effect on search quality
```

### Redis Enterprise Features

When using Redis Enterprise, additional features are available:

- Multi-zone high availability
- Auto-tiering for large datasets
- Enhanced monitoring and metrics

## Further Resources

- [RedisVL Documentation](https://github.com/redis-labs/redisvl)
- [LangChain Redis Documentation](https://python.langchain.com/docs/integrations/memory/redis_chat_memory)
- [Redis Vector Similarity Documentation](https://redis.io/docs/stack/search/reference/vectors/)
