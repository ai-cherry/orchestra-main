"""
Pool extensions mixin for unified PostgreSQL connection manager.

Provides missing pool-related methods through composition without
modifying the core PostgreSQLConnectionManager class.
"""

from typing import Dict, Any, Optional
import logging
import asyncpg

logger = logging.getLogger(__name__)

class PoolExtensionsMixin:
    """
    Mixin that adds missing pool functionality to PostgreSQLConnectionManager.

    Provides enhanced pool statistics and monitoring capabilities
    for optimal performance tuning and resource management.
    """

    async def get_pool_stats(self) -> Dict[str, int]:
        """
        Get detailed connection pool statistics.

        This method was called but not defined in the original implementation.
        It provides comprehensive pool metrics for monitoring and optimization.

        Returns:
            Dictionary with pool statistics
        """
        try:
            if not self._pool:
                return {
                    "total_connections": 0,
                    "idle_connections": 0,
                    "used_connections": 0,
                    "waiting_queries": 0,
                    "max_size": self.max_connections,
                    "min_size": self.min_connections,
                }

            # Get pool statistics from asyncpg
            pool_size = self._pool.get_size()
            idle_size = self._pool.get_idle_size()
            used_size = pool_size - idle_size

            # Additional statistics if available
            stats = {
                "total_connections": pool_size,
                "idle_connections": idle_size,
                "used_connections": used_size,
                "waiting_queries": 0,  # asyncpg doesn't expose waiting count directly
                "max_size": self._pool.get_max_size(),
                "min_size": self._pool.get_min_size(),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting pool statistics: {e}")
            return {
                "total_connections": 0,
                "idle_connections": 0,
                "used_connections": 0,
                "waiting_queries": 0,
                "max_size": self.max_connections,
                "min_size": self.min_connections,
                "error": str(e),
            }

    async def get_extended_pool_stats(self) -> Dict[str, Any]:
        """
        Get extended pool statistics with performance metrics.

        Returns:
            Dictionary with comprehensive pool and performance statistics
        """
        try:
            basic_stats = await self.get_pool_stats()

            # Get database connection statistics
            db_stats = await self.fetchrow(
                """
                SELECT 
                    (SELECT count(*) FROM pg_stat_activity) as total_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle') as idle_connections,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') as idle_in_transaction,
                    (SELECT count(*) FROM pg_stat_activity WHERE wait_event_type IS NOT NULL) as waiting_connections,
                    (SELECT max(EXTRACT(EPOCH FROM (now() - query_start))) 
                     FROM pg_stat_activity 
                     WHERE state = 'active') as longest_query_seconds,
                    (SELECT avg(EXTRACT(EPOCH FROM (now() - query_start))) 
                     FROM pg_stat_activity 
                     WHERE state = 'active') as avg_query_seconds
            """
            )

            # Get pool efficiency metrics
            efficiency_stats = await self.fetchrow(
                """
                SELECT 
                    pg_stat_database.numbackends as backend_connections,
                    pg_stat_database.xact_commit as transactions_committed,
                    pg_stat_database.xact_rollback as transactions_rolled_back,
                    pg_stat_database.blks_hit as cache_hits,
                    pg_stat_database.blks_read as disk_reads,
                    pg_stat_database.tup_returned as rows_returned,
                    pg_stat_database.tup_fetched as rows_fetched,
                    pg_stat_database.conflicts as conflicts,
                    pg_stat_database.deadlocks as deadlocks
                FROM pg_stat_database
                WHERE datname = current_database()
            """
            )

            # Calculate derived metrics
            cache_hit_ratio = 0.0
            if efficiency_stats and efficiency_stats["cache_hits"] + efficiency_stats["disk_reads"] > 0:
                cache_hit_ratio = float(efficiency_stats["cache_hits"]) / (
                    float(efficiency_stats["cache_hits"]) + float(efficiency_stats["disk_reads"])
                )

            return {
                "pool": basic_stats,
                "database": dict(db_stats) if db_stats else {},
                "efficiency": dict(efficiency_stats) if efficiency_stats else {},
                "derived_metrics": {
                    "cache_hit_ratio": cache_hit_ratio,
                    "pool_utilization": (
                        float(basic_stats["used_connections"]) / float(basic_stats["max_size"])
                        if basic_stats["max_size"] > 0
                        else 0
                    ),
                    "connection_efficiency": (
                        float(basic_stats["used_connections"]) / float(db_stats["total_connections"])
                        if db_stats and db_stats["total_connections"] > 0
                        else 0
                    ),
                },
                "health_indicators": {
                    "pool_exhausted": basic_stats["used_connections"] >= basic_stats["max_size"],
                    "high_utilization": basic_stats["used_connections"] > basic_stats["max_size"] * 0.8,
                    "deadlock_detected": efficiency_stats and efficiency_stats["deadlocks"] > 0,
                    "long_running_queries": db_stats
                    and db_stats["longest_query_seconds"]
                    and db_stats["longest_query_seconds"] > 60,
                },
            }

        except Exception as e:
            logger.error(f"Error getting extended pool statistics: {e}")
            return {
                "pool": await self.get_pool_stats(),
                "database": {},
                "efficiency": {},
                "derived_metrics": {},
                "health_indicators": {},
                "error": str(e),
            }

    async def adjust_pool_size(self, min_size: Optional[int] = None, max_size: Optional[int] = None) -> bool:
        """
        Dynamically adjust pool size limits.

        Args:
            min_size: New minimum pool size
            max_size: New maximum pool size

        Returns:
            True if adjustment successful, False otherwise
        """
        try:
            if not self._pool:
                logger.error("Cannot adjust pool size: pool not initialized")
                return False

            # Validate parameters
            if min_size is not None and max_size is not None and min_size > max_size:
                logger.error(f"Invalid pool size: min_size ({min_size}) > max_size ({max_size})")
                return False

            # asyncpg doesn't support dynamic pool resizing directly
            # Log the request for manual intervention or restart
            logger.warning(
                f"Pool size adjustment requested (min: {min_size}, max: {max_size}). "
                "This requires pool recreation. Consider implementing graceful pool rotation."
            )

            # Update internal configuration for next initialization
            if min_size is not None:
                self.min_connections = min_size
            if max_size is not None:
                self.max_connections = max_size

            return True

        except Exception as e:
            logger.error(f"Error adjusting pool size: {e}")
            return False

    async def get_connection_diagnostics(self) -> Dict[str, Any]:
        """
        Get detailed diagnostics for troubleshooting connection issues.

        Returns:
            Dictionary with connection diagnostics
        """
        try:
            # Get current connections with details
            active_connections = await self.fetch(
                """
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    state,
                    query_start,
                    state_change,
                    wait_event_type,
                    wait_event,
                    SUBSTRING(query, 1, 100) as query_preview
                FROM pg_stat_activity
                WHERE datname = current_database()
                ORDER BY query_start
            """
            )

            # Get lock information
            locks = await self.fetch(
                """
                SELECT 
                    l.pid,
                    l.mode,
                    l.granted,
                    l.relation::regclass as table_name,
                    a.query_start,
                    SUBSTRING(a.query, 1, 100) as query_preview
                FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE l.relation IS NOT NULL
                ORDER BY l.granted, a.query_start
            """
            )

            # Get pool internals
            pool_stats = await self.get_pool_stats()

            # Analyze connection states
            state_summary = {}
            for conn in active_connections:
                state = conn["state"] or "unknown"
                state_summary[state] = state_summary.get(state, 0) + 1

            return {
                "pool_stats": pool_stats,
                "connection_states": state_summary,
                "active_connections": [dict(conn) for conn in active_connections],
                "locks": [dict(lock) for lock in locks],
                "diagnostics": {
                    "blocked_queries": len([l for l in locks if not l["granted"]]),
                    "idle_connections": state_summary.get("idle", 0),
                    "active_queries": state_summary.get("active", 0),
                    "waiting_connections": len([c for c in active_connections if c["wait_event_type"]]),
                    "pool_health": (
                        "healthy" if pool_stats["used_connections"] < pool_stats["max_size"] * 0.8 else "stressed"
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error getting connection diagnostics: {e}")
            return {
                "error": str(e),
                "pool_stats": {},
                "connection_states": {},
                "active_connections": [],
                "locks": [],
                "diagnostics": {},
            }

    async def terminate_idle_connections(self, idle_seconds: int = 300) -> int:
        """
        Terminate connections that have been idle for too long.

        Args:
            idle_seconds: Terminate connections idle longer than this

        Returns:
            Number of connections terminated
        """
        try:
            # Find and terminate idle connections
            result = await self.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND state = 'idle'
                  AND state_change < CURRENT_TIMESTAMP - INTERVAL '%s seconds'
                  AND pid != pg_backend_pid()  -- Don't terminate self
            """,
                idle_seconds,
            )

            # Extract count from result
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Terminated {count} idle connections (idle > {idle_seconds}s)")

            return count

        except Exception as e:
            logger.error(f"Error terminating idle connections: {e}")
            return 0

    async def get_pool_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for optimal pool configuration based on usage patterns.

        Returns:
            Dictionary with pool configuration recommendations
        """
        try:
            # Get current stats
            stats = await self.get_extended_pool_stats()
            pool_stats = stats["pool"]
            db_stats = stats["database"]

            recommendations = []
            suggested_config = {"min_size": self.min_connections, "max_size": self.max_connections}

            # Analyze pool utilization
            utilization = stats["derived_metrics"]["pool_utilization"]

            if utilization > 0.9:
                recommendations.append(
                    {"issue": "High pool utilization", "recommendation": "Increase max_connections", "severity": "high"}
                )
                suggested_config["max_size"] = min(100, self.max_connections * 1.5)

            elif utilization < 0.2 and self.max_connections > 20:
                recommendations.append(
                    {
                        "issue": "Low pool utilization",
                        "recommendation": "Decrease max_connections to save resources",
                        "severity": "low",
                    }
                )
                suggested_config["max_size"] = max(10, int(self.max_connections * 0.7))

            # Check for connection leaks
            if db_stats.get("idle_in_transaction", 0) > 5:
                recommendations.append(
                    {
                        "issue": "Multiple idle-in-transaction connections",
                        "recommendation": "Review transaction handling, possible connection leak",
                        "severity": "medium",
                    }
                )

            # Check cache performance
            cache_hit_ratio = stats["derived_metrics"]["cache_hit_ratio"]
            if cache_hit_ratio < 0.9:
                recommendations.append(
                    {
                        "issue": "Low cache hit ratio",
                        "recommendation": "Consider increasing shared_buffers",
                        "severity": "medium",
                    }
                )

            # Check for deadlocks
            if stats["health_indicators"]["deadlock_detected"]:
                recommendations.append(
                    {
                        "issue": "Deadlocks detected",
                        "recommendation": "Review query patterns and locking strategy",
                        "severity": "high",
                    }
                )

            return {
                "current_config": {"min_size": self.min_connections, "max_size": self.max_connections},
                "suggested_config": suggested_config,
                "recommendations": recommendations,
                "metrics_summary": {
                    "pool_utilization": f"{utilization:.1%}",
                    "cache_hit_ratio": f"{cache_hit_ratio:.1%}",
                    "avg_query_time": f"{db_stats.get('avg_query_seconds', 0):.2f}s",
                },
            }

        except Exception as e:
            logger.error(f"Error getting pool recommendations: {e}")
            return {
                "current_config": {"min_size": self.min_connections, "max_size": self.max_connections},
                "suggested_config": {},
                "recommendations": [],
                "metrics_summary": {},
                "error": str(e),
            }
