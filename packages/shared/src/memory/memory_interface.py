import abc
from typing import Dict, List, Optional, Any

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig


class MemoryInterface(abc.ABC):
    @abc.abstractmethod
    async def add_memory_item(self, item: MemoryItem) -> str:
        pass

    @abc.abstractmethod
    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        pass

    @abc.abstractmethod
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        pass

    @abc.abstractmethod
    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        pass

    @abc.abstractmethod
    async def add_raw_agent_data(self, data: AgentData) -> str:
        pass

    @abc.abstractmethod
    async def check_duplicate(self, item: MemoryItem) -> bool:
        pass

    @abc.abstractmethod
    async def cleanup_expired_items(self) -> int:
        pass
