"""
DragonflyDB implementation for short-term memory cache.

This module provides high-performance caching using DragonflyDB with:
- Sub-millisecond latency
- Connection pooling (200 connections)
- Async operations throughout
- Automatic TTL management
- Batch operations for efficiency
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None
    ConnectionPool = None

from .base import BaseMemory, MemoryEntry, MemorySearchResult, MemoryTier
from ..config.dragonfly_config import get_dragonfly_config, validate_dragonfly_config
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)


class DragonflyCache(BaseMemory):
    """
    DragonflyDB-based implementation for hot tier memory.

    Optimized for:
    - High-frequency access patterns
    - Sub-millisecond response times
    - Large connection pools for concurrency
    - Automatic expiration of stale data
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize DragonflyDB cache."""
        super().__init__(MemoryTier.HOT, config)

        # Merge with DragonflyDB config
        dragonfly_config = get_dragonfly_config()
        self.config = {**dragonfly_config, **(config or {})}

        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

        # Performance settings
        self.default_ttl = self.config.get("default_ttl", 3600)  # 1 hour
        self.batch_size = self.config.get("batch_size", 100)
        self.pipeline_size = self.config.get("pipeline_size", 1000)

        # Key prefix for namespace isolation
        self.key_prefix = self.config.get("key_prefix", "mcp:memory:hot:")

    async def initialize(self) -> bool:
        """Initialize DragonflyDB connection with pooling."""
        if not HAS_REDIS:
            logger.error("redis package not installed. Install with: pip install redis[hiredis]")
            return False

        if not validate_dragonfly_config():
            logger.error("Invalid DragonflyDB configuration")
            return False

        try:
            # Create connection pool
            pool_kwargs = self.config.get("connection_pool_kwargs", {})
            self._pool = ConnectionPool(
                host=self.config["host"],
                port=self.config["port"],
                password=self.config.get("password"),
                db=self.config["db"],
                decode_responses=True,
                encoding="utf-8",
                **pool_kwargs,
            )

            # Create client with pool
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()

            # Log connection info
            info = await self._client.info("server")
            logger.info(
                f"Connected to DragonflyDB {info.get('dragonfly_version', 'unknown')} "
                f"at {self.config['host']}:{self.config['port']} "
                f"(DB: {self.config['db']}, Dev mode: {self.config.get('is_dev_mode', False)})"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to initialize DragonflyDB: {e}")
            return False

    async def save(self, entry: MemoryEntry) -> bool:
        """Save entry to DragonflyDB with automatic expiration."""
        await self.ensure_initialized()

        try:
            key = f"{self.key_prefix}{entry.key}"

            # Prepare data
            data = entry.to_dict()
            value = json.dumps(data)

            # Determine TTL
            ttl = entry.metadata.ttl_seconds or self.default_ttl

            # Save with expiration
            if ttl > 0:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)

            # Update stats
            await self._client.hincrby("mcp:stats:hot", "saves", 1)

            logger.debug(f"Saved entry to DragonflyDB: {entry.key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to save to DragonflyDB: {e}")
            return False

    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve entry from DragonflyDB."""
        await self.ensure_initialized()

        try:
            full_key = f"{self.key_prefix}{key}"
            value = await self._client.get(full_key)

            if not value:
                return None

            # Parse entry
            data = json.loads(value)
            entry = MemoryEntry.from_dict(data)

            # Update access metadata
            entry.metadata.update_access()

            # Update in cache (don't wait)
            asyncio.create_task(self._update_access_metadata(full_key, entry))

            # Update stats
            await self._client.hincrby("mcp:stats:hot", "hits", 1)

            return entry

        except Exception as e:
            logger.error(f"Failed to get from DragonflyDB: {e}")
            await self._client.hincrby("mcp:stats:hot", "misses", 1)
            return None

    async def _update_access_metadata(self, key: str, entry: MemoryEntry) -> None:
        """Update access metadata in background."""
        try:
            # Get current TTL
            ttl = await self._client.ttl(key)
            if ttl > 0:
                # Re-save with updated metadata
                value = json.dumps(entry.to_dict())
                await self._client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Failed to update access metadata: {e}")

    async def delete(self, key: str) -> bool:
        """Delete entry from DragonflyDB."""
        await self.ensure_initialized()

        try:
            full_key = f"{self.key_prefix}{key}"
            deleted = await self._client.delete(full_key)

            if deleted:
                await self._client.hincrby("mcp:stats:hot", "deletes", 1)
                logger.debug(f"Deleted entry from DragonflyDB: {key}")

            return bool(deleted)

        except Exception as e:
            logger.error(f"Failed to delete from DragonflyDB: {e}")
            return False

    async def search(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        Search entries in cache.

        Note: DragonflyDB doesn't support vector search natively,
        so this implements basic pattern matching.
        """
        await self.ensure_initialized()

        try:
            results = []

            # Get all keys matching pattern
            pattern = f"{self.key_prefix}*"
            if filters and "prefix" in filters:
                pattern = f"{self.key_prefix}{filters['prefix']}*"

            # Scan keys
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=pattern, count=100)

                # Get values in batch
                if keys:
                    values = await self._client.mget(keys)

                    for key, value in zip(keys, values):
                        if not value:
                            continue

                        try:
                            data = json.loads(value)
                            entry = MemoryEntry.from_dict(data)

                            # Simple text search if query is string
                            if isinstance(query, str):
                                content_str = json.dumps(entry.content).lower()
                                if query.lower() in content_str:
                                    score = content_str.count(query.lower()) / len(content_str)
                                    results.append(MemorySearchResult(entry, score, self.tier))
                            else:
                                # No vector search in cache tier
                                pass

                        except Exception as e:
                            logger.warning(f"Failed to parse entry: {e}")

                if cursor == 0:
                    break

            # Sort by score and limit
            results.sort(reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to search in DragonflyDB: {e}")
            return []

    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys with optional prefix."""
        await self.ensure_initialized()

        try:
            pattern = f"{self.key_prefix}{prefix or ''}*"
            keys = []

            cursor = 0
            while True:
                cursor, batch = await self._client.scan(cursor, match=pattern, count=1000)

                # Strip prefix from keys
                for key in batch:
                    if key.startswith(self.key_prefix):
                        keys.append(key[len(self.key_prefix) :])

                if cursor == 0:
                    break

            return keys

        except Exception as e:
            logger.error(f"Failed to list keys from DragonflyDB: {e}")
            return []

    async def batch_save(self, entries: List[MemoryEntry]) -> Dict[str, bool]:
        """Save multiple entries efficiently using pipeline."""
        await self.ensure_initialized()

        results = {}

        try:
            # Process in chunks
            for i in range(0, len(entries), self.pipeline_size):
                chunk = entries[i : i + self.pipeline_size]

                async with self._client.pipeline(transaction=False) as pipe:
                    for entry in chunk:
                        key = f"{self.key_prefix}{entry.key}"
                        value = json.dumps(entry.to_dict())
                        ttl = entry.metadata.ttl_seconds or self.default_ttl

                        if ttl > 0:
                            pipe.setex(key, ttl, value)
                        else:
                            pipe.set(key, value)

                    # Execute pipeline
                    responses = await pipe.execute()

                    # Map results
                    for entry, response in zip(chunk, responses):
                        results[entry.key] = bool(response)

            # Update stats
            saved_count = sum(1 for success in results.values() if success)
            await self._client.hincrby("mcp:stats:hot", "batch_saves", saved_count)

            logger.info(f"Batch saved {saved_count}/{len(entries)} entries to DragonflyDB")

        except Exception as e:
            logger.error(f"Failed to batch save to DragonflyDB: {e}")
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
            # Add prefix to keys
            full_keys = [f"{self.key_prefix}{key}" for key in keys]

            # Get in batches
            for i in range(0, len(full_keys), self.batch_size):
                batch_keys = full_keys[i : i + self.batch_size]
                batch_values = await self._client.mget(batch_keys)

                for key, full_key, value in zip(keys[i : i + self.batch_size], batch_keys, batch_values):
                    if value:
                        try:
                            data = json.loads(value)
                            entry = MemoryEntry.from_dict(data)
                            entry.metadata.update_access()
                            results[key] = entry

                            # Update access in background
                            asyncio.create_task(self._update_access_metadata(full_key, entry))
                        except Exception as e:
                            logger.warning(f"Failed to parse entry {key}: {e}")
                            results[key] = None
                    else:
                        results[key] = None

            # Update stats
            hit_count = sum(1 for v in results.values() if v is not None)
            miss_count = len(results) - hit_count

            async with self._client.pipeline(transaction=False) as pipe:
                pipe.hincrby("mcp:stats:hot", "batch_hits", hit_count)
                pipe.hincrby("mcp:stats:hot", "batch_misses", miss_count)
                await pipe.execute()

        except Exception as e:
            logger.error(f"Failed to batch get from DragonflyDB: {e}")
            # Mark remaining as None
            for key in keys:
                if key not in results:
                    results[key] = None

        return results

    async def clear(self, prefix: Optional[str] = None) -> int:
        """Clear entries matching prefix."""
        await self.ensure_initialized()

        try:
            pattern = f"{self.key_prefix}{prefix or ''}*"
            count = 0

            # Use SCAN to find keys
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=pattern, count=1000)

                if keys:
                    # Delete in pipeline
                    async with self._client.pipeline(transaction=False) as pipe:
                        for key in keys:
                            pipe.delete(key)

                        deleted = await pipe.execute()
                        count += sum(1 for d in deleted if d)

                if cursor == 0:
                    break

            logger.info(f"Cleared {count} entries from DragonflyDB")
            return count

        except Exception as e:
            logger.error(f"Failed to clear DragonflyDB: {e}")
            return 0

    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        await self.ensure_initialized()

        try:
            # Get DragonflyDB info
            info = await self._client.info()

            # Get custom stats
            stats = await self._client.hgetall("mcp:stats:hot")

            # Count keys
            key_count = 0
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=f"{self.key_prefix}*", count=1000)
                key_count += len(keys)
                if cursor == 0:
                    break

            return {
                "tier": self.tier.value,
                "backend": "DragonflyDB",
                "entries": key_count,
                "memory_used": info.get("used_memory_human", "unknown"),
                "memory_peak": info.get("used_memory_peak_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_connections": info.get("total_connections_received", 0),
                "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "hits": int(stats.get("hits", 0)),
                "misses": int(stats.get("misses", 0)),
                "saves": int(stats.get("saves", 0)),
                "deletes": int(stats.get("deletes", 0)),
                "batch_saves": int(stats.get("batch_saves", 0)),
                "batch_hits": int(stats.get("batch_hits", 0)),
                "batch_misses": int(stats.get("batch_misses", 0)),
                "hit_rate": self._calculate_hit_rate(stats),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            logger.error(f"Failed to get stats from DragonflyDB: {e}")
            return {"tier": self.tier.value, "error": str(e)}

    def _calculate_hit_rate(self, stats: Dict[str, str]) -> float:
        """Calculate cache hit rate."""
        hits = int(stats.get("hits", 0)) + int(stats.get("batch_hits", 0))
        misses = int(stats.get("misses", 0)) + int(stats.get("batch_misses", 0))
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    async def health_check(self) -> Dict[str, Any]:
        """Check DragonflyDB health."""
        try:
            # Ping test
            start = datetime.utcnow()
            await self._client.ping()
            latency_ms = (datetime.utcnow() - start).total_seconds() * 1000

            # Get basic info
            info = await self._client.info("server")

            # Check memory usage
            memory_info = await self._client.info("memory")
            used_memory = int(memory_info.get("used_memory", 0))
            max_memory = int(memory_info.get("maxmemory", 0)) or float("inf")
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory else 0

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "version": info.get("dragonfly_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "memory_usage_percent": round(memory_usage_percent, 2),
                "connected_clients": info.get("connected_clients", 0),
                "db_index": self.config["db"],
                "is_dev_mode": self.config.get("is_dev_mode", False),
            }

        except Exception as e:
            logger.error(f"DragonflyDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "tier": self.tier.value,
            }

    async def close(self) -> None:
        """Close DragonflyDB connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

        self._client = None
        self._pool = None
        self._initialized = False

        logger.info("Closed DragonflyDB connections")
