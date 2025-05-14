#!/usr/bin/env python3
"""
API for AI Orchestra System

This module provides a centralized API for AI assistants to interact with
the system components, including the resource registry, configuration manager,
and conflict resolver. It offers a unified interface for discovering resources,
managing configuration, and handling conflicts.

Key features:
- Resource discovery and awareness
- Configuration management across environments
- Conflict detection and resolution
- Context preservation via MCP memory
- Automated cleanup of development artifacts
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TypeVar, Generic, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestra-system-api")

# Import system components
try:
    from orchestra_system.resource_registry import (
        ResourceType, ResourceStatus, Environment, Resource, 
        get_registry, discover_resources, verify_resources
    )
except ImportError:
    logger.warning("Could not import resource registry, functionality will be limited")
    ResourceType = object
    ResourceStatus = object
    Environment = object
    Resource = object
    
    def get_registry(*args, **kwargs):
        return None
    
    async def discover_resources(*args, **kwargs):
        return []
    
    async def verify_resources(*args, **kwargs):
        return {}

try:
    from orchestra_system.config_manager import (
        ConfigEnvironment, ConfigSource, ConfigEntry, ConfigConflict,
        get_manager, get, set, get_all
    )
except ImportError:
    logger.warning("Could not import config manager, functionality will be limited")
    ConfigEnvironment = object
    ConfigSource = object
    ConfigEntry = object
    ConfigConflict = object
    
    def get_manager(*args, **kwargs):
        return None
    
    def get(*args, **kwargs):
        return None
    
    def set(*args, **kwargs):
        pass
    
    def get_all(*args, **kwargs):
        return {}

try:
    from orchestra_system.conflict_resolver import (
        ConflictType, ResolutionStrategy, ResolutionStatus, Conflict, Resolution,
        get_resolver, detect_conflicts, resolve_conflict, apply_resolution
    )
except ImportError:
    logger.warning("Could not import conflict resolver, functionality will be limited")
    ConflictType = object
    ResolutionStrategy = object
    ResolutionStatus = object
    Conflict = object
    Resolution = object
    
    def get_resolver(*args, **kwargs):
        return None
    
    def detect_conflicts(*args, **kwargs):
        return []
    
    def resolve_conflict(*args, **kwargs):
        return None
    
    def apply_resolution(*args, **kwargs):
        return False

# Try to import MCP client
try:
    from gcp_migration.mcp_client_enhanced import MCPClient, MCPResponse, get_client as get_mcp_client
except ImportError:
    logger.warning("Could not import enhanced MCP client, attempting to import basic client")
    try:
        from gcp_migration.mcp_client import MCPClient, get_client as get_mcp_client
    except ImportError:
        logger.error("Failed to import MCP client. API will operate in offline mode.")
        MCPClient = object
        
        def get_mcp_client(*args, **kwargs):
            return None


class OrchestraSystemAPI:
    """Unified API for AI Orchestra System components."""
    
    # MCP memory keys
    SYSTEM_STATE_KEY = "orchestra:system_state"
    CLEANUP_HISTORY_KEY = "orchestra:cleanup_history"
    
    def __init__(self, mcp_client: Optional[MCPClient] = None):
        """Initialize the API with system components.
        
        Args:
            mcp_client: An instance of MCPClient for accessing shared memory
        """
        self.mcp_client = mcp_client or get_mcp_client()
        
        # Initialize system components
        self.registry = get_registry(mcp_client=self.mcp_client)
        self.config_manager = get_manager(mcp_client=self.mcp_client)
        self.conflict_resolver = get_resolver(mcp_client=self.mcp_client)
        
        # System state
        self.system_state = {
            "initialized_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "components": {
                "resource_registry": self.registry is not None,
                "config_manager": self.config_manager is not None,
                "conflict_resolver": self.conflict_resolver is not None,
                "mcp_client": self.mcp_client is not None
            },
            "environment": self._detect_environment(),
            "resources_count": 0,
            "configs_count": 0,
            "conflicts_count": 0
        }
        
        # Load system state from MCP memory
        self._load_system_state()
    
    def _detect_environment(self) -> str:
        """Detect the current environment.
        
        Returns:
            Environment name
        """
        # Check for GitHub Codespaces
        if os.environ.get("CODESPACES") == "true":
            return "codespaces"
        
        # Check for GCP Cloud Run
        if os.environ.get("K_SERVICE"):
            return "gcp_cloud_run"
        
        # Check for GCP Workstation
        if os.environ.get("CLOUD_WORKSTATIONS_AGENT"):
            return "gcp_workstation"
        
        # Check for CI/CD
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            return "ci_cd"
        
        # Default to local
        return "local"
    
    def _load_system_state(self) -> None:
        """Load system state from MCP memory."""
        if not self.mcp_client:
            return
        
        try:
            state_response = self.mcp_client.get(self.SYSTEM_STATE_KEY)
            if state_response and state_response.success and state_response.value:
                self.system_state.update(state_response.value)
                logger.info("Loaded system state from MCP memory")
        except Exception as e:
            logger.error(f"Failed to load system state: {e}")
    
    def _save_system_state(self) -> bool:
        """Save system state to MCP memory.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.mcp_client:
            return False
        
        try:
            # Update timestamp
            self.system_state["updated_at"] = datetime.now().isoformat()
            
            # Save to MCP memory
            result = self.mcp_client.set(self.SYSTEM_STATE_KEY, self.system_state)
            return result and result.success
        except Exception as e:
            logger.error(f"Failed to save system state: {e}")
            return False
    
    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the system by discovering resources and configuration.
        
        Returns:
            System state
        """
        logger.info("Initializing AI Orchestra System")
        
        # Initialize components
        component_status = {}
        
        # Initialize resource registry
        if self.registry:
            try:
                resources = await discover_resources()
                resource_status = await verify_resources()
                
                component_status["resource_registry"] = {
                    "discovered_resources": len(resources),
                    "available_resources": sum(1 for status in resource_status.values() 
                                             if status == ResourceStatus.AVAILABLE),
                    "unavailable_resources": sum(1 for status in resource_status.values() 
                                               if status != ResourceStatus.AVAILABLE)
                }
                
                self.system_state["resources_count"] = len(resources)
            except Exception as e:
                logger.error(f"Failed to initialize resource registry: {e}")
                component_status["resource_registry"] = {"error": str(e)}
        else:
            component_status["resource_registry"] = {"error": "Resource registry not available"}
        
        # Initialize configuration manager
        if self.config_manager:
            try:
                config_count = self.config_manager.discover_configuration()
                is_valid, errors = self.config_manager.validate()
                
                component_status["config_manager"] = {
                    "discovered_configs": config_count,
                    "is_valid": is_valid,
                    "errors": errors
                }
                
                self.system_state["configs_count"] = config_count
            except Exception as e:
                logger.error(f"Failed to initialize configuration manager: {e}")
                component_status["config_manager"] = {"error": str(e)}
        else:
            component_status["config_manager"] = {"error": "Configuration manager not available"}
        
        # Initialize conflict resolver
        if self.conflict_resolver:
            try:
                conflicts = detect_conflicts()
                
                component_status["conflict_resolver"] = {
                    "detected_conflicts": len(conflicts),
                    "pending_conflicts": sum(1 for c in conflicts 
                                          if c.resolution_status == ResolutionStatus.PENDING),
                    "resolved_conflicts": sum(1 for c in conflicts 
                                           if c.resolution_status == ResolutionStatus.RESOLVED)
                }
                
                self.system_state["conflicts_count"] = len(conflicts)
            except Exception as e:
                logger.error(f"Failed to initialize conflict resolver: {e}")
                component_status["conflict_resolver"] = {"error": str(e)}
        else:
            component_status["conflict_resolver"] = {"error": "Conflict resolver not available"}
        
        # Update system state
        self.system_state["initialization_status"] = component_status
        self.system_state["initialized_at"] = datetime.now().isoformat()
        
        # Save to MCP memory
        self._save_system_state()
        
        return self.system_state
    
    async def get_system_state(self) -> Dict[str, Any]:
        """Get the current system state.
        
        Returns:
            System state
        """
        # Update counts
        if self.registry:
            try:
                resources = list(getattr(self.registry, "resources", {}).values())
                self.system_state["resources_count"] = len(resources)
            except:
                pass
        
        if self.config_manager:
            try:
                configs = self.config_manager.get_all()
                self.system_state["configs_count"] = len(configs)
            except:
                pass
        
        if self.conflict_resolver:
            try:
                conflicts = getattr(self.conflict_resolver, "conflicts", {})
                self.system_state["conflicts_count"] = len(conflicts)
            except:
                pass
        
        return self.system_state
    
    #
    # Resource Registry API
    #
    
    async def discover_resources(self) -> List[Dict[str, Any]]:
        """Discover resources in the current environment.
        
        Returns:
            List of discovered resources
        """
        if not self.registry:
            logger.error("Resource registry not available")
            return []
        
        try:
            resources = await discover_resources()
            
            # Convert to dicts for better serialization
            result = [r.to_dict() for r in resources]
            
            # Update system state
            self.system_state["resources_count"] = len(getattr(self.registry, "resources", {}))
            self._save_system_state()
            
            return result
        except Exception as e:
            logger.error(f"Failed to discover resources: {e}")
            return []
    
    async def get_resources(
        self,
        resource_type: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get resources with optional filtering.
        
        Args:
            resource_type: Filter by resource type
            environment: Filter by environment
            status: Filter by status
            tags: Filter by tags
            
        Returns:
            List of resources
        """
        if not self.registry:
            logger.error("Resource registry not available")
            return []
        
        try:
            # Convert string parameters to enums if needed
            resource_type_enum = None
            if resource_type and hasattr(ResourceType, resource_type.upper()):
                resource_type_enum = getattr(ResourceType, resource_type.upper())
            
            env_enum = None
            if environment and hasattr(Environment, environment.upper()):
                env_enum = getattr(Environment, environment.upper())
            
            status_enum = None
            if status and hasattr(ResourceStatus, status.upper()):
                status_enum = getattr(ResourceStatus, status.upper())
            
            # Get resources
            resources = self.registry.list_resources(
                resource_type=resource_type_enum,
                environment=env_enum,
                status=status_enum,
                tags=tags
            )
            
            # Convert to dicts for better serialization
            return [r.to_dict() for r in resources]
        except Exception as e:
            logger.error(f"Failed to get resources: {e}")
            return []
    
    async def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource by ID.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            Resource if found, None otherwise
        """
        if not self.registry:
            logger.error("Resource registry not available")
            return None
        
        try:
            resource = self.registry.get_resource(resource_id)
            return resource.to_dict() if resource else None
        except Exception as e:
            logger.error(f"Failed to get resource {resource_id}: {e}")
            return None
    
    async def verify_resources(self) -> Dict[str, str]:
        """Verify all resources.
        
        Returns:
            Dict mapping resource IDs to their status
        """
        if not self.registry:
            logger.error("Resource registry not available")
            return {}
        
        try:
            statuses = await verify_resources()
            return {resource_id: status.value for resource_id, status in statuses.items()}
        except Exception as e:
            logger.error(f"Failed to verify resources: {e}")
            return {}
    
    #
    # Configuration Manager API
    #
    
    def discover_configuration(self) -> int:
        """Discover configuration from various sources.
        
        Returns:
            Number of configuration entries discovered
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return 0
        
        try:
            count = self.config_manager.discover_configuration()
            
            # Update system state
            self.system_state["configs_count"] = count
            self._save_system_state()
            
            return count
        except Exception as e:
            logger.error(f"Failed to discover configuration: {e}")
            return 0
    
    def get_configuration(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return default
        
        try:
            return self.config_manager.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get configuration {key}: {e}")
            return default
    
    def set_configuration(
        self,
        key: str,
        value: Any,
        environment: Optional[str] = None,
        source: Optional[str] = None
    ) -> bool:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            environment: Environment this configuration applies to
            source: Source of the configuration
            
        Returns:
            True if successful, False otherwise
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return False
        
        try:
            # Convert string parameters to enums if needed
            env_enum = None
            if environment and hasattr(ConfigEnvironment, environment.upper()):
                env_enum = getattr(ConfigEnvironment, environment.upper())
            
            source_enum = None
            if source and hasattr(ConfigSource, source.upper()):
                source_enum = getattr(ConfigSource, source.upper())
            
            # Set configuration
            self.config_manager.set(
                key=key,
                value=value,
                environment=env_enum,
                source=source_enum
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to set configuration {key}: {e}")
            return False
    
    def get_all_configuration(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """Get all configuration values.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            Dictionary of configuration values
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return {}
        
        try:
            return self.config_manager.get_all(prefix)
        except Exception as e:
            logger.error(f"Failed to get all configuration: {e}")
            return {}
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate configuration.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return False, ["Configuration manager not available"]
        
        try:
            return self.config_manager.validate()
        except Exception as e:
            logger.error(f"Failed to validate configuration: {e}")
            return False, [str(e)]
    
    def export_configuration(self, path: str, format: str = "json") -> bool:
        """Export configuration to a file.
        
        Args:
            path: Path to export to
            format: File format (json, yaml, env)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return False
        
        try:
            return self.config_manager.export_to_file(path, format)
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, path: str) -> int:
        """Import configuration from a file.
        
        Args:
            path: Path to import from
            
        Returns:
            Number of configuration entries imported
        """
        if not self.config_manager:
            logger.error("Configuration manager not available")
            return 0
        
        try:
            return self.config_manager.import_from_file(path)
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return 0
    
    #
    # Conflict Resolver API
    #
    
    def detect_conflicts(self, directory: str = ".") -> List[Dict[str, Any]]:
        """Detect conflicts in a directory.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of detected conflicts
        """
        if not self.conflict_resolver:
            logger.error("Conflict resolver not available")
            return []
        
        try:
            conflicts = self.conflict_resolver.detect_all_conflicts(directory)
            
            # Update system state
            self.system_state["conflicts_count"] = len(conflicts)
            self._save_system_state()
            
            # Convert to dicts for better serialization
            return [c.to_dict() for c in conflicts]
        except Exception as e:
            logger.error(f"Failed to detect conflicts: {e}")
            return []
    
    def get_conflicts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all conflicts.
        
        Args:
            status: Filter by resolution status
            
        Returns:
            List of conflicts
        """
        if not self.conflict_resolver:
            logger.error("Conflict resolver not available")
            return []
        
        try:
            # Convert string status to enum if needed
            status_enum = None
            if status and hasattr(ResolutionStatus, status.upper()):
                status_enum = getattr(ResolutionStatus, status.upper())
            
            conflicts = self.conflict_resolver.get_all_conflicts(status_enum)
            
            # Convert to dicts for better serialization
            return [c.to_dict() for c in conflicts]
        except Exception as e:
            logger.error(f"Failed to get conflicts: {e}")
            return []
    
    def get_conflict(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        """Get a conflict by ID.
        
        Args:
            conflict_id: Conflict ID
            
        Returns:
            Conflict if found, None otherwise
        """
        if not self.conflict_resolver:
            logger.error("Conflict resolver not available")
            return None
        
        try:
            conflict = self.conflict_resolver.get_conflict(conflict_id)
            return conflict.to_dict() if conflict else None
        except Exception as e:
            logger.error(f"Failed to get conflict {conflict_id}: {e}")
            return None
    
    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: str,
        manual_actions: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Resolve a conflict.
        
        Args:
            conflict_id: ID of the conflict to resolve
            strategy: Resolution strategy to use
            manual_actions: Manual actions to take (for MANUAL strategy)
            
        Returns:
            Resolution if successful, None otherwise
        """
        if not self.conflict_resolver:
            logger.error("Conflict resolver not available")
            return None
        
        try:
            # Convert string strategy to enum
            strategy_enum = None
            if hasattr(ResolutionStrategy, strategy.upper()):
                strategy_enum = getattr(ResolutionStrategy, strategy.upper())
            else:
                logger.error(f"Invalid resolution strategy: {strategy}")
                return None
            
            resolution = self.conflict_resolver.resolve_conflict(
                conflict_id=conflict_id,
                strategy=strategy_enum,
                manual_actions=manual_actions
            )
            
            return resolution.to_dict() if resolution else None
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return None
    
    def apply_resolution(self, resolution_id: str) -> bool:
        """Apply a resolution.
        
        Args:
            resolution_id: ID of the resolution to apply
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conflict_resolver:
            logger.error("Conflict resolver not available")
            return False
        
        try:
            return self.conflict_resolver.apply_resolution(resolution_id)
        except Exception as e:
            logger.error(f"Failed to apply resolution {resolution_id}: {e}")
            return False
    
    #
    # Cleanup API
    #
    
    async def cleanup_artifacts(
        self,
        directories: Optional[List[str]] = None,
        file_patterns: Optional[List[str]] = None,
        dry_run: bool = True,
        max_days_old: int = 30
    ) -> Dict[str, Any]:
        """Clean up development artifacts.
        
        Args:
            directories: List of directories to clean
            file_patterns: List of file patterns to match
            dry_run: Only report what would be deleted
            max_days_old: Maximum age of files to delete in days
            
        Returns:
            Report of cleanup operations
        """
        # Default directories to clean
        if not directories:
            directories = [
                "migration_logs",
                "gcp_migration/migration_logs",
                "terraform/.terraform",
                "terraform/migration",
                "gcp_migration/keys",
                "__pycache__",
                ".pytest_cache"
            ]
        
        # Default file patterns to match
        if not file_patterns:
            file_patterns = [
                "*.log",
                "*.tmp",
                "*.bak",
                "*.swp",
                "*.pyc",
                "*.pyo",
                "*.tfstate.backup",
                "*.tfplan",
                ".DS_Store"
            ]
        
        # Calculate timestamp for max age
        max_age_timestamp = time.time() - (max_days_old * 24 * 60 * 60)
        
        # Find matching files
        files_to_delete = []
        
        for directory in directories:
            if os.path.exists(directory) and os.path.isdir(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Match file patterns
                        if not any(self._match_pattern(file, pattern) for pattern in file_patterns):
                            continue
                        
                        # Check file age
                        try:
                            file_mtime = os.path.getmtime(file_path)
                            if file_mtime > max_age_timestamp:
                                continue
                        except:
                            continue
                        
                        files_to_delete.append(file_path)
        
        # Delete files if not dry run
        deleted_files = []
        errors = []
        
        if not dry_run:
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                except Exception as e:
                    errors.append({"file": file_path, "error": str(e)})
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "directories": directories,
            "file_patterns": file_patterns,
            "max_days_old": max_days_old,
            "dry_run": dry_run,
            "files_found": len(files_to_delete),
            "files_deleted": len(deleted_files) if not dry_run else 0,
            "files_to_delete": files_to_delete if dry_run else deleted_files,
            "errors": errors
        }
        
        # Save cleanup history to MCP memory
        if self.mcp_client:
            try:
                history_response = self.mcp_client.get(self.CLEANUP_HISTORY_KEY)
                history = []
                
                if history_response and history_response.success and history_response.value:
                    history = history_response.value
                
                # Add current report to history
                history.append({
                    "timestamp": report["timestamp"],
                    "files_found": report["files_found"],
                    "files_deleted": report["files_deleted"],
                    "dry_run": report["dry_run"]
                })
                
                # Limit history size
                if len(history) > 10:
                    history = history[-10:]
                
                self.mcp_client.set(self.CLEANUP_HISTORY_KEY, history)
            except Exception as e:
                logger.error(f"Failed to save cleanup history: {e}")
        
        return report
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Match a filename against a pattern.
        
        Args:
            filename: Filename to match
            pattern: Pattern to match against
            
        Returns:
            True if the filename matches the pattern
        """
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    #
    # Context awareness API
    #
    
    async def get_context(self) -> Dict[str, Any]:
        """Get current context for AI assistants.
        
        Returns:
            Context information
        """
        context = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.system_state.get("environment"),
            "resources": {},
            "configuration": {},
            "conflicts": {}
        }
        
        # Get resource counts
        if self.registry:
            try:
                resources = await self.get_resources()
                
                # Group by resource type
                by_type = {}
                for resource in resources:
                    resource_type = resource.get("resource_type")
                    if resource_type not in by_type:
                        by_type[resource_type] = []
                    by_type[resource_type].append(resource)
                
                # Get counts
                context["resources"] = {
                    "total": len(resources),
                    "by_type": {rtype: len(items) for rtype, items in by_type.items()},
                    "available": sum(1 for r in resources if r.get("status") == "available"),
                    "high_priority": sum(1 for r in resources if r.get("priority", 2) <= 1)
                }
            except:
                pass
        
        # Get configuration info
        if self.config_manager:
            try:
                configs = self.get_all_configuration()
                is_valid, errors = self.validate_configuration()
                
                context["configuration"] = {
                    "total": len(configs),
                    "is_valid": is_valid,
                    "errors": len(errors),
                    "environments": list(set(getattr(entry, "environment", "unknown") 
                                        for entry in getattr(self.config_manager, "config_entries", {}).values()))
                }
            except:
                pass
        
        # Get conflict info
        if self.conflict_resolver:
            try:
                conflicts = self.get_conflicts()
                
                context["conflicts"] = {
                    "total": len(conflicts),
                    "by_type": {},
                    "pending": sum(1 for c in conflicts 
                                if c.get("resolution_status") == "pending"),
                    "resolved": sum(1 for c in conflicts 
                                 if c.get("resolution_status") == "resolved")
                }
                
                # Group by conflict type
                for conflict in conflicts:
                    conflict_type = conflict.get("conflict_type")
                    if conflict_type not in context["conflicts"]["by_type"]:
                        context["conflicts"]["by_type"][conflict_type] = 0
                    context["conflicts"]["by_type"][conflict_type] += 1
            except:
                pass
        
        return context


# Singleton instance
_default_api: Optional[OrchestraSystemAPI] = None


def get_api(mcp_client: Optional[MCPClient] = None, force_new: bool = False) -> OrchestraSystemAPI:
    """Get the default system API.
    
    Args:
        mcp_client: Optional MCP client to use
        force_new: Force creation of a new API
        
    Returns:
        The default system API
    """
    global _default_api
    
    if _default_api is None or force_new:
        _default_api = OrchestraSystemAPI(mcp_client=mcp_client)
    
    return _default_api


async def initialize_system() -> Dict[str, Any]:
    """Initialize the system.
    
    Convenience function that uses the default API.
    
    Returns:
        System state
    """
    api = get_api()
    return await api.initialize_system()


async def get_context() -> Dict[str, Any]:
    """Get current context for AI assistants.
    
    Convenience function that uses the default API.
    
    Returns:
        Context information
    """
    api = get_api()
    return await api.get_context()


if __name__ == "__main__":
    """Run the API as a script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Orchestra System API")
    parser.add_argument("--init", action="store_true", help="Initialize the system")
    parser.add_argument("--discover", action="store_true", help="Discover resources")
    parser.add_argument("--conflicts", action="store_true", help="Detect conflicts")
    parser.add_argument("--config", action="store_true", help="Discover configuration")
    parser.add_argument("--cleanup", action="store_true", help="Clean up artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for cleanup")
    parser.add_argument("--context", action="store_true", help="Get current context")
    
    args = parser.parse_args()
    
    # Initialize event loop
    loop = asyncio.get_event_loop()
    api = get_api()
    
    if args.init:
        print("Initializing system...")
        state = loop.run_until_complete(api.initialize_system())
        print(json.dumps(state, indent=2))
    
    if args.discover:
        print("Discovering resources...")
        resources = loop.run_until_complete(api.discover_resources())
        print(f"Discovered {len(resources)} resources")
    
    if args.conflicts:
        print("Detecting conflicts...")
        conflicts = api.detect_conflicts()
        print(f"Detected {len(conflicts)} conflicts")
    
    if args.config:
        print("Discovering configuration...")
        count = api.discover_configuration()
        print(f"Discovered {count} configuration entries")
    
    if args.cleanup:
        print("Cleaning up artifacts...")
        report = loop.run_until_complete(api.cleanup_artifacts(dry_run=args.dry_run))
        print(f"Found {report['files_found']} files to clean up")
        if not args.dry_run:
            print(f"Deleted {report['files_deleted']} files")
        else:
            print("Dry run, no files deleted")
    
    if args.context:
        print("Getting current context...")
        context = loop.run_until_complete(api.get_context())
        print(json.dumps(context, indent=2))
    
    if not any([args.init, args.discover, args.conflicts, args.config, args.cleanup, args.context]):
        # Default action is to get system state
        print("Getting system state...")
        state = loop.run_until_complete(api.get_system_state())
        print(json.dumps(state, indent=2))