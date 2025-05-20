"""
Memory manager dependency for AI Orchestration System.

This module provides the dependency injection functions for memory management,
supporting both the legacy MemoryManager and the new hexagonal architecture
with MemoryService and storage adapters.
"""

import logging
import os
from typing import Optional, Dict, Any, Union
import asyncio
from functools import lru_cache
from fastapi import Depends

# Configure logging first, before it's used
logger = logging.getLogger(__name__)

# Import error handling utilities and exceptions
from core.orchestrator.src.utils.error_handling import error_boundary, retry
from core.orchestrator.src.exceptions import (
    MemoryError,
    MemoryConnectionError,
    MemoryOperationError,
    DependencyError,
)

# Import settings
from core.orchestrator.src.config.settings import Settings, get_settings

# Import required components - moved to functions to avoid circular imports
# Use flag variables to track availability
MEMORY_MANAGER_AVAILABLE = False
FIRESTORE_AVAILABLE = False
HEX_ARCH_AVAILABLE = False
USE_STUBS = False


# Initialize imports safely
def _initialize_imports():
    """Initialize imports and set availability flags."""
    global MEMORY_MANAGER_AVAILABLE, FIRESTORE_AVAILABLE, HEX_ARCH_AVAILABLE, USE_STUBS

    # Import the memory manager interface and implementations
    try:
        logger.info(
            "Attempting to import memory managers from packages.shared.src.memory"
        )
        # Importing here to avoid module-level imports that could cause circular dependencies
        global MemoryManager, InMemoryMemoryManager
        from packages.shared.src.memory.memory_manager import MemoryManager
        from packages.shared.src.memory.memory_manager import InMemoryMemoryManager

        MEMORY_MANAGER_AVAILABLE = True
        logger.info("Successfully imported memory managers")

        # Try to import the Firestore adapter
        try:
            logger.info("Attempting to import FirestoreMemoryAdapter")
            global FirestoreMemoryAdapter
            from packages.shared.src.memory.firestore_adapter import (
                FirestoreMemoryAdapter,
            )

            FIRESTORE_AVAILABLE = True
            logger.info("Successfully imported FirestoreMemoryAdapter")
        except ImportError as e:
            logger.warning(
                f"Failed to import FirestoreMemoryAdapter, Firestore storage will not be available: {str(e)}"
            )
            FIRESTORE_AVAILABLE = False

        # Using main implementation, not stubs
        USE_STUBS = False

    except ImportError as e:
        logger.warning(
            f"Failed to import memory managers from packages.shared.src.memory, falling back to stub implementation: {str(e)}"
        )

        # Try to import base memory manager and stubs
        try:
            global MemoryManager, InMemoryMemoryManager
            from packages.shared.src.memory.memory_manager import MemoryManager
            from packages.shared.src.memory.stubs import (
                InMemoryMemoryManagerStub as InMemoryMemoryManager,
            )

            MEMORY_MANAGER_AVAILABLE = True
            FIRESTORE_AVAILABLE = False
            USE_STUBS = True
            logger.info("Using stub memory manager implementation")
        except ImportError as stub_error:
            logger.error(
                f"Failed to import even stub memory managers: {str(stub_error)}"
            )
            MEMORY_MANAGER_AVAILABLE = False

    # Import hexagonal architecture components
    try:
        logger.info(
            "Attempting to import hexagonal architecture components for memory service"
        )
        global MemoryService, MemoryServiceFactory, FirestoreStorageAdapter, PostgresStorageAdapter
        from packages.shared.src.memory.services.memory_service import MemoryService
        from packages.shared.src.memory.services.memory_service_factory import (
            MemoryServiceFactory,
        )
        from packages.shared.src.memory.adapters.firestore_adapter import (
            FirestoreStorageAdapter,
        )
        from packages.shared.src.memory.adapters.postgres_adapter import (
            PostgresStorageAdapter,
        )

        HEX_ARCH_AVAILABLE = True
        logger.info("Successfully imported hexagonal architecture components")
    except ImportError as e:
        logger.warning(
            f"Failed to import hexagonal architecture components, falling back to legacy implementation: {str(e)}"
        )
        HEX_ARCH_AVAILABLE = False


# Initialize imports
_initialize_imports()

# Global memory manager and service instances (using type hints)
_memory_manager: Optional["MemoryManager"] = None
_memory_service: Optional["MemoryService"] = None


@error_boundary(
    fallback_value=None, propagate_types=[MemoryError], log_to_monitoring=True
)
def create_memory_manager(settings: Settings) -> "MemoryManager":
    """
    Create a memory manager instance based on settings.

    This function selects the appropriate memory manager based on
    environment and configuration, but does not initialize it.
    Initialization happens in the application's lifespan event.

    Args:
        settings: Application settings

    Returns:
        A memory manager instance (not initialized)

    Raises:
        MemoryError: If unable to create any memory manager
        DependencyError: If memory manager components are not available
    """
    if not MEMORY_MANAGER_AVAILABLE:
        raise DependencyError("Memory manager components are not available")

    # Determine if we need cloud storage based on environment and project ID
    use_firestore = (
        settings.ENVIRONMENT in ["prod", "production", "stage", "staging"]
        and settings.get_gcp_project_id() is not None
        and FIRESTORE_AVAILABLE
    )

    # Use Firestore if available and configured
    if use_firestore:
        try:
            logger.info(
                f"Creating Firestore memory adapter for environment: {settings.ENVIRONMENT}"
            )
            return FirestoreMemoryAdapter(
                project_id=settings.get_gcp_project_id(),
                credentials_path=settings.get_gcp_credentials_path(),
                namespace=settings.FIRESTORE_NAMESPACE
                or f"orchestra-{settings.ENVIRONMENT}",
            )
        except Exception as e:
            logger.error(f"Failed to create Firestore memory adapter: {str(e)}")
            logger.warning("Falling back to in-memory implementation")
            # Convert general exception to a specific memory error
            raise MemoryConnectionError(
                f"Failed to connect to Firestore: {str(e)}", original_error=e
            )

    # Use in-memory implementation
    namespace = settings.FIRESTORE_NAMESPACE or f"orchestra-{settings.ENVIRONMENT}"
    logger.info(f"Using in-memory memory manager with namespace: {namespace}")
    return InMemoryMemoryManager(namespace=namespace)


@error_boundary(
    fallback_value=None, propagate_types=[MemoryError], log_to_monitoring=True
)
async def get_memory_manager(
    settings: Settings = Depends(get_settings),
) -> "MemoryManager":
    """
    Get an initialized memory manager instance.

    This dependency function creates and initializes a memory manager
    if one doesn't exist, or returns the existing one.

    Args:
        settings: Application settings

    Returns:
        An initialized memory manager

    Raises:
        MemoryError: If unable to initialize the memory manager
        DependencyError: If memory manager components are not available
    """
    global _memory_manager

    if not MEMORY_MANAGER_AVAILABLE:
        raise DependencyError("Memory manager components are not available")

    # Create the memory manager if it doesn't exist
    if _memory_manager is None:
        try:
            _memory_manager = create_memory_manager(settings)
        except MemoryError as e:
            # If we can't create the Firestore adapter, fall back to in-memory
            logger.warning(f"Creating in-memory manager due to error: {str(e)}")
            namespace = (
                settings.FIRESTORE_NAMESPACE or f"orchestra-{settings.ENVIRONMENT}"
            )
            _memory_manager = InMemoryMemoryManager(namespace=namespace)

        try:
            # Initialize the memory manager
            await _memory_manager.initialize()
            logger.info(f"Memory manager initialized: {type(_memory_manager).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {str(e)}")
            # Fall back to in-memory if initialization fails
            if not isinstance(_memory_manager, InMemoryMemoryManager):
                logger.warning("Falling back to in-memory implementation")
                try:
                    namespace = (
                        settings.FIRESTORE_NAMESPACE
                        or f"orchestra-{settings.ENVIRONMENT}"
                    )
                    _memory_manager = InMemoryMemoryManager(namespace=namespace)
                    await _memory_manager.initialize()
                except Exception as fallback_error:
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
    Initialize the memory manager during application startup.

    Args:
        settings: Optional application settings

    Raises:
        MemoryError: If unable to initialize the memory manager
    """
    global _memory_manager

    if not MEMORY_MANAGER_AVAILABLE:
        logger.error("Memory manager components are not available")
        return

    if settings is None:
        settings = get_settings()

    # Create the memory manager if it doesn't exist
    if _memory_manager is None:
        try:
            _memory_manager = create_memory_manager(settings)
        except MemoryError as e:
            # If we can't create the preferred adapter, fall back to in-memory
            logger.warning(f"Creating in-memory manager due to error: {str(e)}")
            namespace = (
                settings.FIRESTORE_NAMESPACE or f"orchestra-{settings.ENVIRONMENT}"
            )
            _memory_manager = InMemoryMemoryManager(namespace=namespace)

    # Initialize the memory manager
    try:
        logger.info(f"Initializing memory manager: {type(_memory_manager).__name__}")
        await _memory_manager.initialize()
        logger.info("Memory manager initialized successfully")
    except Exception as e:
        # If initialization fails with a specific type, fall back to in-memory
        if not isinstance(_memory_manager, InMemoryMemoryManager):
            logger.warning(
                f"Falling back to in-memory implementation after error: {str(e)}"
            )
            namespace = (
                settings.FIRESTORE_NAMESPACE or f"orchestra-{settings.ENVIRONMENT}"
            )
            _memory_manager = InMemoryMemoryManager(namespace=namespace)
            await _memory_manager.initialize()
        else:
            # If even the in-memory manager fails, re-raise
            raise MemoryOperationError(
                f"Failed to initialize memory manager: {str(e)}", original_error=e
            )

    # Perform a health check
    if hasattr(_memory_manager, "health_check"):
        try:
            health_info = await _memory_manager.health_check()
            logger.info(f"Memory manager health check: {health_info}")
        except Exception as e:
            logger.warning(f"Memory manager health check failed: {str(e)}")


@error_boundary(log_to_monitoring=True)
async def close_memory_manager() -> None:
    """
    Close the memory manager during application shutdown.
    """
    global _memory_manager

    if _memory_manager is not None:
        try:
            logger.info(f"Closing memory manager: {type(_memory_manager).__name__}")
            await _memory_manager.close()
            logger.info("Memory manager closed successfully")
        except Exception as e:
            logger.error(f"Error closing memory manager: {str(e)}")
        finally:
            _memory_manager = None


@error_boundary(
    fallback_value=None, propagate_types=[MemoryError], log_to_monitoring=True
)
async def get_memory_service(
    settings: Settings = Depends(get_settings),
) -> "MemoryService":
    """
    Get an initialized memory service instance.

    This dependency function creates and initializes a memory service
    following the hexagonal architecture pattern, with the appropriate
    storage adapter based on the environment.

    Args:
        settings: Application settings

    Returns:
        An initialized memory service

    Raises:
        MemoryError: If unable to create or initialize the memory service
        DependencyError: If hexagonal architecture components are not available
    """
    global _memory_service

    # Create the memory service if it doesn't exist
    if _memory_service is None:
        try:
            # Check if hexagonal architecture components are available
            if not HEX_ARCH_AVAILABLE:
                raise DependencyError(
                    "Hexagonal architecture components are not available"
                )

            # Determine storage type and configuration based on settings
            if (
                settings.ENVIRONMENT in ["prod", "production", "stage", "staging"]
                and settings.get_gcp_project_id() is not None
            ):
                storage_type = "firestore"
                storage_config = {
                    "project_id": settings.get_gcp_project_id(),
                    "credentials_path": settings.get_gcp_credentials_path(),
                    "namespace": settings.FIRESTORE_NAMESPACE
                    or f"orchestra-{settings.ENVIRONMENT}",
                }
            else:
                # Use in-memory implementation for development
                storage_type = "memory"
                storage_config = {"namespace": f"orchestra-{settings.ENVIRONMENT}"}

            logger.info(f"Creating memory service with {storage_type} storage adapter")

            # Create the memory service with the appropriate storage adapter
            try:
                _memory_service = await MemoryServiceFactory.create_memory_service(
                    storage_type=storage_type, config=storage_config
                )
                logger.info(
                    f"Memory service initialized with {storage_type} storage adapter"
                )
            except Exception as adapter_error:
                # If specific adapter fails, try with memory adapter
                if storage_type != "memory":
                    logger.warning(
                        f"Failed to initialize {storage_type} adapter, falling back to memory adapter"
                    )
                    _memory_service = await MemoryServiceFactory.create_memory_service(
                        storage_type="memory",
                        config={"namespace": f"orchestra-{settings.ENVIRONMENT}"},
                    )
                    logger.info(
                        "Memory service initialized with memory adapter as fallback"
                    )
                else:
                    # Re-raise if even memory adapter fails
                    raise MemoryOperationError(
                        f"Failed to initialize memory adapter: {str(adapter_error)}",
                        original_error=adapter_error,
                    )

        except Exception as e:
            logger.error(
                f"Failed to create memory service with hexagonal architecture: {str(e)}"
            )
            logger.warning(
                "Creating simple wrapper service around legacy memory manager"
            )

            # Fall back to using the legacy memory manager with a wrapper
            try:
                memory_manager = await get_memory_manager(settings)
                if memory_manager is None:
                    raise MemoryError(
                        "Failed to get memory manager for wrapper service"
                    )

                # Create a simple MemoryService that uses the legacy memory manager
                _memory_service = MemoryService(memory_manager)
                await _memory_service.initialize()
                logger.info("Memory service initialized with legacy wrapper")
            except Exception as wrapper_error:
                logger.error(f"Failed to create wrapper service: {str(wrapper_error)}")
                raise MemoryOperationError(
                    f"Failed to create any memory service: {str(wrapper_error)}",
                    original_error=wrapper_error,
                )

    return _memory_service


@error_boundary(log_to_monitoring=True)
async def close_memory_service() -> None:
    """
    Close the memory service during application shutdown.
    """
    global _memory_service

    if _memory_service is not None:
        try:
            logger.info("Closing memory service")
            await _memory_service.close()
            logger.info("Memory service closed successfully")
        except Exception as e:
            logger.error(f"Error closing memory service: {str(e)}")
        finally:
            _memory_service = None
