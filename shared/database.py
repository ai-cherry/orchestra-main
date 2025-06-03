"""Unified database interface for the orchestrator."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import asyncpg
from asyncpg import Connection, Pool

logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """Unified database interface with connection pooling."""
    
    _pool: Optional[Pool] = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def initialize_pool(cls) -> None:
        """Initialize the connection pool."""
        if cls._pool is not None:
            return
            
        async with cls._lock:
            if cls._pool is not None:
                return
                
            try:
                cls._pool = await asyncpg.create_pool(
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
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    @classmethod
    async def close_pool(cls) -> None:
        """Close the connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database connection pool closed")
    
    def __init__(self):
        """Initialize database interface."""
        self._connection: Optional[Connection] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self._pool is None:
            await self.initialize_pool()
        
        self._connection = await self._pool.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._connection:
            await self._pool.release(self._connection)
            self._connection = None
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results."""
        if not self._connection:
            raise RuntimeError("Database connection not established")
        return await self._connection.execute(query, *args)
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch a single row."""
        if not self._connection:
            raise RuntimeError("Database connection not established")
        row = await self._connection.fetchrow(query, *args)
        return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows."""
        if not self._connection:
            raise RuntimeError("Database connection not established")
        rows = await self._connection.fetch(query, *args)
        return [dict(row) for row in rows]
    
    async def fetch_value(self, query: str, *args) -> Any:
        """Fetch a single value."""
        if not self._connection:
            raise RuntimeError("Database connection not established")
        return await self._connection.fetchval(query, *args)
    
    async def transaction(self):
        """Start a transaction."""
        if not self._connection:
            raise RuntimeError("Database connection not established")
        return self._connection.transaction()