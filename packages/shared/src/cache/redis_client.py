"""
Redis Client for Orchestra AI System.

This module provides Redis caching functionality with support for
Cloud Memorystore connections and Secret Manager integration for authentication.
"""

import logging
import json
import asyncio
from typing import Optional, Any, Dict, Union
import os
from datetime import timedelta
from fastapi import Depends

# Import Redis
try:
    import redis
    from redis import Redis
    from redis.exceptions import ConnectionError, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = object
    ConnectionError = Exception
    RedisError = Exception
    REDIS_AVAILABLE = False

# Import Google Secret Manager
try:
    from google.cloud import secretmanager
    SECRETMANAGER_AVAILABLE = True
except ImportError:
    secretmanager = None
    SECRETMANAGER_AVAILABLE = False

# Import settings
from core.orchestrator.src.config.settings import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis client for Orchestra caching needs.
    
    This class handles connection to Redis/Memorystore, 
    with support for Cloud Secret Manager for secure authentication.
    """
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        """
        Initialize the Redis client.
        
        Args:
            settings: Application settings containing Redis configuration
        """
        self.settings = settings
        self.redis_client: Optional[Redis] = None
        self._initialized = False
        
        # Set cache configuration
        self.cache_enabled = settings.REDIS_CACHE_ENABLED
        self.default_ttl = settings.REDIS_CACHE_TTL
        
        # Check if Redis is available
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available. Install with: pip install redis")
    
    async def initialize(self) -> bool:
        """
        Initialize the Redis connection.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self._initialized or not REDIS_AVAILABLE or not self.cache_enabled:
            return self._initialized
        
        # Skip if no Redis host
        if not self.settings.REDIS_HOST:
            logger.info("No Redis host configured, skipping initialization")
            return False
            
        try:
            # Run initialization in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._initialize_sync)
            
            self._initialized = success
            if success:
                logger.info(f"Redis client initialized successfully: {self.settings.REDIS_HOST}")
            else:
                logger.warning("Redis client initialization failed")
                
            return success
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}")
            return False
            
    def _initialize_sync(self) -> bool:
        """
        Synchronous initialization of Redis client.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        # Get Redis password from Secret Manager if configured
        password = self._get_redis_password()
        
        try:
            # Initialize Redis client with appropriate SSL settings
            # Cloud Memorystore requires SSL in GCP
            self.redis_client = redis.Redis(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                password=password,
                ssl=self._is_cloud_environment(),
                ssl_cert_reqs=None,  # Don't verify cert for GCP Memorystore
                decode_responses=True  # Auto-decode to strings
            )
            
            # Test connection
            self.redis_client.ping()
            return True
        except (ConnectionError, RedisError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
            
    def _is_cloud_environment(self) -> bool:
        """
        Check if running in a cloud environment (GCP).
        
        Returns:
            True if in a cloud environment, False otherwise
        """
        env = self.settings.ENVIRONMENT.lower()
        return env in ["prod", "production", "stage", "staging"]
            
    def _get_redis_password(self) -> Optional[str]:
        """
        Get Redis password from Secret Manager or environment.
        
        Returns:
            Redis password or None if not configured
        """
        # Check if Secret Manager is available and configured
        if not self.settings.REDIS_AUTH_SECRET or not SECRETMANAGER_AVAILABLE:
            return None
            
        try:
            # Get the project ID
            project_id = self.settings.get_gcp_project_id()
            if not project_id:
                logger.warning("No GCP project ID configured, cannot access Redis auth secret")
                return None
                
            # Access the secret
            secret_name = self.settings.REDIS_AUTH_SECRET
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            password = response.payload.data.decode("UTF-8")
            
            return password
        except Exception as e:
            logger.error(f"Failed to retrieve Redis password from Secret Manager: {e}")
            return None
    
    async def close(self) -> None:
        """Close the Redis connection."""
        if self.redis_client:
            # Redis client doesn't have an async close method,
            # but we can run it in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._close_sync)
            
    def _close_sync(self) -> None:
        """Synchronous close of Redis client."""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis client connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self.redis_client = None
                self._initialized = False
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value or None if not found
        """
        if not self.redis_client or not self._initialized:
            return None
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            value = await loop.run_in_executor(None, lambda: self.redis_client.get(key))
            
            if not value:
                return None
                
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as is if not JSON
                return value
        except Exception as e:
            logger.warning(f"Error getting value from Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized if not a string)
            ttl: Time-to-live in seconds (None for default TTL)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client or not self._initialized:
            return False
            
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.default_ttl
        
        try:
            # Serialize complex types to JSON
            if not isinstance(value, (str, int, float, bool)):
                value = json.dumps(value)
                
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None,
                lambda: self.redis_client.set(key, value, ex=ttl)
            )
            return bool(success)
        except Exception as e:
            logger.warning(f"Error setting value in Redis: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client or not self._initialized:
            return False
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(None, lambda: self.redis_client.delete(key))
            return count > 0
        except Exception as e:
            logger.warning(f"Error deleting value from Redis: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client or not self._initialized:
            return False
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(None, lambda: self.redis_client.exists(key))
            return bool(exists)
        except Exception as e:
            logger.warning(f"Error checking key existence in Redis: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Redis connection.
        
        Returns:
            Dictionary with health status information
        """
        if not REDIS_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "Redis library not available",
                "enabled": self.cache_enabled
            }
            
        if not self.cache_enabled:
            return {
                "status": "disabled",
                "message": "Redis caching is disabled",
                "enabled": False
            }
            
        if not self.settings.REDIS_HOST:
            return {
                "status": "not_configured",
                "message": "Redis host not configured",
                "enabled": self.cache_enabled
            }
            
        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Redis initialization failed: {e}",
                    "enabled": self.cache_enabled
                }
        
        if not self.redis_client:
            return {
                "status": "error",
                "message": "Redis client not initialized",
                "enabled": self.cache_enabled
            }
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            pong = await loop.run_in_executor(None, lambda: self.redis_client.ping())
            
            if pong:
                return {
                    "status": "healthy",
                    "message": "Redis connection is healthy",
                    "host": self.settings.REDIS_HOST,
                    "port": self.settings.REDIS_PORT,
                    "enabled": self.cache_enabled
                }
            else:
                return {
                    "status": "error",
                    "message": "Redis ping failed",
                    "enabled": self.cache_enabled
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis health check failed: {e}",
                "enabled": self.cache_enabled
            }
