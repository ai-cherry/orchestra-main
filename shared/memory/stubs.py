"""
Stub implementations for testing and development.
"""
import random
from typing import List, Optional

from shared.models.base_models import MemoryItem
from shared.memory.memory_manager import MemoryManager


class PatrickMemoryManager(MemoryManager):
    """
    A stub memory manager that always returns Patrick Star themed memories.
    For testing and demonstration purposes only.
    """
    
    _patrick_quotes = [
        "Is mayonnaise an instrument?",
        "The inner machinations of my mind are an enigma.",
        "I can't see my forehead!",
        "We should take Bikini Bottom and push it somewhere else!",
        "I wumbo, you wumbo, he/she/we wumbo.",
        "It's not just any boulder... It's a rock!",
        "I love being purple!",
        "Leedle leedle leedle lee!",
        "I'm so mad, I could just... uh, I don't know."
    ]
    
    async def store(self, memory_item: MemoryItem) -> str:
        """
        Pretends to store a memory but actually does nothing.
        Returns a fake ID.
        """
        return f"patrick_mem_{random.randint(1000, 9999)}"
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Returns a Patrick-themed memory regardless of the ID.
        """
        return MemoryItem(
            id=memory_id,
            content=random.choice(self._patrick_quotes),
            timestamp=random.random() * 1000000,
            metadata={"source": "patrick", "reliability": "questionable"}
        )
    
    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """
        Returns a list of Patrick-themed memories regardless of the query.
        """
        results = []
        for i in range(min(limit, 5)):  # Never return more than 5 results
            results.append(MemoryItem(
                id=f"patrick_search_{i}",
                content=random.choice(self._patrick_quotes),
                timestamp=random.random() * 1000000,
                metadata={"source": "patrick", "relevance": random.random()}
            ))
        return results
    
    async def delete(self, memory_id: str) -> bool:
        """
        Pretends to delete a memory. Always returns True.
        """
        return True