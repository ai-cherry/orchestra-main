"""
Enhanced Connection Manager for PostgreSQL with pool extensions.

This module extends the original PostgreSQLConnectionManager with missing
pool-related methods through composition.
"""

import logging
from typing import Optional, Dict, Any

# Import the original class
from .connection_manager import PostgreSQLConnectionManager, get_connection_manager, close_connection_manager

# Import pool extensions
from .extensions.pool_extensions import PoolExtensionsMixin

logger = logging.getLogger(__name__)


class PostgreSQLConnectionManagerEnhanced(PostgreSQLConnectionManager, PoolExtensionsMixin):
    """
    Enhanced connection manager that includes all missing pool methods.

    This class extends the original PostgreSQLConnectionManager with the
    PoolExtensionsMixin that provides:
    - get_pool_stats: Get detailed connection pool statistics
    - get_extended_pool_stats: Get comprehensive pool and performance metrics
    - adjust_pool_size: Dynamically adjust pool configuration
    - get_connection_diagnostics: Detailed diagnostics for troubleshooting
    - terminate_idle_connections: Clean up idle connections
    - get_pool_recommendations: Get optimization recommendations

    The enhancement maintains full backward compatibility.
    """

    def __init__(self):
        """Initialize enhanced connection manager."""
        super().__init__()
        logger.info("Initialized PostgreSQLConnectionManagerEnhanced with pool extensions")

    async def initialize(self) -> None:
        """
        Initialize the enhanced connection pool.

        Extends the base initialization with additional monitoring setup.
        """
        await super().initialize()

        # Log initial pool configuration
        initial_stats = await self.get_pool_stats()
        logger.info(f"Pool initialized with stats: {initial_stats}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Enhanced health check with additional pool metrics.

        Extends the base health check to include comprehensive pool statistics
        and recommendations.

        Returns:
            Dictionary with enhanced health information
        """
        try:
            # Get base health check
            base_health = await super().health_check()

            # Add extended pool statistics
            extended_stats = await self.get_extended_pool_stats()

            # Add recommendations
            recommendations = await self.get_pool_recommendations()

            # Combine all health information
            return {
                **base_health,
                "extended_pool_stats": extended_stats,
                "recommendations": recommendations["recommendations"],
                "pool_health_summary": {
                    "utilization": extended_stats["derived_metrics"]["pool_utilization"],
                    "cache_hit_ratio": extended_stats["derived_metrics"]["cache_hit_ratio"],
                    "connection_efficiency": extended_stats["derived_metrics"]["connection_efficiency"],
                    "health_score": self._calculate_health_score(extended_stats),
                },
            }

        except Exception as e:
            logger.error(f"Enhanced health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "extended_pool_stats": {},
                "recommendations": [],
                "pool_health_summary": {},
            }

    def _calculate_health_score(self, stats: Dict[str, Any]) -> float:
        """
        Calculate overall health score from 0 to 1.

        Args:
            stats: Extended pool statistics

        Returns:
            Health score between 0 (unhealthy) and 1 (healthy)
        """
        score = 1.0

        # Penalize high utilization
        utilization = stats["derived_metrics"]["pool_utilization"]
        if utilization > 0.9:
            score -= 0.3
        elif utilization > 0.8:
            score -= 0.1

        # Penalize low cache hit ratio
        cache_ratio = stats["derived_metrics"]["cache_hit_ratio"]
        if cache_ratio < 0.8:
            score -= 0.2
        elif cache_ratio < 0.9:
            score -= 0.1

        # Penalize deadlocks
        if stats["health_indicators"]["deadlock_detected"]:
            score -= 0.3

        # Penalize long running queries
        if stats["health_indicators"]["long_running_queries"]:
            score -= 0.2

        return max(0.0, score)

    async def auto_tune_pool(self) -> Dict[str, Any]:
        """
        Automatically tune pool settings based on usage patterns.

        Analyzes current usage and applies recommended settings.

        Returns:
            Dictionary with tuning results
        """
        try:
            # Get recommendations
            recommendations = await self.get_pool_recommendations()

            # Check if adjustment is needed
            current = recommendations["current_config"]
            suggested = recommendations["suggested_config"]

            if current == suggested:
                return {
                    "adjusted": False,
                    "message": "Pool configuration is already optimal",
                    "current_config": current,
                }

            # Log the suggested changes
            logger.info(f"Auto-tuning pool from {current} to {suggested}")

            # Note: Actual pool resizing would require recreating the pool
            # For now, we just update the configuration for next restart
            success = await self.adjust_pool_size(
                min_size=suggested.get("min_size"), max_size=suggested.get("max_size")
            )

            return {
                "adjusted": success,
                "previous_config": current,
                "new_config": suggested,
                "message": "Configuration updated for next pool initialization",
            }

        except Exception as e:
            logger.error(f"Auto-tune pool failed: {e}")
            return {"adjusted": False, "error": str(e)}

    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """
        Get all data needed for a monitoring dashboard.

        Returns:
            Dictionary with comprehensive monitoring data
        """
        try:
            # Gather all monitoring data
            pool_stats = await self.get_pool_stats()
            extended_stats = await self.get_extended_pool_stats()
            diagnostics = await self.get_connection_diagnostics()
            recommendations = await self.get_pool_recommendations()

            # Calculate trend indicators
            utilization = extended_stats["derived_metrics"]["pool_utilization"]
            utilization_status = "critical" if utilization > 0.9 else "warning" if utilization > 0.7 else "healthy"

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "pool_utilization": f"{utilization:.1%}",
                    "pool_status": utilization_status,
                    "total_connections": pool_stats["total_connections"],
                    "active_queries": diagnostics["diagnostics"]["active_queries"],
                    "cache_hit_ratio": f"{extended_stats['derived_metrics']['cache_hit_ratio']:.1%}",
                    "health_score": self._calculate_health_score(extended_stats),
                },
                "pool_stats": pool_stats,
                "performance_metrics": {
                    "cache_hits": extended_stats["efficiency"].get("cache_hits", 0),
                    "disk_reads": extended_stats["efficiency"].get("disk_reads", 0),
                    "transactions_committed": extended_stats["efficiency"].get("transactions_committed", 0),
                    "transactions_rolled_back": extended_stats["efficiency"].get("transactions_rolled_back", 0),
                    "deadlocks": extended_stats["efficiency"].get("deadlocks", 0),
                },
                "active_connections": diagnostics["active_connections"][:10],  # Top 10
                "blocked_queries": [l for l in diagnostics["locks"] if not l["granted"]],
                "recommendations": recommendations["recommendations"],
                "alerts": self._generate_alerts(extended_stats, diagnostics),
            }

        except Exception as e:
            logger.error(f"Error getting monitoring dashboard data: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "summary": {},
                "pool_stats": {},
                "performance_metrics": {},
                "active_connections": [],
                "blocked_queries": [],
                "recommendations": [],
                "alerts": [],
            }

    def _generate_alerts(self, stats: Dict[str, Any], diagnostics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate alerts based on current metrics."""
        alerts = []

        if stats["health_indicators"]["pool_exhausted"]:
            alerts.append(
                {
                    "severity": "critical",
                    "message": "Connection pool is exhausted",
                    "action": "Increase max_connections or investigate connection leaks",
                }
            )

        if stats["health_indicators"]["deadlock_detected"]:
            alerts.append(
                {
                    "severity": "high",
                    "message": "Deadlocks detected in database",
                    "action": "Review query patterns and locking strategy",
                }
            )

        if diagnostics["diagnostics"]["blocked_queries"] > 5:
            alerts.append(
                {
                    "severity": "medium",
                    "message": f"{diagnostics['diagnostics']['blocked_queries']} queries are blocked",
                    "action": "Investigate lock contention",
                }
            )

        if diagnostics["diagnostics"]["idle_connections"] > stats["pool"]["max_size"] * 0.5:
            alerts.append(
                {
                    "severity": "low",
                    "message": "High number of idle connections",
                    "action": "Consider reducing pool size or connection timeout",
                }
            )

        return alerts


# Global instance management for enhanced version
_connection_manager_enhanced: Optional[PostgreSQLConnectionManagerEnhanced] = None


async def get_connection_manager_enhanced() -> PostgreSQLConnectionManagerEnhanced:
    """
    Get or create the global enhanced connection manager.

    This is a drop-in replacement for get_connection_manager() that includes
    all missing pool methods through mixins.

    Returns:
        Enhanced connection manager instance
    """
    global _connection_manager_enhanced
    if _connection_manager_enhanced is None:
        _connection_manager_enhanced = PostgreSQLConnectionManagerEnhanced()
        await _connection_manager_enhanced.initialize()
    return _connection_manager_enhanced


async def close_connection_manager_enhanced() -> None:
    """Close the global enhanced connection manager."""
    global _connection_manager_enhanced
    if _connection_manager_enhanced:
        await _connection_manager_enhanced.close()
        _connection_manager_enhanced = None


# Import datetime for monitoring methods
from datetime import datetime
