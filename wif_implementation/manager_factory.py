"""
Manager factory for WIF implementation.

This module provides a factory for creating managers for the WIF implementation.
It ensures proper dependency injection and consistent configuration.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Type, TypeVar, Any, Union, cast

from .config import WIFConfig
from .error_handler import handle_exception, WIFError, ErrorSeverity

# Import manager interfaces
from .managers.base_manager import BaseManager
from .managers.vulnerability_manager import VulnerabilityManager
from .managers.cicd_manager import CICDManager
from .managers.migration_manager import MigrationManager

logger = logging.getLogger(__name__)

# Type variable for manager types
T = TypeVar('T', bound=BaseManager)


class ManagerFactory:
    """
    Factory for creating managers for the WIF implementation.
    
    This class provides a factory for creating managers with proper
    dependency injection and consistent configuration.
    """
    
    def __init__(
        self,
        config: Optional[WIFConfig] = None,
        base_path: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize the manager factory.
        
        Args:
            config: The WIF configuration
            base_path: The base path for the WIF implementation
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode
        """
        self.config = config or WIFConfig()
        self.base_path = Path(base_path) if base_path else Path(".")
        self.verbose = verbose
        self.dry_run = dry_run
        self._managers: Dict[str, BaseManager] = {}
        
        if self.verbose:
            logger.setLevel(logging.DEBUG)
    
    @handle_exception(logger=logger)
    def get_manager(self, manager_class: Type[T]) -> T:
        """
        Get a manager instance.
        
        This method returns a cached manager instance if available,
        or creates a new one if not.
        
        Args:
            manager_class: The manager class to get
            
        Returns:
            A manager instance
            
        Raises:
            WIFError: If the manager class is not supported
        """
        manager_name = manager_class.__name__
        
        # Return cached manager if available
        if manager_name in self._managers:
            return cast(T, self._managers[manager_name])
        
        # Create a new manager instance
        try:
            manager = manager_class(
                base_path=self.base_path,
                verbose=self.verbose,
                dry_run=self.dry_run,
            )
            self._managers[manager_name] = manager
            logger.debug(f"Created new manager: {manager_name}")
            return manager
        except Exception as e:
            logger.error(f"Error creating manager {manager_name}: {str(e)}")
            raise WIFError(
                message=f"Failed to create manager: {manager_name}",
                severity=ErrorSeverity.ERROR,
                details={"manager_class": manager_name, "error": str(e)},
                cause=e,
            )
    
    def get_vulnerability_manager(self) -> VulnerabilityManager:
        """
        Get a vulnerability manager instance.
        
        Returns:
            A vulnerability manager instance
        """
        return self.get_manager(VulnerabilityManager)
    
    def get_cicd_manager(self) -> CICDManager:
        """
        Get a CICD manager instance.
        
        Returns:
            A CICD manager instance
        """
        return self.get_manager(CICDManager)
    
    def get_migration_manager(self) -> MigrationManager:
        """
        Get a migration manager instance.
        
        Returns:
            A migration manager instance
        """
        return self.get_manager(MigrationManager)
    
    def clear_cache(self) -> None:
        """Clear the manager cache."""
        self._managers.clear()
        logger.debug("Cleared manager cache")


# Global factory instance for convenience
_factory: Optional[ManagerFactory] = None


def get_manager_factory(
    config: Optional[WIFConfig] = None,
    base_path: Optional[Union[str, Path]] = None,
    verbose: bool = False,
    dry_run: bool = False,
) -> ManagerFactory:
    """
    Get the global manager factory instance.
    
    This function returns the global manager factory instance,
    creating it if necessary.
    
    Args:
        config: The WIF configuration
        base_path: The base path for the WIF implementation
        verbose: Whether to enable verbose logging
        dry_run: Whether to run in dry-run mode
        
    Returns:
        The global manager factory instance
    """
    global _factory
    
    if _factory is None:
        _factory = ManagerFactory(
            config=config,
            base_path=base_path,
            verbose=verbose,
            dry_run=dry_run,
        )
    
    return _factory


def reset_manager_factory() -> None:
    """Reset the global manager factory instance."""
    global _factory
    _factory = None
    logger.debug("Reset global manager factory")