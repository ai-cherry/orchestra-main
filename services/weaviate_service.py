"""
Weaviate service for vector search and RAG operations.
Provides clean interface for AI applications.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import weaviate
from pydantic import BaseModel
from weaviate.classes.init import AdditionalConfig, Timeout

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class WeaviateConfig(BaseModel):
    """Configuration model for Weaviate connection."""

    host: str
    port: int = 8080
    api_key: Optional[str] = None
    timeout: int = 10


class VectorSearchResult(BaseModel):
    """Model for vector search results."""

    id: str
    distance: float
    metadata: Dict[str, Any]


class WeaviateService:
    def __init__(self, config: WeaviateConfig):
        """
        Initialize Weaviate client with connection settings.

        Args:
            config: Weaviate connection parameters
        """
        self.config = config
        self.client = self._initialize_client()
        self._verify_connection()

    def _initialize_client(self) -> weaviate.Client:
        """Create and configure Weaviate client with Paperspace support."""
        try:
            if os.getenv("PAPERSPACE_ENV") == "true":
                # Paperspace local configuration
                return weaviate.connect_to_local(
                    host="localhost",
                    port=int(os.getenv("MCP_WEAVIATE_SERVER_PORT", "8081")),
                    timeout=Timeout(connect=self.config.timeout),
                    additional_config=AdditionalConfig(
                        auth=weaviate.AuthApiKey(os.getenv("PAPERSPACE_WEAVIATE_API_KEY"))
                    ),
                )
            else:
                # DigitalOcean production configuration
                return weaviate.connect_to_local(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=Timeout(connect=self.config.timeout),
                    additional_config=AdditionalConfig(
                        auth=(weaviate.AuthApiKey(self.config.api_key) if self.config.api_key else None)
                    ),
                )
        except Exception as e:
            logger.error("Weaviate initialization failed: %s", str(e))
            raise

    def _verify_connection(self) -> None:
        """Verify Weaviate connection is active."""
        try:
            if not self.client.is_ready():
                raise ConnectionError("Weaviate connection failed")
            logger.info("Weaviate connection established")
        except Exception as e:
            logger.error("Weaviate connection test failed: %s", str(e))
            raise

    def vector_search(
        self, collection: str, query_vector: List[float], limit: int = 10, **filters
    ) -> List[VectorSearchResult]:
        """
        Perform vector similarity search.

        Args:
            collection: Name of Weaviate collection
            query_vector: Embedding vector for query
            limit: Maximum results to return
            filters: Additional filter parameters

        Returns:
            List of search results with distances
        """
        try:
            with self.client as client:
                collection = client.collections.get(collection)
                response = collection.query.near_vector(near_vector=query_vector, limit=limit, filters=filters)
                return [
                    VectorSearchResult(
                        id=result.uuid,
                        distance=result.metadata.distance,
                        metadata=result.properties,
                    )
                    for result in response.objects
                ]
        except Exception as e:
            logger.error("Vector search failed: %s", str(e))
            raise

    def create_schema(self, class_definition: Dict[str, Any]) -> bool:
        """
        Create or update Weaviate schema.

        Args:
            class_definition: Schema definition dictionary

        Returns:
            True if operation succeeded
        """
        try:
            with self.client as client:
                client.schema.create_class(class_definition)
                return True
        except Exception as e:
            logger.error("Schema creation failed: %s", str(e))
            return False

    def close(self) -> None:
        """Cleanup client connection."""
        if hasattr(self, "client") and self.client:
            self.client.close()


# Example usage
if __name__ == "__main__":
    service = WeaviateService(WeaviateConfig(host="localhost", api_key="your-api-key"))
    results = service.vector_search(collection="Articles", query_vector=[0.1, 0.2, 0.3])
    print(results)
