"""
Workload Identity Federation (WIF) Implementation

This package provides a comprehensive solution for implementing
Workload Identity Federation between GitHub Actions and Google Cloud Platform.
It eliminates the need for storing service account keys in GitHub Secrets
and improves security by using short-lived credentials.
"""

__version__ = "0.1.0"

from . import config_models
from . import error_handler
from . import template_manager
from . import enhanced_template_manager
from . import cicd_manager
from . import setup_wif_cli

# Expose key classes and functions for easy import
from .config_models import (
    AuthMethod,
    GCPProjectConfig,
    GitHubConfig,
    RepositoryConfig,
    WIFImplementationConfig,
    WorkloadIdentityConfig,
)
from .enhanced_template_manager import EnhancedTemplateManager, create_template_manager
from .error_handler import ErrorSeverity, WIFError, handle_exception, safe_execute
from .setup_wif_cli import main as setup_wif

__all__ = [
    # Modules
    "config_models",
    "error_handler",
    "template_manager",
    "enhanced_template_manager",
    "cicd_manager",
    "setup_wif_cli",
    # Classes
    "AuthMethod",
    "EnhancedTemplateManager",
    "ErrorSeverity",
    "GCPProjectConfig",
    "GitHubConfig",
    "RepositoryConfig",
    "WIFError",
    "WIFImplementationConfig",
    "WorkloadIdentityConfig",
    # Functions
    "create_template_manager",
    "handle_exception",
    "safe_execute",
    "setup_wif",
]
