"""
Enhanced Service Registry for AI Orchestration System.

This module provides an improved registry for managing service lifecycles,
with support for dependency injection, service type lookup, and async operations.
"""

import asyncio
import logging
from abc import ABC
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
)

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for services
T = TypeVar("T")
S = TypeVar("S")


class Service(ABC):
    """
    Base interface for services managed by the registry.

    While not required for registration, implementing this interface
    ensures consistent lifecycle management and better type checking.
    """

    def initialize(self) -> None:
        """Initialize the service (synchronous)."""

    async def initialize_async(self) -> None:
        """Initialize the service asynchronously."""

    def close(self) -> None:
        """Release resources held by the service (synchronous)."""

    async def close_async(self) -> None:
        """Release resources held by the service asynchronously."""


class ServiceFactory(Generic[T]):
    """
    Factory for creating service instances.

    This class enables lazy initialization of services and
    simplifies dependency injection in a type-safe manner.
    """

    def __init__(self, factory_func: Callable[[], T]):
        """
        Initialize the service factory.

        Args:
            factory_func: Function that creates and returns a service instance
        """
        self._factory_func = factory_func
        self._instance: Optional[T] = None

    def get_instance(self) -> T:
        """
        Get the service instance, creating it if necessary.

        Returns:
            The service instance
        """
        if self._instance is None:
            self._instance = self._factory_func()
        return self._instance

    def reset(self) -> None:
        """
        Reset the factory, clearing any existing instance.

        This forces the factory to create a new instance next time get_instance is called.
        """
        self._instance = None


class EnhancedServiceRegistry:
    """
    Enhanced registry for tracking and managing services with type support.

    This class improves on the basic ServiceRegistry with:
    1. Service lookup by type
    2. Support for service factories
    3. Asynchronous initialization and cleanup
    4. Improved error reporting
    5. Better dependency management
    """

    def __init__(self):
        """Initialize the enhanced service registry."""
        # Track services both by instance and by type
        self._services: List[Any] = []
        self._service_by_type: Dict[Type[Any], Any] = {}
        self._service_factories: Dict[Type[Any], ServiceFactory[Any]] = {}
        self._service_ids: Set[int] = set()  # Track service object IDs to prevent duplicates

        logger.debug("EnhancedServiceRegistry initialized")

    def register(self, service: T) -> T:
        """
        Register a service with the registry.

        Args:
            service: The service to register

        Returns:
            The registered service (for chaining)

        Raises:
            ValueError: If the service is already registered
        """
        service_id = id(service)
        service_type = type(service)

        # Check if service is already registered
        if service_id in self._service_ids:
            logger.warning(f"Service {service_type.__name__} is already registered")
            return service

        # Register the service
        self._services.append(service)
        self._service_ids.add(service_id)

        # Also register by concrete type if not already registered
        if service_type not in self._service_by_type:
            self._service_by_type[service_type] = service

        # Register by each base class/interface that it implements
        for base_class in service_type.__mro__[1:]:  # Skip the class itself
            if base_class not in (object, ABC) and base_class not in self._service_by_type:
                self._service_by_type[base_class] = service

        logger.debug(f"Registered service: {service_type.__name__}")
        return service

    def register_factory(
        self, service_type: Type[T], factory: Union[ServiceFactory[T], Callable[[], T]]
    ) -> ServiceFactory[T]:
        """
        Register a factory for a service type.

        Args:
            service_type: The type of service this factory creates
            factory: Factory object or function that creates the service

        Returns:
            The registered service factory
        """
        # Convert callable to ServiceFactory if needed
        if callable(factory) and not isinstance(factory, ServiceFactory):
            factory = ServiceFactory(factory)

        self._service_factories[service_type] = factory
        logger.debug(f"Registered service factory for: {service_type.__name__}")

        return factory

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service by type.

        This method will:
        1. Return a directly registered service of the requested type if available
        2. Try to create the service using a registered factory if available
        3. Return None if the service cannot be found or created

        Args:
            service_type: The type of service to retrieve

        Returns:
            The requested service, or None if not found
        """
        # Check for directly registered services
        if service_type in self._service_by_type:
            return cast(T, self._service_by_type[service_type])

        # Try to create using a factory if available
        if service_type in self._service_factories:
            factory = self._service_factories[service_type]
            instance = factory.get_instance()

            # Register the created instance
            if instance is not None:
                self.register(instance)

            return instance

        return None

    def get_required_service(self, service_type: Type[T]) -> T:
        """
        Get a required service by type.

        Similar to get_service, but raises an exception if the service is not found.

        Args:
            service_type: The type of service to retrieve

        Returns:
            The requested service

        Raises:
            ValueError: If the service is not found
        """
        service = self.get_service(service_type)
        if service is None:
            raise ValueError(f"Required service of type {service_type.__name__} not found")
        return service

    def unregister(self, service: Any) -> bool:
        """
        Unregister a service from the registry.

        Args:
            service: The service to unregister

        Returns:
            True if the service was unregistered, False if it wasn't registered
        """
        service_id = id(service)
        service_type = type(service)

        if service_id in self._service_ids:
            # Remove from services list
            self._services = [s for s in self._services if id(s) != service_id]
            self._service_ids.remove(service_id)

            # Remove from type dictionary if it's the registered service for that type
            for type_key, registered_service in list(self._service_by_type.items()):
                if id(registered_service) == service_id:
                    del self._service_by_type[type_key]

            logger.debug(f"Unregistered service: {service_type.__name__}")
            return True
        else:
            logger.warning(f"Service {service_type.__name__} is not registered")
            return False

    def has_service(self, service_type: Type[T]) -> bool:
        """
        Check if a service of the specified type is available.

        Args:
            service_type: The type of service to check for

        Returns:
            True if the service is available, False otherwise
        """
        return service_type in self._service_by_type or service_type in self._service_factories

    async def initialize_all_async(self) -> Dict[str, str]:
        """
        Initialize all registered services asynchronously.

        This method will:
        1. Call initialize_async() on services that support it
        2. Fall back to initialize() in a thread pool for synchronous services

        Returns:
            Dictionary of service names to error messages for failed initializations
        """
        errors: Dict[str, str] = {}
        initialization_tasks = []

        logger.info(f"Initializing {len(self._services)} services asynchronously")

        for service in self._services:
            service_name = service.__class__.__name__

            # Check if the service supports async initialization
            if hasattr(service, "initialize_async") and callable(service.initialize_async):
                # Create tasks for async initialization
                task = asyncio.create_task(self._initialize_service_async(service, service_name))
                initialization_tasks.append(task)
            elif hasattr(service, "initialize") and callable(service.initialize):
                # For synchronous initialize methods, run in thread pool
                loop = asyncio.get_running_loop()
                task = asyncio.create_task(self._initialize_service_sync(service, service_name, loop))
                initialization_tasks.append(task)

        # Wait for all initialization tasks to complete
        results = await asyncio.gather(*initialization_tasks, return_exceptions=True)

        # Process results and collect errors
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                service_name, error = result
                if error:
                    errors[service_name] = error

        if errors:
            logger.warning(f"Service initialization completed with {len(errors)} errors")
        else:
            logger.info("All services initialized successfully")

        return errors

    async def _initialize_service_async(self, service: Any, service_name: str) -> tuple[str, Optional[str]]:
        """
        Initialize a service using its async initialize method.

        Args:
            service: The service to initialize
            service_name: Name of the service for error reporting

        Returns:
            Tuple of (service_name, error_message or None)
        """
        try:
            await service.initialize_async()
            logger.debug(f"Initialized service asynchronously: {service_name}")
            return service_name, None
        except Exception as e:
            error_msg = f"Failed to initialize service {service_name} asynchronously: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    async def _initialize_service_sync(
        self, service: Any, service_name: str, loop: asyncio.AbstractEventLoop
    ) -> tuple[str, Optional[str]]:
        """
        Initialize a service using its sync initialize method in a thread pool.

        Args:
            service: The service to initialize
            service_name: Name of the service for error reporting
            loop: The event loop to use for thread pool execution

        Returns:
            Tuple of (service_name, error_message or None)
        """
        try:
            # Run synchronous initialize in a thread pool
            await loop.run_in_executor(None, service.initialize)
            logger.debug(f"Initialized service in thread pool: {service_name}")
            return service_name, None
        except Exception as e:
            error_msg = f"Failed to initialize service {service_name} in thread pool: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    def initialize_all(self) -> Dict[str, str]:
        """
        Initialize all registered services synchronously.

        This calls initialize() on all services that support it.
        Services without initialize() are skipped.

        Returns:
            Dictionary of service names to error messages for failed initializations
        """
        errors: Dict[str, str] = {}

        logger.info(f"Initializing {len(self._services)} services")

        for service in self._services:
            service_name = service.__class__.__name__
            if hasattr(service, "initialize") and callable(service.initialize):
                try:
                    service.initialize()
                    logger.debug(f"Initialized service: {service_name}")
                except Exception as e:
                    error_msg = f"Failed to initialize service {service_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors[service_name] = error_msg
                    # Don't re-raise, we want to try initializing all services

        if errors:
            logger.warning(f"Service initialization completed with {len(errors)} errors")
        else:
            logger.info("All services initialized successfully")

        return errors

    async def close_all_async(self) -> Dict[str, str]:
        """
        Close all registered services asynchronously.

        This method will:
        1. Call close_async() on services that support it
        2. Fall back to close() in a thread pool for synchronous services
        3. Process services in reverse order (LIFO) to handle dependencies

        Returns:
            Dictionary of service names to error messages for failed closures
        """
        errors: Dict[str, str] = {}
        closure_tasks = []

        # Process in reverse order to handle dependencies correctly
        for service in reversed(self._services):
            service_name = service.__class__.__name__

            # Check if the service supports async closure
            if hasattr(service, "close_async") and callable(service.close_async):
                task = asyncio.create_task(self._close_service_async(service, service_name))
                closure_tasks.append(task)
            elif hasattr(service, "close") and callable(service.close):
                loop = asyncio.get_running_loop()
                task = asyncio.create_task(self._close_service_sync(service, service_name, loop))
                closure_tasks.append(task)

        # Wait for all closure tasks to complete
        results = await asyncio.gather(*closure_tasks, return_exceptions=True)

        # Process results and collect errors
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                service_name, error = result
                if error:
                    errors[service_name] = error

        # Reset registry state
        self._reset_registry()

        if errors:
            logger.warning(f"Service closure completed with {len(errors)} errors")
        else:
            logger.info("All services closed successfully")

        return errors

    async def _close_service_async(self, service: Any, service_name: str) -> tuple[str, Optional[str]]:
        """
        Close a service using its async close method.

        Args:
            service: The service to close
            service_name: Name of the service for error reporting

        Returns:
            Tuple of (service_name, error_message or None)
        """
        try:
            await service.close_async()
            logger.debug(f"Closed service asynchronously: {service_name}")
            return service_name, None
        except Exception as e:
            error_msg = f"Failed to close service {service_name} asynchronously: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    async def _close_service_sync(
        self, service: Any, service_name: str, loop: asyncio.AbstractEventLoop
    ) -> tuple[str, Optional[str]]:
        """
        Close a service using its sync close method in a thread pool.

        Args:
            service: The service to close
            service_name: Name of the service for error reporting
            loop: The event loop to use for thread pool execution

        Returns:
            Tuple of (service_name, error_message or None)
        """
        try:
            # Run synchronous close in a thread pool
            await loop.run_in_executor(None, service.close)
            logger.debug(f"Closed service in thread pool: {service_name}")
            return service_name, None
        except Exception as e:
            error_msg = f"Failed to close service {service_name} in thread pool: {e}"
            logger.error(error_msg, exc_info=True)
            return service_name, error_msg

    def close_all(self) -> Dict[str, str]:
        """
        Close all registered services synchronously.

        This calls close() on all services that support it,
        in reverse order of registration (LIFO).
        Services without close() are skipped.

        Returns:
            Dictionary of service names to error messages for failed closures
        """
        errors: Dict[str, str] = {}

        # Process in reverse order to handle dependencies correctly
        for service in reversed(self._services):
            service_name = service.__class__.__name__
            if hasattr(service, "close") and callable(service.close):
                try:
                    service.close()
                    logger.debug(f"Closed service: {service_name}")
                except Exception as e:
                    error_msg = f"Failed to close service {service_name}: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors[service_name] = error_msg

        # Reset registry state
        self._reset_registry()

        if errors:
            logger.warning(f"Service registry closed with {len(errors)} errors")
        else:
            logger.info("All services closed successfully")

        return errors

    def _reset_registry(self) -> None:
        """
        Reset the registry state, clearing all service references.

        This internal method is called after closing all services.
        """
        self._services = []
        self._service_by_type = {}
        self._service_ids = set()

        # Reset all factories but keep them registered
        for factory in self._service_factories.values():
            factory.reset()

    def get_service_count(self) -> int:
        """
        Get the number of registered services.

        Returns:
            The number of registered services
        """
        return len(self._services)

    def get_service_names(self) -> List[str]:
        """
        Get the names of all registered services.

        Returns:
            List of service class names
        """
        return [service.__class__.__name__ for service in self._services]


# Global enhanced service registry instance
_enhanced_service_registry = EnhancedServiceRegistry()


def get_enhanced_service_registry() -> EnhancedServiceRegistry:
    """
    Get the global enhanced service registry instance.

    This function provides a simple dependency injection mechanism
    for accessing the enhanced service registry throughout the application.

    Returns:
        The global EnhancedServiceRegistry instance
    """
    return _enhanced_service_registry


# Add type-safe helper functions
def register_service(service: T) -> T:
    """Register a service with the global registry."""
    return get_enhanced_service_registry().register(service)


def get_service(service_type: Type[T]) -> Optional[T]:
    """Get a service from the global registry by type."""
    return get_enhanced_service_registry().get_service(service_type)


def get_required_service(service_type: Type[T]) -> T:
    """Get a required service from the global registry by type."""
    return get_enhanced_service_registry().get_required_service(service_type)


def register_factory(service_type: Type[T], factory: Union[ServiceFactory[T], Callable[[], T]]) -> ServiceFactory[T]:
    """Register a service factory with the global registry."""
    return get_enhanced_service_registry().register_factory(service_type, factory)
