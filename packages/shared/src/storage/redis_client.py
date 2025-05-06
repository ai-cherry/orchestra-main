"""
Redis client implementation for the AI Orchestration System.

This module provides a client for interacting with Redis cache,
with optional Portkey integration for enhanced caching capabilities.
"""

import os
import logging
import json
from typing import Optional, Dict, Any, List, Union

# Import Redis
try:
    import redis
    from redis.asyncio import Redis
    from redis.exceptions import RedisError
except ImportError:
    redis = None
    Redis = None

    class RedisError(Exception):
        pass

# Import Portkey manager
try:
    from ..portkey.manager import PortkeyManager
except ImportError:
    # Fallback for older code structure or direct imports
    try:
        from packages.shared.src.portkey.manager import PortkeyManager
    except ImportError:
        PortkeyManager = None

# Import GCP authentication utilities (for Secret Manager access)
try:
    from ..gcp.auth import get_gcp_credentials
except ImportError:
    # Fallback for older code structure
    try:
        from packages.shared.src.gcp.auth import get_gcp_credentials
    except ImportError:
        get_gcp_credentials = None

# Import Google Secret Manager (optional)
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

# Configure logger
logger = logging.getLogger(__name__)


class RedisClient:
    """
    Client for interacting with Redis cache.

    This class provides methods for storing and retrieving data from Redis,
    with optional Portkey integration for enhanced caching capabilities.
    """

    def __init__(
        self, 
        host: Optional[str] = None, 
        port: Optional[int] = None,
        password: Optional[str] = None,
        ssl: bool = False,
        db: int = 0,
        use_portkey: bool = False,
        portkey_api_key: Optional[str] = None,
        portkey_cache_ttl: int = 3600,
        secret_id: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        """
        Initialize a new RedisClient.

        Args:
            host: Optional Redis host address. If not provided,
                  it will be retrieved from REDIS_HOST environment variable.
            port: Optional Redis port. If not provided,
                  it will be retrieved from REDIS_PORT environment variable.
            password: Optional Redis password. If not provided,
                  it will be retrieved from REDIS_PASSWORD environment variable.
            ssl: Whether to use SSL for the connection.
            db: Redis database number to use.
            use_portkey: Whether to use Portkey for enhanced caching.
            portkey_api_key: Optional Portkey API key. If not provided and use_portkey is True,
                            it will be retrieved from PORTKEY_API_KEY environment variable.
            portkey_cache_ttl: Default TTL for Portkey cache in seconds.
            secret_id: Optional Secret Manager secret ID for Redis password.
                       If provided, will fetch the password from Secret Manager.
            project_id: Optional GCP project ID for Secret Manager access.
        """
        # Redis settings
        self._host = host or os.environ.get("REDIS_HOST", "localhost")
        self._port = port or int(os.environ.get("REDIS_PORT", "6379"))
        self._password = password  # Will be set during initialization
        self._password_env = os.environ.get("REDIS_PASSWORD")
        self._password_secret_id = secret_id or os.environ.get("REDIS_PASSWORD_SECRET_ID")
        self._ssl = ssl or os.environ.get("REDIS_SSL", "false").lower() == "true"
        self._db = db
        self._redis = None
        self._project_id = project_id or os.environ.get("GCP_PROJECT_ID") or "agi-baby-cherry"

        # Portkey settings
        self._use_portkey = use_portkey
        self._portkey_api_key = portkey_api_key or os.environ.get("PORTKEY_API_KEY")
        self._portkey_cache_ttl = portkey_cache_ttl
        self._portkey_manager = None

        # Validate dependencies
        if redis is None:
            logger.error("Redis library not available. Install with: pip install redis")
            raise ImportError("Redis library not available")

        if self._use_portkey and PortkeyManager is None:
            logger.error("PortkeyManager not available. Ensure the module is properly installed.")
            raise ImportError("PortkeyManager not available")

        # Initialize clients
        self._setup_redis_password()
        self._initialize_client()

    def _setup_redis_password(self) -> None:
        """
        Set up the Redis password, with Secret Manager support if available.
        
        This method attempts to get the Redis password from:
        1. The provided password parameter
        2. Secret Manager (if secret_id is provided)
        3. The REDIS_PASSWORD environment variable
        """
        # If password was provided directly, use it
        if self._password:
            logger.debug("Using provided Redis password")
            return
            
        # Try to get password from Secret Manager if secret_id is provided
        if self._password_secret_id and secretmanager is not None and get_gcp_credentials is not None:
            logger.debug(f"Attempting to get Redis password from Secret Manager: {self._password_secret_id}")
            try:
                # Initialize GCP auth for Secret Manager
                credentials, project_id = get_gcp_credentials(project_id=self._project_id)
                
                # Create Secret Manager client
                client = secretmanager.SecretManagerServiceClient(credentials=credentials)
                
                # Build the resource name of the secret version
                name = f"projects/{project_id}/secrets/{self._password_secret_id}/versions/latest"
                
                # Access the secret version
                response = client.access_secret_version(request={"name": name})
                
                # Get the password from the secret
                self._password = response.payload.data.decode("UTF-8")
                logger.info(f"Retrieved Redis password from Secret Manager: {self._password_secret_id}")
                return
            except Exception as e:
                logger.warning(f"Failed to get Redis password from Secret Manager: {e}")
                # Continue to try environment variable
        
        # Fall back to environment variable
        self._password = self._password_env
        if self._password:
            logger.debug("Using Redis password from environment variable")
        else:
            logger.debug("No Redis password provided")

    def _initialize_client(self) -> None:
        """Initialize the Redis client and Portkey if enabled."""
        # Initialize Redis client
        try:
            self._redis = Redis(
                host=self._host,
                port=self._port,
                password=self._password,
                ssl=self._ssl,
                db=self._db,
                decode_responses=True  # Auto-decode to strings
            )
            logger.info(f"Redis client initialized for {self._host}:{self._port}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise ConnectionError(f"Failed to initialize Redis connection: {e}")

        # Initialize Portkey manager if enabled
        if self._use_portkey:
            try:
                self._portkey_manager = PortkeyManager(
                    api_key=self._portkey_api_key,
                    cache_ttl=self._portkey_cache_ttl
                )
                logger.info("Portkey manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Portkey manager: {e}")
                raise ConnectionError(f"Failed to initialize Portkey manager: {e}")

    # Redis operations

    async def set_cache(self, key: str, value: str, ttl: int = 3600) -> None:
        """
        Set a key-value pair in the Redis cache.

        Args:
            key: The cache key
            value: The value to store
            ttl: Time to live in seconds, defaults to 1 hour
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            await self._redis.set(key, value, ex=ttl)
            logger.debug(f"Set cache key {key} with TTL {ttl}")
        except RedisError as e:
            logger.error(f"Error setting Redis cache: {e}")
            raise

    async def get_cache(self, key: str) -> Optional[str]:
        """
        Retrieve a value from the Redis cache.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value or None if not found
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            value = await self._redis.get(key)
            logger.debug(f"Retrieved cache key {key}: {'found' if value else 'not found'}")
            return value
        except RedisError as e:
            logger.error(f"Error getting Redis cache: {e}")
            raise

    async def delete_cache(self, key: str) -> None:
        """
        Delete a key from the Redis cache.

        Args:
            key: The cache key to delete
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            await self._redis.delete(key)
            logger.debug(f"Deleted cache key {key}")
        except RedisError as e:
            logger.error(f"Error deleting Redis cache: {e}")
            raise

    async def set_hash(self, key: str, field: str, value: str) -> None:
        """
        Set a field in a Redis hash.

        Args:
            key: The hash key
            field: The field name
            value: The value to store
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            await self._redis.hset(key, field, value)
            logger.debug(f"Set hash field {key}.{field}")
        except RedisError as e:
            logger.error(f"Error setting Redis hash field: {e}")
            raise

    async def get_hash(self, key: str, field: str) -> Optional[str]:
        """
        Get a field from a Redis hash.

        Args:
            key: The hash key
            field: The field name to retrieve

        Returns:
            The field value or None if not found
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            value = await self._redis.hget(key, field)
            logger.debug(f"Retrieved hash field {key}.{field}: {'found' if value else 'not found'}")
            return value
        except RedisError as e:
            logger.error(f"Error getting Redis hash field: {e}")
            raise

    async def get_all_hash(self, key: str) -> Dict[str, str]:
        """
        Get all fields from a Redis hash.

        Args:
            key: The hash key

        Returns:
            A dictionary of all field-value pairs
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
        
        try:
            result = await self._redis.hgetall(key)
            logger.debug(f"Retrieved all hash fields for {key}: {len(result)} fields")
            return result
        except RedisError as e:
            logger.error(f"Error getting all Redis hash fields: {e}")
            raise
            
    async def set_json(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> None:
        """
        Store a JSON object in Redis.
        
        Args:
            key: The cache key
            value: The dictionary to store as JSON
            ttl: Time to live in seconds, defaults to 1 hour
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
            
        try:
            json_data = json.dumps(value)
            await self._redis.set(key, json_data, ex=ttl)
            logger.debug(f"Set JSON data at key {key} with TTL {ttl}")
        except (RedisError, TypeError) as e:
            logger.error(f"Error setting Redis JSON data: {e}")
            raise
            
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a JSON object from Redis.
        
        Args:
            key: The cache key
            
        Returns:
            Deserialized JSON object or None if not found
        """
        if not self._redis:
            raise RuntimeError("Redis client not initialized")
            
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
                
            return json.loads(data)
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Error retrieving JSON from Redis: {e}")
            raise
    
    # Portkey delegation methods
    
    async def setup_portkey_config(
        self, 
        strategy: str = "fallback", 
        fallbacks: Optional[List[Dict[str, Any]]] = None,
        cache_enabled: bool = True
    ) -> None:
        """
        Configure Portkey settings for the client.

        Args:
            strategy: Routing strategy ('fallback', 'loadbalance', or 'cost_aware')
            fallbacks: List of fallback configurations (model configurations)
            cache_enabled: Whether to enable Portkey's semantic caching
        """
        if not self._use_portkey or not self._portkey_manager:
            raise RuntimeError("Portkey is not enabled or not initialized")
        
        # Delegate to PortkeyManager
        await self._portkey_manager.setup_config(
            strategy=strategy,
            fallbacks=fallbacks,
            cache_enabled=cache_enabled
        )
        logger.info("Portkey configuration completed successfully")

    async def portkey_semantic_cache(
        self, 
        query: str,
        cache_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Try to retrieve a semantically similar result from Portkey's cache.

        Args:
            query: The query to semantically match
            cache_key: Optional explicit cache key

        Returns:
            Cached response if found, None otherwise
        """
        if not self._use_portkey or not self._portkey_manager:
            raise RuntimeError("Portkey is not enabled or not initialized")
            
        # Delegate to PortkeyManager
        return await self._portkey_manager.semantic_cache_get(
            query=query,
            cache_key=cache_key
        )

    async def portkey_store_semantic_cache(
        self,
        query: str,
        response: Dict[str, Any],
        cache_key: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store a response in Portkey's semantic cache.

        Args:
            query: The original query
            response: The response to cache
            cache_key: Optional explicit cache key
            ttl: Optional custom TTL in seconds

        Returns:
            True if stored successfully, False otherwise
        """
        if not self._use_portkey or not self._portkey_manager:
            raise RuntimeError("Portkey is not enabled or not initialized")
            
        # Delegate to PortkeyManager
        return await self._portkey_manager.semantic_cache_store(
            query=query,
            response=response,
            cache_key=cache_key,
            ttl=ttl
        )

    async def clear_portkey_cache(self) -> bool:
        """
        Clear all Portkey's semantic cache.

        Returns:
            True if cleared successfully, False otherwise
        """
        if not self._use_portkey or not self._portkey_manager:
            raise RuntimeError("Portkey is not enabled or not initialized")
            
        # Delegate to PortkeyManager
        return await self._portkey_manager.clear_cache()

    async def is_portkey_enabled(self) -> bool:
        """
        Check if Portkey is enabled and initialized.

        Returns:
            True if Portkey is enabled and initialized, False otherwise
        """
        return self._use_portkey and self._portkey_manager is not None and self._portkey_manager.is_initialized()
            
    async def close(self) -> None:
        """Close the Redis connection and any other resources."""
        if self._redis:
            await self._redis.close()
            logger.debug("Redis connection closed")
            
        # Close PortkeyManager if initialized
        if self._portkey_manager:
            await self._portkey_manager.close()
            logger.debug("Portkey manager closed")
