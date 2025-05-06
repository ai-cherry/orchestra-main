"""
Service Registry for AI Orchestration System.

This module provides a registry for managing service lifecycles,
ensuring proper initialization and cleanup of resources.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, Set

# Configure logging
logger = logging.getLogger(__name__)

# Generic type for services
T = TypeVar("T")


class ServiceRegistry:
    """
    Registry for tracking and managing services.

    This class provides a central registry for tracking services and their lifecycle,
    ensuring proper initialization and cleanup. It's designed to work with any
    services that have initialize() and close() methods.
    """

    def __init__(self):
        """Initialize the service registry."""
        self._services: List[Any] = []
        self._service_ids: Set[int] = (
            set()
        )  # Track service object IDs to prevent duplicates
        logger.debug("ServiceRegistry initialized")

    def register(self, service: Any) -> Any:
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

        # Check if service is already registered
        if service_id in self._service_ids:
            logger.warning(
                f"Service {service.__class__.__name__} is already registered"
            )
            return service

        # Register the service
        self._services.append(service)
        self._service_ids.add(service_id)
        logger.debug(f"Registered service: {service.__class__.__name__}")

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

        if service_id in self._service_ids:
            self._services = [s for s in self._services if id(s) != service_id]
            self._service_ids.remove(service_id)
            logger.debug(f"Unregistered service: {service.__class__.__name__}")
            return True
        else:
            logger.warning(f"Service {service.__class__.__name__} is not registered")
            return False

    def initialize_all(self) -> None:
        """
        Initialize all registered services.

        This calls initialize() on all services that support it.
        Services without initialize() are skipped.

        Returns:
            None
        """
        logger.info(f"Initializing {len(self._services)} services")

        for service in self._services:
            if hasattr(service, "initialize") and callable(service.initialize):
                try:
                    service.initialize()
                    logger.debug(f"Initialized service: {service.__class__.__name__}")
                except Exception as e:
                    logger.error(
                        f"Failed to initialize service {service.__class__.__name__}: {e}"
                    )
                    # Don't re-raise, we want to try initializing all services

    def close_all(self) -> List[str]:
        """
        Close all registered services.

        This calls close() on all services that support it,
        in reverse order of registration (LIFO).
        Services without close() are skipped.

        Returns:
            List of error messages if any services failed to close
        """
        errors = []

        # Process in reverse order to handle dependencies correctly
        for service in reversed(self._services):
            if hasattr(service, "close") and callable(service.close):
                try:
                    service.close()
                    logger.debug(f"Closed service: {service.__class__.__name__}")
                except Exception as e:
                    error_msg = (
                        f"Failed to close service {service.__class__.__name__}: {e}"
                    )
                    logger.error(error_msg)
                    errors.append(error_msg)

        # Clear the registry after closing all services
        self._services = []
        self._service_ids = set()

        if errors:
            logger.warning(f"Service registry closed with {len(errors)} errors")
        else:
            logger.info("All services closed successfully")

        return errors

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


# Global service registry instance
_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """
    Get the global service registry instance.

    This function provides a simple dependency injection mechanism
    for accessing the service registry throughout the application.

    Returns:
        The global ServiceRegistry instance
    """
    return _service_registry
