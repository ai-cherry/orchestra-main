"""
Google Cloud Platform configuration settings for the Orchestra project.

This module contains configurations for connecting to various GCP services
based on the current environment (development, staging, production).
"""

import os
from typing import Dict, Any, Optional
from loguru import logger

# Default environment is development if not specified
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()

# Base configuration shared across all environments
BASE_CONFIG = {
    "project_id": os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
    "region": os.environ.get("GCP_REGION", "us-central1"),
    "memory_type": "firestore",  # Use Firestore for memory management in GCP
    "memory_collection": "memories",
    "credentials_path": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "/app/gcp-credentials.json"),
}

# Environment-specific configurations
ENV_CONFIGS = {
    "development": {
        # Local development can use in-memory storage for quick testing
        "memory_type": os.environ.get("MEMORY_TYPE", "in-memory"),
        "memory_collection": "dev_memories",
    },
    "staging": {
        "memory_collection": "staging_memories",
    },
    "production": {
        "memory_collection": "prod_memories",
    },
}


def get_gcp_config() -> Dict[str, Any]:
    """
    Get the GCP configuration based on the current environment.

    Returns:
        A dictionary containing the GCP configuration values
    """
    # Start with base config
    config = BASE_CONFIG.copy()

    # Update with environment-specific settings
    if ENVIRONMENT in ENV_CONFIGS:
        config.update(ENV_CONFIGS[ENVIRONMENT])
    else:
        logger.warning(f"Unknown environment: {ENVIRONMENT}, using default configuration")

    # Log the active configuration (excluding sensitive info)
    safe_config = config.copy()
    if "credentials_path" in safe_config:
        safe_config["credentials_path"] = "***REDACTED***"
    logger.info(f"Active GCP configuration ({ENVIRONMENT}): {safe_config}")

    return config


def get_memory_manager_config() -> Dict[str, Any]:
    """
    Get the specific configuration for the memory manager.

    Returns:
        A dictionary with memory manager specific configuration
    """
    config = get_gcp_config()
    return {
        "memory_type": config.get("memory_type", "in-memory"),
        "collection_name": config.get("memory_collection", "memories"),
        "credentials_path": config.get("credentials_path"),
    }
