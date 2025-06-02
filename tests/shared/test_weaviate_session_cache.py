import asyncio

from shared.memory.weaviate_session_cache import WeaviateSessionCache

class DummyAdapter:
    def __init__(self):
        self.set_calls = []
        self.query_calls = []

    async def batch_upsert(self, objs):
        self.set_calls.append(objs)

    async def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return [{"properties": {"data": {"foo": "bar"}}}]

def test_set_get(monkeypatch):
    cache = WeaviateSessionCache()
    dummy = DummyAdapter()
    monkeypatch.setattr(cache, "_adapter", dummy)

    asyncio.run(cache.set_json("k", {"foo": "bar"}))
    result = asyncio.run(cache.get_json("k"))

    assert dummy.set_calls
    assert dummy.query_calls
    assert result == {"foo": "bar"}
