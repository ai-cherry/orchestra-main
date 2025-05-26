"""
Secret Manager integration for Orchestra.

This module provides utilities for accessing secrets from both:
- Environment variables (.env file)
- GCP Secret Manager

It maintains backward compatibility with the existing .env approach
while enabling more secure secret access via Secret Manager.
"""

import logging
import os
from functools import lru_cache
from typing import Optional

from .settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Type alias
Secret = str


@lru_cache(maxsize=128)
def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[Secret]:
    """
    Get a secret value with fallback behavior:
    1. Try environment variable first (backwards compatibility)
    2. Try Secret Manager if environment variable is not set
    3. Return default value if provided and neither source has the secret

    Args:
        secret_name: The name of the secret (e.g., "openai-api-key")
        default: Default value to return if secret is not found

    Returns:
        The secret value or default if not found

    Example:
        api_key = get_secret("openai-api-key")
    """
    # Settings for GCP project details
    settings = get_settings()

    # Convert secret name format: "openai-api-key" to "OPENAI_API_KEY"
    env_var_name = secret_name.replace("-", "_").upper()

    # Try environment variable first (backward compatibility)
    if env_var_name in os.environ and os.environ[env_var_name]:
        return os.environ[env_var_name]

    # Only try Secret Manager if GCP project ID is set
    if settings.GCP_PROJECT_ID:
        try:
            return _get_from_secret_manager(
                secret_name, settings.GCP_PROJECT_ID, settings.ENVIRONMENT
            )
        except Exception as e:
            logger.warning(
                f"Failed to get secret '{secret_name}' from Secret Manager: {e}"
            )

    # Return default value if provided
    return default


def _get_from_secret_manager(
    secret_name: str, project_id: str, environment: str
) -> Optional[Secret]:
    """
    Get a secret value from Google Secret Manager.

    Args:
        secret_name: Base name of the secret (e.g., "openai-api-key")
        project_id: GCP project ID
        environment: Environment name (dev, staging, prod)

    Returns:
        Secret value or None if not found

    Raises:
        Exception: If there's an error accessing Secret Manager
    """
    # Import here to avoid unnecessary dependencies if using env vars only
    try:
        from google.cloud import secretmanager
    except ImportError:
        logger.warning(
            "google-cloud-secret-manager package not installed. "
            "Install it with pip: pip install google-cloud-secret-manager"
        )
        return None

    # Generate the secret ID with environment
    full_secret_id = f"{secret_name}-{environment}"
    secret_path = f"projects/{project_id}/secrets/{full_secret_id}/versions/latest"

    # Create the client
    client = secretmanager.SecretManagerServiceClient()

    # Access the secret version
    try:
        response = client.access_secret_version(name=secret_path)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(f"Error accessing secret {full_secret_id}: {e}")
        return None


# Dictionary-like interface for accessing secrets
class SecretManager:
    """Dictionary-like interface for accessing secrets."""

    def __init__(self):
        """Initialize the secret manager."""

    def __getitem__(self, key: str) -> Optional[Secret]:
        """Get a secret value."""
        return get_secret(key)

    def get(self, key: str, default: Optional[str] = None) -> Optional[Secret]:
        """Get a secret value with a default fallback."""
        return get_secret(key, default)

    def __contains__(self, key: str) -> bool:
        """Check if a secret exists."""
        return get_secret(key) is not None


# Singleton instance
secrets = SecretManager()
