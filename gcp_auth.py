#!/usr/bin/env python3
"""
gcp_auth.py - Python helper for non-interactive GCP authentication

This module provides utilities for non-interactive GCP authentication
in Python applications using service account keys. It works with the
same authentication approach as the shell scripts.

Usage:
    import gcp_auth

    # Authenticate with GCP
    if gcp_auth.authenticate():
        # Authentication successful
        client = gcp_auth.get_storage_client()
        # ... use client ...

    # Alternative with context manager
    with gcp_auth.AuthContext() as auth:
        if auth.is_authenticated:
            # Authentication successful
            client = auth.get_storage_client()
            # ... use client ...
"""

import os
import json
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gcp_auth")

# Default paths
DEFAULT_KEY_PATH = os.path.expanduser("~/.gcp/service-account.json")
ENV_SERVICE_ACCOUNT_JSON = "GCP_MASTER_SERVICE_JSON"
ENV_CREDENTIALS_PATH = "GOOGLE_APPLICATION_CREDENTIALS"


def check_auth_configured() -> bool:
    """
    Check if authentication is configured.
    
    Returns:
        bool: True if authentication is configured, False otherwise.
    """
    # Check if key file exists
    if os.path.isfile(DEFAULT_KEY_PATH):
        logger.info(f"Service account key found at {DEFAULT_KEY_PATH}")
        return True
    
    # Check if environment variable is set
    if ENV_SERVICE_ACCOUNT_JSON in os.environ:
        logger.info("Service account JSON found in environment variable")
        return True
    
    # Check if GOOGLE_APPLICATION_CREDENTIALS is set
    if ENV_CREDENTIALS_PATH in os.environ and os.path.isfile(os.environ[ENV_CREDENTIALS_PATH]):
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS points to existing file: {os.environ[ENV_CREDENTIALS_PATH]}")
        return True
    
    logger.warning("No service account credentials found")
    return False


def setup_auth() -> bool:
    """
    Set up authentication by creating key file if needed.
    
    Returns:
        bool: True if setup was successful, False otherwise.
    """
    # If key file already exists, nothing to do
    if os.path.isfile(DEFAULT_KEY_PATH):
        try:
            # Verify the key file is valid JSON
            with open(DEFAULT_KEY_PATH, 'r') as f:
                json.load(f)
            logger.info(f"Service account key at {DEFAULT_KEY_PATH} is valid")
            return True
        except json.JSONDecodeError:
            logger.error(f"Service account key at {DEFAULT_KEY_PATH} is not valid JSON")
            return False
    
    # If we have the environment variable, create key file
    if ENV_SERVICE_ACCOUNT_JSON in os.environ:
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(DEFAULT_KEY_PATH), exist_ok=True)
            
            # Parse JSON to verify it's valid
            service_account_json = json.loads(os.environ[ENV_SERVICE_ACCOUNT_JSON])
            
            # Write to file
            with open(DEFAULT_KEY_PATH, 'w') as f:
                json.dump(service_account_json, f, indent=2)
            
            # Set secure permissions
            os.chmod(DEFAULT_KEY_PATH, 0o600)
            
            logger.info(f"Created service account key at {DEFAULT_KEY_PATH}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to create service account key: {str(e)}")
            return False
    
    logger.warning("No service account credentials available")
    logger.info("Please run ./setup_service_account.sh for guided setup")
    return False


def authenticate() -> bool:
    """
    Authenticate with GCP using service account key.
    
    This function sets the GOOGLE_APPLICATION_CREDENTIALS environment
    variable to point to the service account key file.
    
    Returns:
        bool: True if authentication was successful, False otherwise.
    """
    # If already authenticated, nothing to do
    if ENV_CREDENTIALS_PATH in os.environ and os.path.isfile(os.environ[ENV_CREDENTIALS_PATH]):
        logger.info(f"Already authenticated with credentials at {os.environ[ENV_CREDENTIALS_PATH]}")
        return True
    
    # Check if key file exists or can be created
    if os.path.isfile(DEFAULT_KEY_PATH) or setup_auth():
        # Set environment variable
        os.environ[ENV_CREDENTIALS_PATH] = DEFAULT_KEY_PATH
        logger.info(f"Set {ENV_CREDENTIALS_PATH}={DEFAULT_KEY_PATH}")
        return True
    
    logger.warning("Failed to authenticate with GCP")
    return False


def get_auth_token() -> Optional[str]:
    """
    Get authentication token for API calls.
    
    Returns:
        Optional[str]: Authentication token if available, None otherwise.
    """
    if not authenticate():
        return None
    
    try:
        # Import here to avoid dependencies if not used
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
        
        credentials = service_account.Credentials.from_service_account_file(
            os.environ[ENV_CREDENTIALS_PATH],
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        # Force refresh to get a valid token
        request = Request()
        credentials.refresh(request)
        
        return credentials.token
    except ImportError:
        logger.error("google-auth package not installed. Run: pip install google-auth")
        return None
    except Exception as e:
        logger.error(f"Failed to get authentication token: {str(e)}")
        return None


def get_storage_client():
    """Get authenticated Google Cloud Storage client."""
    if not authenticate():
        return None
    
    try:
        from google.cloud import storage
        return storage.Client()
    except ImportError:
        logger.error("google-cloud-storage package not installed. Run: pip install google-cloud-storage")
        return None


def get_bigquery_client():
    """Get authenticated Google BigQuery client."""
    if not authenticate():
        return None
    
    try:
        from google.cloud import bigquery
        return bigquery.Client()
    except ImportError:
        logger.error("google-cloud-bigquery package not installed. Run: pip install google-cloud-bigquery")
        return None


class AuthContext:
    """Context manager for GCP authentication."""
    
    def __init__(self):
        self.is_authenticated = False
        self.temp_file = None
    
    def __enter__(self):
        self.is_authenticated = authenticate()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up any temporary files if needed
        if self.temp_file and os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
    
    def get_storage_client(self):
        """Get authenticated Google Cloud Storage client."""
        if not self.is_authenticated:
            return None
        return get_storage_client()
    
    def get_bigquery_client(self):
        """Get authenticated Google BigQuery client."""
        if not self.is_authenticated:
            return None
        return get_bigquery_client()


if __name__ == "__main__":
    # Simple command-line functionality
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        if check_auth_configured():
            print("Authentication is configured.")
            sys.exit(0)
        else:
            print("Authentication is not configured.")
            sys.exit(1)
    
    if authenticate():
        print("Successfully authenticated with GCP")
        sys.exit(0)
    else:
        print("Failed to authenticate with GCP")
        sys.exit(1)
