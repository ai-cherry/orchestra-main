"""
Dependency Injection container for the GCP Migration toolkit.

This module provides a dependency injection container that manages
service dependencies and their lifecycle. This makes it easier to:
1. Test components in isolation by mocking dependencies
2. Swap implementations based on configuration
3. Centralize lifecycle management of services
"""

import inspect
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
    cast,
    get_type_hints,
)

from gcp_migration.utils.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")
TImpl = TypeVar("TImpl")


class DIContainer:
    """
    Dependency Injection container for managing service dependencies.

    This container provides a simple registry of interface to implementation
    mappings and resolves dependencies when requested.

    Example:
        ```python
        # Define interfaces and implementations
        class IDatabase(Protocol):
            def query(self, sql: str) -> List[Dict[str, Any]]: ...

        class PostgreSQLDatabase:
            def __init__(self, connection_string: str):
                self.connection_string = connection_string

            def query(self, sql: str) -> List[Dict[str, Any]]:
                # Implementation...
                return []

        # Set up container
        container = DIContainer()

        # Register a factory for database
        container.register_factory(
            IDatabase,
            lambda: PostgreSQLDatabase("postgresql://user:pass@localhost/db")
        )

        # Get database anywhere in the application
        db = container.resolve(IDatabase)
        results = db.query("SELECT * FROM users")
        ```
    """

    def __init__(self):
        """Initialize a new empty container."""
        self._registry: Dict[Type, Callable[..., Any]] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type[T], implementation: Type[TImpl]) -> None:
        """
        Register an implementation for an interface.

        Args:
            interface: The interface or abstract class
            implementation: The concrete implementation class
        """
        logger.debug(
            f"Registering implementation for {interface.__name__}: {implementation.__name__}"
        )
        self._registry[interface] = implementation

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """
        Register a singleton instance for an interface.

        Args:
            interface: The interface or abstract class
            instance: The singleton instance
        """
        logger.debug(f"Registering singleton instance for {interface.__name__}")
        self._singletons[interface] = instance

    def register_factory(self, interface: Type[T], factory: Callable[..., T]) -> None:
        """
        Register a factory function for an interface.

        Args:
            interface: The interface or abstract class
            factory: A factory function that creates instances
        """
        logger.debug(f"Registering factory for {interface.__name__}")
        self._registry[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve an implementation for the given interface.

        Args:
            interface: The interface to resolve

        Returns:
            An instance of the implementation

        Raises:
            KeyError: If no implementation is registered for the interface
            ValueError: If there's an error resolving dependencies
        """
        logger.debug(f"Resolving {interface.__name__}")

        # Check if we have a singleton instance
        if interface in self._singletons:
            return self._singletons[interface]

        # Check if we have a registered implementation
        if interface not in self._registry:
            raise KeyError(f"No implementation registered for {interface.__name__}")

        # Get the implementation or factory
        implementation = self._registry[interface]

        # If it's a callable factory, just call it
        if not inspect.isclass(implementation) and callable(implementation):
            return implementation()

        # If it's a class, we need to resolve its dependencies
        return self._create_instance(cast(Type, implementation))

    def _create_instance(self, implementation: Type[T]) -> T:
        """
        Create an instance of the implementation, resolving its dependencies.

        Args:
            implementation: The implementation class

        Returns:
            An instance of the implementation

        Raises:
            ValueError: If there's an error resolving dependencies
        """
        logger.debug(f"Creating instance of {implementation.__name__}")

        # Get constructor signature
        try:
            signature = inspect.signature(implementation.__init__)
            parameters = signature.parameters
        except (ValueError, TypeError):
            # No __init__ or it's not a callable
            return implementation()

        # Skip 'self' parameter
        parameters = {k: v for k, v in parameters.items() if k != "self"}

        # If no parameters, just instantiate
        if not parameters:
            return implementation()

        # Get type hints for parameters
        type_hints = get_type_hints(implementation.__init__)

        # Resolve constructor arguments
        kwargs: Dict[str, Any] = {}
        for name, param in parameters.items():
            # Skip if it has a default value and doesn't have to be provided
            if param.default is not param.empty:
                continue

            # Get the type hint for this parameter
            if name not in type_hints:
                raise ValueError(
                    f"Cannot resolve dependency for parameter '{name}' in {implementation.__name__}.__init__: "
                    f"No type hint provided"
                )

            param_type = type_hints[name]

            # Try to resolve the dependency
            try:
                kwargs[name] = self.resolve(param_type)
            except KeyError as e:
                raise ValueError(
                    f"Cannot resolve dependency for parameter '{name}' in {implementation.__name__}.__init__: "
                    f"No implementation registered for {param_type}"
                ) from e

        # Instantiate the implementation with resolved dependencies
        return implementation(**kwargs)


# Create a global container instance
container = DIContainer()
