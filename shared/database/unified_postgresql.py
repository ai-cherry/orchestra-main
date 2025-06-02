#!/usr/bin/env python3
"""
Unified PostgreSQL Client for Orchestra AI.

This module provides a single, comprehensive PostgreSQL interface that combines
all functionality (cache, sessions, data storage) using a shared connection pool.
Eliminates all duplication and provides optimal performance.
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import asynccontextmanager
import asyncpg
import logging

from .connection_manager import get_connection_manager, PostgreSQLConnectionManager

logger = logging.getLogger(__name__)

class UnifiedPostgreSQL:
    """
    Unified PostgreSQL interface combining all functionality with shared resources.
    Provides cache, sessions, and data storage through a single optimized interface.
    """

    def __init__(self):
        """Initialize unified PostgreSQL client."""
        self._manager: Optional[PostgreSQLConnectionManager] = None
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the client and ensure all schemas/tables exist."""
        if self._initialized:
            return

        # Get shared connection manager
        self._manager = await get_connection_manager()

        # Create all required tables
        await self._create_all_tables()

        # Start background cleanup tasks
        await self._start_cleanup_tasks()

        self._initialized = True
        logger.info("Unified PostgreSQL client initialized")

    async def close(self) -> None:
        """Close client and stop all background tasks."""
        # Cancel cleanup tasks
        for task_name, task in self._cleanup_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Cleanup task {task_name} cancelled")

        self._cleanup_tasks.clear()
        self._initialized = False

    async def _create_all_tables(self) -> None:
        """Create all required tables with optimal structure."""
        async with self._manager.transaction() as conn:
            # Cache table with automatic expiration
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache.entries (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    tags TEXT[] DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_cache_expires_at 
                ON cache.entries (expires_at) 
                WHERE expires_at > CURRENT_TIMESTAMP;
                
                CREATE INDEX IF NOT EXISTS idx_cache_tags 
                ON cache.entries USING GIN (tags);
                
                CREATE INDEX IF NOT EXISTS idx_cache_accessed_at 
                ON cache.entries (accessed_at DESC);
            """
            )

            # Sessions table with enhanced tracking
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions.sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    agent_id TEXT,
                    data JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    ip_address INET,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT true,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON sessions.sessions (user_id) 
                WHERE is_active = true;
                
                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
                ON sessions.sessions (expires_at) 
                WHERE is_active = true;
                
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at 
                ON sessions.sessions (updated_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_sessions_agent_id 
                ON sessions.sessions (agent_id) 
                WHERE is_active = true;
            """
            )

            # Agents table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestra.agents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    capabilities JSONB DEFAULT '{}',
                    autonomy_level INTEGER DEFAULT 1,
                    model_config JSONB DEFAULT '{}',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_agents_name ON orchestra.agents (name);
                CREATE INDEX IF NOT EXISTS idx_agents_status ON orchestra.agents (status);
                CREATE INDEX IF NOT EXISTS idx_agents_created_at ON orchestra.agents (created_at DESC);
            """
            )

            # Workflows table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestra.workflows (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL,
                    definition JSONB NOT NULL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_workflows_name ON orchestra.workflows (name);
                CREATE INDEX IF NOT EXISTS idx_workflows_status ON orchestra.workflows (status);
                CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON orchestra.workflows (created_at DESC);
            """
            )

            # Audit logs table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestra.audit_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    details JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    user_agent TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_audit_event_type ON orchestra.audit_logs (event_type);
                CREATE INDEX IF NOT EXISTS idx_audit_resource ON orchestra.audit_logs (resource_type, resource_id);
                CREATE INDEX IF NOT EXISTS idx_audit_created_at ON orchestra.audit_logs (created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_audit_actor ON orchestra.audit_logs (actor);
            """
            )

            # Memory snapshots table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestra.memory_snapshots (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id UUID NOT NULL,
                    snapshot_data JSONB NOT NULL,
                    vector_ids TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_memory_agent_id ON orchestra.memory_snapshots (agent_id);
                CREATE INDEX IF NOT EXISTS idx_memory_created_at ON orchestra.memory_snapshots (created_at DESC);
            """
            )

            # Create update trigger for updated_at columns
            await conn.execute(
                """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """
            )

            # Apply trigger to tables with updated_at
            for table in ["sessions.sessions", "orchestra.agents", "orchestra.workflows"]:
                table_name = table.split(".")[-1]
                await conn.execute(
                    f"""
                    DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table};
                    CREATE TRIGGER update_{table_name}_updated_at 
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                """
                )

    async def _start_cleanup_tasks(self) -> None:
        """Start background cleanup tasks."""
        # Cache cleanup every 5 minutes
        self._cleanup_tasks["cache"] = asyncio.create_task(
            self._cleanup_loop("cache", 300, self._cleanup_expired_cache)
        )

        # Session cleanup every hour
        self._cleanup_tasks["sessions"] = asyncio.create_task(
            self._cleanup_loop("sessions", 3600, self._cleanup_expired_sessions)
        )

    async def _cleanup_loop(self, name: str, interval: int, cleanup_func) -> None:
        """Generic cleanup loop for background tasks."""
        while True:
            try:
                await asyncio.sleep(interval)
                count = await cleanup_func()
                if count > 0:
                    logger.info(f"{name} cleanup: removed {count} expired entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in {name} cleanup: {e}")

    async def _cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries."""
        result = await self._manager.execute(
            """
            DELETE FROM cache.entries 
            WHERE expires_at <= CURRENT_TIMESTAMP
        """
        )
        return int(result.split()[-1])

    async def _cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        # Soft delete expired sessions
        result = await self._manager.execute(
            """
            UPDATE sessions.sessions 
            SET is_active = false 
            WHERE is_active = true AND expires_at <= CURRENT_TIMESTAMP
        """
        )
        expired = int(result.split()[-1])

        # Hard delete old inactive sessions
        result = await self._manager.execute(
            """
            DELETE FROM sessions.sessions 
            WHERE is_active = false AND updated_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
        """
        )
        deleted = int(result.split()[-1])

        return expired + deleted

    # ==================== Cache Operations ====================

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache with access tracking."""
        row = await self._manager.fetchrow(
            """
            UPDATE cache.entries
            SET accessed_at = CURRENT_TIMESTAMP,
                access_count = access_count + 1
            WHERE key = $1 AND expires_at > CURRENT_TIMESTAMP
            RETURNING value
        """,
            key,
        )

        return row["value"] if row else None

    async def cache_set(self, key: str, value: Any, ttl: int = 3600, tags: Optional[List[str]] = None) -> bool:
        """Set cache value with TTL and optional tags."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        tags = tags or []

        await self._manager.execute(
            """
            INSERT INTO cache.entries (key, value, expires_at, tags)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                expires_at = EXCLUDED.expires_at,
                tags = EXCLUDED.tags,
                accessed_at = CURRENT_TIMESTAMP
        """,
            key,
            json.dumps(value),
            expires_at,
            tags,
        )

        return True

    async def cache_delete(self, key: str) -> bool:
        """Delete cache entry."""
        result = await self._manager.execute("DELETE FROM cache.entries WHERE key = $1", key)
        return result.split()[-1] != "0"

    async def cache_clear(self, tags: Optional[List[str]] = None) -> int:
        """Clear cache entries, optionally by tags."""
        if tags:
            result = await self._manager.execute(
                """
                DELETE FROM cache.entries 
                WHERE tags && $1::text[]
            """,
                tags,
            )
        else:
            result = await self._manager.execute("DELETE FROM cache.entries")

        return int(result.split()[-1])

    async def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = await self._manager.fetchrow(
            """
            SELECT 
                COUNT(*) as total_entries,
                COUNT(*) FILTER (WHERE expires_at > CURRENT_TIMESTAMP) as active_entries,
                AVG(access_count) as avg_access_count,
                MAX(access_count) as max_access_count,
                pg_size_pretty(pg_total_relation_size('cache.entries')) as table_size
            FROM cache.entries
        """
        )

        return dict(stats)

    # ==================== Session Operations ====================

    async def session_create(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl: int = 86400,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new session with comprehensive tracking."""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        await self._manager.execute(
            """
            INSERT INTO sessions.sessions 
            (id, user_id, agent_id, data, expires_at, ip_address, user_agent, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            session_id,
            user_id,
            agent_id,
            json.dumps(data or {}),
            expires_at,
            ip_address,
            user_agent,
            json.dumps(metadata or {}),
        )

        return session_id

    async def session_get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get active session."""
        row = await self._manager.fetchrow(
            """
            SELECT * FROM sessions.sessions
            WHERE id = $1 AND is_active = true AND expires_at > CURRENT_TIMESTAMP
        """,
            session_id,
        )

        if row:
            return {
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
        if merge_data and data:
            # Get current data
            current = await self.session_get(session_id)
            if not current:
                return False
            current_data = current["data"]
            current_data.update(data)
            data = current_data

        query_parts = ["data = $2"]
        params = [session_id, json.dumps(data or {})]

        if extend_ttl:
            query_parts.append("expires_at = CURRENT_TIMESTAMP + INTERVAL '24 hours'")

        result = await self._manager.execute(
            f"""
            UPDATE sessions.sessions
            SET {', '.join(query_parts)}
            WHERE id = $1 AND is_active = true AND expires_at > CURRENT_TIMESTAMP
        """,
            *params,
        )

        return result.split()[-1] != "0"

    async def session_delete(self, session_id: str) -> bool:
        """Soft delete a session."""
        result = await self._manager.execute(
            """
            UPDATE sessions.sessions
            SET is_active = false
            WHERE id = $1 AND is_active = true
        """,
            session_id,
        )

        return result.split()[-1] != "0"

    async def session_list_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all active sessions for a user."""
        rows = await self._manager.fetch(
            """
            SELECT * FROM sessions.sessions
            WHERE user_id = $1 AND is_active = true AND expires_at > CURRENT_TIMESTAMP
            ORDER BY updated_at DESC
        """,
            user_id,
        )

        return [
            {
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
        row = await self._manager.fetchrow(
            """
            INSERT INTO orchestra.agents 
            (name, description, capabilities, autonomy_level, model_config, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """,
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
        row = await self._manager.fetchrow(
            "SELECT * FROM orchestra.agents WHERE id = $1",
            agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id),
        )

        return self._record_to_dict(row) if row else None

    async def agent_update(self, agent_id: Union[str, uuid.UUID], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent with dynamic fields."""
        # Build update query
        set_clauses = []
        params = [agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id)]
        param_count = 1

        for key, value in updates.items():
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
            UPDATE orchestra.agents
            SET {', '.join(set_clauses)}
            WHERE id = $1
            RETURNING *
        """,
            *params,
        )

        return self._record_to_dict(row) if row else None

    async def agent_list(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List agents with optional filtering."""
        if status:
            rows = await self._manager.fetch(
                """
                SELECT * FROM orchestra.agents
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """,
                status,
                limit,
                offset,
            )
        else:
            rows = await self._manager.fetch(
                """
                SELECT * FROM orchestra.agents
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """,
                limit,
                offset,
            )

        return [self._record_to_dict(row) for row in rows]

    async def agent_delete(self, agent_id: Union[str, uuid.UUID]) -> bool:
        """Delete an agent."""
        result = await self._manager.execute(
            "DELETE FROM orchestra.agents WHERE id = $1",
            agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id),
        )

        return result.split()[-1] != "0"

    # ==================== Workflow Operations ====================

    async def workflow_create(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        row = await self._manager.fetchrow(
            """
            INSERT INTO orchestra.workflows 
            (name, definition, status, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """,
            workflow_data["name"],
            json.dumps(workflow_data["definition"]),
            workflow_data.get("status", "draft"),
            json.dumps(workflow_data.get("metadata", {})),
        )

        return self._record_to_dict(row)

    async def workflow_get(self, workflow_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        row = await self._manager.fetchrow(
            "SELECT * FROM orchestra.workflows WHERE id = $1",
            workflow_id if isinstance(workflow_id, uuid.UUID) else uuid.UUID(workflow_id),
        )

        return self._record_to_dict(row) if row else None

    async def workflow_list(
        self, status: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List workflows with optional status filter."""
        if status:
            rows = await self._manager.fetch(
                """
                SELECT * FROM orchestra.workflows
                WHERE status = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """,
                status,
                limit,
                offset,
            )
        else:
            rows = await self._manager.fetch(
                """
                SELECT * FROM orchestra.workflows
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """,
                limit,
                offset,
            )

        return [self._record_to_dict(row) for row in rows]

    # ==================== Audit Operations ====================

    async def audit_log(
        self,
        event_type: str,
        actor: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an audit log entry."""
        row = await self._manager.fetchrow(
            """
            INSERT INTO orchestra.audit_logs
            (event_type, actor, resource_type, resource_id, details, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """,
            event_type,
            actor,
            resource_type,
            resource_id,
            json.dumps(details) if details else None,
            ip_address,
            user_agent,
        )

        return self._record_to_dict(row)

    async def audit_query(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query audit logs with multiple filters."""
        conditions = []
        params = []
        param_count = 0

        if event_type:
            param_count += 1
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
            SELECT * FROM orchestra.audit_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """,
            *params,
        )

        return [self._record_to_dict(row) for row in rows]

    # ==================== Memory Operations ====================

    async def memory_snapshot_save(
        self,
        agent_id: Union[str, uuid.UUID],
        snapshot_data: Dict[str, Any],
        vector_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save agent memory snapshot."""
        row = await self._manager.fetchrow(
            """
            INSERT INTO orchestra.memory_snapshots
            (agent_id, snapshot_data, vector_ids, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """,
            agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id),
            json.dumps(snapshot_data),
            vector_ids,
            json.dumps(metadata or {}),
        )

        return self._record_to_dict(row)

    async def memory_snapshot_list(self, agent_id: Union[str, uuid.UUID], limit: int = 10) -> List[Dict[str, Any]]:
        """List memory snapshots for an agent."""
        rows = await self._manager.fetch(
            """
            SELECT * FROM orchestra.memory_snapshots
            WHERE agent_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """,
            agent_id if isinstance(agent_id, uuid.UUID) else uuid.UUID(agent_id),
            limit,
        )

        return [self._record_to_dict(row) for row in rows]

    # ==================== Utility Methods ====================

    def _record_to_dict(self, record: asyncpg.Record) -> Dict[str, Any]:
        """Convert asyncpg Record to dictionary with proper serialization."""
        if not record:
            return {}

        result = dict(record)

        # Convert UUID to string
        for key, value in result.items():
            if isinstance(value, uuid.UUID):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (dict, list)) and isinstance(value, str):
                # Parse JSON strings
                try:
                    result[key] = json.loads(value)
                except:
                    pass

        return result

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        manager_health = await self._manager.health_check()

        # Add table-specific stats
        table_stats = {}
        for schema_table in [
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
        return await self._manager.execute(query, *args)

    async def fetch_raw(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch raw SQL query results."""
        rows = await self._manager.fetch(query, *args)
        return [self._record_to_dict(row) for row in rows]

# Global instance
_unified_postgresql: Optional[UnifiedPostgreSQL] = None

async def get_unified_postgresql() -> UnifiedPostgreSQL:
    """Get or create the global unified PostgreSQL client."""
    global _unified_postgresql
    if _unified_postgresql is None:
        _unified_postgresql = UnifiedPostgreSQL()
        await _unified_postgresql.initialize()
    return _unified_postgresql

async def close_unified_postgresql() -> None:
    """Close the global unified PostgreSQL client."""
    global _unified_postgresql
    if _unified_postgresql:
        await _unified_postgresql.close()
        _unified_postgresql = None
