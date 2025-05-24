"""
Portkey Manager for semantic caching and configuration.

This module provides a standalone manager for Portkey functionality,
decoupled from other services like Redis.
"""

import os
import logging
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Union

# Import Portkey (optional)
try:
    import portkey
    from portkey.exceptions import PortkeyError
except ImportError:
    portkey = None

    class PortkeyError(Exception):
        pass


# Configure logger
logger = logging.getLogger(__name__)


class PortkeyManager:
    """
    Manager for Portkey API functionality.

    This class provides methods for configuring Portkey routing strategies,
    and utilizing semantic caching.
    """

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600):
        """
        Initialize a new PortkeyManager.

        Args:
            api_key: Optional Portkey API key. If not provided,
                    it will be retrieved from PORTKEY_API_KEY environment variable.
            cache_ttl: Default TTL for Portkey cache in seconds.
        """
        self._api_key = api_key or os.environ.get("PORTKEY_API_KEY")
        self._cache_ttl = cache_ttl
        self._client = None

        if portkey is None:
            logger.error("Portkey library not available. Install with: pip install portkey-ai")
            raise ImportError("Portkey library not available")

        # Initialize the Portkey client
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Portkey client."""
        try:
            if not self._api_key:
                logger.error("Portkey API key is required")
                raise ValueError("Portkey API key is required")

            self._client = portkey.Portkey(api_key=self._api_key)
            logger.info("Portkey client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Portkey client: {e}")
            raise ConnectionError(f"Failed to initialize Portkey client: {e}")

    async def setup_config(
        self,
        strategy: str = "fallback",
        fallbacks: Optional[List[Dict[str, Any]]] = None,
        cache_enabled: bool = True,
    ) -> None:
        """
        Configure Portkey settings.

        Args:
            strategy: Routing strategy ('fallback', 'loadbalance', or 'cost_aware')
            fallbacks: List of fallback configurations (model configurations)
            cache_enabled: Whether to enable Portkey's semantic caching
        """
        if not self._client:
            raise RuntimeError("Portkey client not initialized")

        # Validate required Portkey API methods are available
        required_methods = ["set_strategy", "set_fallbacks", "enable_cache"]
        missing_methods = [method for method in required_methods if not hasattr(self._client, method)]

        if missing_methods:
            error_msg = f"Portkey client is missing required methods: {', '.join(missing_methods)}"
            logger.error(error_msg)
            raise AttributeError(error_msg)

        try:
            # Set routing strategy
            logger.debug(f"Setting Portkey strategy to: {strategy}")
            await self._run_method(method_name="set_strategy", strategy=strategy)
            logger.info(f"Portkey strategy set to: {strategy}")

            # Set fallback configurations
            if fallbacks:
                # Configure fallbacks - mapping of providers/models
                logger.debug(f"Configuring {len(fallbacks)} Portkey fallbacks")
                await self._run_method(method_name="set_fallbacks", fallbacks=fallbacks)
                logger.info(f"Portkey fallbacks configured: {len(fallbacks)} options")

            # Enable caching if requested
            if cache_enabled:
                logger.debug(f"Enabling Portkey cache with TTL: {self._cache_ttl}s")
                await self._run_method(method_name="enable_cache", ttl=self._cache_ttl)
                logger.info(f"Portkey caching enabled with TTL: {self._cache_ttl}s")

            logger.info("Portkey configuration completed successfully")
        except Exception as e:
            error_msg = f"Failed to configure Portkey: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    async def _run_method(self, method_name: str, **kwargs) -> Any:
        """
        Run a Portkey method safely in an async context.

        This helper method ensures that synchronous Portkey methods
        don't block the async event loop.

        Args:
            method_name: The name of the Portkey method to call
            **kwargs: Arguments to pass to the method

        Returns:
            The result of the method call
        """
        if not self._client:
            raise RuntimeError("Portkey client not initialized")

        method = getattr(self._client, method_name)

        # Run the synchronous method in a thread pool
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: method(**kwargs))
        except Exception as e:
            logger.error(f"Error calling Portkey method {method_name}: {e}")
            raise

    async def semantic_cache_get(self, query: str, cache_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Try to retrieve a semantically similar result from Portkey's cache.

        Args:
            query: The query to semantically match
            cache_key: Optional explicit cache key

        Returns:
            Cached response if found, None otherwise
        """
        if not self._client:
            raise RuntimeError("Portkey client not initialized")

        try:
            # Generate a stable cache key if not provided
            if not cache_key:
                # Create a more stable hash than Python's built-in hash()
                hash_obj = hashlib.sha256(query.encode("utf-8"))
                key = f"semantic_cache:{hash_obj.hexdigest()[:16]}"
            else:
                key = cache_key

            logger.debug(f"Attempting Portkey semantic cache lookup with key: {key}")

            # Try to get from Portkey's semantic cache using the helper method
            cached_response = await self._run_method(method_name="get_from_cache", prompt=query, cache_key=key)

            if cached_response:
                logger.debug(f"Portkey semantic cache hit for query: {query[:30]}...")
                return cached_response
            else:
                logger.debug(f"Portkey semantic cache miss for query: {query[:30]}...")
                return None

        except Exception as e:
            # Provide more context in the error message
            error_msg = f"Portkey semantic cache error with query '{query[:30]}...': {str(e)}"
            logger.warning(error_msg)
            # Don't fail silently for unexpected errors
            if not isinstance(e, PortkeyError):
                logger.error("Unexpected error type in Portkey cache lookup", exc_info=True)
            return None

    async def semantic_cache_store(
        self,
        query: str,
        response: Dict[str, Any],
        cache_key: Optional[str] = None,
        ttl: Optional[int] = None,
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
        if not self._client:
            raise RuntimeError("Portkey client not initialized")

        try:
            # Generate a stable cache key if not provided
            if not cache_key:
                # Create a more stable hash than Python's built-in hash()
                hash_obj = hashlib.sha256(query.encode("utf-8"))
                key = f"semantic_cache:{hash_obj.hexdigest()[:16]}"
            else:
                key = cache_key

            cache_ttl = ttl or self._cache_ttl

            logger.debug(f"Storing in Portkey semantic cache with key: {key}, TTL: {cache_ttl}s")

            # Store in Portkey's semantic cache using the helper method
            await self._run_method(
                method_name="store_in_cache",
                prompt=query,
                response=response,
                cache_key=key,
                ttl=cache_ttl,
            )

            logger.debug(f"Successfully stored in Portkey semantic cache: {query[:30]}...")
            return True

        except Exception as e:
            # Provide more context in the error message
            error_msg = f"Failed to store in Portkey semantic cache with query '{query[:30]}...': {str(e)}"
            logger.warning(error_msg)
            # Don't fail silently for unexpected errors
            if not isinstance(e, PortkeyError):
                logger.error("Unexpected error type in Portkey cache storage", exc_info=True)
            return False

    async def clear_cache(self) -> bool:
        """
        Clear all Portkey's semantic cache.

        Returns:
            True if cleared successfully, False otherwise
        """
        if not self._client:
            raise RuntimeError("Portkey client not initialized")

        try:
            logger.debug("Attempting to clear Portkey semantic cache")
            await self._run_method(method_name="clear_cache")
            logger.info("Successfully cleared Portkey semantic cache")
            return True

        except Exception as e:
            # Provide more context in the error message
            error_msg = f"Failed to clear Portkey semantic cache: {str(e)}"
            logger.warning(error_msg)
            # Don't fail silently for unexpected errors
            if not isinstance(e, PortkeyError):
                logger.error("Unexpected error type in Portkey cache clearing", exc_info=True)
            return False

    def is_initialized(self) -> bool:
        """
        Check if Portkey client is initialized.

        Returns:
            True if Portkey client is initialized, False otherwise
        """
        return self._client is not None

    async def close(self) -> None:
        """Clean up any resources."""
        # Currently no specific cleanup needed for Portkey client
        # But implemented for future-proofing
        logger.debug("Portkey manager closing")
