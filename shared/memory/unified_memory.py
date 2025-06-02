"""
UnifiedMemory: A sophisticated, extensible memory abstraction for AI orchestration.

Integrates Weaviate (vector/semantic search, primary), PostgreSQL (ACID operations),
and optionally DragonflyDB (in-memory cache) under a single, polished interface.
Designed for high performance, modularity, and seamless stack-native deployment.

Author: AI Orchestrator
"""

from typing import Any, Dict, List, Optional, Union, Literal
import uuid
from datetime import datetime

from core.env_config import settings

# Import backend clients (assume these are installed and configured)
try:
    import redis  # DragonflyDB-compatible
except ImportError:
    redis = None

try:
    import weaviate
except ImportError:
    weaviate = None

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

                # Scan keys and filter by content
                for key in self.dragonfly.scan_iter(key_pattern):
                    data = self.dragonfly.hgetall(key)
                    if not data:
                        continue

                    # Decode data
                    decoded = {k.decode(): v.decode() for k, v in data.items()}

                    # Check domain filter if provided
                    if domain and decoded.get("domain") != domain:
                        continue

                    # Check additional filters if provided
                    if filters:
                        skip = False
                        for k, v in filters.items():
                            if k in decoded:
                                if isinstance(v, list):
                                    if decoded[k] not in v:
                                        skip = True
                                        break
                                elif decoded[k] != v:
                                    skip = True
                                    break
                        if skip:
                            continue

                    # Check if content contains query
                    if query.lower() in decoded.get("content", "").lower():
                        results.append(MemoryItem(**decoded))
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"DragonflyDB search error: {e}")

        # Firestore fallback (legacy)
        if self.firestore and isinstance(query, str) and not results:
            try:
                # Start with base query
                base_query = self.postgresql.collection(self.firestore_collection)

                # Apply domain filter if provided
                if domain:
                    base_query = base_query.where("domain", "==", domain)

                # Apply additional filters if provided
                filtered_query = base_query
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, list):
                            # Firestore doesn't support IN queries directly
                            # We'll filter in-memory after fetching
                            pass
                        else:
                            filtered_query = filtered_query.where(key, "==", value)

                # Execute query
                docs = filtered_query.limit(100).stream()

                # Process results and apply in-memory filtering
                for doc in docs:
                    data = doc.to_dict()

                    # Apply list filters in-memory if needed
                    if filters:
                        skip = False
                        for key, value in filters.items():
                            if isinstance(value, list) and key in data:
                                if data[key] not in value:
                                    skip = True
                                    break
                        if skip:
                            continue

                    # Check if content contains query
                    if query.lower() in data.get("content", "").lower():
                        results.append(MemoryItem(**data))
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"Firestore search error: {e}")

        return results

    # --- Delete Memory ---
    def delete(self, memory_id: str, domain: Optional[str] = None) -> bool:
        """
        Delete a memory item from all enabled backends.
        Returns True if deleted from at least one backend.

        Args:
            memory_id: ID of the memory item to delete
            domain: Optional domain the memory belongs to

        Returns:
            True if successfully deleted from at least one backend
        """
        deleted = False
        weaviate_class = self._get_collection_for_domain(domain)

        # Delete from Weaviate (primary)
        if self.weaviate:
            try:
                self.weaviate.data_object.delete(uuid=memory_id, class_name=weaviate_class)
                deleted = True
            except Exception as e:
                print(f"Weaviate delete error: {e}")

        # Delete from PostgreSQL (ACID)
        if self.postgres:
            try:
                with self.postgres.cursor() as cursor:
                    cursor.execute(
                        f"""
                        DELETE FROM {self.postgres_table}
                        WHERE id = %s
                        """,
                        (memory_id,),
                    )
                    if cursor.rowcount > 0:
                        deleted = True
                    self.postgres.commit()
            except Exception as e:
                print(f"PostgreSQL delete error: {e}")
                self.postgres.rollback()

        # Delete from DragonflyDB (cache)
        if self.dragonfly:
            deleted = self.dragonfly.delete(f"memory:{memory_id}") or deleted

        # Delete from Firestore (legacy)
        if self.firestore:
            self.postgresql.collection(self.firestore_collection).document(memory_id).delete()
            deleted = True

        return deleted

    # --- Health Check ---
    def health(self) -> Dict[str, bool]:
        """
        Returns a dictionary indicating the health of each backend.
        """
        status = {}

        # Weaviate (primary)
        if self.weaviate:
            try:
                status["weaviate"] = self.weaviate.is_ready()
            except Exception:
                status["weaviate"] = False

        # PostgreSQL (ACID)
        if self.postgres:
            try:
                with self.postgres.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    status["postgres"] = cursor.fetchone()[0] == 1
            except Exception:
                status["postgres"] = False

        # DragonflyDB (cache)
        if self.dragonfly:
            try:
                status["dragonfly"] = self.dragonfly.ping()
            except Exception:
                status["dragonfly"] = False

        # Firestore (legacy)
        if self.firestore:
            try:
                # Try listing collections
                list(self.postgresql.collections())
                status["firestore"] = True
            except Exception:
                status["firestore"] = False

        return status

# --- Example Usage ---
if __name__ == "__main__":
    # Example: Initialize UnifiedMemory with Weaviate-first configuration
    memory = UnifiedMemory(use_weaviate=True, use_postgres=True, use_dragonfly=False, use_firestore=False)

    # Example: Store a memory item in Personal domain
    item = MemoryItem(
        id="example1",
        content="This is a test memory for the Personal domain.",
        source="demo-agent",
        timestamp="2025-05-24T02:43:00Z",
        metadata={"demo": True},
        priority=0.8,
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        domain="Personal",
    )
    memory.store(item)

    # Example: Store structured ACID data
    try:
        job_id = memory.structured_store(
            table="job_status",
            data={
                "job_name": "data_import",
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "params": {"source": "api", "batch_size": 100},
            },
        )
        print(f"Stored job with ID: {job_id}")
    except Exception as e:
        print(f"Failed to store structured data: {e}")

    # Example: Retrieve from Personal domain
    retrieved = memory.retrieve("example1", domain="Personal")
    print("Retrieved:", retrieved)

    # Example: Search in PayReady domain with filters
    results = memory.search("apartment", domain="PayReady", filters={"status": "active"})
    print("Text search results:", results)

    # Example: Vector search in ParagonRX domain
    results = memory.search([0.1, 0.2, 0.3, 0.4, 0.5], domain="ParagonRX")
    print("Vector search results:", results)

    # Example: Delete
    deleted = memory.delete("example1", domain="Personal")
    print("Deleted:", deleted)

    # Example: Health check
    print("Backend health:", memory.health())
