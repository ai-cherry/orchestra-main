"""
GCP service clients for the migration toolkit.

This module provides client implementations for GCP services with
connection pooling, resilience patterns, and standardized error handling.
"""

import asyncio
import base64
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from google.api_core import exceptions as gcp_exceptions
from google.api_core.retry import Retry
from google.auth import exceptions as auth_exceptions
from google.auth.credentials import Credentials
from google.cloud import secretmanager_v1, storage, firestore
from google.cloud.secretmanager_v1 import SecretManagerServiceClient
from google.cloud.storage import Blob, Bucket, Client as StorageClient
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account

from ..domain.exceptions_fixed import (
    AuthenticationError, AuthorizationError, ConnectionError, GCPError,
    ResourceNotFoundError, SecretError, StorageError, map_gcp_error, ErrorContext
)
from ..domain.models import Secret, StorageItem
from .connection import ConnectionPool, create_connection_pool
from .resilience import with_circuit_breaker, with_retry, CircuitBreakerConfig, RetryConfig

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')


class BaseGCPService:
    """
    Base class for GCP service clients.
    
    This class provides common functionality for GCP service clients,
    including authentication, connection management, and error handling.
    """
    
    def __init__(
        self,
        service_name: str,
        project_id: str,
        credentials_path: Optional[str] = None,
        use_application_default: bool = True,
        location: str = "us-central1",
        pool_config: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize the GCP service client.
        
        Args:
            service_name: Name of the GCP service
            project_id: GCP project ID
            credentials_path: Path to service account key file (optional)
            use_application_default: Whether to use application default credentials
            location: GCP location/region
            pool_config: Connection pool configuration
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
        """
        self.service_name = service_name
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.use_application_default = use_application_default
        self.location = location
        
        # Connection pool
        self.pool_config = pool_config or {
            "min_size": 1,
            "max_size": 10,
            "max_idle_time": 60.0,
            "max_lifetime": 3600.0,
            "connection_timeout": 30.0
        }
        
        # Retry and circuit breaker configs
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        
        # Connection pool
        self._pool: Optional[ConnectionPool] = None
        
        # Thread pool for blocking operations
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    async def initialize(self) -> None:
        """
        Initialize the service client.
        
        This method creates the connection pool and initializes any
        resources needed by the service client.
        """
        if self._pool is not None:
            return
        
        # Create the connection pool
        self._pool = await create_connection_pool(
            name=f"{self.service_name}-pool",
            factory=self._create_client,
            closer=self._close_client,
            min_size=self.pool_config["min_size"],
            max_size=self.pool_config["max_size"],
            max_idle_time=self.pool_config["max_idle_time"],
            max_lifetime=self.pool_config["max_lifetime"],
            connection_timeout=self.pool_config["connection_timeout"]
        )
        
        logger.info(f"Initialized {self.service_name} client for project {self.project_id}")
    
    async def _create_client(self) -> Any:
        """
        Create a new client for the GCP service.
        
        This method should be implemented by subclasses to create
        a specific GCP service client.
        
        Returns:
            A new client instance
        """
        raise NotImplementedError("Subclasses must implement _create_client")
    
    async def _close_client(self, client: Any) -> None:
        """
        Close a GCP service client.
        
        This method should be implemented by subclasses to properly
        close a specific GCP service client.
        
        Args:
            client: The client to close
        """
        # Most GCP clients don't need explicit cleanup
        pass
    
    async def _get_credentials(self) -> Credentials:
        """
        Get the credentials for GCP authentication.
        
        Returns:
            GCP credentials
            
        Raises:
            AuthenticationError: If credentials cannot be obtained
        """
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Use service account key file
                return service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
            elif self.use_application_default:
                # Use application default credentials
                # We need to run this in a thread since it might block
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    service_account.Credentials.get_application_default
                )
            else:
                raise AuthenticationError(
                    "No valid authentication method specified",
                    details={
                        "credentials_path": self.credentials_path,
                        "use_application_default": self.use_application_default
                    }
                )
        except auth_exceptions.GoogleAuthError as e:
            raise AuthenticationError(
                f"Failed to obtain GCP credentials: {e}",
                cause=e
            )
    
    async def _run_with_client(self, func: Callable[[Any], T]) -> T:
        """
        Run a function with a client from the pool.
        
        This method acquires a client from the pool, runs the function,
        and then releases the client back to the pool.
        
        Args:
            func: Function to run with the client
            
        Returns:
            Result of the function
        """
        if not self._pool:
            await self.initialize()
        
        client = await self._pool.acquire()
        try:
            return func(client)
        finally:
            await self._pool.release(client)
    
    async def close(self) -> None:
        """
        Close the service client and release all resources.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
        
        self._executor.shutdown(wait=True)
        logger.info(f"Closed {self.service_name} client for project {self.project_id}")


class SecretManagerService(BaseGCPService):
    """
    Client for Google Secret Manager.
    
    This class provides methods for managing secrets in Google Secret Manager,
    with connection pooling, resilience patterns, and standardized error handling.
    """
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        use_application_default: bool = True,
        location: str = "us-central1",
        pool_config: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize the Secret Manager service client.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file (optional)
            use_application_default: Whether to use application default credentials
            location: GCP location/region
            pool_config: Connection pool configuration
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
        """
        super().__init__(
            service_name="secretmanager",
            project_id=project_id,
            credentials_path=credentials_path,
            use_application_default=use_application_default,
            location=location,
            pool_config=pool_config,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config
        )
    
    async def _create_client(self) -> SecretManagerServiceClient:
        """
        Create a new Secret Manager client.
        
        Returns:
            A new Secret Manager client instance
        """
        credentials = await self._get_credentials()
        
        # Create the client in a thread since it might block
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(SecretManagerServiceClient, credentials=credentials)
        )
    
    @with_retry()
    @with_circuit_breaker("secretmanager-access")
    async def get_secret(self, secret_id: str, version: str = "latest") -> Secret:
        """
        Get a secret from Secret Manager.
        
        Args:
            secret_id: ID of the secret
            version: Version of the secret (default: latest)
            
        Returns:
            Secret object with value and metadata
            
        Raises:
            SecretError: If the secret cannot be accessed
        """
        # Format the name for the secret version
        if version == "latest":
            version_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        else:
            version_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        
        # Access the secret with error handling
        with ErrorContext(
            operation_name=f"get_secret({secret_id}, {version})",
            target_type=SecretError,
            service_name="secretmanager"
        ):
            # Get the secret version
            async def get_secret_version(client):
                # Run in a thread since it's blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    client.access_secret_version,
                    version_name
                )
            
            response = await self._run_with_client(get_secret_version)
            
            # Extract the secret value
            secret_value = response.payload.data.decode('utf-8')
            
            # Create the Secret object
            return Secret(
                id=secret_id,
                name=secret_id,
                value=secret_value,
                version=version,
                create_time=response.create_time,
                source=f"gcpproject/{self.project_id}"
            )
    
    @with_retry()
    @with_circuit_breaker("secretmanager-list")
    async def list_secrets(self) -> List[Secret]:
        """
        List all secrets in the project.
        
        Returns:
            List of Secret objects (without values)
            
        Raises:
            SecretError: If secrets cannot be listed
        """
        # Format the parent name
        parent = f"projects/{self.project_id}"
        
        # List secrets with error handling
        with ErrorContext(
            operation_name="list_secrets",
            target_type=SecretError,
            service_name="secretmanager"
        ):
            # List secrets
            async def list_project_secrets(client):
                # Run in a thread since it's blocking
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    client.list_secrets,
                    parent
                )
            
            response = await self._run_with_client(list_project_secrets)
            
            # Create Secret objects
            secrets = []
            for secret in response:
                secret_id = secret.name.split('/')[-1]
                secrets.append(Secret(
                    id=secret_id,
                    name=secret_id,
                    create_time=secret.create_time,
                    source=f"gcpproject/{self.project_id}"
                ))
            
            return secrets
    
    @with_retry()
    @with_circuit_breaker("secretmanager-create")
    async def create_secret(self, secret_id: str, secret_value: str, labels: Optional[Dict[str, str]] = None) -> Secret:
        """
        Create a new secret in Secret Manager.
        
        Args:
            secret_id: ID for the new secret
            secret_value: Value for the secret
            labels: Labels to apply to the secret
            
        Returns:
            The created Secret object
            
        Raises:
            SecretError: If the secret cannot be created
        """
        # Format the parent name
        parent = f"projects/{self.project_id}"
        
        # Create the secret with error handling
        with ErrorContext(
            operation_name=f"create_secret({secret_id})",
            target_type=SecretError,
            service_name="secretmanager"
        ):
            # Create the secret
            async def create_new_secret(client):
                # Create secret
                loop = asyncio.get_event_loop()
                secret = await loop.run_in_executor(
                    self._executor,
                    partial(
                        client.create_secret,
                        parent=parent,
                        secret_id=secret_id,
                        secret={'replication': {'automatic': {}}, 'labels': labels or {}}
                    )
                )
                
                # Add the secret version
                version = await loop.run_in_executor(
                    self._executor,
                    partial(
                        client.add_secret_version,
                        parent=secret.name,
                        payload={'data': secret_value.encode('utf-8')}
                    )
                )
                
                return secret, version
            
            secret, version = await self._run_with_client(create_new_secret)
            
            # Create the Secret object
            return Secret(
                id=secret_id,
                name=secret_id,
                value=secret_value,
                version="1",
                create_time=secret.create_time,
                labels=labels or {},
                source=f"gcpproject/{self.project_id}"
            )
    
    @with_retry()
    @with_circuit_breaker("secretmanager-update")
    async def update_secret(self, secret_id: str, secret_value: str) -> Secret:
        """
        Update a secret in Secret Manager.
        
        Args:
            secret_id: ID of the secret to update
            secret_value: New value for the secret
            
        Returns:
            The updated Secret object
            
        Raises:
            SecretError: If the secret cannot be updated
        """
        # Format the parent name
        parent = f"projects/{self.project_id}/secrets/{secret_id}"
        
        # Update the secret with error handling
        with ErrorContext(
            operation_name=f"update_secret({secret_id})",
            target_type=SecretError,
            service_name="secretmanager"
        ):
            # Add a new version
            async def add_secret_version(client):
                loop = asyncio.get_event_loop()
                version = await loop.run_in_executor(
                    self._executor,
                    partial(
                        client.add_secret_version,
                        parent=parent,
                        payload={'data': secret_value.encode('utf-8')}
                    )
                )
                return version
            
            version = await self._run_with_client(add_secret_version)
            
            # Get the version number
            version_num = version.name.split('/')[-1]
            
            # Create the Secret object
            return Secret(
                id=secret_id,
                name=secret_id,
                value=secret_value,
                version=version_num,
                create_time=version.create_time,
                source=f"gcpproject/{self.project_id}"
            )


class StorageService(BaseGCPService):
    """
    Client for Google Cloud Storage.
    
    This class provides methods for managing buckets and objects in Google Cloud Storage,
    with connection pooling, resilience patterns, and standardized error handling.
    """
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        use_application_default: bool = True,
        location: str = "us-central1",
        pool_config: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize the Storage service client.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file (optional)
            use_application_default: Whether to use application default credentials
            location: GCP location/region
            pool_config: Connection pool configuration
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
        """
        super().__init__(
            service_name="storage",
            project_id=project_id,
            credentials_path=credentials_path,
            use_application_default=use_application_default,
            location=location,
            pool_config=pool_config,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config
        )
    
    async def _create_client(self) -> StorageClient:
        """
        Create a new Storage client.
        
        Returns:
            A new Storage client instance
        """
        credentials = await self._get_credentials()
        
        # Create the client in a thread since it might block
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(StorageClient, credentials=credentials, project=self.project_id)
        )
    
    @with_retry()
    @with_circuit_breaker("storage-list-buckets")
    async def list_buckets(self) -> List[Bucket]:
        """
        List all buckets in the project.
        
        Returns:
            List of Bucket objects
            
        Raises:
            StorageError: If buckets cannot be listed
        """
        with ErrorContext(
            operation_name="list_buckets",
            target_type=StorageError,
            service_name="storage"
        ):
            async def list_project_buckets(client):
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    self._executor,
                    client.list_buckets
                )
            
            buckets = await self._run_with_client(list_project_buckets)
            return list(buckets)
    
    @with_retry()
    @with_circuit_breaker("storage-list-blobs")
    async def list_blobs(self, bucket_name: str, prefix: Optional[str] = None) -> List[StorageItem]:
        """
        List all blobs in a bucket.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Filter results to objects whose names begin with this prefix
            
        Returns:
            List of StorageItem objects
            
        Raises:
            StorageError: If blobs cannot be listed
        """
        with ErrorContext(
            operation_name=f"list_blobs({bucket_name}, {prefix})",
            target_type=StorageError,
            service_name="storage"
        ):
            async def list_bucket_blobs(client):
                loop = asyncio.get_event_loop()
                bucket = client.bucket(bucket_name)
                blobs = await loop.run_in_executor(
                    self._executor,
                    partial(bucket.list_blobs, prefix=prefix)
                )
                return list(blobs)
            
            blobs = await self._run_with_client(list_bucket_blobs)
            
            # Convert to StorageItem objects
            return [
                StorageItem(
                    bucket=blob.bucket.name,
                    name=blob.name,
                    content_type=blob.content_type,
                    size=blob.size,
                    md5_hash=blob.md5_hash,
                    create_time=None,  # GCS doesn't provide creation time
                    update_time=blob.updated,
                    metadata=dict(blob.metadata or {})
                )
                for blob in blobs
            ]
    
    @with_retry()
    @with_circuit_breaker("storage-upload")
    async def upload_blob(
        self,
        bucket_name: str,
        source_file_path: str,
        destination_blob_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> StorageItem:
        """
        Upload a file to a bucket.
        
        Args:
            bucket_name: Name of the bucket
            source_file_path: Path to the source file
            destination_blob_name: Name for the blob
            content_type: Content type for the blob
            metadata: Custom metadata for the blob
            
        Returns:
            StorageItem for the uploaded blob
            
        Raises:
            StorageError: If the file cannot be uploaded
        """
        with ErrorContext(
            operation_name=f"upload_blob({bucket_name}, {destination_blob_name})",
            target_type=StorageError,
            service_name="storage"
        ):
            async def upload_file(client):
                loop = asyncio.get_event_loop()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(destination_blob_name)
                
                # Set metadata if provided
                if metadata:
                    blob.metadata = metadata
                
                # Upload the file
                await loop.run_in_executor(
                    self._executor,
                    partial(
                        blob.upload_from_filename,
                        source_file_path,
                        content_type=content_type
                    )
                )
                
                # Reload to get updated properties
                await loop.run_in_executor(
                    self._executor,
                    blob.reload
                )
                
                return blob
            
            blob = await self._run_with_client(upload_file)
            
            # Create the StorageItem
            return StorageItem(
                bucket=blob.bucket.name,
                name=blob.name,
                content_type=blob.content_type,
                size=blob.size,
                md5_hash=blob.md5_hash,
                update_time=blob.updated,
                metadata=dict(blob.metadata or {})
            )
    
    @with_retry()
    @with_circuit_breaker("storage-download")
    async def download_blob(
        self,
        bucket_name: str,
        source_blob_name: str,
        destination_file_path: str
    ) -> str:
        """
        Download a blob from a bucket.
        
        Args:
            bucket_name: Name of the bucket
            source_blob_name: Name of the blob
            destination_file_path: Path where the file should be saved
            
        Returns:
            Path to the downloaded file
            
        Raises:
            StorageError: If the blob cannot be downloaded
        """
        with ErrorContext(
            operation_name=f"download_blob({bucket_name}, {source_blob_name})",
            target_type=StorageError,
            service_name="storage"
        ):
            async def download_file(client):
                loop = asyncio.get_event_loop()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(source_blob_name)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
                
                # Download the blob
                await loop.run_in_executor(
                    self._executor,
                    partial(
                        blob.download_to_filename,
                        destination_file_path
                    )
                )
                
                return destination_file_path
            
            return await self._run_with_client(download_file)
    
    @with_retry()
    @with_circuit_breaker("storage-delete")
    async def delete_blob(self, bucket_name: str, blob_name: str) -> None:
        """
        Delete a blob from a bucket.
        
        Args:
            bucket_name: Name of the bucket
            blob_name: Name of the blob
            
        Raises:
            StorageError: If the blob cannot be deleted
        """
        with ErrorContext(
            operation_name=f"delete_blob({bucket_name}, {blob_name})",
            target_type=StorageError,
            service_name="storage"
        ):
            async def delete_file(client):
                loop = asyncio.get_event_loop()
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                # Delete the blob
                await loop.run_in_executor(
                    self._executor,
                    blob.delete
                )
            
            await self._run_with_client(delete_file)


class FirestoreService(BaseGCPService):
    """
    Client for Google Cloud Firestore.
    
    This class provides methods for interacting with Firestore,
    with connection pooling, resilience patterns, and standardized error handling.
    """
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        use_application_default: bool = True,
        location: str = "us-central1",
        pool_config: Optional[Dict[str, Any]] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize the Firestore service client.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file (optional)
            use_application_default: Whether to use application default credentials
            location: GCP location/region
            pool_config: Connection pool configuration
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
        """
        super().__init__(
            service_name="firestore",
            project_id=project_id,
            credentials_path=credentials_path,
            use_application_default=use_application_default,
            location=location,
            pool_config=pool_config,
            retry_config=retry_config,
            circuit_breaker_config=circuit_breaker_config
        )
    
    async def _create_client(self) -> firestore.Client:
        """
        Create a new Firestore client.
        
        Returns:
            A new Firestore client instance
        """
        credentials = await self._get_credentials()
        
        # Create the client in a thread since it might block
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            partial(firestore.Client, credentials=credentials, project=self.project_id)
        )
    
    @with_retry()
    @with_circuit_breaker("firestore-get")
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from Firestore.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            Document data or None if not found
            
        Raises:
            FirestoreError: If the document cannot be retrieved
        """
        with ErrorContext(
            operation_name=f"get_document({collection}, {document_id})",
            target_type=GCPError,
            service_name="firestore"
        ):
            async def get_doc(client):
                loop = asyncio.get_event_loop()
                doc_ref = client.collection(collection).document(document_id)
                doc = await loop.run_in_executor(
                    self._executor,
                    doc_ref.get
                )
                
                if doc.exists:
                    return doc.to_dict()
                else:
                    return None
            
            return await self._run_with_client(get_doc)
    
    @with_retry()
    @with_circuit_breaker("firestore-set")
    async def set_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = False
    ) -> None:
        """
        Set a document in Firestore.
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data
            merge: Whether to merge with existing data
            
        Raises:
            FirestoreError: If the document cannot be set
        """
        with ErrorContext(
            operation_name=f"set_document({collection}, {document_id})",
            target_type=GCPError,
            service_name="firestore"
        ):
            async def set_doc(client):
                loop = asyncio.get_event_loop()
                doc_ref = client.collection(collection).document(document_id)
                await loop.run_in_executor(
                    self._executor,
                    partial(
                        doc_ref.set,
                        data,
                        merge=merge
                    )
                )
            
            await self._run_with_client(set_doc)
    
    @with_retry()
    @with_circuit_breaker("firestore-query")
    async def query_documents(
        self,
        collection: str,
        filters: Optional[List[Tuple[str, str, Any]]] = None,
        order_by: Optional[List[Tuple[str, str]]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from Firestore.
        
        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            order_by: List of (field, direction) tuples
            limit: Maximum number of documents to return
            
        Returns:
            List of document data
            
        Raises:
            FirestoreError: If the query cannot be executed
        """
        with ErrorContext(
            operation_name=f"query_documents({collection})",
            target_type=GCPError,
            service_name="firestore"
        ):
            async def query_docs(client):
                loop = asyncio.get_event_loop()
                
                # Start with the collection reference
                query = client.collection(collection)
                
                # Add filters
                if filters:
                    for field, op, value in filters:
                        query = query.where(field, op, value)
                
                # Add ordering
                if order_by:
                    for field, direction in order_by:
                        if direction.lower() == 'desc':
                            query = query.order_by(field, direction=firestore.Query.DESCENDING)
                        else:
                            query = query.order_by(field)
                
                # Add limit
                if limit:
                    query = query.limit(limit)
                
                # Execute the query
                docs = await loop.run_in_executor(
                    self._executor,
                    query.stream
                )
                
                # Convert to list of dicts
                return [doc.to_dict() for doc in docs]
            
            return await self._run_with_client(query_docs)
    
    @with_retry()
    @with_circuit_breaker("firestore-delete")
    async def delete_document(self, collection: str, document_id: str) -> None:
        """
        Delete a document from Firestore.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Raises:
            FirestoreError: If the document cannot be deleted
        """
        with ErrorContext(
            operation_name=f"delete_document({collection}, {document_id})",
            target_type=GCPError,
            service_name="firestore"
        ):
            async def delete_doc(client):
                loop = asyncio.get_event_loop()
                doc_ref = client.collection(collection).document(document_id)
                await loop.run_in_executor(
                    self._executor,
                    doc_ref.delete
                )
            
            await self._run_with_client(delete_doc)
