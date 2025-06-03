# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """
    """
        """Initialize unified PostgreSQL client."""
        """Initialize the client and ensure all schemas/tables exist."""
        logger.info("Unified PostgreSQL client initialized")

    async def close(self) -> None:
        """Close client and stop all background tasks."""
                logger.info(f"Cleanup task {task_name} cancelled")

        self._cleanup_tasks.clear()
        self._initialized = False

    async def _create_all_tables(self) -> None:
        """Create all required tables with optimal structure."""
                """
            """
                """
            """
                """
            """
                """
            """
                """
            """
                """
            """
                """
            """
            for table in ["sessions.sessions", "orchestra.agents", "orchestra.workflows"]:
                table_name = table.split(".")[-1]
                await conn.execute(
                    f"""
                """
        """Start background cleanup tasks."""
        self._cleanup_tasks["cache"] = asyncio.create_task(
            self._cleanup_loop("cache", 300, self._cleanup_expired_cache)
        )

        # Session cleanup every hour
        self._cleanup_tasks["sessions"] = asyncio.create_task(
            self._cleanup_loop("sessions", 3600, self._cleanup_expired_sessions)
        )

    async def _cleanup_loop(self, name: str, interval: int, cleanup_func) -> None:
        """Generic cleanup loop for background tasks."""
                    logger.info(f"{name} cleanup: removed {count} expired entries")
            except Exception:

                pass
                break
            except Exception:

                pass
                logger.error(f"Error in {name} cleanup: {e}")

    async def _cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries."""
            """
        """
        """Clean up expired sessions."""
            """
        """
            """
        """
        """Get value from cache with access tracking."""
            """
        """
        return row["value"] if row else None

    async def cache_set(self, key: str, value: Any, ttl: int = 3600, tags: Optional[List[str]] = None) -> bool:
        """Set cache value with TTL and optional tags."""
            """
        """
        """Delete cache entry."""
        result = await self._manager.execute("DELETE FROM cache.entries WHERE key = $1", key)
        return result.split()[-1] != "0"

    async def cache_clear(self, tags: Optional[List[str]] = None) -> int:
        """Clear cache entries, optionally by tags."""
                """
            """
            result = await self._manager.execute("DELETE FROM cache.entries")

        return int(result.split()[-1])

    async def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
            """
        """
        """Create a new session with comprehensive tracking."""
            """
        """
        """Get active session."""
            """
        """
                "id": row["id"],
                "user_id": row["user_id"],
                "agent_id": row["agent_id"],
                "data": row["data"],
                "metadata": row["metadata"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "expires_at": row["expires_at"].isoformat(),
                "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
                "user_agent": row["user_agent"],
            }
        return None

    async def session_update(
        self, session_id: str, data: Optional[Dict[str, Any]] = None, extend_ttl: bool = True, merge_data: bool = True
    ) -> bool:
        """Update session with optional TTL extension."""
            current_data = current["data"]
            current_data.update(data)
            data = current_data

        query_parts = ["data = $2"]
        params = [session_id, json.dumps(data or {})]

        if extend_ttl:
            query_parts.append("expires_at = CURRENT_TIMESTAMP + INTERVAL '24 hours'")

        result = await self._manager.execute(
            f"""
        """
        return result.split()[-1] != "0"

    async def session_delete(self, session_id: str) -> bool:
        """Soft delete a session."""
            """
        """
        return result.split()[-1] != "0"

    async def session_list_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all active sessions for a user."""
            """
        """
                "id": row["id"],
                "agent_id": row["agent_id"],
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "expires_at": row["expires_at"].isoformat(),
            }
            for row in rows
        ]

    # ==================== Agent Operations ====================

    async def agent_create(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
            """
        """
            agent_data["name"],
            agent_data.get("description"),
            json.dumps(agent_data.get("capabilities", {})),
            agent_data.get("autonomy_level", 1),
            json.dumps(agent_data.get("model_config", {})),
            json.dumps(agent_data.get("metadata", {})),
        )

        return self._record_to_dict(row)

    async def agent_get(self, agent_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
            "SELECT * FROM orchestra.agents WHERE id = $1",
            agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id),
        )

        return self._record_to_dict(row) if row else None

    async def agent_update(self, agent_id: Union[str, uuid.UUID], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent with dynamic fields."""
            if key not in ["id", "created_at", "updated_at"]:
                param_count += 1
                set_clauses.append(f"{key} = ${param_count}")
                if key in ["capabilities", "model_config", "metadata"]:
                    params.append(json.dumps(value))
                else:
                    params.append(value)

        if not set_clauses:
            return None

        row = await self._manager.fetchrow(
            f"""
        """
        """List agents with optional filtering."""
                """
            """
                """
            """
        """Delete an agent."""
            "DELETE FROM orchestra.agents WHERE id = $1",
            agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id),
        )

        return result.split()[-1] != "0"

    # ==================== Workflow Operations ====================

    async def workflow_create(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
            """
        """
            workflow_data["name"],
            json.dumps(workflow_data["definition"]),
            workflow_data.get("status", "draft"),
            json.dumps(workflow_data.get("metadata", {})),
        )

        return self._record_to_dict(row)

    async def workflow_get(self, workflow_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
            "SELECT * FROM orchestra.workflows WHERE id = $1",
            workflow_id if isinstance(workflow_id, uuid.UUID) else uuid.UUID(workflow_id),
        )

        return self._record_to_dict(row) if row else None

    async def workflow_list(
        self, status: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List workflows with optional status filter."""
                """
            """
                """
            """
        """Create an audit log entry."""
            """
        """
        """Query audit logs with multiple filters."""
            conditions.append(f"event_type = ${param_count}")
            params.append(event_type)

        if actor:
            param_count += 1
            conditions.append(f"actor = ${param_count}")
            params.append(actor)

        if resource_type:
            param_count += 1
            conditions.append(f"resource_type = ${param_count}")
            params.append(resource_type)

        if resource_id:
            param_count += 1
            conditions.append(f"resource_id = ${param_count}")
            params.append(resource_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        param_count += 1
        params.append(limit)
        param_count += 1
        params.append(offset)

        rows = await self._manager.fetch(
            f"""
        """
        """Save agent memory snapshot."""
            """
        """
        """List memory snapshots for an agent."""
            """
        """
        """Convert asyncpg Record to dictionary with proper serialization."""
        """Comprehensive health check."""
            "cache.entries",
            "sessions.sessions",
            "orchestra.agents",
            "orchestra.workflows",
            "orchestra.audit_logs",
        ]:
            count = await self._manager.fetchval(f"SELECT COUNT(*) FROM {schema_table}")
            table_stats[schema_table] = count

        return {
            **manager_health,
            "tables": table_stats,
            "cleanup_tasks": {name: not task.done() for name, task in self._cleanup_tasks.items()},
        }

    async def execute_raw(self, query: str, *args) -> Any:
        """Execute raw SQL query (for advanced use cases)."""
        """Fetch raw SQL query results."""
    """Get or create the global unified PostgreSQL client."""
    """Close the global unified PostgreSQL client."""