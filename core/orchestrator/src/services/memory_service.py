import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from pydantic import BaseModel
from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub

logger = logging.getLogger(__name__)

class HashRecord(BaseModel):
    """Model for storing hash metadata"""
    """Enhanced with Redis SCAN cleanup"""
        self.hash_prefix = "hash:"
        self.scan_batch_size = 100  # Tune based on Redis performance

    async def store_hash(self, hash_key: str, data: Dict) -> bool:
        """Store a content hash with metadata"""
                content_type=hash_key.split(":")[0],
                reference=data.get("filename", ""),
                timestamp=str(datetime.utcnow()),
                ttl=int(timedelta(days=30).total_seconds()),
            )
            redis_key = f"{self.hash_prefix}{hash_key}"
            return await self.memory_manager.store(redis_key, record.dict())
        except Exception:

            pass
            logger.error(f"Failed to store hash {hash_key}: {e}")
            return False

    async def get_by_hash(self, hash_key: str) -> Optional[HashRecord]:
        """Retrieve hash record if exists"""
            redis_key = f"{self.hash_prefix}{hash_key}"
            data = await self.memory_manager.get(redis_key)
            return HashRecord(**data) if data else None
        except Exception:

            pass
            logger.error(f"Failed to retrieve hash {hash_key}: {e}")
            return None

    async def cleanup_hashes(self) -> int:
        """Clean up expired hash records using Redis SCAN"""
        cursor = "0"

        try:


            pass
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

        except Exception:


            pass
            logger.error(f"Hash cleanup failed: {e}")

        logger.info(f"Cleaned up {cleaned} expired hash records")
        return cleaned

    async def cleanup_hashes_periodically(self, interval: int = 3600):
        """Run cleanup on a schedule"""
    """
    """
        logger.warning("Memory service not initialized - using InMemoryMemoryManagerStub")

    return _memory_service

def initialize_memory_service(memory_manager):
    """Initialize the global memory service with a memory manager."""
    logger.info("Memory service initialized")

def get_memory_manager():
    """Backward compatibility wrapper alias for legacy imports."""