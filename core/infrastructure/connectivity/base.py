"""
Base abstractions for service connectivity.

This module provides interfaces for connecting to external services
with health checks, retries, and fallback mechanisms.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ServiceStatus(Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Health check result for a service."""

    status: ServiceStatus
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ServiceConnection(ABC):
    """Abstract base class for service connections."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self._status = ServiceStatus.UNKNOWN
        self._fallback_handler: Optional[Callable] = None

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the service."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the service."""
        pass

    @abstractmethod
    async def health_check(self) -> ServiceHealth:
        """Perform health check on the service."""
        pass

    @abstractmethod
    async def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute an operation on the service."""
        pass

    def set_fallback(self, handler: Callable) -> None:
        """Set a fallback handler for when the service is unavailable."""
        self._fallback_handler = handler

    async def execute_with_fallback(self, operation: str, *args, **kwargs) -> Any:
        """Execute operation with fallback if service is unavailable."""
        try:
            # Check health first
            health = await self.health_check()
            if health.status == ServiceStatus.UNHEALTHY and self._fallback_handler:
                logger.warning(f"Service {self.name} is unhealthy, using fallback")
                return await self._fallback_handler(operation, *args, **kwargs)

            # Try to execute the operation
            return await self.execute(operation, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error executing {operation} on {self.name}: {e}")
            if self._fallback_handler:
                logger.info(f"Using fallback for {self.name}")
                return await self._fallback_handler(operation, *args, **kwargs)
            raise


class ConnectionPool:
    """Manages a pool of service connections with load balancing."""

    def __init__(self, service_class: type, configs: list[Dict[str, Any]]):
        self.service_class = service_class
        self.configs = configs
        self.connections: list[ServiceConnection] = []
        self._current_index = 0
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize all connections in the pool."""
        for i, config in enumerate(self.configs):
            conn = self.service_class(f"{config.get('name', 'service')}-{i}", config)
            await conn.connect()
            self.connections.append(conn)

    async def get_healthy_connection(self) -> Optional[ServiceConnection]:
        """Get a healthy connection from the pool."""
        async with self._lock:
            # Try all connections starting from current index
            for _ in range(len(self.connections)):
                conn = self.connections[self._current_index]
                self._current_index = (self._current_index + 1) % len(self.connections)

                health = await conn.health_check()
                if health.status in (ServiceStatus.HEALTHY, ServiceStatus.DEGRADED):
                    return conn

            return None

    async def execute_on_any(self, operation: str, *args, **kwargs) -> Any:
        """Execute operation on any healthy connection."""
        conn = await self.get_healthy_connection()
        if not conn:
            raise Exception(f"No healthy connections available for {operation}")

        return await conn.execute(operation, *args, **kwargs)

    async def close_all(self) -> None:
        """Close all connections in the pool."""
        for conn in self.connections:
            try:
                await conn.disconnect()
            except Exception as e:
                logger.error(f"Error closing connection {conn.name}: {e}")


class RetryableConnection(ServiceConnection):
    """Base class for connections with built-in retry logic."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def execute_with_retry(self, operation: str, *args, **kwargs) -> Any:
        """Execute operation with automatic retries."""
        return await self.execute(operation, *args, **kwargs)


class ServiceRegistry:
    """Registry for all service connections."""

    def __init__(self):
        self._services: Dict[str, ServiceConnection] = {}
        self._pools: Dict[str, ConnectionPool] = {}

    def register_service(self, name: str, connection: ServiceConnection) -> None:
        """Register a single service connection."""
        self._services[name] = connection

    def register_pool(self, name: str, pool: ConnectionPool) -> None:
        """Register a connection pool."""
        self._pools[name] = pool

    def get_service(self, name: str) -> Optional[ServiceConnection]:
        """Get a registered service by name."""
        return self._services.get(name)

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get a registered connection pool by name."""
        return self._pools.get(name)

    async def health_check_all(self) -> Dict[str, ServiceHealth]:
        """Perform health checks on all registered services."""
        results = {}

        # Check individual services
        for name, service in self._services.items():
            try:
                results[name] = await service.health_check()
            except Exception as e:
                results[name] = ServiceHealth(status=ServiceStatus.UNKNOWN, error=str(e))

        # Check pools
        for pool_name, pool in self._pools.items():
            for i, conn in enumerate(pool.connections):
                try:
                    results[f"{pool_name}[{i}]"] = await conn.health_check()
                except Exception as e:
                    results[f"{pool_name}[{i}]"] = ServiceHealth(status=ServiceStatus.UNKNOWN, error=str(e))

        return results
