#!/usr/bin/env python3
"""
secret_manager.py - Secure Secret Management for MCP

This module provides a secure interface for retrieving secrets from various sources,
with a primary focus on Google Cloud Secret Manager. It includes fallback mechanisms
to environment variables and local files for development environments.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path
import asyncio
from functools import lru_cache

# Import Google Cloud libraries
try:
    from google.cloud import storage
    from google.api_core.exceptions import NotFound, PermissionDenied, InvalidArgument
    HAS_GCP = True
except ImportError:
    HAS_GCP = False

logger = logging.getLogger(__name__)

class SecretManager:
    """Interface for retrieving secrets from various sources with GCP Secret Manager as primary."""
    
    def __init__(
        self, 
        project_id: Optional[str] = None,
        local_fallback_path: Optional[str] = None,
        cache_ttl_seconds: int = 300
    ):
        """Initialize the secret manager.
        
        Args:
            project_id: GCP project ID. If None, will try to get from environment.
            local_fallback_path: Path to local secrets file for development.
            cache_ttl_seconds: Time-to-live for secret cache in seconds.
        """
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID") or "cherry-ai-project"
        self.local_fallback_path = local_fallback_path
        self.cache_ttl_seconds = cache_ttl_seconds
        self._client = None
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
                with open(path, 'r') as f:
                    self._local_secrets = json.load(f)
                logger.info(f"Loaded {len(self._local_secrets)} secrets from {self.local_fallback_path}")
            else:
                logger.warning(f"Local secrets file not found: {self.local_fallback_path}")
        except Exception as e:
            logger.error(f"Error loading local secrets: {e}")
    
    @property
    def client(self):
        """Lazy initialization of the Secret Manager client."""
        # Skip if GCP libraries not available
        if not HAS_GCP:
            return None
            
        # Initialize client if not already done
        if self._client is None:
            try:
                self._client = storage.Client()
                logger.info("Initialized Google Cloud Storage client")
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
                self._client = None
                
        return self._client
    
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
            if cache_entry["timestamp"] + self.cache_ttl_seconds > asyncio.get_event_loop().time():
                logger.debug(f"Using cached secret: {secret_id}")
                return cache_entry["value"]
            # Cache expired, remove it
            del self._secret_cache[cache_key]
        
        # Try GCP Secret Manager
        secret_value = self._get_from_gcp(secret_id, version_id)
        
        # Fall back to local secrets
        if secret_value is None and secret_id in self._local_secrets:
            logger.debug(f"Using local secret: {secret_id}")
            secret_value = self._local_secrets[secret_id]
        
        # Fall back to environment variables
        if secret_value is None:
            env_var = f"{secret_id.upper().replace('-', '_')}"
            secret_value = os.environ.get(env_var)
            if secret_value:
                logger.debug(f"Using environment variable for secret: {secret_id}")
        
        # Cache the result if found
        if secret_value is not None:
            self._secret_cache[cache_key] = {
                "value": secret_value,
                "timestamp": asyncio.get_event_loop().time()
            }
        
        return secret_value
    
    def _get_from_gcp(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        """Get a secret from GCP Storage using the GCP_SECRET_MANAGEMENT_KEY.
        
        Args:
            secret_id: The ID of the secret.
            version_id: The version of the secret (ignored in this implementation).
            
        Returns:
            The secret value as a string, or None if not found.
        """
        if not self.client:
            return None
            
        # Get the bucket name from environment or use default
        bucket_name = os.environ.get("GCP_SECRET_BUCKET", "cherry-ai-secrets")
        secret_key = os.environ.get("GCP_SECRET_MANAGEMENT_KEY")
        
        if not secret_key:
            logger.error("GCP_SECRET_MANAGEMENT_KEY environment variable not set")
            return None
            
        try:
            # Format the object path using the secret key and secret ID
            object_path = f"{secret_key}/{secret_id}"
            
            # Get the bucket and blob
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_path)
            
            # Download the secret content
            content = blob.download_as_text()
            return content
        except NotFound:
            logger.warning(f"Secret not found: {secret_id}")
        except PermissionDenied:
            logger.error(f"Permission denied for secret: {secret_id}")
        except InvalidArgument as e:
            logger.error(f"Invalid argument for secret {secret_id}: {e}")
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            
        return None
    
    async def get_secret_async(self, secret_id: str, version_id: str = "latest") -> Optional[str]:
        """Get a secret asynchronously.
        
        Args:
            secret_id: The ID of the secret.
            version_id: The version of the secret.
            
        Returns:
            The secret value as a string, or None if not found.
        """
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.get_secret, secret_id, version_id
        )
    
    def clear_cache(self, secret_id: Optional[str] = None) -> None:
        """Clear the secret cache.
        
        Args:
            secret_id: The ID of the secret to clear, or None to clear all.
        """
        if secret_id:
            # Clear specific secret
            keys_to_remove = [k for k in self._secret_cache if k.startswith(f"{secret_id}:")]
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
    
    async def get_multiple_secrets_async(self, secret_ids: list[str]) -> Dict[str, Optional[str]]:
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