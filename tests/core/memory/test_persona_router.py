import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import pytest

from core.services.memory.base import MemoryLayer, MemoryItem, SearchResult, MemoryService
from core.services.memory.persona_router import PersonaMemoryRouter
from core.services.memory.meta_graph import MetaGraph


class FakeMemory(MemoryService):
    def __init__(self):
        self.items: Dict[str, MemoryItem] = {}

    async def store(self, content, metadata=None, layer=None, ttl=None, item_id=None, vector=None):
        item_id = item_id or str(len(self.items) + 1)
        metadata = metadata or {}
        item = MemoryItem(id=item_id, content=content, metadata=metadata, timestamp=datetime.utcnow(), layer=layer or MemoryLayer.SHORT_TERM)
        self.items[item_id] = item
        return item_id

    async def retrieve(self, item_id):
        return self.items.get(item_id)

    async def search(self, query, limit=10, layers=None, filters=None):
        results: List[SearchResult] = []
        for it in self.items.values():
            if filters and filters.get("metadata.persona") != it.metadata.get("persona"):
                continue
            if query.lower() in str(it.content).lower():
                results.append(SearchResult(item=it, score=1.0, source=it.layer))
        return results

    async def delete(self, item_id):
        self.items.pop(item_id, None)
        return True

    async def list_items(self, limit=100, offset=0, filters=None):
        return list(self.items.values())[offset:offset+limit]

    async def clear(self):
        count = len(self.items)
        self.items.clear()
        return count

    async def health_check(self):
        return True

    async def promote(self, item_id: str, target_layer: MemoryLayer) -> bool:
        return True

    async def evict(self, item_id: str) -> bool:
        return True

    async def get_stats(self):
        return {}


class DummyMeta(MetaGraph):
    def __init__(self, relations: Dict[str, List[str]]):
        self.relations = relations

    def get_related_personas(self, persona: str, context: str) -> List[str]:
        return self.relations.get(persona, [])


@pytest.mark.asyncio
async def test_persona_isolation():
    mem = FakeMemory()
    await mem.store("hello", {"persona": "cherry"})
    await mem.store("payment", {"persona": "sophia"})

    router = PersonaMemoryRouter("cherry", mem)
    results = await router.query("hello")
    assert len(results) == 1
    assert results[0].item.metadata["persona"] == "cherry"

    results = await router.query("payment")
    assert results == []


@pytest.mark.asyncio
async def test_cross_persona_query():
    mem = FakeMemory()
    await mem.store("hi there", {"persona": "cherry"})
    await mem.store("financial report", {"persona": "sophia"})
    meta = DummyMeta({"cherry": ["sophia"]})
    router = PersonaMemoryRouter("cherry", mem, meta)

    results = await router.query("financial", {"include_related": True})
    assert len(results) == 1
    assert results[0].item.metadata["persona"] == "sophia"

