"""
Redis connection pool manager for AI Orchestra.

This module provides a connection pool manager for Redis connections,
ensuring efficient connection management and resource utilization.
"""

import logging
import threading
from typing import Dict, Optional, Any, Tuple

import redis

from ..config import RedisSettings, get_settings
from ..error_handling import handle_exception, safe_execute

logger = logging.getLogger(__name__)


class RedisConnectionPool:
    """
    Manages Redis connection pools for different configurations.
    
    This class provides a thread-safe singleton for managing Redis connection pools,
    ensuring efficient connection reuse and proper resource management.
    """
    
    _pools: Dict[str, redis.ConnectionPool] = {}
    _lock = threading.RLock()  # Thread-safe access to pools
    _metrics: Dict[str, Dict[str, int]] = {}  # Connection usage metrics
    
    @classmethod
    def get_pool_key(cls, host: str, port: int, db: int = 0) -> str:
        """
        Generate a unique key for a connection pool.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database index
            
        Returns:
            A unique key for the connection pool
        """
        return f"{host}:{port}:{db}"
    
    @classmethod
    def get_pool(
        cls, 
        host: str, 
        port: int, 
        db: int = 0, 
        password: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        socket_keepalive: bool = True,
        health_check_interval: int = 30,
    ) -> redis.ConnectionPool:
        """
        Get or create a connection pool for the given Redis configuration.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database index
            password: Redis password
            max_connections: Maximum connections in the pool
            socket_timeout: Socket timeout in seconds
            socket_keepalive: Whether to keep connections alive
            health_check_interval: Health check interval in seconds
            
        Returns:
            A Redis connection pool
        """
        key = cls.get_pool_key(host, port, db)
        
        with cls._lock:
            if key not in cls._pools:
                cls._pools[key] = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True,
                    max_connections=max_connections,
                    socket_timeout=socket_timeout,
                    socket_keepalive=socket_keepalive,
                    health_check_interval=health_check_interval,
                )
                cls._metrics[key] = {
                    "created": 0,
                    "borrowed": 0,
                    "returned": 0,
                    "errors": 0,
                }
                logger.info(f"Created new Redis connection pool for {host}:{port}/{db}")
            
            return cls._pools[key]
    
    @classmethod
    def get_client(
        cls, 
        host: Optional[str] = None, 
        port: Optional[int] = None, 
        db: Optional[int] = None, 
        password: Optional[str] = None,
        **kwargs: Any,
    ) -> redis.Redis:
        """
        Get a Redis client from the connection pool.
        
        If no parameters are provided, the default settings from the configuration are used.
        
        Args:
            host: Redis host (optional, defaults to configuration)
            port: Redis port (optional, defaults to configuration)
            db: Redis database index (optional, defaults to configuration)
            password: Redis password (optional, defaults to configuration)
            **kwargs: Additional arguments to pass to the connection pool
            
        Returns:
            A Redis client
        """
        settings = get_settings()
        
        # Use configuration defaults if parameters are not provided
        host = host or settings.redis.host
        port = port or settings.redis.port
        db = db if db is not None else settings.redis.db
        password = password or settings.redis.password
        max_connections = kwargs.get("max_connections", settings.redis.max_connections)
        
        # Get the connection pool
        pool = cls.get_pool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            **kwargs,
        )
        
        # Update metrics
        key = cls.get_pool_key(host, port, db)
        with cls._lock:
            cls._metrics[key]["borrowed"] += 1
        
        # Create and return the client
        return redis.Redis(connection_pool=pool)
    
    @classmethod
    def get_metrics(cls) -> Dict[str, Dict[str, int]]:
        """
        Get connection pool metrics.
        
        Returns:
            A dictionary of metrics for each connection pool
        """
        with cls._lock:
            # Add current connection counts
            for key, pool in cls._pools.items():
                cls._metrics[key]["in_use"] = pool.connection_kwargs.get("_in_use_connections", 0)
                cls._metrics[key]["available"] = pool.connection_kwargs.get("_available_connections", 0)
            
            # Return a copy of the metrics
            return {k: v.copy() for k, v in cls._metrics.items()}
    
    @classmethod
    def clear_pools(cls) -> None:
        """
        Clear all connection pools.
        
        This method is useful for testing and should be used with caution in production.
        """
        with cls._lock:
            for pool in cls._pools.values():
                pool.disconnect()
            cls._pools.clear()
            cls._metrics.clear()
            logger.info("Cleared all Redis connection pools")
    
    @classmethod
    @handle_exception(logger=logger)
    def health_check(cls) -> Dict[str, bool]:
        """
        Perform a health check on all connection pools.
        
        Returns:
            A dictionary mapping pool keys to health status
        """
        results = {}
        
        with cls._lock:
            for key, pool in cls._pools.items():
                try:
                    # Get a connection from the pool
                    connection = pool.get_connection("PING")
                    
                    # Send a PING command
                    connection.send_command("PING")
                    response = connection.read_response()
                    
                    # Release the connection back to the pool
                    pool.release(connection)
                    
                    # Check the response
                    results[key] = response == b"PONG"
                except Exception as e:
                    logger.error(f"Health check failed for pool {key}: {str(e)}")
                    results[key] = False
                    cls._metrics[key]["errors"] += 1
        
        return results


class RedisClient:
    """
    High-level Redis client with automatic connection management.
    
    This class provides a convenient interface for Redis operations with
    automatic connection management and error handling.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the Redis client.
        
        Args:
            host: Redis host (optional, defaults to configuration)
            port: Redis port (optional, defaults to configuration)
            db: Redis database index (optional, defaults to configuration)
            password: Redis password (optional, defaults to configuration)
            **kwargs: Additional arguments to pass to the connection pool
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.kwargs = kwargs
        self._client: Optional[redis.Redis] = None
    
    def _get_client(self) -> redis.Redis:
        """
        Get or create a Redis client.
        
        Returns:
            A Redis client
        """
        if self._client is None:
            self._client = RedisConnectionPool.get_client(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                **self.kwargs,
            )
        return self._client
    
    @handle_exception(logger=logger)
    async def ping(self) -> bool:
        """
        Ping the Redis server.
        
        Returns:
            True if the server responded, False otherwise
        """
        client = self._get_client()
        return client.ping()
    
    @handle_exception(logger=logger)
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.
        
        Args:
            key: The key to get
            
        Returns:
            The value, or None if the key does not exist
        """
        client = self._get_client()
        return client.get(key)
    
    @handle_exception(logger=logger)
    async def set(
        self, 
        key: str, 
        value: str, 
        ex: Optional[int] = None, 
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a value in Redis.
        
        Args:
            key: The key to set
            value: The value to set
            ex: Expire time in seconds
            px: Expire time in milliseconds
            nx: Only set the key if it does not already exist
            xx: Only set the key if it already exists
            
        Returns:
            True if the value was set, False otherwise
        """
        client = self._get_client()
        return client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
    
    @handle_exception(logger=logger)
    async def delete(self, key: str) -> int:
        """
        Delete a key from Redis.
        
        Args:
            key: The key to delete
            
        Returns:
            The number of keys that were deleted
        """
        client = self._get_client()
        return client.delete(key)
    
    @handle_exception(logger=logger)
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        client = self._get_client()
        return client.exists(key) > 0
    
    @handle_exception(logger=logger)
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.
        
        Args:
            pattern: The pattern to match
            
        Returns:
            A list of matching keys
        """
        client = self._get_client()
        return client.keys(pattern)
    
    def close(self) -> None:
        """
        Close the Redis client.
        
        This method should be called when the client is no longer needed.
        """
        if self._client is not None:
            self._client.close()
            self._client = None


def get_redis_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: Optional[int] = None,
    password: Optional[str] = None,
    **kwargs: Any,
) -> RedisClient:
    """
    Get a Redis client with the specified configuration.
    
    This function is used for dependency injection in FastAPI.
    
    Args:
        host: Redis host (optional, defaults to configuration)
        port: Redis port (optional, defaults to configuration)
        db: Redis database index (optional, defaults to configuration)
        password: Redis password (optional, defaults to configuration)
        **kwargs: Additional arguments to pass to the connection pool
        
    Returns:
        A Redis client
    """
    return RedisClient(host=host, port=port, db=db, password=password, **kwargs)