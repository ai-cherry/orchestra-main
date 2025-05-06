"""
Layered Memory Management for AI Orchestration System.

This module provides a layered memory management system that combines
different memory stores (short-term, long-term, semantic) to create a
comprehensive memory system for agents.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from pydantic import BaseModel, Field

from core.orchestrator.src.config.models import MemoryType, MemoryConfig
from core.orchestrator.src.agents.memory.manager import (
    MemoryStore, 
    MemoryQuery, 
    RedisMemoryStore, 
    FirestoreMemoryStore
)
from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class MemoryLayer(BaseModel):
    """
    Configuration for a memory layer.
    
    This class defines a layer in the layered memory system, including
    the store type, priority, and configuration.
    """
    name: str
    store_type: MemoryType
    priority: int
    config: Dict[str, Any] = Field(default_factory=dict)
    ttl: Optional[int] = None
    
    class Config:
        arbitrary_types_allowed = True


class LayeredMemoryManager:
    """
    Layered memory management system.
    
    This class provides a unified interface for managing memory across
    different stores, with support for layered retrieval, prioritization,
    and automatic TTL-based memory management.
    """
    
    def __init__(self, layers: Optional[List[MemoryLayer]] = None):
        """
        Initialize the layered memory manager.
        
        Args:
            layers: Optional list of memory layers to use
        """
        self.layers = layers or []
        self._stores: Dict[str, MemoryStore] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize all memory stores.
        
        This method initializes all configured memory stores, establishing
        connections to the underlying storage systems.
        
        Raises:
            ConnectionError: If connection to any storage system fails
        """
        for layer in self.layers:
            store = self._create_store(layer)
            await store.initialize()
            self._stores[layer.name] = store
        
        self._initialized = True
        logger.info(f"Initialized {len(self._stores)} memory stores")
    
    async def close(self) -> None:
        """
        Close all memory stores.
        
        This method closes all initialized memory stores, releasing any
        resources they hold.
        """
        for name, store in self._stores.items():
            await store.close()
            logger.debug(f"Closed memory store: {name}")
        
        self._stores = {}
        self._initialized = False
    
    def _create_store(self, layer: MemoryLayer) -> MemoryStore:
        """
        Create a memory store for a layer.
        
        Args:
            layer: The memory layer configuration
            
        Returns:
            An initialized memory store
            
        Raises:
            ValueError: If the store type is unknown
        """
        config = layer.config.copy()
        
        # Add TTL if specified
        if layer.ttl:
            config["ttl"] = layer.ttl
        
        # Create store based on type
        if layer.store_type == MemoryType.REDIS:
            return RedisMemoryStore(config)
        elif layer.store_type == MemoryType.FIRESTORE:
            return FirestoreMemoryStore(config)
        elif layer.store_type == MemoryType.IN_MEMORY:
            from core.orchestrator.src.agents.memory.in_memory import InMemoryStore
            return InMemoryStore(config)
        elif layer.store_type == MemoryType.PGVECTOR:
            from core.orchestrator.src.agents.memory.pgvector import PGVectorStore
            return PGVectorStore(config)
        elif layer.store_type == MemoryType.VERTEX_VECTOR:
            from core.orchestrator.src.agents.memory.vertex import VertexVectorMemoryStore
            return VertexVectorMemoryStore(config)
        else:
            raise ValueError(f"Unknown memory store type: {layer.store_type}")
    
    async def store(self, item: MemoryItem, layer_name: Optional[str] = None) -> str:
        """
        Store a memory item.
        
        Args:
            item: The memory item to store
            layer_name: Optional name of the layer to store in (if None, stores in all layers)
            
        Returns:
            The ID of the stored item
            
        Raises:
            ValueError: If the layer is unknown or the item is invalid
            ConnectionError: If storage fails due to connection issues
        """
        if not self._initialized:
            await self.initialize()
        
        # If no specific layer is specified, store in all layers
        if layer_name is None:
            # Store in all layers and return the ID from the highest priority layer
            highest_priority = -1
            item_id = None
            
            for layer in sorted(self.layers, key=lambda l: l.priority, reverse=True):
                store = self._stores[layer.name]
                current_id = await store.store(item)
                
                if layer.priority > highest_priority:
                    highest_priority = layer.priority
                    item_id = current_id
            
            if item_id is None:
                raise ValueError("No memory layers configured")
            
            return item_id
        
        # Store in a specific layer
        if layer_name not in self._stores:
            raise ValueError(f"Unknown memory layer: {layer_name}")
        
        store = self._stores[layer_name]
        return await store.store(item)
    
    async def retrieve(self, item_id: str, layer_name: Optional[str] = None) -> Optional[MemoryItem]:
        """
        Retrieve a memory item.
        
        Args:
            item_id: The ID of the item to retrieve
            layer_name: Optional name of the layer to retrieve from (if None, tries all layers)
            
        Returns:
            The retrieved memory item, or None if not found
            
        Raises:
            ValueError: If the layer is unknown
            ConnectionError: If retrieval fails due to connection issues
        """
        if not self._initialized:
            await self.initialize()
        
        # If a specific layer is specified, retrieve from that layer
        if layer_name is not None:
            if layer_name not in self._stores:
                raise ValueError(f"Unknown memory layer: {layer_name}")
            
            store = self._stores[layer_name]
            return await store.retrieve(item_id)
        
        # Try to retrieve from each layer in priority order
        for layer in sorted(self.layers, key=lambda l: l.priority, reverse=True):
            store = self._stores[layer.name]
            item = await store.retrieve(item_id)
            
            if item is not None:
                return item
        
        # Not found in any layer
        return None
    
    async def query(self, query: MemoryQuery, layer_name: Optional[str] = None) -> List[MemoryItem]:
        """
        Query for memory items.
        
        Args:
            query: The query parameters
            layer_name: Optional name of the layer to query (if None, queries all layers)
            
        Returns:
            A list of matching memory items
            
        Raises:
            ValueError: If the layer is unknown
            ConnectionError: If query fails due to connection issues
        """
        if not self._initialized:
            await self.initialize()
        
        # If a specific layer is specified, query that layer
        if layer_name is not None:
            if layer_name not in self._stores:
                raise ValueError(f"Unknown memory layer: {layer_name}")
            
            store = self._stores[layer_name]
            return await store.query(query)
        
        # Query all layers and combine results
        all_results = []
        tasks = []
        
        for layer in self.layers:
            store = self._stores[layer.name]
            task = asyncio.create_task(store.query(query))
            tasks.append((layer, task))
        
        # Wait for all queries to complete
        for layer, task in tasks:
            try:
                results = await task
                # Add layer info to metadata
                for item in results:
                    if item.metadata is None:
                        item.metadata = {}
                    item.metadata["memory_layer"] = layer.name
                
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error querying layer {layer.name}: {e}")
        
        # Sort by timestamp (newest first) and apply limit
        all_results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_results[:query.limit]
    
    async def delete(self, item_id: str, layer_name: Optional[str] = None) -> bool:
        """
        Delete a memory item.
        
        Args:
            item_id: The ID of the item to delete
            layer_name: Optional name of the layer to delete from (if None, deletes from all layers)
            
        Returns:
            True if the item was deleted from any layer, False otherwise
            
        Raises:
            ValueError: If the layer is unknown
            ConnectionError: If deletion fails due to connection issues
        """
        if not self._initialized:
            await self.initialize()
        
        # If a specific layer is specified, delete from that layer
        if layer_name is not None:
            if layer_name not in self._stores:
                raise ValueError(f"Unknown memory layer: {layer_name}")
            
            store = self._stores[layer_name]
            return await store.delete(item_id)
        
        # Delete from all layers
        deleted = False
        
        for layer_name, store in self._stores.items():
            try:
                if await store.delete(item_id):
                    deleted = True
            except Exception as e:
                logger.error(f"Error deleting from layer {layer_name}: {e}")
        
        return deleted
    
    async def clear(self, layer_name: Optional[str] = None) -> int:
        """
        Clear memory items.
        
        Args:
            layer_name: Optional name of the layer to clear (if None, clears all layers)
            
        Returns:
            The number of items cleared
            
        Raises:
            ValueError: If the layer is unknown
            ConnectionError: If clearing fails due to connection issues
        """
        if not self._initialized:
            await self.initialize()
        
        # If a specific layer is specified, clear that layer
        if layer_name is not None:
            if layer_name not in self._stores:
                raise ValueError(f"Unknown memory layer: {layer_name}")
            
            store = self._stores[layer_name]
            return await store.clear()
        
        # Clear all layers
        total_cleared = 0
        
        for layer_name, store in self._stores.items():
            try:
                cleared = await store.clear()
                total_cleared += cleared
            except Exception as e:
                logger.error(f"Error clearing layer {layer_name}: {e}")
        
        return total_cleared
    
    async def recall_relevant(self, text: str, limit: int = 10) -> List[MemoryItem]:
        """
        Recall memories relevant to the given text.
        
        This method is a convenience wrapper around query() that focuses on
        semantic relevance, using vector search when available.
        
        Args:
            text: The text to find relevant memories for
            limit: Maximum number of memories to return
            
        Returns:
            A list of relevant memory items
        """
        # First try semantic search in vector stores
        vector_results = []
        
        for layer in self.layers:
            if layer.store_type in [MemoryType.PGVECTOR, MemoryType.VERTEX_VECTOR]:
                store = self._stores[layer.name]
                query = MemoryQuery(text=text, limit=limit)
                
                try:
                    results = await store.query(query)
                    for item in results:
                        if item.metadata is None:
                            item.metadata = {}
                        item.metadata["memory_layer"] = layer.name
                        item.metadata["retrieval_type"] = "semantic"
                    
                    vector_results.extend(results)
                except Exception as e:
                    logger.error(f"Error querying vector layer {layer.name}: {e}")
        
        # If we have enough vector results, return them
        if len(vector_results) >= limit:
            return vector_results[:limit]
        
        # Otherwise, supplement with keyword search in other stores
        remaining = limit - len(vector_results)
        keyword_results = []
        
        for layer in self.layers:
            if layer.store_type not in [MemoryType.PGVECTOR, MemoryType.VERTEX_VECTOR]:
                store = self._stores[layer.name]
                query = MemoryQuery(text=text, limit=remaining)
                
                try:
                    results = await store.query(query)
                    for item in results:
                        if item.metadata is None:
                            item.metadata = {}
                        item.metadata["memory_layer"] = layer.name
                        item.metadata["retrieval_type"] = "keyword"
                    
                    keyword_results.extend(results)
                except Exception as e:
                    logger.error(f"Error querying layer {layer.name}: {e}")
        
        # Combine and return results
        combined_results = vector_results + keyword_results
        return combined_results[:limit]
    
    async def remember_conversation(
        self, 
        text: str, 
        user_id: str, 
        conversation_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Remember a conversation message.
        
        This is a convenience method for storing conversation messages with
        appropriate metadata.
        
        Args:
            text: The message text
            user_id: The ID of the user
            conversation_id: The ID of the conversation
            metadata: Additional metadata
            
        Returns:
            The ID of the stored memory item
        """
        # Create memory item
        item = MemoryItem(
            text_content=text,
            metadata={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "type": "conversation",
                **(metadata or {})
            }
        )
        
        # Store in all layers
        return await self.store(item)
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[MemoryItem]:
        """
        Get conversation history.
        
        This is a convenience method for retrieving conversation messages.
        
        Args:
            conversation_id: The ID of the conversation
            limit: Maximum number of messages to return
            
        Returns:
            A list of conversation messages
        """
        query = MemoryQuery(
            metadata_filters={"conversation_id": conversation_id, "type": "conversation"},
            limit=limit
        )
        
        return await self.query(query)


def create_default_memory_manager() -> LayeredMemoryManager:
    """
    Create a default memory manager with standard layers.
    
    This function creates a memory manager with three layers:
    - Short-term memory (Redis)
    - Long-term memory (Firestore)
    - Semantic memory (Vertex AI Vector Search)
    
    Returns:
        A configured memory manager
    """
    layers = [
        MemoryLayer(
            name="short_term",
            store_type=MemoryType.REDIS,
            priority=3,  # Highest priority
            ttl=60 * 60 * 24,  # 1 day TTL
            config={
                "host": "localhost",
                "port": 6379,
                "db": 0
            }
        ),
        MemoryLayer(
            name="long_term",
            store_type=MemoryType.FIRESTORE,
            priority=2,
            config={
                "collection": "memory",
                "project": "cherry-ai-project"
            }
        ),
        MemoryLayer(
            name="semantic",
            store_type=MemoryType.VERTEX_VECTOR,
            priority=1,
            config={
                "project": "cherry-ai-project",
                "location": "us-west4",
                "index_name": "memory-index",
                "embedding_model": "textembedding-gecko@latest"
            }
        )
    ]
    
    return LayeredMemoryManager(layers)


# Singleton instance
_memory_manager: Optional[LayeredMemoryManager] = None

async def get_memory_manager() -> LayeredMemoryManager:
    """
    Get the global memory manager instance.
    
    This function returns the global memory manager instance, initializing
    it if necessary.
    
    Returns:
        The global memory manager
    """
    global _memory_manager
    
    if _memory_manager is None:
        _memory_manager = create_default_memory_manager()
        await _memory_manager.initialize()
    
    return _memory_manager