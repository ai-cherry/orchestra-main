#!/usr/bin/env python3
"""
PostgreSQL-based session storage implementation.
Replaces Redis session storage with PostgreSQL for all session management needs.
Provides high-performance session handling with automatic expiration.
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import asyncpg
from asyncpg.pool import Pool
import logging

logger = logging.getLogger(__name__)

class PostgreSQLSessionStore:
    """
    PostgreSQL-based session store with automatic expiration and high performance.
    Designed to replace Redis for session management in Orchestra AI.
    """

    def __init__(
        self,
        dsn: str,
        table_name: str = "sessions",
        schema: str = "public",
        pool_size: int = 20,
        default_ttl: int = 86400,  # 24 hours
        cleanup_interval: int = 3600,  # 1 hour
    ):
        """
        Initialize PostgreSQL session store.

        Args:
            dsn: PostgreSQL connection string
            table_name: Name of the sessions table
            schema: Database schema to use
            pool_size: Connection pool size
            default_ttl: Default session TTL in seconds
            cleanup_interval: Interval for cleaning expired sessions
        """
        self.dsn = dsn
        self.table_name = table_name
        self.schema = schema
        self.pool_size = pool_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.pool: Optional[Pool] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize connection pool and create session table."""
        # Create connection pool with optimized settings
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=5,
            max_size=self.pool_size,
            command_timeout=60,
            # Performance optimizations
            server_settings={
                "jit": "on",
                "max_parallel_workers_per_gather": "4",
            },
        )

        # Create session table
        await self._create_session_table()

        # Start background cleanup
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

        logger.info(f"PostgreSQL session store initialized with table {self.schema}.{self.table_name}")

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

    async def _create_session_table(self):
        """Create optimized session table with proper indexes."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                f"""
                CREATE SCHEMA IF NOT EXISTS {self.schema}
            """
            )

            # Create session table with optimized structure
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.{self.table_name} (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    data JSONB NOT NULL DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    ip_address INET,
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT true
                )
            """
            )

            # Create indexes for performance
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id 
                ON {self.schema}.{self.table_name} (user_id)
                WHERE is_active = true
            """
            )

            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_expires_at 
                ON {self.schema}.{self.table_name} (expires_at)
                WHERE is_active = true
            """
            )

            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_updated_at 
                ON {self.schema}.{self.table_name} (updated_at DESC)
            """
            )

            # Create function for automatic updated_at
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

            # Create trigger
            await conn.execute(
                f"""
                DROP TRIGGER IF EXISTS update_{self.table_name}_updated_at 
                ON {self.schema}.{self.table_name};
                
                CREATE TRIGGER update_{self.table_name}_updated_at 
                BEFORE UPDATE ON {self.schema}.{self.table_name}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
            )

    async def create_session(
        self,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Create a new session.

        Args:
            user_id: Optional user ID
            data: Initial session data
            ttl: Session TTL in seconds
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        data = data or {}

        async with self.pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self.schema}.{self.table_name} 
                (session_id, user_id, data, expires_at, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                session_id,
                user_id,
                json.dumps(data),
                expires_at,
                ip_address,
                user_agent,
            )

        logger.debug(f"Created session {session_id} for user {user_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.

        Args:
            session_id: Session ID

        Returns:
            Session data or None if not found/expired
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT user_id, data, expires_at, ip_address, user_agent, created_at, updated_at
                FROM {self.schema}.{self.table_name}
                WHERE session_id = $1 
                  AND is_active = true
                  AND expires_at > CURRENT_TIMESTAMP
            """,
                session_id,
            )

            if row:
                return {
                    "session_id": session_id,
                    "user_id": row["user_id"],
                    "data": row["data"],
                    "expires_at": row["expires_at"].isoformat(),
                    "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
                    "user_agent": row["user_agent"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                }
            return None

    async def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None,
        extend_ttl: bool = True,
        merge_data: bool = True,
    ) -> bool:
        """
        Update session data.

        Args:
            session_id: Session ID
            data: New session data
            extend_ttl: Whether to extend the session TTL
            merge_data: Whether to merge with existing data or replace

        Returns:
            True if updated successfully
        """
        async with self.pool.acquire() as conn:
            if merge_data:
                # Merge with existing data
                current = await self.get_session(session_id)
                if not current:
                    return False

                if data:
                    current_data = current["data"]
                    current_data.update(data)
                    data = current_data
                else:
                    data = current["data"]

            updates = ["data = $2"]
            params = [session_id, json.dumps(data or {})]

            if extend_ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl)
                updates.append(f"expires_at = ${len(params) + 1}")
                params.append(expires_at)

            result = await conn.execute(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET {', '.join(updates)}
                WHERE session_id = $1 
                  AND is_active = true
                  AND expires_at > CURRENT_TIMESTAMP
            """,
                *params,
            )

            return result.split()[-1] != "0"

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (soft delete).

        Args:
            session_id: Session ID

        Returns:
            True if deleted
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET is_active = false
                WHERE session_id = $1 AND is_active = true
            """,
                session_id,
            )

            return result.split()[-1] != "0"

    async def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions deleted
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET is_active = false
                WHERE user_id = $1 AND is_active = true
            """,
                user_id,
            )

            return int(result.split()[-1])

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of session data
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT session_id, data, expires_at, ip_address, user_agent, created_at, updated_at
                FROM {self.schema}.{self.table_name}
                WHERE user_id = $1 
                  AND is_active = true
                  AND expires_at > CURRENT_TIMESTAMP
                ORDER BY updated_at DESC
            """,
                user_id,
            )

            return [
                {
                    "session_id": row["session_id"],
                    "user_id": user_id,
                    "data": row["data"],
                    "expires_at": row["expires_at"].isoformat(),
                    "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
                    "user_agent": row["user_agent"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                }
                for row in rows
            ]

    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend session TTL.

        Args:
            session_id: Session ID
            ttl: New TTL in seconds

        Returns:
            True if extended
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)

        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""
                UPDATE {self.schema}.{self.table_name}
                SET expires_at = $2
                WHERE session_id = $1 
                  AND is_active = true
                  AND expires_at > CURRENT_TIMESTAMP
            """,
                session_id,
                expires_at,
            )

            return result.split()[-1] != "0"

    async def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval(
                f"""
                SELECT COUNT(*) 
                FROM {self.schema}.{self.table_name}
                WHERE is_active = true 
                  AND expires_at > CURRENT_TIMESTAMP
            """
            )

            return count

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                f"""
                SELECT 
                    COUNT(*) FILTER (WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP) as active_sessions,
                    COUNT(*) FILTER (WHERE is_active = false) as deleted_sessions,
                    COUNT(*) FILTER (WHERE expires_at <= CURRENT_TIMESTAMP) as expired_sessions,
                    COUNT(DISTINCT user_id) FILTER (WHERE is_active = true AND expires_at > CURRENT_TIMESTAMP) as unique_users,
                    MIN(created_at) as oldest_session,
                    MAX(updated_at) as newest_activity,
                    pg_size_pretty(pg_total_relation_size('{self.schema}.{self.table_name}')) as table_size
                FROM {self.schema}.{self.table_name}
            """
            )

            return dict(stats)

    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                async with self.pool.acquire() as conn:
                    # Soft delete expired sessions
                    result = await conn.execute(
                        f"""
                        UPDATE {self.schema}.{self.table_name}
                        SET is_active = false
                        WHERE is_active = true 
                          AND expires_at <= CURRENT_TIMESTAMP
                    """
                    )

                    expired = int(result.split()[-1])

                    # Hard delete old inactive sessions (older than 30 days)
                    result = await conn.execute(
                        f"""
                        DELETE FROM {self.schema}.{self.table_name}
                        WHERE is_active = false 
                          AND updated_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
                    """
                    )

                    deleted = int(result.split()[-1])

                    if expired > 0 or deleted > 0:
                        logger.info(f"Session cleanup: {expired} expired, {deleted} deleted")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")

# Convenience functions for session management
_session_store: Optional[PostgreSQLSessionStore] = None

async def get_session_store(dsn: str, **kwargs) -> PostgreSQLSessionStore:
    """Get the global session store instance."""
    global _session_store
    if _session_store is None:
        _session_store = PostgreSQLSessionStore(dsn, **kwargs)
        await _session_store.initialize()
    return _session_store

async def create_session(**kwargs) -> str:
    """Create a new session using the global store."""
    store = await get_session_store(kwargs.pop("dsn", ""))
    return await store.create_session(**kwargs)

async def get_session(session_id: str, dsn: str = "") -> Optional[Dict[str, Any]]:
    """Get session data using the global store."""
    store = await get_session_store(dsn)
    return await store.get_session(session_id)

async def update_session(session_id: str, data: Dict[str, Any], dsn: str = "") -> bool:
    """Update session data using the global store."""
    store = await get_session_store(dsn)
    return await store.update_session(session_id, data)

async def delete_session(session_id: str, dsn: str = "") -> bool:
    """Delete a session using the global store."""
    store = await get_session_store(dsn)
    return await store.delete_session(session_id)
