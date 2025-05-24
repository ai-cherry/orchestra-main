"""
Centralized configuration loader for AI Orchestration System.

This module provides unified configuration loading utilities to reduce duplication
and standardize configuration patterns across the codebase.
"""

import logging
import os
import json
import yaml
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Type, cast
from pathlib import Path
import functools

from pydantic import BaseModel, Field, ValidationError

from core.orchestrator.src.exceptions import ConfigurationError
from core.orchestrator.src.utils.error_handling import error_boundary

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic config type
T = TypeVar("T", bound=BaseModel)


class ConfigLoader(Generic[T]):
    """
    Generic configuration loader that supports multiple file formats
    and environment variable overrides.

    This class provides a standardized way to load configuration from
    files (YAML, JSON) and environment variables, with validation using
    Pydantic models.
    """

    def __init__(
        self,
        config_class: Type[T],
        config_file_paths: List[str] = None,
        env_prefix: str = "",
        auto_create_config: bool = False,
        default_config_values: Dict[str, Any] = None,
    ):
        """
        Initialize the config loader.

        Args:
            config_class: Pydantic model class for configuration validation
            config_file_paths: List of paths to configuration files (in order of precedence)
            env_prefix: Prefix for environment variables to override config values
            auto_create_config: Whether to create a default config file if none exists
            default_config_values: Default values for config (lower precedence than file or env vars)
        """
        self.config_class = config_class
        self.config_file_paths = config_file_paths or []
        self.env_prefix = env_prefix.upper() + "_" if env_prefix else ""
        self.auto_create_config = auto_create_config
        self.default_config_values = default_config_values or {}

        # Cached config
        self._config: Optional[T] = None

    @error_boundary(propagate_types=[ConfigurationError])
    def load_config(self, reload: bool = False) -> T:
        """
        Load configuration from files and environment variables.

        Args:
            reload: Whether to force reload the configuration

        Returns:
            Validated configuration object

        Raises:
            ConfigurationError: If configuration validation fails
        """
        # Return cached config if available and reload not requested
        if self._config is not None and not reload:
            return self._config

        # Start with default values
        config_data = self.default_config_values.copy()

        # Load from file(s) in order, with later files having higher precedence
        for file_path in self.config_file_paths:
            try:
                file_config = self._load_from_file(file_path)
                if file_config:
                    config_data.update(file_config)
            except Exception as e:
                # Log but continue - file might be optional
                logger.warning(f"Error loading config from {file_path}: {str(e)}")

                # Create default config file if enabled
                if self.auto_create_config and not os.path.exists(file_path):
                    try:
                        self._create_default_config_file(file_path)
                    except Exception as create_error:
                        logger.warning(f"Error creating default config file at {file_path}: {str(create_error)}")

        # Override with environment variables
        env_config = self._load_from_env_vars()
        config_data.update(env_config)

        # Validate configuration with the model
        try:
            validated_config = self.config_class(**config_data)
            self._config = validated_config
            return validated_config
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg, original_error=e)

    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from a file.

        Args:
            file_path: Path to the configuration file

        Returns:
            Dictionary with configuration values
        """
        if not os.path.exists(file_path):
            logger.debug(f"Config file not found: {file_path}")
            return {}

        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            with open(file_path, "r") as f:
                if file_extension in [".yaml", ".yml"]:
                    return yaml.safe_load(f) or {}
                elif file_extension == ".json":
                    return json.load(f)
                else:
                    logger.warning(f"Unsupported file extension for config: {file_extension}")
                    return {}
        except Exception as e:
            logger.error(f"Error reading config file {file_path}: {str(e)}")
            raise ConfigurationError(f"Failed to read config file {file_path}", original_error=e)

    def _load_from_env_vars(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Returns:
            Dictionary with configuration values from environment variables
        """
        env_config = {}

        # Get model fields to know what to look for in env vars
        model_fields = self.config_class.__fields__ if hasattr(self.config_class, "__fields__") else {}

        for field_name, field in model_fields.items():
            # Convert from snake_case to UPPER_SNAKE_CASE with prefix
            env_var_name = f"{self.env_prefix}{field_name.upper()}"

            if env_var_name in os.environ:
                env_value = os.environ[env_var_name]

                # Convert to appropriate type (basic string/int/float/bool)
                if field.type_ == bool:
                    env_config[field_name] = env_value.lower() in [
                        "true",
                        "yes",
                        "y",
                        "1",
                    ]
                elif field.type_ == int:
                    env_config[field_name] = int(env_value)
                elif field.type_ == float:
                    env_config[field_name] = float(env_value)
                else:
                    env_config[field_name] = env_value

        return env_config

    def _create_default_config_file(self, file_path: str) -> None:
        """
        Create a default configuration file.

        Args:
            file_path: Path where to create the configuration file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        # Create with default values
        data = self.default_config_values

        file_extension = os.path.splitext(file_path)[1].lower()

        with open(file_path, "w") as f:
            if file_extension in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False)
            elif file_extension == ".json":
                json.dump(data, f, indent=2)
            else:
                # Just write as JSON if extension not recognized
                json.dump(data, f, indent=2)

        logger.info(f"Created default config file at {file_path}")

    def get_config(self) -> T:
        """
        Get the currently loaded configuration or load it if not loaded.

        Returns:
            Validated configuration object
        """
        if self._config is None:
            return self.load_config()
        return self._config


# Reusable configuration loaders for common configurations
@functools.lru_cache(maxsize=1)
def get_app_config_loader() -> ConfigLoader:
    """
    Get the application configuration loader.

    Returns:
        ConfigLoader for application configuration
    """
    from core.orchestrator.src.config.settings import Settings

    # Default config paths in order of precedence (later overrides earlier)
    config_paths = [
        os.path.join(os.getcwd(), "config/default.yaml"),
        os.path.join(os.getcwd(), "phi_config.yaml"),
        os.environ.get("ORCHESTRA_CONFIG_PATH", ""),
    ]

    # Filter out empty paths
    config_paths = [p for p in config_paths if p]

    return ConfigLoader(
        config_class=Settings,
        config_file_paths=config_paths,
        env_prefix="ORCHESTRA",
        auto_create_config=False,
    )


def get_app_config() -> Any:
    """
    Get the application configuration.

    Returns:
        Application configuration
    """
    loader = get_app_config_loader()
    return loader.get_config()


def get_module_config(
    module_name: str,
    config_class: Type[BaseModel],
    default_config: Dict[str, Any] = None,
) -> BaseModel:
    """
    Get module-specific configuration.

    This is useful for modules that need their own configuration
    separate from the main application.

    Args:
        module_name: Name of the module (used as prefix for env vars)
        config_class: Pydantic model class for validation
        default_config: Default configuration values

    Returns:
        Module configuration
    """
    # Look for config in standard locations
    module_path = module_name.replace(".", "/")
    config_paths = [
        os.path.join(os.getcwd(), f"config/{module_path}.yaml"),
        os.path.join(os.getcwd(), f"config/{module_path}.json"),
        os.environ.get(f"{module_name.upper()}_CONFIG_PATH", ""),
    ]

    # Filter out empty paths
    config_paths = [p for p in config_paths if p]

    loader = ConfigLoader(
        config_class=config_class,
        config_file_paths=config_paths,
        env_prefix=module_name.upper(),
        auto_create_config=True,
        default_config_values=default_config or {},
    )

    return loader.get_config()
