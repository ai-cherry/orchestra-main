#!/usr/bin/env python3
"""
firestore_memory_manager_v2.py - Performance-Optimized Firestore Memory Manager

This module implements a performance-optimized Firestore V2 memory manager with
async operations, batching, connection pooling, and caching for improved performance.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

# Import GCP libraries
try:
    from google.api_core.exceptions import (
        DeadlineExceeded,
        ServiceUnavailable,
    )
    from google.api_core.retry import Retry
    from google.cloud import firestore
except ImportError:
    logging.warning("Google Cloud Firestore library not installed. Install with: pip install google-cloud-firestore")

# Import from relative paths
from ..interfaces.memory_manager import IMemoryManager
from ..models.memory import MemoryEntry, MemoryType
from ..utils.gcp_auth import GCPAuth

logger = logging.getLogger(__name__)


class BatchOperation:
    """Represents a batch operation for Firestore."""

    def __init__(self, operation_type: str, key: str, data: Optional[Any] = None):
        """Initialize a batch operation.

        Args:
            operation_type: Type of operation ('set', 'update', 'delete')
            key: Document key
            data: Data for set/update operations (None for delete)
        """
        self.operation_type = operation_type
        self.key = key
        self.data = data
        self.timestamp = time.time()


class FirestoreMemoryManagerV2(IMemoryManager):
    """Performance-optimized Firestore V2 memory manager with async operations."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        collection_prefix: str = "memory",
        cache_ttl_seconds: int = 300,
        batch_size: int = 500,
        batch_flush_interval: float = 1.0,
        max_cache_size: int = 1000,
        retry_attempts: int = 3,
    ):
        """Initialize the Firestore memory manager.

        Args:
            project_id: Optional Google Cloud project ID
            collection_prefix: Prefix for Firestore collections
            cache_ttl_seconds: TTL for cached items in seconds
            batch_size: Maximum batch size for Firestore operations
            batch_flush_interval: Interval in seconds to flush batch operations
            max_cache_size: Maximum number of items to keep in cache
            retry_attempts: Number of retry attempts for failed operations
        """
        self.project_id = project_id
        self.collection_prefix = collection_prefix
        self.cache_ttl_seconds = cache_ttl_seconds
        self.batch_size = batch_size
        self.batch_flush_interval = batch_flush_interval
        self.max_cache_size = max_cache_size
        self.retry_attempts = retry_attempts

        # Client and initialization state
        self._client = None
        self._async_client = None
        self._initialized = False

        # Memory cache
        self._cache: Dict[str, MemoryEntry] = {}
        self._cache_ttl: Dict[str, float] = {}

        # Batch operations
        self._batch_operations: List[BatchOperation] = []
        self._batch_lock = asyncio.Lock()
        self._last_batch_flush = time.time()
        self._batch_processor_task = None

        # Retry strategy
        self._retry_strategy = None

        logger.info(f"Initialized FirestoreMemoryManagerV2 with collection prefix: {collection_prefix}")

    async def initialize(self) -> bool:
        """Initialize the memory manager.

        Returns:
            bool: True if initialization was successful
        """
        if self._initialized:
            return True

        try:
            # Get authenticated clients
            gcp_auth = GCPAuth.get_instance()
            self._client = gcp_auth.get_firestore_client()
            self._async_client = gcp_auth.get_firestore_async_client()

            # Use project ID from auth if not provided
            if not self.project_id:
                self.project_id = gcp_auth.get_project_id()

            # Configure retry strategy
            self._retry_strategy = Retry(
                initial=0.1,
                maximum=10.0,
                multiplier=1.5,
                predicate=lambda e: isinstance(
                    e,
                    (
                        DeadlineExceeded,
                        ServiceUnavailable,
                        firestore.exceptions.Aborted,
                        firestore.exceptions.InternalServerError,
                    ),
                ),
            )

            # Start background batch processor
            self._batch_processor_task = asyncio.create_task(self._process_batch_operations())

            self._initialized = True
            logger.info(f"Firestore memory manager initialized for project: {self.project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Firestore memory manager: {e}")
            return False

    def _get_collection_name(self, memory_type: Optional[MemoryType] = None) -> str:
        """Get the collection name based on memory type.

        Args:
            memory_type: Optional memory type to use for collection name

        Returns:
            str: Collection name
        """
        if memory_type:
            return f"{self.collection_prefix}_{memory_type.value}"
        return self.collection_prefix

    async def create_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Create a new memory entry.

        Args:
            key: The key for the memory entry
            entry: The memory entry to create
            source_tool: The tool that created the entry

        Returns:
            bool: True if the operation was successful
        """
        if not self._initialized:
            await self.initialize()

        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.update_hash()

        # Add to cache
        self._cache[key] = entry
        self._cache_ttl[key] = time.time() + self.cache_ttl_seconds

        # Manage cache size
        if len(self._cache) > self.max_cache_size:
            self._prune_cache()

        # Add to batch operations
        self._get_collection_name(entry.memory_type)
        async with self._batch_lock:
            self._batch_operations.append(BatchOperation("set", key, entry.to_dict()))

            # Flush if batch is large enough
            if len(self._batch_operations) >= self.batch_size:
                await self._flush_batch_operations()

        logger.debug(f"Created memory entry: {key} from {source_tool}")
        return True

    async def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool.

        Args:
            key: The key for the memory entry
            tool: The tool requesting the entry

        Returns:
            Optional[MemoryEntry]: The memory entry if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        # Check cache first
        if key in self._cache:
            # Check if cached item is still valid
            if time.time() < self._cache_ttl.get(key, 0):
                entry = self._cache[key]
                entry.update_access()
                logger.debug(f"Cache hit for memory entry: {key}")
                return entry
            else:
                # Remove expired item from cache
                del self._cache[key]
                del self._cache_ttl[key]

        # Try all collections if we don't know the memory type
        collections_to_try = [self._get_collection_name(memory_type) for memory_type in MemoryType]
        collections_to_try.append(self.collection_prefix)  # Try default collection too

        # Get from Firestore
        for collection_name in collections_to_try:
            try:
                doc_ref = self._async_client.collection(collection_name).document(key)
                doc = await doc_ref.get()

                if doc.exists:
                    # Convert to MemoryEntry
                    data = doc.to_dict()
                    entry = MemoryEntry.from_dict(data)

                    # Check if expired
                    if entry.is_expired():
                        # Delete expired entry
                        asyncio.create_task(self.delete_memory(key, tool))
                        logger.debug(f"Expired memory entry: {key}")
                        return None

                    # Update access metadata
                    entry.update_access()

                    # Add to cache
                    self._cache[key] = entry
                    self._cache_ttl[key] = time.time() + self.cache_ttl_seconds

                    logger.debug(f"Retrieved memory entry: {key} for {tool}")
                    return entry
            except Exception as e:
                logger.warning(f"Error getting memory {key} from {collection_name}: {e}")
                continue

        logger.debug(f"Memory entry not found: {key}")
        return None

    async def update_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Update an existing memory entry.

        Args:
            key: The key for the memory entry
            entry: The updated memory entry
            source_tool: The tool that updated the entry

        Returns:
            bool: True if the operation was successful
        """
        if not self._initialized:
            await self.initialize()

        # Check if entry exists
        existing_entry = await self.get_memory(key, source_tool)
        if not existing_entry:
            # Create new entry if it doesn't exist
            return await self.create_memory(key, entry, source_tool)

        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.metadata.version = existing_entry.metadata.version + 1
        entry.update_hash()

        # Update cache
        self._cache[key] = entry
        self._cache_ttl[key] = time.time() + self.cache_ttl_seconds

        # Add to batch operations
        self._get_collection_name(entry.memory_type)
        async with self._batch_lock:
            self._batch_operations.append(BatchOperation("set", key, entry.to_dict()))

            # Flush if batch is large enough
            if len(self._batch_operations) >= self.batch_size:
                await self._flush_batch_operations()

        logger.debug(f"Updated memory entry: {key} from {source_tool}")
        return True

    async def delete_memory(self, key: str, source_tool: str) -> bool:
        """Delete a memory entry.

        Args:
            key: The key for the memory entry
            source_tool: The tool that deleted the entry

        Returns:
            bool: True if the operation was successful
        """
        if not self._initialized:
            await self.initialize()

        # Remove from cache
        if key in self._cache:
            del self._cache[key]
        if key in self._cache_ttl:
            del self._cache_ttl[key]

        # Add to batch operations for all possible collections
        # (since we don't know which collection it's in)
        collections_to_try = [self._get_collection_name(memory_type) for memory_type in MemoryType]
        collections_to_try.append(self.collection_prefix)  # Try default collection too

        async with self._batch_lock:
            for collection_name in collections_to_try:
                self._batch_operations.append(BatchOperation("delete", key))

            # Flush if batch is large enough
            if len(self._batch_operations) >= self.batch_size:
                await self._flush_batch_operations()

        logger.debug(f"Deleted memory entry: {key} from {source_tool}")
        return True

    async def search_memory(self, query: str, tool: str, limit: int = 10) -> List[Tuple[str, MemoryEntry, float]]:
        """Search for memory entries for a specific tool.

        Args:
            query: The search query
            tool: The tool requesting the search
            limit: Maximum number of results to return

        Returns:
            List[Tuple[str, MemoryEntry, float]]: List of (key, entry, score) tuples
        """
        if not self._initialized:
            await self.initialize()

        results: List[Tuple[str, MemoryEntry, float]] = []

        # Search in all collections
        collections_to_search = [self._get_collection_name(memory_type) for memory_type in MemoryType]
        collections_to_search.append(self.collection_prefix)  # Search default collection too

        # Simple text search for now
        # In a future version, this would use Firestore's text search or Vertex AI Search
        for collection_name in collections_to_search:
            try:
                # Get all documents in the collection
                # In a real implementation, we would use proper query filters
                docs = self._async_client.collection(collection_name).limit(limit * 2)
                docs_stream = await docs.get()

                for doc in docs_stream:
                    try:
                        # Convert to MemoryEntry
                        data = doc.to_dict()
                        entry = MemoryEntry.from_dict(data)

                        # Skip expired entries
                        if entry.is_expired():
                            continue

                        # Simple text matching
                        content_str = ""
                        if isinstance(entry.content, str):
                            content_str = entry.content
                        elif isinstance(entry.content, dict):
                            content_str = json.dumps(entry.content)
                        elif isinstance(entry.content, list):
                            content_str = json.dumps(entry.content)
                        else:
                            content_str = str(entry.content)

                        # Calculate score based on simple text matching
                        query_lower = query.lower()
                        content_lower = content_str.lower()

                        if query_lower in content_lower:
                            # Calculate a simple relevance score
                            score = content_lower.count(query_lower) / len(content_lower)

                            # Boost score based on metadata
                            if entry.metadata.source_tool == tool:
                                score *= 1.5  # Boost entries from the same tool

                            score *= entry.metadata.context_relevance  # Use context relevance

                            results.append((doc.id, entry, score))
                    except Exception as e:
                        logger.warning(f"Error processing search result: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error searching collection {collection_name}: {e}")
                continue

        # Sort by score (descending) and limit results
        results.sort(key=lambda x: x[2], reverse=True)
        limited_results = results[:limit]

        logger.debug(f"Search for '{query}' found {len(limited_results)} results for {tool}")
        return limited_results

    async def optimize_context_window(self, tool: str, required_keys: Optional[List[str]] = None) -> int:
        """Optimize the context window for a specific tool.

        Args:
            tool: The tool to optimize for
            required_keys: Optional list of keys that must be included

        Returns:
            int: Number of entries included in the optimized context
        """
        if not self._initialized:
            await self.initialize()

        # This is a placeholder implementation
        # In a real implementation, this would use more sophisticated algorithms
        # to optimize the context window based on token budgets, relevance, etc.

        # For now, just return the number of required keys
        if required_keys:
            return len(required_keys)

        return 0

    async def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system.

        Returns:
            Dict[str, Any]: Status information
        """
        if not self._initialized:
            await self.initialize()

        # Count entries by collection
        collection_counts = {}
        for memory_type in MemoryType:
            collection_name = self._get_collection_name(memory_type)
            try:
                # Get count of documents in collection
                query = self._async_client.collection(collection_name)
                docs = await query.get()
                collection_counts[memory_type.value] = len(docs)
            except Exception as e:
                logger.warning(f"Error getting count for collection {collection_name}: {e}")
                collection_counts[memory_type.value] = -1

        # Get cache stats
        cache_stats = {
            "size": len(self._cache),
            "max_size": self.max_cache_size,
            "usage_percentage": (
                round((len(self._cache) / self.max_cache_size) * 100, 2) if self.max_cache_size > 0 else 0
            ),
        }

        # Get batch stats
        batch_stats = {
            "pending_operations": len(self._batch_operations),
            "max_batch_size": self.batch_size,
            "last_flush": time.time() - self._last_batch_flush,
        }

        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "collection_counts": collection_counts,
            "cache": cache_stats,
            "batch": batch_stats,
            "project_id": self.project_id,
        }

    async def _process_batch_operations(self) -> None:
        """Background task to process batch operations."""
        while True:
            try:
                # Check if it's time to flush
                current_time = time.time()
                if (
                    current_time - self._last_batch_flush >= self.batch_flush_interval
                    and len(self._batch_operations) > 0
                ):
                    await self._flush_batch_operations()

                # Sleep to avoid busy waiting
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                # Handle cancellation
                logger.info("Batch processor task cancelled")
                # Flush any remaining operations
                if len(self._batch_operations) > 0:
                    await self._flush_batch_operations()
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)  # Sleep longer on error

    async def _flush_batch_operations(self) -> bool:
        """Flush batch operations to Firestore.

        Returns:
            bool: True if the flush was successful
        """
        async with self._batch_lock:
            if not self._batch_operations:
                return True

            # Group operations by collection
            operations_by_collection = {}
            for op in self._batch_operations:
                collection = self.collection_prefix  # Default collection

                # If this is a set operation with memory_type, use that collection
                if op.operation_type == "set" and op.data and "memory_type" in op.data:
                    memory_type = op.data["memory_type"]
                    collection = f"{self.collection_prefix}_{memory_type}"

                if collection not in operations_by_collection:
                    operations_by_collection[collection] = []

                operations_by_collection[collection].append(op)

            # Clear batch operations
            self._batch_operations.copy()
            self._batch_operations.clear()
            self._last_batch_flush = time.time()

        # Process operations by collection
        success = True
        for collection, collection_ops in operations_by_collection.items():
            # Create batch
            batch = self._client.batch()

            # Add operations to batch
            for op in collection_ops:
                doc_ref = self._client.collection(collection).document(op.key)

                if op.operation_type == "set":
                    batch.set(doc_ref, op.data)
                elif op.operation_type == "update":
                    batch.update(doc_ref, op.data)
                elif op.operation_type == "delete":
                    batch.delete(doc_ref)

            # Commit batch with retries
            for attempt in range(self.retry_attempts):
                try:
                    batch.commit(retry=self._retry_strategy)
                    break
                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        logger.error(f"Failed to commit batch after {self.retry_attempts} attempts: {e}")
                        success = False

                        # Re-add failed operations
                        async with self._batch_lock:
                            self._batch_operations.extend(collection_ops)
                    else:
                        logger.warning(f"Batch commit attempt {attempt+1} failed: {e}, retrying...")
                        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

        return success

    def _prune_cache(self) -> None:
        """Prune the cache to stay within size limits."""
        if len(self._cache) <= self.max_cache_size:
            return

        # Remove expired entries first
        current_time = time.time()
        expired_keys = [key for key, ttl in self._cache_ttl.items() if ttl < current_time]

        for key in expired_keys:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_ttl:
                del self._cache_ttl[key]

        # If still over limit, remove oldest entries
        if len(self._cache) > self.max_cache_size:
            # Sort by TTL (oldest first)
            sorted_keys = sorted(self._cache_ttl.keys(), key=lambda k: self._cache_ttl[k])

            # Remove oldest entries
            keys_to_remove = sorted_keys[: len(self._cache) - self.max_cache_size]
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]

        logger.debug(f"Pruned cache to {len(self._cache)} entries")

    async def close(self) -> None:
        """Close the memory manager and release resources."""
        if self._batch_processor_task:
            # Cancel batch processor task
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining operations
        if self._batch_operations:
            await self._flush_batch_operations()

        # Clear cache
        self._cache.clear()
        self._cache_ttl.clear()

        self._initialized = False
        logger.info("Firestore memory manager closed")
