#!/usr/bin/env python3
"""
"""
    """
    """
    _instance: Optional["PostgreSQLConnectionManager"] = None
    _pool: Optional[Pool] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """Ensure singleton pattern."""
        """Initialize connection manager configuration."""
        if not hasattr(self, "_initialized"):
            self.dsn = self._build_dsn()
            self.min_connections = int(os.getenv("PG_POOL_MIN", "10"))
            self.max_connections = int(os.getenv("PG_POOL_MAX", "50"))
            self._initialized = True

    def _build_dsn(self) -> str:
        """Build PostgreSQL DSN from environment variables."""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "cherry_ai")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    async def initialize(self) -> None:
        """
        """
            logger.info("Initializing PostgreSQL connection pool...")

            # Create pool with performance optimizations
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_connections,
                max_size=self.max_connections,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
                timeout=60.0,
                command_timeout=60.0,
                statement_cache_size=100,
                max_cached_statement_lifetime=3600.0,
                # Performance settings
                server_settings={
                    "jit": "on",
                    "max_parallel_workers_per_gather": "4",
                    "random_page_cost": "1.1",
                    "effective_cache_size": "4GB",
                    "shared_buffers": "1GB",
                    "work_mem": "64MB",
                    "maintenance_work_mem": "256MB",
                    "effective_io_concurrency": "200",
                    "wal_buffers": "16MB",
                    "checkpoint_completion_target": "0.9",
                    "max_wal_size": "4GB",
                    "min_wal_size": "1GB",
                },
            )

            # Ensure cherry_ai schema exists
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE SCHEMA IF NOT EXISTS cherry_ai")
                await conn.execute("CREATE SCHEMA IF NOT EXISTS cache")
                await conn.execute("CREATE SCHEMA IF NOT EXISTS sessions")

            logger.info(f"PostgreSQL pool initialized: {self.min_connections}-{self.max_connections} connections")

    async def close(self) -> None:
        """Close the connection pool gracefully."""
                logger.info("PostgreSQL connection pool closed")

    @property
    def pool(self) -> Pool:
        """Get the connection pool."""
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")
        return self._pool

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        """Acquire a connection and start a transaction."""
        """Execute a query without returning results."""
        """Execute a query and return a single value."""
        """Execute a query and return a single row."""
        """Execute a query and return all rows."""
        """Perform comprehensive health check."""
                await conn.fetchval("SELECT 1")

            # Pool statistics
            pool_stats = {
                "min_size": self._pool.get_min_size(),
                "max_size": self._pool.get_max_size(),
                "size": self._pool.get_size(),
                "free_connections": self._pool.get_idle_size(),
                "used_connections": self._pool.get_size() - self._pool.get_idle_size(),
            }

            # Database statistics
            async with self.acquire() as conn:
                db_stats = await conn.fetchrow(
                    """
                """
                "status": "healthy",
                "pool": pool_stats,
                "database": {
                    "size_bytes": db_stats["db_size"],
                    "active_connections": db_stats["active_connections"],
                    "active_queries": db_stats["active_queries"],
                },
            }
        except Exception:

            pass
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

# Global instance
_connection_manager: Optional[PostgreSQLConnectionManager] = None

async def get_connection_manager() -> PostgreSQLConnectionManager:
    """Get or create the global connection manager."""
    """Close the global connection manager."""