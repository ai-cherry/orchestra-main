"""
Factory for vector search implementations.

This module provides a factory for creating vector search implementations,
allowing for easy switching between different backends.
"""

import logging
import os
from typing import Dict, Any, Optional, Type

from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.vector.base import AbstractVectorSearch
from packages.shared.src.storage.vector.in_memory_vector_search import InMemoryVectorSearch

# Lazy import to avoid circular dependencies
def _import_vertex_vector_search():
    from packages.shared.src.storage.vector.vertex_vector_search import VertexVectorSearchAdapter
    return VertexVectorSearchAdapter


class VectorSearchFactory:
    """
    Factory for creating vector search implementations.
    
    This class provides methods for creating different vector search
    implementations based on configuration.
    """
    
    @staticmethod
    def create_vector_search(
        provider: str = "in_memory",
        config: Optional[Dict[str, Any]] = None,
        log_level: int = logging.INFO
    ) -> AbstractVectorSearch:
        """
        Create a vector search implementation.
        
        Args:
            provider: The vector search provider to use
                      ("in_memory" or "vertex")
            config: Configuration for the vector search provider
            log_level: Logging level for the vector search provider
            
        Returns:
            An instance of a class implementing AbstractVectorSearch
            
        Raises:
            ValueError: If the provider is not supported
        """
        config = config or {}
        storage_config = StorageConfig()
        
        if provider == "in_memory":
            dimensions = config.get("dimensions", 768)
            return InMemoryVectorSearch(
                dimensions=dimensions,
                log_level=log_level
            )
        elif provider == "vertex":
            # Import here to avoid circular dependencies
            VertexVectorSearchAdapter = _import_vertex_vector_search()
            
            project_id = config.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = config.get("location", "us-west4")
            index_endpoint_id = config.get("index_endpoint_id")
            index_id = config.get("index_id")
            
            return VertexVectorSearchAdapter(
                project_id=project_id,
                location=location,
                index_endpoint_id=index_endpoint_id,
                index_id=index_id,
                config=storage_config,
                log_level=log_level
            )
        else:
            raise ValueError(f"Unsupported vector search provider: {provider}")
            
    @staticmethod
    def get_available_providers() -> Dict[str, Type[AbstractVectorSearch]]:
        """
        Get a dictionary of available vector search providers.
        
        Returns:
            Dictionary mapping provider names to their implementation classes
        """
        providers = {
            "in_memory": InMemoryVectorSearch
        }
        
        # Check if Vertex AI is available
        try:
            VertexVectorSearchAdapter = _import_vertex_vector_search()
            providers["vertex"] = VertexVectorSearchAdapter
        except ImportError:
            pass
            
        return providers