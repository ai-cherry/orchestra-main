"""
Optimized Redis connection pool for AI Orchestra.

This module provides an enhanced connection pool manager for Redis connections,
implementing connection pool partitioning, pipelining operations, and adaptive
connection limits for improved performance.
"""

import logging
import threading
import time
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
)

import redis.asyncio
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.client import Pipeline

from ....core.config import get_settings
from ....core.errors import handle_exception
from ....utils.logging import log_event

logger = logging.getLogger(__name__)
T = TypeVar("T")


class PoolType(Enum):
    """Redis connection pool types for different workload patterns."""

    DEFAULT = "default"  # For general purpose operations
    READ_HEAVY = "read_heavy"  # For read-intensive workloads
    WRITE_HEAVY = "write_heavy"  # For write-intensive workloads
    ANALYTICS = "analytics"  # For long-running analytical queries
    CACHE = "cache"  # For caching operations with short TTLs


class EnhancedRedisConnectionPool:
    """
    Enhanced Redis connection pool with workload-specific partitioning.

    This class provides a thread-safe singleton for managing multiple Redis connection pools
    optimized for different workload types, implementing connection pool partitioning,
    circuit breaking, and performance monitoring.
    """

    # Connection pools organized by type and connection parameters
    _pools: Dict[str, Dict[str, ConnectionPool]] = {
        PoolType.DEFAULT.value: {},
        PoolType.READ_HEAVY.value: {},
        PoolType.WRITE_HEAVY.value: {},
        PoolType.ANALYTICS.value: {},
        PoolType.CACHE.value: {},
    }

    # Thread-safe access to pools
    _lock = threading.RLock()

    # Connection usage and performance metrics
    _metrics: Dict[str, Dict[str, Dict[str, Any]]] = {pool_type.value: {} for pool_type in PoolType}

    # Circuit breaker state
    _circuit_breakers: Dict[str, Dict[str, Any]] = {}

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
        pool_type: PoolType = PoolType.DEFAULT,
        max_connections: int = 50,
        socket_timeout: float = 5.0,
        socket_keepalive: bool = True,
        health_check_interval: int = 30,
    ) -> ConnectionPool:
        """
        Get or create a connection pool for the given Redis configuration.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database index
            password: Redis password
            pool_type: Type of pool to use based on workload characteristics
            max_connections: Maximum connections in the pool
            socket_timeout: Socket timeout in seconds
            socket_keepalive: Whether to keep connections alive
            health_check_interval: Health check interval in seconds

        Returns:
            A Redis connection pool
        """
        key = cls.get_pool_key(host, port, db)
        pool_dict = cls._pools[pool_type.value]

        with cls._lock:
            # Adjust max connections based on pool type
            adjusted_max_connections = cls._get_adjusted_max_connections(pool_type, max_connections)

            if key not in pool_dict:
                pool_dict[key] = ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    max_connections=adjusted_max_connections,
                    socket_timeout=socket_timeout,
                    socket_keepalive=socket_keepalive,
                    health_check_interval=health_check_interval,
                    decode_responses=True,
                )

                # Initialize metrics for this pool
                if key not in cls._metrics[pool_type.value]:
                    cls._metrics[pool_type.value][key] = {
                        "created": time.time(),
                        "operations": 0,
                        "errors": 0,
                        "latency_sum": 0.0,
                        "latency_count": 0,
                        "last_operation": time.time(),
                    }

                # Initialize circuit breaker
                cls._circuit_breakers[key] = {
                    "failures": 0,
                    "threshold": 5,  # After 5 failures, circuit breaks
                    "open": False,
                    "last_checked": time.time(),
                    "reset_timeout": 30,  # Seconds until circuit reset attempt
                }

                logger.info(
                    f"Created new {pool_type.value} Redis connection pool for {host}:{port}/{db} "
                    f"with max connections: {adjusted_max_connections}"
                )

            # Check circuit breaker state
            circuit = cls._circuit_breakers[key]
            if circuit["open"]:
                current_time = time.time()
                # Check if it's time to try resetting the circuit
                if current_time - circuit["last_checked"] > circuit["reset_timeout"]:
                    logger.info(f"Attempting to reset circuit breaker for {key}")
                    circuit["open"] = False
                    circuit["failures"] = 0
                    circuit["last_checked"] = current_time
                else:
                    logger.warning(f"Circuit open for {key}, using fallback mechanism")
                    raise redis.exceptions.ConnectionError(f"Circuit breaker open for {key}")

            return pool_dict[key]

    @classmethod
    def _get_adjusted_max_connections(cls, pool_type: PoolType, base_max_connections: int) -> int:
        """
        Calculate adjusted max connections based on pool type.

        Different workloads need different connection pool sizes.

        Args:
            pool_type: Type of pool being configured
            base_max_connections: Base maximum connections specified

        Returns:
            Adjusted maximum connections
        """
        if pool_type == PoolType.READ_HEAVY:
            # Read-heavy workloads benefit from more connections
            return max(base_max_connections, 100)
        elif pool_type == PoolType.WRITE_HEAVY:
            # Write-heavy workloads need controlled concurrency
            return min(base_max_connections, 30)
        elif pool_type == PoolType.ANALYTICS:
            # Analytics queries are long-running, limit connections
            return max(int(base_max_connections * 0.3), 10)
        elif pool_type == PoolType.CACHE:
            # Cache operations are frequent but short
            return max(base_max_connections, 150)
        else:
            # Default pool
            return base_max_connections

    @classmethod
    def record_operation(cls, pool_type: PoolType, key: str, success: bool, latency: float) -> None:
        """
        Record operation metrics for a connection pool.

        Args:
            pool_type: Type of pool used
            key: The pool key
            success: Whether the operation was successful
            latency: Operation latency in seconds
        """
        with cls._lock:
            if key in cls._metrics[pool_type.value]:
                metrics = cls._metrics[pool_type.value][key]
                metrics["operations"] += 1
                metrics["last_operation"] = time.time()
                metrics["latency_sum"] += latency
                metrics["latency_count"] += 1

                if not success:
                    metrics["errors"] += 1

                    # Update circuit breaker
                    if key in cls._circuit_breakers:
                        circuit = cls._circuit_breakers[key]
                        circuit["failures"] += 1
                        if circuit["failures"] >= circuit["threshold"]:
                            logger.warning(f"Circuit breaker tripped for {key}")
                            circuit["open"] = True
                            circuit["last_checked"] = time.time()

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """
        Get comprehensive connection pool metrics.

        Returns:
            A dictionary of metrics for all connection pools
        """
        with cls._lock:
            result = {
                "pools": {},
                "circuits": {},
                "summary": {
                    "total_pools": 0,
                    "total_operations": 0,
                    "error_rate": 0.0,
                    "avg_latency": 0.0,
                },
            }

            total_ops = 0
            total_errors = 0
            latency_sum = 0.0
            latency_count = 0

            # Collect metrics from all pools
            for pool_type, pools in cls._metrics.items():
                result["pools"][pool_type] = {}

                for key, metrics in pools.items():
                    result["pools"][pool_type][key] = {
                        "operations": metrics["operations"],
                        "errors": metrics["errors"],
                        "avg_latency": (
                            (metrics["latency_sum"] / metrics["latency_count"]) if metrics["latency_count"] > 0 else 0
                        ),
                        "error_rate": (
                            (metrics["errors"] / metrics["operations"] * 100) if metrics["operations"] > 0 else 0
                        ),
                        "age_seconds": time.time() - metrics["created"],
                        "idle_seconds": time.time() - metrics["last_operation"],
                    }

                    total_ops += metrics["operations"]
                    total_errors += metrics["errors"]
                    latency_sum += metrics["latency_sum"]
                    latency_count += metrics["latency_count"]

            # Add circuit breaker states
            for key, circuit in cls._circuit_breakers.items():
                result["circuits"][key] = {
                    "state": "open" if circuit["open"] else "closed",
                    "failures": circuit["failures"],
                    "seconds_since_check": time.time() - circuit["last_checked"],
                }

            # Calculate summary
            result["summary"]["total_pools"] = sum(len(pools) for pools in cls._metrics.values())
            result["summary"]["total_operations"] = total_ops
            result["summary"]["error_rate"] = (total_errors / total_ops * 100) if total_ops > 0 else 0
            result["summary"]["avg_latency"] = (latency_sum / latency_count) if latency_count > 0 else 0

            return result

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """
        Perform a health check on all connection pools.

        Returns:
            A dictionary with health status information
        """
        results = {"healthy_pools": 0, "unhealthy_pools": 0, "details": {}}

        for pool_type, pools in cls._pools.items():
            results["details"][pool_type] = {}

            for key, pool in pools.items():
                try:
                    # Create a connection and send PING
                    redis_client = Redis(connection_pool=pool)
                    response = await redis_client.ping()

                    # Record result
                    is_healthy = response is True
                    results["details"][pool_type][key] = {
                        "healthy": is_healthy,
                        "response": str(response),
                        "latency_ms": 0,  # Will be filled in later
                    }

                    # Measure latency
                    start_time = time.time()
                    await redis_client.ping()
                    latency_ms = (time.time() - start_time) * 1000
                    results["details"][pool_type][key]["latency_ms"] = latency_ms

                    if is_healthy:
                        results["healthy_pools"] += 1
                    else:
                        results["unhealthy_pools"] += 1

                except Exception as e:
                    logger.error(f"Health check failed for pool {key}: {str(e)}")
                    results["details"][pool_type][key] = {
                        "healthy": False,
                        "error": str(e),
                    }
                    results["unhealthy_pools"] += 1

        return results

    @classmethod
    async def clear_pools(cls) -> None:
        """
        Clear all connection pools.

        This method is useful for testing and should be used with caution in production.
        """
        for pool_type, pools in cls._pools.items():
            for key, pool in pools.items():
                try:
                    await pool.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting pool {key}: {str(e)}")

        with cls._lock:
            for pool_type in cls._pools:
                cls._pools[pool_type] = {}

            for pool_type in cls._metrics:
                cls._metrics[pool_type] = {}

            cls._circuit_breakers.clear()

        logger.info("Cleared all Redis connection pools")


class OptimizedRedisClient:
    """
    High-performance Redis client with automatic connection management.

    This class provides an efficient interface for Redis operations with
    automatic connection management, pipelining, and error handling.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        pool_type: PoolType = PoolType.DEFAULT,
        **kwargs: Any,
    ):
        """
        Initialize the optimized Redis client.

        Args:
            host: Redis host (optional, defaults to configuration)
            port: Redis port (optional, defaults to configuration)
            db: Redis database index (optional, defaults to configuration)
            password: Redis password (optional, defaults to configuration)
            pool_type: Type of connection pool to use based on workload patterns
            **kwargs: Additional arguments to pass to the connection pool
        """
        settings = get_settings()

        self.host = host or settings.redis.host
        self.port = port or settings.redis.port
        self.db = db if db is not None else settings.redis.db
        self.password = password or settings.redis.password
        self.pool_type = pool_type
        self.kwargs = kwargs
        self._client: Optional[Redis] = None

        # Performance metrics
        self._operation_count = 0
        self._pipeline_operation_count = 0
        self._error_count = 0
        self._last_operation_time = 0.0

        log_event(
            logger,
            "redis",
            "client_created",
            {
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "pool_type": pool_type.value,
            },
        )

    async def get_client(self) -> Redis:
        """
        Get or create a Redis client.

        Returns:
            An async Redis client
        """
        if self._client is None:
            pool = EnhancedRedisConnectionPool.get_pool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                pool_type=self.pool_type,
                **self.kwargs,
            )
            self._client = Redis(connection_pool=pool)

        return self._client

    @handle_exception(logger=logger)
    async def ping(self) -> bool:
        """
        Ping the Redis server.

        Returns:
            True if the server responded, False otherwise
        """
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.ping()
            success = result is True
            return success
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    @handle_exception(logger=logger)
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis.

        Args:
            key: The key to get

        Returns:
            The value, or None if the key does not exist
        """
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.get(key)
            success = True
            return result
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

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
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            success = result is not None
            return success
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    @handle_exception(logger=logger)
    async def pipeline_execute(self, operations: List[Callable[[Pipeline], None]]) -> List[Any]:
        """
        Execute multiple operations in a pipeline.

        This method significantly improves performance when executing multiple Redis
        operations by reducing network round-trips.

        Args:
            operations: List of callables that add operations to the pipeline

        Returns:
            List of results from the pipeline execution
        """
        if not operations:
            return []

        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            pipe = client.pipeline()

            # Add all operations to the pipeline
            for op in operations:
                op(pipe)

            # Execute the pipeline
            results = await pipe.execute()
            success = True
            self._pipeline_operation_count += len(operations)
            return results
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1  # Count as one operation with multiple commands

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    async def batch_get(self, keys: List[str]) -> Dict[str, Optional[str]]:
        """
        Get multiple values in a single operation.

        Args:
            keys: List of keys to get

        Returns:
            Dictionary mapping keys to values (or None if not found)
        """
        if not keys:
            return {}

        # For a single key, use the regular get method
        if len(keys) == 1:
            value = await self.get(keys[0])
            return {keys[0]: value}

        # Create pipeline operations
        results = await self.pipeline_execute([lambda pipe: pipe.get(key) for key in keys])

        # Map keys to results
        return dict(zip(keys, results))

    async def batch_set(self, key_values: Dict[str, str], ttl_seconds: Optional[int] = None) -> bool:
        """
        Set multiple key-value pairs in a single operation.

        Args:
            key_values: Dictionary of key-value pairs to set
            ttl_seconds: Optional TTL in seconds to apply to all keys

        Returns:
            True if all values were set successfully
        """
        if not key_values:
            return True

        # For a single key-value pair, use the regular set method
        if len(key_values) == 1:
            key, value = next(iter(key_values.items()))
            return await self.set(key, value, ex=ttl_seconds)

        # Create pipeline operations
        if ttl_seconds is not None:
            # Need to use set with ex for each key
            ops = [lambda pipe, k=k, v=v: pipe.set(k, v, ex=ttl_seconds) for k, v in key_values.items()]
        else:
            # Can use mset for better performance when no TTL
            ops = [lambda pipe: pipe.mset(key_values)]

        results = await self.pipeline_execute(ops)

        # Check if all operations succeeded
        return all(result for result in results)

    @handle_exception(logger=logger)
    async def delete(self, key: str) -> int:
        """
        Delete a key from Redis.

        Args:
            key: The key to delete

        Returns:
            The number of keys that were deleted
        """
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.delete(key)
            success = True
            return result
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    async def batch_delete(self, keys: List[str]) -> int:
        """
        Delete multiple keys in a single operation.

        Args:
            keys: List of keys to delete

        Returns:
            Number of keys that were deleted
        """
        if not keys:
            return 0

        # For a single key, use the regular delete method
        if len(keys) == 1:
            return await self.delete(keys[0])

        # Use unlink for better performance on large deletions
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.unlink(*keys)
            success = True
            return result
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    @handle_exception(logger=logger)
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.exists(key)
            success = True
            return bool(result)
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    @handle_exception(logger=logger)
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.

        NOTE: This operation can be expensive in production Redis instances.
        Consider using SCAN for large databases.

        Args:
            pattern: The pattern to match

        Returns:
            A list of matching keys
        """
        start_time = time.time()
        success = False

        try:
            client = await self.get_client()
            result = await client.keys(pattern)
            success = True
            return result
        finally:
            latency = time.time() - start_time
            self._last_operation_time = latency
            self._operation_count += 1

            if not success:
                self._error_count += 1

            EnhancedRedisConnectionPool.record_operation(
                self.pool_type,
                EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db),
                success,
                latency,
            )

    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this client.

        Returns:
            Dictionary with performance metrics
        """
        # Get pool metrics
        pool_key = EnhancedRedisConnectionPool.get_pool_key(self.host, self.port, self.db)
        all_metrics = EnhancedRedisConnectionPool.get_metrics()

        pool_metrics = {}
        circuit_state = "unknown"

        if self.pool_type.value in all_metrics["pools"]:
            if pool_key in all_metrics["pools"][self.pool_type.value]:
                pool_metrics = all_metrics["pools"][self.pool_type.value][pool_key]

        if pool_key in all_metrics["circuits"]:
            circuit_state = all_metrics["circuits"][pool_key]["state"]

        # Calculate client error rate
        error_rate = 0.0
        if self._operation_count > 0:
            error_rate = (self._error_count / self._operation_count) * 100

        return {
            "client": {
                "operations_count": self._operation_count,
                "pipeline_operations_count": self._pipeline_operation_count,
                "error_count": self._error_count,
                "error_rate": error_rate,
                "last_operation_time_ms": self._last_operation_time * 1000,
            },
            "pool": pool_metrics,
            "circuit_breaker": circuit_state,
            "pool_type": self.pool_type.value,
            "host": self.host,
            "port": self.port,
            "db": self.db,
        }

    async def close(self) -> None:
        """
        Close the Redis client.

        This method should be called when the client is no longer needed.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None

            log_event(
                logger,
                "redis",
                "client_closed",
                {
                    "host": self.host,
                    "port": self.port,
                    "db": self.db,
                    "operations": self._operation_count,
                    "pipeline_operations": self._pipeline_operation_count,
                    "errors": self._error_count,
                },
            )


async def get_optimized_redis_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: Optional[int] = None,
    password: Optional[str] = None,
    pool_type: PoolType = PoolType.DEFAULT,
    **kwargs: Any,
) -> OptimizedRedisClient:
    """
    Get an optimized Redis client with the specified configuration.

    This function is used for dependency injection in FastAPI.

    Args:
        host: Redis host (optional, defaults to configuration)
        port: Redis port (optional, defaults to configuration)
        db: Redis database index (optional, defaults to configuration)
        password: Redis password (optional, defaults to configuration)
        pool_type: Type of pool to use based on workload characteristics
        **kwargs: Additional arguments to pass to the connection pool

    Returns:
        An optimized Redis client
    """
    client = OptimizedRedisClient(host=host, port=port, db=db, password=password, pool_type=pool_type, **kwargs)

    # Test connection
    await client.ping()

    return client
