"""
Enhanced Unified PostgreSQL Client for Orchestra AI.

This module extends the original UnifiedPostgreSQL class with all missing
functionality through mixins, providing a complete implementation without
modifying the original code.
"""

import logging
from typing import Dict, List, Optional, Any, Union

# Import the original class
from .unified_postgresql import UnifiedPostgreSQL

# Import all extension mixins
from .extensions.cache_extensions import CacheExtensionsMixin
from .extensions.session_extensions import SessionExtensionsMixin
from .extensions.memory_extensions import MemoryExtensionsMixin

logger = logging.getLogger(__name__)

class UnifiedPostgreSQLEnhanced(UnifiedPostgreSQL, CacheExtensionsMixin, SessionExtensionsMixin, MemoryExtensionsMixin):
    """
    Enhanced unified PostgreSQL client that includes all missing methods.

    This class extends the original UnifiedPostgreSQL with mixins that provide:
    - Cache extensions: cache_get_by_tags, cache_get_many, cache_set_many, etc.
    - Session extensions: session_list, session_extend, session_analytics, etc.
    - Memory extensions: memory_snapshot_create, memory_snapshot_get, memory_snapshot_list, etc.

    The enhancement is done through composition without modifying the original implementation,
    maintaining backward compatibility while fixing all missing method issues.
    """

    def __init__(self):
        """Initialize enhanced unified PostgreSQL client."""
        super().__init__()
        logger.info("Initialized UnifiedPostgreSQLEnhanced with all extensions")

    async def initialize(self) -> None:
        """
        Initialize the enhanced client with all extensions.

        Calls the parent initialization and ensures all mixin
        functionality is properly integrated.
        """
        await super().initialize()
        logger.info("UnifiedPostgreSQLEnhanced fully initialized with extensions")

    # The following methods provide better integration between mixins and base class

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics across all subsystems.

        Combines statistics from cache, sessions, memory snapshots,
        and connection pool for a complete system overview.

        Returns:
            Dictionary with comprehensive system statistics
        """
        try:
            # Get stats from all subsystems
            cache_info = await self.cache_info()
            session_analytics = await self.session_analytics()
            memory_stats = await self.memory_snapshot_stats()
            base_health = await self.health_check()

            # Combine all statistics
            return {
                "timestamp": cache_info.get(
                    "timestamp", session_analytics.get("timestamp", memory_stats.get("timestamp"))
                ),
                "cache": cache_info,
                "sessions": session_analytics,
                "memory_snapshots": memory_stats,
                "health": base_health,
                "summary": {
                    "total_cache_entries": cache_info.get("statistics", {}).get("total_entries", 0),
                    "active_sessions": session_analytics.get("statistics", {}).get("active_sessions", 0),
                    "total_snapshots": memory_stats.get("summary", {}).get("total_snapshots", 0),
                    "overall_health": base_health.get("status", "unknown"),
                },
            }

        except Exception as e:
            logger.error(f"Error getting comprehensive stats: {e}")
            return {"error": str(e), "cache": {}, "sessions": {}, "memory_snapshots": {}, "health": {}, "summary": {}}

    async def perform_maintenance(self, aggressive: bool = False) -> Dict[str, Any]:
        """
        Perform maintenance across all subsystems.

        Args:
            aggressive: If True, performs more aggressive cleanup

        Returns:
            Dictionary with maintenance results
        """
        try:
            results = {}

            # Clean up expired cache entries
            cache_cleaned = await self._cleanup_expired_cache()
            results["cache_cleaned"] = cache_cleaned

            # Clean up expired sessions
            sessions_cleaned = await self._cleanup_expired_sessions()
            results["sessions_cleaned"] = sessions_cleaned

            # Clean up old memory snapshots (if aggressive)
            if aggressive:
                snapshots_cleaned = await self.memory_snapshot_cleanup(days_old=30, keep_minimum=3)
                results["snapshots_cleaned"] = snapshots_cleaned

                # Clean up old inactive sessions
                inactive_cleaned = await self.session_cleanup_inactive(days_old=7)
                results["inactive_sessions_cleaned"] = inactive_cleaned

            # Analyze tables for query optimization
            await self.execute_raw("ANALYZE cache.entries")
            await self.execute_raw("ANALYZE sessions.sessions")
            await self.execute_raw("ANALYZE orchestra.memory_snapshots")
            results["tables_analyzed"] = True

            logger.info(f"Maintenance completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Error performing maintenance: {e}")
            return {"error": str(e), "cache_cleaned": 0, "sessions_cleaned": 0}

    async def export_state(self, include_data: bool = False) -> Dict[str, Any]:
        """
        Export current state for backup or migration.

        Args:
            include_data: If True, includes actual data (can be large)

        Returns:
            Dictionary with system state
        """
        try:
            state = {
                "version": "2.0",
                "timestamp": datetime.utcnow().isoformat(),
                "statistics": await self.get_comprehensive_stats(),
            }

            if include_data:
                # Export cache entries
                cache_entries = await self.fetch_raw(
                    """
                    SELECT * FROM cache.entries 
                    WHERE expires_at > CURRENT_TIMESTAMP
                    LIMIT 10000
                """
                )
                state["cache_entries"] = cache_entries

                # Export active sessions
                sessions = await self.fetch_raw(
                    """
                    SELECT * FROM sessions.sessions
                    WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP
                    LIMIT 10000
                """
                )
                state["sessions"] = sessions

                # Export recent memory snapshots
                snapshots = await self.fetch_raw(
                    """
                    SELECT * FROM orchestra.memory_snapshots
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
                )
                state["memory_snapshots"] = snapshots

            return state

        except Exception as e:
            logger.error(f"Error exporting state: {e}")
            return {"error": str(e), "version": "2.0", "timestamp": datetime.utcnow().isoformat()}

# Global instance management for enhanced version
_unified_postgresql_enhanced: Optional[UnifiedPostgreSQLEnhanced] = None

async def get_unified_postgresql_enhanced() -> UnifiedPostgreSQLEnhanced:
    """
    Get or create the global enhanced unified PostgreSQL client.

    This is a drop-in replacement for get_unified_postgresql() that includes
    all missing methods through mixins.

    Returns:
        Enhanced unified PostgreSQL client instance
    """
    global _unified_postgresql_enhanced
    if _unified_postgresql_enhanced is None:
        _unified_postgresql_enhanced = UnifiedPostgreSQLEnhanced()
        await _unified_postgresql_enhanced.initialize()
    return _unified_postgresql_enhanced

async def close_unified_postgresql_enhanced() -> None:
    """Close the global enhanced unified PostgreSQL client."""
    global _unified_postgresql_enhanced
    if _unified_postgresql_enhanced:
        await _unified_postgresql_enhanced.close()
        _unified_postgresql_enhanced = None

# Import datetime for export_state method
from datetime import datetime
