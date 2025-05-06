\"""
Vector Search Provider Interface for AI Orchestra.

This module defines the interface for vector search providers, allowing
for different implementations (in-memory, GCP Vector Search, etc.) to be
used interchangeably.
"""

import abc
from typing import Dict, List, Optional, Any, Tuple, Protocol


class VectorSearchProvider(Protocol):
    """Protocol for vector search providers."""
    
    async def initialize(self) -> None:
        """Initialize the vector search provider."""
        ...
        
    async def close(self) -> None:
        """Close the vector search provider."""
        ...
        
    async def index_embedding(
        self, 
        id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any]
    ) -> None:
        """
        Index an embedding vector.
        
        Args:
            id: Unique identifier for the embedding
            embedding: The vector embedding to index
            metadata: Additional metadata to store with the embedding
        """
        ...
        
    async def search(
        self, 
        query_embedding: List[float], 
        filters: Optional[Dict[str, Any]] = None, 
        top_k: int = 10,
        namespace: Optional[str] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: The query vector embedding
            filters: Optional filters to apply to the search
            top_k: Maximum number of results to return
            namespace: Optional namespace to search in
            
        Returns:
            List of tuples containing (id, similarity_score, metadata)
        """
        ...
        
    async def delete_embedding(self, id: str) -> bool:
        """
        Delete an embedding from the index.
        
        Args:
            id: The ID of the embedding to delete
            
        Returns:
            True if the embedding was deleted, False otherwise
        """
        ...
        
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector search provider.
        
        Returns:
            Dictionary with statistics
        """
        ...