"""
Test Support Configuration for AI Orchestration System.

This module provides utilities for configuring the system in test mode,
allowing for better isolation and mocking during testing.
"""

import logging
import contextlib
from typing import Dict, Any, Optional, Generator, Callable

from core.orchestrator.src.config.config import Settings, get_settings

# Configure logging
logger = logging.getLogger(__name__)


class TestModeSettings(Settings):
    """
    Extended settings class with test mode support.

    This class adds testing-specific configuration settings without
    modifying the base Settings class, maintaining backward compatibility.
    """

    # Test mode flag
    TEST_MODE: bool = False

    # Test-specific overrides
    TEST_OVERRIDES: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """
        Override attribute access to support test overrides.

        Args:
            name: Attribute name

        Returns:
            Attribute value, potentially from test overrides

        Raises:
            AttributeError: If attribute not found
        """
        # Check for test override
        if self.TEST_MODE and name in self.TEST_OVERRIDES:
            return self.TEST_OVERRIDES[name]

        # Fall back to regular attribute access
        return super().__getattr__(name)


# Test mode context manager
@contextlib.contextmanager
def test_mode(
    enable: bool = True, overrides: Optional[Dict[str, Any]] = None
) -> Generator[TestModeSettings, None, None]:
    """
    Context manager for enabling test mode.

    This allows tests to temporarily modify system behavior
    without changing the global configuration.

    Args:
        enable: Whether to enable test mode
        overrides: Optional settings overrides for testing

    Yields:
        TestModeSettings instance with test mode enabled
    """
    # Store original settings instance
    original_settings = get_settings()

    try:
        # Create test settings
        test_settings = TestModeSettings(
            TEST_MODE=enable, TEST_OVERRIDES=overrides or {}
        )

        # Update all fields from original settings
        for key, value in original_settings.dict().items():
            if key not in {"TEST_MODE", "TEST_OVERRIDES"}:
                setattr(test_settings, key, value)

        # Temporarily replace global settings
        from core.orchestrator.src.config.config import _settings

        globals()["_settings"] = test_settings

        # Yield test settings
        yield test_settings

    finally:
        # Restore original settings
        from core.orchestrator.src.config.config import _settings

        globals()["_settings"] = original_settings


# Test mock utility functions
_mocked_services: Dict[str, Any] = {}


def register_test_mock(service_name: str, mock_instance: Any) -> None:
    """
    Register a mock service for testing.

    Args:
        service_name: Name of the service to mock
        mock_instance: Mock instance to use
    """
    _mocked_services[service_name] = mock_instance
    logger.debug(f"Registered test mock for '{service_name}'")


def get_test_mock(service_name: str) -> Optional[Any]:
    """
    Get a registered mock service.

    Args:
        service_name: Name of the mocked service

    Returns:
        Mock instance or None if not found
    """
    return _mocked_services.get(service_name)


def clear_test_mocks() -> None:
    """Clear all registered test mocks."""
    _mocked_services.clear()


def wrap_factory_for_testing(factory_func: Callable, service_name: str) -> Callable:
    """
    Wrap a service factory function to support test mocks.

    This allows seamless substitution of services with mocks during testing
    without modifying the original factory functions.

    Args:
        factory_func: Original factory function to wrap
        service_name: Name of the service for mock lookup

    Returns:
        Wrapped factory function
    """

    def wrapped_factory(*args, **kwargs):
        # Check for test mode and mocked service
        settings = get_settings()
        if isinstance(settings, TestModeSettings) and settings.TEST_MODE:
            mock = get_test_mock(service_name)
            if mock is not None:
                return mock

        # Fall back to original factory
        return factory_func(*args, **kwargs)

    return wrapped_factory
