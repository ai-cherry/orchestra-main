"""
Service factory for GCP service clients.

This module provides a factory for creating GCP service clients with consistent
configuration and error handling. It ensures clients are properly initialized
and configured for optimal performance.
"""

import logging
import os
from typing import Any, Dict, Optional, Type, TypeVar, cast

# Import Google Cloud libraries with proper error handling
try:
    from google.auth import default
    from google.auth.credentials import Credentials
    from google.auth.exceptions import DefaultCredentialsError
    from google.oauth2 import service_account

    # Service-specific clients with proper typing
    from google.cloud import secretmanager_v1
    from google.cloud import storage
    from google.cloud import firestore_v1
    from google.cloud import aiplatform_v1

    # For direct API access
    from google.api_core import exceptions as google_exceptions
    from google.api_core import retry as google_retry

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    # Create stub types for IDE/type checking when GCP libraries not available
    class Credentials:
        pass

    class DefaultCredentialsError(Exception):
        pass

    class service_account:
        @staticmethod
        def Credentials(*args, **kwargs):
            pass

    # Create stub modules
    class secretmanager_v1:
        class SecretManagerServiceClient:
            pass

    class storage:
        class Client:
            pass

    class firestore_v1:
        class Client:
            pass

    class aiplatform_v1:
        class ModelServiceClient:
            pass

        class PredictionServiceClient:
            pass

    # Stub exception types
    class google_exceptions:
        class NotFound(Exception):
            pass

        class AlreadyExists(Exception):
            pass

    GOOGLE_CLOUD_AVAILABLE = False

from gcp_migration.domain.exceptions_fixed import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    CredentialError,
    GCPError,
    map_to_migration_error,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for client types
T = TypeVar("T")


class GCPServiceFactory:
    """
    Factory for creating GCP service clients with consistent configuration.

    This class provides static methods for creating various GCP service clients
    with proper error handling, authentication, and configuration. It ensures
    clients are properly initialized for optimal performance.
    """

    @staticmethod
    def get_credentials(
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        scopes: Optional[list[str]] = None,
    ) -> Credentials:
        """
        Get Google Cloud credentials.

        This method provides a consistent way to obtain credentials for GCP
        services, handling various authentication methods gracefully.

        Args:
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            scopes: Authentication scopes to request

        Returns:
            Google Cloud credentials

        Raises:
            CredentialError: If credentials cannot be obtained
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            # Use provided credentials if available
            if credentials is not None:
                return credentials

            # Try to load from file if path is provided
            if credentials_path:
                if not os.path.exists(credentials_path):
                    raise CredentialError(
                        f"Credentials file not found: {credentials_path}"
                    )

                try:
                    return service_account.Credentials.from_service_account_file(
                        credentials_path, scopes=scopes
                    )
                except Exception as e:
                    raise CredentialError(
                        f"Failed to load credentials from file: {e}"
                    ) from e

            # Fall back to Application Default Credentials
            try:
                credentials, _ = default(scopes=scopes)
                return credentials
            except DefaultCredentialsError as e:
                raise CredentialError(
                    "Failed to obtain default credentials. Set GOOGLE_APPLICATION_CREDENTIALS "
                    "environment variable or provide credentials_path."
                ) from e

        except Exception as e:
            if isinstance(e, CredentialError):
                raise
            raise CredentialError(f"Error obtaining credentials: {e}") from e

    @staticmethod
    def create_secret_manager_client(
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> secretmanager_v1.SecretManagerServiceClient:
        """
        Create a Secret Manager client.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            client_options: Additional client options

        Returns:
            Secret Manager client

        Raises:
            GCPError: If client creation fails
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            # Get credentials
            creds = GCPServiceFactory.get_credentials(
                credentials_path=credentials_path, credentials=credentials
            )

            # Create client options with project ID if provided
            options = client_options or {}
            if project_id:
                options.setdefault("quota_project_id", project_id)

            # Create client
            client = secretmanager_v1.SecretManagerServiceClient(
                credentials=creds, client_options=options
            )

            return client

        except Exception as e:
            raise map_to_migration_error(
                e, GCPError, "Failed to create Secret Manager client"
            )

    @staticmethod
    def create_storage_client(
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> storage.Client:
        """
        Create a Cloud Storage client.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            client_options: Additional client options

        Returns:
            Storage client

        Raises:
            GCPError: If client creation fails
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            # Get credentials
            creds = GCPServiceFactory.get_credentials(
                credentials_path=credentials_path, credentials=credentials
            )

            # Create client
            client_kwargs = {"credentials": creds, "client_options": client_options}

            # Add project ID if provided
            if project_id:
                client_kwargs["project"] = project_id

            # Create client
            client = storage.Client(**client_kwargs)

            return client

        except Exception as e:
            raise map_to_migration_error(e, GCPError, "Failed to create Storage client")

    @staticmethod
    def create_firestore_client(
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> firestore_v1.Client:
        """
        Create a Firestore client.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            client_options: Additional client options

        Returns:
            Firestore client

        Raises:
            GCPError: If client creation fails
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            # Get credentials
            creds = GCPServiceFactory.get_credentials(
                credentials_path=credentials_path, credentials=credentials
            )

            # Create client
            client_kwargs = {"credentials": creds, "client_options": client_options}

            # Add project ID if provided
            if project_id:
                client_kwargs["project"] = project_id

            # Create client
            client = firestore_v1.Client(**client_kwargs)

            return client

        except Exception as e:
            raise map_to_migration_error(
                e, GCPError, "Failed to create Firestore client"
            )

    @staticmethod
    def create_model_client(
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> aiplatform_v1.ModelServiceClient:
        """
        Create a Vertex AI Model client.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            client_options: Additional client options

        Returns:
            Vertex AI Model client

        Raises:
            GCPError: If client creation fails
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            # Get credentials
            creds = GCPServiceFactory.get_credentials(
                credentials_path=credentials_path, credentials=credentials
            )

            # Create client options with project ID if provided
            options = client_options or {}
            if project_id:
                options.setdefault("quota_project_id", project_id)

            # Create client
            client = aiplatform_v1.ModelServiceClient(
                credentials=creds, client_options=options
            )

            return client

        except Exception as e:
            raise map_to_migration_error(
                e, GCPError, "Failed to create Vertex AI Model client"
            )

    @staticmethod
    def create_prediction_client(
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> aiplatform_v1.PredictionServiceClient:
        """
        Create a Vertex AI Prediction client.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            client_options: Additional client options

        Returns:
            Vertex AI Prediction client

        Raises:
            GCPError: If client creation fails
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            # Get credentials
            creds = GCPServiceFactory.get_credentials(
                credentials_path=credentials_path, credentials=credentials
            )

            # Create client options with project ID if provided
            options = client_options or {}
            if project_id:
                options.setdefault("quota_project_id", project_id)

            # Create client
            client = aiplatform_v1.PredictionServiceClient(
                credentials=creds, client_options=options
            )

            return client

        except Exception as e:
            raise map_to_migration_error(
                e, GCPError, "Failed to create Vertex AI Prediction client"
            )

    @staticmethod
    def create_client(
        client_type: Type[T],
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        client_options: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Create a GCP client of the specified type.

        This is a generic method that creates a client based on the client type.
        It dispatches to the appropriate specialized method.

        Args:
            client_type: Type of client to create
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            client_options: Additional client options

        Returns:
            Initialized client of the requested type

        Raises:
            ConfigurationError: If the client type is not supported
            GCPError: If client creation fails
        """
        try:
            if not GOOGLE_CLOUD_AVAILABLE:
                raise ImportError("Google Cloud libraries are not available")

            if client_type == secretmanager_v1.SecretManagerServiceClient:
                return cast(
                    T,
                    GCPServiceFactory.create_secret_manager_client(
                        project_id=project_id,
                        credentials_path=credentials_path,
                        credentials=credentials,
                        client_options=client_options,
                    ),
                )

            elif client_type == storage.Client:
                return cast(
                    T,
                    GCPServiceFactory.create_storage_client(
                        project_id=project_id,
                        credentials_path=credentials_path,
                        credentials=credentials,
                        client_options=client_options,
                    ),
                )

            elif client_type == firestore_v1.Client:
                return cast(
                    T,
                    GCPServiceFactory.create_firestore_client(
                        project_id=project_id,
                        credentials_path=credentials_path,
                        credentials=credentials,
                        client_options=client_options,
                    ),
                )

            elif client_type == aiplatform_v1.ModelServiceClient:
                return cast(
                    T,
                    GCPServiceFactory.create_model_client(
                        project_id=project_id,
                        credentials_path=credentials_path,
                        credentials=credentials,
                        client_options=client_options,
                    ),
                )

            elif client_type == aiplatform_v1.PredictionServiceClient:
                return cast(
                    T,
                    GCPServiceFactory.create_prediction_client(
                        project_id=project_id,
                        credentials_path=credentials_path,
                        credentials=credentials,
                        client_options=client_options,
                    ),
                )

            else:
                raise ConfigurationError(f"Unsupported client type: {client_type}")

        except Exception as e:
            if isinstance(e, (ConfigurationError, GCPError)):
                raise
            raise GCPError(f"Failed to create client of type {client_type}: {e}") from e
