"""
"""
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class cherry_aiCore:
    """Main coordination core that manages all services."""
        """Initialize all core services."""
        logger.info("Initializing Cherry AI Core...")

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

        logger.info("Cherry AI Core initialized successfully")

async def _initialize_connections(self) -> None:
        """Initialize all service connections."""
                    "connection_string": self.settings.mongodb.uri.get_secret_value(),
                    "database": self.settings.mongodb.database,
                }
                mongodb_conn = MongoDBConnection("mongodb-main", mongodb_config)
                await mongodb_conn.connect()
                self.service_registry.register_service("mongodb", mongodb_conn)
                logger.info("MongoDB connection established")
            except Exception:

                pass
                logger.error(f"Failed to connect to MongoDB: {e}")
                if self.settings.is_production:
                    raise

        # DragonflyDB connection
        if self.settings.dragonfly.enabled:
            try:

                pass
                dragonfly_config = {
                    "connection_string": self.settings.dragonfly.uri.get_secret_value(),
                    "decode_responses": self.settings.dragonfly.decode_responses,
                    "max_connections": self.settings.dragonfly.max_connections,
                }
                dragonfly_conn = DragonflyConnection("dragonfly-main", dragonfly_config)
                await dragonfly_conn.connect()
                self.service_registry.register_service("dragonfly", dragonfly_conn)
                logger.info("DragonflyDB connection established")
            except Exception:

                pass
                logger.error(f"Failed to connect to DragonflyDB: {e}")
                if self.settings.is_production:
                    raise

        # Note: Weaviate connection would be added here similarly

def _setup_event_handlers(self) -> None:
        """Set up core event handlers."""
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

        self.event_bus.subscribe("core.shutdown", handle_shutdown, priority=EventPriority.CRITICAL)

async def start(self) -> None:
        """Start the coordination core."""
            logger.warning("cherry_ai Core is already running")
            return

        self._running = True
        logger.info("Starting Cherry AI Core...")

        # Start periodic tasks
        self._tasks.append(asyncio.create_task(self._periodic_health_check()))
        self._tasks.append(asyncio.create_task(self._periodic_memory_cleanup()))

        # Publish start event
        await self.event_bus.publish(
            "core.started",
            {"timestamp": asyncio.get_event_loop().time()},
            priority=EventPriority.HIGH,
        )

        logger.info("Cherry AI Core started")

async def _periodic_health_check(self) -> None:
        """Periodic health check task."""
                await self.event_bus.publish("core.health_check", {})
            except Exception:

                pass
                break
            except Exception:

                pass
                logger.error(f"Error in periodic health check: {e}")

async def _periodic_memory_cleanup(self) -> None:
        """Periodic memory cleanup task."""
                await self.event_bus.publish("core.memory_cleanup", {})
            except Exception:

                pass
                break
            except Exception:

                pass
                logger.error(f"Error in periodic memory cleanup: {e}")

async def shutdown(self) -> None:
        """Shutdown the coordination core."""
        logger.info("Shutting down Cherry AI Core...")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close all service connections
        for service_name, service in self.service_registry._services.items():
            try:

                pass
                await service.disconnect()
                logger.info(f"Disconnected {service_name}")
            except Exception:

                pass
                logger.error(f"Error disconnecting {service_name}: {e}")

        # Publish shutdown complete event
        await self.event_bus.publish("core.shutdown_complete", {}, priority=EventPriority.CRITICAL)

        logger.info("Cherry AI Core shutdown complete")

async def run(self) -> None:
        """Run the coordination core."""
            logger.info("Keyboard interrupt received")
        finally:
            await self.shutdown()

# Global instance
_cherry_ai_core: Optional[cherry_aiCore] = None

def get_cherry_ai_core() -> cherry_aiCore:
    """Get the global cherry_ai core instance."""
    """Main entry point."""
        logger.info(f"Signal {sig} received")
        asyncio.create_task(core.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the core
    await core.run()

if __name__ == "__main__":
    asyncio.run(main())
