"""
Vector Search Providers for AI Orchestra.

This package provides interfaces and implementations for vector search,
allowing for semantic search capabilities in the memory system.
"""

from packages.shared.src.storage.vector.vector_search import VectorSearchProvider
from packages.shared.src.storage.vector.in_memory_vector_search import InMemoryVectorSearch

# Conditionally import GCP Vector Search if dependencies are available
try:
    from packages.shared.src.storage.vector.gcp_vector_search import GCPVectorSearch
    __all__ = ["VectorSearchProvider", "InMemoryVectorSearch", "GCPVectorSearch"]
except ImportError:
    __all__ = ["VectorSearchProvider", "InMemoryVectorSearch"]