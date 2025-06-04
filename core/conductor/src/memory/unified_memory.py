# TODO: Consider adding connection pooling configuration
"""
"""
logger = logging.getLogger("unified_memory")

# --- Error Handling Decorator ---
def log_and_handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:

            pass
            return func(*args, **kwargs)
        except Exception:

            pass
            logger.error(f"Memory operation failed in {func.__name__}: {e}", exc_info=True)
            raise

    return wrapper

def async_log_and_handle_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:

            pass
            return await func(*args, **kwargs)
        except Exception:

            pass
            logger.error(f"Async memory operation failed in {func.__name__}: {e}", exc_info=True)
            raise

    return wrapper

# --- Protocols ---
class MemoryAdapter(Protocol):
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> None: ...
    def search(self, query: str, top_k: int = 5) -> List[Any]: ...

class AsyncMemoryAdapter(Protocol):
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def search(self, query: str, top_k: int = 5) -> List[Any]: ...

# --- Adapter Registry ---
class MemoryAdapterRegistry:
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str, adapter_cls: Type) -> None:
        cls._registry[name] = adapter_cls

    @classmethod
    def get_adapter(cls, name: str) -> Optional[Type]:
        return cls._registry.get(name)

# --- MongoDB Adapter (Sync) ---
class MongoDBMemoryAdapter:
    """MongoDB-backed memory adapter with connection pooling."""
    def __init__(self, mongo_uri: str, db_name: str = "cherry_ai", collection: str = "memory"):
        from pymongo import MongoClient

        self.client = MongoClient(mongo_uri, maxPoolSize=10)
        self.collection = self.client[db_name][collection]

    @log_and_handle_errors
    def get(self, key: str) -> Optional[Any]:
        doc = self.collection.find_one({"_id": key})
        return doc["value"] if doc else None

    @log_and_handle_errors
    def set(self, key: str, value: Any) -> None:
        self.collection.update_one({"_id": key}, {"$set": {"value": value}}, upsert=True)

    @log_and_handle_errors
    def delete(self, key: str) -> None:
        self.collection.delete_one({"_id": key})

    @log_and_handle_errors
    def search(self, query: str, top_k: int = 5) -> List[Any]:
        results = self.collection.find({"value": {"$regex": query, "$options": "i"}}).limit(top_k)
        return [doc["value"] for doc in results]

MemoryAdapterRegistry.register("mongodb", MongoDBMemoryAdapter)

# --- Weaviate Adapter (Async) ---
class WeaviateMemoryAdapter:
    """Weaviate-backed semantic memory adapter (async)."""
        return res["properties"] if res else None

    @async_log_and_handle_errors
    async def set(self, key: str, value: Dict[str, Any]) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.data_object.create(data_object=value, class_name="Memory", uuid=key),
        )

    @async_log_and_handle_errors
    async def delete(self, key: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.client.data_object.delete(uuid=key, class_name="Memory"))

    @async_log_and_handle_errors
    async def search(self, query: str, top_k: int = 5) -> List[Any]:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None,
            lambda: self.client.query.get("Memory", ["content"])
            .with_near_text({"concepts": [query]})
            .with_limit(top_k)
            .do(),
        )
        return [item["content"] for item in res["data"]["Get"]["Memory"]]

MemoryAdapterRegistry.register("weaviate", WeaviateMemoryAdapter)

# --- Dragonfly Adapter (Sync) ---
class DragonflyMemoryAdapter:
    """DragonflyDB-backed key-value memory adapter."""
        keys = self.client.keys("*")
        matches = [k for k in keys if query in k]
        return [self.client.get(k) for k in matches[:top_k]]

MemoryAdapterRegistry.register("dragonfly", DragonflyMemoryAdapter)

# --- Unified Memory Manager ---
class UnifiedMemoryManager:
    """
    """
        backend = config.get("backend")
        adapter_cls = MemoryAdapterRegistry.get_adapter(backend)
        if not adapter_cls:
            raise ValueError(f"Unsupported memory backend: {backend}")
        self.adapter = adapter_cls(**{k: v for k, v in config.items() if k != "backend"})

    def get(self, key: str) -> Optional[Any]:
        return self.adapter.get(key)

    def set(self, key: str, value: Any) -> None:
        self.adapter.set(key, value)

    def delete(self, key: str) -> None:
        self.adapter.delete(key)

    def search(self, query: str, top_k: int = 5) -> List[Any]:
        return self.adapter.search(query, top_k)

    async def aget(self, key: str) -> Optional[Any]:
        if hasattr(self.adapter, "get") and asyncio.iscoroutinefunction(self.adapter.get):
            return await self.adapter.get(key)
        return self.get(key)

    async def aset(self, key: str, value: Any) -> None:
        if hasattr(self.adapter, "set") and asyncio.iscoroutinefunction(self.adapter.set):
            await self.adapter.set(key, value)
        else:
            self.set(key, value)

    async def adelete(self, key: str) -> None:
        if hasattr(self.adapter, "delete") and asyncio.iscoroutinefunction(self.adapter.delete):
            await self.adapter.delete(key)
        else:
            self.delete(key)

    async def asearch(self, query: str, top_k: int = 5) -> List[Any]:
        if hasattr(self.adapter, "search") and asyncio.iscoroutinefunction(self.adapter.search):
            return await self.adapter.search(query, top_k)
        return self.search(query, top_k)
