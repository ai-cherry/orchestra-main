"""
In-Memory Vector Search Provider for AI Orchestra.

This module provides a simple in-memory implementation of the vector search
interface for testing and development purposes.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from packages.shared.src.storage.vector.base import AbstractVectorSearch


class InMemoryVectorSearch(AbstractVectorSearch):
    """
    In-memory vector search implementation.

    This class provides a simple in-memory implementation of vector search
    for testing and development purposes. It is not suitable for production use
    with large datasets.
    """

    def __init__(self, dimensions: int = 768, log_level: int = logging.INFO):
        """
        Initialize the in-memory vector search.

        Args:
            dimensions: The dimensionality of the vectors
            log_level: Logging level for this instance
        """
        self._dimensions = dimensions
        self._embeddings: Dict[str, List[float]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

        # Set up logging
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)

    async def initialize(self) -> None:
        """Initialize the vector search provider."""
        self._initialized = True

    async def close(self) -> None:
        """Close the vector search provider."""
        self._initialized = False

    async def store_embedding(
        self,
        item_id: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store a vector embedding in the backend.

        Args:
            item_id: Unique identifier for the embedding
            embedding: Vector embedding to store
            metadata: Optional metadata to associate with the embedding

        Raises:
            ValueError: If the embedding dimension doesn't match
        """
        if len(embedding) != self._dimensions:
            raise ValueError(
                f"Expected embedding dimension {self._dimensions}, got {len(embedding)}"
            )

        self._embeddings[item_id] = embedding
        self._metadata[item_id] = metadata or {}

        self._logger.debug(f"Stored embedding for item {item_id}")

    async def find_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Find similar embeddings in the backend.

        Args:
            query_embedding: Query vector embedding
            top_k: Maximum number of results to return
            namespace: Optional namespace to restrict search
            filters: Optional filters to apply to the search

        Returns:
            List of tuples containing (item_id, similarity_score)

        Raises:
            ValueError: If the query dimension doesn't match
        """
        if len(query_embedding) != self._dimensions:
            raise ValueError(
                f"Expected query dimension {self._dimensions}, got {len(query_embedding)}"
            )

        self._logger.debug(f"Searching for similar embeddings with top_k={top_k}")

        # Use numpy if available for efficient computation
        if NUMPY_AVAILABLE:
            return await self._find_similar_numpy(
                query_embedding, top_k, namespace, filters
            )
        else:
            return await self._find_similar_python(
                query_embedding, top_k, namespace, filters
            )

    async def _find_similar_numpy(
        self,
        query_embedding: List[float],
        top_k: int,
        namespace: Optional[str],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float]]:
        """
        Find similar embeddings using numpy for efficient computation.

        Args:
            query_embedding: Query vector embedding
            top_k: Maximum number of results to return
            namespace: Optional namespace to restrict search
            filters: Optional filters to apply to the search

        Returns:
            List of tuples containing (item_id, similarity_score)
        """
        query_np = np.array(query_embedding)
        query_norm = np.linalg.norm(query_np)

        results = []
        for item_id, embedding in self._embeddings.items():
            # Apply filters if provided
            if filters and not self._matches_filters(item_id, filters):
                continue

            # Apply namespace filter if provided
            if namespace and self._metadata[item_id].get("namespace") != namespace:
                continue

            # Calculate cosine similarity
            embedding_np = np.array(embedding)
            embedding_norm = np.linalg.norm(embedding_np)

            if embedding_norm > 0 and query_norm > 0:
                similarity = np.dot(query_np, embedding_np) / (
                    query_norm * embedding_norm
                )
            else:
                similarity = 0.0

            results.append((item_id, float(similarity)))

        # Sort by similarity (descending) and take top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def _find_similar_python(
        self,
        query_embedding: List[float],
        top_k: int,
        namespace: Optional[str],
        filters: Optional[Dict[str, Any]],
    ) -> List[Tuple[str, float]]:
        """
        Find similar embeddings using pure Python (slower but no dependencies).

        Args:
            query_embedding: Query vector embedding
            top_k: Maximum number of results to return
            namespace: Optional namespace to restrict search
            filters: Optional filters to apply to the search

        Returns:
            List of tuples containing (item_id, similarity_score)
        """
        query_norm = sum(x * x for x in query_embedding) ** 0.5

        results = []
        for item_id, embedding in self._embeddings.items():
            # Apply filters if provided
            if filters and not self._matches_filters(item_id, filters):
                continue

            # Apply namespace filter if provided
            if namespace and self._metadata[item_id].get("namespace") != namespace:
                continue

            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
            embedding_norm = sum(x * x for x in embedding) ** 0.5

            if embedding_norm > 0 and query_norm > 0:
                similarity = dot_product / (embedding_norm * query_norm)
            else:
                similarity = 0.0

            results.append((item_id, similarity))

        # Sort by similarity (descending) and take top_k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def delete_embedding(self, item_id: str) -> bool:
        """
        Delete a vector embedding from the backend.

        Args:
            item_id: ID of the embedding to delete

        Returns:
            True if the embedding was deleted, False if not found
        """
        if item_id in self._embeddings:
            del self._embeddings[item_id]
            del self._metadata[item_id]
            self._logger.debug(f"Deleted embedding for item {item_id}")
            return True
        return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector search backend.

        Returns:
            Dictionary with health status information
        """
        return {
            "status": "healthy",
            "vector_search": True,
            "details": {
                "provider": "in_memory_vector_search",
                "dimensions": self._dimensions,
                "count": len(self._embeddings),
                "memory_usage_bytes": self._estimate_memory_usage(),
                "numpy_available": NUMPY_AVAILABLE,
            },
        }

    def _matches_filters(self, item_id: str, filters: Dict[str, Any]) -> bool:
        """
        Check if an embedding's metadata matches the given filters.

        Args:
            item_id: The ID of the embedding
            filters: The filters to apply

        Returns:
            True if the metadata matches all filters, False otherwise
        """
        metadata = self._metadata.get(item_id, {})

        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False

        return True

    def _estimate_memory_usage(self) -> int:
        """
        Estimate the memory usage of the stored embeddings.

        Returns:
            Estimated memory usage in bytes
        """
        # Rough estimate: 8 bytes per float (64-bit), plus overhead
        embedding_size = self._dimensions * 8
        total_embeddings = len(self._embeddings)

        # Add estimated metadata size (very rough estimate)
        metadata_size = sum(
            len(str(k)) + len(str(v))
            for m in self._metadata.values()
            for k, v in m.items()
        )

        return total_embeddings * embedding_size + metadata_size
