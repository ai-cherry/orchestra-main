"""
Memory provider interface for AI Orchestra.

This module defines the protocol for memory storage providers.
"""

from typing import Protocol, Any, Optional, Dict, List


class MemoryProvider(Protocol):
    """Memory storage provider interface."""

    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value with an optional TTL.

        Args:
            key: The key to store the value under
            value: The value to store
            ttl: Optional time-to-live in seconds

        Returns:
            True if the value was stored successfully, False otherwise
        """
        ...

    async def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.

        Args:
            key: The key to retrieve the value for

        Returns:
            The stored value, or None if not found
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        Delete a value by key.

        Args:
            key: The key to delete

        Returns:
            True if the value was deleted successfully, False otherwise
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        ...

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """
        List keys matching a pattern.

        Args:
            pattern: The pattern to match keys against

        Returns:
            A list of matching keys
        """
        ...
