import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

# HTTPException kept available for future error handling

logger = logging.getLogger(__name__)

class MemoryServiceStorageAdapter:
    """Enhanced storage adapter with deduplication support"""

    def __init__(self, memory_service, litellm_client, weaviate_adapter, filename, file_type):
        self.memory_service = memory_service
        self.litellm_client = litellm_client
        self.weaviate_adapter = weaviate_adapter
        self.filename = filename
        self.file_type = file_type
        self.file_hash = self._compute_file_hash(filename)

    async def exists(self, fingerprint: str) -> bool:
        """Check if content exists using content hash"""
        try:
            # First check file-level deduplication
            if await self.memory_service.get_by_hash(f"file:{self.file_hash}"):
                return True

            # Then check record-level deduplication
            entry = await self.memory_service.get_by_hash(f"record:{fingerprint}")
            return entry is not None

        except Exception as e:
            logger.error(f"Deduplication check failed: {e}")
            return False  # Fail open to avoid blocking operations

    async def upsert_batch(self, records: List[Dict[str, Any]]) -> None:
        """Process batch with deduplication"""
        deduped_records = []

        for record in records:
            fingerprint = self._fingerprint_record(record)
            if not await self.exists(fingerprint):
                record["_fingerprint"] = fingerprint
                deduped_records.append(record)

        if deduped_records:
            await self._original_upsert_batch(deduped_records)

            # Store file hash after successful processing
            await self.memory_service.store_hash(
                f"file:{self.file_hash}", {"filename": self.filename, "timestamp": datetime.utcnow()}
            )

    def _compute_file_hash(self, filename: str) -> str:
        """Compute SHA-256 hash of file contents"""
        hasher = hashlib.sha256()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _fingerprint_record(self, record: Dict[str, Any]) -> str:
        """Generate content fingerprint"""
        return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
