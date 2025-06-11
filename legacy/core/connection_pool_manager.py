"""
Connection Pool Manager
Manages database connections efficiently
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ConnectionPoolManager:
    """Manages database connection pools"""
    
    def __init__(self, database_url: str, pool_config: Optional[Dict[str, Any]] = None):
        self.database_url = database_url
        self.pool_config = pool_config or {
            'min_size': 5,
            'max_size': 20,
            'max_queries': 50000,
            'max_inactive_connection_lifetime': 300.0,
            'command_timeout': 60.0
        }
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize connection pool"""
        async with self._lock:
            if self._pool is None:
                logger.info("Creating database connection pool...")
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    **self.pool_config
                )
                logger.info(f"Connection pool created with {self.pool_config}")
    
    async def close(self):
        """Close connection pool"""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("Connection pool closed")
    
    @property
    def pool(self) -> asyncpg.Pool:
        """Get connection pool"""
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args, timeout: float = None):
        """Execute a query"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: float = None):
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: float = None):
        """Fetch single row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, timeout: float = None):
        """Fetch single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self._pool:
            return {
                'size': self._pool.get_size(),
                'free_size': self._pool.get_free_size(),
                'min_size': self._pool.get_min_size(),
                'max_size': self._pool.get_max_size()
            }
        return {}
