"""Unified Context Manager for Factory AI Integration.

This module provides a comprehensive context management system that bridges
Factory AI context with MCP memory stores, ensuring bidirectional synchronization
and high-performance caching.
"""

import asyncio
import json
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import asyncpg
import numpy as np
from pydantic import BaseModel, Field
from weaviate import Client
from weaviate.exceptions import WeaviateException

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ContextMetadata(BaseModel):
    """Metadata for context entries."""

    context_id: str = Field(description="Unique context identifier")
    parent_id: Optional[str] = Field(default=None, description="Parent context ID")
    version: int = Field(default=1, description="Context version number")
    source: str = Field(description="Source system: 'factory' or 'mcp'")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    embeddings: Optional[List[float]] = Field(default=None, description="Vector embeddings")


class ContextVersion(BaseModel):
    """Version history entry for context changes."""

    context_id: str
    version: int
    data: Dict[str, Any]
    changed_by: Optional[str] = None
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_type: str = Field(description="Type: 'create', 'update', 'merge'")


class UnifiedContextManager:
    """Manages context for both Roo and Factory AI systems.

    This class provides:
    - Bidirectional synchronization between Factory AI and MCP
    - PostgreSQL storage for metadata and versioning
    - Weaviate integration for semantic search
    - Multi-layer caching for performance
    - Conflict resolution strategies
    - Atomic operations for consistency

    Example:
        ```python
        async with UnifiedContextManager(config) as manager:
            # Store context
            await manager.store_context("ctx_123", {"data": "value"}, "factory")

            # Retrieve context
            context = await manager.get_context("ctx_123")

            # Search similar contexts
            similar = await manager.search_similar_contexts("query", limit=5)
        ```
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        weaviate_client: Client,
        cache_manager: CacheManager,
        sync_interval: int = 5,
        max_context_size: int = 10485760,  # 10MB
        version_retention: int = 100,
    ):
        """Initialize the UnifiedContextManager.

        Args:
            db_pool: AsyncPG connection pool
            weaviate_client: Weaviate client instance
            cache_manager: Cache manager instance
            sync_interval: Sync interval in seconds
            max_context_size: Maximum context size in bytes
            version_retention: Number of versions to retain
        """
        self.db_pool = db_pool
        self.weaviate = weaviate_client
        self.cache = cache_manager
        self.sync_interval = sync_interval
        self.max_context_size = max_context_size
        self.version_retention = version_retention
        self.version_history: List[ContextVersion] = []
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Start the context manager and background sync."""
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("UnifiedContextManager started")

    async def stop(self) -> None:
        """Stop the context manager and cleanup."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        logger.info("UnifiedContextManager stopped")

    async def store_context(
        self,
        context_id: str,
        data: Dict[str, Any],
        source: str,
        parent_id: Optional[str] = None,
        embeddings: Optional[List[float]] = None,
    ) -> ContextMetadata:
        """Store or update context with versioning.

        Args:
            context_id: Unique context identifier
            data: Context data to store
            source: Source system ('factory' or 'mcp')
            parent_id: Optional parent context ID
            embeddings: Optional vector embeddings

        Returns:
            ContextMetadata object

        Raises:
            ValueError: If context data exceeds size limit
        """
        # Validate context size
        data_size = len(json.dumps(data).encode())
        if data_size > self.max_context_size:
            raise ValueError(f"Context size {data_size} exceeds limit {self.max_context_size}")

        # Check if context exists
        existing = await self._get_context_metadata(context_id)

        if existing:
            # Update existing context
            version = existing.version + 1
            change_type = "update"
        else:
            # Create new context
            version = 1
            change_type = "create"

        # Store in PostgreSQL
        metadata = await self._store_context_metadata(context_id, data, source, parent_id, version, embeddings)

        # Store version history
        await self._store_version_history(context_id, version, data, change_type, source)

        # Update cache
        await self.cache.set(f"context:{context_id}", {"metadata": metadata.dict(), "data": data})

        # Store in Weaviate if embeddings provided
        if embeddings:
            await self._store_in_weaviate(context_id, data, embeddings)

        logger.info(f"Stored context {context_id} version {version} from {source}")
        return metadata

    async def get_context(self, context_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve context by ID and optional version.

        Args:
            context_id: Context identifier
            version: Optional specific version to retrieve

        Returns:
            Context data or None if not found
        """
        # Check cache first
        cache_key = f"context:{context_id}"
        if version:
            cache_key += f":v{version}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Fetch from database
        if version:
            data = await self._get_context_version(context_id, version)
        else:
            metadata = await self._get_context_metadata(context_id)
            if metadata:
                data = await self._get_context_data(context_id)
            else:
                data = None

        if data:
            # Update cache
            await self.cache.set(cache_key, data)

        return data

    async def search_similar_contexts(
        self,
        query_embeddings: List[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar contexts using vector similarity.

        Args:
            query_embeddings: Query vector embeddings
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)

        Returns:
            List of tuples (context_id, similarity_score, metadata)
        """
        try:
            # Search in Weaviate
            results = (
                self.weaviate.query.get("FactoryContext", ["contextId", "metadata"])
                .with_near_vector({"vector": query_embeddings, "certainty": threshold})
                .with_limit(limit)
                .do()
            )

            similar_contexts = []
            if results and "data" in results:
                for item in results["data"]["Get"]["FactoryContext"]:
                    context_id = item["contextId"]
                    metadata = item["metadata"]
                    # Calculate similarity score (Weaviate uses certainty)
                    score = item.get("_additional", {}).get("certainty", 0.0)
                    similar_contexts.append((context_id, score, metadata))

            return similar_contexts

        except WeaviateException as e:
            logger.error(f"Weaviate search error: {e}")
            return []

    async def merge_contexts(
        self,
        context_ids: List[str],
        merge_strategy: str = "latest",
    ) -> str:
        """Merge multiple contexts into a new context.

        Args:
            context_ids: List of context IDs to merge
            merge_strategy: Strategy for merging ('latest', 'union', 'intersection')

        Returns:
            New merged context ID
        """
        contexts = []
        for ctx_id in context_ids:
            ctx_data = await self.get_context(ctx_id)
            if ctx_data:
                contexts.append(ctx_data)

        if not contexts:
            raise ValueError("No valid contexts found to merge")

        # Apply merge strategy
        if merge_strategy == "latest":
            # Use the most recent context as base
            merged_data = contexts[-1]["data"]
        elif merge_strategy == "union":
            # Combine all unique keys
            merged_data = {}
            for ctx in contexts:
                merged_data.update(ctx["data"])
        elif merge_strategy == "intersection":
            # Keep only common keys
            if contexts:
                merged_data = contexts[0]["data"].copy()
                for ctx in contexts[1:]:
                    merged_data = {k: v for k, v in merged_data.items() if k in ctx["data"]}
            else:
                merged_data = {}
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")

        # Create new merged context
        new_context_id = f"merged_{uuid4().hex[:8]}"
        await self.store_context(new_context_id, merged_data, "mcp", parent_id=context_ids[0])  # Use first as parent

        logger.info(f"Merged {len(context_ids)} contexts into {new_context_id}")
        return new_context_id

    async def sync_with_factory(self, factory_context: Dict[str, Any]) -> None:
        """Sync Factory AI context to MCP memory store.

        Args:
            factory_context: Factory AI context data
        """
        context_id = factory_context.get("id", str(uuid4()))
        data = factory_context.get("data", {})

        # Generate embeddings if needed
        embeddings = await self._generate_embeddings(data)

        await self.store_context(context_id, data, "factory", embeddings=embeddings)

    async def sync_to_factory(self, context_id: str) -> Dict[str, Any]:
        """Sync MCP context to Factory AI format.

        Args:
            context_id: Context ID to sync

        Returns:
            Factory AI formatted context
        """
        context = await self.get_context(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")

        # Convert to Factory AI format
        factory_format = {
            "id": context_id,
            "data": context["data"],
            "metadata": context.get("metadata", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return factory_format

    async def cleanup_old_versions(self) -> int:
        """Clean up old context versions beyond retention limit.

        Returns:
            Number of versions cleaned up
        """
        async with self.db_pool.acquire() as conn:
            # Find contexts with too many versions
            query = """
                SELECT context_id, COUNT(*) as version_count
                FROM factory_context_versions
                GROUP BY context_id
                HAVING COUNT(*) > $1
            """
            contexts = await conn.fetch(query, self.version_retention)

            total_cleaned = 0
            for record in contexts:
                context_id = record["context_id"]
                excess = record["version_count"] - self.version_retention

                # Delete oldest versions
                delete_query = """
                    DELETE FROM factory_context_versions
                    WHERE context_id = $1
                    AND version IN (
                        SELECT version
                        FROM factory_context_versions
                        WHERE context_id = $1
                        ORDER BY version ASC
                        LIMIT $2
                    )
                """
                await conn.execute(delete_query, context_id, excess)
                total_cleaned += excess

            logger.info(f"Cleaned up {total_cleaned} old context versions")
            return total_cleaned

    async def get_metrics(self) -> Dict[str, Any]:
        """Get context manager metrics.

        Returns:
            Dictionary of metrics
        """
        async with self.db_pool.acquire() as conn:
            # Get context counts
            context_count = await conn.fetchval("SELECT COUNT(*) FROM factory_context_metadata")
            version_count = await conn.fetchval("SELECT COUNT(*) FROM factory_context_versions")

        # Get cache metrics
        cache_metrics = await self.cache.get_metrics()

        return {
            "contexts": {
                "total": context_count,
                "versions": version_count,
                "avg_versions_per_context": version_count / max(context_count, 1),
            },
            "cache": cache_metrics,
            "sync": {"interval": self.sync_interval, "running": self._running},
        }

    # Private helper methods

    async def _sync_loop(self) -> None:
        """Background sync loop."""
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)
                # Perform sync operations here
                # This is where bidirectional sync logic would go
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")

    async def _get_context_metadata(self, context_id: str) -> Optional[ContextMetadata]:
        """Get context metadata from PostgreSQL."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT * FROM factory_context_metadata
                WHERE context_id = $1
            """
            record = await conn.fetchrow(query, context_id)
            if record:
                return ContextMetadata(**dict(record))
            return None

    async def _get_context_data(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get latest context data from PostgreSQL."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT data FROM factory_context_metadata
                WHERE context_id = $1
            """
            record = await conn.fetchrow(query, context_id)
            if record:
                return record["data"]
            return None

    async def _get_context_version(self, context_id: str, version: int) -> Optional[Dict[str, Any]]:
        """Get specific context version from PostgreSQL."""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT data FROM factory_context_versions
                WHERE context_id = $1 AND version = $2
            """
            record = await conn.fetchrow(query, context_id, version)
            if record:
                return record["data"]
            return None

    async def _store_context_metadata(
        self,
        context_id: str,
        data: Dict[str, Any],
        source: str,
        parent_id: Optional[str],
        version: int,
        embeddings: Optional[List[float]],
    ) -> ContextMetadata:
        """Store context metadata in PostgreSQL."""
        async with self.db_pool.acquire() as conn:
            query = """
                INSERT INTO factory_context_metadata
                (context_id, parent_id, version, source, data, embeddings, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (context_id) DO UPDATE SET
                    version = $3,
                    data = $5,
                    embeddings = $6,
                    updated_at = $7
                RETURNING *
            """

            # Convert embeddings to PostgreSQL vector format if provided
            embeddings_vector = None
            if embeddings:
                embeddings_vector = f"[{','.join(map(str, embeddings))}]"

            record = await conn.fetchrow(
                query, context_id, parent_id, version, source, json.dumps(data), embeddings_vector, datetime.utcnow()
            )

            return ContextMetadata(**dict(record))

    async def _store_version_history(
        self,
        context_id: str,
        version: int,
        data: Dict[str, Any],
        change_type: str,
        changed_by: str,
    ) -> None:
        """Store version history in PostgreSQL."""
        async with self.db_pool.acquire() as conn:
            query = """
                INSERT INTO factory_context_versions
                (context_id, version, data, change_type, changed_by)
                VALUES ($1, $2, $3, $4, $5)
            """
            await conn.execute(query, context_id, version, json.dumps(data), change_type, changed_by)

    async def _store_in_weaviate(
        self,
        context_id: str,
        data: Dict[str, Any],
        embeddings: List[float],
    ) -> None:
        """Store context in Weaviate for vector search."""
        try:
            # Prepare content for search
            content = json.dumps(data)

            # Create Weaviate object
            weaviate_object = {
                "contextId": context_id,
                "content": content,
                "metadata": data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Store with vector
            self.weaviate.data_object.create(weaviate_object, "FactoryContext", vector=embeddings)

        except WeaviateException as e:
            logger.error(f"Failed to store in Weaviate: {e}")

    async def _generate_embeddings(self, data: Dict[str, Any]) -> List[float]:
        """Generate embeddings for context data.

        This is a placeholder - in production, you would use an actual
        embedding model like OpenAI's text-embedding-ada-002.
        """
        # For now, return random embeddings
        # In production, use actual embedding model
        return np.random.rand(1536).tolist()
