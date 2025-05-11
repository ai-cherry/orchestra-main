#!/usr/bin/env python3
"""
memory_adapter.py - Memory Storage Adapters

This module provides adapters for memory storage implementations to make them
compatible with the MCP server's interfaces.
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple

from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry, MemoryMetadata

logger = logging.getLogger(__name__)


class StorageBridgeAdapter(IMemoryStorage):
    """
    Adapter class that bridges between our new optimized storage implementation
    and the existing storage interface expected by the memory manager.

    This class implements the IMemoryStorage interface while delegating to our new
    more performant storage implementation.
    """

    def __init__(self, storage):
        """Initialize with a storage backend.

        Args:
            storage: An instance of OptimizedMemoryStorage
        """
        self.storage = storage
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Initialize the storage adapter.

        Returns:
            True if successful, False otherwise
        """
        return await self.storage.initialize()

    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry.

        Args:
            key: The key to store the entry under
            entry: The memory entry to store

        Returns:
            True if successful, False otherwise
        """
        # Determine scope from entry if available
        scope = "default"
        if hasattr(entry, 'scope') and entry.scope:
            scope = entry.scope

        # Store using the optimized storage
        return await self.storage.store(key, entry, scope)

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry.

        Args:
            key: The key to retrieve

        Returns:
            The memory entry if found, None otherwise
        """
        # Retrieve from the optimized storage
        result = await self.storage.retrieve(key)
        return result

    async def delete(self, key: str) -> bool:
        """Delete a memory entry.

        Args:
            key: The key to delete

        Returns:
            True if successful, False otherwise
        """
        # Delete from the optimized storage
        return await self.storage.delete(key)

    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix.

        Args:
            prefix: Optional prefix to filter keys by

        Returns:
            A list of keys
        """
        # List keys from the optimized storage
        all_keys = await self.storage.list_keys()

        # Filter by prefix if provided
        if prefix:
            return [key for key in all_keys if key.startswith(prefix)]
        return all_keys

    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash.

        Args:
            content_hash: The content hash to search for

        Returns:
            The memory entry if found, None otherwise
        """
        # This is a slow operation as we need to search through all entries
        async with self._lock:
            # Search for entries with the matching hash
            results = await self.storage.search(content_hash, limit=1)
            if results:
                # Extract the key from the first result
                result_key = results[0].get("key", None)
                if result_key:
                    # Retrieve the full entry
                    return await self.get(result_key)
        return None

    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, MemoryEntry, float]]:
        """Search for memory entries matching the query.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            A list of tuples containing (key, entry, score)
        """
        # Search using the optimized storage
        results = await self.storage.search(query, limit=limit)

        # Convert to expected format
        converted_results = []
        for result in results:
            key = result.get("_key", "unknown")
            # The content might be stored in different formats
            if isinstance(result, dict) and "_key" in result:
                content_dict = dict(result)
                content_dict.pop("_key", None)
                entry = content_dict
            else:
                entry = result

            # Convert to MemoryEntry if it's not already
            if not isinstance(entry, MemoryEntry):
                try:
                    # Try to convert to MemoryEntry
                    metadata = MemoryMetadata(
                        source_tool="unknown",
                        last_modified=time.time(),
                        access_count=0,
                        context_relevance=1.0,
                        last_accessed=time.time(),
                        version=1,
                        sync_status={},
                        content_hash=None
                    )
                    memory_entry = MemoryEntry(
                        content=entry,
                        metadata=metadata
                    )
                except:
                    # Fall back to raw entry
                    memory_entry = entry

            converted_results.append((key, memory_entry, 1.0))  # Score is hardcoded for now

        return converted_results

    async def health_check(self) -> Dict[str, Any]:
        """Get health information about the storage backend.

        Returns:
            A dictionary containing health information
        """
        # Get health info from the optimized storage
        health_info = await self.storage.get_health()
        return health_info
