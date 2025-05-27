"""
MongoDB connection implementation.

This module provides MongoDB connectivity with health checks and retries.
"""

import time
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from .base import RetryableConnection, ServiceHealth, ServiceStatus


class MongoDBConnection(RetryableConnection):
    """MongoDB connection with health checks and retries."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

        # Extract config
        self.connection_string = config.get("connection_string", config.get("uri"))
        self.database_name = config.get("database", "orchestra")
        self.server_selection_timeout = config.get("server_selection_timeout", 5000)

    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=self.server_selection_timeout,
            )

            # Test the connection
            await self.client.admin.command("ping")

            # Get the database
            self.database = self.client[self.database_name]

            self._status = ServiceStatus.HEALTHY

        except Exception as e:
            self._status = ServiceStatus.UNHEALTHY
            raise ConnectionFailure(f"Failed to connect to MongoDB: {e}")

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self._status = ServiceStatus.UNKNOWN

    async def health_check(self) -> ServiceHealth:
        """Perform health check on MongoDB."""
        if not self.client:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY, error="Client not initialized"
            )

        try:
            start_time = time.time()

            # Ping the server
            result = await self.client.admin.command("ping")

            latency_ms = (time.time() - start_time) * 1000

            # Get server info
            server_info = await self.client.server_info()

            return ServiceHealth(
                status=ServiceStatus.HEALTHY,
                latency_ms=latency_ms,
                metadata={
                    "version": server_info.get("version"),
                    "ok": result.get("ok", 0),
                },
            )

        except ServerSelectionTimeoutError:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY, error="Server selection timeout"
            )
        except Exception as e:
            return ServiceHealth(status=ServiceStatus.UNHEALTHY, error=str(e))

    async def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute a MongoDB operation."""
        if not self.database:
            raise ConnectionFailure("Database not connected")

        # Map operations to MongoDB methods
        operations = {
            "find": self._find,
            "find_one": self._find_one,
            "insert_one": self._insert_one,
            "insert_many": self._insert_many,
            "update_one": self._update_one,
            "update_many": self._update_many,
            "delete_one": self._delete_one,
            "delete_many": self._delete_many,
            "aggregate": self._aggregate,
            "count_documents": self._count_documents,
            "create_index": self._create_index,
        }

        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")

        return await operations[operation](*args, **kwargs)

    async def _find(self, collection: str, filter: Dict = None, **kwargs) -> list:
        """Find documents in a collection."""
        coll = self.database[collection]
        cursor = coll.find(filter or {}, **kwargs)
        return await cursor.to_list(length=kwargs.get("limit", None))

    async def _find_one(
        self, collection: str, filter: Dict = None, **kwargs
    ) -> Optional[Dict]:
        """Find a single document."""
        coll = self.database[collection]
        return await coll.find_one(filter or {}, **kwargs)

    async def _insert_one(self, collection: str, document: Dict, **kwargs) -> Any:
        """Insert a single document."""
        coll = self.database[collection]
        result = await coll.insert_one(document, **kwargs)
        return result.inserted_id

    async def _insert_many(
        self, collection: str, documents: list[Dict], **kwargs
    ) -> list:
        """Insert multiple documents."""
        coll = self.database[collection]
        result = await coll.insert_many(documents, **kwargs)
        return result.inserted_ids

    async def _update_one(
        self, collection: str, filter: Dict, update: Dict, **kwargs
    ) -> Dict:
        """Update a single document."""
        coll = self.database[collection]
        result = await coll.update_one(filter, update, **kwargs)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": result.upserted_id,
        }

    async def _update_many(
        self, collection: str, filter: Dict, update: Dict, **kwargs
    ) -> Dict:
        """Update multiple documents."""
        coll = self.database[collection]
        result = await coll.update_many(filter, update, **kwargs)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
        }

    async def _delete_one(self, collection: str, filter: Dict, **kwargs) -> int:
        """Delete a single document."""
        coll = self.database[collection]
        result = await coll.delete_one(filter, **kwargs)
        return result.deleted_count

    async def _delete_many(self, collection: str, filter: Dict, **kwargs) -> int:
        """Delete multiple documents."""
        coll = self.database[collection]
        result = await coll.delete_many(filter, **kwargs)
        return result.deleted_count

    async def _aggregate(self, collection: str, pipeline: list, **kwargs) -> list:
        """Run an aggregation pipeline."""
        coll = self.database[collection]
        cursor = coll.aggregate(pipeline, **kwargs)
        return await cursor.to_list(length=None)

    async def _count_documents(
        self, collection: str, filter: Dict = None, **kwargs
    ) -> int:
        """Count documents in a collection."""
        coll = self.database[collection]
        return await coll.count_documents(filter or {}, **kwargs)

    async def _create_index(self, collection: str, keys: list, **kwargs) -> str:
        """Create an index on a collection."""
        coll = self.database[collection]
        return await coll.create_index(keys, **kwargs)
