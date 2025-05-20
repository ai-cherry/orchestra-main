#!/usr/bin/env python3
"""
Credential Manager for AI Orchestra

This module provides a secure way to manage credentials for the AI Orchestra project.
It supports:
- Loading credentials from environment variables
- Loading credentials from files
- Securely storing credentials in memory
- Providing credentials to other components

Usage:
    from core.security.credential_manager import CredentialManager
    
    # Initialize the credential manager
    credential_manager = CredentialManager()
    
    # Get credentials
    service_account_key = credential_manager.get_service_account_key()
"""

import base64
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CredentialSource(Enum):
    """Enum representing the source of credentials."""

    ENV_VAR = "environment_variable"
    FILE = "file"
    SECRET_MANAGER = "secret_manager"
    WORKLOAD_IDENTITY = "workload_identity"


@dataclass
class ServiceAccountInfo:
    """Class for storing service account information."""

    project_id: str
    client_email: str
    private_key_id: str
    private_key: str
    client_id: str

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "ServiceAccountInfo":
        """Create a ServiceAccountInfo instance from a JSON dictionary."""
        return cls(
            project_id=json_data.get("project_id", ""),
            client_email=json_data.get("client_email", ""),
            private_key_id=json_data.get("private_key_id", ""),
            private_key=json_data.get("private_key", ""),
            client_id=json_data.get("client_id", ""),
        )

    def to_json(self) -> Dict[str, Any]:
        """Convert the ServiceAccountInfo to a JSON dictionary."""
        return {
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.client_email.replace('@', '%40')}",
        }

    def to_temp_file(self) -> str:
        """Write the service account info to a temporary file and return the path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(self.to_json(), temp_file, indent=2)
            temp_file_path = temp_file.name

        # Set appropriate permissions
        os.chmod(temp_file_path, 0o600)

        return temp_file_path


class CredentialManager:
    """
    Manages credentials for the AI Orchestra project.

    This class provides methods to securely handle credentials, including:
    - Service account keys
    - API keys
    - Other sensitive information

    It supports loading credentials from various sources and providing them
    to other components in a secure manner.
    """

    def __init__(self, env_prefix: str = "ORCHESTRA"):
        """
        Initialize the credential manager.

        Args:
            env_prefix: Prefix for environment variables
        """
        self.env_prefix = env_prefix
        self._service_account_info: Optional[ServiceAccountInfo] = None
        self._temp_files: list[str] = []

        # Try to load credentials from environment variables
        self._load_credentials_from_env()

    def _load_credentials_from_env(self) -> None:
        """Load credentials from environment variables."""
        # Check for service account key in environment variables
        service_account_json = os.environ.get(f"{self.env_prefix}_SERVICE_ACCOUNT_JSON")
        if service_account_json:
            try:
                # Try to parse as JSON
                service_account_data = json.loads(service_account_json)
                self._service_account_info = ServiceAccountInfo.from_json(
                    service_account_data
                )
                logger.info("Loaded service account info from environment variable")
            except json.JSONDecodeError:
                # Try to decode as base64
                try:
                    decoded = base64.b64decode(service_account_json).decode("utf-8")
                    service_account_data = json.loads(decoded)
                    self._service_account_info = ServiceAccountInfo.from_json(
                        service_account_data
                    )
                    logger.info(
                        "Loaded base64-encoded service account info from environment variable"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to decode service account info from environment variable: {e}"
                    )

        # Check for service account key file path
        service_account_path = os.environ.get(f"{self.env_prefix}_SERVICE_ACCOUNT_PATH")
        if service_account_path and not self._service_account_info:
            self.load_service_account_from_file(service_account_path)

    def load_service_account_from_file(self, file_path: Union[str, Path]) -> bool:
        """
        Load service account information from a file.

        Args:
            file_path: Path to the service account key file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(file_path, "r") as f:
                service_account_data = json.load(f)

            self._service_account_info = ServiceAccountInfo.from_json(
                service_account_data
            )
            logger.info(f"Loaded service account info from file: {file_path}")
            return True
        except Exception as e:
            logger.warning(
                f"Failed to load service account info from file {file_path}: {e}"
            )
            return False

    def get_service_account_key(self) -> Optional[ServiceAccountInfo]:
        """
        Get the service account key information.

        Returns:
            ServiceAccountInfo or None if not available
        """
        return self._service_account_info

    def get_service_account_key_path(self) -> Optional[str]:
        """
        Get a path to a file containing the service account key.

        This creates a temporary file with the service account key and returns the path.
        The file will be deleted when the credential manager is cleaned up.

        Returns:
            str: Path to the service account key file, or None if not available
        """
        if not self._service_account_info:
            return None

        temp_file_path = self._service_account_info.to_temp_file()
        self._temp_files.append(temp_file_path)
        return temp_file_path

    def get_project_id(self) -> Optional[str]:
        """
        Get the GCP project ID.

        Returns:
            str: Project ID or None if not available
        """
        if self._service_account_info:
            return self._service_account_info.project_id

        # Try to get from environment variable
        return os.environ.get(f"{self.env_prefix}_PROJECT_ID") or os.environ.get(
            "GCP_PROJECT_ID"
        )

    def secure_service_account_key(self, file_path: Union[str, Path]) -> bool:
        """
        Secure a service account key by loading it and then removing the file.

        Args:
            file_path: Path to the service account key file

        Returns:
            bool: True if successful, False otherwise
        """
        success = self.load_service_account_from_file(file_path)
        if success:
            try:
                os.remove(file_path)
                logger.info(f"Removed service account key file: {file_path}")
                return True
            except Exception as e:
                logger.warning(
                    f"Failed to remove service account key file {file_path}: {e}"
                )
                return False
        return False

    def cleanup(self) -> None:
        """Clean up temporary files."""
        for temp_file in self._temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

        self._temp_files = []

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.cleanup()


def secure_credentials() -> None:
    """
    Secure credentials by loading them into memory and removing the files.

    This function is intended to be run as a script to secure credentials
    in the repository.
    """
    credential_manager = CredentialManager()

    # List of potential service account key files
    service_account_files = [
        "service-account-key.json",
        ".credentials/service-account-key.json",
    ]

    for file_path in service_account_files:
        if os.path.exists(file_path):
            logger.info(f"Securing service account key file: {file_path}")
            credential_manager.secure_service_account_key(file_path)

    # Store the project ID in an environment variable
    project_id = credential_manager.get_project_id()
    if project_id:
        logger.info(f"Setting environment variable ORCHESTRA_PROJECT_ID={project_id}")
        os.environ["ORCHESTRA_PROJECT_ID"] = project_id

    logger.info("Credentials secured successfully")


if __name__ == "__main__":
    secure_credentials()
