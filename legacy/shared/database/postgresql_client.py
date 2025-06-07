"""
"""
    """PostgreSQL client with connection pooling and common operations."""
        """Initialize PostgreSQL client with connection pool."""
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = database or os.getenv("POSTGRES_DB", "cherry_ai")
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")

        self.connection_string = self._build_connection_string()
        self.pool = self._create_pool(min_connections, max_connections)
        self._ensure_schema()

    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        parts = [f"host={self.host}", f"port={self.port}", f"dbname={self.database}", f"user={self.user}"]
        if self.password:
            parts.append(f"password={self.password}")
        return " ".join(parts)

    def _create_pool(self, min_conn: int, max_conn: int) -> ConnectionPool:
        """Create connection pool."""
            self.connection_string, min_size=min_conn, max_size=max_conn, kwargs={"row_factory": dict_row}
        )

    def _ensure_schema(self) -> None:
        """Ensure cherry_ai schema exists."""
                cur.execute("CREATE SCHEMA IF NOT EXISTS cherry_ai")
                conn.commit()

    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        """Create a new agent."""
            """
        """
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
        query = "SELECT * FROM cherry_ai.agents WHERE id = %s"

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(agent_id),))
                return cur.fetchone()

    def list_agents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all agents with pagination."""
        query = """
        """
        """Update agent."""
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

        query = sql.SQL(
            """
        """
        ).format(sql.SQL(", ").join(set_clauses))

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result

    def delete_agent(self, agent_id: Union[str, UUID]) -> bool:
        """Delete agent."""
        query = "DELETE FROM cherry_ai.agents WHERE id = %s"

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(agent_id),))
                conn.commit()
                return cur.rowcount > 0

    # Workflow operations
    def create_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
            """
        """
                if "definition" in workflow_data and isinstance(workflow_data["definition"], dict):
                    workflow_data["definition"] = json.dumps(workflow_data["definition"])

                cur.execute(query, workflow_data)
                result = cur.fetchone()
                conn.commit()
                return result

    def get_workflow(self, workflow_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get workflow by ID."""
        query = "SELECT * FROM cherry_ai.workflows WHERE id = %s"

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (str(workflow_id),))
                return cur.fetchone()

    def list_workflows(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List workflows with optional status filter."""
            query = """
            """
            query = """
            """
        """Save agent memory snapshot."""
            """
        """
                    "agent_id": str(agent_id),
                    "snapshot_data": json.dumps(snapshot_data),
                    "vector_ids": vector_ids,
                }
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result

    def get_memory_snapshots(self, agent_id: Union[str, UUID], limit: int = 10) -> List[Dict[str, Any]]:
        """Get memory snapshots for an agent."""
        query = """
        """
        """Create audit log entry."""
            """
        """
                    "event_type": event_type,
                    "actor": actor,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "details": json.dumps(details) if details else None,
                }
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result

    def get_audit_logs(
        self, event_type: Optional[str] = None, resource_type: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filters."""
            conditions.append("event_type = %s")
            params.append(event_type)
        if resource_type:
            conditions.append("resource_type = %s")
            params.append(resource_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.extend([limit, offset])

        query = f"""
        """
        """Create or update session."""
            """
        """
                params = {"id": session_id, "data": json.dumps(data), "expires_at": expires_at}
                cur.execute(query, params)
                result = cur.fetchone()
                conn.commit()
                return result

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session if not expired."""
        query = """
        """
        """Delete session."""
        query = "DELETE FROM cherry_ai.sessions WHERE id = %s"

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (session_id,))
                conn.commit()
                return cur.rowcount > 0

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        query = "DELETE FROM cherry_ai.sessions WHERE expires_at < CURRENT_TIMESTAMP"

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                conn.commit()
                return cur.rowcount

    # Utility methods
    def execute_query(self, query: str, params: Optional[Union[tuple, dict]] = None) -> List[Dict[str, Any]]:
        """Execute custom query."""
        """Check database connection health."""
                    cur.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute("SELECT 1")
                    return cur.fetchone() is not None
        except Exception:

            pass
            logger.error(f"Health check failed: {e}")
            return False

    def close(self) -> None:
        """Close connection pool."""