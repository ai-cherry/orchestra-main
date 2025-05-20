"""
Extended GCP Service Implementation for AI-Orchestra Migration.

This module provides a comprehensive implementation of the GCP service interfaces
defined in domain/interfaces_ext.py, supporting Secret Manager, Firestore, 
Storage, and Vertex AI integration.
"""

# Standard library imports
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# GCP libraries with fallbacks for environments without GCP dependencies
try:
    # Google Cloud services
    from google.cloud import secretmanager
    from google.cloud import storage
    from google.cloud import firestore
    from google.cloud import aiplatform

    # Google auth
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError

    HAS_GCP_LIBS = True
except ImportError:
    HAS_GCP_LIBS = False
    # Define stub types for type checking when GCP libraries aren't available

    class StubSecretManager:
        class SecretManagerServiceClient:
            pass

    class StubStorage:
        class Client:
            pass

    class StubFirestore:
        class Client:
            pass

    secretmanager = StubSecretManager()
    storage = StubStorage()
    firestore = StubFirestore()
    aiplatform = object()

from gcp_migration.domain.exceptions import (
    AuthenticationError,
    ConfigurationError,
    FirestoreError,
    ResourceNotFoundError,
    SecretError,
    StorageError,
    VertexAIError,
)
from gcp_migration.domain.interfaces_ext import (
    IExtendedGCPService,
    IGCPServiceCore,
    IGCPSecretManager,
    IGCPStorage,
    IGCPFirestore,
    IGCPVertexAI,
    IGeminiConfigService,
)

# Configure logging
logger = logging.getLogger(__name__)


class ExtendedGCPService(IExtendedGCPService):
    """
    Comprehensive implementation of GCP service interfaces providing access to
    Secret Manager, Firestore, Storage, Vertex AI, and Gemini Code Assist configuration.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Extended GCP Service with project ID and authentication.

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
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("Could not determine GCP project ID from gcloud config")

        if not self._project_id:
            logger.error("No GCP project ID provided or found in environment")
            raise ValueError("GCP project ID is required")

        # Check for GCP libraries
        if not HAS_GCP_LIBS:
            logger.error(
                "GCP libraries not installed. Run: pip install google-cloud-storage google-cloud-secretmanager google-cloud-firestore google-cloud-aiplatform"
            )
            raise ImportError("Required GCP libraries not installed")

        # Initialize clients
        self._credentials = None
        self._secret_client = None
        self._storage_client = None
        self._firestore_client = None
        self._aiplatform_client = None

        # Initialize on creation
        self.initialize()

    def initialize(self) -> None:
        """
        Initialize the GCP service connections.

        Raises:
            AuthenticationError: If authentication with GCP fails
        """
        # Authenticate with GCP
        try:
            self._credentials, _ = default()
            logger.info(f"Authenticated with GCP project: {self._project_id}")
        except DefaultCredentialsError as e:
            error_msg = (
                f"Failed to authenticate with GCP using default credentials: {str(e)}"
            )
            logger.error(error_msg)
            raise AuthenticationError(message=error_msg, cause=e)

    @property
    def project_id(self) -> str:
        """Get the current GCP project ID."""
        if self._project_id is None:
            raise ValueError("Project ID is not set")
        return self._project_id

    @property
    def secret_client(self) -> secretmanager.SecretManagerServiceClient:
        """Get or create Secret Manager client."""
        if self._secret_client is None:
            self._secret_client = secretmanager.SecretManagerServiceClient(
                credentials=self._credentials
            )
        return self._secret_client

    @property
    def storage_client(self) -> storage.Client:
        """Get or create Storage client."""
        if self._storage_client is None:
            self._storage_client = storage.Client(
                credentials=self._credentials, project=self._project_id
            )
        return self._storage_client

    @property
    def firestore_client(self) -> firestore.Client:
        """Get or create Firestore client."""
        if self._firestore_client is None:
            self._firestore_client = firestore.Client(
                credentials=self._credentials, project=self._project_id
            )
        return self._firestore_client

    def check_gcp_apis_enabled(self) -> Dict[str, bool]:
        """
        Check if required GCP APIs are enabled.

        Returns:
            Dictionary of API names and their enabled status
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
                    ["gcloud", "services", "list", "--enabled", f"--filter={api}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                results[api] = api in result.stdout
            except subprocess.SubprocessError:
                results[api] = False
                logger.warning(f"Failed to check if {api} is enabled")

        return results

    def enable_gcp_apis(self, apis: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Enable required GCP APIs.

        Args:
            apis: List of APIs to enable (optional, uses default list if None)

        Returns:
            Dictionary of API names and their enabled status after enabling
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
                        f"--project={self._project_id}",
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
        """
        # Check if necessary folders and files exist
        home_dir = Path.home()
        ai_memory_dir = home_dir / ".ai-memory"
        gemini_config_dir = home_dir / ".config" / "Google" / "CloudCodeAI"
        claude_config_dir = home_dir / ".config" / "Anthropic"

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
            "gcp_apis": self.check_gcp_apis_enabled(),
            "gcp_project": self._project_id,
        }

        return results

    # Secret Manager implementation
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
        name = f"projects/{self._project_id}/secrets/{secret_id}/versions/{version_id}"

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
        parent = f"projects/{self._project_id}"

        # Check if secret exists
        try:
            self.secret_client.get_secret(name=f"{parent}/secrets/{secret_id}")
            logger.debug(f"Secret {secret_id} already exists, adding new version")
        except Exception as e:
            # Create secret if it doesn't exist
            if "NotFound" in str(e):
                logger.info(f"Secret {secret_id} does not exist, creating new secret")
                try:
                    self.secret_client.create_secret(
                        parent=parent,
                        secret_id=secret_id,
                        secret={"replication": {"automatic": {}}},
                    )
                    logger.info(f"Created new secret: {secret_id}")
                except Exception as create_err:
                    # Check for specific permission errors
                    if "Permission" in str(create_err):
                        error_msg = f"Permission denied when creating secret {secret_id}. Verify IAM permissions include secretmanager.secrets.create"
                    else:
                        error_msg = (
                            f"Failed to create secret {secret_id}: {str(create_err)}"
                        )

                    logger.error(error_msg, exc_info=True)
                    raise SecretError(message=error_msg, cause=create_err)
            else:
                # Handle non-NotFound errors during secret check
                error_msg = f"Error checking if secret {secret_id} exists: {str(e)}"
                logger.error(error_msg, exc_info=True)
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
            # Provide more specific error messages based on the error type
            if "Permission" in str(e):
                error_msg = f"Permission denied when adding version to secret {secret_id}. Verify IAM permissions include secretmanager.versions.add"
            elif "Resource exhausted" in str(e):
                error_msg = f"Resource limits exceeded when adding version to secret {secret_id}. Check Secret Manager quotas."
            elif "Invalid argument" in str(e):
                error_msg = f"Invalid secret data format for {secret_id}. Ensure the secret value is properly formatted."
            else:
                error_msg = f"Error storing secret {secret_id}: {str(e)}"

            logger.error(error_msg, exc_info=True)
            raise SecretError(message=error_msg, cause=e)

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
        parent = f"projects/{self._project_id}"

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
        name = f"projects/{self._project_id}/secrets/{secret_id}"

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

    def download_file(
        self, bucket_name: str, source_blob_name: str, destination_file_path: Path
    ) -> Path:
        """
        Download a file from a GCS bucket.

        Args:
            bucket_name: Name of the GCS bucket
            source_blob_name: Name of the blob in GCS
            destination_file_path: Path where the file should be saved

        Returns:
            Path to the downloaded file

        Raises:
            ResourceNotFoundError: If the bucket or blob doesn't exist
            StorageError: If downloading fails
        """
        try:
            # Create parent directories if they don't exist
            destination_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Get bucket
            bucket = self.storage_client.bucket(bucket_name)

            # Check if bucket exists
            if not bucket.exists():
                error_msg = f"Bucket not found: {bucket_name}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg)

            # Get blob
            blob = bucket.blob(source_blob_name)

            # Check if blob exists
            if not blob.exists():
                error_msg = f"Blob not found: {source_blob_name}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg)

            # Download file
            blob.download_to_filename(str(destination_file_path))
            logger.info(f"Downloaded {source_blob_name} to {destination_file_path}")
            return destination_file_path
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error downloading file from GCS: {str(e)}"
            logger.error(error_msg)
            raise StorageError(message=error_msg, cause=e)

    def list_files(self, bucket_name: str, prefix: Optional[str] = None) -> List[str]:
        """
        List files in a GCS bucket.

        Args:
            bucket_name: Name of the GCS bucket
            prefix: Optional prefix to filter files by

        Returns:
            List of blob names

        Raises:
            ResourceNotFoundError: If the bucket doesn't exist
            StorageError: If listing fails
        """
        try:
            # Get bucket
            bucket = self.storage_client.bucket(bucket_name)

            # Check if bucket exists
            if not bucket.exists():
                error_msg = f"Bucket not found: {bucket_name}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg)

            # List blobs with prefix
            blobs = self.storage_client.list_blobs(bucket_name, prefix=prefix)

            # Extract blob names
            blob_names = [blob.name for blob in blobs]
            return blob_names
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error listing files in GCS bucket: {str(e)}"
            logger.error(error_msg)
            raise StorageError(message=error_msg, cause=e)

    def ensure_bucket_exists(
        self, bucket_name: str, region: Optional[str] = None
    ) -> bool:
        """
        Ensure a GCS bucket exists, creating it if necessary.

        Args:
            bucket_name: Name of the GCS bucket
            region: Optional region for the bucket

        Returns:
            True if the bucket exists or was created

        Raises:
            StorageError: If ensuring bucket existence fails
        """
        try:
            # Check if bucket already exists
            bucket = self.storage_client.bucket(bucket_name)
            if bucket.exists():
                logger.info(f"Bucket already exists: {bucket_name}")
                return True

            # Create bucket
            bucket = self.storage_client.create_bucket(
                bucket_name, location=region or "us-central1"
            )
            logger.info(f"Created bucket: {bucket_name}")
            return True
        except Exception as e:
            error_msg = f"Error ensuring bucket exists: {str(e)}"
            logger.error(error_msg)
            raise StorageError(message=error_msg, cause=e)

    # Firestore implementation
    def store_document(
        self, collection: str, document_id: str, data: Dict[str, Any]
    ) -> str:
        """
        Store a document in Firestore.

        Args:
            collection: Firestore collection name
            document_id: Document ID (optional, will be generated if None)
            data: Document data

        Returns:
            Document ID of the stored document

        Raises:
            FirestoreError: If storing the document fails
        """
        try:
            # Get collection reference
            coll_ref = self.firestore_client.collection(collection)

            # Create or update document
            if document_id:
                doc_ref = coll_ref.document(document_id)
                doc_ref.set(data)
            else:
                doc_ref = coll_ref.add(data)[1]  # add() returns (None, doc_ref)
                document_id = doc_ref.id

            logger.info(f"Stored document in {collection}/{document_id}")
            return document_id
        except Exception as e:
            error_msg = f"Error storing document in Firestore: {str(e)}"
            logger.error(error_msg)
            raise FirestoreError(message=error_msg, cause=e)

    def get_document(self, collection: str, document_id: str) -> Dict[str, Any]:
        """
        Get a document from Firestore.

        Args:
            collection: Firestore collection name
            document_id: Document ID

        Returns:
            Document data

        Raises:
            ResourceNotFoundError: If the document doesn't exist
            FirestoreError: If getting the document fails
        """
        try:
            # Get document reference
            doc_ref = self.firestore_client.collection(collection).document(document_id)

            # Get document
            doc = doc_ref.get()

            # Check if document exists
            if not doc.exists:
                error_msg = f"Document not found: {collection}/{document_id}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg)

            # Return document data
            return doc.to_dict()
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error getting document from Firestore: {str(e)}"
            logger.error(error_msg)
            raise FirestoreError(message=error_msg, cause=e)

    def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """
        Update a document in Firestore.

        Args:
            collection: Firestore collection name
            document_id: Document ID
            data: Document data to update
            merge: Whether to merge with existing data (default: True)

        Returns:
            True if update was successful

        Raises:
            ResourceNotFoundError: If the document doesn't exist
            FirestoreError: If updating the document fails
        """
        try:
            # Get document reference
            doc_ref = self.firestore_client.collection(collection).document(document_id)

            # Check if document exists
            if not doc_ref.get().exists:
                error_msg = f"Document not found: {collection}/{document_id}"
                logger.error(error_msg)
                raise ResourceNotFoundError(message=error_msg)

            # Update document
            doc_ref.set(data, merge=merge)
            logger.info(f"Updated document {collection}/{document_id}")
            return True
        except ResourceNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error updating document in Firestore: {str(e)}"
            logger.error(error_msg)
            raise FirestoreError(message=error_msg, cause=e)

    # Vertex AI implementation
    def initialize_vertex(self, location: str = "us-central1") -> None:
        """
        Initialize Vertex AI with project and location.

        Args:
            location: GCP region for Vertex AI resources

        Raises:
            VertexAIError: If initialization fails
        """
        try:
            aiplatform.init(project=self._project_id, location=location)
            self._aiplatform_client = aiplatform
            logger.info(f"Initialized Vertex AI in {location}")
        except Exception as e:
            error_msg = f"Error initializing Vertex AI: {str(e)}"
            logger.error(error_msg)
            raise VertexAIError(message=error_msg, cause=e)

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

            # Get model list using aiplatform.Model.list()
            models = aiplatform.Model.list()

            # Convert to dictionaries
            model_info = []
            for model in models:
                model_info.append(
                    {
                        "name": model.display_name,
                        "id": model.name,
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

    # Gemini Code Assist configuration
    def setup_gemini_config(self, config_path: Optional[str] = None) -> str:
        """
        Set up Gemini Code Assist configuration.

        Args:
            config_path: Path to write the configuration file (optional)

        Returns:
            Path to the configuration file

        Raises:
            ConfigurationError: If setup fails
        """
        try:
            if not config_path:
                home_dir = Path.home()
                config_dir = home_dir / ".config" / "Google" / "CloudCodeAI"
                config_dir.mkdir(parents=True, exist_ok=True)
                config_path = str(config_dir / "gemini-code-assist.yaml")

            # Get template configuration
            template_path = (
                Path(__file__).parent.parent
                / "docker"
                / "workstation-image"
                / "gemini-code-assist.yaml"
            )

            if template_path.exists():
                with open(template_path, "r") as f:
                    config_content = f.read()

                # Replace variables
                project_id = self._project_id or "unknown-project"
                config_content = config_content.replace("${GCP_PROJECT_ID}", project_id)

                # Write to target path
                with open(config_path, "w") as f:
                    f.write(config_content)

                logger.info(f"Set up Gemini Code Assist configuration at {config_path}")
                return config_path
            else:
                error_msg = f"Template configuration not found at {template_path}"
                logger.error(error_msg)
                raise ConfigurationError(message=error_msg)
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            error_msg = f"Error setting up Gemini Code Assist configuration: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)

    def setup_mcp_memory(self, memory_path: Optional[str] = None) -> str:
        """
        Set up MCP memory system for AI assistants.

        Args:
            memory_path: Path for MCP memory (optional)

        Returns:
            Path to the MCP memory directory

        Raises:
            ConfigurationError: If setup fails
        """
        try:
            if not memory_path:
                home_dir = Path.home()
                memory_path = str(home_dir / ".ai-memory")

            memory_dir = Path(memory_path)
            memory_dir.mkdir(parents=True, exist_ok=True)

            # Create memory index
            memory_index = {
                "version": "1.0",
                "environment": "gcp-workstation",
                "memory_format": "vector",
                "memory_location": "firestore",
                "project_id": self._project_id,
                "storage_options": {
                    "persistent": True,
                    "encrypted": True,
                    "geo_redundant": True,
                },
                "assistants": [
                    {
                        "name": "gemini",
                        "type": "code-assist",
                        "provider": "google",
                        "enabled": True,
                    },
                    {
                        "name": "roo",
                        "type": "chat",
                        "provider": "anthropic",
                        "enabled": True,
                    },
                    {
                        "name": "cline",
                        "type": "chat",
                        "provider": "anthropic",
                        "enabled": True,
                    },
                ],
            }

            # Write memory index
            with open(memory_dir / "memory_index.json", "w") as f:
                json.dump(memory_index, f, indent=2)

            logger.info(f"Set up MCP memory system at {memory_path}")
            return memory_path
        except Exception as e:
            error_msg = f"Error setting up MCP memory: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)

    def verify_installation(self) -> Dict[str, bool]:
        """
        Verify that Gemini Code Assist is installed and configured.

        Returns:
            Dictionary with verification results

        Raises:
            ConfigurationError: If verification fails
        """
        try:
            home_dir = Path.home()
            gemini_config_dir = home_dir / ".config" / "Google" / "CloudCodeAI"
            gemini_config_file = gemini_config_dir / "gemini-code-assist.yaml"

            # Also check VS Code extension
            vscode_dir = home_dir / ".vscode" / "extensions"
            gemini_extension_installed = False

            if vscode_dir.exists():
                # Look for Google.cloud-code extension
                for ext_dir in vscode_dir.glob("Google.cloud-code-*"):
                    if ext_dir.is_dir():
                        gemini_extension_installed = True
                        break

            # Check Vertex AI API
            vertex_api_enabled = False
            apis = self.check_gcp_apis_enabled()
            if "aiplatform.googleapis.com" in apis:
                vertex_api_enabled = apis["aiplatform.googleapis.com"]

            # Return results
            return {
                "config_exists": gemini_config_file.exists(),
                "extension_installed": gemini_extension_installed,
                "vertex_api_enabled": vertex_api_enabled,
                "project_configured": self._project_id is not None,
            }
        except Exception as e:
            error_msg = f"Error verifying Gemini installation: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(message=error_msg, cause=e)
