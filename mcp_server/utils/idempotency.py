#!/usr/bin/env python3
"""
"""
T = TypeVar("T")
R = TypeVar("R")

class IdempotencyKey:
    """Generate and validate idempotency keys."""
        """
        """
        """
        """
        """
        """
        data = {"args": args, "kwargs": kwargs}
        return IdempotencyKey.from_request(data)

    @staticmethod
    def is_valid(key: str) -> bool:
        """
        """
        if len(key) == 36 and key.count("-") == 4:
            try:

                pass
                uuid.UUID(key)
                return True
            except Exception:

                pass
                pass

        # SHA-256 hash format check (64 hex characters)
        if len(key) == 64 and all(c in "0123456789abcdef" for c in key.lower()):
            return True

        return False

class InMemoryIdempotencyStore:
    """In-memory store for idempotency keys and their results."""
        """
        """
        """
        """
            if entry["timestamp"] + self.ttl_seconds > time.time():
                return entry["result"]
            # Remove expired entry
            del self.store[key]

        return None

    async def store_result(self, key: str, result: Dict[str, Any]) -> bool:
        """
        """
        self.store[key] = {"result": result, "timestamp": time.time()}

        # Remove from in-progress if present
        if key in self.in_progress:
            del self.in_progress[key]

        return True

    async def mark_in_progress(self, key: str) -> bool:
        """
        """
        """
        """
        """Clean up expired entries."""
        expired_keys = [key for key, entry in self.store.items() if entry["timestamp"] + self.ttl_seconds <= now]
        for key in expired_keys:
            del self.store[key]

        # Clean up expired in-progress markers
        expired_markers = [key for key, timestamp in self.in_progress.items() if timestamp + 300 <= now]
        for key in expired_markers:
            del self.in_progress[key]

class RedisIdempotencyStore:
    """Redis-based store for idempotency keys and their results."""
        prefix: str = "idempotency:",
    ):
        """
        """
            raise ImportError("Redis package not installed. Install with 'pip install redis'")

        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        self.prefix = prefix

    async def get_result(self, key: str) -> Optional[Dict[str, Any]]:
        """
        """
            result_json = await self.redis.get(f"{self.prefix}{key}")
            if result_json:
                return json.loads(result_json)
            return None
        except Exception:

            pass
            logger.error(f"Error getting idempotency result: {e}")
            return None

    async def store_result(self, key: str, result: Dict[str, Any]) -> bool:
        """
        """
            await self.redis.set(f"{self.prefix}{key}", result_json, ex=self.ttl_seconds)

            # Clear in-progress marker
            await self.clear_in_progress(key)

            return True
        except Exception:

            pass
            logger.error(f"Error storing idempotency result: {e}")
            return False

    async def mark_in_progress(self, key: str) -> bool:
        """
        """
            in_progress_key = f"{self.prefix}{key}:in_progress"
            result = await self.redis.set(in_progress_key, "1", ex=300, nx=True)
            return bool(result)
        except Exception:

            pass
            logger.error(f"Error marking idempotency key as in progress: {e}")
            return False

    async def clear_in_progress(self, key: str) -> bool:
        """
        """
            in_progress_key = f"{self.prefix}{key}:in_progress"
            await self.redis.delete(in_progress_key)
            return True
        except Exception:

            pass
            logger.error(f"Error clearing in-progress marker: {e}")
            return False

class IdempotencyManager:
    """Manager for idempotent operations."""
        """
        """
        redis_url: str, ttl_seconds: int = 86400, prefix: str = "idempotency:"
    ) -> "IdempotencyManager":
        """
        """
            raise ImportError("Redis package not installed. Install with 'pip install redis'")

        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
        )

        store = RedisIdempotencyStore(redis_client, ttl_seconds, prefix)
        return IdempotencyManager(store, ttl_seconds)

    async def execute_idempotent(self, key: str, func: Callable[..., Awaitable[R]], *args: Any, **kwargs: Any) -> R:
        """
        """
            logger.info(f"Using cached result for idempotency key: {key}")
            return cast(R, existing_result.get("result"))

        # Try to mark as in progress
        if not await self.store.mark_in_progress(key):
            # Another process is already handling this request
            logger.info(f"Request with key {key} is already being processed")

            # Wait and check for result
            for i in range(10):  # Try 10 times with exponential backoff
                await asyncio.sleep(0.5 * (2**i))  # Exponential backoff
                result = await self.store.get_result(key)
                if result:
                    return cast(R, result.get("result"))

            # If we still don't have a result, proceed anyway
            logger.warning(f"No result found after waiting for idempotency key: {key}")
            await self.store.clear_in_progress(key)

        try:


            pass
            # Execute the function
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()

            # Store the result
            await self.store.store_result(
                key,
                {
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": end_time - start_time,
                },
            )

            return result
        except Exception:

            pass
            # Store the error
            await self.store.store_result(
                key,
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Re-raise the except Exception:
     pass
            # Clear in-progress marker
            await self.store.clear_in_progress(key)

def idempotent(
    store: Optional[Union[InMemoryIdempotencyStore, RedisIdempotencyStore]] = None,
    key_func: Optional[Callable[..., str]] = None,
    ttl_seconds: int = 86400,
) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """
    """
            idempotency_key = kwargs.pop("idempotency_key", None)

            if not idempotency_key:
                if key_func:
                    # Use the provided key function
                    idempotency_key = key_func(*args, **kwargs)
                else:
                    # Generate from arguments
                    idempotency_key = IdempotencyKey.from_args(*args, **kwargs)

            return await idempotency_manager.execute_idempotent(idempotency_key, func, *args, **kwargs)

        return wrapper

    return decorator

# Singleton instance for global use
_default_manager: Optional[IdempotencyManager] = None

def get_idempotency_manager() -> IdempotencyManager:
    """Get the default IdempotencyManager instance."""
    prefix: str = "idempotency:",
) -> None:
    """
    """
    logger.info(f"Configured idempotency manager with TTL: {ttl_seconds} seconds")

# Convenience decorator using the default manager
def default_idempotent(
    key_func: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """
    """