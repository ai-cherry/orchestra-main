#!/usr/bin/env python3
"""
PostgreSQL-based caching implementation.
Replaces Redis/DragonflyDB with PostgreSQL for all caching needs.
Uses JSONB for flexible data storage and PostgreSQL's built-in expiration features.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import asyncpg
from asyncpg.pool import Pool
import logging

logger = logging.getLogger(__name__)

class PostgreSQLCache:
    """
    PostgreSQL-based cache implementation with TTL support.
    Uses a dedicated cache table with JSONB storage and automatic expiration.
    """

    def __init__(
        self,
        dsn: str,
        table_name: str = "cache_entries",
        schema: str = "public",
        pool_size: int = 10,
        default_ttl: int = 3600,
    ):
        """
        Initialize PostgreSQL cache.

        Args:
            dsn: PostgreSQL connection string
            table_name: Name of the cache table
            schema: Database schema to use
            pool_size: Connection pool size
            default_ttl: Default TTL in seconds
        """
        self.dsn = dsn
        self.table_name = table_name
        self.schema = schema
        self.pool_size = pool_size
        self.default_ttl = default_ttl
        self.pool: Optional[Pool] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize connection pool and create cache table if needed."""
        # Create connection pool
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=2,
            max_size=self.pool_size,
            command_timeout=60,
        )

        # Create cache table if it doesn't exist
        await self._create_cache_table()

        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())

        logger.info(f"PostgreSQL cache initialized with table {self.schema}.{self.table_name}")

    async def close(self):
        """Close connection pool and stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.pool:
            await self.pool.close()

    async def _create_cache_table(self):
        """Create cache table with proper indexes."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"""
                CREATE SCHEMA IF NOT EXISTS {self.schema}
            """
            )

            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.{self.table_name} (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """
            )

            # Create indexes for performance
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_expires_at 
                ON {self.schema}.{self.table_name} (expires_at)
                WHERE expires_at > CURRENT_TIMESTAMP
            """
            )

            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_accessed_at 
                ON {self.schema}.{self.table_name} (accessed_at)
            """
            )

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self.pool.acquire() as conn:
            # Get non-expired entry and update access time
            row = await conn.fetchrow(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET accessed_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE key = $1 
                  AND expires_at > CURRENT_TIMESTAMP
                RETURNING value
            """,
                key,
            )

            if row:
                return row["value"]
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, if_not_exists: bool = False) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (uses default if not specified)
            if_not_exists: Only set if key doesn't exist

        Returns:
            True if set successfully
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        try:
            async with self.pool.acquire() as conn:
                if if_not_exists:
                    # Only insert if not exists
                    result = await conn.execute(
                        f"""
                        INSERT INTO {self.schema}.{self.table_name} (key, value, expires_at)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (key) DO NOTHING
                    """,
                        key,
                        json.dumps(value),
                        expires_at,
                    )
                    return result.split()[-1] == "1"
                else:
                    # Upsert
                    await conn.execute(
                        f"""
                        INSERT INTO {self.schema}.{self.table_name} (key, value, expires_at)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (key) 
                        DO UPDATE SET 
                            value = EXCLUDED.value,
                            expires_at = EXCLUDED.expires_at,
                            accessed_at = CURRENT_TIMESTAMP
                    """,
                        key,
                        json.dumps(value),
                        expires_at,
                    )
                    return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                DELETE FROM {self.schema}.{self.table_name}
                WHERE key = $1
            """,
                key,
            )
            return result.split()[-1] != "0"

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                f"""
                SELECT EXISTS(
                    SELECT 1 FROM {self.schema}.{self.table_name}
                    WHERE key = $1 AND expires_at > CURRENT_TIMESTAMP
                )
            """,
                key,
            )
            return result

    async def expire(self, key: str, ttl: int) -> bool:
        """Update TTL for existing key."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET expires_at = $2
                WHERE key = $1 AND expires_at > CURRENT_TIMESTAMP
            """,
                key,
                expires_at,
            )
            return result.split()[-1] != "0"

    async def ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key in seconds."""
        async with self.pool.acquire() as conn:
            expires_at = await conn.fetchval(
                f"""
                SELECT expires_at FROM {self.schema}.{self.table_name}
                WHERE key = $1 AND expires_at > CURRENT_TIMESTAMP
            """,
                key,
            )

            if expires_at:
                remaining = (expires_at - datetime.utcnow()).total_seconds()
                return max(0, int(remaining))
            return None

    async def clear(self) -> int:
        """Clear all cache entries."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                DELETE FROM {self.schema}.{self.table_name}
            """
            )
            return int(result.split()[-1])

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.

        Args:
            pattern: SQL LIKE pattern (% for wildcard)

        Returns:
            List of matching keys
        """
        # Convert Redis-style pattern to SQL LIKE
        sql_pattern = pattern.replace("*", "%")

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT key FROM {self.schema}.{self.table_name}
                WHERE key LIKE $1 AND expires_at > CURRENT_TIMESTAMP
                ORDER BY accessed_at DESC
            """,
                sql_pattern,
            )

            return [row["key"] for row in rows]

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET accessed_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE key = ANY($1::text[]) 
                  AND expires_at > CURRENT_TIMESTAMP
                RETURNING key, value
            """,
                keys,
            )

            return {row["key"]: row["value"] for row in rows}

    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple keys at once."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        try:
            async with self.pool.acquire() as conn:
                # Prepare data for bulk insert
                values = [(key, json.dumps(value), expires_at) for key, value in mapping.items()]

                await conn.executemany(
                    f"""
                    INSERT INTO {self.schema}.{self.table_name} (key, value, expires_at)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (key) 
                    DO UPDATE SET 
                        value = EXCLUDED.value,
                        expires_at = EXCLUDED.expires_at,
                        accessed_at = CURRENT_TIMESTAMP
                """,
                    values,
                )
                return True
        except Exception as e:
            logger.error(f"Error in mset: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total_keys,
                    COUNT(*) FILTER (WHERE expires_at > CURRENT_TIMESTAMP) as active_keys,
                    COUNT(*) FILTER (WHERE expires_at <= CURRENT_TIMESTAMP) as expired_keys,
                    AVG(access_count) as avg_access_count,
                    MAX(access_count) as max_access_count,
                    pg_size_pretty(pg_total_relation_size('{self.schema}.{self.table_name}')) as table_size
                FROM {self.schema}.{self.table_name}
            """
            )

            return dict(stats)

    async def _cleanup_expired_entries(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                async with self.pool.acquire() as conn:
                    result = await conn.execute(
                        f"""
                        DELETE FROM {self.schema}.{self.table_name}
                        WHERE expires_at <= CURRENT_TIMESTAMP
                    """
                    )

                    deleted = int(result.split()[-1])
                    if deleted > 0:
                        logger.info(f"Cleaned up {deleted} expired cache entries")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

class CacheManager:
    """
    High-level cache manager supporting multiple cache instances.
    Provides Redis-compatible API for easy migration.
    """

    def __init__(self, dsn: str, prefix: str = "orchestra"):
        """
        Initialize cache manager.

        Args:
            dsn: PostgreSQL connection string
            prefix: Prefix for cache tables
        """
        self.dsn = dsn
        self.prefix = prefix
        self.caches: Dict[str, PostgreSQLCache] = {}

    async def get_cache(self, name: str = "default", **kwargs) -> PostgreSQLCache:
        """Get or create a named cache instance."""
        if name not in self.caches:
            table_name = f"{self.prefix}_{name}_cache"
            cache = PostgreSQLCache(dsn=self.dsn, table_name=table_name, **kwargs)
            await cache.initialize()
            self.caches[name] = cache

        return self.caches[name]

    async def close_all(self):
        """Close all cache instances."""
        for cache in self.caches.values():
            await cache.close()
        self.caches.clear()

# Singleton instance for easy access
_cache_manager: Optional[CacheManager] = None

async def get_cache_manager(dsn: str) -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(dsn)
    return _cache_manager

async def get_cache(name: str = "default", **kwargs) -> PostgreSQLCache:
    """Get a cache instance by name."""
    manager = await get_cache_manager(kwargs.get("dsn", ""))
    return await manager.get_cache(name, **kwargs)
