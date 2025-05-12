"""
Interfaces (protocols) for GCP service components.

This module defines the protocols for GCP services, allowing for consistent 
interfaces and dependency injection. These protocols are implemented by concrete
adapter classes to provide stable interfaces for various GCP services.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, TypeVar, Union

from .models import Secret, StorageItem, MigrationContext


T = TypeVar('T')


class IGCPServiceCore(Protocol):
    """
    Core interface for GCP service operations.
    
    This protocol defines the basic methods that all GCP service implementations
    must provide.
    """
    
    @property
    def project_id(self) -> str:
        """Get the GCP project ID."""
        ...
    
    async def validate_credentials(self) -> bool:
        """
        Validate the configured credentials.
        
        Returns:
            True if credentials are valid
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the service.
        
        Returns:
            A dictionary with health status information
        """
        ...

    async def initialize(self) -> None:
        """
        Initialize the service.
        
        This method is called to perform any necessary initialization such as
        connection establishment, resource allocation, etc.
        """
        ...

    async def shutdown(self) -> None:
        """
        Shut down the service.
        
        This method is called to perform any necessary cleanup such as
        connection termination, resource release, etc.
        """
        ...


class IExtendedGCPService(IGCPServiceCore, Protocol):
    """
    Extended interface for GCP service operations.
    
    This protocol extends the core interface with additional methods for
    more complex service operations.
    """
    
    @property
    def secret_manager(self) -> "IGCPSecretManager":
        """Get the Secret Manager service."""
        ...
    
    @property
    def storage(self) -> "IGCPStorage":
        """Get the Cloud Storage service."""
        ...
    
    @property
    def firestore(self) -> "IGCPFirestore":
        """Get the Firestore service."""
        ...
    
    @property
    def vertex_ai(self) -> "IGCPVertexAI":
        """Get the Vertex AI service."""
        ...
    
    async def migrate_github_repository(
        self, 
        github_repo: str,
        destination_path: str,
        migration_context: Optional[MigrationContext] = None
    ) -> str:
        """
        Migrate a GitHub repository to a GCP environment.
        
        Args:
            github_repo: The GitHub repository URL or name
            destination_path: The destination path in GCP
            migration_context: Optional migration context
            
        Returns:
            The URL or path to the migrated repository in GCP
            
        Raises:
            MigrationError: If migration fails
        """
        ...


class IGCPSecretManager(Protocol):
    """
    Interface for Secret Manager operations.
    
    This protocol defines methods for interacting with Google Secret Manager.
    """
    
    async def access_secret(
        self, 
        secret_id: str, 
        version_id: str = "latest"
    ) -> str:
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
        ...
    
    async def store_secret(
        self, 
        secret_id: str, 
        secret_value: str
    ) -> str:
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
        ...
    
    async def list_secrets(
        self, 
        filter_prefix: Optional[str] = None
    ) -> List[str]:
        """
        List secrets in the project.
        
        Args:
            filter_prefix: Optional prefix to filter by
            
        Returns:
            List of secret IDs
            
        Raises:
            SecretError: If listing fails
        """
        ...
    
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
        ...
        
    async def migrate_github_secrets(
        self,
        github_secrets: Dict[str, str],
        prefix: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Migrate GitHub secrets to GCP Secret Manager.
        
        Args:
            github_secrets: Dictionary of GitHub secrets
            prefix: Optional prefix for secret names
            context: Optional context information
            
        Returns:
            Dictionary mapping from GitHub secret name to GCP secret name
            
        Raises:
            MigrationError: If migration fails
        """
        ...


class IGCPStorage(Protocol):
    """
    Interface for Cloud Storage operations.
    
    This protocol defines methods for interacting with Google Cloud Storage.
    """
    
    async def upload_file(
        self, 
        bucket_name: str, 
        source_file_path: str,
        destination_blob_name: Optional[str] = None
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
        ...
    
    async def download_file(
        self, 
        bucket_name: str, 
        source_blob_name: str,
        destination_file_path: str
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
        ...
    
    async def list_blobs(
        self, 
        bucket_name: str, 
        prefix: Optional[str] = None
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
        ...
    
    async def delete_blob(
        self,
        bucket_name: str,
        blob_name: str
    ) -> bool:
        """
        Delete a blob from a GCS bucket.
        
        Args:
            bucket_name: Name of the GCS bucket
            blob_name: Name of the blob to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ResourceNotFoundError: If bucket or blob not found
            StorageError: If deletion fails
        """
        ...


class IGCPFirestore(Protocol):
    """
    Interface for Firestore operations.
    
    This protocol defines methods for interacting with Google Firestore.
    """
    
    async def store_document(
        self, 
        collection_id: str, 
        document_id: Optional[str], 
        data: Dict[str, Any]
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
        ...
    
    async def get_document(
        self, 
        collection_id: str, 
        document_id: str
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
        ...
    
    async def update_document(
        self,
        collection_id: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """
        Update a document in Firestore.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document
            data: Data to update
            merge: Whether to merge with existing data
            
        Returns:
            True if updated successfully
            
        Raises:
            FirestoreError: If update fails
        """
        ...
    
    async def delete_document(
        self,
        collection_id: str,
        document_id: str
    ) -> bool:
        """
        Delete a document from Firestore.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document
            
        Returns:
            True if deleted successfully
            
        Raises:
            FirestoreError: If deletion fails
        """
        ...
    
    async def query_documents(
        self,
        collection_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents in Firestore.
        
        Args:
            collection_id: ID of the collection
            filters: Optional filters for the query
            limit: Optional limit for the results
            order_by: Optional ordering for the results
            
        Returns:
            List of document data
            
        Raises:
            FirestoreError: If query fails
        """
        ...


class IGCPVertexAI(Protocol):
    """
    Interface for Vertex AI operations.
    
    This protocol defines methods for interacting with Google Vertex AI.
    """
    
    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Vertex AI models.
        
        Returns:
            List of model information
            
        Raises:
            VertexAIError: If listing fails
        """
        ...
    
    async def predict_text(
        self, 
        model_name: str, 
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None
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
        ...
    
    async def initialize_vertex(
        self,
        location: str = "us-central1",
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Initialize the Vertex AI service.
        
        Args:
            location: GCP region for Vertex AI
            context: Optional context information
            
        Returns:
            True if initialized successfully
            
        Raises:
            VertexAIError: If initialization fails
        """
        ...