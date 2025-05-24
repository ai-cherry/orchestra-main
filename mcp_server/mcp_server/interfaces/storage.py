#!/usr/bin/env python3
"""
storage.py - MCP Storage Interface

This module defines the standard interface that all storage implementations
must follow. It ensures consistent functionality across different storage backends
such as in-memory storage, file-based storage, Redis, and AlloyDB.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.memory import MemoryEntry


class IMemoryStorage(ABC):
    """Base interface for all memory storage implementations."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the storage backend."""

    @abstractmethod
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry."""

    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""

    @abstractmethod
    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[tuple[str, MemoryEntry, float]]:
        """Search for memory entries matching the query."""

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend."""


class SyncMemoryStorage:
    """Synchronous wrapper for async memory storage interfaces.

    This class provides a synchronous interface on top of the async storage interface,
    making it easier to use in non-async contexts.
    """

    def __init__(self, async_storage: IMemoryStorage):
        """Initialize with an async storage implementation."""
        self.async_storage = async_storage
        self.loop = asyncio.get_event_loop()

    def initialize(self) -> bool:
        """Initialize the storage backend."""
        return self.loop.run_until_complete(self.async_storage.initialize())

    def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry."""
        return self.loop.run_until_complete(self.async_storage.save(key, entry))

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        return self.loop.run_until_complete(self.async_storage.get(key))

    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        return self.loop.run_until_complete(self.async_storage.delete(key))

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        return self.loop.run_until_complete(self.async_storage.list_keys(prefix))

    def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        return self.loop.run_until_complete(self.async_storage.get_by_hash(content_hash))

    def search(self, query: str, limit: int = 10) -> List[tuple[str, MemoryEntry, float]]:
        """Search for memory entries matching the query."""
        return self.loop.run_until_complete(self.async_storage.search(query, limit))

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend."""
        return self.loop.run_until_complete(self.async_storage.health_check())
