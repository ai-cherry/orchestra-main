"""
Memory interface for AI Orchestra.

This module defines the interface for memory implementations.
"""

import abc
from typing import Any, Dict, List, Optional


class MemoryInterface(abc.ABC):
    """Abstract base class for memory implementations."""

    @abc.abstractmethod
    async def store(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store an item in memory.

        Args:
            key: The key to store the value under
            value: The value to store
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """

    @abc.abstractmethod
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from memory.

        Args:
            key: The key to retrieve

        Returns:
            The stored value, or None if not found
        """

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete an item from memory.

        Args:
            key: The key to delete

        Returns:
            True if successful, False otherwise
        """

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if an item exists in memory.

        Args:
            key: The key to check

        Returns:
            True if the item exists, False otherwise
        """

    @abc.abstractmethod
    async def search(self, field: str, value: Any, operator: str = "==", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for items in memory.

        Args:
            field: The field to search on
            value: The value to search for
            operator: The comparison operator to use
            limit: Maximum number of results to return

        Returns:
            List of matching items
        """

    async def update(self, key: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item in memory.

        Args:
            key: The key of the item to update
            updates: The fields to update

        Returns:
            True if successful, False otherwise
        """
        # Default implementation: retrieve, update, store
        item = await self.retrieve(key)
        if item is None:
            return False

        item.update(updates)
        return await self.store(key, item)

    async def clear_all(self) -> bool:
        """
        Clear all items from memory.

        Returns:
            True if successful, False otherwise
        """
        # Default implementation: not supported
        return False

    async def batch_store(self, items: Dict[str, Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """
        Store multiple items in memory.

        Args:
            items: Dictionary mapping keys to values
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if all items were stored successfully, False otherwise
        """
        # Default implementation: store each item individually
        success = True
        for key, value in items.items():
            if not await self.store(key, value, ttl):
                success = False
        return success

    async def batch_retrieve(self, keys: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve multiple items from memory.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dictionary mapping keys to values (or None if not found)
        """
        # Default implementation: retrieve each item individually
        result = {}
        for key in keys:
            result[key] = await self.retrieve(key)
        return result

    async def batch_delete(self, keys: List[str]) -> bool:
        """
        Delete multiple items from memory.

        Args:
            keys: List of keys to delete

        Returns:
            True if all items were deleted successfully, False otherwise
        """
        # Default implementation: delete each item individually
        success = True
        for key in keys:
            if not await self.delete(key):
                success = False
        return success
