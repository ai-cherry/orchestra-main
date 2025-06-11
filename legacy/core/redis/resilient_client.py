#!/usr/bin/env python3
"""
Resilient Redis Client with Circuit Breaker, Connection Pooling, and Fallback
"""

import os
import json
import time
import asyncio
import logging
from typing import Optional, Any, Dict, List, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum
import redis
from redis import ConnectionPool, Redis
from redis.asyncio import Redis as AsyncRedis, ConnectionPool as AsyncConnectionPool
from redis.sentinel import Sentinel
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import aioredis

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ConnectionError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise ConnectionError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ResilientRedisClient:
    """Resilient Redis client with connection pooling and circuit breaker"""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        circuit_breaker_config: Optional[Dict] = None,
        fallback_handler: Optional[Callable] = None,
        sentinel_hosts: Optional[List[tuple]] = None,
        sentinel_service_name: Optional[str] = None
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        self.fallback_handler = fallback_handler
        self.sentinel_hosts = sentinel_hosts
        self.sentinel_service_name = sentinel_service_name
        
        # Circuit breaker setup
        cb_config = circuit_breaker_config or {}
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get("failure_threshold", 5),
            recovery_timeout=cb_config.get("recovery_timeout", 60),
            expected_exception=RedisError
        )
        
        # Connection pool setup
        self._pool = None
        self._client = None
        self._sentinel = None
        self._last_health_check = None
        self._is_connected = False
        
        # Metrics
        self.metrics = {
            "connections_created": 0,
            "connections_failed": 0,
            "commands_executed": 0,
            "commands_failed": 0,
            "circuit_breaker_trips": 0,
            "fallback_used": 0
        }
        
    def _create_connection_pool(self) -> ConnectionPool:
        """Create connection pool with proper configuration"""
        pool_kwargs = {
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "socket_keepalive": True,
            "socket_keepalive_options": {},
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
        }
        
        if self.sentinel_hosts:
            # Use Redis Sentinel for HA
            self._sentinel = Sentinel(
                self.sentinel_hosts,
                socket_timeout=self.socket_timeout
            )
            master = self._sentinel.master_for(
                self.sentinel_service_name,
                **pool_kwargs
            )
            return master.connection_pool
        else:
            # Standard connection pool
            return redis.ConnectionPool.from_url(
                self.redis_url,
                **pool_kwargs
            )
    
    def _get_client(self) -> Redis:
        """Get Redis client with lazy initialization"""
        if not self._pool:
            self._pool = self._create_connection_pool()
            
        if not self._client:
            self._client = Redis(connection_pool=self._pool)
            self.metrics["connections_created"] += 1
            
        return self._client
    
    def _execute_with_fallback(self, operation: str, func: Callable, *args, **kwargs) -> Any:
        """Execute operation with circuit breaker and fallback"""
        try:
            result = self.circuit_breaker.call(func, *args, **kwargs)
            self.metrics["commands_executed"] += 1
            return result
        except Exception as e:
            self.metrics["commands_failed"] += 1
            logger.error(f"Redis operation '{operation}' failed: {e}")
            
            if self.circuit_breaker.state == CircuitState.OPEN:
                self.metrics["circuit_breaker_trips"] += 1
                
            if self.fallback_handler:
                self.metrics["fallback_used"] += 1
                return self.fallback_handler(operation, *args, **kwargs)
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with fallback support"""
        def _get():
            client = self._get_client()
            value = client.get(key)
            return value.decode('utf-8') if value else default
            
        return self._execute_with_fallback("get", _get)
    
    def set(self, key: str, value: Any, ex: Optional[int] = None, px: Optional[int] = None) -> bool:
        """Set value with fallback support"""
        def _set():
            client = self._get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return client.set(key, value, ex=ex, px=px)
            
        return self._execute_with_fallback("set", _set)
    
    def delete(self, *keys: str) -> int:
        """Delete keys with fallback support"""
        def _delete():
            client = self._get_client()
            return client.delete(*keys)
            
        return self._execute_with_fallback("delete", _delete)
    
    def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        def _exists():
            client = self._get_client()
            return client.exists(*keys)
            
        return self._execute_with_fallback("exists", _exists)
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration"""
        def _expire():
            client = self._get_client()
            return client.expire(key, seconds)
            
        return self._execute_with_fallback("expire", _expire)
    
    def ping(self) -> bool:
        """Health check"""
        try:
            client = self._get_client()
            return client.ping()
        except Exception:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        metrics = self.metrics.copy()
        metrics["circuit_breaker_state"] = self.circuit_breaker.state.value
        metrics["is_connected"] = self.ping()
        
        if self._pool:
            metrics["pool_connections_created"] = self._pool.connection_kwargs.get("max_connections", 0)
            
        return metrics
    
    def close(self):
        """Close connections and cleanup"""
        if self._client:
            self._client.close()
        if self._pool:
            self._pool.disconnect()
        self._client = None
        self._pool = None


class AsyncResilientRedisClient:
    """Async version of resilient Redis client"""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 50,
        **kwargs
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.max_connections = max_connections
        self.kwargs = kwargs
        self._pool = None
        self._client = None
        
        # Circuit breaker
        cb_config = kwargs.get("circuit_breaker_config", {})
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get("failure_threshold", 5),
            recovery_timeout=cb_config.get("recovery_timeout", 60),
            expected_exception=RedisError
        )
        
    async def _get_client(self) -> AsyncRedis:
        """Get async Redis client"""
        if not self._pool:
            self._pool = await aioredis.create_redis_pool(
                self.redis_url,
                maxsize=self.max_connections,
                **self.kwargs
            )
        return self._pool
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Async get with circuit breaker"""
        async def _get():
            client = await self._get_client()
            value = await client.get(key)
            return value.decode('utf-8') if value else default
            
        return await self.circuit_breaker.async_call(_get)
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Async set with circuit breaker"""
        async def _set():
            client = await self._get_client()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return await client.set(key, value, expire=expire)
            
        return await self.circuit_breaker.async_call(_set)
    
    async def close(self):
        """Close async connections"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()


# Fallback handlers for graceful degradation
class InMemoryFallback:
    """In-memory fallback when Redis is unavailable"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl
        
    def __call__(self, operation: str, *args, **kwargs) -> Any:
        """Handle fallback operations"""
        if operation == "get":
            return self._get(args[0])
        elif operation == "set":
            return self._set(args[0], args[1], kwargs.get("ex", self.ttl))
        elif operation == "delete":
            return self._delete(*args)
        elif operation == "exists":
            return self._exists(*args)
        else:
            logger.warning(f"Fallback: Operation '{operation}' not supported")
            return None
    
    def _get(self, key: str) -> Any:
        """Get from in-memory cache"""
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def _set(self, key: str, value: Any, ttl: int) -> bool:
        """Set in in-memory cache with LRU eviction"""
        if len(self.cache) >= self.max_size:
            # Evict oldest entry
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
            
        self.cache[key] = value
        self.timestamps[key] = time.time()
        return True
    
    def _delete(self, *keys: str) -> int:
        """Delete from in-memory cache"""
        count = 0
        for key in keys:
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
                count += 1
        return count
    
    def _exists(self, *keys: str) -> int:
        """Check existence in in-memory cache"""
        count = 0
        for key in keys:
            if key in self.cache and time.time() - self.timestamps[key] < self.ttl:
                count += 1
        return count


# Decorator for automatic Redis caching with fallback
def redis_cache(
    key_prefix: str,
    ttl: int = 300,
    fallback: bool = True
):
    """Decorator for Redis caching with automatic fallback"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            try:
                redis_client = get_redis_client()
                cached = redis_client.get(cache_key)
                if cached:
                    return json.loads(cached) if isinstance(cached, str) else cached
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")
                
            # Execute function
            result = func(*args, **kwargs)
            
            # Try to cache result
            try:
                redis_client = get_redis_client()
                redis_client.set(cache_key, json.dumps(result) if not isinstance(result, str) else result, ex=ttl)
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")
                
            return result
            
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            try:
                redis_client = get_async_redis_client()
                cached = await redis_client.get(cache_key)
                if cached:
                    return json.loads(cached) if isinstance(cached, str) else cached
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")
                
            # Execute function
            result = await func(*args, **kwargs)
            
            # Try to cache result
            try:
                redis_client = get_async_redis_client()
                await redis_client.set(cache_key, json.dumps(result) if not isinstance(result, str) else result, expire=ttl)
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")
                
            return result
            
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
    return decorator


# Global client instances
_redis_client = None
_async_redis_client = None


def get_redis_client(fallback_handler: Optional[Callable] = None) -> ResilientRedisClient:
    """Get or create global Redis client"""
    global _redis_client
    if not _redis_client:
        _redis_client = ResilientRedisClient(
            fallback_handler=fallback_handler or InMemoryFallback()
        )
    return _redis_client


def get_async_redis_client() -> AsyncResilientRedisClient:
    """Get or create global async Redis client"""
    global _async_redis_client
    if not _async_redis_client:
        _async_redis_client = AsyncResilientRedisClient()
    return _async_redis_client


# Health check endpoint helper
async def redis_health_check() -> Dict[str, Any]:
    """Comprehensive Redis health check"""
    client = get_redis_client()
    
    health = {
        "status": "unknown",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": client.get_metrics(),
        "checks": {}
    }
    
    try:
        # Basic connectivity
        health["checks"]["ping"] = client.ping()
        
        # Write test
        test_key = f"health_check:{int(time.time())}"
        health["checks"]["write"] = client.set(test_key, "test", ex=10)
        
        # Read test
        health["checks"]["read"] = client.get(test_key) == "test"
        
        # Delete test
        health["checks"]["delete"] = client.delete(test_key) > 0
        
        # Overall status
        all_passed = all(health["checks"].values())
        health["status"] = "healthy" if all_passed else "degraded"
        
    except Exception as e:
        health["status"] = "unhealthy"
        health["error"] = str(e)
        
    return health