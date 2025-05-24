"""
Failover memory provider implementation for AI Orchestra.

This module provides a memory provider with failover capability using the circuit breaker pattern.
"""

import logging
import time
from typing import Any, List, Optional, Tuple

from ai_orchestra.core.errors import MemoryError
from ai_orchestra.core.interfaces.memory import MemoryProvider

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
    ):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = 0
        self.open = False

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.open = True
            logger.warning("Circuit breaker opened")

    def record_success(self) -> None:
        """Record a success and reset failure count."""
        self.failure_count = 0

    def is_closed(self) -> bool:
        """Check if the circuit is closed."""
        if not self.open:
            return True

        # Check if enough time has passed to try again
        if time.time() - self.last_failure_time >= self.reset_timeout:
            logger.info("Circuit breaker reset timeout elapsed, attempting to close")
            self.open = False
            self.failure_count = 0
            return True

        return False


class FailoverMemoryProvider(MemoryProvider):
    """Memory provider with failover capability."""

    def __init__(
        self,
        providers: List[Tuple[MemoryProvider, str]],
    ):
        """
        Initialize the failover memory provider.

        Args:
            providers: List of (provider, name) tuples in priority order
        """
        self.providers = providers
        self.circuit_breakers = {name: CircuitBreaker() for _, name in providers}

    async def _execute_with_failover(
        self,
        operation: str,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an operation with failover support.

        Args:
            operation: Operation description for logging
            method: Method name to call on providers
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            The result of the operation

        Raises:
            MemoryError: If all providers fail
        """
        last_error = None

        for provider, name in self.providers:
            # Skip providers with open circuit breakers
            if not self.circuit_breakers[name].is_closed():
                logger.debug(f"Skipping provider {name} due to open circuit breaker")
                continue

            try:
                # Call the method on the provider
                result = await getattr(provider, method)(*args, **kwargs)

                # Record success
                self.circuit_breakers[name].record_success()

                logger.debug(f"Operation {operation} succeeded with provider {name}")
                return result

            except Exception as e:
                # Record failure
                self.circuit_breakers[name].record_failure()

                logger.warning(f"Operation {operation} failed with provider {name}: {str(e)}")
                last_error = e

        # If we get here, all providers failed
        raise MemoryError(f"All memory providers failed for operation {operation}", cause=last_error)

    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store with failover support."""
        return await self._execute_with_failover(
            operation=f"store({key})",
            method="store",
            key=key,
            value=value,
            ttl=ttl,
        )

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve with failover support."""
        return await self._execute_with_failover(
            operation=f"retrieve({key})",
            method="retrieve",
            key=key,
        )

    async def delete(self, key: str) -> bool:
        """Delete with failover support."""
        return await self._execute_with_failover(
            operation=f"delete({key})",
            method="delete",
            key=key,
        )

    async def exists(self, key: str) -> bool:
        """Exists with failover support."""
        return await self._execute_with_failover(
            operation=f"exists({key})",
            method="exists",
            key=key,
        )

    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys with failover support."""
        return await self._execute_with_failover(
            operation=f"list_keys({pattern})",
            method="list_keys",
            pattern=pattern,
        )
