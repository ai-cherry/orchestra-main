"""
Session extensions mixin for unified PostgreSQL.

Provides missing session-related methods through composition without
modifying the core UnifiedPostgreSQL class.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class SessionExtensionsMixin:
    """
    Mixin that adds missing session functionality to UnifiedPostgreSQL.

    Provides session management methods that maintain consistency with
    the existing session operations while adding missing functionality.
    """

    async def session_list(
        self, user_id: Optional[str] = None, agent_id: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List sessions with flexible filtering options.

        This method was called but not defined in the original implementation.
        It provides a unified interface for listing sessions by various criteria.

        Args:
            user_id: Optional filter by user ID
            agent_id: Optional filter by agent ID
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of session dictionaries
        """
        try:
            # Build dynamic query based on filters
            conditions = ["is_active = true", "expires_at > CURRENT_TIMESTAMP"]
            params = []
            param_count = 0

            if user_id:
                param_count += 1
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)

            if agent_id:
                param_count += 1
                conditions.append(f"agent_id = ${param_count}")
                params.append(agent_id)

            # Add limit and offset
            param_count += 1
            limit_param = param_count
            params.append(limit)

            param_count += 1
            offset_param = param_count
            params.append(offset)

            where_clause = " AND ".join(conditions)

            rows = await self._manager.fetch(
                f"""
                SELECT 
                    id,
                    user_id,
                    agent_id,
                    data,
                    created_at,
                    updated_at,
                    expires_at,
                    ip_address,
                    user_agent,
                    metadata,
                    (data->>'interaction_count')::int as interaction_count
                FROM sessions.sessions
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT ${limit_param} OFFSET ${offset_param}
            """,
                *params,
            )

            return [self._format_session(row) for row in rows]

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    async def session_extend(self, session_id: str, additional_ttl: int = 3600) -> bool:
        """
        Extend session expiration time by additional TTL.

        Args:
            session_id: Session ID to extend
            additional_ttl: Additional seconds to add to expiration

        Returns:
            True if session was extended, False otherwise
        """
        try:
            result = await self._manager.execute(
                """
                UPDATE sessions.sessions
                SET expires_at = expires_at + INTERVAL '%s seconds',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 
                  AND is_active = true 
                  AND expires_at > CURRENT_TIMESTAMP
            """,
                session_id,
                additional_ttl,
            )

            return result.split()[-1] != "0"

        except Exception as e:
            logger.error(f"Error extending session {session_id}: {e}")
            return False

    async def session_touch(self, session_id: str) -> bool:
        """
        Update session last access time without modifying data.

        Args:
            session_id: Session ID to touch

        Returns:
            True if session was touched, False otherwise
        """
        try:
            result = await self._manager.execute(
                """
                UPDATE sessions.sessions
                SET updated_at = CURRENT_TIMESTAMP,
                    data = jsonb_set(
                        data, 
                        '{last_accessed}', 
                        to_jsonb(CURRENT_TIMESTAMP::text)
                    )
                WHERE id = $1 
                  AND is_active = true 
                  AND expires_at > CURRENT_TIMESTAMP
            """,
                session_id,
            )

            return result.split()[-1] != "0"

        except Exception as e:
            logger.error(f"Error touching session {session_id}: {e}")
            return False

    async def session_bulk_delete(self, session_ids: List[str]) -> int:
        """
        Bulk delete multiple sessions efficiently.

        Args:
            session_ids: List of session IDs to delete

        Returns:
            Number of sessions deleted
        """
        if not session_ids:
            return 0

        try:
            # Soft delete for audit trail
            result = await self._manager.execute(
                """
                UPDATE sessions.sessions
                SET is_active = false,
                    updated_at = CURRENT_TIMESTAMP,
                    data = jsonb_set(data, '{deleted_at}', to_jsonb(CURRENT_TIMESTAMP::text))
                WHERE id = ANY($1::text[])
                  AND is_active = true
            """,
                session_ids,
            )

            count = int(result.split()[-1])
            logger.info(f"Bulk deleted {count} sessions")
            return count

        except Exception as e:
            logger.error(f"Error bulk deleting sessions: {e}")
            return 0

    async def session_get_active_count(
        self, user_id: Optional[str] = None, agent_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get count of active sessions with optional filtering.

        Args:
            user_id: Optional filter by user ID
            agent_id: Optional filter by agent ID

        Returns:
            Dictionary with session counts
        """
        try:
            # Build conditions
            conditions = ["is_active = true", "expires_at > CURRENT_TIMESTAMP"]
            params = []

            if user_id:
                conditions.append(f"user_id = ${len(params) + 1}")
                params.append(user_id)

            if agent_id:
                conditions.append(f"agent_id = ${len(params) + 1}")
                params.append(agent_id)

            where_clause = " AND ".join(conditions)

            result = await self._manager.fetchrow(
                f"""
                SELECT 
                    COUNT(*) as total_active,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT agent_id) as unique_agents,
                    AVG((data->>'interaction_count')::int) as avg_interactions
                FROM sessions.sessions
                WHERE {where_clause}
            """,
                *params,
            )

            return {
                "total_active": result["total_active"] or 0,
                "unique_users": result["unique_users"] or 0,
                "unique_agents": result["unique_agents"] or 0,
                "avg_interactions": float(result["avg_interactions"] or 0),
            }

        except Exception as e:
            logger.error(f"Error getting active session count: {e}")
            return {"total_active": 0, "unique_users": 0, "unique_agents": 0, "avg_interactions": 0.0}

    def _format_session(self, row) -> Dict[str, Any]:
        """
        Format session row into consistent dictionary format.

        Args:
            row: Database row

        Returns:
            Formatted session dictionary
        """
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "agent_id": row["agent_id"],
            "data": row["data"],
            "metadata": row.get("metadata", {}),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
            "ip_address": str(row["ip_address"]) if row.get("ip_address") else None,
            "user_agent": row.get("user_agent"),
            "interaction_count": row.get("interaction_count", 0),
        }
