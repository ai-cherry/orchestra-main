"""
Pinecone Vector Storage Adapter for Orchestra AI
High-performance, async batch upsert/query/delete with robust error handling.
Credentials are loaded from centralized settings (via Pulumi/environment).

Performance, stability, and optimization are prioritized over cost and complex security.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from core.env_config import settings

import pinecone  # Requires 'pinecone-client' package

logger = logging.getLogger(__name__)


class PineconeAdapter:
    """
    Async adapter for Pinecone vector database.
    Designed for high-throughput, robust ingestion and search.
    """

    def __init__(
        self,
        index_name: str,
        namespace: Optional[str] = None,
        dimension: Optional[int] = None,
        environment: Optional[str] = None,
    ):
        # Credentials loaded from centralized settings
        api_key = settings.pinecone_api_key
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY not configured.")
        pinecone_env = environment or settings.pinecone_environment or "us-west1-gcp"
        pinecone.init(api_key=api_key, environment=pinecone_env)
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self._index = None

    async def connect(self):
        """Connect to Pinecone index (idempotent)."""
        if self._index is None:
            # Pinecone's client is sync, but can be wrapped for async
            loop = asyncio.get_event_loop()
            self._index = await loop.run_in_executor(
                None, lambda: pinecone.Index(self.index_name)
            )
            logger.info(f"Connected to Pinecone index: {self.index_name}")

    async def upsert_vectors(
        self, vectors: List[Dict[str, Any]], batch_size: int = 100
    ):
        """
        Batch upsert vectors to Pinecone.
        Each vector: {'id': str, 'values': List[float], 'metadata': dict}
        """
        await self.connect()
        total = len(vectors)
        for i in range(0, total, batch_size):
            batch = vectors[i : i + batch_size]
            ids = [v["id"] for v in batch]
            values = [v["values"] for v in batch]
            metadata = [v.get("metadata", {}) for v in batch]
            # Pinecone expects list of (id, vector, metadata)
            upsert_batch = [(ids[j], values[j], metadata[j]) for j in range(len(batch))]
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._index.upsert(upsert_batch, namespace=self.namespace),
                )
                logger.info(f"Upserted batch {i}-{i+len(batch)-1} to Pinecone.")
            except Exception as e:
                logger.error(
                    f"Pinecone upsert failed for batch {i}-{i+len(batch)-1}: {e}"
                )

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone for nearest neighbors.
        Returns list of {'id': str, 'score': float, 'metadata': dict}
        """
        await self.connect()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._index.query(
                    vector=vector,
                    top_k=top_k,
                    filter=filter,
                    include_metadata=True,
                    namespace=self.namespace,
                ),
            )
            matches = result.get("matches", [])
            return [
                {"id": m["id"], "score": m["score"], "metadata": m.get("metadata", {})}
                for m in matches
            ]
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []

    async def delete(self, ids: List[str]):
        """Delete vectors by IDs."""
        await self.connect()
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._index.delete(ids=ids, namespace=self.namespace)
            )
            logger.info(f"Deleted {len(ids)} vectors from Pinecone.")
        except Exception as e:
            logger.error(f"Pinecone delete failed: {e}")
