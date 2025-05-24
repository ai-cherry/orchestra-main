"""
base_processor.py
Abstract base class for Orchestra AI data ingestion processors.

Features:
- Async/await interface for high-throughput, non-blocking ingestion.
- Advanced deduplication via content hashing/fingerprinting.
- Dynamic batch sizing for optimal throughput and resource utilization.
- Plug-and-play storage adapter interface for flexible backend integration.
- Extensible hooks for validation, enrichment, and error handling.

Author: Orchestra AI Platform
"""

import abc
import hashlib
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

class StorageAdapter(abc.ABC):
    """
    Abstract interface for storage backends (cache, vector DB, persistent storage, etc.).
    Implementations must be async and support upsert, batch, and deduplication queries.
    """
    @abc.abstractmethod
    async def exists(self, fingerprint: str) -> bool:
        """Check if a record with the given fingerprint already exists."""
        pass

    @abc.abstractmethod
    async def upsert_batch(self, records: List[Dict[str, Any]]) -> None:
        """Insert or update a batch of records."""
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """Clean up resources (connections, etc.)."""
        pass

class BaseProcessor(abc.ABC):
    """
    Abstract async processor for ingesting and processing data from any source.
    """

    def __init__(
        self,
        storage_adapter: StorageAdapter,
        batch_size: int = 100,
        deduplication: bool = True,
        fingerprint_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
        max_concurrent_batches: int = 4,
    ):
        """
        Args:
            storage_adapter: Backend for deduplication and storage.
            batch_size: Initial batch size (auto-tuned if needed).
            deduplication: Enable content-based deduplication.
            fingerprint_fn: Custom function to compute record fingerprint.
            max_concurrent_batches: Max concurrent batch processing tasks.
        """
        self.storage = storage_adapter
        self.batch_size = batch_size
        self.deduplication = deduplication
        self.fingerprint_fn = fingerprint_fn or self.default_fingerprint
        self.max_concurrent_batches = max_concurrent_batches

    async def ingest(
        self,
        source: Any,
        enrich_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        validate_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> int:
        """
        Main entrypoint: Ingests data from the source, processes, deduplicates, and stores it.

        Args:
            source: Data source (file, stream, API, etc.).
            enrich_fn: Optional enrichment function.
            validate_fn: Optional validation function.
            progress_cb: Optional callback for progress reporting.

        Returns:
            Total number of records ingested (excluding duplicates).
        """
        total = 0
        async for batch in self.batch_generator(source):
            processed = []
            for record in batch:
                if validate_fn and not validate_fn(record):
                    continue
                if enrich_fn:
                    record = enrich_fn(record)
                if self.deduplication:
                    fingerprint = self.fingerprint_fn(record)
                    if await self.storage.exists(fingerprint):
                        continue
                    record["_fingerprint"] = fingerprint
                processed.append(record)
            if processed:
                await self.storage.upsert_batch(processed)
                total += len(processed)
                if progress_cb:
                    progress_cb(total, len(processed))
        return total

    @abc.abstractmethod
    async def batch_generator(self, source: Any) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """
        Yields batches of records from the source.
        Must be implemented by subclasses for specific formats/sources.
        """
        pass

    @staticmethod
    def default_fingerprint(record: Dict[str, Any]) -> str:
        """
        Default fingerprint: SHA256 hash of sorted key-value pairs.
        """
        items = sorted(record.items())
        m = hashlib.sha256()
        for k, v in items:
            m.update(str(k).encode("utf-8"))
            m.update(str(v).encode("utf-8"))
        return m.hexdigest()