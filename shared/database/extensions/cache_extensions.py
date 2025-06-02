"""
Cache extensions mixin for unified PostgreSQL.

Provides missing cache-related methods through composition without
modifying the core UnifiedPostgreSQL class.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CacheExtensionsMixin:
    """
    Mixin that adds missing cache functionality to UnifiedPostgreSQL.

    This mixin provides methods that were called but not defined in the
    original implementation, maintaining the same interface and behavior.
    """

    async def cache_get_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """
        Get cache entries by tags with optimized query.

        Args:
            tags: List of tags to search for

        Returns:
            List of cache entries matching any of the provided tags
        """
        if not tags:
            return []

        try:
            # Use GIN index on tags array for optimal performance
            rows = await self._manager.fetch(
                """
                SELECT 
                    key,
                    value,
                    expires_at,
                    tags,
                    created_at,
                    accessed_at,
                    access_count
                FROM cache.entries
                WHERE tags && $1::text[]  -- Array overlap operator uses GIN index
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY accessed_at DESC
                LIMIT 1000  -- Prevent excessive results
            """,
                tags,
            )

            # Update access statistics for retrieved entries
            if rows:
                keys = [row["key"] for row in rows]
                await self._manager.execute(
                    """
                    UPDATE cache.entries
                    SET accessed_at = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE key = ANY($1::text[])
                """,
                    keys,
                )

            return [self._record_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting cache entries by tags {tags}: {e}")
            return []

    async def cache_get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple cache entries in a single query for performance.

        Args:
            keys: List of cache keys to retrieve

        Returns:
            Dictionary mapping keys to their values (None if not found/expired)
        """
        if not keys:
            return {}

        try:
            # Batch fetch for optimal performance
            rows = await self._manager.fetch(
                """
                UPDATE cache.entries
                SET accessed_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE key = ANY($1::text[])
                  AND expires_at > CURRENT_TIMESTAMP
                RETURNING key, value
            """,
                keys,
            )

            # Build result dictionary
            result = {key: None for key in keys}
            for row in rows:
                result[row["key"]] = row["value"]

            return result

        except Exception as e:
            logger.error(f"Error getting multiple cache entries: {e}")
            return {key: None for key in keys}

    async def cache_set_many(self, items: Dict[str, Any], ttl: int = 3600, tags: Optional[List[str]] = None) -> int:
        """
        Set multiple cache entries in a single query for performance.

        Args:
            items: Dictionary of key-value pairs to cache
            ttl: Time to live in seconds
            tags: Optional tags to apply to all entries

        Returns:
            Number of entries successfully cached
        """
        if not items:
            return 0

        from datetime import datetime, timedelta
        import json

        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        tags = tags or []

        try:
            # Build values for bulk insert
            values = []
            for key, value in items.items():
                values.append((key, json.dumps(value), expires_at, tags))

            # Bulk upsert with ON CONFLICT
            result = await self._manager.execute(
                """
                INSERT INTO cache.entries (key, value, expires_at, tags)
                SELECT * FROM UNNEST($1::text[], $2::jsonb[], $3::timestamptz[], $4::text[][])
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    expires_at = EXCLUDED.expires_at,
                    tags = EXCLUDED.tags,
                    accessed_at = CURRENT_TIMESTAMP
            """,
                [v[0] for v in values],  # keys
                [v[1] for v in values],  # values
                [v[2] for v in values],  # expires_at
                [v[3] for v in values],  # tags
            )

            # Extract count from result
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Cached {count} entries in bulk operation")
            return count

        except Exception as e:
            logger.error(f"Error setting multiple cache entries: {e}")
            return 0

    async def cache_touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        Update expiration time for a cache entry without changing its value.

        Args:
            key: Cache key to touch
            ttl: New TTL in seconds (if None, extends by original TTL)

        Returns:
            True if entry was touched, False if not found
        """
        try:
            if ttl is not None:
                from datetime import datetime, timedelta

                expires_at = datetime.utcnow() + timedelta(seconds=ttl)

                result = await self._manager.execute(
                    """
                    UPDATE cache.entries
                    SET expires_at = $2,
                        accessed_at = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE key = $1 AND expires_at > CURRENT_TIMESTAMP
                """,
                    key,
                    expires_at,
                )
            else:
                # Extend by the difference between current expiry and creation
                result = await self._manager.execute(
                    """
                    UPDATE cache.entries
                    SET expires_at = CURRENT_TIMESTAMP + (expires_at - created_at),
                        accessed_at = CURRENT_TIMESTAMP,
                        access_count = access_count + 1
                    WHERE key = $1 AND expires_at > CURRENT_TIMESTAMP
                """,
                    key,
                )

            return result.split()[-1] != "0"

        except Exception as e:
            logger.error(f"Error touching cache entry {key}: {e}")
            return False

    async def cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information including memory usage and performance metrics.

        Returns:
            Dictionary with comprehensive cache statistics
        """
        try:
            # Get detailed statistics using window functions for performance
            stats = await self._manager.fetchrow(
                """
                WITH cache_stats AS (
                    SELECT 
                        COUNT(*) as total_entries,
                        COUNT(*) FILTER (WHERE expires_at > CURRENT_TIMESTAMP) as active_entries,
                        COUNT(*) FILTER (WHERE expires_at <= CURRENT_TIMESTAMP) as expired_entries,
                        AVG(access_count) as avg_access_count,
                        MAX(access_count) as max_access_count,
                        MIN(access_count) as min_access_count,
                        SUM(pg_column_size(value)) as total_size_bytes,
                        AVG(pg_column_size(value)) as avg_entry_size,
                        MAX(pg_column_size(value)) as max_entry_size,
                        COUNT(DISTINCT tags) as unique_tags_count,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY access_count) as median_access_count,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY access_count) as p95_access_count
                    FROM cache.entries
                ),
                table_stats AS (
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('cache.entries')) as table_size,
                        pg_size_pretty(pg_relation_size('cache.entries')) as data_size,
                        pg_size_pretty(pg_indexes_size('cache.entries')) as index_size
                )
                SELECT * FROM cache_stats CROSS JOIN table_stats
            """
            )

            # Get hot keys (most accessed)
            hot_keys = await self._manager.fetch(
                """
                SELECT key, access_count, expires_at
                FROM cache.entries
                WHERE expires_at > CURRENT_TIMESTAMP
                ORDER BY access_count DESC
                LIMIT 10
            """
            )

            # Get tag distribution
            tag_dist = await self._manager.fetch(
                """
                SELECT tag, COUNT(*) as count
                FROM cache.entries, UNNEST(tags) as tag
                WHERE expires_at > CURRENT_TIMESTAMP
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 20
            """
            )

            return {
                "statistics": dict(stats) if stats else {},
                "hot_keys": [dict(row) for row in hot_keys],
                "tag_distribution": [dict(row) for row in tag_dist],
                "health": {
                    "expired_ratio": (
                        float(stats["expired_entries"]) / float(stats["total_entries"])
                        if stats and stats["total_entries"] > 0
                        else 0
                    ),
                    "avg_entry_size_kb": (
                        float(stats["avg_entry_size"]) / 1024 if stats and stats["avg_entry_size"] else 0
                    ),
                    "cache_efficiency": float(stats["avg_access_count"]) if stats and stats["avg_access_count"] else 0,
                },
            }

        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e), "statistics": {}, "hot_keys": [], "tag_distribution": [], "health": {}}
