"""
Service adapters for GCP services.

This module provides adapter classes that wrap GCP service clients, providing:
1. A stable interface for service operations
2. Consistent error handling and mapping
3. Performance optimization through caching and connection pooling
4. Circuit breaker integration for resilience
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

# Import specific error handling and utility modules
from gcp_migration.domain.exceptions_fixed import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    BatchProcessingError,
    ConfigurationError,
    ConnectionError,
    CredentialError,
    FirestoreError,
    GCPError,
    ResourceAlreadyExistsError,
    ResourceExhaustedError,
    ResourceNotFoundError,
    SecretError,
    StorageError,
    TimeoutError,
    VertexAIError,
    map_to_migration_error,
)
from gcp_migration.domain.models import Secret, StorageItem
from gcp_migration.domain.protocols import (
    IGCPServiceCore,
    IGCPSecretManager,
    IGCPStorage,
    IGCPFirestore,
    IGCPVertexAI,
)
from gcp_migration.infrastructure.connection import ConnectionPool
from gcp_migration.infrastructure.resilience import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    with_circuit_breaker,
)
from gcp_migration.infrastructure.service_factory import GCPServiceFactory

# Import GCP libraries with proper error handling
try:
    from google.auth.credentials import Credentials

    # GCP service-specific imports
    from google.cloud import secretmanager_v1
    from google.cloud import storage
    from google.cloud import firestore_v1
    from google.cloud import aiplatform_v1

    # For direct API access and batching
    from google.api_core import exceptions as google_exceptions
    from google.protobuf import timestamp_pb2

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    # Create stub types for IDE/type checking when GCP libraries not available
    class Credentials:
        pass

    # Create stub modules
    class secretmanager_v1:
        class SecretManagerServiceClient:
            pass

    class storage:
        class Client:
            pass

        class Blob:
            pass

        class Bucket:
            pass

    class firestore_v1:
        class Client:
            pass

        class DocumentReference:
            pass

        class CollectionReference:
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

    class timestamp_pb2:
        class Timestamp:
            pass

    GOOGLE_CLOUD_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class SecretManagerAdapter(IGCPSecretManager):
    """
    Adapter for Secret Manager operations with consistent error handling.

    This class wraps a Secret Manager client and provides a stable interface
    for secret management operations with consistent error handling and resilience.
    """

    def __init__(
        self,
        client: secretmanager_v1.SecretManagerServiceClient,
        project_id: str,
        connection_pool: Optional[ConnectionPool] = None,
    ):
        """
        Initialize the Secret Manager adapter.

        Args:
            client: Secret Manager client
            project_id: GCP project ID
            connection_pool: Optional connection pool for client management
        """
        self._client = client
        self._project_id = project_id
        self._connection_pool = connection_pool

    @with_circuit_breaker("secret_access")
    async def access_secret(self, secret_id: str, version_id: str = "latest") -> str:
        """
        Access a secret from Secret Manager.

        Args:
            secret_id: ID of the secret
            version_id: Version to access (default: latest)

        Returns:
            The secret value

        Raises:
            ResourceNotFoundError: If secret not found
            SecretError: If access fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._access_secret_impl(client, secret_id, version_id)
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._access_secret_impl(
                    self._client, secret_id, version_id
                )

        except google_exceptions.NotFound as e:
            raise map_to_migration_error(
                e, ResourceNotFoundError, f"Secret {secret_id} not found"
            )
        except Exception as e:
            raise map_to_migration_error(
                e, SecretError, f"Failed to access secret {secret_id}"
            )

    async def _access_secret_impl(
        self,
        client: secretmanager_v1.SecretManagerServiceClient,
        secret_id: str,
        version_id: str,
    ) -> str:
        """
        Implementation for accessing a secret.

        Args:
            client: Secret Manager client
            secret_id: ID of the secret
            version_id: Version to access

        Returns:
            The secret value
        """
        # Construct the resource name
        if version_id == "latest":
            name = f"projects/{self._project_id}/secrets/{secret_id}/versions/latest"
        else:
            name = (
                f"projects/{self._project_id}/secrets/{secret_id}/versions/{version_id}"
            )

        # Access the secret
        # Use asyncio.to_thread to make blocking API call non-blocking
        response = await asyncio.to_thread(
            client.access_secret_version, request={"name": name}
        )

        return response.payload.data.decode("UTF-8")

    @with_circuit_breaker("secret_store")
    async def store_secret(self, secret_id: str, secret_value: str) -> str:
        """
        Store a secret in Secret Manager.

        Args:
            secret_id: ID for the secret
            secret_value: Value to store

        Returns:
            The version name of the stored secret

        Raises:
            ResourceAlreadyExistsError: If the secret already exists
            SecretError: If storage fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._store_secret_impl(
                        client, secret_id, secret_value
                    )
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._store_secret_impl(
                    self._client, secret_id, secret_value
                )

        except google_exceptions.AlreadyExists as e:
            raise map_to_migration_error(
                e, ResourceAlreadyExistsError, f"Secret {secret_id} already exists"
            )
        except Exception as e:
            raise map_to_migration_error(
                e, SecretError, f"Failed to store secret {secret_id}"
            )

    async def _store_secret_impl(
        self,
        client: secretmanager_v1.SecretManagerServiceClient,
        secret_id: str,
        secret_value: str,
    ) -> str:
        """
        Implementation for storing a secret.

        Args:
            client: Secret Manager client
            secret_id: ID for the secret
            secret_value: Value to store

        Returns:
            The version name of the stored secret
        """
        # Construct the parent resource name
        parent = f"projects/{self._project_id}"

        # Check if secret already exists
        secret_path = f"{parent}/secrets/{secret_id}"
        try:
            await asyncio.to_thread(client.get_secret, request={"name": secret_path})
            secret_exists = True
        except google_exceptions.NotFound:
            secret_exists = False

        # Create secret if it doesn't exist
        if not secret_exists:
            await asyncio.to_thread(
                client.create_secret,
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                },
            )

        # Add secret version
        version = await asyncio.to_thread(
            client.add_secret_version,
            request={
                "parent": secret_path,
                "payload": {"data": secret_value.encode("UTF-8")},
            },
        )

        return version.name

    @with_circuit_breaker("secret_list")
    async def list_secrets(self, filter_prefix: Optional[str] = None) -> List[str]:
        """
        List secrets in the project.

        Args:
            filter_prefix: Optional prefix to filter by

        Returns:
            List of secret IDs

        Raises:
            SecretError: If listing fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._list_secrets_impl(client, filter_prefix)
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._list_secrets_impl(self._client, filter_prefix)

        except Exception as e:
            raise map_to_migration_error(e, SecretError, "Failed to list secrets")

    async def _list_secrets_impl(
        self,
        client: secretmanager_v1.SecretManagerServiceClient,
        filter_prefix: Optional[str],
    ) -> List[str]:
        """
        Implementation for listing secrets.

        Args:
            client: Secret Manager client
            filter_prefix: Optional prefix to filter by

        Returns:
            List of secret IDs
        """
        # Construct the parent resource name
        parent = f"projects/{self._project_id}"

        # List secrets
        response = await asyncio.to_thread(
            client.list_secrets, request={"parent": parent}
        )

        # Extract secret IDs and filter if needed
        secret_ids = []
        for secret in response:
            # Extract ID from name (format: projects/{project}/secrets/{secret})
            name_parts = secret.name.split("/")
            if len(name_parts) >= 4:
                secret_id = name_parts[3]

                # Apply filter if provided
                if filter_prefix is None or secret_id.startswith(filter_prefix):
                    secret_ids.append(secret_id)

        return secret_ids

    @with_circuit_breaker("secret_delete")
    async def delete_secret(self, secret_id: str) -> bool:
        """
        Delete a secret.

        Args:
            secret_id: ID of the secret to delete

        Returns:
            True if deleted successfully

        Raises:
            SecretError: If deletion fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._delete_secret_impl(client, secret_id)
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._delete_secret_impl(self._client, secret_id)

        except google_exceptions.NotFound:
            # Secret doesn't exist, consider it deleted
            return True
        except Exception as e:
            raise map_to_migration_error(
                e, SecretError, f"Failed to delete secret {secret_id}"
            )

    async def _delete_secret_impl(
        self, client: secretmanager_v1.SecretManagerServiceClient, secret_id: str
    ) -> bool:
        """
        Implementation for deleting a secret.

        Args:
            client: Secret Manager client
            secret_id: ID of the secret to delete

        Returns:
            True if deleted successfully
        """
        # Construct the resource name
        name = f"projects/{self._project_id}/secrets/{secret_id}"

        # Delete the secret
        await asyncio.to_thread(client.delete_secret, request={"name": name})

        return True


class StorageAdapter(IGCPStorage):
    """
    Adapter for Cloud Storage operations with consistent error handling.

    This class wraps a Storage client and provides a stable interface
    for storage operations with consistent error handling and resilience.
    """

    def __init__(
        self,
        client: storage.Client,
        project_id: str,
        connection_pool: Optional[ConnectionPool] = None,
    ):
        """
        Initialize the Storage adapter.

        Args:
            client: Storage client
            project_id: GCP project ID
            connection_pool: Optional connection pool for client management
        """
        self._client = client
        self._project_id = project_id
        self._connection_pool = connection_pool

    @with_circuit_breaker("storage_upload")
    async def upload_file(
        self,
        bucket_name: str,
        source_file_path: str,
        destination_blob_name: Optional[str] = None,
    ) -> str:
        """
        Upload a file to a GCS bucket.

        Args:
            bucket_name: Name of the GCS bucket
            source_file_path: Path to the file to upload
            destination_blob_name: Name for the blob (default: source filename)

        Returns:
            Public URL of the uploaded file


        Raises:
            ResourceNotFoundError: If bucket or file not found
            StorageError: If upload fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._upload_file_impl(
                        client, bucket_name, source_file_path, destination_blob_name
                    )
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._upload_file_impl(
                    self._client, bucket_name, source_file_path, destination_blob_name
                )

        except google_exceptions.NotFound as e:
            raise map_to_migration_error(
                e, ResourceNotFoundError, f"Bucket {bucket_name} not found"
            )
        except FileNotFoundError as e:
            raise map_to_migration_error(
                e, ResourceNotFoundError, f"Source file not found: {source_file_path}"
            )
        except Exception as e:
            raise map_to_migration_error(
                e,
                StorageError,
                f"Failed to upload file to {bucket_name}/{destination_blob_name or os.path.basename(source_file_path)}",
            )

    async def _upload_file_impl(
        self,
        client: storage.Client,
        bucket_name: str,
        source_file_path: str,
        destination_blob_name: Optional[str],
    ) -> str:
        """
        Implementation for uploading a file.

        Args:
            client: Storage client
            bucket_name: Name of the GCS bucket
            source_file_path: Path to the file to upload
            destination_blob_name: Name for the blob

        Returns:
            Public URL of the uploaded file
        """
        # Use source filename if destination not provided
        if destination_blob_name is None:
            destination_blob_name = os.path.basename(source_file_path)

        # Check if source file exists
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Source file not found: {source_file_path}")

        # Get bucket
        bucket = client.bucket(bucket_name)

        # Create blob
        blob = bucket.blob(destination_blob_name)

        # Upload file (this operation can be slow for large files)
        await asyncio.to_thread(blob.upload_from_filename, source_file_path)

        # Return public URL
        return f"gs://{bucket_name}/{destination_blob_name}"

    @with_circuit_breaker("storage_download")
    async def download_file(
        self, bucket_name: str, source_blob_name: str, destination_file_path: str
    ) -> str:
        """
        Download a file from a GCS bucket.

        Args:
            bucket_name: Name of the GCS bucket
            source_blob_name: Name of the blob to download
            destination_file_path: Path to save the file

        Returns:
            Path to the downloaded file

        Raises:
            ResourceNotFoundError: If bucket or blob not found
            StorageError: If download fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._download_file_impl(
                        client, bucket_name, source_blob_name, destination_file_path
                    )
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._download_file_impl(
                    self._client, bucket_name, source_blob_name, destination_file_path
                )

        except google_exceptions.NotFound as e:
            raise map_to_migration_error(
                e,
                ResourceNotFoundError,
                f"Blob {source_blob_name} not found in bucket {bucket_name}",
            )
        except Exception as e:
            raise map_to_migration_error(
                e,
                StorageError,
                f"Failed to download blob {source_blob_name} from bucket {bucket_name}",
            )

    async def _download_file_impl(
        self,
        client: storage.Client,
        bucket_name: str,
        source_blob_name: str,
        destination_file_path: str,
    ) -> str:
        """
        Implementation for downloading a file.

        Args:
            client: Storage client
            bucket_name: Name of the GCS bucket
            source_blob_name: Name of the blob to download
            destination_file_path: Path to save the file

        Returns:
            Path to the downloaded file
        """
        # Ensure destination directory exists
        os.makedirs(
            os.path.dirname(os.path.abspath(destination_file_path)), exist_ok=True
        )

        # Get bucket
        bucket = client.bucket(bucket_name)

        # Get blob
        blob = bucket.blob(source_blob_name)

        # Download file (this operation can be slow for large files)
        await asyncio.to_thread(blob.download_to_filename, destination_file_path)

        return destination_file_path

    @with_circuit_breaker("storage_list")
    async def list_blobs(
        self, bucket_name: str, prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List blobs in a GCS bucket.

        Args:
            bucket_name: Name of the GCS bucket
            prefix: Optional prefix to filter by

        Returns:
            List of blob metadata

        Raises:
            ResourceNotFoundError: If bucket not found
            StorageError: If listing fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._list_blobs_impl(client, bucket_name, prefix)
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._list_blobs_impl(self._client, bucket_name, prefix)

        except google_exceptions.NotFound as e:
            raise map_to_migration_error(
                e, ResourceNotFoundError, f"Bucket {bucket_name} not found"
            )
        except Exception as e:
            raise map_to_migration_error(
                e, StorageError, f"Failed to list blobs in bucket {bucket_name}"
            )

    async def _list_blobs_impl(
        self, client: storage.Client, bucket_name: str, prefix: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Implementation for listing blobs.

        Args:
            client: Storage client
            bucket_name: Name of the GCS bucket
            prefix: Optional prefix to filter by

        Returns:
            List of blob metadata
        """
        # Get bucket
        bucket = client.bucket(bucket_name)

        # List blobs
        blobs = await asyncio.to_thread(lambda: list(bucket.list_blobs(prefix=prefix)))

        # Extract metadata
        result = []
        for blob in blobs:
            result.append(
                {
                    "name": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type,
                    "md5_hash": blob.md5_hash,
                    "public_url": blob.public_url,
                }
            )

        return result


class FirestoreAdapter(IGCPFirestore):
    """
    Adapter for Firestore operations with consistent error handling.

    This class wraps a Firestore client and provides a stable interface
    for database operations with consistent error handling and resilience.
    """

    def __init__(
        self,
        client: firestore_v1.Client,
        project_id: str,
        connection_pool: Optional[ConnectionPool] = None,
    ):
        """
        Initialize the Firestore adapter.

        Args:
            client: Firestore client
            project_id: GCP project ID
            connection_pool: Optional connection pool for client management
        """
        self._client = client
        self._project_id = project_id
        self._connection_pool = connection_pool

    @with_circuit_breaker("firestore_store")
    async def store_document(
        self, collection_id: str, document_id: Optional[str], data: Dict[str, Any]
    ) -> str:
        """
        Store a document in Firestore.

        Args:
            collection_id: ID of the collection
            document_id: Optional document ID (auto-generated if None)
            data: Document data

        Returns:
            The document ID

        Raises:
            FirestoreError: If storage fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._store_document_impl(
                        client, collection_id, document_id, data
                    )
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._store_document_impl(
                    self._client, collection_id, document_id, data
                )

        except Exception as e:
            raise map_to_migration_error(e, FirestoreError, "Failed to store document")

    async def _store_document_impl(
        self,
        client: firestore_v1.Client,
        collection_id: str,
        document_id: Optional[str],
        data: Dict[str, Any],
    ) -> str:
        """
        Implementation for storing a document.

        Args:
            client: Firestore client
            collection_id: ID of the collection
            document_id: Optional document ID
            data: Document data

        Returns:
            The document ID
        """
        # Get collection reference
        collection_ref = client.collection(collection_id)

        # Store document
        if document_id:
            doc_ref = collection_ref.document(document_id)
            await asyncio.to_thread(doc_ref.set, data)
            return document_id
        else:
            doc_ref = await asyncio.to_thread(lambda: collection_ref.add(data)[1])
            return doc_ref.id

    @with_circuit_breaker("firestore_get")
    async def get_document(
        self, collection_id: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document from Firestore.

        Args:
            collection_id: ID of the collection
            document_id: ID of the document

        Returns:
            The document data or None if not found

        Raises:
            FirestoreError: If retrieval fails
        """
        try:
            # Use the connection pool if available
            if self._connection_pool:
                client = await self._connection_pool.acquire()
                try:
                    return await self._get_document_impl(
                        client, collection_id, document_id
                    )
                finally:
                    await self._connection_pool.release(client)
            else:
                # Use the instance client directly
                return await self._get_document_impl(
                    self._client, collection_id, document_id
                )

        except Exception as e:
            raise map_to_migration_error(
                e, FirestoreError, f"Failed to get document {document_id}"
            )

    async def _get_document_impl(
        self, client: firestore_v1.Client, collection_id: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Implementation for getting a document.

        Args:
            client: Firestore client
            collection_id: ID of the collection
            document_id: ID of the document

        Returns:
            The document data or None if not found
        """
        # Get document reference
        doc_ref = client.collection(collection_id).document(document_id)

        # Get document
        doc = await asyncio.to_thread(doc_ref.get)

        # Return data if exists
        if doc.exists:
            return doc.to_dict()
        else:
            return None


class VertexAIAdapter(IGCPVertexAI):
    """
    Adapter for Vertex AI operations with consistent error handling.

    This class wraps Vertex AI clients and provides a stable interface
    for AI operations with consistent error handling and resilience.
    """

    def __init__(
        self,
        model_client: aiplatform_v1.ModelServiceClient,
        prediction_client: aiplatform_v1.PredictionServiceClient,
        project_id: str,
        location: str = "us-central1",
        connection_pool: Optional[ConnectionPool] = None,
    ):
        """
        Initialize the Vertex AI adapter.

        Args:
            model_client: Vertex AI Model client
            prediction_client: Vertex AI Prediction client
            project_id: GCP project ID
            location: GCP region for Vertex AI
            connection_pool: Optional connection pool for client management
        """
        self._model_client = model_client
        self._prediction_client = prediction_client
        self._project_id = project_id
        self._location = location
        self._connection_pool = connection_pool

    @with_circuit_breaker("vertex_models")
    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Vertex AI models.

        Returns:
            List of model information

        Raises:
            VertexAIError: If listing fails
        """
        try:
            # Use the model client
            client = self._model_client

            # Get location
            location = self._location

            # List models
            parent = f"projects/{self._project_id}/locations/{location}"
            models = await asyncio.to_thread(lambda: client.list_models(parent=parent))

            # Convert to list of dictionaries
            result = []
            for model in models:
                result.append(
                    {
                        "name": model.name,
                        "display_name": model.display_name,
                        "version_id": model.version_id,
                        "create_time": model.create_time.ToDatetime().isoformat()
                        if model.create_time
                        else None,
                        "update_time": model.update_time.ToDatetime().isoformat()
                        if model.update_time
                        else None,
                    }
                )

            return result

        except Exception as e:
            raise map_to_migration_error(e, VertexAIError, "Failed to get model list")

    @with_circuit_breaker("vertex_predict")
    async def predict_text(
        self, model_name: str, prompt: str, parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a prediction from a text model.

        Args:
            model_name: Name of the model to use
            prompt: Input prompt
            parameters: Optional model parameters

        Returns:
            The model's prediction

        Raises:
            VertexAIError: If prediction fails
        """
        try:
            # Use the prediction client
            client = self._prediction_client

            # Get location
            location = self._location

            # Prepare request
            instance = {"content": prompt}

            # Add parameters
            params = parameters or {}
            default_params = {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
                "topK": 40,
                "topP": 0.95,
            }

            # Merge with defaults
            for key, value in default_params.items():
                if key not in params:
                    params[key] = value

            # Make prediction
            endpoint = f"projects/{self._project_id}/locations/{location}/publishers/google/models/{model_name}"
            response = await asyncio.to_thread(
                lambda: client.predict(
                    endpoint=endpoint, instances=[instance], parameters=params
                )
            )

            # Extract prediction
            if response.predictions and len(response.predictions) > 0:
                prediction = response.predictions[0]
                if isinstance(prediction, dict) and "content" in prediction:
                    return prediction["content"]
                return str(prediction)

            return ""

        except Exception as e:
            raise map_to_migration_error(
                e, VertexAIError, "Failed to generate prediction"
            )


class AdapterFactory:
    """
    Factory for creating service adapters.

    This class provides methods for creating various service adapters
    with consistent configuration and initialization.
    """

    @staticmethod
    async def create_secret_manager_adapter(
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        connection_pool: Optional[ConnectionPool] = None,
    ) -> SecretManagerAdapter:
        """
        Create a Secret Manager adapter.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            connection_pool: Optional connection pool for client management

        Returns:
            SecretManagerAdapter
        """
        # Create client
        client = GCPServiceFactory.create_secret_manager_client(
            project_id=project_id,
            credentials_path=credentials_path,
            credentials=credentials,
        )

        # Create adapter
        return SecretManagerAdapter(
            client=client, project_id=project_id, connection_pool=connection_pool
        )

    @staticmethod
    async def create_storage_adapter(
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        connection_pool: Optional[ConnectionPool] = None,
    ) -> StorageAdapter:
        """
        Create a Storage adapter.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            connection_pool: Optional connection pool for client management

        Returns:
            StorageAdapter
        """
        # Create client
        client = GCPServiceFactory.create_storage_client(
            project_id=project_id,
            credentials_path=credentials_path,
            credentials=credentials,
        )

        # Create adapter
        return StorageAdapter(
            client=client, project_id=project_id, connection_pool=connection_pool
        )

    @staticmethod
    async def create_firestore_adapter(
        project_id: str,
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        connection_pool: Optional[ConnectionPool] = None,
    ) -> FirestoreAdapter:
        """
        Create a Firestore adapter.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            connection_pool: Optional connection pool for client management

        Returns:
            FirestoreAdapter
        """
        # Create client
        client = GCPServiceFactory.create_firestore_client(
            project_id=project_id,
            credentials_path=credentials_path,
            credentials=credentials,
        )

        # Create adapter
        return FirestoreAdapter(
            client=client, project_id=project_id, connection_pool=connection_pool
        )

    @staticmethod
    async def create_vertex_ai_adapter(
        project_id: str,
        location: str = "us-central1",
        credentials_path: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        connection_pool: Optional[ConnectionPool] = None,
    ) -> VertexAIAdapter:
        """
        Create a Vertex AI adapter.

        Args:
            project_id: GCP project ID
            location: GCP region for Vertex AI
            credentials_path: Path to service account credentials file
            credentials: Explicit credentials object
            connection_pool: Optional connection pool for client management

        Returns:
            VertexAIAdapter
        """
        # Create clients
        model_client = GCPServiceFactory.create_model_client(
            project_id=project_id,
            credentials_path=credentials_path,
            credentials=credentials,
        )

        prediction_client = GCPServiceFactory.create_prediction_client(
            project_id=project_id,
            credentials_path=credentials_path,
            credentials=credentials,
        )

        # Create adapter
        return VertexAIAdapter(
            model_client=model_client,
            prediction_client=prediction_client,
            project_id=project_id,
            location=location,
            connection_pool=connection_pool,
        )
