"""
Secret Manager Service for AI Orchestra.

This module provides a service for accessing secrets stored in Google Cloud Secret Manager.
"""

import logging
import os
from typing import Dict, Optional

from google.api_core.exceptions import NotFound, PermissionDenied
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretManagerService:
    """
    Service for accessing secrets from Google Cloud Secret Manager.

    This service provides a unified interface for accessing secrets stored in
    Google Cloud Secret Manager, with caching and error handling.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Secret Manager service.

        Args:
            project_id: The GCP project ID. If not provided, it will be read from
                       the GCP_PROJECT_ID environment variable.
        """
        self.project_id = project_id or os.environ.get(
            "GCP_PROJECT_ID", "cherry-ai-project"
        )
        self.client = secretmanager.SecretManagerServiceClient()
        self._cache: Dict[str, str] = {}

    def get_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Get a secret from Secret Manager.

        Args:
            secret_id: The ID of the secret
            version_id: The version of the secret (default: "latest")

        Returns:
            The secret value as a string

        Raises:
            ValueError: If the secret cannot be accessed
        """
        # Check cache first
        cache_key = f"{secret_id}:{version_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Build the resource name
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"

        try:
            # Access the secret
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")

            # Cache the result
            self._cache[cache_key] = secret_value

            return secret_value
        except NotFound:
            logger.error(f"Secret {secret_id} not found")
            raise ValueError(f"Secret {secret_id} not found")
        except PermissionDenied:
            logger.error(f"Permission denied for secret {secret_id}")
            raise ValueError(f"Permission denied for secret {secret_id}")
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            raise ValueError(f"Error accessing secret {secret_id}: {e}")

    def get_llm_api_key(self, provider: str) -> str:
        """
        Get an API key for an LLM provider.

        Args:
            provider: The LLM provider (e.g., "openai", "anthropic", "gemini")

        Returns:
            The API key as a string
        """
        secret_id = f"{provider}-api-key"
        return self.get_secret(secret_id)

    def clear_cache(self) -> None:
        """Clear the secret cache."""
        self._cache.clear()


# Singleton instance
_secret_manager: Optional[SecretManagerService] = None


def get_secret_manager(project_id: Optional[str] = None) -> SecretManagerService:
    """
    Get the Secret Manager service instance.

    Args:
        project_id: The GCP project ID (optional)

    Returns:
        The Secret Manager service instance
    """
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManagerService(project_id)
    return _secret_manager
