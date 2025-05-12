"""
Extended domain interfaces for the GCP Migration toolkit.

This module defines additional interfaces for the comprehensive GCP service
architecture, supporting Secret Manager, Firestore, Storage, and Vertex AI integration.
"""

import abc
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union


class IGCPServiceCore(abc.ABC):
    """Core interface for interacting with Google Cloud Platform services."""
    
    @abc.abstractmethod
    def initialize(self) -> None:
        """
        Initialize the GCP service connections.
        
        Raises:
            AuthenticationError: If authentication with GCP fails
        """
        pass
    
    @property
    @abc.abstractmethod
    def project_id(self) -> str:
        """Get the current GCP project ID."""
        pass
    
    @abc.abstractmethod
    def check_gcp_apis_enabled(self) -> Dict[str, bool]:
        """
        Check if required GCP APIs are enabled.
        
        Returns:
            Dictionary of API names and their enabled status
        """
        pass
    
    @abc.abstractmethod
    def enable_gcp_apis(self, apis: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Enable required GCP APIs.
        
        Args:
            apis: List of APIs to enable (optional, uses default list if None)
            
        Returns:
            Dictionary of API names and their enabled status after enabling
        """
        pass
    
    @abc.abstractmethod
    def verify_ai_integration(self) -> Dict[str, Any]:
        """
        Verify AI integration with GCP services.
        Checks if all necessary components are in place.
        
        Returns:
            Dictionary with verification results
        """
        pass


class IGCPSecretManager(abc.ABC):
    """Interface for interacting with Google Secret Manager."""
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass


class IGCPStorage(abc.ABC):
    """Interface for interacting with Google Cloud Storage."""
    
    @abc.abstractmethod
    def upload_file(self, bucket_name: str, source_file_path: Path, 
                   destination_blob_name: Optional[str] = None) -> str:
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
        pass
    
    @abc.abstractmethod
    def download_file(self, bucket_name: str, source_blob_name: str,
                     destination_file_path: Path) -> Path:
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    def ensure_bucket_exists(self, bucket_name: str, region: Optional[str] = None) -> bool:
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
        pass


class IGCPFirestore(abc.ABC):
    """Interface for interacting with Google Firestore."""
    
    @abc.abstractmethod
    def store_document(self, collection: str, document_id: str, data: Dict[str, Any]) -> str:
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    def update_document(self, collection: str, document_id: str, data: Dict[str, Any],
                       merge: bool = True) -> bool:
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
        pass


class IGCPVertexAI(abc.ABC):
    """Interface for interacting with Google Vertex AI."""
    
    @abc.abstractmethod
    def initialize_vertex(self, location: str = "us-central1") -> None:
        """
        Initialize Vertex AI with project and location.
        
        Args:
            location: GCP region for Vertex AI resources
            
        Raises:
            VertexAIError: If initialization fails
        """
        pass
    
    @abc.abstractmethod
    def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available Vertex AI models.
        
        Returns:
            List of model information dictionaries
            
        Raises:
            VertexAIError: If getting the model list fails
        """
        pass


class IGeminiConfigService(abc.ABC):
    """Service for setting up and managing Gemini Code Assist configuration."""
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    def verify_installation(self) -> Dict[str, bool]:
        """
        Verify that Gemini Code Assist is installed and configured.
        
        Returns:
            Dictionary with verification results
            
        Raises:
            ConfigurationError: If verification fails
        """
        pass


class IExtendedGCPService(IGCPServiceCore, IGCPSecretManager, IGCPStorage, 
                          IGCPFirestore, IGCPVertexAI, IGeminiConfigService, abc.ABC):
    """Comprehensive interface for all GCP and AI assistant services."""
    pass