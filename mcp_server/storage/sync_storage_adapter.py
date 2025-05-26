#!/usr/bin/env python3
"""
sync_storage_adapter.py - Synchronous Storage Adapter

This module provides a synchronous adapter for async storage implementations,
making it easier to integrate with both synchronous and asynchronous code.
"""

import asyncio
import logging
import threading
from typing import Any, Dict, List, Optional

from ..interfaces.storage import IMemoryStorage
from ..utils.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)


class SyncStorageAdapter:
    """Adapter to use async storage implementations in a synchronous context."""

    def __init__(self, storage: IMemoryStorage):
        """Initialize with an async storage implementation.

        Args:
            storage: The async storage implementation to adapt
        """
        self.storage = storage
        self.loop = self._get_event_loop()
        self.perf = get_performance_monitor()
        self._lock = threading.RLock()

    def _get_event_loop(self):
        """Get or create an event loop for async operations."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            # Create a new loop if none exists in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def _run_coroutine(self, coro):
        """Run a coroutine synchronously.

        Args:
            coro: The coroutine to run

        Returns:
            The result of the coroutine
        """
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # We're in a running event loop, create a future and run it
                return asyncio.run_coroutine_threadsafe(coro, loop).result()
        except RuntimeError:
            # We're not in an event loop
            pass

        # Run the coroutine in our loop
        with self._lock:
            return self.loop.run_until_complete(coro)

    def initialize(self) -> bool:
        """Initialize the storage backend."""
        return self._run_coroutine(self.storage.initialize())

    def store(self, key: str, entry, scope: str = "default") -> bool:
        """Store an entry in the storage backend.

        Args:
            key: The key to store under
            entry: The entry to store
            scope: The scope to store in

        Returns:
            True if successful, False otherwise
        """
        return self._run_coroutine(self.storage.store(key, entry, scope))

    def retrieve(self, key: str, scope: str = "default") -> Optional[Any]:
        """Retrieve an entry from the storage backend.

        Args:
            key: The key to retrieve
            scope: The scope to retrieve from

        Returns:
            The retrieved entry, or None if not found
        """
        return self._run_coroutine(self.storage.retrieve(key, scope))

    def delete(self, key: str, scope: str = "default") -> bool:
        """Delete an entry from the storage backend.

        Args:
            key: The key to delete
            scope: The scope to delete from

        Returns:
            True if successful, False otherwise
        """
        return self._run_coroutine(self.storage.delete(key, scope))

    def list_keys(self, scope: str = "default") -> List[str]:
        """List all keys in a scope.

        Args:
            scope: The scope to list keys from

        Returns:
            A list of keys
        """
        return self._run_coroutine(self.storage.list_keys(scope))

    def search(
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
        return self._run_coroutine(self.storage.search(query, scope, limit))

    def get_health(self) -> Dict[str, Any]:
        """Get health information about the storage backend.

        Returns:
            A dictionary containing health information
        """
        return self._run_coroutine(self.storage.get_health())
