#!/usr/bin/env python3
"""
Configuration Manager for AI Orchestra

This module implements a centralized Configuration Manager for managing
configuration across different environments (GCP, GitHub Codespaces).
It provides automatic detection of conflicts, handling of environment-specific
configurations, and integration with MCP memory for configuration persistence.

Key features:
- Environment-aware configuration management
- Automatic conflict detection and resolution
- Config version tracking and rollback support
- Integration with Resource Registry for resource configuration
- Cross-environment configuration synchronization
"""

import asyncio
import json
import logging
import os
import time
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("config-manager")

# Import MCP client
try:
    from gcp_migration.mcp_client_enhanced import MCPClient, MCPResponse, get_client as get_mcp_client
except ImportError:
    logger.warning("Could not import enhanced MCP client, attempting to import basic client")
    try:
        from gcp_migration.mcp_client import MCPClient, get_client as get_mcp_client
    except ImportError:
        logger.error("Failed to import MCP client. Config Manager will operate in offline mode.")
        MCPClient = object
        
        def get_mcp_client(*args, **kwargs):
            return None


class ConfigEnvironment(str, Enum):
    """Environment where configuration is used."""
    
    LOCAL = "local"                  # Local development machine
    CODESPACES = "codespaces"        # GitHub Codespaces
    GCP_CLOUD_RUN = "gcp_cloud_run"  # GCP Cloud Run
    GCP_WORKSTATION = "gcp_workstation"  # GCP Workstation
    CI_CD = "ci_cd"                  # CI/CD pipelines
    ALL = "all"                      # Applies to all environments


class ConfigPriority(int, Enum):
    """Priority levels for configuration."""
    
    CRITICAL = 0    # Critical configuration that must not be overridden
    HIGH = 1        # High priority configuration
    MEDIUM = 2      # Medium priority configuration
    LOW = 3         # Low priority configuration
    DEFAULT = 4     # Default configuration with lowest priority


class ConfigSource(str, Enum):
    """Source of configuration values."""
    
    FILE = "file"                 # Configuration from a file
    ENVIRONMENT = "environment"   # Configuration from environment variables
    MCP = "mcp"                   # Configuration from MCP memory
    DEFAULT = "default"           # Default configuration values
    COMMAND_LINE = "command_line" # Configuration from command line arguments
    API = "api"                   # Configuration from API call


class ConfigEntry:
    """Represents a single configuration entry."""
    
    def __init__(
        self,
        key: str,
        value: Any,
        environment: ConfigEnvironment,
        priority: ConfigPriority = ConfigPriority.MEDIUM,
        source: ConfigSource = ConfigSource.DEFAULT,
        description: str = "",
        source_path: Optional[str] = None,
        version: int = 1,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        """Initialize a configuration entry.
        
        Args:
            key: Configuration key
            value: Configuration value
            environment: Environment this configuration applies to
            priority: Priority level
            source: Source of the configuration
            description: Human-readable description
            source_path: Path to the source file if applicable
            version: Version of the configuration
            created_at: Creation timestamp
            updated_at: Last update timestamp
            tags: List of tags for categorization
        """
        self.key = key
        self.value = value
        self.environment = environment
        self.priority = priority
        self.source = source
        self.description = description
        self.source_path = source_path
        self.version = version
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.tags = tags or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration entry to a dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "environment": self.environment,
            "priority": self.priority.value,
            "source": self.source,
            "description": self.description,
            "source_path": self.source_path,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigEntry':
        """Create a configuration entry from a dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            environment=data["environment"],
            priority=ConfigPriority(data["priority"]),
            source=data["source"],
            description=data.get("description", ""),
            source_path=data.get("source_path"),
            version=data.get("version", 1),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            tags=data.get("tags", [])
        )
    
    def update_value(self, value: Any, source: ConfigSource, source_path: Optional[str] = None) -> None:
        """Update the configuration value.
        
        Args:
            value: New configuration value
            source: Source of the new value
            source_path: Path to the source file if applicable
        """
        # Only update if value is different
        if self.value != value:
            self.value = value
            self.source = source
            self.updated_at = datetime.now().isoformat()
            self.version += 1
            
            if source_path:
                self.source_path = source_path


class ConfigConflict:
    """Represents a conflict between configuration values."""
    
    def __init__(
        self,
        key: str,
        entries: List[ConfigEntry],
        detected_at: Optional[str] = None
    ):
        """Initialize a configuration conflict.
        
        Args:
            key: Configuration key with conflict
            entries: Conflicting configuration entries
            detected_at: Timestamp when conflict was detected
        """
        self.key = key
        self.entries = entries
        self.detected_at = detected_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the conflict to a dictionary for serialization."""
        return {
            "key": self.key,
            "entries": [entry.to_dict() for entry in self.entries],
            "detected_at": self.detected_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigConflict':
        """Create a conflict from a dictionary."""
        entries = [ConfigEntry.from_dict(entry_data) for entry_data in data["entries"]]
        return cls(
            key=data["key"],
            entries=entries,
            detected_at=data.get("detected_at")
        )
    
    def resolve_by_priority(self) -> ConfigEntry:
        """Resolve conflict by selecting the entry with highest priority (lowest numerical value).
        
        Returns:
            The resolved configuration entry
        """
        if not self.entries:
            raise ValueError("No entries to resolve conflict")
        
        # Sort by priority (lowest numerical value is highest priority)
        entries = sorted(self.entries, key=lambda e: e.priority.value)
        return entries[0]
    
    def resolve_by_environment(self, current_env: ConfigEnvironment) -> ConfigEntry:
        """Resolve conflict by selecting the entry matching the current environment.
        
        Args:
            current_env: Current environment
            
        Returns:
            The resolved configuration entry
        """
        if not self.entries:
            raise ValueError("No entries to resolve conflict")
        
        # First try to find an exact environment match
        for entry in self.entries:
            if entry.environment == current_env:
                return entry
        
        # Then try to find ALL environment
        for entry in self.entries:
            if entry.environment == ConfigEnvironment.ALL:
                return entry
        
        # Fall back to priority-based resolution
        return self.resolve_by_priority()


class ConfigurationManager:
    """Central manager for application configuration."""
    
    # MCP memory keys
    CONFIG_KEY = "configuration:entries"
    CONFIG_CONFLICTS_KEY = "configuration:conflicts"
    CONFIG_HISTORY_KEY = "configuration:history"
    
    # Common configuration file paths
    CONFIG_FILE_PATHS = [
        ".env",
        "config.json",
        "settings.json",
        "config.yaml",
        "config.yml",
        "pyproject.toml",
        "poetry.toml",
        "terraform/variables.tf"
    ]
    
    def __init__(
        self, 
        mcp_client: Optional[MCPClient] = None,
        auto_discover: bool = True,
        environment: Optional[ConfigEnvironment] = None
    ):
        """Initialize the Configuration Manager.
        
        Args:
            mcp_client: An instance of MCPClient for accessing shared memory
            auto_discover: Automatically discover configuration files
            environment: Current environment, auto-detected if None
        """
        self.mcp_client = mcp_client or get_mcp_client()
        self.config_entries: Dict[str, Dict[ConfigEnvironment, ConfigEntry]] = defaultdict(dict)
        self.conflicts: Dict[str, ConfigConflict] = {}
        self.environment = environment or self._detect_environment()
        self.initialized = False
        
        # Initialize the manager
        self._initialize_manager()
        
        # Auto-discover configuration
        if auto_discover:
            self.discover_configuration()
    
    def _initialize_manager(self) -> None:
        """Initialize the Configuration Manager."""
        try:
            # Load configuration from MCP memory if available
            if self.mcp_client:
                self._load_from_mcp()
            else:
                logger.warning("No MCP client available. Configuration will not be persistent.")
            
            self.initialized = True
            logger.info(f"Configuration Manager initialized for {self.environment} environment")
        
        except Exception as e:
            logger.error(f"Failed to initialize Configuration Manager: {e}")
    
    def _load_from_mcp(self) -> None:
        """Load configuration entries from MCP memory."""
        try:
            if not self.mcp_client:
                return
            
            # Load configuration entries
            config_response = self.mcp_client.get(self.CONFIG_KEY)
            if config_response and config_response.success and config_response.value:
                config_data = config_response.value
                
                # Clear existing entries
                self.config_entries.clear()
                
                # Load entries
                for key, env_entries in config_data.items():
                    for env, entry_data in env_entries.items():
                        entry = ConfigEntry.from_dict(entry_data)
                        self.config_entries[key][ConfigEnvironment(env)] = entry
                
                logger.info(f"Loaded {len(self.config_entries)} configuration entries from MCP memory")
            
            # Load conflicts
            conflicts_response = self.mcp_client.get(self.CONFIG_CONFLICTS_KEY)
            if conflicts_response and conflicts_response.success and conflicts_response.value:
                conflicts_data = conflicts_response.value
                
                # Clear existing conflicts
                self.conflicts.clear()
                
                # Load conflicts
                for key, conflict_data in conflicts_data.items():
                    self.conflicts[key] = ConfigConflict.from_dict(conflict_data)
                
                logger.info(f"Loaded {len(self.conflicts)} configuration conflicts from MCP memory")
        
        except Exception as e:
            logger.error(f"Failed to load configuration from MCP memory: {e}")
    
    def _save_to_mcp(self) -> bool:
        """Save configuration entries to MCP memory."""
        try:
            if not self.mcp_client:
                return False
            
            # Convert entries to dictionaries
            entries_data = {}
            for key, env_entries in self.config_entries.items():
                entries_data[key] = {}
                for env, entry in env_entries.items():
                    entries_data[key][env] = entry.to_dict()
            
            # Save entries
            entries_result = self.mcp_client.set(self.CONFIG_KEY, entries_data)
            
            # Convert conflicts to dictionaries
            conflicts_data = {}
            for key, conflict in self.conflicts.items():
                conflicts_data[key] = conflict.to_dict()
            
            # Save conflicts
            conflicts_result = self.mcp_client.set(self.CONFIG_CONFLICTS_KEY, conflicts_data)
            
            if (not entries_result or not entries_result.success) or (not conflicts_result or not conflicts_result.success):
                logger.error("Failed to save configuration to MCP memory")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save configuration to MCP memory: {e}")
            return False
    
    def _detect_environment(self) -> ConfigEnvironment:
        """Detect the current environment.
        
        Returns:
            The detected environment
        """
        # Check for GitHub Codespaces
        if os.environ.get("CODESPACES") == "true":
            return ConfigEnvironment.CODESPACES
        
        # Check for GCP Cloud Run
        if os.environ.get("K_SERVICE"):
            return ConfigEnvironment.GCP_CLOUD_RUN
        
        # Check for GCP Workstation
        if os.environ.get("CLOUD_WORKSTATIONS_AGENT"):
            return ConfigEnvironment.GCP_WORKSTATION
        
        # Check for CI/CD
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            return ConfigEnvironment.CI_CD
        
        # Default to local
        return ConfigEnvironment.LOCAL
    
    def discover_configuration(self) -> int:
        """Discover and load configuration from various sources.
        
        Look for configuration in standard locations like .env files,
        environment variables, etc.
        
        Returns:
            Number of configuration entries discovered
        """
        entry_count = 0
        
        # Discover environment variables
        env_count = self._discover_environment_variables()
        entry_count += env_count
        logger.info(f"Discovered {env_count} configuration entries from environment variables")
        
        # Discover configuration files
        file_count = self._discover_configuration_files()
        entry_count += file_count
        logger.info(f"Discovered {file_count} configuration entries from files")
        
        # Check for conflicts
        self._detect_conflicts()
        
        return entry_count
    
    def _discover_environment_variables(self) -> int:
        """Discover configuration from environment variables.
        
        Returns:
            Number of configuration entries discovered
        """
        entry_count = 0
        
        # Look for environment variables with common prefixes
        prefixes = ["CONFIG_", "APP_", "ORCHESTRA_", "GCP_", "GITHUB_", "GOOGLE_"]
        
        for name, value in os.environ.items():
            # Check if variable name starts with any of the prefixes
            if any(name.startswith(prefix) for prefix in prefixes):
                # Convert to config key (lowercase)
                key = name.lower()
                
                # Add as config entry
                self.set(
                    key=key,
                    value=value,
                    environment=self.environment,
                    priority=ConfigPriority.HIGH if name.startswith("CONFIG_") else ConfigPriority.MEDIUM,
                    source=ConfigSource.ENVIRONMENT,
                    description=f"Environment variable: {name}"
                )
                
                entry_count += 1
        
        return entry_count
    
    def _discover_configuration_files(self) -> int:
        """Discover configuration from common configuration files.
        
        Returns:
            Number of configuration entries discovered
        """
        entry_count = 0
        
        for file_path in self.CONFIG_FILE_PATHS:
            path = Path(file_path)
            if path.exists() and path.is_file():
                loaded = self._load_config_file(path)
                entry_count += loaded
                logger.info(f"Loaded {loaded} configuration entries from {path}")
        
        return entry_count
    
    def _load_config_file(self, path: Path) -> int:
        """Load configuration from a file.
        
        Args:
            path: Path to configuration file
            
        Returns:
            Number of configuration entries loaded
        """
        try:
            entry_count = 0
            file_str = str(path)
            
            # JSON files
            if path.suffix.lower() in [".json"]:
                with open(path, "r") as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    # Flatten nested dictionary
                    flat_data = self._flatten_dict(data)
                    
                    for key, value in flat_data.items():
                        self.set(
                            key=key,
                            value=value,
                            environment=self.environment,
                            priority=ConfigPriority.MEDIUM,
                            source=ConfigSource.FILE,
                            source_path=file_str,
                            description=f"From {path.name}"
                        )
                        
                        entry_count += 1
            
            # YAML files
            elif path.suffix.lower() in [".yaml", ".yml"]:
                try:
                    import yaml
                    with open(path, "r") as f:
                        data = yaml.safe_load(f)
                    
                    if isinstance(data, dict):
                        # Flatten nested dictionary
                        flat_data = self._flatten_dict(data)
                        
                        for key, value in flat_data.items():
                            self.set(
                                key=key,
                                value=value,
                                environment=self.environment,
                                priority=ConfigPriority.MEDIUM,
                                source=ConfigSource.FILE,
                                source_path=file_str,
                                description=f"From {path.name}"
                            )
                            
                            entry_count += 1
                
                except ImportError:
                    logger.warning("PyYAML not available, skipping YAML configuration")
            
            # .env files
            elif path.name == ".env":
                with open(path, "r") as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse key-value pairs
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        self.set(
                            key=key.lower(),
                            value=value,
                            environment=self.environment,
                            priority=ConfigPriority.HIGH,
                            source=ConfigSource.FILE,
                            source_path=file_str,
                            description=f"From {path.name}"
                        )
                        
                        entry_count += 1
            
            # TOML files (pyproject.toml, poetry.toml)
            elif path.suffix.lower() == ".toml":
                try:
                    import toml
                    with open(path, "r") as f:
                        data = toml.load(f)
                    
                    if isinstance(data, dict):
                        # Flatten nested dictionary
                        flat_data = self._flatten_dict(data)
                        
                        for key, value in flat_data.items():
                            self.set(
                                key=key,
                                value=value,
                                environment=self.environment,
                                priority=ConfigPriority.MEDIUM,
                                source=ConfigSource.FILE,
                                source_path=file_str,
                                description=f"From {path.name}"
                            )
                            
                            entry_count += 1
                
                except ImportError:
                    logger.warning("TOML parser not available, skipping TOML configuration")
            
            # Terraform variables file
            elif path.name == "variables.tf":
                try:
                    # Simple parser for Terraform variables
                    with open(path, "r") as f:
                        content = f.read()
                    
                    # Extract variable blocks
                    import re
                    var_blocks = re.findall(r'variable\s+"([^"]+)"\s+{([^}]+)}', content)
                    
                    for var_name, var_content in var_blocks:
                        # Extract default value if present
                        default_match = re.search(r'default\s+=\s+(?:"([^"]+)"|(\d+)|([a-z]+))', var_content)
                        if default_match:
                            value = default_match.group(1) or default_match.group(2) or default_match.group(3)
                            
                            # Convert to appropriate type
                            if default_match.group(2):  # Number
                                try:
                                    value = int(value)
                                except ValueError:
                                    try:
                                        value = float(value)
                                    except ValueError:
                                        pass
                            elif default_match.group(3):  # Boolean
                                value = value.lower() == "true"
                            
                            # Extract description if present
                            description = "Terraform variable"
                            desc_match = re.search(r'description\s+=\s+"([^"]+)"', var_content)
                            if desc_match:
                                description = desc_match.group(1)
                            
                            self.set(
                                key=f"terraform.{var_name}",
                                value=value,
                                environment=self.environment,
                                priority=ConfigPriority.MEDIUM,
                                source=ConfigSource.FILE,
                                source_path=file_str,
                                description=description
                            )
                            
                            entry_count += 1
                
                except Exception as e:
                    logger.warning(f"Failed to parse Terraform variables file: {e}")
            
            return entry_count
        
        except Exception as e:
            logger.error(f"Failed to load configuration from {path}: {e}")
            return 0
    
    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten a nested dictionary.
        
        Args:
            data: Dictionary to flatten
            prefix: Prefix for keys
            
        Returns:
            Flattened dictionary
        """
        result = {}
        
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                nested = self._flatten_dict(value, new_key)
                result.update(nested)
            else:
                result[new_key] = value
        
        return result
    
    def set(
        self,
        key: str,
        value: Any,
        environment: Optional[ConfigEnvironment] = None,
        priority: ConfigPriority = ConfigPriority.MEDIUM,
        source: ConfigSource = ConfigSource.DEFAULT,
        source_path: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            environment: Environment this configuration applies to
            priority: Priority level
            source: Source of the configuration
            source_path: Path to the source file if applicable
            description: Human-readable description
            tags: List of tags for categorization
        """
        env = environment or self.environment
        
        # Check if entry already exists
        if key in self.config_entries and env in self.config_entries[key]:
            # Update existing entry
            entry = self.config_entries[key][env]
            entry.update_value(value, source, source_path)
        else:
            # Create new entry
            entry = ConfigEntry(
                key=key,
                value=value,
                environment=env,
                priority=priority,
                source=source,
                description=description,
                source_path=source_path,
                tags=tags or []
            )
            
            # Add to entries
            self.config_entries[key][env] = entry
        
        # Check for conflicts
        self._detect_conflicts_for_key(key)
        
        # Save to MCP memory
        self._save_to_mcp()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        # Check if key exists
        if key not in self.config_entries:
            return default
        
        # Check for conflicts
        if key in self.conflicts:
            # Resolve conflict
            conflict = self.conflicts[key]
            entry = conflict.resolve_by_environment(self.environment)
            return entry.value
        
        # Check for entry in current environment
        if self.environment in self.config_entries[key]:
            return self.config_entries[key][self.environment].value
        
        # Check for entry in ALL environment
        if ConfigEnvironment.ALL in self.config_entries[key]:
            return self.config_entries[key][ConfigEnvironment.ALL].value
        
        # Fall back to default
        return default
    
    def get_entry(self, key: str) -> Optional[ConfigEntry]:
        """Get a configuration entry.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration entry if found, None otherwise
        """
        # Check if key exists
        if key not in self.config_entries:
            return None
        
        # Check for conflicts
        if key in self.conflicts:
            # Resolve conflict
            conflict = self.conflicts[key]
            return conflict.resolve_by_environment(self.environment)
        
        # Check for entry in current environment
        if self.environment in self.config_entries[key]:
            return self.config_entries[key][self.environment]
        
        # Check for entry in ALL environment
        if ConfigEnvironment.ALL in self.config_entries[key]:
            return self.config_entries[key][ConfigEnvironment.ALL]
        
        return None
    
    def get_all(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """Get all configuration values.
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            Dictionary of configuration values
        """
        result = {}
        
        for key in self.config_entries:
            # Filter by prefix if provided
            if prefix and not key.startswith(prefix):
                continue
            
            # Get value
            result[key] = self.get(key)
        
        return result
    
    def delete(self, key: str, environment: Optional[ConfigEnvironment] = None) -> bool:
        """Delete a configuration entry.
        
        Args:
            key: Configuration key
            environment: Environment to delete from, all environments if None
            
        Returns:
            True if deleted, False otherwise
        """
        if key not in self.config_entries:
            return False
        
        if environment:
            # Delete from specific environment
            if environment in self.config_entries[key]:
                del self.config_entries[key][environment]
                
                # Remove key if no environments left
                if not self.config_entries[key]:
                    del self.config_entries[key]
                
                # Remove from conflicts
                if key in self.conflicts:
                    del self.conflicts[key]
                
                # Save to MCP memory
                self._save_to_mcp()
                
                return True
            else:
                return False
        else:
            # Delete from all environments
            del self.config_entries[key]
            
            # Remove from conflicts
            if key in self.conflicts:
                del self.conflicts[key]
            
            # Save to MCP memory
            self._save_to_mcp()
            
            return True
    
    def _detect_conflicts(self) -> List[str]:
        """Detect conflicts between configuration values.
        
        Returns:
            List of keys with conflicts
        """
        # Clear existing conflicts
        self.conflicts.clear()
        
        # Check for conflicts
        conflict_keys = []
        for key, env_entries in self.config_entries.items():
            # Skip if only one environment
            if len(env_entries) <= 1:
                continue
            
            self._detect_conflicts_for_key(key)
            
            if key in self.conflicts:
                conflict_keys.append(key)
        
        return conflict_keys
    
    def _detect_conflicts_for_key(self, key: str) -> bool:
        """Detect conflicts for a specific key.
        
        Args:
            key: Configuration key
            
        Returns:
            True if conflict detected, False otherwise
        """
        if key not in self.config_entries:
            return False
        
        env_entries = self.config_entries[key]
        
        # Skip if only one environment
        if len(env_entries) <= 1:
            return False
        
        # Check for conflicts
        values = {}
        for env, entry in env_entries.items():
            value_str = json.dumps(entry.value) if isinstance(entry.value, (dict, list)) else str(entry.value)
            if value_str not in values:
                values[value_str] = []
            values[value_str].append(entry)
        
        # If more than one distinct value, we have a conflict
        if len(values) > 1:
            # Create conflict
            entries = [entry for entries in values.values() for entry in entries]
            self.conflicts[key] = ConfigConflict(key=key, entries=entries)
            return True
        
        # No conflict
        if key in self.conflicts:
            del self.conflicts[key]
        
        return False
    
    def export_to_file(self, path: str, format: str = "json") -> bool:
        """Export configuration to a file.
        
        Args:
            path: Path to export to
            format: File format (json, yaml, env)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all configuration values for current environment
            config = self.get_all()
            
            if format.lower() == "json":
                with open(path, "w") as f:
                    json.dump(config, f, indent=2)
            
            elif format.lower() == "yaml":
                try:
                    import yaml
                    with open(path, "w") as f:
                        yaml.dump(config, f)
                except ImportError:
                    logger.error("PyYAML not available")
                    return False
            
            elif format.lower() == "env":
                with open(path, "w") as f:
                    for key, value in config.items():
                        # Skip complex values
                        if not isinstance(value, (str, int, float, bool)):
                            continue
                        
                        # Convert to string
                        if isinstance(value, bool):
                            value_str = "true" if value else "false"
                        else:
                            value_str = str(value)
                        
                        f.write(f"{key.upper()}={value_str}\n")
            
            else:
                logger.error(f"Unsupported format: {format}")
                return False
            
            logger.info(f"Exported configuration to {path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_from_file(
        self,
        path: str,
        environment: Optional[ConfigEnvironment] = None,
        priority: ConfigPriority = ConfigPriority.MEDIUM
    ) -> int:
        """Import configuration from a file.
        
        Args:
            path: Path to import from
            environment: Environment to import for
            priority: Priority level for imported configuration
            
        Returns:
            Number of entries imported
        """
        try:
            file_path = Path(path)
            if not file_path.exists():
                logger.error(f"File not found: {path}")
                return 0
            
            env = environment or self.environment
            count = 0
            
            if file_path.suffix.lower() == ".json":
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    # Flatten nested dictionary
                    flat_data = self._flatten_dict(data)
                    
                    for key, value in flat_data.items():
                        self.set(
                            key=key,
                            value=value,
                            environment=env,
                            priority=priority,
                            source=ConfigSource.FILE,
                            source_path=str(file_path),
                            description=f"Imported from {file_path.name}"
                        )
                        count += 1
            
            elif file_path.suffix.lower() in [".yaml", ".yml"]:
                try:
                    import yaml
                    with open(file_path, "r") as f:
                        data = yaml.safe_load(f)
                    
                    if isinstance(data, dict):
                        # Flatten nested dictionary
                        flat_data = self._flatten_dict(data)
                        
                        for key, value in flat_data.items():
                            self.set(
                                key=key,
                                value=value,
                                environment=env,
                                priority=priority,
                                source=ConfigSource.FILE,
                                source_path=str(file_path),
                                description=f"Imported from {file_path.name}"
                            )
                            count += 1
                
                except ImportError:
                    logger.error("PyYAML not available")
                    return 0
            
            elif file_path.name.endswith(".env"):
                with open(file_path, "r") as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse key-value pairs
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        
                        self.set(
                            key=key.lower(),
                            value=value,
                            environment=env,
                            priority=priority,
                            source=ConfigSource.FILE,
                            source_path=str(file_path),
                            description=f"Imported from {file_path.name}"
                        )
                        count += 1
            
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                return 0
            
            logger.info(f"Imported {count} configuration entries from {path}")
            return count
        
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return 0
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration.
        
        Check for required configuration, invalid values, etc.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check for conflicts
        for key, conflict in self.conflicts.items():
            entries = conflict.entries
            values = [entry.value for entry in entries]
            envs = [entry.environment for entry in entries]
            
            errors.append(f"Conflict for key '{key}': {len(values)} different values across environments {envs}")
        
        return len(errors) == 0, errors


# Singleton instance
_default_manager: Optional[ConfigurationManager] = None


def get_manager(
    mcp_client: Optional[MCPClient] = None,
    environment: Optional[ConfigEnvironment] = None,
    force_new: bool = False
) -> ConfigurationManager:
    """Get the default configuration manager.
    
    Args:
        mcp_client: Optional MCP client to use
        environment: Current environment, auto-detected if None
        force_new: Force creation of a new manager
        
    Returns:
        The default configuration manager
    """
    global _default_manager
    
    if _default_manager is None or force_new:
        _default_manager = ConfigurationManager(mcp_client=mcp_client, environment=environment)
    
    return _default_manager


# Convenience functions
def get(key: str, default: Any = None) -> Any:
    """Get a configuration value.
    
    Args:
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    return get_manager().get(key, default)


def set(key: str, value: Any, **kwargs) -> None:
    """Set a configuration value.
    
    Args:
        key: Configuration key
        value: Configuration value
        **kwargs: Additional arguments for ConfigurationManager.set()
    """
    return get_manager().set(key, value, **kwargs)


def get_all(prefix: Optional[str] = None) -> Dict[str, Any]:
    """Get all configuration values.
    
    Args:
        prefix: Optional prefix to filter keys
        
    Returns:
        Dictionary of configuration values
    """
    return get_manager().get_all(prefix)


if __name__ == "__main__":
    """Run the configuration manager as a script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration Manager for AI Orchestra")
    parser.add_argument("--discover", action="store_true", help="Discover configuration")
    parser.add_argument("--export", metavar="PATH", help="Export configuration to file")
    parser.add_argument("--format", choices=["json", "yaml", "env"], default="json", help="Export format")
    parser.add_argument("--import", dest="import_path", metavar="PATH", help="Import configuration from file")
    parser.add_argument("--environment", choices=[e.value for e in ConfigEnvironment], help="Environment")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    
    args = parser.parse_args()
    
    if args.environment:
        env = ConfigEnvironment(args.environment)
    else:
        env = None
    
    manager = ConfigurationManager(environment=env)
    
    if args.discover:
        count = manager.discover_configuration()
        print(f"Discovered {count} configuration entries")
        
        if manager.conflicts:
            print(f"Found {len(manager.conflicts)} conflicts:")
            for key, conflict in manager.conflicts.items():
                print(f"  - {key}: {len(conflict.entries)} conflicting entries")
    
    if args.export:
        success = manager.export_to_file(args.export, args.format)
        if success:
            print(f"Exported configuration to {args.export}")
        else:
            print(f"Failed to export configuration to {args.export}")
    
    if args.import_path:
        count = manager.import_from_file(args.import_path)
        print(f"Imported {count} configuration entries from {args.import_path}")
    
    if args.validate:
        valid, errors = manager.validate()
        if valid:
            print("Configuration is valid")
        else:
            print(f"Configuration is invalid ({len(errors)} errors):")
            for error in errors:
                print(f"  - {error}")
    
    if not any([args.discover, args.export, args.import_path, args.validate]):
        # Show current configuration
        config = manager.get_all()
        print(f"Current configuration ({len(config)} entries):")
        for key, value in config.items():
            entry = manager.get_entry(key)
            print(f"  - {key} = {value}")
            if entry:
                print(f"    Source: {entry.source}")
                if entry.description:
                    print(f"    Description: {entry.description}")
