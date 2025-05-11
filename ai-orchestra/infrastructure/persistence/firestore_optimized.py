"""
Optimized Firestore implementation of the memory provider interface.

This module provides a performance-optimized Firestore-based implementation
of the memory provider with connection pooling and result caching.
"""

import json
import time
import threading
import functools
from typing import Any, Dict, List, Optional, Union, Tuple, TypeVar, Callable

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ai_orchestra.core.interfaces.memory import MemoryProvider
from ai_orchestra.core.errors import MemoryError
from ai_orchestra.core.config import settings
from ai_orchestra.utils.logging import log_event, log_start, log_end, log_error

import logging
logger = logging.getLogger("ai_orchestra.infrastructure.persistence.firestore_optimized")

# Type variable for generic function return type
T = TypeVar('T')


class FirestoreClientPool:
    """
    Singleton pool for Firestore clients to optimize connection management.
    
    This class implements a thread-safe singleton pattern to ensure
    only one Firestore client is created per project, reducing
    connection overhead and improving performance.
    """
    
    _instances: Dict[str, firestore.Client] = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_client(cls, project_id: Optional[str] = None) -> firestore.Client:
        """
        Get or create a Firestore client for the specified project.
        
        Args:
            project_id: The GCP project ID (defaults to settings.gcp.project_id)
            
        Returns:
            A Firestore client instance
        """
        project_id = project_id or settings.gcp.project_id
        
        with cls._lock:
            if project_id not in cls._instances:
                # Use emulator if configured
                if settings.database.use_firestore_emulator and settings.database.firestore_emulator_host:
                    import os
                    os.environ["FIRESTORE_EMULATOR_HOST"] = settings.database.firestore_emulator_host
                
                # Create new client
                cls._instances[project_id] = firestore.Client(project=project_id)
                logger.info(f"Created new Firestore client for project: {project_id}")
            
            return cls._instances[project_id]


def cache_result(ttl_seconds: int = 300, max_size: int = 100):
    """
    Decorator to cache function results for a specified time period.
    
    Args:
        ttl_seconds: Time-to-live in seconds for cached results
        max_size: Maximum number of items to keep in the cache
        
    Returns:
        Decorated function with caching capability
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: Dict[str, Dict[str, Any]] = {}
        cache_order: List[str] = []
        lock = threading.RLock()
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate a cache key from the function arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            now = time.time()
            
            with lock:
                # Check if result is in cache and not expired
                if key in cache and now - cache[key]['timestamp'] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[key]['result']
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Update the cache
                cache[key] = {'result': result, 'timestamp': now}
                
                # Add to cache order for LRU tracking
                if key in cache_order:
                    cache_order.remove(key)
                cache_order.append(key)
                
                # Trim cache if it exceeds max size
                if len(cache_order) > max_size:
                    oldest_key = cache_order.pop(0)
                    if oldest_key in cache:
                        del cache[oldest_key]
                
                return result
        
        # Add method to clear the cache
        def clear_cache() -> None:
            with lock:
                cache.clear()
                cache_order.clear()
        
        wrapper.clear_cache = clear_cache  # type: ignore
        
        return wrapper
    
    return decorator


class OptimizedFirestoreMemoryProvider(MemoryProvider):
    """
    Optimized Firestore implementation of the memory provider interface.
    
    This class provides a performance-optimized implementation of the
    MemoryProvider interface using Firestore, with connection pooling
    and result caching.
    """
    
    def __init__(
        self,
        collection_name: str = "memory",
        client: Optional[firestore.Client] = None,
        cache_ttl: int = 300,  # 5 minutes default cache TTL
        cache_size: int = 1000,  # Maximum cache size
    ):
        """
        Initialize the optimized Firestore memory provider.
        
        Args:
            collection_name: The Firestore collection name
            client: Optional Firestore client (uses pool if not provided)
            cache_ttl: Time-to-live in seconds for cached results
            cache_size: Maximum number of items to keep in the cache
        """
        self.collection_name = collection_name
        self.cache_ttl = cache_ttl
        self.cache_size = cache_size
        
        # Use provided client or get from pool
        self.client = client or FirestoreClientPool.get_client()
        
        log_event(logger, "optimized_firestore_memory_provider", "initialized", {
            "collection_name": collection_name,
            "project_id": settings.gcp.project_id,
            "cache_ttl": cache_ttl,
            "cache_size": cache_size,
        })
    
    @cache_result(ttl_seconds=300)
    async def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key with caching.
        
        Args:
            key: The key to retrieve the value for
            
        Returns:
            The stored value, or None if not found
            
        Raises:
            MemoryError: If there was an error retrieving the value
        """
        start_time = log_start(logger, "retrieve", {"key": key})
        
        try:
            # Get the document
            doc_ref = self.client.collection(self.collection_name).document(key)
            doc = await self._run_async(doc_ref.get)
            
            # Check if document exists
            if not doc.exists:
                log_end(logger, "retrieve", start_time, {"key": key, "exists": False})
                return None
            
            # Get document data
            data = doc.to_dict()
            
            # Check if document has expired
            if "expiry" in data and data["expiry"] < time.time():
                # Document has expired, delete it
                await self._run_async(doc_ref.delete)
                log_end(logger, "retrieve", start_time, {"key": key, "expired": True})
                return None
            
            # Return the value
            log_end(logger, "retrieve", start_time, {"key": key, "exists": True})
            return data["value"]
            
        except Exception as e:
            log_error(logger, "retrieve", e, {"key": key})
            raise MemoryError(f"Failed to retrieve value for key '{key}'", cause=e)
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value with an optional TTL.
        
        Args:
            key: The key to store the value under
            value: The value to store
            ttl: Optional time-to-live in seconds
            
        Returns:
            True if the value was stored successfully, False otherwise
            
        Raises:
            MemoryError: If there was an error storing the value
        """
        start_time = log_start(logger, "store", {"key": key})
        
        try:
            # Serialize the value to JSON
            if not isinstance(value, (str, int, float, bool, dict, list, type(None))):
                value = json.dumps({"serialized": str(value)})
            
            # Calculate expiry time if TTL is provided
            expiry = int(time.time() + ttl) if ttl else None
            
            # Create document data
            doc_data = {
                "key": key,
                "value": value,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            
            if expiry:
                doc_data["expiry"] = expiry
            
            # Store the document
            await self._run_async(
                lambda: self.client.collection(self.collection_name).document(key).set(doc_data)
            )
            
            # Clear cache for this key to ensure fresh data
            # This is a bit of a hack since we can't directly access the cache from the decorator
            # In a real implementation, we would use a more sophisticated caching system
            retrieve_method = type(self).retrieve
            if hasattr(retrieve_method, 'clear_cache'):
                retrieve_method.clear_cache()  # type: ignore
            
            log_end(logger, "store", start_time, {"key": key, "success": True})
            return True
            
        except Exception as e:
            log_error(logger, "store", e, {"key": key})
            raise MemoryError(f"Failed to store value for key '{key}'", cause=e)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value by key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the value was deleted successfully, False otherwise
            
        Raises:
            MemoryError: If there was an error deleting the value
        """
        start_time = log_start(logger, "delete", {"key": key})
        
        try:
            # Delete the document
            await self._run_async(
                lambda: self.client.collection(self.collection_name).document(key).delete()
            )
            
            # Clear cache for this key
            retrieve_method = type(self).retrieve
            if hasattr(retrieve_method, 'clear_cache'):
                retrieve_method.clear_cache()  # type: ignore
            
            log_end(logger, "delete", start_time, {"key": key, "success": True})
            return True
            
        except Exception as e:
            log_error(logger, "delete", e, {"key": key})
            raise MemoryError(f"Failed to delete value for key '{key}'", cause=e)
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
            
        Raises:
            MemoryError: If there was an error checking if the key exists
        """
        start_time = log_start(logger, "exists", {"key": key})
        
        try:
            # Get the document
            doc_ref = self.client.collection(self.collection_name).document(key)
            doc = await self._run_async(doc_ref.get)
            
            # Check if document exists
            exists = doc.exists
            
            # If document exists, check if it has expired
            if exists and "expiry" in doc.to_dict() and doc.to_dict()["expiry"] < time.time():
                # Document has expired, delete it
                await self._run_async(doc_ref.delete)
                exists = False
            
            log_end(logger, "exists", start_time, {"key": key, "exists": exists})
            return exists
            
        except Exception as e:
            log_error(logger, "exists", e, {"key": key})
            raise MemoryError(f"Failed to check if key '{key}' exists", cause=e)
    
    async def list_keys(self, pattern: str = "*") -> List[str]:
        """
        List keys matching a pattern.
        
        Args:
            pattern: The pattern to match keys against
            
        Returns:
            A list of matching keys
            
        Raises:
            MemoryError: If there was an error listing keys
        """
        start_time = log_start(logger, "list_keys", {"pattern": pattern})
        
        try:
            # Firestore doesn't support glob patterns directly, so we need to handle this differently
            # For now, we'll just list all keys and filter them in Python
            # In a real implementation, you might want to use a more efficient approach
            
            # Get all documents
            collection_ref = self.client.collection(self.collection_name)
            docs = await self._run_async(collection_ref.stream)
            
            # Convert pattern to regex
            import re
            pattern_regex = re.compile(pattern.replace("*", ".*"))
            
            # Filter keys by pattern and check expiry
            current_time = time.time()
            keys = []
            
            for doc in docs:
                data = doc.to_dict()
                key = data.get("key")
                
                # Skip if key doesn't match pattern
                if not key or not pattern_regex.match(key):
                    continue
                
                # Skip if document has expired
                if "expiry" in data and data["expiry"] < current_time:
                    continue
                
                keys.append(key)
            
            log_end(logger, "list_keys", start_time, {"pattern": pattern, "count": len(keys)})
            return keys
            
        except Exception as e:
            log_error(logger, "list_keys", e, {"pattern": pattern})
            raise MemoryError(f"Failed to list keys matching pattern '{pattern}'", cause=e)
    
    async def store_batch(self, items: List[Tuple[str, Any, Optional[int]]]) -> Dict[str, bool]:
        """
        Store multiple items in a batch operation.
        
        Args:
            items: List of (key, value, ttl) tuples to store
            
        Returns:
            Dictionary mapping keys to success status
            
        Raises:
            MemoryError: If there was an error storing the values
        """
        start_time = log_start(logger, "store_batch", {"item_count": len(items)})
        
        try:
            # Create a batch
            batch = self.client.batch()
            current_time = time.time()
            results = {}
            
            # Add each item to the batch
            for key, value, ttl in items:
                # Serialize the value to JSON if needed
                if not isinstance(value, (str, int, float, bool, dict, list, type(None))):
                    value = json.dumps({"serialized": str(value)})
                
                # Calculate expiry time if TTL is provided
                expiry = int(current_time + ttl) if ttl else None
                
                # Create document data
                doc_data = {
                    "key": key,
                    "value": value,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                }
                
                if expiry:
                    doc_data["expiry"] = expiry
                
                # Add to batch
                batch.set(self.client.collection(self.collection_name).document(key), doc_data)
                results[key] = True
            
            # Commit the batch
            await self._run_async(batch.commit)
            
            # Clear cache
            retrieve_method = type(self).retrieve
            if hasattr(retrieve_method, 'clear_cache'):
                retrieve_method.clear_cache()  # type: ignore
            
            log_end(logger, "store_batch", start_time, {"success_count": len(results)})
            return results
            
        except Exception as e:
            log_error(logger, "store_batch", e, {"item_count": len(items)})
            raise MemoryError(f"Failed to store batch of {len(items)} items", cause=e)
    
    async def delete_batch(self, keys: List[str]) -> Dict[str, bool]:
        """
        Delete multiple items in a batch operation.
        
        Args:
            keys: List of keys to delete
            
        Returns:
            Dictionary mapping keys to success status
            
        Raises:
            MemoryError: If there was an error deleting the values
        """
        start_time = log_start(logger, "delete_batch", {"key_count": len(keys)})
        
        try:
            # Create a batch
            batch = self.client.batch()
            results = {}
            
            # Add each key to the batch
            for key in keys:
                batch.delete(self.client.collection(self.collection_name).document(key))
                results[key] = True
            
            # Commit the batch
            await self._run_async(batch.commit)
            
            # Clear cache
            retrieve_method = type(self).retrieve
            if hasattr(retrieve_method, 'clear_cache'):
                retrieve_method.clear_cache()  # type: ignore
            
            log_end(logger, "delete_batch", start_time, {"success_count": len(results)})
            return results
            
        except Exception as e:
            log_error(logger, "delete_batch", e, {"key_count": len(keys)})
            raise MemoryError(f"Failed to delete batch of {len(keys)} keys", cause=e)
    
    async def _run_async(self, func: Callable[[], T]) -> T:
        """
        Run a synchronous function asynchronously.
        
        Args:
            func: The function to run
            
        Returns:
            The result of the function
        """
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, func)