"""
GCP Secret Manager Client Library
=================================

A robust and efficient client library for accessing secrets from Google Cloud Secret Manager 
with advanced features like caching, error handling, and fallback mechanisms.

Example usage:

    from gcp_secret_client import SecretClient

    # Initialize client
    client = SecretClient(
        project_id="my-project",
        cache_ttl=300  # Cache secrets for 5 minutes
    )

    # Access a secret
    api_key = client.get_secret("API_KEY")
    
    # Access with version control
    db_password = client.get_secret("DB_PASSWORD", version="latest")
    
    # Access with fallback value
    debug_mode = client.get_secret(
        "DEBUG_MODE", 
        fallback="false", 
        transform=lambda x: x.lower() == "true"
    )
"""

from .client import SecretClient
from .exceptions import (
    SecretAccessError,
    SecretNotFoundError,
    SecretVersionNotFoundError,
)

__all__ = [
    "SecretClient",
    "SecretAccessError",
    "SecretNotFoundError",
    "SecretVersionNotFoundError",
]

__version__ = "0.1.0"
