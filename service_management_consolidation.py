"""
Consolidated service management framework for the entire codebase.

This implementation provides a unified approach to service management across all modules,
combining the functionality from:
- gcp_migration/infrastructure/service_factory.py
- gcp_migration/infrastructure/service_container.py

Usage:
    1. Import the ServiceContainer or ServiceFactory class from this module
    2. Create an instance with the appropriate configuration
    3. Use the instance to manage services
"""

import inspect
import logging
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
)

# Import error handling from consolidated framework
from error_handling_consolidation import BaseError, ErrorSeverity, handle_exception

# Type variables
T = TypeVar("T")
S = TypeVar("S")

# Configure logging
logger = logging.getLogger(__name__)


class ServiceError(BaseError):
    """Exception raised when there is a service error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: The error message
            details: Additional details about the error
            cause: The underlying exception that caused this error
        """
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details,
            cause=cause,
        )


class ServiceScope(Enum):
    """Service scope types."""

    # Service is created once and reused throughout the application lifetime
    SINGLETON = "singleton"

    # Service is created for each request/operation and then discarded
    TRANSIENT = "transient"

    # Service is created for each scope/context and reused within that scope
    SCOPED = "scoped"


class ServiceLifecycle(Enum):
    """Service lifecycle events."""

    # Called when the service is constructed
    INITIALIZE = "initialize"

    # Called when the service is being used
    ACTIVATE = "activate"

    # Called when the service is being disposed
    DISPOSE = "dispose"


class ServiceRegistration(Generic[T]):
    """Registration information for a service."""

    def __init__(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        scope: ServiceScope = ServiceScope.TRANSIENT,
        lifecycle_hooks: Optional[Dict[ServiceLifecycle, Callable[[T], None]]] = None,
        dependencies: Optional[List[Type]] = None,
    ):
        """
        Initialize the service registration.

        Args:
            service_type: The type of service being registered
            factory: Factory function to create the service
            scope: The service scope
            lifecycle_hooks: Optional hooks for service lifecycle events
            dependencies: Optional list of service dependencies
        """
        self.service_type = service_type
        self.factory = factory
        self.scope = scope
        self.lifecycle_hooks = lifecycle_hooks or {}
        self.dependencies = dependencies or []


class ServiceFactory:
    """
    Factory for creating services.

    This class provides functionality to register and create services.
    """

    def __init__(self):
        """Initialize the service factory."""
        self.registrations: Dict[Type, ServiceRegistration] = {}
        self.instances: Dict[Type, Any] = {}

    def register(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        scope: ServiceScope = ServiceScope.TRANSIENT,
        lifecycle_hooks: Optional[Dict[ServiceLifecycle, Callable[[T], None]]] = None,
        dependencies: Optional[List[Type]] = None,
    ) -> None:
        """
        Register a service with the factory.

        Args:
            service_type: The type of service to register
            factory: Factory function to create the service
            scope: The service scope
            lifecycle_hooks: Optional hooks for service lifecycle events
            dependencies: Optional list of service dependencies
        """
        registration = ServiceRegistration(
            service_type=service_type,
            factory=factory,
            scope=scope,
            lifecycle_hooks=lifecycle_hooks,
            dependencies=dependencies,
        )

        self.registrations[service_type] = registration
        logger.debug(f"Registered service {service_type.__name__} with scope {scope.value}")

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance with the factory.

        Args:
            service_type: The type of service to register
            instance: The instance to register
        """
        self.instances[service_type] = instance
        logger.debug(f"Registered instance of {service_type.__name__}")

    @handle_exception(target_error=ServiceError)
    def create(self, service_type: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Create an instance of the specified service type.

        Args:
            service_type: The type of service to create
            *args: Positional arguments to pass to the factory
            **kwargs: Keyword arguments to pass to the factory

        Returns:
            An instance of the service

        Raises:
            ServiceError: If the service cannot be created
        """
        # Check if we already have an instance for singleton services
        if service_type in self.instances:
            return cast(T, self.instances[service_type])

        # Check if the service is registered
        if service_type not in self.registrations:
            raise ServiceError(
                f"Service {service_type.__name__} not registered",
                details={"service_type": service_type.__name__},
            )

        # Get the registration
        registration = self.registrations[service_type]

        # Create dependencies if needed
        dependency_instances = {}
        for dependency_type in registration.dependencies:
            dependency_instances[dependency_type] = self.create(dependency_type)

        # Create the service instance
        try:
            # Combine dependency instances with explicit args and kwargs
            combined_kwargs = {**dependency_instances, **kwargs}
            instance = registration.factory(*args, **combined_kwargs)
        except Exception as e:
            raise ServiceError(
                f"Failed to create service {service_type.__name__}",
                details={"service_type": service_type.__name__},
                cause=e,
            )

        # Call initialize hook if present
        if ServiceLifecycle.INITIALIZE in registration.lifecycle_hooks:
            try:
                registration.lifecycle_hooks[ServiceLifecycle.INITIALIZE](instance)
            except Exception as e:
                raise ServiceError(
                    f"Failed to initialize service {service_type.__name__}",
                    details={"service_type": service_type.__name__},
                    cause=e,
                )

        # Store instance if singleton
        if registration.scope == ServiceScope.SINGLETON:
            self.instances[service_type] = instance

        return instance

    def dispose(self) -> None:
        """Dispose of all singleton services."""
        for service_type, instance in list(self.instances.items()):
            if service_type in self.registrations:
                registration = self.registrations[service_type]

                # Call dispose hook if present
                if ServiceLifecycle.DISPOSE in registration.lifecycle_hooks:
                    try:
                        registration.lifecycle_hooks[ServiceLifecycle.DISPOSE](instance)
                    except Exception as e:
                        logger.warning(f"Error disposing service {service_type.__name__}: {str(e)}")

        # Clear instances
        self.instances.clear()


class ServiceContainer:
    """
    Container for services.

    This class provides a more robust approach to service management,
    with support for dependency injection and scoped services.
    """

    def __init__(self, parent: Optional["ServiceContainer"] = None):
        """
        Initialize the service container.

        Args:
            parent: Optional parent container for hierarchical resolution
        """
        self.factory = ServiceFactory()
        self.parent = parent
        self.scoped_containers: List["ServiceContainer"] = []
        self.is_disposed = False

    def register(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        scope: ServiceScope = ServiceScope.TRANSIENT,
        lifecycle_hooks: Optional[Dict[ServiceLifecycle, Callable[[T], None]]] = None,
        dependencies: Optional[List[Type]] = None,
    ) -> None:
        """
        Register a service with the container.

        Args:
            service_type: The type of service to register
            factory: Factory function to create the service
            scope: The service scope
            lifecycle_hooks: Optional hooks for service lifecycle events
            dependencies: Optional list of service dependencies
        """
        self.factory.register(
            service_type=service_type,
            factory=factory,
            scope=scope,
            lifecycle_hooks=lifecycle_hooks,
            dependencies=dependencies,
        )

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Register an existing instance with the container.

        Args:
            service_type: The type of service to register
            instance: The instance to register
        """
        self.factory.register_instance(service_type, instance)

    def register_auto_factory(
        self,
        concrete_type: Type[T],
        interface_type: Optional[Type[S]] = None,
        scope: ServiceScope = ServiceScope.TRANSIENT,
        lifecycle_hooks: Optional[Dict[ServiceLifecycle, Callable[[T], None]]] = None,
    ) -> None:
        """
        Register a service with automatic dependency resolution.

        Args:
            concrete_type: The concrete type to create
            interface_type: Optional interface type to register as
            scope: The service scope
            lifecycle_hooks: Optional hooks for service lifecycle events
        """
        # If no interface type is provided, use the concrete type
        service_type = interface_type or concrete_type

        # Get the constructor parameters
        constructor = concrete_type.__init__
        if not constructor:
            raise ServiceError(f"Cannot auto-register {concrete_type.__name__} without a constructor")

        signature = inspect.signature(constructor)
        dependency_types = []

        # Skip 'self' parameter
        for param in list(signature.parameters.values())[1:]:
            # If the parameter has a type annotation, add it to the dependencies
            if param.annotation != inspect.Parameter.empty:
                dependency_types.append(param.annotation)

        # Create a factory function that creates the concrete type with dependencies
        def auto_factory(**kwargs: Any) -> T:
            return concrete_type(**kwargs)

        # Register the service
        self.register(
            service_type=service_type,
            factory=auto_factory,
            scope=scope,
            lifecycle_hooks=lifecycle_hooks,
            dependencies=dependency_types,
        )

    @handle_exception(target_error=ServiceError)
    def resolve(self, service_type: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Resolve an instance of the specified service type.

        Args:
            service_type: The type of service to resolve
            *args: Positional arguments to pass to the factory
            **kwargs: Keyword arguments to pass to the factory

        Returns:
            An instance of the service

        Raises:
            ServiceError: If the service cannot be resolved
        """
        try:
            # Try to create the service from this container
            return self.factory.create(service_type, *args, **kwargs)
        except ServiceError:
            # If the service is not registered in this container, check the parent
            if self.parent:
                return self.parent.resolve(service_type, *args, **kwargs)

            # No parent or parent couldn't resolve, re-raise the error
            raise

    def create_scope(self) -> "ServiceContainer":
        """
        Create a scoped service container.

        Returns:
            A new scoped service container
        """
        scoped_container = ServiceContainer(parent=self)
        self.scoped_containers.append(scoped_container)
        return scoped_container

    def dispose(self) -> None:
        """Dispose of all services in this container and its children."""
        if self.is_disposed:
            return

        # Dispose of all scoped containers
        for container in self.scoped_containers:
            container.dispose()

        # Clear scoped containers
        self.scoped_containers.clear()

        # Dispose of the factory
        self.factory.dispose()

        self.is_disposed = True


# Factory functions for creating service containers
def create_container(parent: Optional[ServiceContainer] = None) -> ServiceContainer:
    """
    Create a service container.

    Args:
        parent: Optional parent container for hierarchical resolution

    Returns:
        A new service container
    """
    return ServiceContainer(parent=parent)


def create_factory() -> ServiceFactory:
    """
    Create a service factory.

    Returns:
        A new service factory
    """
    return ServiceFactory()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Define some example services
    class Database:
        def __init__(self, connection_string: str):
            self.connection_string = connection_string

        def connect(self) -> None:
            print(f"Connected to database: {self.connection_string}")

    class Repository:
        def __init__(self, database: Database):
            self.database = database

        def get_data(self) -> List[str]:
            self.database.connect()
            return ["Item 1", "Item 2", "Item 3"]

    class Service:
        def __init__(self, repository: Repository):
            self.repository = repository

        def process(self) -> None:
            data = self.repository.get_data()
            print(f"Processing {len(data)} items")

    # Create a container
    container = create_container()

    # Register services
    container.register(
        Database,
        lambda connection_string: Database(connection_string),
        scope=ServiceScope.SINGLETON,
    )

    container.register_auto_factory(
        Repository,
        scope=ServiceScope.SINGLETON,
    )

    container.register_auto_factory(
        Service,
        scope=ServiceScope.TRANSIENT,
    )

    # Resolve and use services
    database = container.resolve(Database, connection_string="localhost:5432")
    service = container.resolve(Service)
    service.process()

    print("Example complete")
