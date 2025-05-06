"""
Vertex AI Vector Search integration for AI Orchestra memory system.

This module provides integration with Google Cloud Vertex AI Vector Search
for efficient and scalable semantic search operations.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform import MatchingEngineIndexEndpoint
    from google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint import Namespace
    VERTEX_VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VERTEX_VECTOR_SEARCH_AVAILABLE = False

from packages.shared.src.models.base_models import MemoryItem, PersonaConfig
from .monitoring import MemoryMonitoring

# Configure logging
logger = logging.getLogger(__name__)

class VertexVectorSearch:
    """
    Vertex AI Vector Search integration for semantic search.
    
    This class provides integration with Google Cloud Vertex AI Vector Search
    for efficient and scalable semantic search operations.
    """
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        index_endpoint_id: Optional[str] = None,
        index_id: Optional[str] = None,
        embedding_dimension: int = 768,
        monitoring: Optional[MemoryMonitoring] = None,
        enabled: bool = True,
    ):
        """
        Initialize the Vertex Vector Search integration.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            index_endpoint_id: ID of the Vector Search index endpoint
            index_id: ID of the Vector Search index
            embedding_dimension: Dimension of the embedding vectors
            monitoring: Optional monitoring instance
            enabled: Whether Vector Search is enabled
        """
        self.project_id = project_id
        self.location = location
        self.index_endpoint_id = index_endpoint_id
        self.index_id = index_id
        self.embedding_dimension = embedding_dimension
        self.monitoring = monitoring
        self.enabled = enabled and VERTEX_VECTOR_SEARCH_AVAILABLE
        
        self._index_endpoint = None
        self._initialized = False
        self._fallback_to_custom = False
        
        # Cache for document ID to MemoryItem mapping
        self._memory_item_cache: Dict[str, MemoryItem] = {}
        
    async def initialize(self) -> None:
        """
        Initialize the Vertex Vector Search client.
        
        This method initializes the connection to Vertex AI Vector Search
        and validates the index endpoint and index.
        
        Raises:
            ConnectionError: If connection to Vertex AI fails
            ValueError: If required configuration is missing
        """
        if not self.enabled:
            logger.warning("Vertex Vector Search is not enabled or not available")
            self._fallback_to_custom = True
            return
            
        if not self.index_endpoint_id or not self.index_id:
            logger.warning("Vertex Vector Search index_endpoint_id or index_id not provided")
            self._fallback_to_custom = True
            return
            
        try:
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Get the index endpoint
            self._index_endpoint = MatchingEngineIndexEndpoint(
                index_endpoint_name=self.index_endpoint_id
            )
            
            # Validate the index endpoint
            try:
                # This will raise an exception if the endpoint doesn't exist
                await asyncio.to_thread(self._index_endpoint.list_deployed_indexes)
                self._initialized = True
                logger.info(f"Vertex Vector Search initialized for project {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to validate Vertex Vector Search index endpoint: {e}")
                self._fallback_to_custom = True
                
        except Exception as e:
            logger.error(f"Failed to initialize Vertex Vector Search: {e}")
            self._fallback_to_custom = True
            
    def _check_initialized(self) -> None:
        """
        Check if Vertex Vector Search is initialized.
        
        Raises:
            RuntimeError: If Vertex Vector Search is not initialized
        """
        if not self._initialized and not self._fallback_to_custom:
            raise RuntimeError("Vertex Vector Search not initialized. Call initialize() first.")
            
    async def index_memory_item(self, item: MemoryItem) -> bool:
        """
        Index a memory item in Vertex Vector Search.
        
        Args:
            item: The memory item to index
            
        Returns:
            True if indexing was successful, False otherwise
        """
        if not self.enabled or self._fallback_to_custom:
            return False
            
        self._check_initialized()
        
        # Skip if no embedding
        if not item.embedding:
            logger.debug(f"Skipping indexing for item {item.id} with no embedding")
            return False
            
        # Ensure embedding has the correct dimension
        if len(item.embedding) != self.embedding_dimension:
            logger.warning(
                f"Embedding dimension mismatch: expected {self.embedding_dimension}, "
                f"got {len(item.embedding)} for item {item.id}"
            )
            return False
            
        try:
            start_time = time.time()
            
            # Create namespace for the user if it doesn't exist
            namespace = item.user_id
            
            # Prepare the document
            document = {
                "id": item.id,
                "embedding": item.embedding,
                "metadata": {
                    "user_id": item.user_id,
                    "item_type": item.item_type,
                    "timestamp": item.timestamp,
                }
            }
            
            # Add to session_id metadata if available
            if item.session_id:
                document["metadata"]["session_id"] = item.session_id
                
            # Add to cache for retrieval
            self._memory_item_cache[item.id] = item
            
            # Upsert the document
            await asyncio.to_thread(
                self._index_endpoint.upsert_datapoints,
                index_id=self.index_id,
                namespace=namespace,
                datapoints=[document]
            )
            
            # Record operation time if monitoring is enabled
            if self.monitoring:
                self.monitoring.record_operation_time(
                    "vertex_vector_search_index", time.time() - start_time
                )
                
            logger.debug(f"Indexed memory item {item.id} in Vertex Vector Search")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index memory item {item.id} in Vertex Vector Search: {e}")
            if self.monitoring:
                self.monitoring.record_error("vertex_vector_search_index")
            return False
            
    async def search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Perform semantic search using Vertex Vector Search.
        
        Args:
            user_id: The user ID to search memories for
            query_embedding: The vector embedding of the query
            persona_context: Optional persona context for personalized results
            top_k: Maximum number of results to return
            filters: Optional filters to apply
            
        Returns:
            List of tuples containing memory items and their similarity scores
        """
        if not self.enabled or self._fallback_to_custom:
            logger.warning("Vertex Vector Search not available, falling back to custom implementation")
            return []
            
        self._check_initialized()
        
        # Ensure query embedding has the correct dimension
        if len(query_embedding) != self.embedding_dimension:
            logger.warning(
                f"Query embedding dimension mismatch: expected {self.embedding_dimension}, "
                f"got {len(query_embedding)}"
            )
            return []
            
        try:
            start_time = time.time()
            
            # Create namespace for the user
            namespace = user_id
            
            # Prepare filter string if needed
            filter_string = None
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_parts.append(f'metadata.{key} = "{value}"')
                    else:
                        filter_parts.append(f'metadata.{key} = {value}')
                        
                if filter_parts:
                    filter_string = " AND ".join(filter_parts)
                    
            # Perform the search
            response = await asyncio.to_thread(
                self._index_endpoint.find_neighbors,
                index_id=self.index_id,
                namespace=namespace,
                queries=[query_embedding],
                num_neighbors=top_k,
                filter=filter_string
            )
            
            # Process results
            results = []
            if response and response.results and response.results[0].neighbors:
                for neighbor in response.results[0].neighbors:
                    item_id = neighbor.datapoint.datapoint_id
                    score = neighbor.distance
                    
                    # Get the memory item from cache or fetch it
                    if item_id in self._memory_item_cache:
                        item = self._memory_item_cache[item_id]
                        results.append((item, score))
                    else:
                        # In a real implementation, you would fetch the item from your storage
                        # For now, we'll just log a warning
                        logger.warning(f"Memory item {item_id} not found in cache")
                        
            # Record operation time if monitoring is enabled
            if self.monitoring:
                self.monitoring.record_operation_time(
                    "vertex_vector_search", time.time() - start_time
                )
                
            logger.debug(f"Performed semantic search for user {user_id}, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search in Vertex Vector Search: {e}")
            if self.monitoring:
                self.monitoring.record_error("vertex_vector_search")
            return []
            
    async def delete_memory_item(self, item: MemoryItem) -> bool:
        """
        Delete a memory item from Vertex Vector Search.
        
        Args:
            item: The memory item to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.enabled or self._fallback_to_custom:
            return False
            
        self._check_initialized()
        
        try:
            start_time = time.time()
            
            # Create namespace for the user
            namespace = item.user_id
            
            # Delete the document
            await asyncio.to_thread(
                self._index_endpoint.remove_datapoints,
                index_id=self.index_id,
                namespace=namespace,
                datapoint_ids=[item.id]
            )
            
            # Remove from cache
            if item.id in self._memory_item_cache:
                del self._memory_item_cache[item.id]
                
            # Record operation time if monitoring is enabled
            if self.monitoring:
                self.monitoring.record_operation_time(
                    "vertex_vector_search_delete", time.time() - start_time
                )
                
            logger.debug(f"Deleted memory item {item.id} from Vertex Vector Search")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory item {item.id} from Vertex Vector Search: {e}")
            if self.monitoring:
                self.monitoring.record_error("vertex_vector_search_delete")
            return False
            
    async def close(self) -> None:
        """Close the Vertex Vector Search client and release resources."""
        # Nothing to do here, as Vertex AI doesn't require explicit cleanup
        self._initialized = False
        self._memory_item_cache.clear()
        logger.debug("Closed Vertex Vector Search client")