"""
AI Orchestra System

A comprehensive framework for AI assistants to maintain real-time awareness of
development resources in a hybrid GCP-GitHub-Codespaces environment.

This package provides tools for resource discovery, configuration management,
conflict detection and resolution, and a unified API for AI assistants.
"""

__version__ = "0.1.0"

# Import main components for easier access
try:
    from orchestra_system.resource_registry import (
        ResourceType,
        ResourceStatus,
        Environment,
        Resource,
        get_registry,
        discover_resources,
        verify_resources,
    )
except ImportError:
    pass

try:
    from orchestra_system.config_manager import (
        ConfigEnvironment,
        ConfigSource,
        ConfigEntry,
        ConfigConflict,
        get_manager,
        get,
        set,
        get_all,
    )
except ImportError:
    pass

try:
    from orchestra_system.conflict_resolver import (
        ConflictType,
        ResolutionStrategy,
        ResolutionStatus,
        Conflict,
        Resolution,
        get_resolver,
        detect_conflicts,
        resolve_conflict,
        apply_resolution,
    )
except ImportError:
    pass

try:
    from orchestra_system.api import (
        OrchestraSystemAPI,
        get_api,
        initialize_system,
        get_context,
    )
except ImportError:
    pass
