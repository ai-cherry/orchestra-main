#!/usr/bin/env python3
"""
simplified_gcp_auth.py - Streamlined GCP Authentication for Single-Developer Projects

This module provides simplified Google Cloud Platform authentication for
single-developer, single-user projects. It prioritizes development velocity
and ease of use over complex security measures.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("simplified-gcp-auth")


class SimplifiedGCPAuth:
    """Simplified GCP authentication for single-developer projects."""

    def __init__(
        self,
        service_account_path: Optional[str] = None,
        project_id: Optional[str] = None,
        cache_credentials: bool = True,
    ):
        """
        Initialize the simplified GCP authentication.

        Args:
            service_account_path: Path to service account key file
            project_id: GCP project ID (if None, will be extracted from key file)
            cache_credentials: Whether to cache credentials for performance
        """
        self.service_account_path = service_account_path
        self.project_id = project_id
        self.cache_credentials = cache_credentials
        self._credentials_cache = None

        # Try to find service account key if not provided
        if not self.service_account_path:
            self._find_service_account_key()

        # Extract project ID from service account key if not provided
        if not self.project_id and self.service_account_path:
            self._extract_project_id()

    def _find_service_account_key(self) -> None:
        """Find service account key file in common locations."""
        common_locations = [
            "service-account-key.json",
            "service_account_key.json",
            "key.json",
            os.path.expanduser("~/.gcp/service-account-key.json"),
            os.path.expanduser("~/.config/gcloud/service-account-key.json"),
        ]

        for location in common_locations:
            if os.path.exists(location):
                self.service_account_path = location
                logger.info(f"Found service account key at: {location}")
                return

        logger.warning("No service account key file found")

    def _extract_project_id(self) -> None:
        """Extract project ID from service account key file."""
        try:
            with open(self.service_account_path, "r") as f:
                key_data = json.load(f)
                if "project_id" in key_data:
                    self.project_id = key_data["project_id"]
                    logger.info(f"Extracted project ID: {self.project_id}")
        except Exception as e:
            logger.error(f"Error extracting project ID: {e}")

    def get_credentials(self) -> Any:
        """
        Get GCP credentials for authentication.

        Returns:
            Google Auth credentials object
        """
        # Return cached credentials if available
        if self.cache_credentials and self._credentials_cache:
            return self._credentials_cache

        try:
            from google.oauth2 import service_account
            from google.auth.exceptions import DefaultCredentialsError

            # Try service account authentication first
            if self.service_account_path and os.path.exists(self.service_account_path):
                logger.info(f"Using service account key: {self.service_account_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path
                )

                # Cache credentials if enabled
                if self.cache_credentials:
                    self._credentials_cache = credentials

                return credentials

            # Fall back to application default credentials
            logger.info("Using application default credentials")
            from google.auth import default

            credentials, project_id = default()

            # Update project ID if not set
            if not self.project_id and project_id:
                self.project_id = project_id

            # Cache credentials if enabled
            if self.cache_credentials:
                self._credentials_cache = credentials

            return credentials

        except ImportError:
            logger.error("Google Cloud libraries not installed")
            logger.info("Install with: pip install google-auth google-cloud-core")
            return None
        except DefaultCredentialsError:
            logger.error("No default credentials found")
            logger.info(
                "Run 'gcloud auth application-default login' or provide a service account key"
            )
            return None
        except Exception as e:
            logger.error(f"Error getting credentials: {e}")
            return None

    def get_project_id(self) -> Optional[str]:
        """Get the GCP project ID."""
        return self.project_id

    def initialize_client(self, client_class: Any, **kwargs) -> Optional[Any]:
        """
        Initialize a GCP client with authentication.

        Args:
            client_class: The GCP client class to initialize
            **kwargs: Additional arguments to pass to the client constructor

        Returns:
            Initialized GCP client or None if initialization failed
        """
        credentials = self.get_credentials()
        if not credentials:
            return None

        try:
            # Initialize client with credentials
            client = client_class(
                credentials=credentials, project=self.project_id, **kwargs
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing client: {e}")
            return None


def get_default_auth() -> SimplifiedGCPAuth:
    """Get a default SimplifiedGCPAuth instance."""
    return SimplifiedGCPAuth()


def initialize_firestore() -> Optional[Any]:
    """Initialize Firestore client with simplified authentication."""
    try:
        from google.cloud import firestore

        auth = get_default_auth()
        return auth.initialize_client(firestore.Client)
    except ImportError:
        logger.error("Firestore library not installed")
        logger.info("Install with: pip install google-cloud-firestore")
        return None


def initialize_storage() -> Optional[Any]:
    """Initialize Storage client with simplified authentication."""
    try:
        from google.cloud import storage

        auth = get_default_auth()
        return auth.initialize_client(storage.Client)
    except ImportError:
        logger.error("Storage library not installed")
        logger.info("Install with: pip install google-cloud-storage")
        return None


def initialize_secretmanager() -> Optional[Any]:
    """Initialize Secret Manager client with simplified authentication."""
    try:
        from google.cloud import secretmanager

        auth = get_default_auth()
        return auth.initialize_client(secretmanager.SecretManagerServiceClient)
    except ImportError:
        logger.error("Secret Manager library not installed")
        logger.info("Install with: pip install google-cloud-secret-manager")
        return None


if __name__ == "__main__":
    # Simple CLI for testing authentication
    import argparse

    parser = argparse.ArgumentParser(description="Test simplified GCP authentication")
    parser.add_argument("--key", help="Path to service account key file")
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument(
        "--test",
        choices=["firestore", "storage", "secretmanager"],
        help="Test specific client initialization",
    )

    args = parser.parse_args()

    # Create auth instance
    auth = SimplifiedGCPAuth(service_account_path=args.key, project_id=args.project)

    # Get credentials
    credentials = auth.get_credentials()
    if credentials:
        print(f"Successfully obtained credentials")
        print(f"Project ID: {auth.get_project_id()}")

        # Test specific client if requested
        if args.test == "firestore":
            client = initialize_firestore()
            if client:
                print("Successfully initialized Firestore client")
        elif args.test == "storage":
            client = initialize_storage()
            if client:
                print("Successfully initialized Storage client")
        elif args.test == "secretmanager":
            client = initialize_secretmanager()
            if client:
                print("Successfully initialized Secret Manager client")
    else:
        print("Failed to obtain credentials")
