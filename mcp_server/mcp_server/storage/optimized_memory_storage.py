#!/usr/bin/env python3
"""
optimized_memory_storage.py - Optimized In-Memory Storage Implementation

This module provides a high-performance in-memory storage implementation
optimized for single-instance, development, and test environments.
"""

import time
import logging
import json
import asyncio
import threading
from typing import Dict, List, Optional, Any, Union, Set

from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry
from ..utils.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)


class OptimizedMemoryStorage(IMemoryStorage):
    """High-performance in-memory storage implementation.

    This implementation is optimized for speed and simplicity in development environments.
    It stores all data in memory with the following optimizations:
    - Uses dictionaries for O(1) key lookup
    - Implements simple expiration without background threads
    - Provides basic search capabilities
    - Optimizes for common operation patterns

    It is NOT recommended for production use with large datasets due to memory constraints.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with optional configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.data: Dict[str, Dict[str, Dict[str, Any]]] = {}  # scope -> key -> data
        self.ttls: Dict[str, Dict[str, float]] = {}  # scope -> key -> expiration time
        self.lock = asyncio.Lock()
        self.perf = get_performance_monitor()
        self._initialized = False

        # Optional persistence configuration
        self.persistence_path = self.config.get("persistence_path")
        self.persist_on_change = self.config.get("persist_on_change", False)
        self.auto_load = self.config.get("auto_load", True)

        # Performance settings
        self.max_keys_per_scope = self.config.get("max_keys_per_scope", 10000)
        self.enable_search_index = self.config.get("enable_search_index", True)

        # Search index (scope -> term -> set of keys)
        self.search_index: Dict[str, Dict[str, Set[str]]] = {}

        # Stats
        self.stats = {
            "stores": 0,
            "retrievals": 0,
            "hits": 0,
            "misses": 0,
            "expirations": 0,
            "deletes": 0,
            "searches": 0,
        }

    async def initialize(self) -> bool:
        """Initialize the storage backend.

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        try:
            # First-time initialization
            if not self._initialized:
                logger.info("Initializing optimized memory storage")

                # Create initial data structure
                # No need to acquire lock since we're initializing

                # Auto-load from persistence if configured
                if self.persistence_path and self.auto_load:
                    try:
                        await self._load_from_persistence()
                    except Exception as e:
                        logger.warning(f"Could not load data from persistence: {e}")

                self._initialized = True

            duration = time.time() - start_time
            self.perf.record_operation("storage.initialize", duration)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize optimized memory storage: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.initialize.error", duration)
            return False

    async def store(self, key: str, entry: Any, scope: str = "default") -> bool:
        """Store an entry in memory.

        Args:
            key: The key to store under
            entry: The entry to store (can be any JSON-serializable object)
            scope: The scope to store in

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        try:
            self.stats["stores"] += 1

            async with self.lock:
                # Create scope if it doesn't exist
                if scope not in self.data:
                    self.data[scope] = {}
                    self.ttls[scope] = {}
                    if self.enable_search_index:
                        self.search_index[scope] = {}

                # Check if we've reached the max keys limit
                if len(self.data[scope]) >= self.max_keys_per_scope:
                    # Try to clean expired keys first
                    await self._clean_expired_keys(scope)

                    # If still at limit, remove oldest key
                    if len(self.data[scope]) >= self.max_keys_per_scope:
                        oldest_key = next(iter(self.data[scope]))
                        del self.data[scope][oldest_key]
                        if oldest_key in self.ttls[scope]:
                            del self.ttls[scope][oldest_key]
                        # Remove from search index
                        if self.enable_search_index and scope in self.search_index:
                            for term_keys in self.search_index[scope].values():
                                if oldest_key in term_keys:
                                    term_keys.remove(oldest_key)

                # Store the data (make a copy to avoid reference issues)
                if isinstance(entry, dict):
                    self.data[scope][key] = json.loads(json.dumps(entry))
                elif isinstance(entry, (str, int, float, bool, list)):
                    self.data[scope][key] = entry
                else:
                    try:
                        self.data[scope][key] = json.loads(json.dumps(entry))
                    except (TypeError, json.JSONDecodeError):
                        # Fall back to string representation
                        self.data[scope][key] = str(entry)

                # Set TTL if provided
                ttl = None
                if isinstance(entry, dict) and "ttl_seconds" in entry:
                    ttl = entry["ttl_seconds"]
                elif isinstance(entry, MemoryEntry) and entry.metadata.ttl_seconds:
                    ttl = entry.metadata.ttl_seconds

                if ttl:
                    self.ttls[scope][key] = time.time() + ttl
                elif key in self.ttls[scope]:
                    # Remove any existing TTL
                    del self.ttls[scope][key]

                # Update search index
                if self.enable_search_index:
                    await self._update_search_index(key, entry, scope)

            # Persist if configured
            if self.persistence_path and self.persist_on_change:
                await self._persist_to_storage()

            duration = time.time() - start_time
            self.perf.record_operation("storage.store", duration)
            return True
        except Exception as e:
            logger.error(f"Failed to store entry: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.store.error", duration)
            return False

    async def retrieve(self, key: str, scope: str = "default") -> Optional[Any]:
        """Retrieve an entry from memory.

        Args:
            key: The key to retrieve
            scope: The scope to retrieve from

        Returns:
            The entry, or None if not found or expired
        """
        start_time = time.time()
        try:
            self.stats["retrievals"] += 1

            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    self.stats["misses"] += 1
                    return None

                # Check if key exists
                if key not in self.data[scope]:
                    self.stats["misses"] += 1
                    return None

                # Check if key has expired
                if scope in self.ttls and key in self.ttls[scope]:
                    if time.time() > self.ttls[scope][key]:
                        # Key has expired, remove it
                        del self.data[scope][key]
                        del self.ttls[scope][key]

                        # Remove from search index
                        if self.enable_search_index and scope in self.search_index:
                            for term_keys in self.search_index[scope].values():
                                if key in term_keys:
                                    term_keys.remove(key)

                        self.stats["expirations"] += 1
                        self.stats["misses"] += 1
                        return None

                # Return data (make a copy to avoid reference issues)
                self.stats["hits"] += 1
                if isinstance(self.data[scope][key], dict):
                    result = json.loads(json.dumps(self.data[scope][key]))
                else:
                    result = self.data[scope][key]

            duration = time.time() - start_time
            self.perf.record_operation("storage.retrieve", duration)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve entry: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.retrieve.error", duration)
            return None

    async def delete(self, key: str, scope: str = "default") -> bool:
        """Delete an entry from memory.

        Args:
            key: The key to delete
            scope: The scope to delete from

        Returns:
            True if deleted, False if not found or error
        """
        start_time = time.time()
        try:
            self.stats["deletes"] += 1

            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    return False

                # Check if key exists
                if key not in self.data[scope]:
                    return False

                # Delete the key
                del self.data[scope][key]

                # Delete TTL if exists
                if scope in self.ttls and key in self.ttls[scope]:
                    del self.ttls[scope][key]

                # Remove from search index
                if self.enable_search_index and scope in self.search_index:
                    for term_keys in self.search_index[scope].values():
                        if key in term_keys:
                            term_keys.remove(key)

            # Persist if configured
            if self.persistence_path and self.persist_on_change:
                await self._persist_to_storage()

            duration = time.time() - start_time
            self.perf.record_operation("storage.delete", duration)
            return True
        except Exception as e:
            logger.error(f"Failed to delete entry: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.delete.error", duration)
            return False

    async def list_keys(self, scope: str = "default") -> List[str]:
        """List all keys in a scope.

        Args:
            scope: The scope to list keys from

        Returns:
            A list of keys
        """
        start_time = time.time()
        try:
            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    return []

                # Clean expired keys first
                await self._clean_expired_keys(scope)

                # Return list of keys
                keys = list(self.data[scope].keys())

            duration = time.time() - start_time
            self.perf.record_operation("storage.list_keys", duration)
            return keys
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.list_keys.error", duration)
            return []

    async def search(
        self, query: str, scope: str = "default", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for entries matching a query.

        Args:
            query: The query to search for
            scope: The scope to search in
            limit: Maximum number of results to return

        Returns:
            A list of matching entries
        """
        start_time = time.time()
        try:
            self.stats["searches"] += 1

            results = []
            async with self.lock:
                # Check if scope exists
                if scope not in self.data:
                    return []

                # Clean expired keys first
                await self._clean_expired_keys(scope)

                # Use search index if enabled
                if self.enable_search_index and scope in self.search_index:
                    matching_keys = set()
                    # Split query into terms
                    terms = self._get_search_terms(query)

                    for term in terms:
                        if term in self.search_index[scope]:
                            # For first term, initialize the set
                            if not matching_keys:
                                matching_keys = self.search_index[scope][term].copy()
                            else:
                                # For subsequent terms, keep only keys that match all terms
                                matching_keys &= self.search_index[scope][term]

                    # Get data for matching keys
                    for key in list(matching_keys)[:limit]:
                        if key in self.data[scope]:
                            entry = self.data[scope][key]
                            # Add key to entry for reference
                            if isinstance(entry, dict):
                                entry_copy = json.loads(json.dumps(entry))
                                entry_copy["_key"] = key
                                results.append(entry_copy)
                            else:
                                results.append({"_key": key, "value": entry})
                else:
                    # Fallback to simple string matching
                    query_lower = query.lower()
                    for key, entry in self.data[scope].items():
                        if len(results) >= limit:
                            break

                        # Check if query is in key
                        if query_lower in key.lower():
                            if isinstance(entry, dict):
                                entry_copy = json.loads(json.dumps(entry))
                                entry_copy["_key"] = key
                                results.append(entry_copy)
                            else:
                                results.append({"_key": key, "value": entry})
                            continue

                        # Check if query is in values
                        if isinstance(entry, dict):
                            entry_str = json.dumps(entry).lower()
                            if query_lower in entry_str:
                                entry_copy = json.loads(json.dumps(entry))
                                entry_copy["_key"] = key
                                results.append(entry_copy)
                        elif isinstance(entry, str) and query_lower in entry.lower():
                            results.append({"_key": key, "value": entry})

            duration = time.time() - start_time
            self.perf.record_operation("storage.search", duration)
            return results
        except Exception as e:
            logger.error(f"Failed to search entries: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.search.error", duration)
            return []

    async def get_health(self) -> Dict[str, Any]:
        """Get health information about the storage backend.

        Returns:
            A dictionary containing health information
        """
        start_time = time.time()
        try:
            async with self.lock:
                # Get memory usage statistics
                memory_usage = {}
                total_keys = 0
                total_scopes = len(self.data)

                for scope, keys in self.data.items():
                    total_keys += len(keys)
                    memory_usage[scope] = len(keys)

                health = {
                    "status": "healthy",
                    "type": "in-memory",
                    "initialized": self._initialized,
                    "scopes": total_scopes,
                    "keys": total_keys,
                    "memory_usage": memory_usage,
                    "stats": self.stats,
                    "persistence": bool(self.persistence_path),
                    "search_index_enabled": self.enable_search_index,
                }

            duration = time.time() - start_time
            self.perf.record_operation("storage.get_health", duration)
            return health
        except Exception as e:
            logger.error(f"Failed to get health information: {e}")
            duration = time.time() - start_time
            self.perf.record_operation("storage.get_health.error", duration)
            return {"status": "unhealthy", "error": str(e), "type": "in-memory"}

    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to storage.

        Args:
            key: The key to store the entry under
            entry: The memory entry to store

        Returns:
            True if successful, False otherwise
        """
        # Map to the store method
        return await self.store(key, entry, getattr(entry, "scope", "default"))

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from storage.

        Args:
            key: The key to retrieve

        Returns:
            The memory entry if found, None otherwise
        """
        # Map to the retrieve method
        return await self.retrieve(key)

    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash.

        Args:
            content_hash: The content hash to search for

        Returns:
            The memory entry if found, None otherwise
        """
        # This is a slow operation as we need to scan all entries
        try:
            async with self.lock:
                for scope_data in self.data.values():
                    for key, value in scope_data.items():
                        # Check if it's a MemoryEntry with matching hash
                        if (
                            isinstance(value, dict)
                            and value.get("metadata", {}).get("content_hash")
                            == content_hash
                        ):
                            entry = await self.retrieve(key)
                            if entry:
                                return entry
            return None
        except Exception as e:
            logger.error(f"Error retrieving by hash: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Get health information about the storage backend.

        Returns:
            A dictionary containing health information
        """
        # Map to get_health method
        return await self.get_health()

    async def _clean_expired_keys(self, scope: str) -> int:
        """Clean expired keys in a scope.

        Args:
            scope: The scope to clean

        Returns:
            Number of keys removed
        """
        if scope not in self.ttls:
            return 0

        # No need for lock since this is called from methods that already hold the lock
        current_time = time.time()
        expired_keys = []

        for key, expiry_time in self.ttls[scope].items():
            if current_time > expiry_time:
                expired_keys.append(key)

        # Remove expired keys
        for key in expired_keys:
            if key in self.data[scope]:
                del self.data[scope][key]

            del self.ttls[scope][key]

            # Remove from search index
            if self.enable_search_index and scope in self.search_index:
                for term_keys in self.search_index[scope].values():
                    if key in term_keys:
                        term_keys.remove(key)

            self.stats["expirations"] += 1

        return len(expired_keys)

    async def _update_search_index(self, key: str, entry: Any, scope: str) -> None:
        """Update the search index for an entry.

        Args:
            key: The key of the entry
            entry: The entry to index
            scope: The scope of the entry
        """
        if not self.enable_search_index:
            return

        # Create scope index if it doesn't exist
        if scope not in self.search_index:
            self.search_index[scope] = {}

        # Get all terms to index
        terms = self._get_index_terms(key, entry)

        # Remove existing terms for this key
        for term_dict in self.search_index[scope].values():
            if key in term_dict:
                term_dict.remove(key)

        # Add new terms
        for term in terms:
            if term not in self.search_index[scope]:
                self.search_index[scope][term] = set()
            self.search_index[scope][term].add(key)

    def _get_index_terms(self, key: str, entry: Any) -> Set[str]:
        """Get all terms to index from an entry.

        Args:
            key: The key of the entry
            entry: The entry to get terms from

        Returns:
            A set of terms
        """
        terms = set()

        # Add terms from key
        terms.update(self._get_search_terms(key))

        # Add terms from entry
        if isinstance(entry, dict):
            # Add terms from specified fields
            for field_name, field_value in entry.items():
                if isinstance(field_value, str):
                    terms.update(self._get_search_terms(field_value))
                elif isinstance(field_value, (int, float, bool)):
                    terms.add(str(field_value).lower())
        elif isinstance(entry, str):
            terms.update(self._get_search_terms(entry))
        elif isinstance(entry, (int, float, bool)):
            terms.add(str(entry).lower())
        elif hasattr(entry, "__dict__"):
            # For objects, use their string representation
            terms.update(self._get_search_terms(str(entry)))

        return terms

    def _get_search_terms(self, text: str) -> Set[str]:
        """Extract search terms from text.

        Args:
            text: The text to extract terms from

        Returns:
            A set of terms
        """
        if not text:
            return set()

        # Remove punctuation, convert to lowercase, and split by whitespace
        terms = set()
        import re

        # Remove non-alphanumeric characters and split by whitespace
        words = re.sub(r"[^\w\s]", " ", text.lower()).split()

        # Filter out very short words and common stop words
        stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "of",
        }

        for word in words:
            if len(word) > 2 and word not in stop_words:
                terms.add(word)

        return terms

    async def _persist_to_storage(self) -> bool:
        """Persist data to storage.

        Returns:
            True if successful, False otherwise
        """
        if not self.persistence_path:
            return False

        try:
            import os
            import json
            from pathlib import Path

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)

            # Serialize data
            data_to_persist = {}
            for scope, keys in self.data.items():
                data_to_persist[scope] = {}
                for key, value in keys.items():
                    # Include TTL information if available
                    ttl_remaining = None
                    if scope in self.ttls and key in self.ttls[scope]:
                        ttl_remaining = max(0, self.ttls[scope][key] - time.time())

                    data_to_persist[scope][key] = {
                        "value": value,
                        "ttl_remaining": ttl_remaining,
                    }

            # Write to temporary file first
            temp_path = f"{self.persistence_path}.tmp"
            with open(temp_path, "w") as f:
                json.dump(data_to_persist, f)

            # Rename to actual file (atomic operation)
            import os

            os.replace(temp_path, self.persistence_path)

            return True
        except Exception as e:
            logger.error(f"Failed to persist data: {e}")
            return False

    async def _load_from_persistence(self) -> bool:
        """Load data from persistence.

        Returns:
            True if successful, False otherwise
        """
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return False

        try:
            import json

            with open(self.persistence_path, "r") as f:
                persisted_data = json.load(f)

            # Load data
            current_time = time.time()

            for scope, keys in persisted_data.items():
                # Create scope if it doesn't exist
                if scope not in self.data:
                    self.data[scope] = {}
                    self.ttls[scope] = {}
                    if self.enable_search_index:
                        self.search_index[scope] = {}

                for key, data in keys.items():
                    # Extract value and TTL
                    value = data["value"]
                    ttl_remaining = data.get("ttl_remaining")

                    # Store the value
                    self.data[scope][key] = value

                    # Set TTL if available
                    if ttl_remaining is not None and ttl_remaining > 0:
                        self.ttls[scope][key] = current_time + ttl_remaining

                    # Update search index if enabled
                    if self.enable_search_index:
                        await self._update_search_index(key, value, scope)

            logger.info(f"Loaded data from {self.persistence_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load persisted data: {e}")
            return False
