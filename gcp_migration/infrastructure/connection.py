"""
Connection management for GCP services.

This module provides utilities for managing connections to GCP services,
including connection pooling and resource management.
"""

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Tuple, TypeVar

from ..domain.exceptions_fixed import ConnectionError, TimeoutError

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar("T")  # Type for connection objects
PoolFactory = Callable[[], Awaitable[T]]
PoolCleaner = Callable[[T], Awaitable[None]]


class ConnectionPool:
    """
    Pool for managing connections to external services.

    This class provides a pool of reusable connections to optimize
    resource usage and improve performance by avoiding frequent
    connection establishment and teardown.
    """

    def __init__(
        self,
        name: str,
        factory: PoolFactory,
        closer: PoolCleaner,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: float = 60.0,
        max_lifetime: float = 3600.0,
        connection_timeout: float = 10.0,
    ):
        """
        Initialize the connection pool.

        Args:
            name: Name of the pool
            factory: Async factory function to create new connections
            closer: Async function to close connections
            min_size: Minimum pool size
            max_size: Maximum pool size
            max_idle_time: Maximum idle time for a connection in seconds
            max_lifetime: Maximum lifetime for a connection in seconds
            connection_timeout: Timeout for acquiring a connection in seconds
        """
        self.name = name
        self.factory = factory
        self.closer = closer
        self.min_size = max(0, min_size)
        self.max_size = max(1, max_size)
        self.max_idle_time = max_idle_time
        self.max_lifetime = max_lifetime
        self.connection_timeout = connection_timeout

        # Ensure min_size <= max_size
        if self.min_size > self.max_size:
            self.min_size = self.max_size

        self._pool: List[
            Tuple[T, float, float]
        ] = []  # (connection, create_time, last_used_time)
        self._in_use: Set[T] = set()
        self._waiter_count = 0
        self._events: Dict[T, asyncio.Event] = {}
        self._closed = False
        self._lock = asyncio.Lock()
        self._maintenance_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """
        Initialize the connection pool.

        Creates the minimum number of connections and starts the maintenance task.
        """
        if self._closed:
            raise ConnectionError(f"Cannot initialize closed pool: {self.name}")

        async with self._lock:
            # Create minimum connections
            for _ in range(self.min_size):
                conn = await self._create_connection()
                self._pool.append((conn, time.time(), time.time()))

        # Start maintenance task
        self._maintenance_task = asyncio.create_task(self._maintain_pool())
        logger.debug(
            f"Connection pool '{self.name}' initialized with {self.min_size} connections"
        )

    async def acquire(self) -> T:
        """
        Acquire a connection from the pool.

        Returns:
            A connection object

        Raises:
            TimeoutError: If connection acquisition times out
            ConnectionError: If the pool is closed or connection creation fails
        """
        if self._closed:
            raise ConnectionError(f"Connection pool '{self.name}' is closed")

        # Try to get an idle connection
        async with self._lock:
            if self._pool:
                conn, create_time, _ = self._pool.pop(0)
                self._in_use.add(conn)
                logger.debug(f"Acquired existing connection from pool '{self.name}'")
                return conn

            # If we haven't reached max_size, create a new connection
            if len(self._in_use) < self.max_size:
                conn = await self._create_connection()
                self._in_use.add(conn)
                logger.debug(f"Created new connection for pool '{self.name}'")
                return conn

        # If we're here, we need to wait for a connection
        self._waiter_count += 1
        try:
            # Create a waiter event for this acquisition
            waiter = asyncio.Event()

            # Wait for a connection with timeout
            conn = None
            try:
                async with self._lock:
                    # Check again if a connection became available
                    if self._pool:
                        conn, create_time, _ = self._pool.pop(0)
                        self._in_use.add(conn)
                        return conn

                # Wait for a connection to be released
                try:
                    # Wait for timeout duration
                    await asyncio.wait_for(
                        waiter.wait(), timeout=self.connection_timeout
                    )

                    # Try to get the connection after the event is set
                    async with self._lock:
                        if self._pool:
                            conn, create_time, _ = self._pool.pop(0)
                            self._in_use.add(conn)
                            return conn

                except asyncio.TimeoutError:
                    raise TimeoutError(
                        f"Timeout waiting for connection from pool '{self.name}'",
                        service_name=self.name,
                        operation="acquire",
                        details={"timeout": self.connection_timeout},
                    )

            finally:
                # Clean up the waiter
                if conn:
                    self._events.pop(conn, None)

        finally:
            self._waiter_count -= 1

        # This should not happen if the code is correct
        raise ConnectionError(f"Failed to acquire connection from pool '{self.name}'")

    async def release(self, conn: T) -> None:
        """
        Release a connection back to the pool.

        Args:
            conn: Connection to release

        Raises:
            ConnectionError: If the connection is not from this pool
        """
        if self._closed:
            # If pool is closed, close the connection
            await self._close_connection(conn)
            return

        async with self._lock:
            # Check if this connection is actually from our pool
            if conn not in self._in_use:
                logger.warning(
                    f"Attempted to release foreign connection to pool '{self.name}'"
                )
                return

            # Remove from in_use set
            self._in_use.remove(conn)

            # If we have waiters, notify one of them
            if self._waiter_count > 0:
                # Find a waiter event
                for waiter in self._events.values():
                    if not waiter.is_set():
                        # Add connection back to pool
                        self._pool.append((conn, time.time(), time.time()))
                        # Set the event to wake up a waiter
                        waiter.set()
                        return

            # Otherwise, return connection to pool if not exceeding min size
            current_pool_size = len(self._pool) + len(self._in_use)
            if current_pool_size <= self.max_size:
                self._pool.append((conn, time.time(), time.time()))
            else:
                # Pool is at capacity, close the connection
                await self._close_connection(conn)

    async def close(self) -> None:
        """
        Close the connection pool and all connections.
        """
        if self._closed:
            return

        self._closed = True

        # Cancel maintenance task
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._lock:
            # Close in-use connections
            for conn in list(self._in_use):
                await self._close_connection(conn)
                self._in_use.remove(conn)

            # Close pooled connections
            while self._pool:
                conn, _, _ = self._pool.pop()
                await self._close_connection(conn)

        logger.info(f"Connection pool '{self.name}' closed")

    async def _create_connection(self) -> T:
        """
        Create a new connection.

        Returns:
            A new connection

        Raises:
            ConnectionError: If connection creation fails
        """
        try:
            return await self.factory()
        except Exception as e:
            raise ConnectionError(
                f"Failed to create connection for pool '{self.name}'", cause=e
            )

    async def _close_connection(self, conn: T) -> None:
        """
        Close a connection.

        Args:
            conn: Connection to close
        """
        try:
            await self.closer(conn)
        except Exception as e:
            logger.warning(f"Error closing connection in pool '{self.name}': {e}")

    async def _maintain_pool(self) -> None:
        """
        Maintenance task to manage pool size and connection health.
        """
        while not self._closed:
            try:
                # Wait for next maintenance interval
                await asyncio.sleep(max(self.max_idle_time / 2, 10))

                if self._closed:
                    break

                # Check for expired connections
                current_time = time.time()
                to_remove = []

                async with self._lock:
                    # Identify connections to remove
                    for i, (conn, create_time, last_used_time) in enumerate(self._pool):
                        idle_time = current_time - last_used_time
                        lifetime = current_time - create_time

                        if (
                            idle_time > self.max_idle_time
                            or lifetime > self.max_lifetime
                        ):
                            to_remove.append((i, conn))

                    # Remove them from the list (in reverse order to avoid index issues)
                    for i, conn in sorted(to_remove, reverse=True):
                        del self._pool[i]
                        await self._close_connection(conn)

                    # Ensure minimum pool size
                    shortfall = self.min_size - len(self._pool)
                    if shortfall > 0:
                        # Create new connections to maintain min_size
                        for _ in range(shortfall):
                            conn = await self._create_connection()
                            self._pool.append((conn, current_time, current_time))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error in connection pool maintenance for '{self.name}': {e}"
                )

    @property
    def size(self) -> int:
        """Get the current pool size."""
        return len(self._pool) + len(self._in_use)

    @property
    def available(self) -> int:
        """Get the number of available connections."""
        return len(self._pool)

    @property
    def in_use(self) -> int:
        """Get the number of connections currently in use."""
        return len(self._in_use)


class ConnectionPoolManager:
    """
    Manager for multiple connection pools.

    This class provides centralized management for multiple connection pools,
    allowing for shared configurations and coordinated lifecycle management.
    """

    def __init__(self):
        """Initialize the connection pool manager."""
        self._pools: Dict[str, ConnectionPool] = {}
        self._lock = asyncio.Lock()

    async def create_pool(
        self,
        name: str,
        factory: PoolFactory,
        closer: PoolCleaner,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: float = 60.0,
        max_lifetime: float = 3600.0,
        connection_timeout: float = 10.0,
    ) -> ConnectionPool:
        """
        Create and register a new connection pool.

        Args:
            name: Name of the pool
            factory: Async factory function to create new connections
            closer: Async function to close connections
            min_size: Minimum pool size
            max_size: Maximum pool size
            max_idle_time: Maximum idle time for a connection in seconds
            max_lifetime: Maximum lifetime for a connection in seconds
            connection_timeout: Timeout for acquiring a connection in seconds

        Returns:
            The created connection pool

        Raises:
            ConnectionError: If a pool with the same name already exists
        """
        async with self._lock:
            if name in self._pools:
                raise ConnectionError(f"Connection pool '{name}' already exists")

            # Create the pool
            pool = ConnectionPool(
                name=name,
                factory=factory,
                closer=closer,
                min_size=min_size,
                max_size=max_size,
                max_idle_time=max_idle_time,
                max_lifetime=max_lifetime,
                connection_timeout=connection_timeout,
            )

            # Initialize the pool
            await pool.initialize()

            # Register the pool
            self._pools[name] = pool

            return pool

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """
        Get a connection pool by name.

        Args:
            name: Name of the pool

        Returns:
            The connection pool or None if not found
        """
        return self._pools.get(name)

    async def close_pool(self, name: str) -> None:
        """
        Close a specific connection pool.

        Args:
            name: Name of the pool

        Raises:
            ConnectionError: If the pool does not exist
        """
        async with self._lock:
            if name not in self._pools:
                raise ConnectionError(f"Connection pool '{name}' does not exist")

            pool = self._pools.pop(name)
            await pool.close()

    async def close_all(self) -> None:
        """
        Close all connection pools.
        """
        async with self._lock:
            for name, pool in list(self._pools.items()):
                await pool.close()

            self._pools.clear()

    @property
    def pool_names(self) -> List[str]:
        """Get the names of all registered pools."""
        return list(self._pools.keys())

    @property
    def total_connections(self) -> int:
        """Get the total number of connections across all pools."""
        return sum(pool.size for pool in self._pools.values())

    @property
    def available_connections(self) -> int:
        """Get the total number of available connections across all pools."""
        return sum(pool.available for pool in self._pools.values())


# Global connection pool manager instance
_pool_manager: Optional[ConnectionPoolManager] = None


def get_pool_manager() -> ConnectionPoolManager:
    """
    Get the global connection pool manager instance.

    Returns:
        The global connection pool manager
    """
    global _pool_manager

    if _pool_manager is None:
        _pool_manager = ConnectionPoolManager()

    return _pool_manager


async def create_connection_pool(
    name: str,
    factory: PoolFactory,
    closer: PoolCleaner,
    min_size: int = 1,
    max_size: int = 10,
    max_idle_time: float = 60.0,
    max_lifetime: float = 3600.0,
    connection_timeout: float = 10.0,
) -> ConnectionPool:
    """
    Create a connection pool using the global manager.

    Args:
        name: Name of the pool
        factory: Async factory function to create new connections
        closer: Async function to close connections
        min_size: Minimum pool size
        max_size: Maximum pool size
        max_idle_time: Maximum idle time for a connection in seconds
        max_lifetime: Maximum lifetime for a connection in seconds
        connection_timeout: Timeout for acquiring a connection in seconds

    Returns:
        The created connection pool
    """
    manager = get_pool_manager()
    return await manager.create_pool(
        name=name,
        factory=factory,
        closer=closer,
        min_size=min_size,
        max_size=max_size,
        max_idle_time=max_idle_time,
        max_lifetime=max_lifetime,
        connection_timeout=connection_timeout,
    )


async def close_all_pools() -> None:
    """
    Close all connection pools in the global manager.
    """
    manager = get_pool_manager()
    await manager.close_all()
