import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HashRecord(BaseModel):
    """Model for storing hash metadata"""

    content_type: str  # 'file' or 'record'
    reference: str  # Original content reference
    timestamp: str
    ttl: Optional[int] = None  # TTL in seconds


class MemoryService:
    """Enhanced with Redis SCAN cleanup"""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.hash_prefix = "hash:"
        self.scan_batch_size = 100  # Tune based on Redis performance

    async def store_hash(self, hash_key: str, data: Dict) -> bool:
        """Store a content hash with metadata"""
        try:
            record = HashRecord(
                content_type=hash_key.split(":")[0],
                reference=data.get("filename", ""),
                timestamp=str(datetime.utcnow()),
                ttl=int(timedelta(days=30).total_seconds()),
            )
            redis_key = f"{self.hash_prefix}{hash_key}"
            return await self.memory_manager.store(redis_key, record.dict())
        except Exception as e:
            logger.error(f"Failed to store hash {hash_key}: {e}")
            return False

    async def get_by_hash(self, hash_key: str) -> Optional[HashRecord]:
        """Retrieve hash record if exists"""
        try:
            redis_key = f"{self.hash_prefix}{hash_key}"
            data = await self.memory_manager.get(redis_key)
            return HashRecord(**data) if data else None
        except Exception as e:
            logger.error(f"Failed to retrieve hash {hash_key}: {e}")
            return None

    async def cleanup_hashes(self) -> int:
        """Clean up expired hash records using Redis SCAN"""
        cleaned = 0
        cursor = "0"

        try:
            while True:
                cursor, keys = await self.memory_manager.scan(
                    cursor=cursor, match=f"{self.hash_prefix}*", count=self.scan_batch_size
                )

                for key in keys:
                    ttl = await self.memory_manager.ttl(key)
                    if ttl == -1:  # No TTL set
                        await self.memory_manager.delete(key)
                        cleaned += 1

                if cursor == "0":
                    break

        except Exception as e:
            logger.error(f"Hash cleanup failed: {e}")

        logger.info(f"Cleaned up {cleaned} expired hash records")
        return cleaned

    async def cleanup_hashes_periodically(self, interval: int = 3600):
        """Run cleanup on a schedule"""
        while True:
            await self.cleanup_hashes()
            await asyncio.sleep(interval)
