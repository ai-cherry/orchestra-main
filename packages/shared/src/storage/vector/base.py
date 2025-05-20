"""
Base classes for vector search implementations.

This module provides abstract base classes and interfaces for vector search
implementations, allowing for different backends to be used interchangeably.
"""

import abc
from typing import Any, Dict, List, Optional, Tuple, Protocol


class VectorSearchInterface(Protocol):
    """
    Protocol defining the interface for vector search implementations.

    This protocol defines the methods that must be implemented by any
    vector search backend to be compatible with the memory management system.
    """

    async def initialize(self) -> None:
        """
        Initialize the vector search backend.

        This method should establish any necessary connections and
        perform any required setup.

        Raises:
            Exception: If initialization fails
        """
        ...

    async def close(self) -> None:
        """
        Close the vector search backend.

        This method should clean up any resources used by the backend.
        """
        ...

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
            Exception: If the operation fails
        """
        ...

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
            Exception: If the search operation fails
        """
        ...

    async def delete_embedding(self, item_id: str) -> bool:
        """
        Delete a vector embedding from the backend.

        Args:
            item_id: ID of the embedding to delete

        Returns:
            True if the embedding was deleted, False if not found

        Raises:
            Exception: If the delete operation fails
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector search backend.

        Returns:
            Dictionary with health status information
        """
        ...


class AbstractVectorSearch(abc.ABC):
    """
    Abstract base class for vector search implementations.

    This class defines the interface that all vector search implementations
    must adhere to, ensuring compatibility with the memory management system.
    """

    @abc.abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the vector search backend.

        This method should establish any necessary connections and
        perform any required setup.

        Raises:
            Exception: If initialization fails
        """
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """
        Close the vector search backend.

        This method should clean up any resources used by the backend.
        """
        pass

    @abc.abstractmethod
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
            Exception: If the operation fails
        """
        pass

    @abc.abstractmethod
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
            Exception: If the search operation fails
        """
        pass

    @abc.abstractmethod
    async def delete_embedding(self, item_id: str) -> bool:
        """
        Delete a vector embedding from the backend.

        Args:
            item_id: ID of the embedding to delete

        Returns:
            True if the embedding was deleted, False if not found

        Raises:
            Exception: If the delete operation fails
        """
        pass

    @abc.abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector search backend.

        Returns:
            Dictionary with health status information
        """
        pass
