#!/usr/bin/env python3
"""
Connection Pool Manager for Orchestra
Manages database connection pools with monitoring
"""

import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manages connection pools for all databases"""
    
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize all connection pools"""
        if self._initialized:
            return
        
        # PostgreSQL pool
        self.pg_pool = await asyncpg.create_pool(
            host=config.get("POSTGRES_HOST", "localhost"),
            port=config.get("POSTGRES_PORT", 5432),
            user=config.get("POSTGRES_USER", "postgres"),
            password=config.get("POSTGRES_PASSWORD", "postgres"),
            database=config.get("POSTGRES_DB", "conductor"),
            min_size=config.get("DATABASE_POOL_MIN_SIZE", 5),
            max_size=config.get("DATABASE_POOL_MAX_SIZE", 20),
            command_timeout=60,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        logger.info("PostgreSQL connection pool initialized")
        
        # Redis pool
        self.redis_pool = redis.ConnectionPool(
            host=config.get("REDIS_HOST", "localhost"),
            port=config.get("REDIS_PORT", 6379),
            password=config.get("REDIS_PASSWORD"),
            max_connections=config.get("REDIS_MAX_CONNECTIONS", 50),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        logger.info("Redis connection pool initialized")
        
        self._initialized = True
    
    async def get_pg_connection(self):
        """Get PostgreSQL connection from pool"""
        if not self.pg_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        return await self.pg_pool.acquire()
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client with pool"""
        if not self.redis_pool:
            raise RuntimeError("Redis pool not initialized")
        return redis.Redis(connection_pool=self.redis_pool)
    
    async def close(self):
        """Close all connection pools"""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()
        self._initialized = False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connections"""
        health = {
            "postgresql": False,
            "redis": False
        }
        
        # Check PostgreSQL
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health["postgresql"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        
        # Check Redis
        try:
            client = self.get_redis_client()
            await client.ping()
            health["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        return health


# Global instance
_pool_manager = ConnectionPoolManager()


async def get_pool_manager() -> ConnectionPoolManager:
    """Get global connection pool manager"""
    return _pool_manager
