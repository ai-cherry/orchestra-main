"""
Performance optimization utilities for AI Cherry
Focused on single-developer workflow efficiency
"""

import asyncio
import time
import functools
import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support for single-developer use"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.now() > entry['expires']:
            del self._cache[key]
            return None
        
        entry['last_accessed'] = datetime.now()
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        ttl = ttl or self._default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires': expires,
            'created': datetime.now(),
            'last_accessed': datetime.now()
        }
    
    def invalidate(self, key: str) -> bool:
        """Remove key from cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry['expires']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        valid_entries = [
            entry for entry in self._cache.values()
            if now <= entry['expires']
        ]
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': len(valid_entries),
            'expired_entries': len(self._cache) - len(valid_entries),
            'memory_usage_mb': len(str(self._cache)) / (1024 * 1024)
        }


def cached(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        cache = SimpleCache(default_ttl=ttl)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper
        
        # Add cache management methods
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.stats
        wrapper.cache_invalidate = cache.invalidate
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """Simple performance monitoring for development"""
    
    def __init__(self):
        self._metrics: Dict[str, list] = {}
    
    def record(self, operation: str, duration: float, metadata: Optional[Dict] = None):
        """Record operation performance"""
        if operation not in self._metrics:
            self._metrics[operation] = []
        
        self._metrics[operation].append({
            'duration': duration,
            'timestamp': datetime.now(),
            'metadata': metadata or {}
        })
        
        # Keep only last 1000 entries per operation
        if len(self._metrics[operation]) > 1000:
            self._metrics[operation] = self._metrics[operation][-1000:]
    
    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get performance statistics for an operation"""
        if operation not in self._metrics:
            return {}
        
        durations = [m['duration'] for m in self._metrics[operation]]
        
        return {
            'count': len(durations),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_duration': sum(durations),
            'last_recorded': self._metrics[operation][-1]['timestamp']
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations"""
        return {op: self.get_stats(op) for op in self._metrics.keys()}


def performance_monitor(operation_name: Optional[str] = None):
    """Decorator to monitor function performance"""
    monitor = PerformanceMonitor()
    
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitor.record(op_name, duration)
                logger.debug(f"Operation {op_name} took {duration:.3f}s")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitor.record(op_name, duration)
                logger.debug(f"Operation {op_name} took {duration:.3f}s")
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            wrapper = async_wrapper
        else:
            wrapper = sync_wrapper
        
        # Add monitoring methods
        wrapper.get_stats = lambda: monitor.get_stats(op_name)
        wrapper.get_all_stats = monitor.get_all_stats
        
        return wrapper
    return decorator


class AsyncBatchProcessor:
    """Batch processor for efficient async operations"""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self._queue = []
        self._processing = False
    
    async def add_task(self, coro):
        """Add a coroutine to the batch"""
        self._queue.append(coro)
        
        if len(self._queue) >= self.batch_size:
            await self._process_batch()
        elif not self._processing:
            # Start timer for partial batch
            asyncio.create_task(self._wait_and_process())
    
    async def _wait_and_process(self):
        """Wait for max_wait_time then process partial batch"""
        await asyncio.sleep(self.max_wait_time)
        if self._queue and not self._processing:
            await self._process_batch()
    
    async def _process_batch(self):
        """Process current batch of tasks"""
        if self._processing or not self._queue:
            return
        
        self._processing = True
        try:
            batch = self._queue[:self.batch_size]
            self._queue = self._queue[self.batch_size:]
            
            # Execute batch concurrently
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch task {i} failed: {result}")
            
            return results
        finally:
            self._processing = False
    
    async def flush(self):
        """Process all remaining tasks"""
        while self._queue:
            await self._process_batch()


# Global instances for easy use
default_cache = SimpleCache()
performance_monitor_instance = PerformanceMonitor()

