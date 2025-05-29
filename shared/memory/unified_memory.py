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
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    priority: float = Field(default=0.5, description="Priority of the memory (0.0-1.0)")
    embedding: Optional[List[float]] = Field(
        default=None, description="Vector embedding of the memory content"
    )
    domain: Optional[str] = Field(
        default="Personal", description="Business domain (Personal, PayReady, ParagonRX)"
    )


# --- Domain Collection Types ---
DomainType = Literal["Personal", "PayReady", "ParagonRX", "Session"]


# --- Unified Memory Abstraction ---
class UnifiedMemory:
    """
    UnifiedMemory provides a seamless, high-performance interface for storing, retrieving,
    searching, and deleting memory items across Weaviate (primary), PostgreSQL (ACID), 
    and optionally DragonflyDB (cache) backends.

    Backend selection is controlled via environment variables or constructor arguments.
    """

    def __init__(
        self,
        use_weaviate: bool = True,
        use_dragonfly: bool = False,
        use_firestore: bool = False,
        use_postgres: bool = True,
        dragonfly_url: Optional[str] = None,
        weaviate_url: Optional[str] = None,
        weaviate_api_key: Optional[str] = None,
        postgres_dsn: Optional[str] = None,
        firestore_project: Optional[str] = None,
        weaviate_class: str = "Session",
        firestore_collection: str = "memory_items",
        postgres_table: str = "memory_items",
    ):
        # --- Weaviate (Vector DB - Primary) ---
        self.weaviate = None
        self.weaviate_class = weaviate_class
        if use_weaviate and weaviate:
            endpoint = weaviate_url or settings.weaviate_endpoint
            api_key = weaviate_api_key or settings.weaviate_api_key
            if endpoint and api_key:
                self.weaviate = weaviate.Client(
                    url=endpoint,
                    auth_client_secret=weaviate.AuthApiKey(api_key=api_key),
                )

        # --- PostgreSQL (ACID Operations) ---
        self.postgres = None
        self.postgres_table = postgres_table
        if use_postgres and psycopg2:
            dsn = postgres_dsn or settings.postgres_dsn
            if dsn:
                try:
                    self.postgres = psycopg2.connect(dsn)
                    # Ensure table exists
                    self._ensure_postgres_table()
                except Exception as e:
                    print(f"PostgreSQL connection error: {e}")

        # --- DragonflyDB (Redis-compatible - Optional Cache) ---
        self.dragonfly = None
        if use_dragonfly and redis:
            self.dragonfly = redis.Redis.from_url(
                dragonfly_url or settings.dragonfly_url or "redis://localhost:6379/0"
            )

        # --- Firestore (Legacy Support) ---
        self.firestore = None
        self.firestore_collection = firestore_collection
        if use_firestore and firestore:
            self.firestore = firestore.Client(
                project=firestore_project or settings.gcp_project_id
            )

    def _ensure_postgres_table(self):
        """Create the memory_items table in PostgreSQL if it doesn't exist."""
        if not self.postgres:
            return

        with self.postgres.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.postgres_table} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata JSONB,
                    priority FLOAT,
                    domain TEXT,
                    embedding VECTOR(384)
                );
                CREATE INDEX IF NOT EXISTS idx_{self.postgres_table}_domain ON {self.postgres_table} (domain);
                CREATE INDEX IF NOT EXISTS idx_{self.postgres_table}_source ON {self.postgres_table} (source);
                """
            )
            self.postgres.commit()

    def _get_collection_for_domain(self, domain: Optional[str]) -> str:
        """Map domain to the appropriate Weaviate collection."""
        if not domain or domain == "Session":
            return self.weaviate_class
        
        # Map to one of the three business domains
        if domain in ["Personal", "PayReady", "ParagonRX"]:
            return domain
        
        # Default to Session for unknown domains
        return self.weaviate_class

    # --- Store Memory ---
    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item in all enabled backends.
        Returns the memory ID.
        """
        # Generate ID if not provided
        if not item.id:
            item.id = str(uuid.uuid4())
            
        # Set timestamp if not provided
        if not item.timestamp:
            item.timestamp = datetime.now().isoformat()

        # Determine the appropriate collection based on domain
        weaviate_class = self._get_collection_for_domain(item.domain)

        # Weaviate (vector search - primary)
        if self.weaviate and item.embedding:
            try:
                self.weaviate.data_object.create(
                    data_object=item.dict(exclude={"embedding"}),
                    class_name=weaviate_class,
                    uuid=item.id,
                    vector=item.embedding,
                )
            except Exception:
                # Attempt update if already exists
                try:
                    self.weaviate.data_object.replace(
                        data_object=item.dict(exclude={"embedding"}),
                        class_name=weaviate_class,
                        uuid=item.id,
                        vector=item.embedding,
                    )
                except Exception as e:
                    print(f"Weaviate store error: {e}")

        # PostgreSQL (ACID operations)
        if self.postgres:
            try:
                with self.postgres.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO {self.postgres_table} 
                        (id, content, source, timestamp, metadata, priority, domain, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        source = EXCLUDED.source,
                        timestamp = EXCLUDED.timestamp,
                        metadata = EXCLUDED.metadata,
                        priority = EXCLUDED.priority,
                        domain = EXCLUDED.domain,
                        embedding = EXCLUDED.embedding
                        """,
                        (
                            item.id,
                            item.content,
                            item.source,
                            item.timestamp,
                            psycopg2.extras.Json(item.metadata),
                            item.priority,
                            item.domain,
                            item.embedding,
                        ),
                    )
                    self.postgres.commit()
            except Exception as e:
                print(f"PostgreSQL store error: {e}")
                self.postgres.rollback()

        # DragonflyDB (fast cache - optional)
        if self.dragonfly:
            self.dragonfly.hset(f"memory:{item.id}", mapping=item.dict())

        # Firestore (legacy support)
        if self.firestore:
            self.firestore.collection(self.firestore_collection).document(item.id).set(
                item.dict()
            )

        return item.id

    # --- Structured Store for ACID Operations ---
    def structured_store(self, table: str, data: Dict[str, Any], key_field: str = "id") -> str:
        """
        Store structured data requiring ACID guarantees in PostgreSQL.
        Ideal for billing records, job status, and other transactional data.
        
        Args:
            table: PostgreSQL table name
            data: Dictionary of column:value pairs
            key_field: Primary key field name
            
        Returns:
            ID of the stored record
        """
        if not self.postgres:
            raise RuntimeError("PostgreSQL is required for structured_store operations")
            
        # Ensure ID exists
        if key_field not in data:
            data[key_field] = str(uuid.uuid4())
            
        try:
            # Dynamically build SQL based on data dict
            columns = list(data.keys())
            placeholders = ["%s"] * len(columns)
            values = [data[col] for col in columns]
            
            # Handle JSON fields
            for i, val in enumerate(values):
                if isinstance(val, dict) or isinstance(val, list):
                    values[i] = psycopg2.extras.Json(val)
            
            # Build update clause for conflict resolution
            update_clauses = [f"{col} = EXCLUDED.{col}" for col in columns if col != key_field]
            update_sql = ", ".join(update_clauses)
            
            with self.postgres.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {table} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT ({key_field}) DO UPDATE SET
                    {update_sql}
                    """,
                    values,
                )
                self.postgres.commit()
                
            return data[key_field]
        except Exception as e:
            print(f"PostgreSQL structured_store error: {e}")
            if self.postgres:
                self.postgres.rollback()
            raise

    # --- Retrieve Memory ---
    def retrieve(self, memory_id: str, domain: Optional[str] = None) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID, preferring Weaviate, then PostgreSQL, then cache.
        
        Args:
            memory_id: The ID of the memory item to retrieve
            domain: Optional domain to search in (Personal, PayReady, ParagonRX)
            
        Returns:
            MemoryItem if found, None otherwise
        """
        weaviate_class = self._get_collection_for_domain(domain)
        
        # Try Weaviate first (primary)
        if self.weaviate:
            try:
                result = self.weaviate.data_object.get_by_id(
                    uuid=memory_id, 
                    class_name=weaviate_class, 
                    with_vector=True
                )
                if result:
                    # Extract vector from _additional if present
                    embedding = None
                    if "_additional" in result and "vector" in result["_additional"]:
                        embedding = result["_additional"]["vector"]
                        del result["_additional"]
                    
                    # Create MemoryItem from result
                    return MemoryItem(
                        **result,
                        embedding=embedding
                    )
            except Exception as e:
                print(f"Weaviate retrieve error: {e}")

        # Try PostgreSQL next (ACID)
        if self.postgres:
            try:
                with self.postgres.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(
                        f"""
                        SELECT * FROM {self.postgres_table}
                        WHERE id = %s
                        """,
                        (memory_id,),
                    )
                    row = cursor.fetchone()
                    if row:
                        # Convert row to dict and handle JSON
                        item_dict = dict(row)
                        if isinstance(item_dict["metadata"], str):
                            import json
                            item_dict["metadata"] = json.loads(item_dict["metadata"])
                        return MemoryItem(**item_dict)
            except Exception as e:
                print(f"PostgreSQL retrieve error: {e}")

        # Try DragonflyDB if enabled (cache)
        if self.dragonfly:
            data = self.dragonfly.hgetall(f"memory:{memory_id}")
            if data:
                # Redis returns bytes, decode
                decoded = {k.decode(): v.decode() for k, v in data.items()}
                return MemoryItem(**decoded)

        # Fallback to Firestore (legacy)
        if self.firestore:
            doc = (
                self.firestore.collection(self.firestore_collection)
                .document(memory_id)
                .get()
            )
            if doc.exists:
                return MemoryItem(**doc.to_dict())

        return None

    # --- Search Memory (Semantic/Vector) ---
    def search(
        self, 
        query: Union[str, List[float]], 
        limit: int = 10,
        domain: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """
        Search memory items across backends.
        - If query is a vector: perform semantic search in Weaviate (primary).
        - If query is a string: perform hybrid search in Weaviate or text search in other backends.
        
        Args:
            query: Vector for semantic search or text for keyword search
            limit: Maximum number of results to return
            domain: Optional domain to search in (Personal, PayReady, ParagonRX)
            filters: Optional filters to apply to the search
            
        Returns:
            List of matching MemoryItem objects
        """
        results = []
        weaviate_class = self._get_collection_for_domain(domain)
        
        # Prepare filters for Weaviate
        weaviate_where = None
        if filters:
            # Convert simple filters to Weaviate format
            weaviate_where = {"operator": "And", "operands": []}
            for key, value in filters.items():
                if isinstance(value, list):
                    # Handle IN operator
                    weaviate_where["operands"].append({
                        "operator": "Or",
                        "operands": [{"path": [key], "operator": "Equal", "valueString": v} for v in value]
                    })
                else:
                    # Handle simple equality
                    weaviate_where["operands"].append({
                        "path": [key],
                        "operator": "Equal",
                        "valueString": value
                    })

        # Vector search in Weaviate (primary approach)
        if self.weaviate:
            try:
                if isinstance(query, list):
                    # Vector search
                    result = (
                        self.weaviate.query
                        .get(weaviate_class, ["*", "_additional { id distance vector }"])
                        .with_near_vector({"vector": query})
                        .with_limit(limit)
                    )
                    
                    # Apply filters if provided
                    if weaviate_where:
                        result = result.with_where(weaviate_where)
                        
                    # Execute query
                    res = result.do()
                    
                    # Process results
                    matches = res.get("data", {}).get("Get", {}).get(weaviate_class, [])
                    for m in matches:
                        # Extract and remove _additional
                        additional = m.pop("_additional", {})
                        embedding = additional.get("vector")
                        
                        # Create MemoryItem
                        results.append(MemoryItem(
                            **m,
                            embedding=embedding
                        ))
                    
                    return results
                else:
                    # Text/hybrid search
                    result = (
                        self.weaviate.query
                        .get(weaviate_class, ["*", "_additional { id distance vector }"])
                        .with_hybrid(query=query, alpha=0.5)  # Hybrid search with ACORN
                        .with_limit(limit)
                    )
                    
                    # Apply filters if provided
                    if weaviate_where:
                        result = result.with_where(weaviate_where)
                        
                    # Execute query
                    res = result.do()
                    
                    # Process results
                    matches = res.get("data", {}).get("Get", {}).get(weaviate_class, [])
                    for m in matches:
                        # Extract and remove _additional
                        additional = m.pop("_additional", {})
                        embedding = additional.get("vector")
                        
                        # Create MemoryItem
                        results.append(MemoryItem(
                            **m,
                            embedding=embedding
                        ))
                    
                    if results:
                        return results
            except Exception as e:
                print(f"Weaviate search error: {e}")

        # PostgreSQL full-text search fallback
        if self.postgres and isinstance(query, str):
            try:
                sql_filters = []
                sql_params = [f"%{query}%"]  # For content LIKE
                
                # Add domain filter if provided
                if domain:
                    sql_filters.append("domain = %s")
                    sql_params.append(domain)
                
                # Add additional filters if provided
                if filters:
                    for key, value in filters.items():
                        if isinstance(value, list):
                            placeholders = ", ".join(["%s"] * len(value))
                            sql_filters.append(f"{key} IN ({placeholders})")
                            sql_params.extend(value)
                        else:
                            sql_filters.append(f"{key} = %s")
                            sql_params.append(value)
                
                # Build WHERE clause
                where_clause = "content ILIKE %s"
                if sql_filters:
                    where_clause += " AND " + " AND ".join(sql_filters)
                
                with self.postgres.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(
                        f"""
                        SELECT * FROM {self.postgres_table}
                        WHERE {where_clause}
                        ORDER BY priority DESC
                        LIMIT %s
                        """,
                        sql_params + [limit],
                    )
                    rows = cursor.fetchall()
                    for row in rows:
                        # Convert row to dict and handle JSON
                        item_dict = dict(row)
                        if isinstance(item_dict["metadata"], str):
                            import json
                            item_dict["metadata"] = json.loads(item_dict["metadata"])
                        results.append(MemoryItem(**item_dict))
                    
                    if results:
                        return results
            except Exception as e:
                print(f"PostgreSQL search error: {e}")

        # DragonflyDB text search (if enabled and no results yet)
        if self.dragonfly and isinstance(query, str) and not results:
            try:
                # Apply domain filter to key pattern if provided
                key_pattern = f"memory:*"
                if domain:
                    # We'll filter in-memory since Redis doesn't support complex patterns
                    pass
                
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
                base_query = self.firestore.collection(self.firestore_collection)
                
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
                self.weaviate.data_object.delete(
                    uuid=memory_id, class_name=weaviate_class
                )
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
            self.firestore.collection(self.firestore_collection).document(
                memory_id
            ).delete()
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
                list(self.firestore.collections())
                status["firestore"] = True
            except Exception:
                status["firestore"] = False
                
        return status


# --- Example Usage ---
if __name__ == "__main__":
    # Example: Initialize UnifiedMemory with Weaviate-first configuration
    memory = UnifiedMemory(
        use_weaviate=True,
        use_postgres=True,
        use_dragonfly=False,
        use_firestore=False
    )

    # Example: Store a memory item in Personal domain
    item = MemoryItem(
        id="example1",
        content="This is a test memory for the Personal domain.",
        source="demo-agent",
        timestamp="2025-05-24T02:43:00Z",
        metadata={"demo": True},
        priority=0.8,
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        domain="Personal"
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
                "params": {"source": "api", "batch_size": 100}
            }
        )
        print(f"Stored job with ID: {job_id}")
    except Exception as e:
        print(f"Failed to store structured data: {e}")

    # Example: Retrieve from Personal domain
    retrieved = memory.retrieve("example1", domain="Personal")
    print("Retrieved:", retrieved)

    # Example: Search in PayReady domain with filters
    results = memory.search(
        "apartment", 
        domain="PayReady",
        filters={"status": "active"}
    )
    print("Text search results:", results)

    # Example: Vector search in ParagonRX domain
    results = memory.search(
        [0.1, 0.2, 0.3, 0.4, 0.5],
        domain="ParagonRX"
    )
    print("Vector search results:", results)

    # Example: Delete
    deleted = memory.delete("example1", domain="Personal")
    print("Deleted:", deleted)

    # Example: Health check
    print("Backend health:", memory.health())
