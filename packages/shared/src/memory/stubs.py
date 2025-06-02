from typing import Any, Dict, Tuple, List

class InMemoryMemoryManagerStub:
    """A simplistic in-memory key-value store used as a stub for real memory managers."""

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    # Optional initialization routine
    def initialize(self) -> None:  # noqa: D401  # Simple placeholder
        """Initialize the stub (no-op)."""
        pass

    # Sync store API -----------------------------------------------------
    def store(self, key: str, value: Any) -> bool:
        self._store[key] = value
        return True

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    # Redis-like SCAN implementation (simplified) ------------------------
    def scan(self, cursor: str = "0", match: str | None = None, count: int = 10) -> Tuple[str, List[str]]:  # noqa: D401
        """Return a fake cursor and keys matching simple prefix match."""
        keys = list(self._store.keys())
        if match:
            # Very naive glob-like prefix filtering
            prefix = match.rstrip("*")
            keys = [k for k in keys if k.startswith(prefix)]
        return "0", keys[:count]

    def ttl(self, key: str) -> int:
        # No TTL support in stub
        return -1

    # Async variants -----------------------------------------------------
    async def store_async(self, key: str, value: Any) -> bool:
        return self.store(key, value)

    async def get_async(self, key: str) -> Any:
        return self.get(key)

    async def delete_async(self, key: str) -> bool:
        return self.delete(key)

    async def scan_async(self, cursor: str = "0", match: str | None = None, count: int = 10):
        return self.scan(cursor, match, count) 