#!/usr/bin/env python3
"""
gcp_auth.py - Streamlined GCP Authentication Helper

This module provides a simplified authentication helper for Google Cloud Platform
services, leveraging the GCP_MASTER_SERVICE_JSON credential for direct authentication.
It implements a singleton pattern to reuse credentials across different services.
"""

import json
import logging
import os
import tempfile
from typing import Optional

# Import GCP libraries
try:
    from google.cloud import aiplatform, firestore, storage
    from google.oauth2 import service_account
except ImportError:
    logging.warning(
        "Google Cloud libraries not installed. Install with: pip install google-cloud-firestore google-cloud-storage google-cloud-aiplatform"
    )

logger = logging.getLogger(__name__)


class GCPAuth:
    """Simplified GCP authentication helper with singleton pattern."""

    _instance: Optional["GCPAuth"] = None
    _credentials = None
    _project_id: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "GCPAuth":
        """Get or create the singleton instance.

        Returns:
            GCPAuth: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize with credentials from environment."""
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from environment variable.

        Attempts to load credentials from GCP_MASTER_SERVICE_JSON environment variable.
        Falls back to application default credentials if not available.
        """
        creds_json = os.environ.get("GCP_MASTER_SERVICE_JSON")
        if creds_json:
            try:
                # Create a temporary file to store the credentials
                with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp:
                    temp.write(creds_json)
                    temp_path = temp.name

                # Load credentials from the temporary file
                self._credentials = service_account.Credentials.from_service_account_file(temp_path)

                # Extract project ID
                creds_data = json.loads(creds_json)
                self._project_id = creds_data.get("project_id")

                # Clean up the temporary file
                os.unlink(temp_path)

                logger.info(f"Loaded GCP credentials for project: {self._project_id}")
            except Exception as e:
                logger.error(f"Error loading GCP credentials: {e}")
                self._credentials = None
                self._project_id = None
        else:
            # Fall back to application default credentials
            logger.info("GCP_MASTER_SERVICE_JSON not found, using application default credentials")
            self._credentials = None

            # Try to get project ID from environment
            self._project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    def get_project_id(self) -> Optional[str]:
        """Get the GCP project ID.

        Returns:
            Optional[str]: The project ID or None if not available
        """
        return self._project_id

    def get_firestore_client(self) -> firestore.Client:
        """Get authenticated Firestore client.

        Returns:
            firestore.Client: Authenticated Firestore client
        """
        if self._credentials:
            return firestore.Client(credentials=self._credentials, project=self._project_id)
        return firestore.Client()

    def get_firestore_async_client(self) -> firestore.AsyncClient:
        """Get authenticated Firestore async client.

        Returns:
            firestore.AsyncClient: Authenticated Firestore async client
        """
        if self._credentials:
            return firestore.AsyncClient(credentials=self._credentials, project=self._project_id)
        return firestore.AsyncClient()

    def get_storage_client(self) -> storage.Client:
        """Get authenticated Storage client.

        Returns:
            storage.Client: Authenticated Storage client
        """
        if self._credentials:
            return storage.Client(credentials=self._credentials, project=self._project_id)
        return storage.Client()

    def init_vertex_ai(self, location: str = "us-west4") -> None:
        """Initialize Vertex AI with credentials.

        Args:
            location: GCP region for Vertex AI (default: "us-west4")
        """
        project = self._project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            raise ValueError("Project ID not available. Set GOOGLE_CLOUD_PROJECT environment variable.")

        if self._credentials:
            aiplatform.init(project=project, location=location, credentials=self._credentials)
        else:
            aiplatform.init(project=project, location=location)

        logger.info(f"Initialized Vertex AI for project {project} in {location}")

    def get_credentials(self) -> Optional[service_account.Credentials]:
        """Get the loaded credentials.

        Returns:
            Optional[service_account.Credentials]: The loaded credentials or None
        """
        return self._credentials
