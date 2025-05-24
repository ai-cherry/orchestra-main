#!/usr/bin/env python3
"""
Performance wrapper for MCP servers
Adds caching, connection pooling, and optimization
"""

import asyncio
import functools
import logging
import os
import time
from typing import Any, Callable, Optional

import aioredis
import uvloop
import yaml
from aiocache import Cache
from aiocache.serializers import PickleSerializer
from prometheus_client import Counter, Gauge, Histogram

# Use uvloop for better async performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load performance configuration
with open(os.path.join(os.path.dirname(__file__), "config/performance.yaml"), "r") as f:
    PERF_CONFIG = yaml.safe_load(f)

# Metrics
request_latency = Histogram("mcp_request_duration_seconds", "Request latency", ["server", "endpoint"])
cache_hits = Counter("mcp_cache_hits_total", "Cache hits", ["cache_name"])
cache_misses = Counter("mcp_cache_misses_total", "Cache misses", ["cache_name"])
connection_pool_size = Gauge("mcp_connection_pool_size", "Connection pool size", ["pool_name"])

# Initialize caches
memory_cache = Cache(Cache.MEMORY, serializer=PickleSerializer())
redis_cache = None


async def init_redis_cache():
    """Initialize Redis cache with connection pooling"""
    global redis_cache

    redis_config = PERF_CONFIG["connection_pools"]["redis"]

    redis_cache = await aioredis.create_redis_pool(
        "redis://localhost:6379",
        minsize=redis_config["min_idle"],
        maxsize=redis_config["max_connections"],
        timeout=redis_config["connection_timeout"] / 1000,
    )

    connection_pool_size.labels(pool_name="redis").set(redis_config["max_connections"])
    logger.info("Redis cache initialized with connection pooling")


def cached(cache_name: str, ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{cache_name}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            try:
                result = await memory_cache.get(cache_key)
                if result is not None:
                    cache_hits.labels(cache_name=cache_name).inc()
                    return result
            except Exception as e:
                logger.warning(f"Cache get error: {e}")

            cache_misses.labels(cache_name=cache_name).inc()

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                await memory_cache.set(cache_key, result, ttl=ttl)
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

            return result

        return wrapper

    return decorator


def rate_limited(endpoint: str, default_limit: int = 100):
    """Decorator for rate limiting"""
    limit = PERF_CONFIG["rate_limiting"]["per_endpoint"].get(endpoint, default_limit)

    def decorator(func):
        # Simple in-memory rate limiting
        calls = []

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal calls

            now = time.time()
            # Clean old calls
            calls = [t for t in calls if now - t < 60]

            if len(calls) >= limit:
                raise Exception(f"Rate limit exceeded for {endpoint}")

            calls.append(now)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def timed(server: str, endpoint: str):
    """Decorator to measure request latency"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                request_latency.labels(server=server, endpoint=endpoint).observe(duration)

        return wrapper

    return decorator


class ConnectionPool:
    """Generic connection pool implementation"""

    def __init__(self, name: str, create_func: Callable, max_size: int = 10):
        self.name = name
        self.create_func = create_func
        self.max_size = max_size
        self.pool = asyncio.Queue(maxsize=max_size)
        self.created = 0

    async def acquire(self):
        """Acquire a connection from the pool"""
        try:
            # Try to get from pool
            conn = self.pool.get_nowait()
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if self.created < self.max_size:
                conn = await self.create_func()
                self.created += 1
            else:
                # Wait for available connection
                conn = await self.pool.get()

        return conn

    async def release(self, conn):
        """Release connection back to pool"""
        try:
            self.pool.put_nowait(conn)
        except asyncio.QueueFull:
            # Pool is full, close the connection
            if hasattr(conn, "close"):
                await conn.close()


class BatchProcessor:
    """Batch processing for better performance"""

    def __init__(self, process_func: Callable, max_batch_size: int = 100, timeout: float = 0.1):
        self.process_func = process_func
        self.max_batch_size = max_batch_size
        self.timeout = timeout
        self.batch = []
        self.results = {}
        self.lock = asyncio.Lock()
        self.condition = asyncio.Condition()
        self.processor_task = None

    async def start(self):
        """Start the batch processor"""
        self.processor_task = asyncio.create_task(self._process_batches())

    async def stop(self):
        """Stop the batch processor"""
        if self.processor_task:
            self.processor_task.cancel()
            await self.processor_task

    async def add(self, item: Any) -> Any:
        """Add item to batch and wait for result"""
        item_id = id(item)

        async with self.lock:
            self.batch.append((item_id, item))

        async with self.condition:
            # Notify processor
            self.condition.notify()

            # Wait for result
            while item_id not in self.results:
                await self.condition.wait()

            result = self.results.pop(item_id)

        return result

    async def _process_batches(self):
        """Process batches in background"""
        while True:
            try:
                # Wait for items or timeout
                async with self.condition:
                    await asyncio.wait_for(self.condition.wait(), timeout=self.timeout)

                # Process batch
                async with self.lock:
                    if not self.batch:
                        continue

                    # Take up to max_batch_size items
                    current_batch = self.batch[: self.max_batch_size]
                    self.batch = self.batch[self.max_batch_size :]

                # Process the batch
                items = [item for _, item in current_batch]
                results = await self.process_func(items)

                # Store results
                async with self.condition:
                    for (item_id, _), result in zip(current_batch, results):
                        self.results[item_id] = result
                    self.condition.notify_all()

            except asyncio.TimeoutError:
                # Process any pending items on timeout
                async with self.lock:
                    if self.batch:
                        current_batch = self.batch
                        self.batch = []

                        items = [item for _, item in current_batch]
                        results = await self.process_func(items)

                        async with self.condition:
                            for (item_id, _), result in zip(current_batch, results):
                                self.results[item_id] = result
                            self.condition.notify_all()

            except Exception as e:
                logger.error(f"Error in batch processor: {e}")


def optimize_app(app, server_name: str):
    """Apply performance optimizations to FastAPI app"""

    # Add middleware for compression
    from fastapi.middleware.gzip import GZipMiddleware

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add middleware for timing
    @app.middleware("http")
    async def add_process_time_header(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Initialize caches on startup
    @app.on_event("startup")
    async def startup_performance():
        await init_redis_cache()
        logger.info(f"Performance optimizations initialized for {server_name}")

    return app


# Export optimization utilities
__all__ = ["cached", "rate_limited", "timed", "ConnectionPool", "BatchProcessor", "optimize_app", "init_redis_cache"]
