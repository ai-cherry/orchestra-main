# AI Orchestra Implementation Plan

This document outlines the step-by-step implementation plan for deploying the new agent configuration and memory architecture in AI Orchestra.

## Phase 1: Infrastructure Setup (Week 1)

### Day 1-2: Set Up Credentials and GCP Resources

1. **Run setup scripts**:

   ```bash
   # Make scripts executable
   chmod +x scripts/setup_all_credentials.sh
   chmod +x scripts/bootstrap_orchestra_infrastructure.sh

   # Set up credentials
   ./scripts/setup_all_credentials.sh

   # Set up infrastructure
   ./scripts/bootstrap_orchestra_infrastructure.sh
   ```

2. **Update Poetry dependencies**:

   ```bash
   # Add required dependencies
   poetry add google-cloud-secret-manager google-cloud-firestore \
     google-cloud-redis google-cloud-aiplatform redis

   # Add development dependencies
   poetry add --group dev pytest-asyncio pytest-mock
   ```

3. **Create directory structure**:

   ```bash
   # Create memory directories if they don't exist
   mkdir -p core/orchestrator/src/memory/backends
   mkdir -p tests/core/orchestrator/memory
   ```

4. **Update GitHub organization secrets**:
   - Add `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SECRET_MANAGEMENT_KEY`, and `GCP_PROJECT_ADMIN_KEY`

## Phase 2: Memory Backend Implementation (Week 1-2)

### Day 3-5: Implement Memory Backends

1. **Create memory interface**:

   ```python
   # core/orchestrator/src/memory/interface.py
   from abc import ABC, abstractmethod
   from typing import Any, Dict, List, Optional, Tuple

   class MemoryInterface(ABC):
       """Interface for memory backends."""

       @abstractmethod
       async def store(self, key: str, value: Dict[str, Any], **kwargs) -> bool:
           """Store an item in memory."""
           pass

       @abstractmethod
       async def retrieve(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
           """Retrieve an item from memory."""
           pass

       @abstractmethod
       async def delete(self, key: str, **kwargs) -> bool:
           """Delete an item from memory."""
           pass

       @abstractmethod
       async def semantic_search(
           self,
           query_embedding: List[float],
           limit: int = 5,
           threshold: float = 0.7,
           **kwargs
       ) -> List[Tuple[Dict[str, Any], float]]:
           """Search for semantically similar items."""
           pass
   ```

2. **Implement Redis memory backend** for short-term memory
3. **Implement Firestore memory backend** for mid/long-term memory
4. **Implement Vertex AI Vector Search backend** for semantic memory

## Phase 3: Layered Memory Implementation (Week 2)

1. **Implement layered memory system**:

   ```python
   # core/orchestrator/src/memory/layered_memory.py
   import logging
   from typing import Any, Dict, List, Optional, Tuple

   logger = logging.getLogger(__name__)

   class LayeredMemory:
       """
       Layered memory system with automatic migration between layers.

       This class provides a unified interface for accessing different memory layers,
       with automatic migration of data between layers based on relevance and age.
       """

       def __init__(self, layers: Dict[str, Any]):
           """Initialize layered memory with memory backends."""
           self.layers = layers
           logger.info(f"LayeredMemory initialized with layers: {list(layers.keys())}")

       async def store(self, key: str, value: Dict[str, Any], layer: str = "short_term") -> bool:
           """Store an item in the specified memory layer."""
           if layer not in self.layers:
               logger.error(f"Layer {layer} not found in memory layers")
               return False

           return await self.layers[layer].store(key, value)

       async def retrieve(self, key: str, layers: List[str] = None) -> Optional[Dict[str, Any]]:
           """
           Retrieve an item from memory, checking multiple layers if needed.

           Args:
               key: The key to retrieve
               layers: List of layers to check, in order (defaults to all layers)
           """
           # Default to all layers in order of speed (fastest first)
           if layers is None:
               layers = list(self.layers.keys())

           # Check each layer
           for layer_name in layers:
               if layer_name not in self.layers:
                   logger.warning(f"Layer {layer_name} not found in memory layers")
                   continue

               result = await self.layers[layer_name].retrieve(key)
               if result:
                   logger.debug(f"Retrieved item with key {key} from layer {layer_name}")
                   return result

           logger.debug(f"Item with key {key} not found in any layer")
           return None

       async def semantic_search(
           self,
           query_embedding: List[float],
           layer: str = "semantic",
           limit: int = 5,
           threshold: float = 0.7
       ) -> List[Tuple[Dict[str, Any], float]]:
           """
           Search for semantically similar items in the specified layer.

           Args:
               query_embedding: The embedding vector to search for
               layer: The layer to search in (defaults to "semantic")
               limit: Maximum number of results to return
               threshold: Minimum similarity score (0-1)
           """
           if layer not in self.layers:
               logger.error(f"Layer {layer} not found in memory layers")
               return []

           return await self.layers[layer].semantic_search(
               query_embedding=query_embedding,
               limit=limit,
               threshold=threshold
           )
   ```

2. **Create memory factory**:

   ```python
   # core/orchestrator/src/memory/factory.py
   from typing import Dict, Optional, Any

   from core.orchestrator.src.config.models import MemoryConfig, MemoryType
   from core.orchestrator.src.memory.layered_memory import LayeredMemory
   from core.orchestrator.src.memory.backends.redis_memory import RedisMemory
   from core.orchestrator.src.memory.backends.firestore_memory import FirestoreMemory
   from core.orchestrator.src.memory.backends.vertex_memory import VertexMemory
   from core.orchestrator.src.services.unified_registry import Service

   class MemoryFactory(Service):
       """Factory for creating memory systems based on configuration."""

       def __init__(self, redis_client=None, firestore_client=None, vertex_client=None):
           """Initialize with optional clients for different backends."""
           self.redis_client = redis_client
           self.firestore_client = firestore_client
           self.vertex_client = vertex_client

       def create_layered_memory(self, config: Dict[str, Any]) -> LayeredMemory:
           """Create a layered memory system from configuration."""
           layers = {}

           # Create memory layers based on configuration
           if "short_term" in config:
               layers["short_term"] = self._create_redis_memory(config["short_term"])

           if "mid_term" in config:
               layers["mid_term"] = self._create_firestore_memory(config["mid_term"])

           if "long_term" in config:
               layers["long_term"] = self._create_firestore_memory(config["long_term"])

           if "semantic" in config:
               layers["semantic"] = self._create_vertex_memory(config["semantic"])

           return LayeredMemory(layers)

       def create_memory_from_config(self, memory_config: MemoryConfig):
           """Create a memory system from a MemoryConfig."""
           if memory_config.memory_type == MemoryType.REDIS:
               return self._create_redis_memory({
                   "ttl": memory_config.ttl
               })
           elif memory_config.memory_type == MemoryType.FIRESTORE:
               return self._create_firestore_memory({
                   "collection": memory_config.table_name,
                   "ttl": memory_config.ttl
               })
           elif memory_config.memory_type == MemoryType.VERTEX_VECTOR:
               return self._create_vertex_memory({
                   "vector_dimension": memory_config.vector_dimension,
                   "ttl": memory_config.ttl
               })
           else:
               raise ValueError(f"Unsupported memory type: {memory_config.memory_type}")
   ```

## Phase 4: Agent Integration (Week 3)

1. **Create observable agent wrapper**:

   ```python
   # core/orchestrator/src/agents/observable_agent.py
   import logging
   import time
   from typing import Any, Dict, Optional

   from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
   from core.orchestrator.src.memory.factory import MemoryFactory

   logger = logging.getLogger(__name__)

   class ObservableAgent(Agent):
       """
       Observable agent wrapper with logging, metrics, and memory.

       This class wraps an agent and adds:
       - Logging of agent operations
       - Metrics collection
       - Memory integration
       """

       def __init__(
           self,
           wrapped_agent: Agent,
           agent_id: str,
           memory = None,
           log_level: str = "INFO",
           enable_metrics: bool = True,
           enable_tracing: bool = True
       ):
           """Initialize observable agent wrapper."""
           self.wrapped_agent = wrapped_agent
           self.agent_id = agent_id
           self.memory = memory
           self.log_level = log_level
           self.enable_metrics = enable_metrics
           self.enable_tracing = enable_tracing

           # Set up logging
           self.logger = logging.getLogger(f"agent.{agent_id}")
           self.logger.setLevel(log_level)

           logger.info(f"ObservableAgent initialized for agent {agent_id}")

       async def process(self, context: AgentContext) -> AgentResponse:
           """Process a request with observability and memory."""
           start_time = time.time()
           self.logger.info(f"Agent {self.agent_id} processing request")

           # Check memory for relevant information
           if self.memory and context.user_input:
               # Create embedding for semantic search
               embedding = await self._create_embedding(context.user_input)

               # Search memory for relevant information
               memory_results = await self.memory.semantic_search(
                   query_embedding=embedding,
                   limit=5,
                   threshold=0.7
               )

               # Augment context with memory results
               if memory_results:
                   memory_context = "\n".join([f"- {item[0]}" for item in memory_results])
                   context.metadata["memory_context"] = memory_context
                   self.logger.debug(f"Added memory context: {memory_context}")

           # Process with wrapped agent
           response = await self.wrapped_agent.process(context)

           # Store the interaction in memory
           if self.memory:
               await self.memory.store(
                   key=f"interaction:{context.conversation_id}:{time.time()}",
                   value={
                       "user_input": context.user_input,
                       "response": response.text
                   },
                   layer="short_term"
               )

           # Log and collect metrics
           elapsed_time = time.time() - start_time
           self.logger.info(f"Agent {self.agent_id} processed request in {elapsed_time:.2f}s")

           return response
   ```

2. **Create observable agent factory**:

   ```python
   # core/orchestrator/src/agents/observable_agent_factory.py
   from typing import Optional

   from core.orchestrator.src.agents.agent_base import Agent
   from core.orchestrator.src.agents.observable_agent import ObservableAgent
   from core.orchestrator.src.config.models import MemoryConfig
   from core.orchestrator.src.memory.factory import MemoryFactory

   class ObservableAgentFactory:
       """Factory for creating observable agents."""

       def __init__(self, memory_factory: Optional[MemoryFactory] = None):
           """Initialize with optional memory factory."""
           self.memory_factory = memory_factory

       def create_observable_agent(
           self,
           wrapped_agent: Agent,
           agent_id: str,
           memory_config: Optional[MemoryConfig] = None,
           log_level: str = "INFO",
           enable_metrics: bool = True,
           enable_tracing: bool = True
       ) -> ObservableAgent:
           """Create an observable agent with memory."""
           # Create memory if config is provided
           memory = None
           if memory_config and self.memory_factory:
               memory = self.memory_factory.create_memory_from_config(memory_config)

           # Create observable agent
           return ObservableAgent(
               wrapped_agent=wrapped_agent,
               agent_id=agent_id,
               memory=memory,
               log_level=log_level,
               enable_metrics=enable_metrics,
               enable_tracing=enable_tracing
           )
   ```

3. **Integrate with agent registry**:

   ```python
   # core/orchestrator/src/agents/registry_extension.py
   from core.orchestrator.src.agents.unified_agent_registry import AgentRegistry
   from core.orchestrator.src.agents.observable_agent_factory import ObservableAgentFactory
   from core.orchestrator.src.memory.factory import MemoryFactory
   from core.orchestrator.src.services.unified_registry import get_service

   def register_agent_with_memory(
       registry: AgentRegistry,
       agent,
       agent_type: str,
       capabilities: list,
       priority: int = 0,
       memory_config = None
   ):
       """Register an agent with memory capabilities."""
       # Get memory factory
       memory_factory = get_service(MemoryFactory)

       # Create observable agent factory
       observable_factory = ObservableAgentFactory(memory_factory=memory_factory)

       # Create observable agent with memory
       observable_agent = observable_factory.create_observable_agent(
           wrapped_agent=agent,
           agent_id=agent_type,
           memory_config=memory_config,
           log_level="INFO",
           enable_metrics=True,
           enable_tracing=True
       )

       # Register with agent registry
       registry.register_agent(
           agent=observable_agent,
           agent_type=agent_type,
           capabilities=capabilities,
           priority=priority
       )

       return observable_agent
   ```

## Phase 5: Testing and Deployment (Week 3-4)

1. **Create unit tests** for memory backends and layered memory
2. **Create integration tests** for agent memory integration
3. **Update CI/CD pipeline** to include memory tests
4. **Deploy to development environment** and test with real agents
5. **Monitor performance** and make adjustments as needed

## Next Steps

1. **Implement advanced memory features**:

   - Automatic summarization of long-term memory
   - Relevance scoring for memory retrieval
   - Memory compression techniques

2. **Enhance observability**:

   - Create custom dashboards in Cloud Monitoring
   - Set up alerts for memory usage and performance

3. **Optimize memory usage**:

   - Implement memory pruning strategies
   - Add memory indexing for faster retrieval

4. **Extend agent capabilities**:
   - Add support for multi-agent memory sharing
   - Implement collaborative memory for agent teams
