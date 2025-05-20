"""
Secret Manager Module for Orchestra LLM Services
------------------------------------------------

This module provides secure access to API keys and configurations using Google Cloud Secret Manager.
It implements best practices for secret handling including:
- Workload identity support
- Secret versioning
- Caching with expiration
- Centralized management of all LLM provider credentials

Usage:
    from core.orchestrator.src.services.llm.secret_manager import SecretManager
    
    # Initialize with your GCP project
    secret_manager = SecretManager(project_id="your-project-id")
    
    # Get a secret (cached with expiration)
    api_key = secret_manager.get_secret("ANTHROPIC_API_KEY")
    
    # Access all LLM credentials
    llm_credentials = secret_manager.get_llm_credentials()
"""

import os
import time
import logging
from typing import Dict, Optional, Any, Union
from functools import lru_cache

# Import GCP libraries if available
try:
    from google.cloud import secretmanager
    from google.cloud.secretmanager_v1.types import AccessSecretVersionResponse
    from google.auth import default

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

logger = logging.getLogger(__name__)

# Default cache timeout - secrets will be refreshed after this time
DEFAULT_SECRET_TIMEOUT_SECONDS = 3600


class SecretManager:
    """
    Manages secure access to API keys and other sensitive configurations
    using Google Cloud Secret Manager with fallback to environment variables.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        cache_timeout: int = DEFAULT_SECRET_TIMEOUT_SECONDS,
    ):
        """
        Initialize the Secret Manager.

        Args:
            project_id: Google Cloud project ID (defaults to environment or current project)
            cache_timeout: How long to cache secrets before refreshing (seconds)
        """
        self.project_id = project_id
        self.cache_timeout = cache_timeout
        self._secret_cache = {}  # Type: Dict[str, Dict[str, Any]]

        # Initialize GCP client if available
        self.client = None
        if GOOGLE_CLOUD_AVAILABLE:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                if not self.project_id:
                    # Try to get project ID from credentials
                    _, project_id = default()
                    self.project_id = project_id
                logger.info(
                    f"Secret Manager initialized with project: {self.project_id}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Secret Manager client: {str(e)}")
                logger.warning("Will fall back to environment variables for secrets")
        else:
            logger.warning(
                "Google Cloud libraries not available. Using environment variables."
            )
            logger.warning("Install with: pip install google-cloud-secretmanager")

    def get_secret(self, secret_id: str, version: str = "latest") -> Optional[str]:
        """
        Get a secret from the Secret Manager or environment variable.

        Args:
            secret_id: The name of the secret to access
            version: The version of the secret to access (default: latest)

        Returns:
            The secret value as a string, or None if not found
        """
        # Check cache first
        cached = self._get_from_cache(secret_id, version)
        if cached is not None:
            return cached

        # First try Secret Manager if available
        if self.client and self.project_id:
            try:
                secret_path = (
                    f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
                )
                response = self.client.access_secret_version(name=secret_path)
                secret_value = response.payload.data.decode("UTF-8")

                # Cache the result
                self._add_to_cache(secret_id, version, secret_value)

                return secret_value
            except Exception as e:
                logger.warning(f"Error accessing secret {secret_id}: {str(e)}")
                # Fall through to environment variable

        # Fall back to environment variables
        env_value = os.environ.get(secret_id)
        if env_value:
            logger.debug(f"Retrieved {secret_id} from environment variable")
            # Cache the environment variable result too
            self._add_to_cache(secret_id, version, env_value)
            return env_value

        logger.warning(
            f"Secret {secret_id} not found in Secret Manager or environment variables"
        )
        return None

    def _add_to_cache(self, secret_id: str, version: str, value: str) -> None:
        """Add a secret to the cache with the current timestamp."""
        self._secret_cache[f"{secret_id}:{version}"] = {
            "value": value,
            "timestamp": time.time(),
        }

    def _get_from_cache(self, secret_id: str, version: str) -> Optional[str]:
        """Get a secret from the cache if not expired."""
        cache_key = f"{secret_id}:{version}"
        if cache_key in self._secret_cache:
            cached_data = self._secret_cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - cached_data["timestamp"] < self.cache_timeout:
                return cached_data["value"]
            # Expired
            del self._secret_cache[cache_key]
        return None

    @lru_cache(maxsize=1)
    def get_llm_credentials(self) -> Dict[str, str]:
        """
        Get all LLM provider credentials in one call.

        Returns:
            Dictionary mapping provider names to their API keys and configurations
        """
        credentials = {}

        # Commonly used LLM provider credentials
        credential_keys = [
            "OPENAI_API_KEY",
            "AZURE_API_KEY",
            "AZURE_API_BASE",
            "ANTHROPIC_API_KEY",
            "PORTKEY_API_KEY",
            "PORTKEY_CONFIG",
            "PORTKEY_VIRTUAL_KEY",
            "OPENROUTER_API_KEY",
            "LITELLM_MASTER_KEY",
            "COHERE_API_KEY",
            "GOOGLE_API_KEY",
            "MISTRAL_API_KEY",
        ]

        # Fetch all keys in one batch
        for key in credential_keys:
            value = self.get_secret(key)
            if value:
                credentials[key] = value

        return credentials

    def rotate_secret(self, secret_id: str) -> bool:
        """
        Request a rotation of the specified secret.
        Only works with Google Cloud Secret Manager.

        Args:
            secret_id: The name of the secret to rotate

        Returns:
            True if rotation was successfully requested, False otherwise
        """
        if not (self.client and self.project_id):
            logger.error("Secret rotation requires Google Cloud Secret Manager")
            return False

        try:
            # This creates a new version with the current value
            # In a real implementation, you would generate a new value
            current_value = self.get_secret(secret_id)
            if not current_value:
                logger.error(f"Cannot rotate {secret_id}: current value not found")
                return False

            secret_path = f"projects/{self.project_id}/secrets/{secret_id}"

            # Add a new version with the same value (in practice, you would create a new credential)
            response = self.client.add_secret_version(
                parent=secret_path, payload={"data": current_value.encode("UTF-8")}
            )

            # Clear from cache
            for key in list(self._secret_cache.keys()):
                if key.startswith(f"{secret_id}:"):
                    del self._secret_cache[key]

            logger.info(f"Rotated secret {secret_id}, new version: {response.name}")
            return True
        except Exception as e:
            logger.error(f"Error rotating secret {secret_id}: {str(e)}")
            return False


# Singleton instance for convenience
_default_secret_manager = None


def get_secret_manager(project_id: Optional[str] = None) -> SecretManager:
    """
    Get or create the default SecretManager instance.

    Args:
        project_id: Optional Google Cloud project ID to use

    Returns:
        A SecretManager instance
    """
    global _default_secret_manager
    if _default_secret_manager is None:
        _default_secret_manager = SecretManager(project_id=project_id)
    return _default_secret_manager
