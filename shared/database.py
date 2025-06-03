# TODO: Consider adding connection pooling configuration
"""Unified database interface for the orchestrator."""
    """Unified database interface with connection pooling."""
        """Initialize the connection pool."""
                    host=os.getenv("POSTGRES_HOST", "localhost"),
                    port=int(os.getenv("POSTGRES_PORT", "5432")),
                    user=os.getenv("POSTGRES_USER", "postgres"),
                    password=os.getenv("POSTGRES_PASSWORD", ""),
                    database=os.getenv("POSTGRES_DB", "orchestrator"),
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                )
                logger.info("Database connection pool initialized")
            except Exception:

                pass
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @classmethod
    async def close_pool(cls) -> None:
        """Close the connection pool."""
            logger.info("Database connection pool closed")
    
    def __init__(self):
        """Initialize database interface."""
        """Async context manager entry."""
        """Async context manager exit."""
        """Execute a query without returning results."""
            raise RuntimeError("Database connection not established")
        return await self._connection.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
            raise RuntimeError("Database connection not established")
        row = await self._connection.fetchrow(query, *args)
        return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows."""
            raise RuntimeError("Database connection not established")
        rows = await self._connection.fetch(query, *args)
        return [dict(row) for row in rows]
    
    async def fetch_value(self, query: str, *args) -> Any:
        """Fetch a single value."""
            raise RuntimeError("Database connection not established")
        return await self._connection.fetchval(query, *args)
    
    async def transaction(self):
        """Start a transaction."""
            raise RuntimeError("Database connection not established")
        return self._connection.transaction()