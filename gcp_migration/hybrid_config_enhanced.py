#!/usr/bin/env python3
"""
Enhanced Hybrid Configuration for AI Orchestra

This module provides improved configuration management with schema validation, 
caching, and better error handling for applications running across multiple environments.
"""

import json
import logging
import os
import time
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set, Type, TypeVar, cast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hybrid-config")

# Type variables
T = TypeVar('T')


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class SchemaError(ConfigError):
    """Schema validation error."""
    pass


class ConfigNotFoundError(ConfigError):
    """Configuration not found error."""
    pass


class Environment(Enum):
    """Application environment types."""
    LOCAL = "local"
    CODESPACES = "codespaces"
    WORKSTATION = "workstation"
    CLOUD_RUN = "cloud_run"
    
    @classmethod
    def detect(cls) -> "Environment":
        """Detect the current environment.
        
        Returns:
            Detected environment
        """
        # Check Cloud Run (highest priority)
        if os.environ.get("K_SERVICE") is not None:
            return cls.CLOUD_RUN
            
        # Check GitHub Codespaces
        if os.environ.get("CODESPACES") == "true" or os.environ.get("CODESPACE_NAME"):
            return cls.CODESPACES
            
        # Check GCP Cloud Workstation
        try:
            if os.path.exists("/google/workstations"):
                return cls.WORKSTATION
        except (PermissionError, OSError):
            pass
            
        # Default to local environment
        return cls.LOCAL


class ConfigSchema:
    """Configuration schema with validation."""
    
    @staticmethod
    def validate_config(config: Dict[str, Any], schema: Dict[str, Type]) -> List[str]:
        """Validate configuration against schema.
        
        Args:
            config: Configuration to validate
            schema: Schema to validate against
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for required fields
        for key, type_info in schema.items():
            if key not in config:
                errors.append(f"Missing required field: {key}")
            elif not isinstance(config[key], type_info):
                errors.append(f"Invalid type for {key}: expected {type_info.__name__}, got {type(config[key]).__name__}")
        
        return errors
    
    @staticmethod
    def common_schema() -> Dict[str, Type]:
        """Get schema for common configuration.
        
        Returns:
            Schema for common configuration
        """
        return {
            "project_id": str,
        }
    
    @staticmethod
    def environment_schema(env: Environment) -> Dict[str, Type]:
        """Get schema for environment-specific configuration.
        
        Args:
            env: Environment
            
        Returns:
            Schema for environment-specific configuration
        """
        if env == Environment.LOCAL:
            return {
                "endpoints": dict,
            }
        elif env == Environment.CODESPACES:
            return {
                "codespaces_endpoints": dict,
            }
        elif env == Environment.WORKSTATION:
            return {}
        elif env == Environment.CLOUD_RUN:
            return {
                "enable_monitoring": bool,
            }
        
        return {}


class HybridConfig:
    """Enhanced configuration for hybrid environments."""
    
    # Cache expiration time in seconds
    CACHE_EXPIRATION = 60
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        config_path: Optional[Union[str, Path]] = None,
        validate_schema: bool = True,
        create_defaults: bool = True,
    ):
        """Initialize the configuration manager.
        
        Args:
            project_id: GCP project ID
            config_path: Configuration directory path
            validate_schema: Whether to validate configuration schema
            create_defaults: Whether to create default configuration files
        """
        # Set environment
        self.environment = Environment.detect()
        logger.info(f"Detected environment: {self.environment.value}")
        
        # Set project ID
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT", "cherry-ai-project")
        
        # Set config path
        self.config_path = Path(config_path or "config")
        
        # Create config directory if it doesn't exist
        if not self.config_path.exists():
            try:
                self.config_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created configuration directory: {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to create configuration directory: {e}")
        
        # Set validation flag
        self.validate_schema = validate_schema
        
        # Initialize cache
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp: Dict[str, float] = {}
        
        # Load configuration
        self._load_config()
        
        # Create default configuration files if requested
        if create_defaults and self.config_path.exists():
            self._create_default_configs()
    
    def _load_config(self) -> None:
        """Load configuration from files."""
        self.config: Dict[str, Dict[str, Any]] = {
            "local": {},
            "codespaces": {},
            "workstation": {},
            "cloud_run": {},
            "common": {},
        }
        
        if not self.config_path.exists():
            logger.warning(f"Configuration directory not found: {self.config_path}")
            return
        
        # Load configuration files
        for section in self.config:
            file_path = self.config_path / f"{section}.json"
            config_data = self._load_json_file(file_path)
            
            if config_data:
                # Validate schema if enabled
                if self.validate_schema:
                    schema = (
                        ConfigSchema.common_schema() if section == "common"
                        else ConfigSchema.environment_schema(Environment(section))
                    )
                    
                    errors = ConfigSchema.validate_config(config_data, schema)
                    if errors:
                        logger.warning(f"Schema validation errors in {file_path}:")
                        for error in errors:
                            logger.warning(f"  - {error}")
                
                self.config[section] = config_data
        
        # Set active configuration
        self.active_config = self._get_active_config()
    
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON from file with error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded JSON data or empty dict
        """
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {file_path}")
            return {}
        except Exception as e:
            logger.warning(f"Error loading {file_path}: {e}")
            return {}
    
    def _get_active_config(self) -> Dict[str, Any]:
        """Get active configuration for current environment.
        
        Returns:
            Active configuration
        """
        # Start with common config
        active = dict(self.config.get("common", {}))
        
        # Overlay environment-specific config
        env_config = self.config.get(self.environment.value, {})
        active.update(env_config)
        
        return active
    
    def _create_default_configs(self) -> None:
        """Create default configuration files."""
        # Common config
        common_path = self.config_path / "common.json"
        if not common_path.exists():
            common_config = {
                "project_id": self.project_id,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save_json_file(common_path, common_config)
        
        # Environment-specific configs
        env_configs = {
            "local.json": {
                "endpoints": {
                    "admin-api": "http://localhost:8000",
                    "memory": "http://localhost:8001",
                    "agent": "http://localhost:8002",
                    "mcp": "http://localhost:8003",
                }
            },
            "codespaces.json": {
                "codespaces_endpoints": {
                    "admin-api": "http://localhost:8000",
                    "memory": "http://localhost:8001",
                    "agent": "http://localhost:8002",
                    "mcp": "http://localhost:8003",
                }
            },
            "workstation.json": {
                "workstation_id": "ai-orchestra-ws",
            },
            "cloud_run.json": {
                "enable_monitoring": True,
            }
        }
        
        for filename, config in env_configs.items():
            file_path = self.config_path / filename
            if not file_path.exists():
                self._save_json_file(file_path, config)
    
    def _save_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Save JSON to file with error handling.
        
        Args:
            file_path: Path to JSON file
            data: Data to save
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Created configuration file: {file_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to create configuration file: {e}")
            return False
    
    def reload(self) -> None:
        """Reload configuration from files."""
        self._config_cache.clear()
        self._cache_timestamp.clear()
        self._load_config()
    
    @lru_cache(maxsize=128)
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with caching.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.active_config.get(key, default)
    
    def set(self, key: str, value: Any, section: str = "common") -> bool:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            section: Configuration section
            
        Returns:
            True if successful
            
        Raises:
            ConfigError: If section is invalid
        """
        if section not in self.config:
            raise ConfigError(f"Invalid configuration section: {section}")
        
        # Update configuration
        self.config[section][key] = value
        
        # Update active configuration if applicable
        if section == "common" or section == self.environment.value:
            self.active_config[key] = value
        
        # Save configuration file
        file_path = self.config_path / f"{section}.json"
        result = self._save_json_file(file_path, self.config[section])
        
        # Clear caches
        self.get.cache_clear()
        
        return result
    
    def get_endpoint(self, service_name: str) -> str:
        """Get endpoint URL for service.
        
        Args:
            service_name: Service name
            
        Returns:
            Endpoint URL
        """
        # Check for direct override
        endpoint_key = f"{service_name}_endpoint"
        if endpoint_key in self.active_config:
            return cast(str, self.active_config[endpoint_key])
        
        # Check for endpoints in config
        endpoints = self.active_config.get("endpoints", {})
        if service_name in endpoints:
            return cast(str, endpoints[service_name])
        
        # Check for Codespaces endpoints
        if self.environment == Environment.CODESPACES:
            codespaces_endpoints = self.active_config.get("codespaces_endpoints", {})
            if service_name in codespaces_endpoints:
                return cast(str, codespaces_endpoints[service_name])
        
        # Generate based on environment
        if self.environment == Environment.CLOUD_RUN:
            return f"https://{service_name}-internal.{self.project_id}.cloud.goog"
        elif self.environment == Environment.WORKSTATION:
            return f"https://{service_name}.{self.project_id}.cloud.goog"
        else:
            # Local/Codespaces: use localhost with port
            service_ports = {
                "admin-api": 8000,
                "memory": 8001,
                "agent": 8002,
                "mcp": 8003,
            }
            
            port = service_ports.get(service_name, 8000 + hash(service_name) % 1000)
            return f"http://localhost:{port}"
    
    def get_connections(self) -> Dict[str, str]:
        """Get connection details for all services.
        
        Returns:
            Dictionary of service name to endpoint URL
        """
        services = [
            "admin-api",
            "memory",
            "agent",
            "mcp",
        ]
        
        return {service: self.get_endpoint(service) for service in services}
    
    def is_production(self) -> bool:
        """Check if running in production environment.
        
        Returns:
            True if running in Cloud Run
        """
        return self.environment == Environment.CLOUD_RUN
    
    def is_development(self) -> bool:
        """Check if running in development environment.
        
        Returns:
            True if running in non-production environment
        """
        return self.environment != Environment.CLOUD_RUN
    
    def get_environment_type(self) -> str:
        """Get environment type.
        
        Returns:
            Environment type as string
        """
        return self.environment.value


# Default configuration instance
_default_config: Optional[HybridConfig] = None


def get_config(
    project_id: Optional[str] = None,
    config_path: Optional[Union[str, Path]] = None,
    validate_schema: bool = True,
    force_new: bool = False,
) -> HybridConfig:
    """Get default configuration instance.
    
    Args:
        project_id: GCP project ID
        config_path: Configuration directory path
        validate_schema: Whether to validate configuration schema
        force_new: Force creation of new configuration instance
        
    Returns:
        HybridConfig instance
    """
    global _default_config
    
    if _default_config is None or force_new:
        _default_config = HybridConfig(
            project_id=project_id,
            config_path=config_path,
            validate_schema=validate_schema,
        )
    
    return _default_config


if __name__ == "__main__":
    """CLI interface for hybrid configuration."""
    import argparse
    import sys
    import pprint
    
    parser = argparse.ArgumentParser(description="Hybrid Configuration")
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--config", help="Configuration directory")
    parser.add_argument("--key", help="Configuration key to get")
    parser.add_argument("--service", help="Service name for endpoint")
    parser.add_argument("--list-connections", action="store_true", help="List all connections")
    parser.add_argument("--set", help="Set configuration value")
    parser.add_argument("--value", help="Value to set")
    parser.add_argument("--section", default="common", help="Configuration section for set")
    parser.add_argument("--create-defaults", action="store_true", help="Create default configurations")
    parser.add_argument("--validate", action="store_true", help="Validate configuration schema")
    parser.add_argument("--show-all", action="store_true", help="Show all configuration")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set verbose logging if requested
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create configuration
        config = HybridConfig(
            project_id=args.project,
            config_path=args.config,
            validate_schema=args.validate,
            create_defaults=args.create_defaults,
        )
        
        # Show environment info
        print(f"Environment: {config.environment.value}")
        print(f"Project ID: {config.project_id}")
        print(f"Config Path: {config.config_path}")
        print(f"Is Production: {config.is_production()}")
        print(f"Is Development: {config.is_development()}")
        
        # Set value if requested
        if args.set and args.value is not None:
            try:
                # Try to parse as integer or boolean
                if args.value.lower() == "true":
                    value = True
                elif args.value.lower() == "false":
                    value = False
                elif args.value.isdigit():
                    value = int(args.value)
                elif args.value.replace(".", "", 1).isdigit():
                    value = float(args.value)
                else:
                    value = args.value
                
                if config.set(args.set, value, args.section):
                    print(f"Set {args.section}.{args.set} = {value}")
                else:
                    print(f"Failed to set {args.section}.{args.set}")
                    sys.exit(1)
            except ConfigError as e:
                print(f"Configuration error: {e}")
                sys.exit(1)
        
        # Get specific value if requested
        if args.key:
            value = config.get(args.key)
            print(f"{args.key}: {value}")
        
        # Get service endpoint if requested
        if args.service:
            endpoint = config.get_endpoint(args.service)
            print(f"{args.service} endpoint: {endpoint}")
        
        # List connections if requested
        if args.list_connections:
            connections = config.get_connections()
            print("\nService Connections:")
            for service, endpoint in connections.items():
                print(f"  {service}: {endpoint}")
        
        # Show all configuration if requested
        if args.show_all:
            print("\nActive Configuration:")
            pprint.pprint(config.active_config)
            
            print("\nAll Configuration:")
            pprint.pprint(config.config)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
