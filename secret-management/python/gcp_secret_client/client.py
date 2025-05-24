"""
Primary client class for interacting with GCP Secret Manager.
"""

import datetime
import json
import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

try:
    from google.api_core import exceptions as gcp_exceptions
    from google.auth import exceptions as auth_exceptions
    from google.cloud import secretmanager
except ImportError:
    raise ImportError(
        "Google Cloud Secret Manager dependencies not installed. "
        "Please install with: pip install google-cloud-secret-manager"
    )

from .exceptions import (
    SecretAccessError,
    SecretAccessPermissionError,
    SecretNotFoundError,
    SecretOperationError,
    SecretVersionNotFoundError,
)

# Type variables for generic functions
T = TypeVar("T")
R = TypeVar("R")

# Configure logging
logger = logging.getLogger(__name__)


def retry(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    retry_errors: Optional[List[type]] = None,
):
    """Retry decorator for API call functions."""
    if retry_errors is None:
        retry_errors = [
            gcp_exceptions.DeadlineExceeded,
            gcp_exceptions.ServiceUnavailable,
            gcp_exceptions.InternalServerError,
            gcp_exceptions.GatewayTimeout,
        ]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(retry_errors) as e:
                    last_exception = e
                    if attempt < max_retries:
                        sleep_time = backoff_factor * (2**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. " f"Retrying in {sleep_time:.2f}s..."
                        )
                        time.sleep(sleep_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
            raise last_exception

        return wrapper

    return decorator


class CacheEntry:
    """Container for cached secret values with expiration."""

    def __init__(self, value: str, expiry: Optional[datetime.datetime] = None):
        self.value = value
        self.expiry = expiry
        self.created_at = datetime.datetime.now()

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.expiry is None:
            return False
        return datetime.datetime.now() > self.expiry

    def __str__(self) -> str:
        return f"CacheEntry(created={self.created_at}, expires={self.expiry})"


class SecretClient:
    """
    Client for accessing secrets from Google Cloud Secret Manager
    with caching, error handling, and fallback mechanisms.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        cache_ttl: int = 300,
        max_retries: int = 3,
        fallback_to_env: bool = True,
        env_prefix: str = "",
        client: Optional[secretmanager.SecretManagerServiceClient] = None,
    ):
        """
        Initialize a new SecretClient.

        Args:
            project_id: GCP project ID. If None, detected from environment.
            cache_ttl: Time-to-live for cached secrets, in seconds (0 to disable).
            max_retries: Maximum number of retry attempts for transient failures.
            fallback_to_env: Whether to check environment variables as fallback.
            env_prefix: Prefix for environment variables (e.g., "APP_").
            client: Existing Secret Manager client to reuse.
        """
        # Detect project ID from environment if not provided
        self.project_id = project_id or os.environ.get("GCP_PROJECT")
        if not self.project_id:
            try:
                import google.auth

                _, self.project_id = google.auth.default()
            except (ImportError, auth_exceptions.DefaultCredentialsError):
                logger.warning(
                    "Project ID not specified and could not be auto-detected. "
                    "You'll need to specify project_id in each method call."
                )

        # Initialize client
        self.client = client or secretmanager.SecretManagerServiceClient()

        # Configure caching
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, CacheEntry] = {}

        # Retry configuration
        self.max_retries = max_retries

        # Fallback configuration
        self.fallback_to_env = fallback_to_env
        self.env_prefix = env_prefix

        logger.debug(
            f"Initialized SecretClient for project '{self.project_id}' "
            f"with cache_ttl={cache_ttl}s, max_retries={max_retries}"
        )

    def _format_secret_path(self, secret_id: str, version: str = "latest", project_id: Optional[str] = None) -> str:
        """
        Format the full path to a secret.

        Args:
            secret_id: The name/ID of the secret.
            version: The version of the secret (number or 'latest').
            project_id: Project ID override.

        Returns:
            Fully qualified secret path string.

        Raises:
            ValueError: If project_id is not available.
        """
        project = project_id or self.project_id
        if not project:
            raise ValueError("Project ID must be specified")

        # Clean up secret_id (remove any leading/trailing whitespace)
        secret_id = secret_id.strip()

        # Create the secret path
        return f"projects/{project}/secrets/{secret_id}/versions/{version}"

    def _get_from_environment(self, secret_id: str) -> Optional[str]:
        """
        Try to get a secret value from environment variables.

        Args:
            secret_id: The name/ID of the secret.

        Returns:
            Secret value if found in environment, None otherwise.
        """
        if not self.fallback_to_env:
            return None

        # Try different formats of environment variable names
        variations = [
            f"{self.env_prefix}{secret_id}",
            f"{self.env_prefix}{secret_id.upper()}",
            secret_id,
            secret_id.upper(),
        ]

        for var_name in variations:
            value = os.environ.get(var_name)
            if value is not None:
                logger.debug(f"Secret '{secret_id}' found in environment as '{var_name}'")
                return value

        return None

    def _cache_secret(self, cache_key: str, value: str) -> None:
        """
        Store a secret value in the cache.

        Args:
            cache_key: The key to use for caching.
            value: The secret value to cache.
        """
        if self.cache_ttl <= 0:
            return  # Caching disabled

        expiry = None
        if self.cache_ttl > 0:
            expiry = datetime.datetime.now() + datetime.timedelta(seconds=self.cache_ttl)

        self.cache[cache_key] = CacheEntry(value, expiry)
        logger.debug(f"Cached secret '{cache_key}' until {expiry}")

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Try to get a secret value from the cache.

        Args:
            cache_key: The cache key to look up.

        Returns:
            Cached value if found and not expired, None otherwise.
        """
        if self.cache_ttl <= 0:
            return None  # Caching disabled

        entry = self.cache.get(cache_key)
        if entry is None:
            return None

        if entry.is_expired:
            logger.debug(f"Cached secret '{cache_key}' has expired")
            del self.cache[cache_key]
            return None

        logger.debug(f"Retrieved secret '{cache_key}' from cache")
        return entry.value

    @retry(max_retries=3)
    def _access_secret_version(self, secret_path: str, allow_missing: bool = False) -> str:
        """
        Access a secret version with retries.

        Args:
            secret_path: Full path to the secret version.
            allow_missing: Whether to return None for missing secrets.

        Returns:
            The secret value as a string.

        Raises:
            SecretNotFoundError: If the secret doesn't exist.
            SecretVersionNotFoundError: If the version doesn't exist.
            SecretAccessPermissionError: If permission is denied.
            SecretOperationError: For other errors.
        """
        try:
            # Access the secret version
            response = self.client.access_secret_version(name=secret_path)

            # Decode the payload
            payload = response.payload.data
            return payload.decode("UTF-8")

        except gcp_exceptions.NotFound as e:
            if "Secret" in str(e) and "not found" in str(e):
                if allow_missing:
                    return None
                secret_id = secret_path.split("/secrets/")[1].split("/versions")[0]
                project_id = secret_path.split("/projects/")[1].split("/secrets")[0]
                raise SecretNotFoundError(secret_id, project_id)
            elif "Version" in str(e) and "not found" in str(e):
                if allow_missing:
                    return None
                secret_id = secret_path.split("/secrets/")[1].split("/versions")[0]
                version = secret_path.split("/versions/")[1]
                project_id = secret_path.split("/projects/")[1].split("/secrets")[0]
                raise SecretVersionNotFoundError(secret_id, version, project_id)
            else:
                raise SecretOperationError(
                    secret_path,
                    "access",
                    e,
                    secret_path.split("/projects/")[1].split("/secrets")[0],
                )

        except gcp_exceptions.PermissionDenied:
            secret_id = secret_path.split("/secrets/")[1].split("/versions")[0]
            project_id = secret_path.split("/projects/")[1].split("/secrets")[0]
            raise SecretAccessPermissionError(secret_id, project_id)

        except Exception as e:
            secret_id = secret_path.split("/secrets/")[1].split("/versions")[0]
            raise SecretOperationError(
                secret_id,
                "access",
                e,
                secret_path.split("/projects/")[1].split("/secrets")[0],
            )

    def get_secret(
        self,
        secret_id: str,
        version: str = "latest",
        project_id: Optional[str] = None,
        fallback: Optional[Any] = None,
        transform: Optional[Callable[[str], T]] = None,
        use_cache: bool = True,
        allow_missing: bool = False,
    ) -> Union[str, T, Any]:
        """
        Get a secret value from Secret Manager.

        Args:
            secret_id: The name/ID of the secret.
            version: The version to access (number or 'latest').
            project_id: Project ID override.
            fallback: Value to return if the secret is not found.
            transform: Function to transform the secret value.
            use_cache: Whether to use cached values.
            allow_missing: Whether to return the fallback for missing secrets
                          without raising an exception.

        Returns:
            The secret value, transformed if a transform function was provided.

        Raises:
            SecretAccessError: If the secret couldn't be accessed and no fallback
                              was provided.
        """
        # Create a cache key for this secret
        project = project_id or self.project_id
        cache_key = f"{project}:{secret_id}:{version}"

        # Check cache first if caching is enabled
        if use_cache and self.cache_ttl > 0:
            cached_value = self._get_from_cache(cache_key)
            if cached_value is not None:
                return transform(cached_value) if transform else cached_value

        try:
            # Try to get from Secret Manager
            secret_path = self._format_secret_path(secret_id, version, project_id)
            value = self._access_secret_version(secret_path, allow_missing)

            # If the value is None (secret not found) and allow_missing,
            # check environment then return fallback
            if value is None and allow_missing:
                env_value = self._get_from_environment(secret_id)
                if env_value is not None:
                    return transform(env_value) if transform else env_value
                return fallback

            # Cache the raw value
            if use_cache and self.cache_ttl > 0 and value is not None:
                self._cache_secret(cache_key, value)

            # Transform if requested
            if transform and value is not None:
                return transform(value)

            return value

        except SecretAccessError as e:
            # Try environment variables as fallback
            env_value = self._get_from_environment(secret_id)
            if env_value is not None:
                return transform(env_value) if transform else env_value

            # If we have a fallback value, use it
            if fallback is not None:
                logger.warning(f"Couldn't access secret '{secret_id}', using fallback value. Error: {e}")
                return fallback

            # Otherwise propagate the exception
            raise

    def get_json_secret(
        self,
        secret_id: str,
        version: str = "latest",
        project_id: Optional[str] = None,
        fallback: Optional[Any] = None,
        use_cache: bool = True,
        allow_missing: bool = False,
    ) -> Dict[str, Any]:
        """
        Get and parse a JSON secret value.

        Args:
            secret_id: The name/ID of the secret.
            version: The version to access (number or 'latest').
            project_id: Project ID override.
            fallback: Value to return if the secret is not found.
            use_cache: Whether to use cached values.
            allow_missing: Whether to return the fallback for missing secrets
                          without raising an exception.

        Returns:
            The parsed JSON object.

        Raises:
            SecretAccessError: If the secret couldn't be accessed.
            ValueError: If the secret value is not valid JSON.
        """

        def parse_json(value: str) -> Dict[str, Any]:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise ValueError(f"Secret '{secret_id}' is not valid JSON: {e}")

        return self.get_secret(
            secret_id=secret_id,
            version=version,
            project_id=project_id,
            fallback=fallback,
            transform=parse_json,
            use_cache=use_cache,
            allow_missing=allow_missing,
        )

    def get_multiple_secrets(
        self,
        secret_ids: List[str],
        version: str = "latest",
        project_id: Optional[str] = None,
        fallbacks: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        allow_missing: bool = False,
    ) -> Dict[str, str]:
        """
        Get multiple secrets in a batch.

        Args:
            secret_ids: List of secret IDs to retrieve.
            version: The version to access for all secrets.
            project_id: Project ID override.
            fallbacks: Dictionary of fallback values by secret ID.
            use_cache: Whether to use cached values.
            allow_missing: Whether to return fallbacks for missing secrets
                          without raising exceptions.

        Returns:
            Dictionary of secret values by secret ID.

        Raises:
            SecretAccessError: If any secret couldn't be accessed and no
                              fallback was provided.
        """
        results = {}
        errors = {}

        for secret_id in secret_ids:
            try:
                fallback = None
                if fallbacks and secret_id in fallbacks:
                    fallback = fallbacks[secret_id]

                value = self.get_secret(
                    secret_id=secret_id,
                    version=version,
                    project_id=project_id,
                    fallback=fallback,
                    use_cache=use_cache,
                    allow_missing=allow_missing,
                )

                results[secret_id] = value

            except Exception as e:
                errors[secret_id] = str(e)

        if errors and not allow_missing:
            error_msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
            raise SecretAccessError(f"Failed to retrieve some secrets: {error_msg}")

        return results

    def clear_cache(self, secret_id: Optional[str] = None, project_id: Optional[str] = None) -> None:
        """
        Clear cached secrets.

        Args:
            secret_id: If provided, clear only this secret from the cache.
            project_id: If provided with secret_id, clear only the specific project's secret.
        """
        if secret_id:
            project = project_id or self.project_id
            pattern = f"{project}:{secret_id}:"

            # Remove matching entries
            keys_to_remove = [k for k in self.cache if k.startswith(pattern)]
            for key in keys_to_remove:
                del self.cache[key]

            logger.debug(f"Cleared {len(keys_to_remove)} cached entries for secret '{secret_id}'")
        else:
            # Clear all cached secrets
            count = len(self.cache)
            self.cache.clear()
            logger.debug(f"Cleared all {count} cached secrets")
