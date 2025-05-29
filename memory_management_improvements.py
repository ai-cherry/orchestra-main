#!/usr/bin/env python3
"""
Reference implementation of improvements for memory management components.

This file provides complete examples of improved implementations for the
memory management system, focusing on performance, error handling, and
cloud optimization.
"""

import asyncio
import concurrent.futures
import datetime
import functools
import logging
import time
import uuid
from typing import List, Optional, TypeVar

# Imports would normally be from the actual codebase
# These are placeholders to demonstrate patterns
from google.api_core.exceptions import GoogleAPIError

from packages.shared.src.memory.memory_manager import MemoryHealth, MemoryManager
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Set up logger
logger = logging.getLogger(__name__)

# Generic type for function return
T = TypeVar("T")

# Define MEMORY_ITEMS_COLLECTION if it's a constant
MEMORY_ITEMS_COLLECTION = "memory_items_default_collection"  # Placeholder value, adjust as needed

# ============================
# Thread Pool Management
# ============================


class ThreadPoolManager:
    """
    Singleton thread pool manager to prevent resource exhaustion.

    This class provides a managed thread pool for offloading blocking I/O
    operations, ensuring controlled concurrency and proper resource cleanup.
    """

    _instance = None
    _thread_pool = None
    _max_workers = 20
    _thread_name_prefix = "memory_worker_"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ThreadPoolManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the thread pool."""
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers, thread_name_prefix=self._thread_name_prefix
        )
        logger.info(f"Thread pool initialized with {self._max_workers} workers")

    @classmethod
    def get_pool(cls):
        """Get the thread pool instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance._thread_pool

    @classmethod
    async def run_in_thread(cls, func, *args, **kwargs):
        """
        Run a function in the thread pool.

        Args:
            func: The function to run
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function
        """
        return await asyncio.wrap_future(cls.get_pool().submit(func, *args, **kwargs))

    @classmethod
    async def shutdown(cls):
        """Shutdown the thread pool."""
        if cls._instance and cls._instance._thread_pool:
            cls._instance._thread_pool.shutdown(wait=True)
            cls._instance._thread_pool = None
            logger.info("Thread pool shut down")


# ============================
# Error Handling Decorators
# ============================


class StorageError(Exception):
    """Base exception for storage-related errors."""


class ValidationError(Exception):
    """Exception for validation errors in storage operations."""


class ConnectionError(Exception):
    """Exception for connection-related errors."""


def handle_storage_errors(func):
    """
    Decorator for standardizing error handling in storage operations.

    This decorator catches and transforms exceptions into consistent
    StorageError exceptions, adding appropriate logging.

    Args:
        func: The async function to decorate

    Returns:
        Decorated function with standardized error handling
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            # Don't wrap validation errors, just log them
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise
        except GoogleAPIError as e:
            error_msg = f"{func.__name__} operation failed: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e
        except Exception as e:
            # Don't wrap other known exceptions, only unexpected ones
            if isinstance(e, (StorageError, ConnectionError)):
                raise
            error_msg = f"Unexpected error in {func.__name__}: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg) from e

    return wrapper


def with_retry(
    max_retries=3,
    base_delay=0.1,
    retryable_exceptions=(GoogleAPIError, ConnectionError),
):
    """
    Decorator for adding exponential backoff retry logic to async functions.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        retryable_exceptions: Tuple of exception types that should trigger retry

    Returns:
        Decorator function that adds retry logic
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Operation {func.__name__} failed after {max_retries} retries: {e}")
                        raise

                    delay = base_delay * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(
                        f"Operation {func.__name__} failed, retrying in {delay:.2f}s ({retries}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(delay)

        return wrapper

    return decorator


# ============================
# Improved Semantic Search
# ============================


async def optimized_semantic_search(
    self,
    user_id: str,
    query_embedding: List[float],
    persona_context: Optional[PersonaConfig] = None,
    top_k: int = 5,
) -> List[MemoryItem]:
    """
    Improved semantic search implementation using batched processing and pagination.

    This implementation:
    1. Uses pagination to avoid loading all embeddings at once
    2. Processes embeddings in batches to reduce memory usage
    3. Uses numpy for efficient vector calculations when available
    4. Is ready to integrate with GCP Vector Search for production

    Args:
        user_id: The user ID to search memories for
        query_embedding: The vector embedding of the query
        persona_context: Optional persona context for personalized results
        top_k: Maximum number of results to return

    Returns:
        List of memory items ordered by relevance
    """
    self._check_initialized()

    if not query_embedding:
        raise ValidationError("Query embedding cannot be empty")

    # Try to use numpy for efficient vector calculations if available
    try:
        import numpy as np

        use_numpy = True
    except ImportError:
        use_numpy = False

    # Calculate query embedding magnitude once
    if use_numpy:
        query_np = np.array(query_embedding)
        mag_query = np.linalg.norm(query_np)
    else:
        mag_query = (sum(a * a for a in query_embedding)) ** 0.5

    # Prepare for finding top-k results
    top_items_with_scores = []
    page_size = 100  # Process in batches of 100 items
    page_token = None
    batch_count = 0
    total_processed = 0

    try:
        # Paginate through results to avoid memory issues
        while True:
            batch_count += 1

            # Get a batch of memory items using pagination
            query = (
                self._async_client.collection(MEMORY_ITEMS_COLLECTION).where("user_id", "==", user_id).limit(page_size)
            )

            # Add persona filter if provided
            if persona_context and persona_context.name:
                query = query.where("persona_active", "==", persona_context.name)

            # Apply pagination
            if page_token:
                query = query.start_after(page_token)

            # Execute query
            docs = await query.get()

            # If no documents, we've processed all batches
            if not docs:
                break

            # Remember the last document for pagination
            page_token = docs[-1] if docs else None

            # Process this batch of items
            batch_items_with_scores = []

            for doc in docs:
                total_processed += 1
                try:
                    item_data = doc.to_dict()
                    embedding = item_data.get("embedding")
                    if not embedding:
                        continue

                    # Skip items with mismatched embedding dimensions
                    if len(embedding) != len(query_embedding):
                        logger.warning(f"Embedding dimension mismatch: {len(embedding)} vs {len(query_embedding)}")
                        continue

                    # Calculate similarity more efficiently
                    if use_numpy:
                        item_np = np.array(embedding)
                        mag_item = np.linalg.norm(item_np)
                        if mag_item > 0 and mag_query > 0:
                            similarity = np.dot(query_np, item_np) / (mag_item * mag_query)
                        else:
                            similarity = 0
                    else:
                        dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
                        mag_item = sum(a * a for a in embedding) ** 0.5
                        similarity = dot_product / (mag_item * mag_query) if mag_item > 0 and mag_query > 0 else 0

                    item = MemoryItem(**item_data)
                    batch_items_with_scores.append((item, similarity))
                except Exception as e:
                    logger.warning(f"Error processing item during semantic search: {e}")
                    continue

            # Merge with top results so far
            top_items_with_scores.extend(batch_items_with_scores)

            # Keep only top-k results to conserve memory across batches
            top_items_with_scores.sort(key=lambda x: x[1], reverse=True)
            top_items_with_scores = top_items_with_scores[:top_k]

            # If we didn't get enough items to fill a page, we're done
            if len(docs) < page_size:
                break

        # Final sort and extract items
        top_items_with_scores.sort(key=lambda x: x[1], reverse=True)
        top_items = [item for item, _ in top_items_with_scores[:top_k]]

        logger.debug(
            f"Performed semantic search for user {user_id}, processed {total_processed} items in {batch_count} batches, found {len(top_items)} results"
        )
        return top_items

    except GoogleAPIError as e:
        error_msg = f"Failed to perform semantic search in mongodb: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during semantic search: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg)


# ============================
# Improved Cleanup Operations
# ============================


async def cleanup_expired_items_with_progress(self) -> int:
    """
    Remove expired items from storage with progress reporting.

    This improved implementation:
    1. Uses configurable batch sizes
    2. Reports progress for long-running operations
    3. Includes proper error handling

    Returns:
        Number of items removed
    """
    self._check_initialized()

    # Configurable batch sizes
    QUERY_BATCH_SIZE = 100
    DELETE_BATCH_SIZE = 400  # mongodb limit is 500

    try:
        # Get current time
        now = datetime.utcnow()
        total_deleted = 0
        total_batches = 0
        start_time = time.time()

        logger.info(f"Starting cleanup of expired items older than {now}")

        # Process in multiple query batches as there might be many expired items
        has_more_items = True
        last_doc = None

        while has_more_items:
            # Build the query for expired items
            query = (
                self._async_client.collection(MEMORY_ITEMS_COLLECTION)
                .where("expiration", "<", now)
                .limit(QUERY_BATCH_SIZE)
            )

            # Apply pagination start point if we have one
            if last_doc:
                query = query.start_after(last_doc)

            # Execute query
            docs = await query.get()
            batch_count = len(docs)

            # If no items in this batch, we're done
            if batch_count == 0:
                has_more_items = False
                continue

            # Remember the last doc for next query
            last_doc = docs[-1]

            # Check if there are potentially more items
            has_more_items = batch_count == QUERY_BATCH_SIZE

            # Delete items in sub-batches to stay within mongodb limits
            delete_batch = self._async_client.batch()
            items_in_batch = 0

            for doc in docs:
                delete_batch.delete(doc.reference)
                items_in_batch += 1

                # If we've reached the delete batch limit, commit and create a new batch
                if items_in_batch >= DELETE_BATCH_SIZE:
                    await delete_batch.commit()
                    total_deleted += items_in_batch
                    total_batches += 1

                    # Log progress
                    logger.info(f"Deleted batch of {items_in_batch} expired items (total: {total_deleted})")

                    # Start a new batch
                    delete_batch = self._async_client.batch()
                    items_in_batch = 0

            # Commit any remaining deletes in the current batch
            if items_in_batch > 0:
                await delete_batch.commit()
                total_deleted += items_in_batch
                total_batches += 1
                logger.info(f"Deleted batch of {items_in_batch} expired items (total: {total_deleted})")

        # Log summary
        duration = time.time() - start_time
        logger.info(
            f"Cleanup completed: deleted {total_deleted} expired items in {total_batches} batches ({duration:.2f} seconds)"
        )

        return total_deleted
    except GoogleAPIError as e:
        error_msg = f"Failed to cleanup expired items in mongodb: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during cleanup: {e}"
        logger.error(error_msg)
        raise StorageError(error_msg)


# ============================
# Complete FirestoreMemoryAdapter Example
# ============================


class ImprovedFirestoreMemoryAdapter(MemoryManager):
    """
    Improved mongodb memory adapter with optimized performance, error handling, and cloud-native patterns.

    This class demonstrates the recommended implementation patterns for
    a production-ready FirestoreMemoryAdapter.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        namespace: str = "default",
        batch_size: int = 400,
    ):
        """
        Initialize the improved mongodb memory adapter.

        Args:
            project_id: Optional Google Cloud project ID
            credentials_json: Optional JSON string containing service account credentials
            credentials_path: Optional path to service account credentials file
            namespace: Namespace for collection prefixing
            batch_size: Batch size for batch operations
        """
        # Initialize the underlying mongodb manager
        # In actual implementation, this would be replaced with direct mongodb clients
        self._firestore_manager = None  # Placeholder

        # Store configuration
        self.namespace = namespace
        self.batch_size = batch_size
        self._project_id = project_id
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path

        # Initialization state
        self._is_initialized = False

        # Collection names with namespace
        self._memory_collection = f"{namespace}_memory_items"
        self._agent_data_collection = f"{namespace}_agent_data"
        self._user_sessions_collection = f"{namespace}_user_sessions"

    @handle_storage_errors
    @with_retry()
    async def initialize(self) -> None:
        """Initialize the memory manager with retry and error handling."""
        if self._is_initialized:
            return

        try:
            # In a real implementation, would initialize mongodb clients directly
            # For demonstration, using ThreadPoolManager to run sync initialization
            await ThreadPoolManager.run_in_thread(self._initialize_sync)
            self._is_initialized = True
            logger.info(f"ImprovedFirestoreMemoryAdapter initialized with namespace {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to initialize mongodb adapter: {e}")
            raise ConnectionError(f"Failed to initialize mongodb connection: {e}")

    def _initialize_sync(self):
        """Synchronous initialization for running in thread pool."""
        # In a real implementation, would initialize clients and create collections if needed

    @handle_storage_errors
    async def close(self) -> None:
        """Close the memory manager and release resources."""
        if not self._is_initialized:
            return

        try:
            # Close clients properly, using an async context manager pattern
            await ThreadPoolManager.run_in_thread(self._close_sync)
            self._is_initialized = False
            logger.info("ImprovedFirestoreMemoryAdapter closed")
        finally:
            # Ensure consistent state even if close fails
            self._is_initialized = False

    def _close_sync(self):
        """Synchronous close method for running in thread pool."""
        # In a real implementation, would close mongodb clients

    def _check_initialized(self) -> None:
        """Check if initialized and raise appropriate exception if not."""
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized. Call initialize() first.")

    @handle_storage_errors
    @with_retry()
    async def add_memory_item(self, item: MemoryItem) -> str:
        """Add a memory item to storage with retry and error handling."""
        self._check_initialized()

        # Generate an ID if not provided
        if not item.id:
            item.id = str(uuid.uuid4())

        # Validate required fields
        if not item.user_id:
            raise ValidationError("user_id is required for memory items")

        # Store in mongodb using ThreadPoolManager
        await ThreadPoolManager.run_in_thread(self._add_item_sync, item)

        logger.debug(f"Saved memory item {item.id} for user {item.user_id}")
        return item.id

    def _add_item_sync(self, item: MemoryItem) -> None:
        """Synchronous add item method for running in thread pool."""
        # In a real implementation, would convert item to dict and store in mongodb

    # Other methods would be implemented similarly using the patterns demonstrated above
    # Each method would use the ThreadPoolManager, error handling, and retry decorators

    # Implementing the semantic search method using the optimized version
    semantic_search = optimized_semantic_search

    # Implementing the cleanup method using the improved version
    cleanup_expired_items = cleanup_expired_items_with_progress

    @handle_storage_errors
    @with_retry()
    async def health_check(self) -> MemoryHealth:
        """
        Perform a health check on the mongodb connection.

        Returns:
            Dictionary with health status information
        """
        health: MemoryHealth = {
            "status": "healthy",
            "mongodb": False,
            "redis": False,  # Not using Redis directly
            "error_count": 0,
            "details": {
                "provider": "mongodb",
                "adapter": "ImprovedFirestoreMemoryAdapter",
                "namespace": self.namespace,
            },
        }

        if not self._is_initialized:
            try:
                await self.initialize()
                health["details"]["initialization"] = "Initialized during health check"
            except Exception as e:
                health["status"] = "error"
                health["details"]["initialization_error"] = str(e)
                return health

        try:
            # Attempt a lightweight operation to verify connection
            # In a real implementation, would check actual mongodb connection
            await ThreadPoolManager.run_in_thread(self._check_connection_sync)

            health["mongodb"] = True
            return health
        except Exception as e:
            return {
                "status": "error",
                "mongodb": False,
                "redis": False,
                "error_count": 1,
                "last_error": str(e),
                "details": {
                    "message": f"mongodb health check failed: {e}",
                    "namespace": self.namespace,
                },
            }

    def _check_connection_sync(self) -> bool:
        """Synchronous connection check for running in thread pool."""
        # In a real implementation, would perform a lightweight mongodb operation
        return True


# ============================
# Usage Example
# ============================


async def usage_example():
    """Example of using the improved FirestoreMemoryAdapter."""

    # Initialize the adapter
    memory_manager = ImprovedFirestoreMemoryAdapter(project_id="your-project-id", namespace="example-namespace")

    try:
        # Initialize
        await memory_manager.initialize()

        # Check health
        health = await memory_manager.health_check()
        logger.info(f"Memory manager health: {health}")

        # Add a memory item
        item = MemoryItem(
            id=None,  # Will be generated
            user_id="test-user",
            session_id="test-session",
            timestamp=datetime.utcnow(),
            item_type="conversation",
            text_content="This is a test memory",
            metadata={"source": "example"},
        )

        item_id = await memory_manager.add_memory_item(item)
        logger.info(f"Added memory item with ID: {item_id}")

        # Retrieve the item
        retrieved = await memory_manager.get_memory_item(item_id)
        logger.info(f"Retrieved item: {retrieved}")

        # Clean up finally
        await memory_manager.close()
        await ThreadPoolManager.shutdown()

    except Exception as e:
        logger.error(f"Error in usage example: {e}")
        # Ensure proper cleanup
        await memory_manager.close()
        await ThreadPoolManager.shutdown()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the example
    asyncio.run(usage_example())
