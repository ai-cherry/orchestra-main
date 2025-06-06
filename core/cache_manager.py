"""
Cache Manager
Provides caching functionality for improved performance
"""

import asyncio
import json
from typing import Any, Optional, Callable, Union
from datetime import datetime, timedelta
import hashlib
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages application caching"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        logger.info("Cache manager initialized")
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Cache manager closed")
    
    def _generate_key(self, namespace: str, key: Union[str, dict]) -> str:
        """Generate cache key"""
        if isinstance(key, dict):
            key = json.dumps(key, sort_keys=True)
        
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{namespace}:{key_hash}"
    
    async def get(self, namespace: str, key: Union[str, dict]) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            value = await self._redis.get(cache_key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(self, namespace: str, key: Union[str, dict], value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl or self.default_ttl
        
        try:
            await self._redis.setex(
                cache_key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, namespace: str, key: Union[str, dict]):
        """Delete value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            await self._redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def clear_namespace(self, namespace: str):
        """Clear all keys in a namespace"""
        try:
            pattern = f"{namespace}:*"
            cursor = 0
            
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def cached(self, namespace: str, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Generate cache key from function arguments
                cache_key = {
                    'func': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                
                # Try to get from cache
                cached_value = await self.get(namespace, cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(namespace, cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
