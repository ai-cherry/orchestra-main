"""
"""
    """
    """
        """
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
                logger.error("Portkey API key is required")
                raise ValueError("Portkey API key is required")

            self._client = portkey.Portkey(api_key=self._api_key)
            logger.info("Portkey client initialized")
        except Exception:

            pass
            logger.error(f"Failed to initialize Portkey client: {e}")
            raise ConnectionError(f"Failed to initialize Portkey client: {e}")

    async def setup_config(
        self,
        strategy: str = "fallback",
        fallbacks: Optional[List[Dict[str, Any]]] = None,
        cache_enabled: bool = True,
    ) -> None:
        """
        """
            raise RuntimeError("Portkey client not initialized")

        # Validate required Portkey API methods are available
        required_methods = ["set_strategy", "set_fallbacks", "enable_cache"]
        missing_methods = [method for method in required_methods if not hasattr(self._client, method)]

        if missing_methods:
            error_msg = f"Portkey client is missing required methods: {', '.join(missing_methods)}"
            logger.error(error_msg)
            raise AttributeError(error_msg)

        try:


            pass
            # Set routing strategy
            await self._run_method(method_name="set_strategy", strategy=strategy)
            logger.info(f"Portkey strategy set to: {strategy}")

            # Set fallback configurations
            if fallbacks:
                # Configure fallbacks - mapping of providers/models
                await self._run_method(method_name="set_fallbacks", fallbacks=fallbacks)
                logger.info(f"Portkey fallbacks configured: {len(fallbacks)} options")

            # Enable caching if requested
            if cache_enabled:
                await self._run_method(method_name="enable_cache", ttl=self._cache_ttl)
                logger.info(f"Portkey caching enabled with TTL: {self._cache_ttl}s")

            logger.info("Portkey configuration completed successfully")
        except Exception:

            pass
            error_msg = f"Failed to configure Portkey: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    async def _run_method(self, method_name: str, **kwargs) -> Any:
        """
        """
            raise RuntimeError("Portkey client not initialized")

        method = getattr(self._client, method_name)

        # Run the synchronous method in a thread pool
        try:

            pass
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: method(**kwargs))
        except Exception:

            pass
            logger.error(f"Error calling Portkey method {method_name}: {e}")
            raise

    async def semantic_cache_get(self, query: str, cache_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        """
            raise RuntimeError("Portkey client not initialized")

        try:


            pass
            # Generate a stable cache key if not provided
            if not cache_key:
                # Create a more stable hash than Python's built-in hash()
                hash_obj = hashlib.sha256(query.encode("utf-8"))
                key = f"semantic_cache:{hash_obj.hexdigest()[:16]}"
            else:
                key = cache_key


            # Try to get from Portkey's semantic cache using the helper method
            cached_response = await self._run_method(method_name="get_from_cache", prompt=query, cache_key=key)

            if cached_response:
                return cached_response
            else:
                return None

        except Exception:


            pass
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
        """
            raise RuntimeError("Portkey client not initialized")

        try:


            pass
            # Generate a stable cache key if not provided
            if not cache_key:
                # Create a more stable hash than Python's built-in hash()
                hash_obj = hashlib.sha256(query.encode("utf-8"))
                key = f"semantic_cache:{hash_obj.hexdigest()[:16]}"
            else:
                key = cache_key

            cache_ttl = ttl or self._cache_ttl


            # Store in Portkey's semantic cache using the helper method
            await self._run_method(
                method_name="store_in_cache",
                prompt=query,
                response=response,
                cache_key=key,
                ttl=cache_ttl,
            )

            return True

        except Exception:


            pass
            # Provide more context in the error message
            error_msg = f"Failed to store in Portkey semantic cache with query '{query[:30]}...': {str(e)}"
            logger.warning(error_msg)
            # Don't fail silently for unexpected errors
            if not isinstance(e, PortkeyError):
                logger.error("Unexpected error type in Portkey cache storage", exc_info=True)
            return False

    async def clear_cache(self) -> bool:
        """
        """
            raise RuntimeError("Portkey client not initialized")

        try:


            pass
            await self._run_method(method_name="clear_cache")
            logger.info("Successfully cleared Portkey semantic cache")
            return True

        except Exception:


            pass
            # Provide more context in the error message
            error_msg = f"Failed to clear Portkey semantic cache: {str(e)}"
            logger.warning(error_msg)
            # Don't fail silently for unexpected errors
            if not isinstance(e, PortkeyError):
                logger.error("Unexpected error type in Portkey cache clearing", exc_info=True)
            return False

    def is_initialized(self) -> bool:
        """
        """
        """Clean up any resources."""
