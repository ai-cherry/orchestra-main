"""
Redis connection pool manager for AI Orchestra.

This module provides a connection pool manager for Redis connections,
ensuring efficient connection management and resource utilization.
"""

import asyncio
import logging
import os
import threading
from typing import Any, Dict, List, Optional

import redis

from ..config import get_settings
from ..error_handling import handle_exception

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
        ssl: bool = False,
        ssl_cert_reqs: Optional[str] = None,
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
            ssl: Whether to use SSL
            ssl_cert_reqs: SSL certificate requirements

        Returns:
            A Redis connection pool
        """
        key = cls.get_pool_key(host, port, db)

        with cls._lock:
            if key not in cls._pools:
                logger.info(f"Creating new connection pool for {key} (SSL: {ssl})")
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
                    ssl=ssl,
                    ssl_cert_reqs=ssl_cert_reqs,
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
        max_connections: Optional[int] = None,
        socket_timeout: Optional[float] = None,
        socket_keepalive: Optional[bool] = None,
        health_check_interval: Optional[int] = None,
        **kwargs: Any,
    ) -> redis.Redis:
        """
        Get a Redis client. Prioritizes DragonflyDB env vars, then direct args, then app settings.
        """
        # Attempt to use DRAGONFLY_CONNECTION_URI first
        dragonfly_uri_env = os.environ.get("DRAGONFLY_CONNECTION_URI")
        if dragonfly_uri_env:
            logger.info(f"Connecting to DragonflyDB using DRAGONFLY_CONNECTION_URI: {dragonfly_uri_env}")
            try:
                # from_url handles 'rediss://' scheme and extracts necessary components
                client = redis.Redis.from_url(dragonfly_uri_env, decode_responses=True, **kwargs)
                if client.ping():
                    logger.info("Successfully connected to DragonflyDB via URI.")
                    return client
                else:
                    logger.warning("Ping failed when connecting to DragonflyDB via URI. Falling back.")
            except redis.exceptions.RedisError as e:
                logger.warning(f"Failed to connect to DragonflyDB via URI '{dragonfly_uri_env}': {e}. Falling back.")
            # If URI connection fails, we proceed to other methods

        # Resolve parameters: Env Vars -> Direct Args -> Settings Fallback
        app_settings = get_settings()

        df_host_env = os.environ.get("DRAGONFLY_HOST")
        df_port_env_str = os.environ.get("DRAGONFLY_PORT")
        df_password_env = os.environ.get("DRAGONFLY_PASSWORD")
        df_db_index_env_str = os.environ.get("DRAGONFLY_DB_INDEX")

        final_host = df_host_env or host or app_settings.redis.host

        final_port_str = df_port_env_str or (str(port) if port is not None else None) or str(app_settings.redis.port)
        try:
            final_port = int(final_port_str)
        except (ValueError, TypeError):
            logger.error(f"Invalid port value: {final_port_str}. Defaulting to 6379.")
            final_port = 6379  # Default Redis port

        final_password = df_password_env or password or app_settings.redis.password

        final_db_index_str = df_db_index_env_str or (str(db) if db is not None else None) or str(app_settings.redis.db)
        try:
            final_db_index = int(final_db_index_str)
        except (ValueError, TypeError):
            logger.error(f"Invalid DB index value: {final_db_index_str}. Defaulting to 0.")
            final_db_index = 0

        # SSL settings determination (e.g. if host implies rediss, or from URI if we parsed it)
        # For simplicity, if DRAGONFLY_CONNECTION_URI started with 'rediss://', we assume SSL.
        # Or if the provided host/port implies it.
        use_ssl = False
        ssl_certs = None  # Typically 'CERT_REQUIRED' for rediss if not using system CAs
        if dragonfly_uri_env and dragonfly_uri_env.startswith("rediss://"):
            use_ssl = True
            # ssl_certs = 'CERT_REQUIRED' # More secure for production if not using custom CAs
        elif final_host and "dragonflydb.cloud" in final_host:  # Heuristic for managed cloud Dragonfly
            use_ssl = True  # Managed DragonflyDB often uses rediss
            # ssl_certs = 'CERT_REQUIRED'

        if df_host_env:  # Log if we are using Dragonfly specific env vars
            logger.info(
                f"Connecting to DragonflyDB using individual ENV VARS: Host={final_host}, Port={final_port}, DB={final_db_index}, SSL={use_ssl}"
            )
        elif host:  # Log if direct arguments were used
            logger.info(
                f"Connecting to Redis/DragonflyDB using direct arguments: Host={final_host}, Port={final_port}, DB={final_db_index}, SSL={use_ssl}"
            )
        else:  # Log if falling back to app settings
            logger.info(
                f"Connecting to Redis (default from settings): Host={final_host}, Port={final_port}, DB={final_db_index}, SSL={use_ssl}"
            )

        # Resolve pool-specific arguments
        final_max_connections = max_connections or app_settings.redis.max_connections
        final_socket_timeout = socket_timeout if socket_timeout is not None else app_settings.redis.socket_timeout
        final_socket_keepalive = (
            socket_keepalive if socket_keepalive is not None else app_settings.redis.socket_keepalive
        )
        final_health_check_interval = (
            health_check_interval if health_check_interval is not None else app_settings.redis.health_check_interval
        )

        pool = cls.get_pool(
            host=final_host,
            port=final_port,
            db=final_db_index,
            password=final_password,
            max_connections=final_max_connections,
            socket_timeout=final_socket_timeout,
            socket_keepalive=final_socket_keepalive,
            health_check_interval=final_health_check_interval,
            ssl=use_ssl,
            ssl_cert_reqs=ssl_certs,
            **kwargs,
        )

        key = cls.get_pool_key(final_host, final_port, final_db_index)
        with cls._lock:
            if key in cls._metrics:  # Ensure key exists
                cls._metrics[key]["borrowed"] = cls._metrics[key].get("borrowed", 0) + 1

        client = redis.Redis(connection_pool=pool)
        try:
            if client.ping():
                logger.info(f"Successfully connected to {final_host}:{final_port}/{final_db_index}.")
            else:
                # This case should ideally be caught by redis.exceptions.ConnectionError by ping
                logger.warning(
                    f"Ping failed for {final_host}:{final_port}/{final_db_index} after establishing client from pool."
                )
        except redis.exceptions.RedisError as e:
            logger.error(f"Connection test (ping) failed for {final_host}:{final_port}/{final_db_index}: {e}")
            # Depending on strictness, might raise here or return a non-functional client
            # which will fail on first actual operation. For now, let it proceed.
        return client

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
                # Safely access connection stats with proper fallbacks
                if hasattr(pool, "connection_kwargs") and isinstance(pool.connection_kwargs, dict):
                    cls._metrics[key]["in_use"] = pool.connection_kwargs.get("_in_use_connections", 0)
                    cls._metrics[key]["available"] = pool.connection_kwargs.get("_available_connections", 0)
                else:
                    # Fallback for newer Redis client versions with different attribute names
                    cls._metrics[key]["in_use"] = getattr(pool, "_in_use_connections", 0)
                    cls._metrics[key]["available"] = getattr(pool, "_available_connections", 0)

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
                try:
                    pool.disconnect(inuse_connections=True)
                except Exception as e:
                    logger.warning(f"Error disconnecting pool during clear_pools: {e}")
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
        connection_uri: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the Redis client.

        Args:
            host: Redis host (optional, defaults to configuration)
            port: Redis port (optional, defaults to configuration)
            db: Redis database index (optional, defaults to configuration)
            password: Redis password (optional, defaults to configuration)
            connection_uri: Redis connection URI (optional, defaults to configuration)
            **kwargs: Additional arguments to pass to the connection pool
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.connection_uri = connection_uri
        self.kwargs = kwargs
        self._client: Optional[redis.Redis] = None
        # Attempt to initialize client immediately to catch config errors early
        try:
            self._get_client()
            logger.info(
                f"RedisClient initialized. Target: {self._client.connection_pool.connection_kwargs.get('host')}:{self._client.connection_pool.connection_kwargs.get('port')}/{self._client.connection_pool.connection_kwargs.get('db')}"
            )
        except Exception as e:
            logger.error(f"RedisClient failed to initialize connection: {e}", exc_info=True)
            # self._client will remain None, operations will fail until successfully re-attempted or re-configured.

    def _get_client(self) -> redis.Redis:
        """
        Get or create a Redis client.

        Returns:
            A Redis client
        """
        if self._client is None or not self._is_connected():
            # Pass original constructor args; get_client will prioritize ENV and then these args
            self._client = RedisConnectionPool.get_client(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                # Pass through other kwargs like max_connections from constructor
                **self.kwargs,
            )
        return self._client

    def _is_connected(self) -> bool:
        if self._client is None:
            return False
        try:
            return self._client.ping()
        except redis.exceptions.ConnectionError:
            return False
        except Exception as e:  # Catch other potential issues during ping
            logger.warning(f"Ping check encountered an unexpected error: {e}")
            return False

    @handle_exception(logger=logger)
    async def ping(self) -> bool:
        """
        Ping the Redis server.

        Returns:
            True if the server responded, False otherwise
        """
        client = self._get_client()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, client.ping)

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, client.get, key)

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
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: client.set(key, value, ex=ex, px=px, nx=nx, xx=xx))

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
        loop = asyncio.get_event_loop()
        # client.delete returns an int, ensure wrapper handles bool vs int if interface expects bool
        result = await loop.run_in_executor(None, client.delete, key)
        return result  # type: ignore

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
        loop = asyncio.get_event_loop()
        # client.exists returns int (number of keys existing)
        num_existing = await loop.run_in_executor(None, client.exists, key)
        return num_existing > 0

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
        loop = asyncio.get_event_loop()
        # client.keys returns List[bytes], decode if necessary (decode_responses=True in pool handles this)
        key_list_bytes = await loop.run_in_executor(None, client.keys, pattern)
        return key_list_bytes  # type: ignore

    def close(self) -> None:
        """
        Close the Redis client.

        This method should be called when the client is no longer needed.
        """
        if self._client is not None:
            # For clients from a pool, close() is a no-op or may release the connection.
            # The pool itself should be disconnected for full cleanup via RedisConnectionPool.clear_pools()
            logger.debug("RedisClient.close() called. Connection is managed by the pool.")
            # self._client.close() # This is often a no-op for pooled connections
            self._client = None


def get_redis_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: Optional[int] = None,
    password: Optional[str] = None,
    connection_uri: Optional[str] = None,
    **kwargs: Any,
) -> RedisClient:
    """
    Get a Redis client, prioritizing DragonflyDB ENV VARS for configuration.
    """
    # The RedisClient constructor now handles the logic of prioritizing ENV VARS
    return RedisClient(host=host, port=port, db=db, password=password, connection_uri=connection_uri, **kwargs)
