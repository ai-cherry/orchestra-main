"""
Vertex AI Vector Search adapter for AI Orchestra.

This module provides an adapter for Google Cloud's Vertex AI Vector Search
(formerly Matching Engine) to be used for semantic search operations in the
memory management system.

It implements a common interface with the in-memory vector search implementation
to allow for seamless switching between implementations.
"""

import asyncio
import logging
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import MatchingEngineIndexEndpoint

from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.exceptions import StorageError, ConfigurationError
from packages.shared.src.storage.vector.base import AbstractVectorSearch
class VertexVectorSearchAdapter(AbstractVectorSearch):
    """
    Adapter for Google Cloud's Vertex AI Vector Search.
    
    This class provides methods for storing and retrieving vector embeddings
    using Google Cloud's Vertex AI Vector Search service, which is optimized
    for high-performance vector similarity search at scale.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-west4",
        index_endpoint_id: Optional[str] = None,
        index_id: Optional[str] = None,
        config: Optional[StorageConfig] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize the Vertex Vector Search adapter.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region (default: us-west4)
            index_endpoint_id: ID of the Vector Search index endpoint
            index_id: ID of the Vector Search index
            config: Optional storage configuration
            log_level: Logging level for this instance
        """
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._location = location
        self._index_endpoint_id = index_endpoint_id
        self._index_id = index_id
        self._config = config or StorageConfig()
        
        # Set up logging
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)
        
        # Initialize state
        self._initialized = False
        self._index_endpoint = None
        self._deployed_index_id = None
        
    async def initialize(self) -> None:
        """
        Initialize the connection to Vertex AI Vector Search.
        
        This method establishes a connection to the Vector Search service
        and validates the index endpoint and index.
        
        Raises:
            ConfigurationError: If required configuration is missing
            StorageError: If connection to Vector Search fails
        """
        if self._initialized:
            return
            
        try:
            # Validate configuration
            if not self._project_id:
                raise ConfigurationError("Google Cloud project ID is required")
                
            if not self._index_endpoint_id:
                raise ConfigurationError("Vector Search index endpoint ID is required")
                
            if not self._index_id:
                raise ConfigurationError("Vector Search index ID is required")
                
            # Initialize the AI Platform client
            aiplatform.init(project=self._project_id, location=self._location)
            
            # Get the index endpoint
            self._index_endpoint = await asyncio.to_thread(
                MatchingEngineIndexEndpoint.get,
                index_endpoint_id=self._index_endpoint_id
            )
            
            # Verify the index is deployed
            deployed_indexes = await asyncio.to_thread(
                lambda: self._index_endpoint.deployed_indexes
            )
            
            # Find the deployed index ID
            for deployed_index in deployed_indexes:
                if deployed_index.index == self._index_id:
                    self._deployed_index_id = deployed_index.id
                    break
                    
            if not self._deployed_index_id:
                raise ConfigurationError(
                    f"Index {self._index_id} is not deployed to endpoint {self._index_endpoint_id}"
                )
                
            self._initialized = True
            self._logger.info(
                f"Successfully initialized Vector Search connection to project {self._project_id}, "
                f"index endpoint {self._index_endpoint_id}, index {self._index_id}"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to initialize Vector Search: {e}")
            raise StorageError(f"Failed to initialize Vector Search: {e}")
            
    async def close(self) -> None:
        """
        Close the connection to Vector Search.
        
        This method cleans up resources used by the Vector Search client.
        """
        self._index_endpoint = None
        self._deployed_index_id = None
        self._initialized = False
        self._logger.debug("Closed Vector Search connection")
        
    def _check_initialized(self) -> None:
        """
        Check if the adapter is initialized and raise error if not.
        
        Raises:
            RuntimeError: If the adapter is not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "Vector Search adapter not initialized. Call initialize() first."
            )
            
    async def store_embedding(
        self, 
        item_id: str, 
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store a vector embedding in Vector Search.
        
        Args:
            item_id: Unique identifier for the embedding
            embedding: Vector embedding to store
            metadata: Optional metadata to associate with the embedding
            
        Raises:
            StorageError: If the operation fails
        """
        self._check_initialized()
        
        try:
            # Vector Search doesn't support direct embedding storage through the API
            # Embeddings are typically uploaded in batch through import jobs
            # This is a placeholder for future implementation
            self._logger.warning(
                "Direct embedding storage is not supported by Vector Search API. "
                "Use batch import jobs instead."
            )
            
        except Exception as e:
            self._logger.error(f"Failed to store embedding: {e}")
            raise StorageError(f"Failed to store embedding: {e}")
            
    async def find_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float]]:
        """
        Find similar embeddings in Vector Search.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Maximum number of results to return
            namespace: Optional namespace to restrict search
            filters: Optional filters to apply to the search
            
        Returns:
            List of tuples containing (item_id, similarity_score)
            
        Raises:
            StorageError: If the search operation fails
        """
        self._check_initialized()
        
        try:
            # Convert query embedding to numpy array
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            # Prepare filters if provided
            filter_str = None
            if filters:
                # Convert filters to Vector Search filter format
                filter_parts = []
                for key, value in filters.items():
                    filter_parts.append(f"{key} = {value}")
                filter_str = " AND ".join(filter_parts)
                
            # Perform the search
            response = await asyncio.to_thread(
                self._index_endpoint.match,
                deployed_index_id=self._deployed_index_id,
                queries=[query_vector],
                num_neighbors=top_k,
                filter=filter_str
            )
            
            # Process results
            results = []
            if response and len(response) > 0:
                matches = response[0]
                for match in matches:
                    item_id = match.id
                    distance = match.distance
                    # Convert distance to similarity score (1.0 - distance)
                    similarity = 1.0 - distance
                    results.append((item_id, similarity))
                    
            return results
            
        except Exception as e:
            self._logger.error(f"Failed to perform vector search: {e}")
            raise StorageError(f"Failed to perform vector search: {e}")
            
    async def delete_embedding(self, item_id: str) -> bool:
        """
        Delete a vector embedding from Vector Search.
        
        Args:
            item_id: ID of the embedding to delete
            
        Returns:
            True if the embedding was deleted, False if not found
            
        Raises:
            StorageError: If the delete operation fails
        """
        self._check_initialized()
        
        try:
            # Vector Search doesn't support direct deletion through the API
            # Deletions are typically handled through batch operations
            self._logger.warning(
                "Direct embedding deletion is not supported by Vector Search API. "
                "Use batch operations instead."
            )
            return False
            
        except Exception as e:
            self._logger.error(f"Failed to delete embedding: {e}")
            raise StorageError(f"Failed to delete embedding: {e}")
            
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Vector Search connection.
        
        Returns:
            Dictionary with health status information
        """
        health = {
            "status": "healthy",
            "vector_search": False,
            "details": {
                "provider": "vertex_ai_vector_search",
                "project_id": self._project_id,
                "location": self._location,
                "index_endpoint_id": self._index_endpoint_id,
                "index_id": self._index_id
            }
        }
        
        if not self._initialized:
            try:
                await self.initialize()
                health["details"]["initialization"] = "Initialized during health check"
            except Exception as e:
                health["status"] = "error"
                health["details"]["initialization_error"] = str(e)
                return health
                
        try:
            # Try to perform a simple search to verify connection
            test_vector = [0.0] * 768  # Assuming 768-dimensional embeddings
            await self.find_similar(test_vector, top_k=1)
            health["vector_search"] = True
            health["details"]["vector_search_check"] = "Successfully verified connectivity"
            
        except Exception as e:
            health["status"] = "error"
            health["details"]["vector_search_error"] = str(e)
            
        return health