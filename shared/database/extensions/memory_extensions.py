"""
Memory extensions mixin for unified PostgreSQL.

Provides missing memory-related methods through composition without
modifying the core UnifiedPostgreSQL class.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import json

logger = logging.getLogger(__name__)


class MemoryExtensionsMixin:
    """
    Mixin that adds missing memory snapshot functionality to UnifiedPostgreSQL.

    Provides memory management methods for agent context persistence
    and retrieval with optimized performance.
    """

    async def memory_snapshot_create(
        self,
        agent_id: Union[str, UUID],
        user_id: Optional[str] = None,
        snapshot_data: Dict[str, Any] = None,
        vector_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a memory snapshot for an agent.

        This method was called but not defined in the original implementation.
        It stores agent memory state for persistence and recovery.

        Args:
            agent_id: Agent UUID or string
            user_id: Optional user ID associated with the snapshot
            snapshot_data: Dictionary containing the memory state
            vector_ids: Optional list of vector IDs from Weaviate
            metadata: Optional metadata for the snapshot

        Returns:
            Snapshot ID as string
        """
        try:
            # Ensure agent_id is UUID
            if isinstance(agent_id, str):
                agent_id = UUID(agent_id)

            snapshot_id = uuid4()

            # Store snapshot with optimized JSONB
            await self._manager.execute(
                """
                INSERT INTO orchestra.memory_snapshots 
                (id, agent_id, user_id, snapshot_data, vector_ids, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
            """,
                snapshot_id,
                agent_id,
                user_id,
                json.dumps(snapshot_data or {}),
                vector_ids or [],
                json.dumps(metadata or {}),
            )

            logger.info(f"Created memory snapshot {snapshot_id} for agent {agent_id}")
            return str(snapshot_id)

        except Exception as e:
            logger.error(f"Error creating memory snapshot for agent {agent_id}: {e}")
            raise

    async def memory_snapshot_get(self, snapshot_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory snapshot by ID.

        Args:
            snapshot_id: Snapshot UUID or string

        Returns:
            Snapshot dictionary if found, None otherwise
        """
        try:
            # Ensure snapshot_id is UUID
            if isinstance(snapshot_id, str):
                snapshot_id = UUID(snapshot_id)

            row = await self._manager.fetchrow(
                """
                SELECT 
                    id,
                    agent_id,
                    user_id,
                    snapshot_data,
                    vector_ids,
                    metadata,
                    created_at
                FROM orchestra.memory_snapshots
                WHERE id = $1
            """,
                snapshot_id,
            )

            if row:
                return self._format_memory_snapshot(row)

            return None

        except Exception as e:
            logger.error(f"Error getting memory snapshot {snapshot_id}: {e}")
            return None

    async def memory_snapshot_list(
        self, agent_id: Union[str, UUID], user_id: Optional[str] = None, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List memory snapshots for an agent with optional user filtering.

        Args:
            agent_id: Agent UUID or string
            user_id: Optional filter by user ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of snapshot dictionaries
        """
        try:
            # Ensure agent_id is UUID
            if isinstance(agent_id, str):
                agent_id = UUID(agent_id)

            # Build query with optional user filter
            if user_id:
                rows = await self._manager.fetch(
                    """
                    SELECT 
                        id,
                        agent_id,
                        user_id,
                        snapshot_data,
                        vector_ids,
                        metadata,
                        created_at
                    FROM orchestra.memory_snapshots
                    WHERE agent_id = $1 AND user_id = $2
                    ORDER BY created_at DESC
                    LIMIT $3 OFFSET $4
                """,
                    agent_id,
                    user_id,
                    limit,
                    offset,
                )
            else:
                rows = await self._manager.fetch(
                    """
                    SELECT 
                        id,
                        agent_id,
                        user_id,
                        snapshot_data,
                        vector_ids,
                        metadata,
                        created_at
                    FROM orchestra.memory_snapshots
                    WHERE agent_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                """,
                    agent_id,
                    limit,
                    offset,
                )

            return [self._format_memory_snapshot(row) for row in rows]

        except Exception as e:
            logger.error(f"Error listing memory snapshots for agent {agent_id}: {e}")
            return []

    async def memory_snapshot_delete(self, snapshot_id: Union[str, UUID]) -> bool:
        """
        Delete a memory snapshot.

        Args:
            snapshot_id: Snapshot UUID or string

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Ensure snapshot_id is UUID
            if isinstance(snapshot_id, str):
                snapshot_id = UUID(snapshot_id)

            result = await self._manager.execute(
                """
                DELETE FROM orchestra.memory_snapshots
                WHERE id = $1
            """,
                snapshot_id,
            )

            deleted = result.split()[-1] != "0"
            if deleted:
                logger.info(f"Deleted memory snapshot {snapshot_id}")

            return deleted

        except Exception as e:
            logger.error(f"Error deleting memory snapshot {snapshot_id}: {e}")
            return False

    async def memory_snapshot_cleanup(self, days_old: int = 90, keep_minimum: int = 5) -> int:
        """
        Clean up old memory snapshots while keeping a minimum number per agent.

        Args:
            days_old: Delete snapshots older than this many days
            keep_minimum: Keep at least this many snapshots per agent

        Returns:
            Number of snapshots deleted
        """
        try:
            # Delete old snapshots while keeping minimum per agent
            result = await self._manager.execute(
                """
                WITH ranked_snapshots AS (
                    SELECT 
                        id,
                        agent_id,
                        created_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY agent_id 
                            ORDER BY created_at DESC
                        ) as rank
                    FROM orchestra.memory_snapshots
                )
                DELETE FROM orchestra.memory_snapshots
                WHERE id IN (
                    SELECT id 
                    FROM ranked_snapshots
                    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                      AND rank > %s
                )
            """,
                days_old,
                keep_minimum,
            )

            count = int(result.split()[-1])
            logger.info(f"Cleaned up {count} old memory snapshots")
            return count

        except Exception as e:
            logger.error(f"Error cleaning up memory snapshots: {e}")
            return 0

    async def memory_snapshot_restore(
        self, snapshot_id: Union[str, UUID], target_agent_id: Optional[Union[str, UUID]] = None
    ) -> Dict[str, Any]:
        """
        Restore a memory snapshot, optionally to a different agent.

        Args:
            snapshot_id: Snapshot to restore
            target_agent_id: Optional different agent to restore to

        Returns:
            New snapshot created from restoration
        """
        try:
            # Get original snapshot
            original = await self.memory_snapshot_get(snapshot_id)
            if not original:
                raise ValueError(f"Snapshot {snapshot_id} not found")

            # Use original agent if no target specified
            if target_agent_id is None:
                target_agent_id = original["agent_id"]
            elif isinstance(target_agent_id, str):
                target_agent_id = UUID(target_agent_id)

            # Create new snapshot with restored data
            new_snapshot_id = await self.memory_snapshot_create(
                agent_id=target_agent_id,
                user_id=original.get("user_id"),
                snapshot_data=original["snapshot_data"],
                vector_ids=original.get("vector_ids"),
                metadata={
                    **original.get("metadata", {}),
                    "restored_from": str(snapshot_id),
                    "restored_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Restored snapshot {snapshot_id} to new snapshot {new_snapshot_id}")
            return await self.memory_snapshot_get(new_snapshot_id)

        except Exception as e:
            logger.error(f"Error restoring memory snapshot {snapshot_id}: {e}")
            raise

    async def memory_snapshot_search(
        self, query: str, agent_id: Optional[Union[str, UUID]] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search memory snapshots using full-text search on snapshot data.

        Args:
            query: Search query
            agent_id: Optional filter by agent
            limit: Maximum results

        Returns:
            List of matching snapshots
        """
        try:
            # Build query with optional agent filter
            params = [query, limit]
            agent_filter = ""

            if agent_id:
                if isinstance(agent_id, str):
                    agent_id = UUID(agent_id)
                params.insert(1, agent_id)
                agent_filter = "AND agent_id = $2"
                limit_param = "$3"
            else:
                limit_param = "$2"

            rows = await self._manager.fetch(
                f"""
                SELECT 
                    id,
                    agent_id,
                    user_id,
                    snapshot_data,
                    vector_ids,
                    metadata,
                    created_at,
                    ts_rank(
                        to_tsvector('english', snapshot_data::text),
                        plainto_tsquery('english', $1)
                    ) as rank
                FROM orchestra.memory_snapshots
                WHERE to_tsvector('english', snapshot_data::text) @@ 
                      plainto_tsquery('english', $1)
                {agent_filter}
                ORDER BY rank DESC, created_at DESC
                LIMIT {limit_param}
            """,
                *params,
            )

            return [self._format_memory_snapshot(row) for row in rows]

        except Exception as e:
            logger.error(f"Error searching memory snapshots: {e}")
            return []

    async def memory_snapshot_stats(self, agent_id: Optional[Union[str, UUID]] = None) -> Dict[str, Any]:
        """
        Get statistics about memory snapshots.

        Args:
            agent_id: Optional filter by agent

        Returns:
            Dictionary with snapshot statistics
        """
        try:
            # Build query with optional agent filter
            agent_filter = ""
            params = []

            if agent_id:
                if isinstance(agent_id, str):
                    agent_id = UUID(agent_id)
                params.append(agent_id)
                agent_filter = "WHERE agent_id = $1"

            stats = await self._manager.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total_snapshots,
                    COUNT(DISTINCT agent_id) as unique_agents,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(pg_column_size(snapshot_data)) as avg_snapshot_size,
                    MAX(pg_column_size(snapshot_data)) as max_snapshot_size,
                    MIN(created_at) as oldest_snapshot,
                    MAX(created_at) as newest_snapshot,
                    AVG(array_length(vector_ids, 1)) as avg_vector_count
                FROM orchestra.memory_snapshots
                {agent_filter}
            """,
                *params,
            )

            # Get size distribution
            size_dist = await self._manager.fetch(
                f"""
                SELECT 
                    CASE 
                        WHEN pg_column_size(snapshot_data) < 1024 THEN '< 1KB'
                        WHEN pg_column_size(snapshot_data) < 10240 THEN '1-10KB'
                        WHEN pg_column_size(snapshot_data) < 102400 THEN '10-100KB'
                        WHEN pg_column_size(snapshot_data) < 1048576 THEN '100KB-1MB'
                        ELSE '> 1MB'
                    END as size_range,
                    COUNT(*) as count
                FROM orchestra.memory_snapshots
                {agent_filter}
                GROUP BY size_range
                ORDER BY 
                    CASE size_range
                        WHEN '< 1KB' THEN 1
                        WHEN '1-10KB' THEN 2
                        WHEN '10-100KB' THEN 3
                        WHEN '100KB-1MB' THEN 4
                        ELSE 5
                    END
            """,
                *params,
            )

            return {
                "summary": dict(stats) if stats else {},
                "size_distribution": [dict(row) for row in size_dist],
                "health": {
                    "avg_size_kb": (
                        float(stats["avg_snapshot_size"]) / 1024 if stats and stats["avg_snapshot_size"] else 0
                    ),
                    "total_size_mb": (
                        float(stats["total_snapshots"] * stats["avg_snapshot_size"]) / 1048576
                        if stats and stats["total_snapshots"] and stats["avg_snapshot_size"]
                        else 0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error getting memory snapshot stats: {e}")
            return {"summary": {}, "size_distribution": [], "health": {}, "error": str(e)}

    def _format_memory_snapshot(self, row) -> Dict[str, Any]:
        """
        Format memory snapshot row into consistent dictionary format.

        Args:
            row: Database row

        Returns:
            Formatted snapshot dictionary
        """
        return {
            "id": str(row["id"]),
            "agent_id": str(row["agent_id"]),
            "user_id": row.get("user_id"),
            "snapshot_data": row["snapshot_data"],
            "vector_ids": row.get("vector_ids", []),
            "metadata": row.get("metadata", {}),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "rank": float(row["rank"]) if "rank" in row else None,
        }
