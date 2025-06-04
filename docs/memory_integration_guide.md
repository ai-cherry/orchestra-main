# Memory Integration Guide

This guide explains how to integrate the AI cherry_ai memory system with agents. It provides step-by-step instructions for implementing different types of memory and using them in agents.

## Table of Contents

1. [Overview](#overview)
2. [Memory Types](#memory-types)
3. [Configuration](#configuration)
4. [Basic Integration](#basic-integration)
5. [Advanced Integration](#advanced-integration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## Overview

The AI cherry_ai memory system provides a layered approach to memory management, with different types of memory for different use cases:

- **Short-term Memory**: Fast, ephemeral storage for conversation context and working memory
- **Mid-term Memory**: Structured storage for session data and user preferences
- **Long-term Memory**: Persistent storage for user profiles and important facts
- **Semantic Memory**: Vector-based storage for knowledge retrieval and similar examples

This guide will show you how to integrate these memory types with your agents.

## Memory Types

### Short-term Memory (Redis)

- Fast, in-memory storage
- Automatically expires after a configurable TTL (default: 1 hour)
- Ideal for conversation context, recent interactions, and working memory
- Implemented using Redis (Memorystore)

### Mid-term Memory (PostgreSQL

- Structured, document-based storage
- Longer TTL than short-term memory (default: 1 day)
- Ideal for session data, user preferences, and ongoing tasks
- Implemented using PostgreSQL

### Long-term Memory (PostgreSQL

- Persistent storage for important information
- Very long TTL or no expiration (default: 30 days)
- Ideal for user profiles, learned behaviors, and important facts
- Implemented using PostgreSQL

### Semantic Memory (
- Vector-based storage for semantic search
- Stores embeddings for text data
- Enables similarity search and retrieval of relevant information
- Ideal for knowledge retrieval, similar examples, and contextual understanding
- Implemented using
## Configuration

### Memory Configuration in YAML

Agents are configured using YAML files in the `config/agents/` directory. Here's an example configuration for an agent with layered memory:

```yaml
agents:
  persona_agent:
    type: persona
    model: gemini-pro
    temperature: 0.7
    memory:
      memory_type: layered
      short_term:
        ttl: 3600 # 1 hour
      mid_term:
        ttl: 86400 # 1 day
      long_term:
        ttl: 2592000 # 30 days
      semantic:
        vector_dimension: 768
    capabilities:
      - conversation
      - knowledge_retrieval
    priority: 10
```

### Memory Configuration in Python

You can also configure memory programmatically using Pydantic models:

```python
from core.conductor.src.config.models import MemoryConfig, MemoryType

# Configure layered memory
memory_config = MemoryConfig(
    memory_type=MemoryType.LAYERED,
    short_term={"ttl": 3600},
    mid_term={"ttl": 86400},
    long_term={"ttl": 2592000},
    semantic={"vector_dimension": 768}
)

# Configure Redis memory
redis_memory_config = MemoryConfig(
    memory_type=MemoryType.REDIS,
    ttl=3600
)

# Configure PostgreSQL
PostgreSQL
    memory_type=MemoryType.PostgreSQL
    table_name="agent_memory",
    ttl=86400
)

# Configure vertex_memory_config = MemoryConfig(
    memory_type=MemoryType.VERTEX_VECTOR,
    vector_dimension=768
)
```

## Basic Integration

### Step 1: Import Required Modules

```python
from core.conductor.src.agents.observable_agent import ObservableAgentFactory
from core.conductor.src.memory.factory import MemoryFactory, get_memory_factory
from core.conductor.src.config.models import MemoryConfig, MemoryType
from core.conductor.src.services.unified_registry import get_service
```

### Step 2: Create Memory Factory

```python
# Get memory factory from service registry
memory_factory = get_service(MemoryFactory)

# Or create a new memory factory
memory_factory = get_memory_factory()
```

### Step 3: Create Observable Agent Factory

```python
# Create observable agent factory
observable_factory = ObservableAgentFactory(memory_factory=memory_factory)
```

### Step 4: Create Observable Agent with Memory

```python
# Create observable agent with memory
observable_agent = observable_factory.create_observable_agent(
    wrapped_agent=original_agent,
    agent_id=agent_type,
    memory_config=agent_config.memory
)
```

### Step 5: Register the Agent

```python
# Register the agent with the registry
registry.register_agent(observable_agent, agent_type, capabilities, priority)
```

## Advanced Integration

### Using Memory Directly

You can also use the memory system directly in your agents:

```python
from core.conductor.src.memory.factory import get_memory_factory
from core.conductor.src.config.models import MemoryConfig, MemoryType

class MyAgent:
    def __init__(self):
        # Create memory factory
        memory_factory = get_memory_factory()

        # Create memory config
        memory_config = MemoryConfig(
            memory_type=MemoryType.LAYERED,
            short_term={"ttl": 3600},
            mid_term={"ttl": 86400},
            long_term={"ttl": 2592000},
            semantic={"vector_dimension": 768}
        )

        # Create memory
        self.memory = memory_factory.create_memory_from_config(memory_config)

    async def process(self, context):
        # Store data in memory
        await self.memory.store("conversation:123", {
            "user_input": context.user_input,
            "timestamp": time.time()
        })

        # Retrieve data from memory
        previous_conversation = await self.memory.retrieve("conversation:123")

        # Perform semantic search
        similar_conversations = await self.memory.semantic_search(
            query_embedding=context.embedding,
            limit=5,
            threshold=0.7
        )

        # Process the request
        # ...

        return response
```

### Custom Memory Integration

For more advanced use cases, you can create a custom memory integration:

```python
from core.conductor.src.memory.factory import get_memory_factory
from core.conductor.src.memory.layered_memory import LayeredMemory

class CustomMemoryAgent:
    def __init__(self):
        # Create memory factory
        memory_factory = get_memory_factory()

        # Create layered memory with custom configuration
        self.memory = memory_factory.create_layered_memory({
            "short_term": {
                "host": "localhost",
                "port": 6379,
                "ttl": 3600
            },
            "mid_term": {
                "collection": "mid_term_memory",
                "ttl": 86400
            },
            "long_term": {
                "collection": "long_term_memory",
                "ttl": 2592000
            },
            "semantic": {
                "project_id": "cherry-ai-project",
                "region": "us-west4",
                "vector_dimension": 768
            }
        })

    async def store_conversation(self, conversation_id, user_input, response):
        """Store conversation in memory."""
        key = f"conversation:{conversation_id}:{time.time()}"

        # Store in short-term memory
        await self.memory.store(key, {
            "user_input": user_input,
            "response": response,
            "timestamp": time.time()
        }, layer="short_term")

        # Store important conversations in long-term memory
        if self._is_important(user_input, response):
            await self.memory.store(key, {
                "user_input": user_input,
                "response": response,
                "timestamp": time.time(),
                "importance": self._calculate_importance(user_input, response)
            }, layer="long_term")

    async def retrieve_conversation_history(self, conversation_id, limit=10):
        """Retrieve conversation history from memory."""
        # Search for conversation history
        results = await self.memory.search(
            field="conversation_id",
            value=conversation_id,
            operator="==",
            limit=limit
        )

        return results

    async def find_similar_conversations(self, query_embedding, limit=5):
        """Find similar conversations using semantic search."""
        results = await self.memory.semantic_search(
            query_embedding=query_embedding,
            limit=limit,
            threshold=0.7
        )

        return results
```

## Testing

### Unit Testing Memory Integration

Here's an example of how to unit test memory integration:

```python
import pytest
from unittest.mock import MagicMock, patch

from core.conductor.src.memory.factory import MemoryFactory
from core.conductor.src.config.models import MemoryConfig, MemoryType
from core.conductor.src.agents.observable_agent import ObservableAgentFactory

@pytest.fixture
def mock_memory_factory():
    """Create a mock memory factory."""
    mock_factory = MagicMock(spec=MemoryFactory)
    mock_memory = MagicMock()
    mock_factory.create_memory_from_config.return_value = mock_memory
    return mock_factory, mock_memory

@pytest.mark.asyncio
async def test_observable_agent_with_memory(mock_memory_factory):
    """Test observable agent with memory."""
    mock_factory, mock_memory = mock_memory_factory

    # Create mock agent
    mock_agent = MagicMock()
    mock_agent.process.return_value = {"text": "Hello, world!"}

    # Create memory config
    memory_config = MemoryConfig(
        memory_type=MemoryType.REDIS,
        ttl=3600
    )

    # Create observable agent factory
    observable_factory = ObservableAgentFactory(memory_factory=mock_factory)

    # Create observable agent with memory
    observable_agent = observable_factory.create_observable_agent(
        wrapped_agent=mock_agent,
        agent_id="test_agent",
        memory_config=memory_config
    )

    # Create mock context
    mock_context = MagicMock()
    mock_context.user_input = "Hello"
    mock_context.conversation_id = "123"

    # Process request
    response = await observable_agent.process(mock_context)

    # Verify that the agent was called
    mock_agent.process.assert_called_once_with(mock_context)

    # Verify that memory was used
    mock_memory.store.assert_called_once()
    assert response == {"text": "Hello, world!"}
```

### Integration Testing Memory System

Here's an example of how to integration test the memory system:

```python
import pytest
import time

from core.conductor.src.memory.factory import get_memory_factory
from core.conductor.src.config.models import MemoryConfig, MemoryType

@pytest.mark.asyncio
async def test_redis_memory():
    """Test Redis memory."""
    # Create memory factory
    memory_factory = get_memory_factory()

    # Create Redis memory
    redis_memory = memory_factory.create_memory_from_config(
        MemoryConfig(
            memory_type=MemoryType.REDIS,
            ttl=3600
        )
    )

    # Store data
    key = f"test:{time.time()}"
    value = {"test": "value"}
    result = await redis_memory.store(key, value)
    assert result is True

    # Retrieve data
    retrieved = await redis_memory.retrieve(key)
    assert retrieved == value

    # Delete data
    result = await redis_memory.delete(key)
    assert result is True

    # Verify deletion
    retrieved = await redis_memory.retrieve(key)
    assert retrieved is None

@pytest.mark.asyncio
async def test_layered_memory():
    """Test layered memory."""
    # Create memory factory
    memory_factory = get_memory_factory()

    # Create layered memory
    layered_memory = memory_factory.create_layered_memory({
        "short_term": {
            "host": "localhost",
            "port": 6379,
            "ttl": 3600
        },
        "mid_term": {
            "collection": "mid_term_memory",
            "ttl": 86400
        }
    })

    # Store data in short-term memory
    key = f"test:{time.time()}"
    value = {"test": "value"}
    result = await layered_memory.store(key, value, layer="short_term")
    assert result is True

    # Retrieve data
    retrieved = await layered_memory.retrieve(key)
    assert retrieved == value

    # Store data in mid-term memory
    key = f"test:{time.time()}"
    value = {"test": "value"}
    result = await layered_memory.store(key, value, layer="mid_term")
    assert result is True

    # Retrieve data
    retrieved = await layered_memory.retrieve(key)
    assert retrieved == value
```

## Troubleshooting

### Common Issues

#### Connection Issues

If you're having trouble connecting to Redis or PostgreSQL

1. Ensure that the services are running and accessible
2. Check that the connection parameters (host, port, etc.) are correct
3. Verify that the service account has the necessary permissions

#### Memory Not Persisting

If data is not being persisted in memory, check the following:

1. Ensure that the store operation is successful (returns True)
2. Check that the TTL is set correctly
3. Verify that the key is correct when retrieving data

#### Semantic Search Not Working

If semantic search is not working, check the following:

1. Ensure that the embedding model is correctly configured
2. Check that the embeddings are being generated correctly
3. Verify that the
### Logging

The memory system uses Python's logging module for debugging. You can enable debug logging to see more information:

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("core.conductor.src.memory").setLevel(logging.DEBUG)
```

### Support

If you encounter issues that you can't resolve, please contact the AI cherry_ai team for support.
