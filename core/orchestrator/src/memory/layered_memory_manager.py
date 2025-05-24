"""
Layered Memory Manager for AI Orchestra
Provides a unified interface for managing short-term, mid-term, and long-term memory
with semantic search capabilities using Redis, Firestore, and Vertex AI Vector Search.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import aioredis
from google.cloud import aiplatform, firestore

from core.orchestrator.src.config.loader import get_settings
from core.orchestrator.src.memory.models import (
    MemoryEntry,
    MemorySearchResult,
    MemoryType,
)

logger = logging.getLogger(__name__)


class LayeredMemoryManager:
    """
    Manages different memory layers (short-term, mid-term, long-term) with semantic search.

    Memory Layers:
    - Short-term: Redis (fast, ephemeral, high-frequency access)
    - Mid-term: Firestore (persistent, structured, moderate access)
    - Long-term: Firestore + Vector Search (persistent, semantic search)
    """

    def __init__(
        self,
        agent_id: str,
        conversation_id: Optional[str] = None,
        redis_url: Optional[str] = None,
        project_id: Optional[str] = None,
        vector_index_endpoint: Optional[str] = None,
        vector_deployed_index_id: Optional[str] = None,
    ):
        """Initialize the layered memory manager."""
        self.agent_id = agent_id
        self.conversation_id = conversation_id or str(uuid.uuid4())

        # Load settings
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.region = settings.gcp_region

        # Initialize Redis for short-term memory
        self.redis_url = redis_url or f"redis://{settings.redis_host}:{settings.redis_port}"
        self.redis_pool = None  # Will be initialized in connect()

        # Initialize Firestore for mid-term and long-term memory
        self.firestore_client = firestore.Client(project=self.project_id)

        # Initialize Vector Search for semantic search
        self.vector_index_endpoint = vector_index_endpoint
        self.vector_deployed_index_id = vector_deployed_index_id
        self.vector_search_initialized = False

        # Memory expiration settings (in seconds)
        self.short_term_expiry = 60 * 60  # 1 hour
        self.mid_term_expiry = 60 * 60 * 24 * 7  # 1 week
        # Long-term memory doesn't expire

    async def connect(self):
        """Connect to Redis and initialize Vector Search."""
        # Connect to Redis
        self.redis_pool = await aioredis.from_url(self.redis_url, decode_responses=True)

        # Initialize Vector Search if endpoint is provided
        if self.vector_index_endpoint and self.vector_deployed_index_id:
            aiplatform.init(project=self.project_id, location=self.region)
            self.vector_search_initialized = True

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_pool:
            await self.redis_pool.close()

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """
        Store a memory in the appropriate storage layer based on memory_type.

        Args:
            content: The content to store
            memory_type: Type of memory (SHORT_TERM, MID_TERM, LONG_TERM)
            metadata: Additional metadata for the memory
            embedding: Vector embedding for semantic search (required for LONG_TERM)
            memory_id: Optional ID for the memory (if not provided, a UUID will be generated)

        Returns:
            The ID of the stored memory
        """
        memory_id = memory_id or str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        memory_entry = MemoryEntry(
            id=memory_id,
            agent_id=self.agent_id,
            conversation_id=self.conversation_id,
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
            timestamp=timestamp,
            embedding=embedding,
        )

        if memory_type == MemoryType.SHORT_TERM:
            # Store in Redis with expiration
            await self._store_in_redis(memory_entry)

        elif memory_type == MemoryType.MID_TERM:
            # Store in Firestore with mid-term expiration
            self._store_in_firestore(memory_entry, self.mid_term_expiry)

        elif memory_type == MemoryType.LONG_TERM:
            # Ensure embedding is provided for long-term memory
            if not embedding:
                raise ValueError("Embedding is required for LONG_TERM memory")

            # Store in Firestore without expiration
            self._store_in_firestore(memory_entry)

            # Store embedding in Vector Search if initialized
            if self.vector_search_initialized:
                await self._store_in_vector_search(memory_entry)

        return memory_id

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve a memory by ID, checking all storage layers.

        Args:
            memory_id: The ID of the memory to retrieve

        Returns:
            The memory entry if found, None otherwise
        """
        # Check Redis first (fastest)
        memory = await self._retrieve_from_redis(memory_id)
        if memory:
            return memory

        # Check Firestore
        memory = self._retrieve_from_firestore(memory_id)
        return memory

    async def search_memory(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        embedding: Optional[List[float]] = None,
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        Search for memories across all storage layers.

        Args:
            query: Text query for searching
            memory_types: Types of memory to search (defaults to all)
            embedding: Vector embedding for semantic search
            limit: Maximum number of results to return
            metadata_filter: Filter results by metadata fields

        Returns:
            List of memory search results with relevance scores
        """
        memory_types = memory_types or [
            MemoryType.SHORT_TERM,
            MemoryType.MID_TERM,
            MemoryType.LONG_TERM,
        ]

        results = []

        # Search short-term memory in Redis
        if MemoryType.SHORT_TERM in memory_types:
            short_term_results = await self._search_in_redis(query, limit, metadata_filter)
            results.extend(short_term_results)

        # Search mid-term memory in Firestore
        if MemoryType.MID_TERM in memory_types:
            mid_term_results = self._search_in_firestore(query, MemoryType.MID_TERM, limit, metadata_filter)
            results.extend(mid_term_results)

        # Search long-term memory with semantic search
        if MemoryType.LONG_TERM in memory_types:
            # Use vector search if embedding is provided and vector search is initialized
            if embedding and self.vector_search_initialized:
                long_term_results = await self._search_in_vector_search(embedding, limit, metadata_filter)
                results.extend(long_term_results)
            else:
                # Fall back to text search in Firestore
                long_term_results = self._search_in_firestore(query, MemoryType.LONG_TERM, limit, metadata_filter)
                results.extend(long_term_results)

        # Sort by relevance score and limit results
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:limit]

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory from all storage layers.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            True if the memory was deleted, False otherwise
        """
        # Try to delete from Redis
        redis_deleted = await self._delete_from_redis(memory_id)

        # Try to delete from Firestore
        firestore_deleted = self._delete_from_firestore(memory_id)

        # If vector search is initialized, try to delete from there too
        vector_deleted = False
        if self.vector_search_initialized:
            vector_deleted = await self._delete_from_vector_search(memory_id)

        return redis_deleted or firestore_deleted or vector_deleted

    # Private methods for Redis operations

    async def _store_in_redis(self, memory: MemoryEntry) -> None:
        """Store a memory in Redis with expiration."""
        key = f"memory:{memory.id}"
        value = memory.model_dump_json()

        # Store in Redis with expiration
        await self.redis_pool.set(key, value, ex=self.short_term_expiry)

        # Add to agent's memory set
        await self.redis_pool.sadd(f"agent:{self.agent_id}:memories", memory.id)

        # Add to conversation's memory set if conversation_id is provided
        if self.conversation_id:
            await self.redis_pool.sadd(f"conversation:{self.conversation_id}:memories", memory.id)

    async def _retrieve_from_redis(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory from Redis."""
        key = f"memory:{memory_id}"
        value = await self.redis_pool.get(key)

        if value:
            return MemoryEntry.model_validate_json(value)

        return None

    async def _search_in_redis(
        self, query: str, limit: int, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """
        Search for memories in Redis.
        This is a simple implementation that scans all memories for the agent/conversation.
        """
        results = []

        # Get all memory IDs for the agent or conversation
        if self.conversation_id:
            memory_ids = await self.redis_pool.smembers(f"conversation:{self.conversation_id}:memories")
        else:
            memory_ids = await self.redis_pool.smembers(f"agent:{self.agent_id}:memories")

        # Retrieve each memory and check if it matches the query
        for memory_id in memory_ids:
            memory = await self._retrieve_from_redis(memory_id)
            if not memory:
                continue

            # Apply metadata filter if provided
            if metadata_filter and not self._matches_metadata_filter(memory.metadata, metadata_filter):
                continue

            # Simple text matching (could be improved)
            if query.lower() in memory.content.lower():
                # Calculate a simple relevance score based on string matching
                relevance = self._calculate_text_relevance(query, memory.content)

                results.append(
                    MemorySearchResult(
                        memory=memory,
                        relevance=relevance,
                    )
                )

        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:limit]

    async def _delete_from_redis(self, memory_id: str) -> bool:
        """Delete a memory from Redis."""
        key = f"memory:{memory_id}"

        # Check if memory exists
        exists = await self.redis_pool.exists(key)
        if not exists:
            return False

        # Delete the memory
        await self.redis_pool.delete(key)

        # Remove from agent's memory set
        await self.redis_pool.srem(f"agent:{self.agent_id}:memories", memory_id)

        # Remove from conversation's memory set if conversation_id is provided
        if self.conversation_id:
            await self.redis_pool.srem(f"conversation:{self.conversation_id}:memories", memory_id)

        return True

    # Private methods for Firestore operations

    def _store_in_firestore(self, memory: MemoryEntry, ttl_seconds: Optional[int] = None) -> None:
        """Store a memory in Firestore with optional TTL."""
        # Convert memory to dict for Firestore
        memory_dict = memory.model_dump(exclude={"embedding"})

        # Add TTL if provided
        if ttl_seconds:
            memory_dict["expiry_time"] = datetime.utcnow().timestamp() + ttl_seconds

        # Store in Firestore
        self.firestore_client.collection("memories").document(memory.id).set(memory_dict)

    def _retrieve_from_firestore(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory from Firestore."""
        doc_ref = self.firestore_client.collection("memories").document(memory_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Convert Firestore document to MemoryEntry
        memory_data = doc.to_dict()

        # Check if memory has expired
        if "expiry_time" in memory_data:
            if memory_data["expiry_time"] < datetime.utcnow().timestamp():
                # Memory has expired, delete it
                doc_ref.delete()
                return None

            # Remove expiry_time from data before converting to MemoryEntry
            del memory_data["expiry_time"]

        return MemoryEntry(**memory_data)

    def _search_in_firestore(
        self,
        query: str,
        memory_type: MemoryType,
        limit: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        Search for memories in Firestore.
        This is a simple implementation that filters by memory_type and agent_id.
        """
        results = []

        # Build query
        firestore_query = (
            self.firestore_client.collection("memories")
            .where("memory_type", "==", memory_type.value)
            .where("agent_id", "==", self.agent_id)
        )

        # Add conversation_id filter if provided
        if self.conversation_id:
            firestore_query = firestore_query.where("conversation_id", "==", self.conversation_id)

        # Execute query
        docs = firestore_query.limit(limit * 2).stream()  # Get more than needed for filtering

        # Process results
        for doc in docs:
            memory_data = doc.to_dict()

            # Check if memory has expired
            if "expiry_time" in memory_data:
                if memory_data["expiry_time"] < datetime.utcnow().timestamp():
                    # Memory has expired, delete it
                    doc.reference.delete()
                    continue

                # Remove expiry_time from data before converting to MemoryEntry
                del memory_data["expiry_time"]

            # Apply metadata filter if provided
            if metadata_filter and not self._matches_metadata_filter(memory_data.get("metadata", {}), metadata_filter):
                continue

            # Simple text matching (could be improved)
            if query.lower() in memory_data.get("content", "").lower():
                # Calculate a simple relevance score based on string matching
                relevance = self._calculate_text_relevance(query, memory_data.get("content", ""))

                memory = MemoryEntry(**memory_data)
                results.append(
                    MemorySearchResult(
                        memory=memory,
                        relevance=relevance,
                    )
                )

        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:limit]

    def _delete_from_firestore(self, memory_id: str) -> bool:
        """Delete a memory from Firestore."""
        doc_ref = self.firestore_client.collection("memories").document(memory_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        return True

    # Private methods for Vector Search operations

    async def _store_in_vector_search(self, memory: MemoryEntry) -> None:
        """
        Store a memory's embedding in Vector Search.
        This is a simplified implementation that assumes the Vector Search index
        is updated in batch mode. In a real implementation, you would need to
        upload the embeddings to a GCS bucket and then update the index.
        """
        if not self.vector_search_initialized or not memory.embedding:
            return

        # In a real implementation, you would store the embedding in a format
        # compatible with Vertex AI Vector Search batch updates
        logger.info(f"Storing embedding for memory {memory.id} in Vector Search")

    async def _search_in_vector_search(
        self,
        embedding: List[float],
        limit: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        Search for memories in Vector Search using embedding.
        """
        if not self.vector_search_initialized:
            return []

        # Create a MatchingEngineIndexEndpoint client
        endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=self.vector_index_endpoint)

        # Query the index
        response = endpoint.find_neighbors(
            deployed_index_id=self.vector_deployed_index_id,
            queries=[embedding],
            num_neighbors=limit,
        )

        results = []

        # Process results
        for idx, neighbor in enumerate(response[0]):
            memory_id = neighbor.id
            distance = neighbor.distance

            # Retrieve the full memory from Firestore
            memory = self._retrieve_from_firestore(memory_id)
            if not memory:
                continue

            # Apply metadata filter if provided
            if metadata_filter and not self._matches_metadata_filter(memory.metadata, metadata_filter):
                continue

            # Convert distance to relevance score (1.0 is most relevant)
            # For cosine distance, relevance = 1 - distance
            relevance = 1.0 - distance

            results.append(
                MemorySearchResult(
                    memory=memory,
                    relevance=relevance,
                )
            )

        return results

    async def _delete_from_vector_search(self, memory_id: str) -> bool:
        """
        Delete a memory's embedding from Vector Search.
        This is a simplified implementation. In a real implementation,
        you would need to remove the embedding from the index.
        """
        if not self.vector_search_initialized:
            return False

        # In a real implementation, you would remove the embedding from the index
        logger.info(f"Deleting embedding for memory {memory_id} from Vector Search")
        return True

    # Utility methods

    def _matches_metadata_filter(self, metadata: Dict[str, Any], metadata_filter: Dict[str, Any]) -> bool:
        """Check if metadata matches the filter."""
        for key, value in metadata_filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def _calculate_text_relevance(self, query: str, content: str) -> float:
        """
        Calculate a simple relevance score based on text matching.
        This is a very basic implementation and could be improved.
        """
        query_lower = query.lower()
        content_lower = content.lower()

        # Check if query is an exact match
        if query_lower == content_lower:
            return 1.0

        # Check if content contains the query
        if query_lower in content_lower:
            # Calculate relevance based on the length of the match relative to content
            return len(query) / len(content)

        # Calculate word overlap
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())

        if not query_words or not content_words:
            return 0.0

        # Jaccard similarity
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)

        return len(intersection) / len(union)
