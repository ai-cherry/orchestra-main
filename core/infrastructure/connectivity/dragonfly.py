"""
DragonflyDB (Redis-compatible) connection implementation.

This module provides DragonflyDB connectivity with health checks and retries.
"""

import asyncio
import time
from typing import Any, Dict, Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from .base import RetryableConnection, ServiceHealth, ServiceStatus

class DragonflyConnection(RetryableConnection):
    """DragonflyDB connection with health checks and retries."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.client: Optional[redis.Redis] = None

        # Extract config
        self.connection_string = config.get("connection_string", config.get("uri"))
        self.decode_responses = config.get("decode_responses", True)
        self.socket_timeout = config.get("socket_timeout", 5)
        self.socket_connect_timeout = config.get("socket_connect_timeout", 5)
        self.max_connections = config.get("max_connections", 50)

    async def connect(self) -> None:
        """Establish connection to DragonflyDB."""
        try:
            # Parse connection string or use individual params
            if self.connection_string:
                self.client = redis.from_url(
                    self.connection_string,
                    decode_responses=self.decode_responses,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_connect_timeout,
                    max_connections=self.max_connections,
                )
            else:
                # Fall back to individual parameters
                self.client = redis.Redis(
                    host=self.config.get("host", "localhost"),
                    port=self.config.get("port", 6379),
                    password=self.config.get("password"),
                    db=self.config.get("db", 0),
                    decode_responses=self.decode_responses,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_connect_timeout,
                    max_connections=self.max_connections,
                )

            # Test the connection
            await self.client.ping()

            self._status = ServiceStatus.HEALTHY

        except Exception as e:
            self._status = ServiceStatus.UNHEALTHY
            raise ConnectionError(f"Failed to connect to DragonflyDB: {e}")

    async def disconnect(self) -> None:
        """Close DragonflyDB connection."""
        if self.client:
            await self.client.close()
            self.client = None
            self._status = ServiceStatus.UNKNOWN

    async def health_check(self) -> ServiceHealth:
        """Perform health check on DragonflyDB."""
        if not self.client:
            return ServiceHealth(status=ServiceStatus.UNHEALTHY, error="Client not initialized")

        try:
            start_time = time.time()

            # Ping the server
            pong = await self.client.ping()

            latency_ms = (time.time() - start_time) * 1000

            # Get server info
            info = await self.client.info()

            # Extract key metrics
            used_memory = info.get("used_memory_human", "unknown")
            connected_clients = info.get("connected_clients", 0)

            return ServiceHealth(
                status=ServiceStatus.HEALTHY,
                latency_ms=latency_ms,
                metadata={
                    "ping": pong,
                    "used_memory": used_memory,
                    "connected_clients": connected_clients,
                    "version": info.get("redis_version", "unknown"),
                },
            )

        except TimeoutError:
            return ServiceHealth(status=ServiceStatus.UNHEALTHY, error="Connection timeout")
        except Exception as e:
            return ServiceHealth(status=ServiceStatus.UNHEALTHY, error=str(e))

    async def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute a Redis/DragonflyDB operation."""
        if not self.client:
            raise ConnectionError("Client not connected")

        # Map operations to Redis methods
        operations = {
            # String operations
            "get": self.client.get,
            "set": self.client.set,
            "mget": self.client.mget,
            "mset": self.client.mset,
            "delete": self.client.delete,
            "exists": self.client.exists,
            "expire": self.client.expire,
            "ttl": self.client.ttl,
            # Hash operations
            "hget": self.client.hget,
            "hset": self.client.hset,
            "hmget": self.client.hmget,
            "hmset": self.client.hmset,
            "hgetall": self.client.hgetall,
            "hdel": self.client.hdel,
            "hexists": self.client.hexists,
            # List operations
            "lpush": self.client.lpush,
            "rpush": self.client.rpush,
            "lpop": self.client.lpop,
            "rpop": self.client.rpop,
            "lrange": self.client.lrange,
            "llen": self.client.llen,
            # Set operations
            "sadd": self.client.sadd,
            "srem": self.client.srem,
            "smembers": self.client.smembers,
            "sismember": self.client.sismember,
            "scard": self.client.scard,
            # Sorted set operations
            "zadd": self.client.zadd,
            "zrem": self.client.zrem,
            "zrange": self.client.zrange,
            "zrevrange": self.client.zrevrange,
            "zscore": self.client.zscore,
            "zcard": self.client.zcard,
            # Pub/Sub operations
            "publish": self.client.publish,
            "subscribe": self._subscribe,
            "unsubscribe": self._unsubscribe,
            # Transaction operations
            "pipeline": self._pipeline,
            # Utility operations
            "ping": self.client.ping,
            "flushdb": self.client.flushdb,
            "dbsize": self.client.dbsize,
            "keys": self.client.keys,
        }

        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")

        return await operations[operation](*args, **kwargs)

    async def _subscribe(self, *channels: str) -> redis.PubSub:
        """Subscribe to channels."""
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    async def _unsubscribe(self, pubsub: redis.PubSub, *channels: str) -> None:
        """Unsubscribe from channels."""
        await pubsub.unsubscribe(*channels)
        await pubsub.close()

    async def _pipeline(self, transaction: bool = True) -> redis.Pipeline:
        """Create a pipeline for batch operations."""
        return self.client.pipeline(transaction=transaction)

    # Convenience methods for common patterns

    async def get_json(self, key: str) -> Optional[Dict]:
        """Get and decode JSON value."""
        import json

        value = await self.client.get(key)
        return json.loads(value) if value else None

    async def set_json(self, key: str, value: Dict, ex: Optional[int] = None) -> bool:
        """Encode and set JSON value."""
        import json

        return await self.client.set(key, json.dumps(value), ex=ex)

    async def cache_get_or_set(self, key: str, factory: callable, ttl: int = 3600) -> Any:
        """Get from cache or compute and set."""
        value = await self.client.get(key)
        if value is not None:
            return value

        # Compute value
        value = await factory() if asyncio.iscoroutinefunction(factory) else factory()

        # Cache it
        await self.client.set(key, value, ex=ttl)

        return value
