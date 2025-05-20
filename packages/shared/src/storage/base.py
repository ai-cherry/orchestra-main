"""
Base storage manager classes for the AI Orchestration System.

This module provides base classes for both synchronous and asynchronous
storage managers, defining common functionality and interfaces.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, Type

from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.exceptions import (
    StorageError,
    ConnectionError,
    OperationError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for operation result
T = TypeVar("T")


class BaseStorageManager(ABC):
    """
    Base class for all storage managers.

    This abstract class defines common functionality for storage managers,
    including configuration, initialization, and error handling.
    """

    def __init__(
        self, config: Optional[StorageConfig] = None, log_level: int = logging.INFO
    ):
        """
        Initialize the base storage manager.

        Args:
            config: Optional storage configuration
            log_level: Logging level for this instance
        """
        self.config = config or StorageConfig()
        self._initialized = False
        self._logger = self._setup_logger(log_level)

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """
        Set up a logger instance for this storage manager.

        Args:
            log_level: Logging level to use

        Returns:
            Configured logger instance
        """
        logger_name = f"{__name__}.{self.__class__.__name__}"
        instance_logger = logging.getLogger(logger_name)
        instance_logger.setLevel(log_level)
        return instance_logger

    def _get_collection_name(self, base_name: str) -> str:
        """
        Get a collection name using the configuration.

        Args:
            base_name: Base collection name

        Returns:
            Final collection name with all configuration applied
        """
        return self.config.get_collection_name(base_name)

    def check_initialized(self) -> None:
        """
        Check if the storage manager is initialized.

        Raises:
            RuntimeError: If the storage manager is not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                f"{self.__class__.__name__} not initialized. Call initialize() first."
            )

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the storage manager.

        This method should set up any necessary connections, create
        resources, or perform other initialization tasks.

        Raises:
            ConnectionError: If connection to the storage backend fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the storage manager and release resources.

        This method should clean up any resources used by the storage manager,
        such as database connections, file handles, etc.
        """
        pass

    def handle_operation_error(
        self, operation: str, error: Exception, message: Optional[str] = None
    ) -> None:
        """
        Handle an operation error in a standardized way.

        Args:
            operation: The name of the operation that failed
            error: The exception that was raised
            message: Optional additional message to include

        Raises:
            OperationError: A standardized operation error
        """
        error_message = message or str(error)
        self._logger.error(f"{operation} failed: {error_message}", exc_info=True)
        raise OperationError(operation, error_message, error)


class AsyncStorageManager(BaseStorageManager):
    """
    Base class for asynchronous storage managers.

    This abstract class extends BaseStorageManager with async-specific
    functionality and interfaces.
    """

    @abstractmethod
    async def initialize_async(self) -> None:
        """
        Initialize the storage manager asynchronously.

        This method should set up any necessary async connections and resources.

        Raises:
            ConnectionError: If connection to the storage backend fails
        """
        pass

    @abstractmethod
    async def close_async(self) -> None:
        """
        Close the storage manager and release resources asynchronously.

        This method should clean up any async resources used by the storage manager.
        """
        pass
