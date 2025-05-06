"""
Vertex AI-based embedding service implementation.

This module provides an embedding service that uses Google Cloud's Vertex AI
to generate embeddings for use in vector search and semantic memory operations.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from fastapi import Depends

# Import Google Cloud
try:
    from google.cloud import aiplatform
    from google.api_core.exceptions import GoogleAPIError
    VERTEXAI_AVAILABLE = True
except ImportError:
    aiplatform = None
    GoogleAPIError = Exception
    VERTEXAI_AVAILABLE = False

# Import settings
from core.orchestrator.src.config.settings import Settings, get_settings

# Import base class (will fail gracefully if not available)
try:
    from packages.shared.src.embedding.embedding_service import EmbeddingService
    HAS_BASE_CLASS = True
except ImportError:
    HAS_BASE_CLASS = False
    # Create dummy base class
    class EmbeddingService:
        """Dummy base class for embedding service."""
        async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
            """Generate embeddings for a list of texts."""
            raise NotImplementedError("Base class method not implemented")

# Configure logging
logger = logging.getLogger(__name__)


class VertexEmbeddingService(EmbeddingService if HAS_BASE_CLASS else object):
    """
    Vertex AI implementation of embedding service.
    
    This class provides methods to generate embeddings using Google Cloud's 
    Vertex AI service and perform vector search operations against a Vertex
    AI Vector Search index.
    """
    
    def __init__(self, settings: Settings = Depends(get_settings)):
        """
        Initialize the Vertex AI embedding service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._initialized = False
        
        # Extract settings
        self.project_id = settings.get_gcp_project_id()
        self.location = settings.GCP_LOCATION
        self.index_name = settings.VECTOR_INDEX_NAME
        self.vector_dimension = settings.VECTOR_DIMENSION
        
        # Will be initialized later
        self.embedding_endpoint = None
        self.vector_search_index = None
    
    async def initialize(self) -> bool:
        """
        Initialize the Vertex AI client and services.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self._initialized or not VERTEXAI_AVAILABLE:
            return self._initialized
            
        # Skip if no project ID
        if not self.project_id:
            logger.info("No GCP project ID configured, skipping Vertex AI initialization")
            return False
            
        try:
            # Run initialization in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._initialize_sync)
            
            self._initialized = success
            if success:
                logger.info(f"Vertex AI embedding service initialized successfully")
            else:
                logger.warning("Vertex AI embedding service initialization failed")
                
            return success
        except Exception as e:
            logger.error(f"Error initializing Vertex AI embedding service: {e}")
            return False
    
    def _initialize_sync(self) -> bool:
        """
        Synchronous initialization of Vertex AI services.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Get text embedding model
            self.embedding_endpoint = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
            
            # Initialize Vector Search index if a name is provided
            if self.index_name:
                # Get the index endpoint
                index_endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
                    filter=f'display_name="{self.index_name}"',
                    project=self.project_id,
                    location=self.location
                )
                
                if index_endpoints:
                    self.vector_search_index = index_endpoints[0]
                    logger.info(f"Connected to Vector Search index: {self.index_name}")
                else:
                    logger.warning(f"Vector Search index not found: {self.index_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            return False
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Vertex AI.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
            
        Raises:
            RuntimeError: If the service is not initialized or an error occurs
        """
        if not self._initialized:
            await self.initialize()
            
        if not self._initialized or not self.embedding_endpoint:
            raise RuntimeError("Vertex AI embedding service not initialized")
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self._get_embeddings_sync(texts)
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}")
    
    def _get_embeddings_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Synchronous implementation of embedding generation.
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        # Generate embeddings
        embeddings = self.embedding_endpoint.get_embeddings(texts)
        
        # Extract values
        embedding_vectors = []
        for emb in embeddings:
            embedding_vectors.append(emb.values)
            
        return embedding_vectors
    
    async def vector_search(self, 
                           query_vector: List[float], 
                           namespace: str = "default",
                           num_neighbors: int = 10
                          ) -> List[Dict[str, Any]]:
        """
        Search the vector index for similar vectors.
        
        Args:
            query_vector: The embedding vector to search for
            namespace: The namespace to search within (default: "default")
            num_neighbors: Number of results to return (default: 10)
            
        Returns:
            List of search results containing the document ID and similarity score
            
        Raises:
            RuntimeError: If vector search is not initialized or an error occurs
        """
        if not self._initialized:
            await self.initialize()
            
        if not self._initialized or not self.vector_search_index:
            raise RuntimeError("Vertex AI Vector Search not initialized")
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._vector_search_sync(query_vector, namespace, num_neighbors)
            )
            
            return results
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            raise RuntimeError(f"Failed to perform vector search: {e}")
    
    def _vector_search_sync(self, 
                           query_vector: List[float], 
                           namespace: str = "default",
                           num_neighbors: int = 10
                          ) -> List[Dict[str, Any]]:
        """
        Synchronous implementation of vector search.
        
        Args:
            query_vector: The embedding vector to search for
            namespace: The namespace to search within
            num_neighbors: Number of results to return
            
        Returns:
            List of search results
        """
        # Perform the search
        response = self.vector_search_index.find_neighbors(
            deployed_index_id=self.index_name,
            queries=[query_vector],
            num_neighbors=num_neighbors,
            return_full_datapoint=True
        )
        
        # Extract results
        results = []
        for match in response[0]:
            # Parse metadata if available
            metadata = {}
            if hasattr(match, 'datapoint') and hasattr(match.datapoint, 'user_info'):
                try:
                    metadata = json.loads(match.datapoint.user_info)
                except json.JSONDecodeError:
                    metadata = {"raw_info": match.datapoint.user_info}
            
            # Add to results
            results.append({
                "id": match.id,
                "distance": match.distance,
                "metadata": metadata
            })
            
        return results
    
    async def close(self) -> None:
        """Close the Vertex AI connections."""
        self._initialized = False
        self.embedding_endpoint = None
        self.vector_search_index = None
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Vertex AI embedding service.
        
        Returns:
            Dictionary with health status information
        """
        if not VERTEXAI_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "Vertex AI library not available",
                "initialized": False
            }
            
        if not self.project_id:
            return {
                "status": "not_configured",
                "message": "GCP project ID not configured",
                "initialized": False
            }
            
        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to initialize Vertex AI: {e}",
                    "initialized": False
                }
        
        if not self._initialized:
            return {
                "status": "error",
                "message": "Vertex AI initialization failed",
                "initialized": False
            }
            
        # Check if embedding works
        try:
            # Run a simple test
            loop = asyncio.get_event_loop()
            test_result = await loop.run_in_executor(
                None,
                lambda: self._get_embeddings_sync(["Test health check"])
            )
            
            status = {
                "status": "healthy",
                "message": "Vertex AI embedding service is working",
                "initialized": True,
                "project_id": self.project_id,
                "location": self.location,
                "embedding_available": True,
                "vector_search_available": self.vector_search_index is not None,
                "vector_dimension": self.vector_dimension
            }
            
            if self.vector_search_index:
                status["index_name"] = self.index_name
                
            return status
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vertex AI health check failed: {e}",
                "initialized": self._initialized,
                "project_id": self.project_id,
                "location": self.location
            }
