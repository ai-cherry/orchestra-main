"""
Configuration module for AI Orchestration System.

This module provides configuration loading and access for the orchestration
system, centralizing settings management.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import the PersonaConfig model from the shared package
try:
    from packages.shared.src.models.core_models import PersonaConfig
except ImportError:
    # If imports don't work due to PYTHONPATH issues, try a relative import
    import sys

    sys.path.append("/workspaces/orchestra-main")
    from packages.shared.src.models.core_models import PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Configuration settings for the AI Orchestration System.

    This class centralizes all configuration settings for the application,
    with automatic loading from environment variables and sensible defaults.
    """

    # Basic configuration
    APP_NAME: str = "AI Orchestration System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Storage configuration
    GCP_PROJECT_ID: Optional[str] = None
    FIRESTORE_ENABLED: bool = True
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Resource paths
    PERSONA_CONFIG_PATH: str = "core/orchestrator/src/config/personas"

    # Memory settings
    MEMORY_PROVIDER: str = "in_memory"
    CONVERSATION_HISTORY_LIMIT: int = 10

    # Agent settings
    DEFAULT_AGENT_TYPE: str = "simple_text"
    PREFERRED_AGENTS_ENABLED: bool = True
    AGENT_TIMEOUT_SECONDS: int = 30

    # LLM settings
    OPENROUTER_API_KEY: Optional[SecretStr] = None
    DEFAULT_LLM_MODEL: str = "openai/gpt-3.5-turbo"

    # API settings
    CORS_ORIGINS: List[str] = ["*"]
    API_PREFIX: str = "/api"

    # Configure Pydantic to load from .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )


def load_all_persona_configs() -> Dict[str, PersonaConfig]:
    """
    Load all persona configurations from YAML files.

    This function scans the persona config directory specified in the settings
    and loads each YAML file into a PersonaConfig object.

    Returns:
        A dictionary mapping persona names to their configuration objects
    """
    import yaml

    personas = {}
    persona_dir = settings.PERSONA_CONFIG_PATH

    # Check if the directory exists
    if not os.path.exists(persona_dir):
        logger.warning(f"Persona config directory '{persona_dir}' not found")
        return personas

    # Scan the directory for YAML files
    for filename in os.listdir(persona_dir):
        if filename.endswith((".yaml", ".yml")):
            file_path = os.path.join(persona_dir, filename)
            try:
                with open(file_path, "r") as file:
                    # Load YAML content
                    yaml_data = yaml.safe_load(file)

                    # Create PersonaConfig from YAML data
                    persona_config = PersonaConfig(**yaml_data)

                    # Use lowercase filename (without extension) as the key
                    persona_name = os.path.splitext(filename)[0].lower()
                    personas[persona_name] = persona_config

                    logger.info(f"Loaded persona configuration for '{persona_name}'")
            except Exception as e:
                logger.error(f"Error loading persona config from {file_path}: {str(e)}")

    if not personas:
        logger.warning("No persona configurations found")

    return personas


# Global settings instance for singleton pattern
settings = Settings()

# Log that settings have been loaded
logger.info(
    f"Loaded configuration for {settings.APP_NAME} in {settings.ENVIRONMENT} environment"
)

def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings instance.
    """
    return settings
