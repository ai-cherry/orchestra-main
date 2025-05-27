#!/usr/bin/env python3
"""
secret_manager.py - Secure Secret Management for MCP

This module provides a secure interface for retrieving secrets from various sources,
with a primary focus on Pulumi-managed environment variables. It includes fallback mechanisms
to local files for development environments.
"""

import asyncio
import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

# No cloud-specific imports required.

logger = logging.getLogger(__name__)


class SecretManager:
    """Interface for retrieving secrets from environment variables or local files."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        local_fallback_path: Optional[str] = None,
        cache_ttl_seconds: int = 300,
    ):
        """Initialize the secret manager.

        Args:
            project_id: Project ID (unused, for compatibility).
            local_fallback_path: Path to local secrets file for development.
            cache_ttl_seconds: Time-to-live for secret cache in seconds.
        """
        self.project_id = project_id or os.environ.get("PROJECT_ID") or "orchestra-local"
        self.local_fallback_path = local_fallback_path
        self.cache_ttl_seconds = cache_ttl_seconds
        self._local_secrets: Dict[str, str] = {}
        self._secret_cache: Dict[str, Dict[str, Any]] = {}
        self._last_init_attempt = 0

        # Try to load local secrets if path is provided
        if self.local_fallback_path:
            self._load_local_secrets()

    def _load_local_secrets(self) -> None:
        """Load secrets from local file if available."""
        if not self.local_fallback_path:
            return

        try:
            path = Path(self.local_fallback_path)
            if path.exists() and path.is_file():
                with open(path, "r") as f:
                    self._local_secrets = json.load(f)
                logger.info(
                    f"Loaded {len(self._local_secrets)} secrets from {self.local_fallback_path}"
                )
            else:
                logger.warning(
                    f"Local secrets file not found: {self.local_fallback_path}"
                )
        except Exception as e:
            logger.error(f"Error loading local secrets: {e}")

    # No cloud client required.

    @lru_cache(maxsize=128)
    def get_secret(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        """Get a secret from Secret Manager with caching.

        Args:
            secret_id: The ID of the secret.
            version_id: The version of the secret. Defaults to "latest".

        Returns:
            The secret value as a string, or None if not found.
        """
        # Check cache first
        cache_key = f"{secret_id}:{version_id}"
        if cache_key in self._secret_cache:
            cache_entry = self._secret_cache[cache_key]
            # Check if cache is still valid
            if (
                cache_entry["timestamp"] + self.cache_ttl_seconds
                > asyncio.get_event_loop().time()
            ):
                logger.debug(f"Using cached secret: {secret_id}")
                return cache_entry["value"]
            # Cache expired, remove it
            del self._secret_cache[cache_key]

        # Try environment variables first (Pulumi-managed)
        env_var = f"{secret_id.upper().replace('-', '_')}"
        secret_value = os.environ.get(env_var)

        # Fall back to local secrets
        if secret_value is None and secret_id in self._local_secrets:
            logger.debug(f"Using local secret: {secret_id}")
            secret_value = self._local_secrets[secret_id]

        # Cache the result if found
        if secret_value is not None:
            self._secret_cache[cache_key] = {
                "value": secret_value,
                "timestamp": asyncio.get_event_loop().time(),
            }

        return secret_value

    # GCP Secret Manager logic removed.

    async def get_secret_async(
        self, secret_id: str, version_id: str = "latest"
    ) -> Optional[str]:
        """Get a secret asynchronously.

        Args:
            secret_id: The ID of the secret.
            version_id: The version of the secret.

        Returns:
            The secret value as a string, or None if not found.
        """
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_secret, secret_id, version_id)

    def clear_cache(self, secret_id: Optional[str] = None) -> None:
        """Clear the secret cache.

        Args:
            secret_id: The ID of the secret to clear, or None to clear all.
        """
        if secret_id:
            # Clear specific secret
            keys_to_remove = [
                k for k in self._secret_cache if k.startswith(f"{secret_id}:")
            ]
            for key in keys_to_remove:
                del self._secret_cache[key]
            logger.debug(f"Cleared cache for secret: {secret_id}")
        else:
            # Clear all secrets
            self._secret_cache.clear()
            logger.debug("Cleared entire secret cache")

            # Also clear the lru_cache
            self.get_secret.cache_clear()

    def get_multiple_secrets(self, secret_ids: list[str]) -> Dict[str, Optional[str]]:
        """Get multiple secrets at once.

        Args:
            secret_ids: List of secret IDs to retrieve.

        Returns:
            Dictionary mapping secret IDs to their values.
        """
        return {secret_id: self.get_secret(secret_id) for secret_id in secret_ids}

    async def get_multiple_secrets_async(
        self, secret_ids: list[str]
    ) -> Dict[str, Optional[str]]:
        """Get multiple secrets asynchronously.

        Args:
            secret_ids: List of secret IDs to retrieve.

        Returns:
            Dictionary mapping secret IDs to their values.
        """
        tasks = [self.get_secret_async(secret_id) for secret_id in secret_ids]
        results = await asyncio.gather(*tasks)
        return dict(zip(secret_ids, results))


# Singleton instance for global use
_default_instance: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get the default SecretManager instance."""
    global _default_instance
    if _default_instance is None:
        _default_instance = SecretManager()
    return _default_instance


def get_secret(secret_id: str, version_id: str = "latest") -> Optional[str]:
    """Convenience function to get a secret from the default SecretManager."""
    return get_secret_manager().get_secret(secret_id, version_id)


async def get_secret_async(secret_id: str, version_id: str = "latest") -> Optional[str]:
    """Convenience function to get a secret asynchronously from the default SecretManager."""
    return await get_secret_manager().get_secret_async(secret_id, version_id)
