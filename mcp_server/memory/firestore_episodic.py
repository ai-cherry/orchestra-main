"""
Firestore implementation for mid-term episodic memory.

This module provides structured storage using Firestore with:
- Document-based storage for complex data
- Rich querying capabilities
- Automatic indexing
- Batch operations for efficiency
- Integration with existing Firestore infrastructure
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

try:
    from google.cloud import firestore
    from google.cloud.firestore_v1 import AsyncClient, AsyncTransaction

    HAS_FIRESTORE = True
except ImportError:
    HAS_FIRESTORE = False
    firestore = None
    AsyncClient = None
    AsyncTransaction = None

from .base import BaseMemory, MemoryEntry, MemorySearchResult, MemoryTier
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)


class FirestoreEpisodicMemory(BaseMemory):
    """
    Firestore-based implementation for warm tier episodic memory.

    Optimized for:
    - Structured episodic data storage
    - Complex queries and filtering
    - Medium-frequency access patterns
    - Automatic scaling with GCP
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Firestore episodic memory."""
        super().__init__(MemoryTier.WARM, config)

        # Firestore settings
        self.project_id = self.config.get("project_id")
        self.database_id = self.config.get("database_id", "(default)")
        self.collection_name = self.config.get("collection_name", "mcp_episodic_memory")

        # Performance settings
        self.batch_size = self.config.get("batch_size", 500)  # Firestore limit
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1.0)

        # TTL settings
        self.default_ttl = self.config.get("default_ttl", 86400)  # 24 hours
        self.enable_ttl_cleanup = self.config.get("enable_ttl_cleanup", True)

        self._client: Optional[AsyncClient] = None
        self._collection = None

    async def initialize(self) -> bool:
        """Initialize Firestore client and collection."""
        if not HAS_FIRESTORE:
            logger.error("google-cloud-firestore not installed. Install with: pip install google-cloud-firestore")
            return False

        try:
            # Create async client
            self._client = AsyncClient(
                project=self.project_id,
                database=self.database_id,
            )

            # Get collection reference
            self._collection = self._client.collection(self.collection_name)

            # Create indexes if needed (this would typically be done via deployment)
            await self._ensure_indexes()

            logger.info(
                f"Initialized Firestore episodic memory "
                f"(project: {self.project_id}, database: {self.database_id}, "
                f"collection: {self.collection_name})"
            )

            # Start TTL cleanup task if enabled
            if self.enable_ttl_cleanup:
                asyncio.create_task(self._ttl_cleanup_task())

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            return False

    async def _ensure_indexes(self) -> None:
        """Ensure required indexes exist (placeholder for actual index creation)."""
        # In production, indexes would be created via:
        # - gcloud firestore indexes create
        # - Terraform/deployment scripts
        # - Firestore console

        # This is just a placeholder to document required indexes
        required_indexes = [
            {
                "fields": [
                    {"field_path": "metadata.tier", "order": "ASCENDING"},
                    {"field_path": "metadata.accessed_at", "order": "DESCENDING"},
                ]
            },
            {
                "fields": [
                    {"field_path": "metadata.tags", "array_config": "CONTAINS"},
                    {"field_path": "metadata.created_at", "order": "DESCENDING"},
                ]
            },
            {
                "fields": [
                    {"field_path": "metadata.expires_at", "order": "ASCENDING"},
                ]
            },
        ]

        logger.debug(f"Required indexes: {required_indexes}")

    async def save(self, entry: MemoryEntry) -> bool:
        """Save entry to Firestore."""
        await self.ensure_initialized()

        try:
            # Prepare document data
            doc_data = self._entry_to_firestore(entry)

            # Save to Firestore
            doc_ref = self._collection.document(entry.key)
            await doc_ref.set(doc_data)

            logger.debug(f"Saved entry to Firestore: {entry.key}")
            return True

        except Exception as e:
            logger.error(f"Failed to save to Firestore: {e}")
            return False

    def _entry_to_firestore(self, entry: MemoryEntry) -> Dict[str, Any]:
        """Convert MemoryEntry to Firestore document format."""
        # Calculate expiration time
        expires_at = None
        if entry.metadata.ttl_seconds > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=entry.metadata.ttl_seconds)

        return {
            "key": entry.key,
            "content": entry.content,  # Firestore handles nested structures
            "metadata": {
                "id": entry.metadata.id,
                "created_at": entry.metadata.created_at,
                "updated_at": entry.metadata.updated_at,
                "accessed_at": entry.metadata.accessed_at,
                "access_count": entry.metadata.access_count,
                "tier": entry.metadata.tier.value,
                "ttl_seconds": entry.metadata.ttl_seconds,
                "tags": entry.metadata.tags,
                "source": entry.metadata.source,
                "content_hash": entry.metadata.content_hash,
                "expires_at": expires_at,
            },
            "embedding": entry.embedding,
            "_search_text": self._generate_search_text(entry),
        }

    def _generate_search_text(self, entry: MemoryEntry) -> str:
        """Generate searchable text from entry content."""
        # Create searchable text from content
        if isinstance(entry.content, str):
            return entry.content.lower()
        elif isinstance(entry.content, dict):
            return json.dumps(entry.content, sort_keys=True).lower()
        else:
            return str(entry.content).lower()

    def _firestore_to_entry(self, doc_data: Dict[str, Any]) -> MemoryEntry:
        """Convert Firestore document to MemoryEntry."""
        metadata = doc_data.get("metadata", {})

        # Convert back to MemoryEntry format
        entry_dict = {
            "key": doc_data["key"],
            "content": doc_data["content"],
            "metadata": metadata,
            "embedding": doc_data.get("embedding"),
        }

        return MemoryEntry.from_dict(entry_dict)

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve entry from Firestore."""
        await self.ensure_initialized()

        try:
            doc_ref = self._collection.document(key)
            doc = await doc_ref.get()

            if not doc.exists:
                return None

            doc_data = doc.to_dict()

            # Check if expired
            expires_at = doc_data.get("metadata", {}).get("expires_at")
            if expires_at and expires_at < datetime.utcnow():
                # Delete expired entry
                await doc_ref.delete()
                return None

            # Convert to MemoryEntry
            entry = self._firestore_to_entry(doc_data)

            # Update access metadata
            entry.metadata.update_access()

            # Update in Firestore (don't wait)
            asyncio.create_task(self._update_access_metadata(key, entry))

            return entry

        except Exception as e:
            logger.error(f"Failed to get from Firestore: {e}")
            return None

    async def _update_access_metadata(self, key: str, entry: MemoryEntry) -> None:
        """Update access metadata in background."""
        try:
            doc_ref = self._collection.document(key)
            await doc_ref.update(
                {
                    "metadata.accessed_at": entry.metadata.accessed_at,
                    "metadata.access_count": entry.metadata.access_count,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update access metadata: {e}")

    async def delete(self, key: str) -> bool:
        """Delete entry from Firestore."""
        await self.ensure_initialized()

        try:
            doc_ref = self._collection.document(key)
            await doc_ref.delete()

            logger.debug(f"Deleted entry from Firestore: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete from Firestore: {e}")
            return False

    async def search(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """Search entries in Firestore."""
        await self.ensure_initialized()

        try:
            results = []

            # Build query
            query_ref = self._collection

            # Apply filters
            if filters:
                if "tags" in filters:
                    for tag in filters["tags"]:
                        query_ref = query_ref.where("metadata.tags", "array_contains", tag)

                if "min_access_count" in filters:
                    query_ref = query_ref.where("metadata.access_count", ">=", filters["min_access_count"])

                if "source" in filters:
                    query_ref = query_ref.where("metadata.source", "==", filters["source"])

            # Text search (basic contains search)
            if isinstance(query, str) and query:
                # Firestore doesn't have full-text search, so we do client-side filtering
                # In production, consider using Algolia or Elasticsearch
                query_lower = query.lower()

                # Get more documents and filter client-side
                docs = await query_ref.limit(limit * 10).get()

                for doc in docs:
                    doc_data = doc.to_dict()
                    search_text = doc_data.get("_search_text", "")

                    if query_lower in search_text:
                        entry = self._firestore_to_entry(doc_data)

                        # Calculate simple relevance score
                        score = search_text.count(query_lower) / len(search_text)
                        results.append(MemorySearchResult(entry, score, self.tier))

                # Sort by score and limit
                results.sort(reverse=True)
                results = results[:limit]

            else:
                # No text query, just return filtered results
                docs = await query_ref.limit(limit).get()

                for doc in docs:
                    doc_data = doc.to_dict()
                    entry = self._firestore_to_entry(doc_data)
                    results.append(MemorySearchResult(entry, 1.0, self.tier))

            return results

        except Exception as e:
            logger.error(f"Failed to search in Firestore: {e}")
            return []

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix."""
        await self.ensure_initialized()

        try:
            keys = []

            # Build query
            query_ref = self._collection

            if prefix:
                # Firestore range query for prefix matching
                query_ref = query_ref.where(firestore.FieldPath.document_id(), ">=", prefix).where(
                    firestore.FieldPath.document_id(), "<", prefix + "\uffff"
                )

            # Get documents
            docs = await query_ref.select([]).get()

            for doc in docs:
                keys.append(doc.id)

            return keys

        except Exception as e:
            logger.error(f"Failed to list keys from Firestore: {e}")
            return []

    async def batch_save(self, entries: List[MemoryEntry]) -> Dict[str, bool]:
        """Save multiple entries using batch writes."""
        await self.ensure_initialized()

        results = {}

        try:
            # Process in batches (Firestore limit is 500)
            for i in range(0, len(entries), self.batch_size):
                batch_entries = entries[i : i + self.batch_size]
                batch = self._client.batch()

                for entry in batch_entries:
                    doc_ref = self._collection.document(entry.key)
                    doc_data = self._entry_to_firestore(entry)
                    batch.set(doc_ref, doc_data)

                # Commit batch
                await batch.commit()

                # Mark as successful
                for entry in batch_entries:
                    results[entry.key] = True

            logger.info(f"Batch saved {len(entries)} entries to Firestore")

        except Exception as e:
            logger.error(f"Failed to batch save to Firestore: {e}")
            # Mark remaining as failed
            for entry in entries:
                if entry.key not in results:
                    results[entry.key] = False

        return results

    async def batch_get(self, keys: List[str]) -> Dict[str, Optional[MemoryEntry]]:
        """Retrieve multiple entries efficiently."""
        await self.ensure_initialized()

        results = {}

        try:
            # Get documents
            doc_refs = [self._collection.document(key) for key in keys]
            docs = await self._client.get_all(doc_refs)

            for key, doc in zip(keys, docs):
                if doc.exists:
                    doc_data = doc.to_dict()

                    # Check expiration
                    expires_at = doc_data.get("metadata", {}).get("expires_at")
                    if expires_at and expires_at < datetime.utcnow():
                        results[key] = None
                        # Delete expired entry in background
                        asyncio.create_task(self.delete(key))
                    else:
                        entry = self._firestore_to_entry(doc_data)
                        entry.metadata.update_access()
                        results[key] = entry

                        # Update access in background
                        asyncio.create_task(self._update_access_metadata(key, entry))
                else:
                    results[key] = None

        except Exception as e:
            logger.error(f"Failed to batch get from Firestore: {e}")
            # Mark remaining as None
            for key in keys:
                if key not in results:
                    results[key] = None

        return results

    async def clear(self, prefix: Optional[str] = None) -> int:
        """Clear entries matching prefix."""
        await self.ensure_initialized()

        try:
            count = 0

            # Get keys to delete
            keys = await self.list_keys(prefix)

            # Delete in batches
            for i in range(0, len(keys), self.batch_size):
                batch_keys = keys[i : i + self.batch_size]
                batch = self._client.batch()

                for key in batch_keys:
                    doc_ref = self._collection.document(key)
                    batch.delete(doc_ref)

                await batch.commit()
                count += len(batch_keys)

            logger.info(f"Cleared {count} entries from Firestore")
            return count

        except Exception as e:
            logger.error(f"Failed to clear Firestore: {e}")
            return 0

    async def stats(self) -> Dict[str, Any]:
        """Get Firestore statistics."""
        await self.ensure_initialized()

        try:
            # Count documents
            count_query = self._collection.count()
            count_result = await count_query.get()
            total_count = count_result[0][0].value

            # Count by tier (should all be WARM)
            tier_counts = {}
            for tier in MemoryTier:
                tier_query = self._collection.where("metadata.tier", "==", tier.value).count()
                tier_result = await tier_query.get()
                tier_counts[tier.value] = tier_result[0][0].value

            # Get access statistics
            high_access_query = self._collection.where("metadata.access_count", ">=", 10).count()
            high_access_result = await high_access_query.get()
            high_access_count = high_access_result[0][0].value

            return {
                "tier": self.tier.value,
                "backend": "Firestore",
                "project_id": self.project_id,
                "database_id": self.database_id,
                "collection": self.collection_name,
                "total_entries": total_count,
                "tier_distribution": tier_counts,
                "high_access_entries": high_access_count,
                "batch_size": self.batch_size,
                "ttl_cleanup_enabled": self.enable_ttl_cleanup,
            }

        except Exception as e:
            logger.error(f"Failed to get stats from Firestore: {e}")
            return {"tier": self.tier.value, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Check Firestore health."""
        try:
            # Simple read test
            start = datetime.utcnow()
            await self._collection.document("_health_check").get()
            latency_ms = (datetime.utcnow() - start).total_seconds() * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "project_id": self.project_id,
                "database_id": self.database_id,
                "collection": self.collection_name,
            }

        except Exception as e:
            logger.error(f"Firestore health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "tier": self.tier.value,
            }

    async def _ttl_cleanup_task(self) -> None:
        """Background task to clean up expired entries."""
        while self._initialized:
            try:
                # Query for expired entries
                now = datetime.utcnow()
                expired_query = self._collection.where("metadata.expires_at", "<", now).limit(100)

                expired_docs = await expired_query.get()

                if expired_docs:
                    # Delete in batch
                    batch = self._client.batch()
                    for doc in expired_docs:
                        batch.delete(doc.reference)

                    await batch.commit()
                    logger.info(f"Cleaned up {len(expired_docs)} expired entries from Firestore")

                # Sleep for 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"TTL cleanup task error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute

    async def close(self) -> None:
        """Close Firestore client."""
        if self._client:
            self._client.close()

        self._client = None
        self._collection = None
        self._initialized = False

        logger.info("Closed Firestore client")
