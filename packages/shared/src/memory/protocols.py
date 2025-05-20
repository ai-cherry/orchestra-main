"""
Protocols for memory management in the Orchestra system.

This module defines the interfaces for memory management operations, ensuring a clear contract
for different memory backend implementations.
"""

from typing import Protocol, List, Any
from packages.shared.src.models.base_models import MemoryItem


class MemoryManagerProtocol(Protocol):
    """
    Protocol defining the interface for memory management operations.
    """

    async def get_memories(self, user_id: str, limit: int = 10) -> List[MemoryItem]:
        """
        Retrieve memories for a specific user.

        Args:
            user_id: The identifier of the user whose memories are to be retrieved.
            limit: The maximum number of memory items to return. Defaults to 10.

        Returns:
            A list of MemoryItem objects associated with the user.
        """
        ...

    async def add_memory(self, user_id: str, memory: MemoryItem) -> None:
        """
        Add a memory item for a specific user.

        Args:
            user_id: The identifier of the user to associate the memory with.
            memory: The MemoryItem to be added.
        """
        ...
