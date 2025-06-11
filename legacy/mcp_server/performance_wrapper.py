#!/usr/bin/env python3
"""
"""
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
                cache_key = f"{cache_name}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            try:

                pass
                result = await memory_cache.get(cache_key)
                if result is not None:
                    cache_hits.labels(cache_name=cache_name).inc()
                    return result
            except Exception:

                pass
                logger.warning(f"Cache get error: {e}")

            cache_misses.labels(cache_name=cache_name).inc()

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:

                pass
                await memory_cache.set(cache_key, result, ttl=ttl)
            except Exception:

                pass
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
    """Generic connection pool implementation"""
        """Acquire a connection from the pool"""
        """Release connection back to pool"""
            if hasattr(conn, "close"):
                await conn.close()

class BatchProcessor:
    """Batch processing for better performance"""
        """Start the batch processor"""
        """Stop the batch processor"""
        """Add item to batch and wait for result"""
        """Process batches in background"""
                logger.error(f"Error in batch processor: {e}")

def optimize_app(app, server_name: str):
    """Apply performance optimizations to FastAPI app"""
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
__all__ = [
    "cached",
    "rate_limited",
    "timed",
    "ConnectionPool",
    "BatchProcessor",
    "optimize_app",
    "init_redis_cache",
]
