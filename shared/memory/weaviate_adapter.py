"""
Weaviate Vector Storage Adapter for Orchestra AI
High-performance, async batch upsert/query/delete with robust error handling.
Credentials and endpoint are loaded from centralized settings (via Pulumi/environment).

Performance, stability, and optimization are prioritized over cost and complex security.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import weaviate
from weaviate.util import get_valid_uuid

from core.env_config import settings

logger = logging.getLogger(__name__)

class WeaviateAdapter:
    """
    Async adapter for Weaviate vector database.
    Designed for high-throughput, robust ingestion and search.
    """

    def __init__(
        self,
        class_name: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        # Credentials and endpoint loaded from centralized settings
        self.endpoint = endpoint or settings.weaviate_endpoint
        self.api_key = api_key or settings.weaviate_api_key
        if not self.endpoint or not self.api_key:
            raise RuntimeError("WEAVIATE_ENDPOINT and WEAVIATE_API_KEY must be configured")
        self.class_name = class_name
        self._client = None

    async def connect(self):
        """Connect to Weaviate instance (idempotent)."""
        if self._client is None:
            # Weaviate client is sync, but can be wrapped for async
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None,
                lambda: weaviate.Client(
                    url=self.endpoint,
                    auth_client_secret=weaviate.AuthApiKey(api_key=self.api_key),
                    timeout_config=(10, 60),
                ),
            )
            logger.info(f"Connected to Weaviate at: {self.endpoint}")

    async def batch_upsert(self, objects: List[Dict[str, Any]], batch_size: int = 100):
        """
        Batch upsert objects to Weaviate.
        Each object: {'id': str, 'vector': List[float], 'properties': dict}
        """
        await self.connect()
        total = len(objects)
        for i in range(0, total, batch_size):
            batch = objects[i : i + batch_size]
            try:

                def upsert_batch():
                    with self._client.batch as batcher:
                        for obj in batch:
                            uuid = get_valid_uuid(obj["id"])
                            batcher.add_data_object(
                                data_object=obj["properties"],
                                class_name=self.class_name,
                                uuid=uuid,
                                vector=obj["vector"],
                            )

                await asyncio.get_event_loop().run_in_executor(None, upsert_batch)
                logger.info(f"Upserted batch {i}-{i+len(batch)-1} to Weaviate.")
            except Exception as e:
                logger.error(f"Weaviate upsert failed for batch {i}-{i+len(batch)-1}: {e}")

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query Weaviate for nearest neighbors.
        Returns list of {'id': str, 'score': float, 'properties': dict}
        """
        await self.connect()
        try:

            def do_query():
                return (
                    self._client.query.get(self.class_name, ["_additional { id distance }", "*"])
                    .with_near_vector({"vector": vector})
                    .with_limit(top_k)
                    .with_where(filters)
                    .do()
                )

            result = await asyncio.get_event_loop().run_in_executor(None, do_query)
            matches = result.get("data", {}).get("Get", {}).get(self.class_name, [])
            return [
                {
                    "id": m["_additional"]["id"],
                    "score": 1.0 - m["_additional"]["distance"],  # Weaviate uses distance, convert to similarity
                    "properties": {k: v for k, v in m.items() if k != "_additional"},
                }
                for m in matches
            ]
        except Exception as e:
            logger.error(f"Weaviate query failed: {e}")
            return []

    async def delete(self, ids: List[str]):
        """Delete objects by IDs."""
        await self.connect()
        try:

            def do_delete():
                for uuid in ids:
                    self._client.data_object.delete(uuid=get_valid_uuid(uuid), class_name=self.class_name)

            await asyncio.get_event_loop().run_in_executor(None, do_delete)
            logger.info(f"Deleted {len(ids)} objects from Weaviate.")
        except Exception as e:
            logger.error(f"Weaviate delete failed: {e}")
