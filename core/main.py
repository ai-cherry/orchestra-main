"""
Main orchestration entry point for Orchestra AI.

This module initializes and coordinates all core services.
"""

import asyncio
import logging
import signal
from typing import Optional

from core.infrastructure.config.settings import get_settings
from core.infrastructure.connectivity.base import ServiceRegistry
from core.infrastructure.connectivity.mongodb import MongoDBConnection
from core.infrastructure.connectivity.dragonfly import DragonflyConnection
from core.services.memory.unified_memory import get_memory_service
from core.services.events.event_bus import get_event_bus, EventPriority


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OrchestraCore:
    """Main orchestration core that manages all services."""

    def __init__(self):
        self.settings = get_settings()
        self.service_registry = ServiceRegistry()
        self.event_bus = get_event_bus()
        self.memory_service = None
        self._running = False
        self._tasks = []

    async def initialize(self) -> None:
        """Initialize all core services."""
        logger.info("Initializing Orchestra AI Core...")

        # Initialize service connections
        await self._initialize_connections()

        # Initialize memory service
        self.memory_service = get_memory_service(self.service_registry)
        await self.memory_service.initialize()

        # Set up event handlers
        self._setup_event_handlers()

        # Publish initialization complete event
        await self.event_bus.publish(
            "core.initialized",
            {"services": list(self.service_registry._services.keys())},
            priority=EventPriority.HIGH,
        )

        logger.info("Orchestra AI Core initialized successfully")

    async def _initialize_connections(self) -> None:
        """Initialize all service connections."""

        # MongoDB connection
        if self.settings.mongodb.enabled:
            try:
                mongodb_config = {
                    "connection_string": self.settings.mongodb.uri.get_secret_value(),
                    "database": self.settings.mongodb.database,
                }
                mongodb_conn = MongoDBConnection("mongodb-main", mongodb_config)
                await mongodb_conn.connect()
                self.service_registry.register_service("mongodb", mongodb_conn)
                logger.info("MongoDB connection established")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                if self.settings.is_production:
                    raise

        # DragonflyDB connection
        if self.settings.dragonfly.enabled:
            try:
                dragonfly_config = {
                    "connection_string": self.settings.dragonfly.uri.get_secret_value(),
                    "decode_responses": self.settings.dragonfly.decode_responses,
                    "max_connections": self.settings.dragonfly.max_connections,
                }
                dragonfly_conn = DragonflyConnection("dragonfly-main", dragonfly_config)
                await dragonfly_conn.connect()
                self.service_registry.register_service("dragonfly", dragonfly_conn)
                logger.info("DragonflyDB connection established")
            except Exception as e:
                logger.error(f"Failed to connect to DragonflyDB: {e}")
                if self.settings.is_production:
                    raise

        # Note: Weaviate connection would be added here similarly

    def _setup_event_handlers(self) -> None:
        """Set up core event handlers."""

        # Health check event
        async def handle_health_check(event):
            health_status = await self.service_registry.health_check_all()
            await self.event_bus.publish(
                "core.health_status",
                {"status": health_status, "request_id": event.data.get("request_id")},
            )

        self.event_bus.subscribe("core.health_check", handle_health_check)

        # Memory cleanup event
        async def handle_memory_cleanup(event):
            if self.memory_service:
                await self.memory_service.cleanup()
                logger.info("Memory cleanup completed")

        self.event_bus.subscribe("core.memory_cleanup", handle_memory_cleanup)

        # Shutdown event
        async def handle_shutdown(event):
            logger.info("Shutdown event received")
            await self.shutdown()

        self.event_bus.subscribe(
            "core.shutdown", handle_shutdown, priority=EventPriority.CRITICAL
        )

    async def start(self) -> None:
        """Start the orchestration core."""
        if self._running:
            logger.warning("Orchestra Core is already running")
            return

        self._running = True
        logger.info("Starting Orchestra AI Core...")

        # Start periodic tasks
        self._tasks.append(asyncio.create_task(self._periodic_health_check()))
        self._tasks.append(asyncio.create_task(self._periodic_memory_cleanup()))

        # Publish start event
        await self.event_bus.publish(
            "core.started",
            {"timestamp": asyncio.get_event_loop().time()},
            priority=EventPriority.HIGH,
        )

        logger.info("Orchestra AI Core started")

    async def _periodic_health_check(self) -> None:
        """Periodic health check task."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self.event_bus.publish("core.health_check", {})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")

    async def _periodic_memory_cleanup(self) -> None:
        """Periodic memory cleanup task."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                await self.event_bus.publish("core.memory_cleanup", {})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic memory cleanup: {e}")

    async def shutdown(self) -> None:
        """Shutdown the orchestration core."""
        if not self._running:
            return

        logger.info("Shutting down Orchestra AI Core...")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close all service connections
        for service_name, service in self.service_registry._services.items():
            try:
                await service.disconnect()
                logger.info(f"Disconnected {service_name}")
            except Exception as e:
                logger.error(f"Error disconnecting {service_name}: {e}")

        # Publish shutdown complete event
        await self.event_bus.publish(
            "core.shutdown_complete", {}, priority=EventPriority.CRITICAL
        )

        logger.info("Orchestra AI Core shutdown complete")

    async def run(self) -> None:
        """Run the orchestration core."""
        await self.initialize()
        await self.start()

        # Keep running until shutdown
        try:
            while self._running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            await self.shutdown()


# Global instance
_orchestra_core: Optional[OrchestraCore] = None


def get_orchestra_core() -> OrchestraCore:
    """Get the global orchestra core instance."""
    global _orchestra_core

    if _orchestra_core is None:
        _orchestra_core = OrchestraCore()

    return _orchestra_core


async def main():
    """Main entry point."""
    core = get_orchestra_core()

    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Signal {sig} received")
        asyncio.create_task(core.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the core
    await core.run()


if __name__ == "__main__":
    asyncio.run(main())
