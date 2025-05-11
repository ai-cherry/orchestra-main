"""
Workload Identity Federation (WIF) Implementation

This package provides a comprehensive implementation of the Workload Identity Federation (WIF)
enhancement plan for the AI Orchestra project.

The package is organized into the following modules:
- client: Main entry point for WIF operations
- config: Configuration for WIF implementation
- error_handler: Error handling utilities
- types: Type definitions and data models
- managers: Implementation managers for different phases
- utils: Utility functions for WIF implementation
"""

__version__ = "1.0.0"

# Export public API
from .client import WIFClient
from .config import WIFConfig, get_config
from .error_handler import WIFError, ErrorSeverity, handle_exception, safe_execute
from .types import (
    ImplementationPhase,
    TaskStatus,
    Task,
    ImplementationPlan,
    Vulnerability,
)

# For backward compatibility
from .managers.vulnerability_manager import VulnerabilityManager
from .managers.migration_manager import MigrationManager
from .managers.cicd_manager import CICDManager

__all__ = [
    # Main client
    "WIFClient",
    
    # Configuration
    "WIFConfig",
    "get_config",
    
    # Error handling
    "WIFError",
    "ErrorSeverity",
    "handle_exception",
    "safe_execute",
    
    # Types
    "ImplementationPhase",
    "TaskStatus",
    "Task",
    "ImplementationPlan",
    "Vulnerability",
    
    # Managers
    "VulnerabilityManager",
    "MigrationManager",
    "CICDManager",
]
