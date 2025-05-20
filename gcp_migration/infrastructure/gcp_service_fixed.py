"""
Enhanced GCP Service Implementation for AI-Orchestra Migration.

This module provides a comprehensive implementation of the GCP service interfaces
with proper type annotations, error handling and efficiency optimizations.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, Union, cast

# GCP libraries with proper error handling for imports
try:
    # Import GCP libraries with explicit types
    from google.cloud import secretmanager as sm_lib
    from google.cloud import storage as storage_lib
    from google.cloud import firestore as firestore_lib
    from google.cloud import aiplatform as aiplatform_lib
    from google.auth import default
    from google.auth.credentials import Credentials
    from google.auth.exceptions import DefaultCredentialsError

    HAS_GCP_LIBS = True
except ImportError:
    HAS_GCP_LIBS = False

    # Define stub types for type checking when libraries aren't available
    class StubClient:
        """Stub client for when GCP libraries are not available."""

        pass

    class StubSecretManager:
        """Stub for Secret Manager."""

        class SecretManagerServiceClient(StubClient):
            """Stub for Secret Manager client."""

            def access_secret_version(self, name: str) -> Any:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

            def get_secret(self, name: str) -> Any:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

            def create_secret(
                self, parent: str, secret_id: str, secret: Dict[str, Any]
            ) -> Any:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

            def add_secret_version(self, parent: str, payload: Dict[str, Any]) -> Any:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

    class StubStorage:
        """Stub for Storage."""

        class Client(StubClient):
            """Stub for Storage client."""

            def bucket(self, name: str) -> Any:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

            def list_blobs(
                self, bucket_name: str, prefix: Optional[str] = None
            ) -> List[Any]:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

    class StubFirestore:
        """Stub for Firestore."""

        class Client(StubClient):
            """Stub for Firestore client."""

            def collection(self, name: str) -> Any:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

    class StubAIPlatform:
        """Stub for AI Platform."""

        def init(self, project: str, location: str) -> None:
            """Stub method."""
            raise NotImplementedError("GCP libraries not installed")

        class Model:
            """Stub for AI Platform Model."""

            @staticmethod
            def list() -> List[Any]:
                """Stub method."""
                raise NotImplementedError("GCP libraries not installed")

    # Set stub implementations for type checking
    sm_lib = StubSecretManager()
    storage_lib = StubStorage()
    firestore_lib = StubFirestore()
    aiplatform_lib = StubAIPlatform()

    # Define credential type for stubs
    class Credentials:
        """Stub for credentials."""

        pass


from gcp_migration.domain.exceptions import (
    AuthenticationError,
    ConfigurationError,
    FirestoreError,
    GCPError,
    ResourceNotFoundError,
    SecretError,
    StorageError,
    ValidationError,
    VertexAIError,
)
from gcp_migration.domain.interfaces_ext import (
    IExtendedGCPService,
)
from gcp_migration.utils.error_handling import (
    with_error_mapping,
    with_retry,
    map_authentication_error,
    map_secret_error,
    map_storage_error,
    map_firestore_error,
)

# Configure logging
logger = logging.getLogger(__name__)


class EnhancedGCPService(IExtendedGCPService):
    """
    Enhanced implementation of GCP service interfaces with proper type annotations
    and standardized error handling.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Enhanced GCP Service with project ID and authentication.

        Args:
            project_id: The GCP project ID. If None, will attempt to get from environment.

        Raises:
            AuthenticationError: If authentication with GCP fails
            ValueError: If project ID cannot be determined
        """
        self._project_id = project_id or os.environ.get("GCP_PROJECT_ID")

        if not self._project_id:
            try:
                # Try to get project ID from gcloud config
                result = subprocess.run(
                    ["gcloud", "config", "get-value", "project"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self._project_id = result.stdout.strip()
                logger.info(f"Using project ID from gcloud config: {self._project_id}")
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("Could not determine GCP project ID from gcloud config")

        if not self._project_id:
            logger.error("No GCP project ID provided or found in environment")
            raise ValueError("GCP project ID is required")

        # Check for GCP libraries
        if not HAS_GCP_LIBS:
            logger.error(
                "GCP libraries not installed. Run: pip install google-cloud-storage google-cloud-secretmanager google-cloud-firestore google-cloud-aiplatform google-auth"
            )
            raise ImportError("Required GCP libraries not installed")

        # Initialize clients
        self._credentials: Optional[Credentials] = None
        self._secret_client: Optional[sm_lib.SecretManagerServiceClient] = None
        self._storage_client: Optional[storage_lib.Client] = None
        self._firestore_client: Optional[firestore_lib.Client] = None
        self._aiplatform_client: Optional[aiplatform_lib] = None

        # Initialize the service
        self.initialize()

    @with_error_mapping(
        AuthenticationError,
        (DefaultCredentialsError, Exception),
        "Failed to authenticate with GCP",
    )
    def initialize(self) -> None:
        """
        Initialize the GCP service connections.

        Raises:
            AuthenticationError: If authentication with GCP fails
        """
        # Authenticate with GCP
        if self._credentials is None:
            self._credentials, project_id = default()

            # Use discovered project ID if not explicitly set and available
            if not self._project_id and project_id:
                self._project_id = project_id
                logger.info(f"Using project ID from credentials: {self._project_id}")

            logger.info(f"Authenticated with GCP project: {self._project_id}")

    @property
    def project_id(self) -> str:
        """Get the current GCP project ID."""
        if self._project_id is None:
            raise ValueError("Project ID is not set")
        return self._project_id

    @property
    def secret_client(self) -> sm_lib.SecretManagerServiceClient:
        """Get or create Secret Manager client."""
        if self._secret_client is None:
            if self._credentials is None:
                self.initialize()
            self._secret_client = sm_lib.SecretManagerServiceClient(
                credentials=self._credentials
            )
            logger.debug("Initialized Secret Manager client")
        return self._secret_client

    @property
    def storage_client(self) -> storage_lib.Client:
        """Get or create Storage client."""
        if self._storage_client is None:
            if self._credentials is None:
                self.initialize()
            self._storage_client = storage_lib.Client(
                credentials=self._credentials, project=self.project_id
            )
            logger.debug("Initialized Storage client")
        return self._storage_client

    @property
    def firestore_client(self) -> firestore_lib.Client:
        """Get or create Firestore client."""
        if self._firestore_client is None:
            if self._credentials is None:
                self.initialize()
            self._firestore_client = firestore_lib.Client(
                credentials=self._credentials, project=self.project_id
            )
            logger.debug("Initialized Firestore client")
        return self._firestore_client

    @property
    def aiplatform_client(self) -> aiplatform_lib:
        """Get or initialize AI Platform."""
        if self._aiplatform_client is None:
            aiplatform_lib.init(project=self.project_id, location="us-central1")
            self._aiplatform_client = aiplatform_lib
            logger.debug("Initialized AI Platform client")
        return self._aiplatform_client

    @with_error_mapping(
        GCPError,
        (subprocess.SubprocessError,),
        "Failed to check if GCP APIs are enabled",
    )
    @with_retry(max_attempts=3, retryable_errors=(subprocess.SubprocessError,))
    def check_gcp_apis_enabled(self) -> Dict[str, bool]:
        """
        Check if required GCP APIs are enabled.

        Returns:
            Dictionary of API names and their enabled status

        Raises:
            GCPError: If the check fails
        """
        apis = [
            "secretmanager.googleapis.com",
            "firestore.googleapis.com",
            "storage.googleapis.com",
            "aiplatform.googleapis.com",
        ]

        results = {}

        for api in apis:
            try:
                result = subprocess.run(
                    [
                        "gcloud",
                        "services",
                        "list",
                        "--enabled",
                        f"--filter={api}",
                        f"--project={self.project_id}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                results[api] = api in result.stdout
                logger.debug(f"API {api} enabled: {results[api]}")
            except subprocess.SubprocessError as e:
                logger.warning(f"Failed to check if {api} is enabled: {e}")
                results[api] = False

        return results

    @with_error_mapping(
        GCPError, (subprocess.SubprocessError,), "Failed to enable GCP APIs"
    )
    @with_retry(max_attempts=3, retryable_errors=(subprocess.SubprocessError,))
    def enable_gcp_apis(self, apis: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Enable required GCP APIs.

        Args:
            apis: List of APIs to enable (optional, uses default list if None)

        Returns:
            Dictionary of API names and their enabled status after enabling

        Raises:
            GCPError: If enabling APIs fails
        """
        if apis is None:
            apis = [
                "secretmanager.googleapis.com",
                "firestore.googleapis.com",
                "storage.googleapis.com",
                "aiplatform.googleapis.com",
            ]

        results = {}

        for api in apis:
            try:
                subprocess.run(
                    [
                        "gcloud",
                        "services",
                        "enable",
                        api,
                        f"--project={self.project_id}",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                results[api] = True
                logger.info(f"Enabled API: {api}")
            except subprocess.SubprocessError as e:
                results[api] = False
                logger.error(f"Failed to enable {api}: {e}")

        return results

    def verify_ai_integration(self) -> Dict[str, Any]:
        """
        Verify AI integration with GCP services.
        Checks if all necessary components are in place.

        Returns:
            Dictionary with verification results

        Raises:
            ConfigurationError: If verification fails
        """
        try:
            # Check if necessary folders and files exist
            home_dir = Path.home()
            ai_memory_dir = home_dir / ".ai-memory"
            gemini_config_dir = home_dir / ".config" / "Google" / "CloudCodeAI"
            claude_config_dir = home_dir / ".config" / "Anthropic"

            # Check API enablement
            api_status = self.check_gcp_apis_enabled()

            results = {
                "mcp_memory": {
                    "exists": ai_memory_dir.exists(),
                    "memory_index": (ai_memory_dir / "memory_index.json").exists()
                    if ai_memory_dir.exists()
                    else False,
                },
                "gemini": {
                    "config_exists": (
                        gemini_config_dir / "gemini-code-assist.yaml"
                    ).exists()
                    if gemini_config_dir.exists()
                    else False
                },
                "claude": {
                    "config_exists": (claude_config_dir / "config.json").exists()
                    if claude_config_dir.exists()
                    else False
                },
                "gcp_apis": api_status,
                "gcp_project": self.project_id,
            }

            return results
        except Exception as e:
            logger.error(f"Error verifying AI integration: {e}")
            raise ConfigurationError(
                message=f"Failed to verify AI integration: {str(e)}", cause=e
            )

    # Secret Manager implementation
    @with_error_mapping(SecretError, (Exception,), "Failed to access secret")
    @with_retry(max_attempts=3)
    def access_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Access a secret from Secret Manager.

        Args:
            secret_id: ID of the secret to access
            version_id: Version of the secret (default: latest)

        Returns:
            The secret value as a string

        Raises:
            ResourceNotFoundError: If the secret doesn't exist
            SecretError: If accessing the secret fails
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"

        try:
            response = self.secret_client.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            if "NotFound" in str(e):
                error_msg = f"Secret not found: {secret_id}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg, cause=e)
            else:
                error_msg = f"Error accessing secret {secret_id}: {str(e)}"
                logger.error(error_msg)
                raise SecretError(message=error_msg, cause=e)

    @with_error_mapping(SecretError, (Exception,), "Failed to store secret")
    @with_retry(max_attempts=3)
    def store_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Store a secret in Secret Manager.
        Creates the secret if it doesn't exist.

        Args:
            secret_id: ID for the secret
            secret_value: Value to store

        Returns:
            The name of the secret version created

        Raises:
            SecretError: If storing the secret fails
        """
        parent = f"projects/{self.project_id}"

        # Check if secret exists
        try:
            self.secret_client.get_secret(name=f"{parent}/secrets/{secret_id}")
            logger.debug(f"Secret {secret_id} already exists")
        except Exception:
            # Create secret if it doesn't exist
            try:
                self.secret_client.create_secret(
                    parent=parent,
                    secret_id=secret_id,
                    secret={"replication": {"automatic": {}}},
                )
                logger.info(f"Created new secret: {secret_id}")
            except Exception as e:
                error_msg = f"Failed to create secret {secret_id}: {str(e)}"
                logger.error(error_msg)
                raise SecretError(message=error_msg, cause=e)

        # Add secret version
        parent = f"{parent}/secrets/{secret_id}"
        payload = secret_value.encode("UTF-8")

        try:
            response = self.secret_client.add_secret_version(
                parent=parent, payload={"data": payload}
            )
            logger.info(f"Added secret version {response.name}")
            return response.name
        except Exception as e:
            error_msg = f"Error storing secret {secret_id}: {str(e)}"
            logger.error(error_msg)
            raise SecretError(message=error_msg, cause=e)

    @with_error_mapping(SecretError, (Exception,), "Failed to list secrets")
    def list_secrets(self, filter_prefix: Optional[str] = None) -> List[str]:
        """
        List secrets in the project.

        Args:
            filter_prefix: Optional prefix to filter secrets by

        Returns:
            List of secret IDs

        Raises:
            SecretError: If listing secrets fails
        """
        parent = f"projects/{self.project_id}"

        try:
            response = self.secret_client.list_secrets(parent=parent)

            secret_ids = []
            for secret in response:
                # Extract secret ID from name (format: projects/{project}/secrets/{secret})
                secret_id = secret.name.split("/")[-1]

                # Apply filter if provided
                if filter_prefix is None or secret_id.startswith(filter_prefix):
                    secret_ids.append(secret_id)

            return secret_ids
        except Exception as e:
            error_msg = f"Error listing secrets: {str(e)}"
            logger.error(error_msg)
            raise SecretError(message=error_msg, cause=e)

    @with_error_mapping(SecretError, (Exception,), "Failed to delete secret")
    def delete_secret(self, secret_id: str) -> bool:
        """
        Delete a secret from Secret Manager.

        Args:
            secret_id: ID of the secret to delete

        Returns:
            True if deletion was successful

        Raises:
            ResourceNotFoundError: If the secret doesn't exist
            SecretError: If deleting the secret fails
        """
        name = f"projects/{self.project_id}/secrets/{secret_id}"

        try:
            # Check if secret exists first
            try:
                self.secret_client.get_secret(name=name)
            except Exception as e:
                if "NotFound" in str(e):
                    error_msg = f"Secret not found: {secret_id}"
                    logger.error(error_msg)
                    raise ResourceNotFoundError(message=error_msg, cause=e)
                raise

            # Delete the secret
            self.secret_client.delete_secret(name=name)
            logger.info(f"Deleted secret: {secret_id}")
            return True
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error deleting secret {secret_id}: {str(e)}"
            logger.error(error_msg)
            raise SecretError(message=error_msg, cause=e)

    @with_error_mapping(SecretError, (Exception,), "Failed to migrate GitHub secrets")
    def migrate_github_secrets(self, github_secrets: Dict[str, str]) -> List[str]:
        """
        Migrate GitHub secrets to GCP Secret Manager.

        Args:
            github_secrets: Dictionary of GitHub secret names and values

        Returns:
            List of secret IDs that were migrated

        Raises:
            SecretError: If migrating secrets fails
        """
        migrated_secrets = []

        for secret_id, secret_value in github_secrets.items():
            try:
                self.store_secret(secret_id, secret_value)
                migrated_secrets.append(secret_id)
                logger.info(f"Migrated GitHub secret: {secret_id}")
            except Exception as e:
                logger.error(f"Failed to migrate GitHub secret {secret_id}: {e}")

        return migrated_secrets

    # Storage implementation
    @with_error_mapping(StorageError, (Exception,), "Failed to upload file")
    def upload_file(
        self,
        bucket_name: str,
        source_file_path: Path,
        destination_blob_name: Optional[str] = None,
    ) -> str:
        """
        Upload a file to a GCS bucket.

        Args:
            bucket_name: Name of the GCS bucket
            source_file_path: Path to the file to upload
            destination_blob_name: Name of the blob in GCS (defaults to filename)

        Returns:
            Public URL of the uploaded file

        Raises:
            ResourceNotFoundError: If the bucket doesn't exist or file not found
            StorageError: If uploading fails
        """
        # Validate source file exists
        if not source_file_path.exists():
            error_msg = f"Source file not found: {source_file_path}"
            logger.error(error_msg)
            raise ResourceNotFoundError(message=error_msg)

        # Default destination blob name to source filename if not provided
        if destination_blob_name is None:
            destination_blob_name = source_file_path.name

        try:
            # Get bucket
            bucket = self.storage_client.bucket(bucket_name)

            # Check if bucket exists
            if not bucket.exists():
                error_msg = f"Bucket not found: {bucket_name}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg)

            # Create blob and upload
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(str(source_file_path))

            # Generate public URL
            url = f"gs://{bucket_name}/{destination_blob_name}"
            logger.info(f"File uploaded to {url}")
            return url
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error uploading file to GCS: {str(e)}"
            logger.error(error_msg)
            raise StorageError(message=error_msg, cause=e)

    # Initialize Vertex AI
    @with_error_mapping(VertexAIError, (Exception,), "Failed to initialize Vertex AI")
    def initialize_vertex(self, location: str = "us-central1") -> None:
        """
        Initialize Vertex AI with project and location.

        Args:
            location: GCP region for Vertex AI resources

        Raises:
            VertexAIError: If initialization fails
        """
        try:
            aiplatform_lib.init(project=self.project_id, location=location)
            self._aiplatform_client = aiplatform_lib
            logger.info(f"Initialized Vertex AI in {location}")
        except Exception as e:
            error_msg = f"Error initializing Vertex AI: {str(e)}"
            logger.error(error_msg)
            raise VertexAIError(message=error_msg, cause=e)

    @with_error_mapping(VertexAIError, (Exception,), "Failed to get model list")
    def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Vertex AI models.

        Returns:
            List of model information dictionaries

        Raises:
            VertexAIError: If getting the model list fails
        """
        try:
            # Initialize if needed
            if self._aiplatform_client is None:
                self.initialize_vertex()

            # Get model list
            models = aiplatform_lib.Model.list()

            # Convert to dictionaries
            model_info = []
            for model in models:
                model_info.append(
                    {
                        "name": model.display_name
                        if hasattr(model, "display_name")
                        else "Unknown",
                        "id": model.name if hasattr(model, "name") else "Unknown",
                        "version": model.version_id
                        if hasattr(model, "version_id")
                        else None,
                        "create_time": model.create_time
                        if hasattr(model, "create_time")
                        else None,
                        "update_time": model.update_time
                        if hasattr(model, "update_time")
                        else None,
                    }
                )

            return model_info
        except Exception as e:
            error_msg = f"Error getting Vertex AI model list: {str(e)}"
            logger.error(error_msg)
            raise VertexAIError(message=error_msg, cause=e)
