"""
Memory Manager for AI Orchestration System.

This module provides the main MemoryManager class which acts as a factory
and orchestrator for different concrete memory implementations.
It selects and delegates operations to the appropriate backend
(e.g., Firestore V1, Firestore V2, etc.) based on configuration.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union, TypedDict

from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig
from packages.shared.src.memory.memory_interface import MemoryInterface
from .memory_types import MemoryHealth
from packages.shared.src.memory.base_memory_manager import BaseMemoryManager
from packages.shared.src.memory.concrete_memory_manager import FirestoreV1MemoryManager
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
from packages.shared.src.storage.firestore.v2.resilient_adapter import ResilientFirestoreAdapter
from packages.shared.src.memory.monitoring import MemoryMonitoring
from packages.shared.src.memory.vertex_vector_search import VertexVectorSearch

# Set up logger
logger = logging.getLogger(__name__)

class MemoryManager(MemoryInterface): # The main MemoryManager should implement the interface
    """
    Main Memory Manager class.

    This class acts as a factory and orchestrator for different concrete
    memory implementations, delegating operations based on configuration.
    """
    def __init__(
        self,
        memory_backend_type: str = "firestore_v1",  # Configuration parameter
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_password: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour default
        connection_pool_size: int = 10,  # For V2 connection pooling
        namespace: str = "default",  # For V2 namespace
        log_level: int = logging.INFO,  # For V2 logging
        use_resilient_adapter: bool = True,  # Whether to use the resilient adapter
        use_vertex_vector_search: bool = False,  # Whether to use Vertex Vector Search
        vertex_location: str = "us-central1",  # GCP region for Vertex AI
        vertex_index_endpoint_id: Optional[str] = None,  # Vertex Vector Search index endpoint ID
        vertex_index_id: Optional[str] = None,  # Vertex Vector Search index ID
        embedding_dimension: int = 768,  # Dimension of embedding vectors
        enable_monitoring: bool = True,  # Whether to enable monitoring
    ):
        """
        Initialize the main memory manager.

        Args:
            memory_backend_type: The type of memory backend to use (e.g., "firestore_v1", "firestore_v2").
            project_id: Optional Google Cloud project ID for Firestore.
            credentials_json: Optional JSON string for Firestore credentials.
            credentials_path: Optional path for Firestore credentials file.
            redis_host: Optional Redis host.
            redis_port: Optional Redis port.
            redis_password: Optional Redis password.
            cache_ttl: Cache TTL in seconds for Redis.
            connection_pool_size: Size of connection pool for V2 backend.
            namespace: Namespace for V2 backend.
            log_level: Logging level for V2 backend.
        """
        self._backend: BaseMemoryManager  # The chosen concrete backend

        if memory_backend_type == "firestore_v1":
            # Need to instantiate FirestoreMemoryManager first, then pass it to FirestoreV1MemoryManager
            firestore_v1_storage = FirestoreMemoryManager(
                project_id=project_id,
                credentials_json=credentials_json,
                credentials_path=credentials_path,
            )
            self._backend = FirestoreV1MemoryManager(
                firestore_memory=firestore_v1_storage,
                redis_host=redis_host,
                redis_port=redis_port,
                redis_password=redis_password,
                cache_ttl=cache_ttl,
            )
        elif memory_backend_type == "firestore_v2":
            # Initialize monitoring if enabled
            monitoring = None
            if enable_monitoring and project_id:
                monitoring = MemoryMonitoring(
                    project_id=project_id,
                    enabled=True,
                    metric_prefix="custom.googleapis.com/ai_orchestra/memory",
                )
                logger.info("Memory monitoring enabled")
                
            # Initialize Vertex Vector Search if enabled
            vector_search = None
            if use_vertex_vector_search and project_id:
                vector_search = VertexVectorSearch(
                    project_id=project_id,
                    location=vertex_location,
                    index_endpoint_id=vertex_index_endpoint_id,
                    index_id=vertex_index_id,
                    embedding_dimension=embedding_dimension,
                    monitoring=monitoring,
                    enabled=use_vertex_vector_search,
                )
                logger.info("Vertex Vector Search integration enabled")
                
            # Create the base V2 implementation
            firestore_v2 = FirestoreMemoryManagerV2(
                project_id=project_id,
                credentials_json=credentials_json,
                credentials_path=credentials_path,
                namespace=namespace,
                log_level=log_level,
            )
            
            # Wrap with resilient adapter if enabled
            if use_resilient_adapter:
                self._backend = ResilientFirestoreAdapter(
                    firestore_adapter=firestore_v2,
                    circuit_breaker_failure_threshold=5,
                    circuit_breaker_recovery_timeout=30.0,
                    circuit_breaker_reset_timeout=60.0,
                )
                logger.info("Using ResilientFirestoreAdapter with circuit breaker protection")
            else:
                self._backend = firestore_v2
                logger.info("Using FirestoreMemoryManagerV2 with improved async support")
                
            # Store references to components for initialization
            self._monitoring = monitoring
            self._vector_search = vector_search
        else:
            raise ValueError(f"Unknown memory backend type: {memory_backend_type}")

        logger.info(f"MemoryManager initialized with backend: {memory_backend_type}")

    async def initialize(self) -> None:
        """Initialize the selected memory backend and related components."""
        # Initialize the backend first
        await self._backend.initialize()
        
        # Initialize monitoring if available
        if hasattr(self, '_monitoring') and self._monitoring:
            logger.info("Initializing memory monitoring")
            # Monitoring doesn't require async initialization
            
        # Initialize vector search if available
        if hasattr(self, '_vector_search') and self._vector_search:
            logger.info("Initializing Vertex Vector Search")
            await self._vector_search.initialize()
        
    # Synchronous wrapper for initialize to handle sync/async mismatch
    def initialize_sync(self) -> None:
        """
        Initialize the selected memory backend synchronously.
        
        This is a wrapper around the async initialize method for use in synchronous contexts.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if one doesn't exist
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(self.initialize())

    async def close(self) -> None:
        """Close the selected memory backend and related components."""
        # Close the backend first
        await self._backend.close()
        
        # Close vector search if available
        if hasattr(self, '_vector_search') and self._vector_search:
            logger.info("Closing Vertex Vector Search")
            await self._vector_search.close()
        
    # Synchronous wrapper for close to handle sync/async mismatch
    def close_sync(self) -> None:
        """
        Close the selected memory backend synchronously.
        
        This is a wrapper around the async close method for use in synchronous contexts.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if one doesn't exist
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(self.close())

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage via the selected backend.
        
        If Vertex Vector Search is enabled, the item will also be indexed there.
        """
        # Add to backend first
        item_id = await self._backend.add_memory_item(item)
        
        # Index in Vertex Vector Search if available and item has embedding
        if (hasattr(self, '_vector_search') and
            self._vector_search and
            self._vector_search.enabled and
            item.embedding):
            try:
                await self._vector_search.index_memory_item(item)
            except Exception as e:
                logger.error(f"Failed to index memory item in Vertex Vector Search: {e}")
                # Don't re-raise, as the primary operation (storing in backend) succeeded
                
        return item_id

    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory item by ID via the selected backend."""
        return await self._backend.get_memory_item(item_id)

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """Retrieve conversation history for a user via the selected backend."""
        return await self._backend.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            filters=filters,
        )

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search via the selected backend or Vertex Vector Search.
        
        If Vertex Vector Search is enabled and initialized, it will be used for
        semantic search. Otherwise, the backend's semantic search will be used.
        """
        # Use Vertex Vector Search if available
        if hasattr(self, '_vector_search') and self._vector_search and self._vector_search.enabled:
            try:
                # Perform search using Vertex Vector Search
                results_with_scores = await self._vector_search.search(
                    user_id=user_id,
                    query_embedding=query_embedding,
                    persona_context=persona_context,
                    top_k=top_k,
                )
                
                # Extract just the items (without scores)
                if results_with_scores:
                    return [item for item, _ in results_with_scores]
                    
                # Fall back to backend if no results
                logger.debug("No results from Vertex Vector Search, falling back to backend")
            except Exception as e:
                logger.error(f"Error using Vertex Vector Search, falling back to backend: {e}")
                
        # Use the backend's semantic search
        return await self._backend.semantic_search(
            user_id=user_id,
            query_embedding=query_embedding,
            persona_context=persona_context,
            top_k=top_k,
        )

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """Store raw agent data via the selected backend."""
        return await self._backend.add_raw_agent_data(data)

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """Check if a memory item already exists via the selected backend."""
        return await self._backend.check_duplicate(item)

    async def cleanup_expired_items(self) -> int:
        """Remove expired items via the selected backend."""
        return await self._backend.cleanup_expired_items()

    async def health_check(self) -> MemoryHealth:
        """
        Check the health of the memory system.
        
        This includes the backend, Vertex Vector Search, and monitoring components.
        """
        # Get backend health
        health = await self._backend.health_check()
        
        # Add Vertex Vector Search health if available
        if hasattr(self, '_vector_search') and self._vector_search:
            health["vector_search_enabled"] = self._vector_search.enabled
            health["vector_search_initialized"] = self._vector_search._initialized
            health["vector_search_fallback"] = self._vector_search._fallback_to_custom
            
        # Add monitoring health if available
        if hasattr(self, '_monitoring') and self._monitoring:
            health["monitoring_enabled"] = self._monitoring.enabled
            
        return health

    # Add other methods from MemoryInterface here, delegating to self._backend
    # async def add_message_to_conversation(self, conversation_id: str, message: dict):
    #     await self._backend.add_message_to_conversation(conversation_id, message)
