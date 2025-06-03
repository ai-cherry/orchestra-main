"""
"""
    """
    """
        """
        """
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

        except Exception:


            pass
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
        """
                """
            """
                """
            """
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

        except Exception:


            pass
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
        """
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

        except Exception:


            pass
            logger.error(f"Error adjusting pool size: {e}")
            return False

    async def get_connection_diagnostics(self) -> Dict[str, Any]:
        """
        """
                """
            """
                """
            """
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

        except Exception:


            pass
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
        """
                """
            """
            logger.info(f"Terminated {count} idle connections (idle > {idle_seconds}s)")

            return count

        except Exception:


            pass
            logger.error(f"Error terminating idle connections: {e}")
            return 0

    async def get_pool_recommendations(self) -> Dict[str, Any]:
        """
        """
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

        except Exception:


            pass
            logger.error(f"Error getting pool recommendations: {e}")
            return {
                "current_config": {"min_size": self.min_connections, "max_size": self.max_connections},
                "suggested_config": {},
                "recommendations": [],
                "metrics_summary": {},
                "error": str(e),
            }
