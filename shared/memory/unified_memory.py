"""
UnifiedMemory: A sophisticated, extensible memory abstraction for AI orchestration.

Integrates DragonflyDB (in-memory cache), Qdrant (vector/semantic search), and Firestore (persistent storage)
under a single, polished interface. Designed for high performance, modularity, and seamless GCP/cloud deployment.

Author: AI Orchestrator
"""

import os
from typing import Optional, List, Dict, Any, Union

# Import backend clients (assume these are installed and configured)
try:
    import redis  # DragonflyDB-compatible
except ImportError:
    redis = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import PointStruct
except ImportError:
    QdrantClient = None

try:
    from google.cloud import firestore
except ImportError:
    firestore = None

from pydantic import BaseModel, Field


# --- Canonical Memory Item Model ---
class MemoryItem(BaseModel):
    id: str = Field(..., description="Unique identifier for this memory item")
    content: str = Field(..., description="Content of the memory")
    source: str = Field(..., description="Source of the memory (e.g., agent ID)")
    timestamp: str = Field(..., description="Timestamp when memory was created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    priority: float = Field(default=0.5, description="Priority of the memory (0.0-1.0)")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding of the memory content")


# --- Unified Memory Abstraction ---
class UnifiedMemory:
    """
    UnifiedMemory provides a seamless, high-performance interface for storing, retrieving,
    searching, and deleting memory items across DragonflyDB, Qdrant, and Firestore backends.

    Backend selection is controlled via environment variables or constructor arguments.
    """

    def __init__(
        self,
        use_dragonfly: bool = True,
        use_qdrant: bool = True,
        use_firestore: bool = True,
        dragonfly_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        firestore_project: Optional[str] = None,
        qdrant_collection: str = "memory_items",
        firestore_collection: str = "memory_items",
    ):
        # --- DragonflyDB (Redis-compatible) ---
        self.dragonfly = None
        if use_dragonfly and redis:
            self.dragonfly = redis.Redis.from_url(
                dragonfly_url or os.getenv("DRAGONFLY_URL", "redis://localhost:6379/0")
            )

        # --- Qdrant (Vector DB) ---
        self.qdrant = None
        self.qdrant_collection = qdrant_collection
        if use_qdrant and QdrantClient:
            self.qdrant = QdrantClient(url=qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333"))

        # --- Firestore (Persistent) ---
        self.firestore = None
        self.firestore_collection = firestore_collection
        if use_firestore and firestore:
            self.firestore = firestore.Client(project=firestore_project or os.getenv("GCP_PROJECT"))

    # --- Store Memory ---
    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item in all enabled backends.
        Returns the memory ID.
        """
        # DragonflyDB (fast cache)
        if self.dragonfly:
            self.dragonfly.hset(f"memory:{item.id}", mapping=item.dict())

        # Qdrant (vector search)
        if self.qdrant and item.embedding:
            self.qdrant.upsert(
                collection_name=self.qdrant_collection,
                points=[PointStruct(id=item.id, vector=item.embedding, payload=item.dict())],
            )

        # Firestore (persistent)
        if self.firestore:
            self.firestore.collection(self.firestore_collection).document(item.id).set(item.dict())

        return item.id

    # --- Retrieve Memory ---
    def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID, preferring cache (Dragonfly), then persistent (Firestore).
        """
        # Try DragonflyDB first
        if self.dragonfly:
            data = self.dragonfly.hgetall(f"memory:{memory_id}")
            if data:
                # Redis returns bytes, decode
                decoded = {k.decode(): v.decode() for k, v in data.items()}
                return MemoryItem(**decoded)

        # Fallback to Firestore
        if self.firestore:
            doc = self.firestore.collection(self.firestore_collection).document(memory_id).get()
            if doc.exists:
                return MemoryItem(**doc.to_dict())

        return None

    # --- Search Memory (Semantic/Vector) ---
    def search(self, query: Union[str, List[float]], limit: int = 10) -> List[MemoryItem]:
        """
        Search memory items.
        - If query is a string: perform metadata/content search (cache or Firestore).
        - If query is a vector: perform semantic search (Qdrant).
        """
        results = []

        # Vector search (Qdrant)
        if self.qdrant and isinstance(query, list):
            search_result = self.qdrant.search(
                collection_name=self.qdrant_collection,
                query_vector=query,
                limit=limit,
            )
            for point in search_result:
                results.append(MemoryItem(**point.payload))
            return results

        # Text search (DragonflyDB or Firestore)
        if self.dragonfly:
            # Naive scan (for demo; optimize with RediSearch if available)
            for key in self.dragonfly.scan_iter("memory:*"):
                data = self.dragonfly.hgetall(key)
                decoded = {k.decode(): v.decode() for k, v in data.items()}
                if query.lower() in decoded.get("content", "").lower():
                    results.append(MemoryItem(**decoded))
                    if len(results) >= limit:
                        break
            if results:
                return results

        # Fallback to Firestore
        if self.firestore:
            docs = self.firestore.collection(self.firestore_collection).limit(100).stream()
            for doc in docs:
                data = doc.to_dict()
                if query.lower() in data.get("content", "").lower():
                    results.append(MemoryItem(**data))
                    if len(results) >= limit:
                        break

        return results

    # --- Delete Memory ---
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory item from all enabled backends.
        Returns True if deleted from at least one backend.
        """
        deleted = False

        if self.dragonfly:
            deleted = self.dragonfly.delete(f"memory:{memory_id}") or deleted

        if self.qdrant:
            self.qdrant.delete(collection_name=self.qdrant_collection, points_selector={"points": [memory_id]})
            deleted = True

        if self.firestore:
            self.firestore.collection(self.firestore_collection).document(memory_id).delete()
            deleted = True

        return deleted

    # --- Health Check ---
    def health(self) -> Dict[str, bool]:
        """
        Returns a dictionary indicating the health of each backend.
        """
        status = {}
        # DragonflyDB
        if self.dragonfly:
            try:
                self.dragonfly.ping()
                status["dragonfly"] = True
            except Exception:
                status["dragonfly"] = False
        # Qdrant
        if self.qdrant:
            try:
                self.qdrant.get_collections()
                status["qdrant"] = True
            except Exception:
                status["qdrant"] = False
        # Firestore
        if self.firestore:
            try:
                # Try listing collections
                list(self.firestore.collections())
                status["firestore"] = True
            except Exception:
                status["firestore"] = False
        return status


# --- Example Usage ---
if __name__ == "__main__":
    # Example: Initialize UnifiedMemory with all backends enabled (env-configurable)
    memory = UnifiedMemory()

    # Example: Store a memory item
    item = MemoryItem(
        id="example1",
        content="This is a test memory for demonstration.",
        source="demo-agent",
        timestamp="2025-05-24T02:43:00Z",
        metadata={"demo": True},
        priority=0.8,
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
    )
    memory.store(item)

    # Example: Retrieve
    retrieved = memory.retrieve("example1")
    print("Retrieved:", retrieved)

    # Example: Search (text)
    results = memory.search("test")
    print("Text search results:", results)

    # Example: Search (vector)
    results = memory.search([0.1, 0.2, 0.3, 0.4, 0.5])
    print("Vector search results:", results)

    # Example: Delete
    deleted = memory.delete("example1")
    print("Deleted:", deleted)

    # Example: Health check
    print("Backend health:", memory.health())
