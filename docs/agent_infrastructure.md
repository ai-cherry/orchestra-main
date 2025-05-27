# AI Orchestra Agent Infrastructure

This document provides an overview of the AI Orchestra agent infrastructure, focusing on the memory system and agent configuration.

## Memory Architecture

AI Orchestra uses a layered memory architecture that provides different types of memory for different use cases:

### Memory Layers

1. **Short-term Memory (Redis)**

   - Fast, in-memory storage for frequently accessed data
   - Automatically expires after a configurable TTL (default: 1 hour)
   - Ideal for conversation context, recent interactions, and working memory

2. **Mid-term Memory (MongoDB

   - Structured, document-based storage for medium-term persistence
   - Longer TTL than short-term memory (default: 1 day)
   - Ideal for session data, user preferences, and ongoing tasks

3. **Long-term Memory (MongoDB

   - Persistent storage for important information
   - Very long TTL or no expiration (default: 30 days)
   - Ideal for user profiles, learned behaviors, and important facts

4. **Semantic Memory (   - Vector-based storage for semantic search
   - Stores embeddings for text data
   - Enables similarity search and retrieval of relevant information
   - Ideal for knowledge retrieval, similar examples, and contextual understanding

### Memory Flow

The memory system automatically manages the flow of information between layers:

1. **Promotion**: When an item is accessed from a lower layer (e.g., mid-term), it can be automatically promoted to higher layers (e.g., short-term) for faster access.

2. **Demotion**: Important items can be demoted from higher layers to lower layers for long-term storage.

3. **Expiration**: Items automatically expire from each layer based on their TTL, with the option to cascade deletion across layers.

4. **Semantic Indexing**: Text data can be automatically embedded and indexed in the semantic memory layer for similarity search.

## Infrastructure Components

The memory system is built on the following
1. **Redis (Memorystore)**

   - Used for short-term memory
   - Provides fast, in-memory storage with automatic expiration
   - Configured with authentication for security

2. **MongoDB

   - Used for mid-term and long-term memory
   - Provides structured, document-based storage
   - Scales automatically with usage

3. **
   - Used for semantic memory
   - Provides efficient similarity search for embeddings
   - Integrated with
4. **   - Stores sensitive configuration (e.g., Redis password)
   - Securely accessed by the application

## Memory System Implementation

The memory system is implemented as a set of Python classes:

1. **Memory Interface (`MemoryInterface`)**

   - Abstract base class defining the memory API
   - Methods for storing, retrieving, and deleting data
   - Methods for semantic search and batch operations

2. **Memory Backends**

   - `RedisMemory`: Implementation for Redis
   - `MongoDB
   - `VertexMemory`: Implementation for
3. **Layered Memory (`LayeredMemory`)**

   - Combines multiple memory backends into a unified system
   - Manages the flow of information between layers
   - Provides a single API for accessing all memory types

4. **Memory Factory (`MemoryFactory`)**
   - Creates memory instances based on configuration
   - Manages dependencies and connections
   - Provides a simple way to create memory systems

## Agent Integration

Agents can use the memory system through the `ObservableAgent` wrapper:

```python
from core.orchestrator.src.agents.observable_agent import ObservableAgentFactory
from core.orchestrator.src.memory.factory import MemoryFactory

# Get memory factory
memory_factory = get_service(MemoryFactory)

# Create observable agent factory
observable_factory = ObservableAgentFactory(memory_factory=memory_factory)

# Create observable agent with memory
observable_agent = observable_factory.create_observable_agent(
    wrapped_agent=original_agent,
    agent_id=agent_type,
    memory_config=agent_config.memory
)

# Register the wrapped agent
registry.register_agent(observable_agent, agent_type, capabilities, priority)
```

The `ObservableAgent` wrapper adds the following capabilities to agents:

1. **Memory Access**: Agents can store and retrieve data from the memory system
2. **Automatic Context Enhancement**: Relevant information is automatically retrieved from memory
3. **Logging and Metrics**: Agent operations are logged and metrics are collected
4. **Tracing**: Agent execution is traced for debugging and monitoring

## Agent Configuration

Agents are configured using YAML files in the `config/agents/` directory:

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

The configuration includes:

1. **Agent Type**: The type of agent (e.g., persona, tool, router)
2. **Model Configuration**: The LLM model and parameters
3. **Memory Configuration**: The memory layers and TTLs
4. **Capabilities**: The capabilities of the agent
5. **Priority**: The priority of the agent in the registry

## Infrastructure Setup

The memory infrastructure is provisioned using Pulumi:

1. **Pulumi Module**: `infra/modules/memory_infrastructure/`
2. **Setup Script**: `scripts/setup_memory_infrastructure.sh`

To set up the infrastructure:

```bash
# Make the script executable
chmod +x scripts/setup_memory_infrastructure.sh

# Run the script
./scripts/setup_memory_infrastructure.sh
```

The script will:

1. Create a service account for the memory system
2. Grant the necessary permissions
3. Create a storage bucket for vector embeddings
4. Apply the Pulumi configuration

## Best Practices

1. **Memory Layer Selection**

   - Use short-term memory for conversation context and working memory
   - Use mid-term memory for session data and user preferences
   - Use long-term memory for user profiles and important facts
   - Use semantic memory for knowledge retrieval and similar examples

2. **TTL Configuration**

   - Set appropriate TTLs for each memory layer based on the use case
   - Consider the cost and performance implications of longer TTLs

3. **Batch Operations**

   - Use batch operations for better performance when storing or retrieving multiple items
   - Consider the atomicity requirements of your operations

4. **Error Handling**

   - Handle memory errors gracefully in your agents
   - Provide fallbacks for when memory operations fail

5. **Monitoring**
   - Monitor memory usage and performance
   - Set up alerts for memory-related issues

## Future Enhancements

1. **Memory Compression**

   - Automatically compress and summarize memory items
   - Reduce storage costs and improve retrieval performance

2. **Memory Prioritization**

   - Prioritize important memory items for retention
   - Automatically identify and retain important information

3. **Cross-Agent Memory Sharing**

   - Enable agents to share memory with each other
   - Implement access controls for memory sharing

4. **Memory Visualization**

   - Visualize the contents of the memory system
   - Provide tools for debugging and monitoring

5. **Memory Analytics**
   - Analyze memory usage patterns
   - Optimize memory configuration based on usage

## Conclusion

The AI Orchestra memory system provides a robust foundation for building intelligent agents with different types of memory. By leveraging
