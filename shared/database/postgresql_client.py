"""
PostgreSQL client for Orchestra AI.

Provides connection pooling, query execution, and common database operations
for all structured data in the Orchestra system.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from contextlib import contextmanager
from uuid import UUID

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


class PostgreSQLClient:
    """PostgreSQL client with connection pooling and common operations."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """Initialize PostgreSQL client with connection pool."""
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = database or os.getenv("POSTGRES_DB", "orchestra")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")
        
        self.connection_string = self._build_connection_string()
        self.pool = self._create_pool(min_connections, max_connections)
        self._ensure_schema()
        
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.database}",
            f"user={self.user}"
        ]
        if self.password:
            parts.append(f"password={self.password}")
        return " ".join(parts)
    
    def _create_pool(self, min_conn: int, max_conn: int) -> ConnectionPool:
        """Create connection pool."""
        return ConnectionPool(
            self.connection_string,
            min_size=min_conn,
            max_size=max_conn,
            kwargs={"row_factory": dict_row}
        )
    
    def _ensure_schema(self) -> None:
        """Ensure orchestra schema exists."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS orchestra")
                conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        with self.pool.connection() as conn:
            yield conn
    
    # Agent operations
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        query = sql.SQL("""
            INSERT INTO orchestra.agents 
            (name, description, capabilities, autonomy_level, model_config)
            VALUES (%(name)s, %(description)s, %(capabilities)s, %(autonomy_level)s, %(model_config)s)
            RETURNING *
        """)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Convert dict fields to JSON
                if "capabilities" in agent_data and isinstance(agent_data["capabilities"], dict):
                    agent_data["capabilities"] = json.dumps(agent_data["capabilities"])
                if "model_config" in agent_data and isinstance(agent_data["model_config"], dict):
                    agent_data["model_config"] = json.dumps(agent_data["model_config"])
                    
                cur.execute(query, agent_data)
                result = cur.fetchone()
                conn.commit()
                return result
    
    def get_agent(self, agent_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        query = "SELECT * FROM orchestra.agents WHERE id = %s"
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(agent_id),))
                return cur.fetchone()
    
    def list_agents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all agents with pagination."""
        query = """
            SELECT * FROM orchestra.agents 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit, offset))
                return cur.fetchall()
    
    def update_agent(self, agent_id: Union[str, UUID], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent."""
        # Build dynamic update query
        set_clauses = []
        params = {"id": str(agent_id)}
        
        for key, value in updates.items():
            if key not in ["id", "created_at"]:  # Don't update these fields
                set_clauses.append(sql.SQL("{} = %({})s").format(sql.Identifier(key), sql.SQL(key)))
                if isinstance(value, dict):
                    params[key] = json.dumps(value)
                else:
                    params[key] = value
        
        if not set_clauses:
            return None
            
        query = sql.SQL("""
            UPDATE orchestra.agents 
            SET {}, updated_at = CURRENT_TIMESTAMP
            WHERE id = %(id)s
            RETURNING *
        """).format(sql.SQL(", ").join(set_clauses))
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result
    
    def delete_agent(self, agent_id: Union[str, UUID]) -> bool:
        """Delete agent."""
        query = "DELETE FROM orchestra.agents WHERE id = %s"
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(agent_id),))
                conn.commit()
                return cur.rowcount > 0
    
    # Workflow operations
    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        query = sql.SQL("""
            INSERT INTO orchestra.workflows 
            (name, definition, status)
            VALUES (%(name)s, %(definition)s, %(status)s)
            RETURNING *
        """)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if "definition" in workflow_data and isinstance(workflow_data["definition"], dict):
                    workflow_data["definition"] = json.dumps(workflow_data["definition"])
                    
                cur.execute(query, workflow_data)
                result = cur.fetchone()
                conn.commit()
                return result
    
    def get_workflow(self, workflow_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        query = "SELECT * FROM orchestra.workflows WHERE id = %s"
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(workflow_id),))
                return cur.fetchone()
    
    def list_workflows(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List workflows with optional status filter."""
        if status:
            query = """
                SELECT * FROM orchestra.workflows 
                WHERE status = %s
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            params = (status, limit, offset)
        else:
            query = """
                SELECT * FROM orchestra.workflows 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            params = (limit, offset)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    # Memory operations
    def save_memory_snapshot(self, agent_id: Union[str, UUID], snapshot_data: Dict[str, Any], vector_ids: List[str]) -> Dict[str, Any]:
        """Save agent memory snapshot."""
        query = sql.SQL("""
            INSERT INTO orchestra.memory_snapshots 
            (agent_id, snapshot_data, vector_ids)
            VALUES (%(agent_id)s, %(snapshot_data)s, %(vector_ids)s)
            RETURNING *
        """)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                params = {
                    "agent_id": str(agent_id),
                    "snapshot_data": json.dumps(snapshot_data),
                    "vector_ids": vector_ids
                }
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result
    
    def get_memory_snapshots(self, agent_id: Union[str, UUID], limit: int = 10) -> List[Dict[str, Any]]:
        """Get memory snapshots for an agent."""
        query = """
            SELECT * FROM orchestra.memory_snapshots 
            WHERE agent_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(agent_id), limit))
                return cur.fetchall()
    
    # Audit log operations
    def create_audit_log(
        self,
        event_type: str,
        actor: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create audit log entry."""
        query = sql.SQL("""
            INSERT INTO orchestra.audit_logs 
            (event_type, actor, resource_type, resource_id, details)
            VALUES (%(event_type)s, %(actor)s, %(resource_type)s, %(resource_id)s, %(details)s)
            RETURNING *
        """)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                params = {
                    "event_type": event_type,
                    "actor": actor,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": json.dumps(details) if details else None
                }
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result
    
    def get_audit_logs(
        self,
        event_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filters."""
        conditions = []
        params = []
        
        if event_type:
            conditions.append("event_type = %s")
            params.append(event_type)
        if resource_type:
            conditions.append("resource_type = %s")
            params.append(resource_type)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])
        
        query = f"""
            SELECT * FROM orchestra.audit_logs 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    # Session operations (replacing Redis)
    def create_session(self, session_id: str, data: Dict[str, Any], expires_at: datetime) -> Dict[str, Any]:
        """Create or update session."""
        query = sql.SQL("""
            INSERT INTO orchestra.sessions (id, data, expires_at)
            VALUES (%(id)s, %(data)s, %(expires_at)s)
            ON CONFLICT (id) DO UPDATE 
            SET data = EXCLUDED.data, 
                expires_at = EXCLUDED.expires_at,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                params = {
                    "id": session_id,
                    "data": json.dumps(data),
                    "expires_at": expires_at
                }
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session if not expired."""
        query = """
            SELECT * FROM orchestra.sessions 
            WHERE id = %s AND expires_at > CURRENT_TIMESTAMP
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (session_id,))
                return cur.fetchone()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        query = "DELETE FROM orchestra.sessions WHERE id = %s"
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (session_id,))
                conn.commit()
                return cur.rowcount > 0
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        query = "DELETE FROM orchestra.sessions WHERE expires_at < CURRENT_TIMESTAMP"
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                conn.commit()
                return cur.rowcount
    
    # Utility methods
    def execute_query(self, query: str, params: Optional[Union[tuple, dict]] = None) -> List[Dict[str, Any]]:
        """Execute custom query."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    def health_check(self) -> bool:
        """Check database connection health."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self) -> None:
        """Close connection pool."""
        self.pool.close() 