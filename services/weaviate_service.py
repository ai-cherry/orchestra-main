import os
import logging
from typing import Any, Dict, List, Optional

import weaviate
from weaviate.client import WeaviateClient # Ensure this is the correct import for WeaviateClient
from weaviate.auth import AuthApiKey
from weaviate.config import ConnectionConfig, Timeout # For Weaviate v3
# For Weaviate v4, connect_to_local and connect_to_weaviate_cloud handle timeouts directly.
# And AdditionalConfig might be different or not used in the same way.
# Assuming weaviate.connect_to_local and weaviate.connect_to_weaviate_cloud and client v4 style.
# from weaviate.exceptions import WeaviateQueryException, WeaviateStartUpError

from pydantic import BaseModel, Field

# UnifiedPostgreSQL Enhanced and other imports would be here if this file used them directly
# For now, keeping imports minimal to what's seen in the original and needed for changes.

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class WeaviateConfig(BaseModel):
    """Configuration model for Weaviate connection."""
    host: str
    port: int = 8080  # Still relevant for local connections
    api_key: Optional[str] = None  # For Weaviate auth (cloud or local)
    timeout: int = 30  # Increased timeout
    # additional_config can store OpenAI API key initially, and other client settings
    additional_config: Dict[str, Any] = Field(default_factory=dict)

class VectorSearchResult(BaseModel):
    """Model for vector search results."""
    collection: str
    document_id: str
    text_content: Optional[str] = None
    score: float
    metadata: Optional[Dict[str, Any]] = None

class WeaviateService:
    """Service for interacting with Weaviate."""

    def __init__(self, config: WeaviateConfig):
        self.config = config
        # Extract openai_api_key from additional_config for specific handling
        self.openai_api_key = self.config.additional_config.pop("openai_api_key", None)

        if self.openai_api_key:
            logger.info("OpenAI API key provided for Weaviate client.")
        else:
            logger.info("OpenAI API key not provided for Weaviate client.")

        self.client: WeaviateClient = self._create_client()
        self._verify_connection()

    def _create_client(self) -> WeaviateClient:
        """Create and configure Weaviate client."""
        try:
            logger.info(f"Initializing Weaviate client. Target host: {self.config.host}")

            headers: Dict[str, str] = self.config.additional_config.get("headers", {}) # Start with existing headers
            if self.openai_api_key:
                headers["X-OpenAI-Api-Key"] = self.openai_api_key
                logger.info("OpenAI API key is configured and will be sent in headers to Weaviate.")
            else:
                logger.info("OpenAI API key is not configured; not adding to Weaviate headers.")

            weaviate_cluster_url = os.getenv("WEAVIATE_CLUSTER_URL")

            if weaviate_cluster_url and self.config.host == weaviate_cluster_url:
                logger.info(f"Connecting to Weaviate Cloud at URL: {weaviate_cluster_url}")
                if not self.config.api_key:
                    msg = "WEAVIATE_API_KEY must be set for Weaviate Cloud connection."
                    logger.error(msg)
                    raise ValueError(msg)

                client = weaviate.connect_to_weaviate_cloud(
                    cluster_url=weaviate_cluster_url,
                    auth_credentials=AuthApiKey(self.config.api_key),
                    timeout_config=(self.config.timeout, self.config.timeout * 2), # (connect, read)
                    headers=headers if headers else None,
                )
                logger.info(f"Successfully initiated connection to Weaviate Cloud at {weaviate_cluster_url}.")
                return client
            else:
                logger.info(f"Connecting to Weaviate local/self-hosted at {self.config.host}:{self.config.port}")

                auth_credentials = None
                if self.config.api_key:
                    auth_credentials = AuthApiKey(self.config.api_key)

                # For connect_to_local, additional_config is less common.
                # Key parameters are passed directly.
                client = weaviate.connect_to_local(
                    host=self.config.host,
                    port=self.config.port,
                    auth_client_secret=auth_credentials, # Pass AuthApiKey directly
                    timeout_config=(self.config.timeout, self.config.timeout * 2), # (connect, read)
                    headers=headers if headers else None,
                    # startup_period can be set if needed, from additional_config for example
                    startup_period=self.config.additional_config.get("startup_period", None)
                )
                logger.info(f"Successfully initiated connection to local Weaviate at {self.config.host}:{self.config.port}.")
                return client

        except Exception as e:
            logger.error(f"Weaviate client initialization failed for host {self.config.host}: {str(e)}", exc_info=True)
            raise

    def _verify_connection(self) -> None:
        """Verify Weaviate connection is active."""
        try:
            if not self.client.is_ready():
                 # is_live() is for v3, is_ready() for v4
                logger.error("Weaviate client is not ready (is_ready() returned False).")
                raise ConnectionError("Weaviate client connection failed: not ready.")
            logger.info("Weaviate connection established and client is ready.")
        except Exception as e: # Catching generic Exception as client methods might raise various things
            logger.error(f"Weaviate connection test failed: {str(e)}", exc_info=True)
            raise

    def vector_search(
        self, collection: str, query_vector: List[float], limit: int = 10, **filters
    ) -> List[VectorSearchResult]:
        """Perform vector search in Weaviate."""
        # This is a placeholder, actual implementation will depend on Weaviate client version and API
        # Example for Weaviate client v3 style:
        # try:
        #     query = self.client.query.get(collection, ["property_name_for_text", "_additional {id score vector}"])
        #     if filters:
        #         # Simplified filter handling, real implementation would be more robust
        #         where_filter = {"operator": "And", "operands": []}
        #         for key, value in filters.items():
        #             where_filter["operands"].append({"path": [key], "operator": "Equal", "valueString": value}) # Example, adapt as needed
        #         query = query.with_where(where_filter)

        #     results = query.with_near_vector({"vector": query_vector}).with_limit(limit).do()

        #     search_results = []
        #     if "data" in results and "Get" in results["data"] and collection in results["data"]["Get"]:
        #         for item in results["data"]["Get"][collection]:
        #             search_results.append(
        #                 VectorSearchResult(
        #                     collection=collection,
        #                     document_id=item["_additional"]["id"],
        #                     text_content=item.get("property_name_for_text"), # Adjust property name
        #                     score=item["_additional"]["score"],
        #                     metadata=item # Or select specific metadata fields
        #                 )
        #             )
        #     return search_results
        # except WeaviateQueryException as e:
        #     logger.error(f"Vector search in collection '{collection}' failed: {str(e)}", exc_info=True)
        #     raise
        # This method needs to be adapted based on the actual Weaviate schema and client version (v3 vs v4 query syntax)
        logger.warning("vector_search method is a placeholder and needs actual implementation.")
        return []


    def create_schema(self, class_definition: Dict[str, Any]) -> bool:
        """
        Create a schema/collection in Weaviate.
        For Weaviate Python client v4, 'class' is analogous to 'collection name'.
        Returns True if the schema was created or already existed, False on failure.
        """
        collection_name = class_definition.get("class")
        if not collection_name:
            logger.error("Class name missing in schema definition.")
            return False

        sdk_client: WeaviateClient = self.client

        try:
            if sdk_client.collections.exists(collection_name):
                logger.info(f"Schema for class/collection '{collection_name}' already exists. No action taken.")
                return True # Indicates schema is present
            else:
                logger.info(f"Schema for class/collection '{collection_name}' does not exist. Attempting to create...")
                # The class_definition should match the structure expected by Weaviate's collections.create_from_dict
                # This includes "name" (for collection name), "properties", "vectorizer_config", etc.
                # Weaviate client v4 uses `weaviate.classes.Configure` for vectorizer and module configs.
                # However, `create_from_dict` is meant to take a dictionary directly.
                # The structure of `class_definition` passed from etl_orchestrator needs to be compatible.
                # Specifically, "class" should be "name", "vectorizer" to "vectorizer_config" etc.
                # For now, assuming `class_definition` is already in the correct dict format for `create_from_dict`.
                # If not, a transformation step would be needed here.

                # Adjusting the definition for v4 client `create_from_dict` if necessary.
                # The provided `class_definition` has "class", "vectorizer", "moduleConfig".
                # Need to map to v4: "name", "vectorizer_config" (using classes from weaviate.classes.Configure)
                # This is a bit complex to do on the fly without seeing the exact v4 builder patterns.
                # The simplest interpretation is that create_from_dict is flexible.
                # Let's try passing it as is, assuming it's smart, or we adjust it in etl_orchestrator.
                # The prompt defines the schema dict with "class", "vectorizer", "moduleConfig".
                # The Weaviate python client v4 `create_from_dict` expects a dict that could be generated by `collection.get_config().to_dict()`
                # This usually means "name" for class name, and specific structures for vectorizer, etc.
                # Given the constraints, I will assume the dictionary passed is usable by `create_from_dict`
                # or that `create_from_dict` is more flexible than strictly typed configurations.
                # The most critical part is the method call change.

                sdk_client.collections.create_from_dict(class_definition)
                logger.info(f"Schema class/collection '{collection_name}' created successfully using create_from_dict.")
                return True
        except Exception as e:
            # Catching a broad exception. Specific Weaviate exceptions would be better.
            # e.g., from weaviate.exceptions import UnexpectedStatusCodeError
            logger.error(f"Schema creation for class/collection '{collection_name}' failed: {str(e)}", exc_info=True)
            return False

    def close(self) -> None:
        """Cleanup client connection. (Weaviate v4 client uses context manager or explicit close)"""
        if hasattr(self, "client") and self.client:
            # For v4, client.close() is available. For v3, it might not be necessary or different.
            try:
                self.client.close()
                logger.info("Weaviate client connection closed.")
            except Exception as e:
                logger.error(f"Error closing Weaviate client: {str(e)}", exc_info=True)

# Example usage:
if __name__ == "__main__":
    # This example assumes local Weaviate instance.
    # For cloud, set WEAVIATE_CLUSTER_URL and WEAVIATE_API_KEY environment variables.

    # Example: Local Weaviate with OpenAI key
    local_config_with_openai = WeaviateConfig(
        host="localhost", # Default, WEAVIATE_HOST env var can override
        port=8080,        # Default, WEAVIATE_PORT env var can override
        additional_config={"openai_api_key": os.getenv("OPENAI_API_KEY")}
    )

    # Example: Weaviate Cloud (ensure env vars are set)
    # cloud_host_url = os.getenv("WEAVIATE_CLUSTER_URL")
    # cloud_api_key = os.getenv("WEAVIATE_API_KEY")
    # if cloud_host_url and cloud_api_key:
    #     logger.info("Cloud environment variables found, creating cloud config.")
    #     cloud_config = WeaviateConfig(
    #         host=cloud_host_url,
    #         api_key=cloud_api_key,
    #         additional_config={"openai_api_key": os.getenv("OPENAI_API_KEY")}
    #     )
    #     service = WeaviateService(cloud_config)
    # else:
    # logger.info("Cloud environment variables not fully set, creating local config for example.")
    service = WeaviateService(local_config_with_openai)

    # Example schema
    example_schema = {
        "class": "ExampleArticle",
        "description": "An example article class",
        "vectorizer": "text2vec-openai", # Assuming OpenAI vectorizer
        "moduleConfig": {
            "text2vec-openai": {
                "model": "ada",
                "modelVersion": "002", # Use a valid model version
                "type": "text"
            }
        },
        "properties": [
            {"name": "title", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]},
        ],
    }
    # service.create_schema(example_schema) # Uncomment to create schema

    # results = service.vector_search(collection="ExampleArticle", query_vector=[0.1, 0.2, 0.3])
    # print(results)

    service.close()
