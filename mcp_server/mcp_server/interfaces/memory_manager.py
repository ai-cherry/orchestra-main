#!/usr/bin/env python3
"""
memory_manager.py - MCP Memory Manager Interface

This module defines the standard interface for memory managers, which coordinate
memory operations across tools, handle context window optimization, and ensure
consistent memory synchronization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from ..models.memory import MemoryEntry


class IMemoryManager(ABC):
    """Interface for memory managers."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the memory manager."""
        pass

    @abstractmethod
    async def create_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Create a new memory entry."""
        pass

    @abstractmethod
    async def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool."""
        pass

    @abstractmethod
    async def update_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Update an existing memory entry."""
        pass

    @abstractmethod
    async def delete_memory(self, key: str, source_tool: str) -> bool:
        """Delete a memory entry."""
        pass

    @abstractmethod
    async def search_memory(self, query: str, tool: str, limit: int = 10) -> List[tuple[str, MemoryEntry, float]]:
        """Search for memory entries for a specific tool."""
        pass

    @abstractmethod
    async def optimize_context_window(self, tool: str, required_keys: Optional[List[str]] = None) -> int:
        """Optimize the context window for a specific tool."""
        pass

    @abstractmethod
    async def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system."""
        pass


class SyncMemoryManager:
    """Synchronous wrapper for async memory manager interfaces.

    This class provides a synchronous interface on top of the async memory manager interface,
    making it easier to use in non-async contexts.
    """

    def __init__(self, async_manager: IMemoryManager):
        """Initialize with an async memory manager implementation."""
        import asyncio

        self.async_manager = async_manager
        self.loop = asyncio.get_event_loop()

    def initialize(self) -> bool:
        """Initialize the memory manager."""
        return self.loop.run_until_complete(self.async_manager.initialize())

    def create_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Create a new memory entry."""
        return self.loop.run_until_complete(self.async_manager.create_memory(key, entry, source_tool))

    def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool."""
        return self.loop.run_until_complete(self.async_manager.get_memory(key, tool))

    def update_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Update an existing memory entry."""
        return self.loop.run_until_complete(self.async_manager.update_memory(key, entry, source_tool))

    def delete_memory(self, key: str, source_tool: str) -> bool:
        """Delete a memory entry."""
        return self.loop.run_until_complete(self.async_manager.delete_memory(key, source_tool))

    def search_memory(self, query: str, tool: str, limit: int = 10) -> List[tuple[str, MemoryEntry, float]]:
        """Search for memory entries for a specific tool."""
        return self.loop.run_until_complete(self.async_manager.search_memory(query, tool, limit))

    def optimize_context_window(self, tool: str, required_keys: Optional[List[str]] = None) -> int:
        """Optimize the context window for a specific tool."""
        return self.loop.run_until_complete(self.async_manager.optimize_context_window(tool, required_keys))

    def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system."""
        return self.loop.run_until_complete(self.async_manager.get_memory_status())
