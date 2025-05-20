"""
Resilient Firestore adapter with circuit breaker pattern for AI Orchestra.

This module provides a resilient wrapper around the Firestore V2 adapter,
implementing the circuit breaker pattern to improve fault tolerance.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic, cast

from google.api_core.exceptions import (
    GoogleAPIError,
    ServiceUnavailable,
    DeadlineExceeded,
)

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.memory.memory_interface import MemoryInterface
from packages.shared.src.memory.memory_types import MemoryHealth
from packages.shared.src.memory.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
)
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar("T")


class ResilientFirestoreAdapter(MemoryInterface):
    """
    Resilient wrapper around FirestoreMemoryManagerV2 with circuit breaker pattern.

    This class wraps the FirestoreMemoryManagerV2 with a circuit breaker to
    improve fault tolerance when Firestore is experiencing issues.
    """

    def __init__(
        self,
        firestore_adapter: FirestoreMemoryManagerV2,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_recovery_timeout: float = 30.0,
        circuit_breaker_reset_timeout: float = 60.0,
    ):
        """
        Initialize the resilient Firestore adapter.

        Args:
            firestore_adapter: The Firestore V2 adapter to wrap
            circuit_breaker_failure_threshold: Number of failures before opening the circuit
            circuit_breaker_recovery_timeout: Time in seconds to wait before trying recovery
            circuit_breaker_reset_timeout: Time in seconds to reset failure count if no failures
        """
        self._adapter = firestore_adapter

        # Create circuit breakers for different operation types
        self._read_circuit = CircuitBreaker(
            name="firestore_read",
            failure_threshold=circuit_breaker_failure_threshold,
            recovery_timeout=circuit_breaker_recovery_timeout,
            reset_timeout=circuit_breaker_reset_timeout,
            excluded_exceptions=[],  # No exceptions are excluded for read operations
        )

        self._write_circuit = CircuitBreaker(
            name="firestore_write",
            failure_threshold=circuit_breaker_failure_threshold,
            recovery_timeout=circuit_breaker_recovery_timeout,
            reset_timeout=circuit_breaker_reset_timeout,
            excluded_exceptions=[],  # No exceptions are excluded for write operations
        )

        self._query_circuit = CircuitBreaker(
            name="firestore_query",
            failure_threshold=circuit_breaker_failure_threshold,
            recovery_timeout=circuit_breaker_recovery_timeout,
            reset_timeout=circuit_breaker_reset_timeout,
            excluded_exceptions=[],  # No exceptions are excluded for query operations
        )

        logger.info("Resilient Firestore adapter initialized with circuit breakers")

    async def initialize(self) -> None:
        """Initialize the underlying Firestore adapter."""
        try:
            await self._adapter.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize Firestore adapter: {e}")
            raise

    async def close(self) -> None:
        """Close the underlying Firestore adapter."""
        try:
            await self._adapter.close()
        except Exception as e:
            logger.error(f"Failed to close Firestore adapter: {e}")
            raise

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item with circuit breaker protection.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._write_circuit.execute(
                self._adapter.add_memory_item, item
            )
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker prevented add_memory_item operation: {e}")
            # Return a temporary ID with circuit breaker error indication
            return f"circuit_breaker_error_{int(time.time())}"

    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Get a memory item with circuit breaker protection.

        Args:
            item_id: The ID of the item to get

        Returns:
            The memory item, or None if not found

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._read_circuit.execute(
                self._adapter.get_memory_item, item_id
            )
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker prevented get_memory_item operation: {e}")
            return None

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Get conversation history with circuit breaker protection.

        Args:
            user_id: The user ID to get history for
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            filters: Optional filters to apply

        Returns:
            List of conversation memory items

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._query_circuit.execute(
                self._adapter.get_conversation_history,
                user_id=user_id,
                session_id=session_id,
                limit=limit,
                filters=filters,
            )
        except CircuitBreakerError as e:
            logger.error(
                f"Circuit breaker prevented get_conversation_history operation: {e}"
            )
            return []

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search with circuit breaker protection.

        Args:
            user_id: The user ID to search memories for
            query_embedding: The vector embedding of the query
            persona_context: Optional persona context for personalized results
            top_k: Maximum number of results to return

        Returns:
            List of memory items ordered by relevance

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._query_circuit.execute(
                self._adapter.semantic_search,
                user_id=user_id,
                query_embedding=query_embedding,
                persona_context=persona_context,
                top_k=top_k,
            )
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker prevented semantic_search operation: {e}")
            return []

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Add raw agent data with circuit breaker protection.

        Args:
            data: The agent data to add

        Returns:
            The ID of the added data

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._write_circuit.execute(
                self._adapter.add_raw_agent_data, data
            )
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker prevented add_raw_agent_data operation: {e}")
            # Return a temporary ID with circuit breaker error indication
            return f"circuit_breaker_error_{int(time.time())}"

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check for duplicate items with circuit breaker protection.

        Args:
            item: The memory item to check

        Returns:
            True if a duplicate exists, False otherwise

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._query_circuit.execute(
                self._adapter.check_duplicate, item
            )
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker prevented check_duplicate operation: {e}")
            return False

    async def cleanup_expired_items(self) -> int:
        """
        Clean up expired items with circuit breaker protection.

        Returns:
            Number of items removed

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the adapter
        """
        try:
            return await self._write_circuit.execute(
                self._adapter.cleanup_expired_items
            )
        except CircuitBreakerError as e:
            logger.error(
                f"Circuit breaker prevented cleanup_expired_items operation: {e}"
            )
            return 0

    async def health_check(self) -> MemoryHealth:
        """
        Check the health of the Firestore adapter.

        Returns:
            Health information
        """
        health: MemoryHealth = {
            "status": "unknown",
            "connection_status": "unknown",
            "error_count": 0,
            "latency_ms": 0,
            "circuit_breaker_status": {
                "read": self._read_circuit.state.value,
                "write": self._write_circuit.state.value,
                "query": self._query_circuit.state.value,
            },
            "timestamp": time.time(),
        }

        # Check if any circuit is open
        if (
            self._read_circuit.is_open
            or self._write_circuit.is_open
            or self._query_circuit.is_open
        ):
            health["status"] = "degraded"
            health["connection_status"] = "partial"
            health["error_count"] = max(
                self._read_circuit.failure_count,
                self._write_circuit.failure_count,
                self._query_circuit.failure_count,
            )
            return health

        # If all circuits are closed, check the underlying adapter
        try:
            adapter_health = await self._adapter.health_check()
            health.update(adapter_health)
            return health
        except Exception as e:
            logger.error(f"Failed to check adapter health: {e}")
            health["status"] = "unhealthy"
            health["connection_status"] = "disconnected"
            health["error_count"] = 1
            health["error_message"] = str(e)
            return health
