"""
Memory module for AI Orchestration System.

This module provides memory management functionality for storing and retrieving
conversation history and other relevant information.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import logging
import uuid
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Base class for items stored in memory."""

    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    item_type: str = "generic"
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryProvider(ABC):
    """Abstract base class for memory providers."""

    @abstractmethod
    def add_item(self, item: MemoryItem) -> str:
        """
        Add an item to memory.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item
        """
        pass

    @abstractmethod
    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get an item from memory by ID.

        Args:
            item_id: The ID of the item to get

        Returns:
            The memory item, or None if not found
        """
        pass

    @abstractmethod
    def get_items(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        item_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryItem]:
        """
        Get items from memory.

        Args:
            user_id: The user ID to filter by
            session_id: Optional session ID to filter by
            item_type: Optional item type to filter by
            limit: Maximum number of items to return

        Returns:
            List of memory items
        """
        pass


class InMemoryProvider(MemoryProvider):
    """Memory provider that stores items in memory."""

    def __init__(self):
        """Initialize the in-memory provider."""
        self._items: Dict[str, MemoryItem] = {}

    def add_item(self, item: MemoryItem) -> str:
        """Add an item to memory."""
        self._items[item.item_id] = item
        return item.item_id

    def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """Get an item from memory by ID."""
        return self._items.get(item_id)

    def get_items(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        item_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryItem]:
        """Get items from memory."""
        items = []
        for item in self._items.values():
            if item.user_id != user_id:
                continue

            if session_id is not None and item.session_id != session_id:
                continue

            if item_type is not None and item.item_type != item_type:
                continue

            items.append(item)

            if len(items) >= limit:
                break

        # Sort by timestamp
        items.sort(key=lambda x: x.timestamp)
        return items


class MemoryManager:
    """
    Central manager for memory operations.

    This class provides a unified interface to memory operations, delegating
    to the appropriate memory provider based on the operation type.
    """

    def __init__(self, provider: MemoryProvider = None):
        """
        Initialize the memory manager.

        Args:
            provider: Memory provider to use (defaults to InMemoryProvider)
        """
        self._provider = provider or InMemoryProvider()
        logger.info(
            f"MemoryManager initialized with provider: {self._provider.__class__.__name__}"
        )

    def add_memory(
        self,
        user_id: str,
        content: Any,
        session_id: str = None,
        item_type: str = "conversation",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Add a memory item.

        Args:
            user_id: The ID of the user
            content: The content to store
            session_id: Optional session ID
            item_type: The type of item
            metadata: Optional metadata

        Returns:
            The ID of the added item
        """
        # Generate a session ID if not provided
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        # Create memory item
        item = MemoryItem(
            user_id=user_id,
            session_id=session_id,
            item_type=item_type,
            content=content,
            metadata=metadata or {},
        )

        # Add to provider
        return self._provider.add_item(item)

    def get_memory(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get a memory item by ID.

        Args:
            item_id: The ID of the item to get

        Returns:
            The memory item, or None if not found
        """
        return self._provider.get_item(item_id)

    def get_conversation_history(
        self, user_id: str, session_id: Optional[str] = None, limit: int = 10
    ) -> List[MemoryItem]:
        """
        Get conversation history for a user.

        Args:
            user_id: The ID of the user
            session_id: Optional session ID to filter by
            limit: Maximum number of items to return

        Returns:
            List of memory items
        """
        return self._provider.get_items(
            user_id=user_id,
            session_id=session_id,
            item_type="conversation",
            limit=limit,
        )

    def get_memories_by_type(
        self,
        user_id: str,
        item_type: str,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryItem]:
        """
        Get memories of a specific type.

        Args:
            user_id: The ID of the user
            item_type: The type of items to get
            session_id: Optional session ID to filter by
            limit: Maximum number of items to return

        Returns:
            List of memory items
        """
        return self._provider.get_items(
            user_id=user_id, session_id=session_id, item_type=item_type, limit=limit
        )


# Global memory manager instance
_memory_manager = None


def get_memory_manager() -> MemoryManager:
    """
    Get the global memory manager instance.

    Returns:
        The memory manager instance
    """
    global _memory_manager

    if _memory_manager is None:
        _memory_manager = MemoryManager()

    return _memory_manager
