"""
Embedding Generator Module for File Ingestion System.

This module provides integration with Vertex AI to generate embeddings
for text chunks that will be stored in the vector database.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union

from google.cloud import aiplatform
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError

from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingGenerationError(Exception):
    """Exception for embedding generation-related errors."""
    pass


class EmbeddingGenerator:
    """
    Vertex AI embedding generation implementation.
    
    This class provides methods for generating vector embeddings
    from text chunks using Vertex AI Embedding API.
    """
    
    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None):
        """
        Initialize the embedding generator with Vertex AI settings.
        
        Args:
            project_id: Optional Google Cloud project ID. If not provided,
                       will be read from settings or environment.
            location: Optional Vertex AI API location. If not provided,
                    will be read from settings.
        """
        settings = get_settings()
        vertex_settings = settings.vertex_ai
        
        self.project_id = project_id or vertex_settings.project_id
        self.location = location or vertex_settings.location
        self.embedding_model = vertex_settings.embedding_model
        self._client = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the Vertex AI client."""
        if self._initialized:
            return
            
        try:
            # Initialize Vertex AI SDK
            client_options = ClientOptions(api_endpoint=f"{self.location}-aiplatform.googleapis.com")
            
            # Init aiplatform
            aiplatform.init(
                project=self.project_id,
                location=self.location,
                client_options=client_options
            )
            
            # Initialize Prediction Service client
            self._client = aiplatform.PredictionServiceClient(client_options=client_options)
            
            self._initialized = True
            logger.info("Vertex AI embedding generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI client: {e}")
            raise EmbeddingGenerationError(f"Failed to initialize Vertex AI: {e}")
            
    def _check_initialized(self) -> None:
        """Check if the client is initialized and raise error if not."""
        if not self._initialized or not self._client:
            raise EmbeddingGenerationError("Vertex AI client not initialized")
            
    @staticmethod
    def _format_text_for_embeddings(text: str) -> Dict[str, str]:
        """
        Format text for the embedding model.
        
        Args:
            text: Text to format
            
        Returns:
            Dictionary formatted for the model
        """
        return {"content": text}
        
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text chunk using Vertex AI.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of float values representing the embedding vector
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        self._check_initialized()
        
        if not text:
            raise EmbeddingGenerationError("Cannot generate embedding for empty text")
            
        try:
            # Get the model endpoint
            model_name = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.embedding_model}"
            
            # Format text for the model
            instances = [self._format_text_for_embeddings(text)]
            
            # Run synchronously (since Vertex AI's Python client doesn't offer async)
            response = self._client.predict(endpoint=model_name, instances=instances)
            
            # Extract the embedding vector from the response
            embeddings = response.predictions[0]["embeddings"]["values"]
            
            logger.debug(f"Generated embedding with {len(embeddings)} dimensions")
            return embeddings
        except GoogleAPIError as e:
            logger.error(f"Vertex AI API error: {e}")
            raise EmbeddingGenerationError(f"Vertex AI API error: {e}")
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {e}")
            
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 5) -> List[List[float]]:
        """
        Generate embeddings for multiple text chunks in batches.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        self._check_initialized()
        
        if not texts:
            return []
            
        try:
            # Create batches of texts
            batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
            
            all_embeddings = []
            
            for batch in batches:
                # Get the model endpoint
                model_name = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.embedding_model}"
                
                # Format texts for the model
                instances = [self._format_text_for_embeddings(text) for text in batch]
                
                # Run synchronously (since Vertex AI's Python client doesn't offer async)
                response = self._client.predict(endpoint=model_name, instances=instances)
                
                # Extract the embedding vectors from the response
                batch_embeddings = [pred["embeddings"]["values"] for pred in response.predictions]
                all_embeddings.extend(batch_embeddings)
                
                # Add a small delay to avoid rate limits
                if len(batches) > 1:
                    await asyncio.sleep(0.5)
                    
            logger.debug(f"Generated {len(all_embeddings)} embeddings in {len(batches)} batches")
            return all_embeddings
        except GoogleAPIError as e:
            logger.error(f"Vertex AI API error in batch: {e}")
            raise EmbeddingGenerationError(f"Vertex AI API error in batch: {e}")
        except Exception as e:
            logger.error(f"Error generating embeddings in batch: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embeddings in batch: {e}")
            
    async def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings generated by the model.
        
        This method generates a sample embedding and returns its dimension.
        
        Returns:
            Dimension of the embedding vector
            
        Raises:
            EmbeddingGenerationError: If dimension retrieval fails
        """
        try:
            # Generate embedding for a simple sample text
            sample_embedding = await self.generate_embedding("Sample text for dimension check")
            
            return len(sample_embedding)
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {e}")
            raise EmbeddingGenerationError(f"Failed to get embedding dimension: {e}")
