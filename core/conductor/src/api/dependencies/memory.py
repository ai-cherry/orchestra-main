# TODO: Consider adding connection pooling configuration
"""
"""
    """Initialize imports and set availability flags."""
        logger.info("Attempting to import memory managers from packages.shared.src.memory")
        # Importing here to avoid module-level imports that could cause circular dependencies
        global MemoryManager, InMemoryMemoryManager
        from packages.shared.src.memory.memory_manager import InMemoryMemoryManager, MemoryManager

        MEMORY_MANAGER_AVAILABLE = True
        logger.info("Successfully imported memory managers")

        # Try to import the MongoDB adapter
        try:

            pass
            logger.info("Attempting to import MongoDBMemoryAdapter")
            global MongoDBMemoryAdapter
            from packages.shared.src.memory.mongodb_adapter import MongoDBMemoryAdapter

            MONGODB_AVAILABLE = True
            logger.info("Successfully imported MongoDBMemoryAdapter")
        except Exception:

            pass
            logger.warning(f"Failed to import MongoDBMemoryAdapter, MongoDB storage will not be available: {str(e)}")
            MONGODB_AVAILABLE = False

        # Using main implementation, not stubs
        USE_STUBS = False

    except Exception:


        pass
        logger.warning(
            f"Failed to import memory managers from packages.shared.src.memory, falling back to stub implementation: {str(e)}"
        )

        # Try to import base memory manager and stubs
        try:

            pass
            global MemoryManager, InMemoryMemoryManager
            from packages.shared.src.memory.memory_manager import MemoryManager
            from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub as InMemoryMemoryManager

            MEMORY_MANAGER_AVAILABLE = True
            MONGODB_AVAILABLE = False
            USE_STUBS = True
            logger.info("Using stub memory manager implementation")
        except Exception:

            pass
            logger.error(f"Failed to import even stub memory managers: {str(stub_error)}")
            MEMORY_MANAGER_AVAILABLE = False

    # Import hexagonal architecture components
    try:

        pass
        logger.info("Attempting to import hexagonal architecture components for memory service")
        global MemoryService, MemoryServiceFactory, MongoDBStorageAdapter, PostgresStorageAdapter
        from packages.shared.src.memory.adapters.mongodb_adapter import MongoDBStorageAdapter
        from packages.shared.src.memory.adapters.postgres_adapter import PostgresStorageAdapter
        from packages.shared.src.memory.services.memory_service import MemoryService
        from packages.shared.src.memory.services.memory_service_factory import MemoryServiceFactory

        HEX_ARCH_AVAILABLE = True
        logger.info("Successfully imported hexagonal architecture components")
    except Exception:

        pass
        logger.warning(
            f"Failed to import hexagonal architecture components for memory service: {str(e)}"
        )
        HEX_ARCH_AVAILABLE = False

# Initialize imports
_initialize_imports()

# Global memory manager and service instances (using type hints)
_memory_manager: Optional["MemoryManager"] = None
_memory_service: Optional["MemoryService"] = None

@error_boundary(fallback_value=None, propagate_types=[MemoryError], log_to_monitoring=True)
def create_memory_manager(settings: Settings) -> "MemoryManager":
    """
    """
        raise DependencyError("Memory manager components are not available")

    # Determine if we need cloud storage based on environment and project ID
    use_mongodb = (
        settings.ENVIRONMENT in ["prod", "production", "stage", "staging"]
        and settings.get_vultr_project_id() is not None
        and MONGODB_AVAILABLE
    )

    # Use MongoDB if available and configured
    if use_mongodb:
        try:

            pass
            logger.info(f"Creating MongoDB memory adapter for environment: {settings.ENVIRONMENT}")
            return MongoDBMemoryAdapter(
                project_id=settings.get_vultr_project_id(),
                credentials_path=settings.get_vultr_credentials_path(),
                namespace=settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}",
            )
        except Exception:

            pass
            logger.error(f"Failed to create MongoDB memory adapter: {str(e)}")
            logger.warning("Falling back to in-memory implementation")
            # Convert general exception to a specific memory error
            raise MemoryConnectionError(f"Failed to connect to MongoDB: {str(e)}", original_error=e)

    # Use in-memory implementation
    namespace = settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}"
    logger.info(f"Using in-memory memory manager with namespace: {namespace}")
    return InMemoryMemoryManager(namespace=namespace)

@error_boundary(fallback_value=None, propagate_types=[MemoryError], log_to_monitoring=True)
async def get_memory_manager(
    settings: Settings = Depends(get_settings),
) -> "MemoryManager":
    """
    """
        raise DependencyError("Memory manager components are not available")

    # Create the memory manager if it doesn't exist
    if _memory_manager is None:
        try:

            pass
            _memory_manager = create_memory_manager(settings)
        except Exception:

            pass
            # If we can't create the MongoDB adapter, fall back to in-memory
            logger.warning(f"Creating in-memory manager due to error: {str(e)}")
            namespace = settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}"
            _memory_manager = InMemoryMemoryManager(namespace=namespace)

        try:


            pass
            # Initialize the memory manager
            await _memory_manager.initialize()
            logger.info(f"Memory manager initialized: {type(_memory_manager).__name__}")
        except Exception:

            pass
            logger.error(f"Failed to initialize memory manager: {str(e)}")
            # Fall back to in-memory if initialization fails
            if not isinstance(_memory_manager, InMemoryMemoryManager):
                logger.warning("Falling back to in-memory implementation")
                try:

                    pass
                    namespace = settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}"
                    _memory_manager = InMemoryMemoryManager(namespace=namespace)
                    await _memory_manager.initialize()
                except Exception:

                    pass
                    # If even in-memory initialization fails, we're in trouble
                    _memory_manager = None
                    raise MemoryOperationError(
                        f"Failed to initialize any memory manager: {str(fallback_error)}",
                        original_error=fallback_error,
                    )

    return _memory_manager

@error_boundary(propagate_types=[MemoryError], log_to_monitoring=True)
async def initialize_memory_manager(settings: Settings = None) -> None:
    """
    """
        logger.error("Memory manager components are not available")
        return

    if settings is None:
        settings = get_settings()

    # Create the memory manager if it doesn't exist
    if _memory_manager is None:
        try:

            pass
            _memory_manager = create_memory_manager(settings)
        except Exception:

            pass
            # If we can't create the preferred adapter, fall back to in-memory
            logger.warning(f"Creating in-memory manager due to error: {str(e)}")
            namespace = settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}"
            _memory_manager = InMemoryMemoryManager(namespace=namespace)

    # Initialize the memory manager
    try:

        pass
        logger.info(f"Initializing memory manager: {type(_memory_manager).__name__}")
        await _memory_manager.initialize()
        logger.info("Memory manager initialized successfully")
    except Exception:

        pass
        # If initialization fails with a specific type, fall back to in-memory
        if not isinstance(_memory_manager, InMemoryMemoryManager):
            logger.warning(f"Falling back to in-memory implementation after error: {str(e)}")
            namespace = settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}"
            _memory_manager = InMemoryMemoryManager(namespace=namespace)
            await _memory_manager.initialize()
        else:
            # If even the in-memory manager fails, re-raise
            raise MemoryOperationError(f"Failed to initialize memory manager: {str(e)}", original_error=e)

    # Perform a health check
    if hasattr(_memory_manager, "health_check"):
        try:

            pass
            health_info = await _memory_manager.health_check()
            logger.info(f"Memory manager health check: {health_info}")
        except Exception:

            pass
            logger.warning(f"Memory manager health check failed: {str(e)}")

@error_boundary(log_to_monitoring=True)
async def close_memory_manager() -> None:
    """
    """
            logger.info(f"Closing memory manager: {type(_memory_manager).__name__}")
            await _memory_manager.close()
            logger.info("Memory manager closed successfully")
        except Exception:

            pass
            logger.error(f"Error closing memory manager: {str(e)}")
        finally:
            _memory_manager = None

@error_boundary(fallback_value=None, propagate_types=[MemoryError], log_to_monitoring=True)
async def get_memory_service(
    settings: Settings = Depends(get_settings),
) -> "MemoryService":
    """
    """
                raise DependencyError("Hexagonal architecture components are not available")

            # Determine storage type and configuration based on settings
            if (
                settings.ENVIRONMENT in ["prod", "production", "stage", "staging"]
                and settings.get_vultr_project_id() is not None
            ):
                storage_type = "mongodb"
                storage_config = {
                    "project_id": settings.get_vultr_project_id(),
                    "credentials_path": settings.get_vultr_credentials_path(),
                    "namespace": settings.MONGODB_NAMESPACE or f"cherry_ai-{settings.ENVIRONMENT}",
                }
            else:
                # Use in-memory implementation for development
                storage_type = "memory"
                storage_config = {"namespace": f"cherry_ai-{settings.ENVIRONMENT}"}

            logger.info(f"Creating memory service with {storage_type} storage adapter")

            # Create the memory service with the appropriate storage adapter
            try:

                pass
                _memory_service = await MemoryServiceFactory.create_memory_service(
                    storage_type=storage_type, config=storage_config
                )
                logger.info(f"Memory service initialized with {storage_type} storage adapter")
            except Exception:

                pass
                # If specific adapter fails, try with memory adapter
                if storage_type != "memory":
                    logger.warning(f"Failed to initialize {storage_type} adapter, falling back to memory adapter")
                    _memory_service = await MemoryServiceFactory.create_memory_service(
                        storage_type="memory",
                        config={"namespace": f"cherry_ai-{settings.ENVIRONMENT}"},
                    )
                    logger.info("Memory service initialized with memory adapter as fallback")
                else:
                    # Re-raise if even memory adapter fails
                    raise MemoryOperationError(
                        f"Failed to initialize memory adapter: {str(adapter_error)}",
                        original_error=adapter_error,
                    )

        except Exception:


            pass
            logger.error(f"Failed to create memory service with hexagonal architecture: {str(e)}")
            logger.warning("Creating simple wrapper service around legacy memory manager")

            # Fall back to using the legacy memory manager with a wrapper
            try:

                pass
                memory_manager = await get_memory_manager(settings)
                if memory_manager is None:
                    raise MemoryError("Failed to get memory manager for wrapper service")

                # Create a simple MemoryService that uses the legacy memory manager
                _memory_service = MemoryService(memory_manager)
                await _memory_service.initialize()
                logger.info("Memory service initialized with legacy wrapper")
            except Exception:

                pass
                logger.error(f"Failed to create wrapper service: {str(wrapper_error)}")
                raise MemoryOperationError(
                    f"Failed to create any memory service: {str(wrapper_error)}",
                    original_error=wrapper_error,
                )

    return _memory_service

@error_boundary(log_to_monitoring=True)
async def close_memory_service() -> None:
    """
    """
            logger.info("Closing memory service")
            await _memory_service.close()
            logger.info("Memory service closed successfully")
        except Exception:

            pass
            logger.error(f"Error closing memory service: {str(e)}")
        finally:
            _memory_service = None
