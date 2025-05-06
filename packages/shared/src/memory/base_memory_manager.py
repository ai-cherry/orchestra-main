import abc
from typing import Dict, List, Optional, Any

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.memory.memory_interface import MemoryInterface

class BaseMemoryManager(MemoryInterface):
    """
    Abstract base class for memory managers.

    This class defines the interface for interacting with memory systems.
    """
    @abc.abstractmethod
    async def add_memory_item(self, item: MemoryItem) -> str:
        """Add a memory item to storage."""
        pass

    @abc.abstractmethod
    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory item by ID."""
        pass

    @abc.abstractmethod
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """Retrieve conversation history for a user."""
        pass

    @abc.abstractmethod
    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """Perform semantic search using vector embeddings."""
        pass

    @abc.abstractmethod
    async def add_raw_agent_data(self, data: AgentData) -> str:
        """Store raw agent data."""
        pass

    @abc.abstractmethod
    async def check_duplicate(self, item: MemoryItem) -> bool:
        """Check if a memory item already exists in storage."""
        pass

    @abc.abstractmethod
    async def cleanup_expired_items(self) -> int:
        """Remove expired items from storage."""
        pass

    # Add other methods as needed based on the MemoryInterface
    # For example, add_message_to_conversation if it's part of the interface
    # @abc.abstractmethod
    # async def add_message_to_conversation(self, conversation_id: str, message: dict):
    #     pass
