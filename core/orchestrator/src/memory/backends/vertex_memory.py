"""
Vertex AI memory backend for AI Orchestra.

This module provides a Vertex AI-based memory implementation for long-term semantic storage.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import aiplatform
from google.cloud import firestore

from core.orchestrator.src.memory.interface import MemoryInterface

logger = logging.getLogger(__name__)


class VertexMemory(MemoryInterface):
    """Vertex AI-based memory implementation for long-term semantic storage."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-west4",
        index_name: str = "orchestra-memory-index",
        embedding_model: str = "textembedding-gecko@003",
        collection_name: str = "vertex_memory",
        client=None,
        firestore_client=None,
    ):
        """
        Initialize Vertex AI memory.

        Args:
            project_id: GCP project ID
            location: GCP region
            index_name: Vector index name
            embedding_model: Embedding model name
            collection_name: Firestore collection name for metadata storage
            client: Vertex AI client (optional, will create one if not provided)
            firestore_client: Firestore client (optional, will create one if not provided)
        """
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        self.project_id = project_id
        self.location = location
        self.index_name = index_name
        self.embedding_model = embedding_model
        self.collection_name = collection_name

        # Initialize clients
        self.vertex_client = client or aiplatform.MatchingEngineIndexEndpoint()
        self.firestore_client = firestore_client or firestore.Client(project=project_id)
        self.collection = self.firestore_client.collection(collection_name)

        # Initialize embedding model
        self.model = aiplatform.TextEmbeddingModel.from_pretrained(embedding_model)

        logger.info(
            f"VertexMemory initialized with project={project_id}, location={location}"
        )

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Vertex AI.

        Args:
            text: Text to generate embedding for

        Returns:
            Embedding vector
        """
        try:
            # Generate embedding
            embeddings = self.model.get_embeddings([text])

            # Return the first embedding
            if embeddings and len(embeddings) > 0:
                return embeddings[0].values

            logger.warning(f"Failed to generate embedding for text: {text[:100]}...")
            return []
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []

    async def store(
        self, key: str, value: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Store an item in Vertex AI.

        Args:
            key: The key to store the value under
            value: The value to store
            ttl: Time-to-live in seconds (optional, not used for Vertex AI)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a copy of the value
            document = value.copy()

            # Add metadata
            document["created_at"] = firestore.SERVER_TIMESTAMP

            # Add TTL if provided
            if ttl is not None:
                # Calculate expiration time as a timestamp
                expires_at = int(time.time()) + ttl
                document["expires_at"] = expires_at

            # Extract text for embedding
            text = ""
            if "content" in document and isinstance(document["content"], str):
                text = document["content"]
            elif "text" in document and isinstance(document["text"], str):
                text = document["text"]
            else:
                # Convert the entire document to a string
                text = json.dumps(document)

            # Generate embedding
            embedding = await self._generate_embedding(text)

            if not embedding:
                logger.error(f"Failed to generate embedding for key {key}")
                return False

            # Store embedding in document
            document["embedding"] = embedding

            # Store in Firestore
            self.collection.document(key).set(document)

            # In a production implementation, you would also store the vector
            # in Vertex AI Vector Search using the Matching Engine API

            logger.debug(f"Stored item with key {key} in Vertex AI")
            return True
        except Exception as e:
            logger.error(f"Error storing item in Vertex AI: {e}")
            return False

    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from Vertex AI.

        Args:
            key: The key to retrieve

        Returns:
            The stored value, or None if not found
        """
        try:
            # Retrieve from Firestore
            doc = self.collection.document(key).get()
            if not doc.exists:
                logger.debug(f"No item found with key {key} in Vertex AI")
                return None

            data = doc.to_dict()

            # Check if the item has expired
            if "expires_at" in data:
                current_time = int(time.time())
                if data["expires_at"] < current_time:
                    logger.debug(f"Item with key {key} has expired in Vertex AI")
                    # Delete the expired item
                    await self.delete(key)
                    return None

            logger.debug(f"Retrieved item with key {key} from Vertex AI")
            return data
        except Exception as e:
            logger.error(f"Error retrieving item from Vertex AI: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete an item from Vertex AI.

        Args:
            key: The key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete from Firestore
            self.collection.document(key).delete()

            # In a production implementation, you would also delete
            # the vector from Vertex AI Vector Search

            logger.debug(f"Deleted item with key {key} from Vertex AI")
            return True
        except Exception as e:
            logger.error(f"Error deleting item from Vertex AI: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if an item exists in Vertex AI.

        Args:
            key: The key to check

        Returns:
            True if the item exists, False otherwise
        """
        try:
            # Check in Firestore
            doc = self.collection.document(key).get()
            exists = doc.exists

            # Check if the item has expired
            if exists and "expires_at" in doc.to_dict():
                current_time = int(time.time())
                if doc.to_dict()["expires_at"] < current_time:
                    logger.debug(f"Item with key {key} has expired in Vertex AI")
                    # Delete the expired item
                    await self.delete(key)
                    return False

            return exists
        except Exception as e:
            logger.error(f"Error checking if item exists in Vertex AI: {e}")
            return False

    async def search(
        self, field: str, value: Any, operator: str = "==", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for items in Vertex AI.

        Args:
            field: The field to search on
            value: The value to search for
            operator: The comparison operator to use
            limit: Maximum number of results to return

        Returns:
            List of matching items
        """
        try:
            # If field is "semantic" or "vector", perform semantic search
            if field in ["semantic", "vector", "embedding"] and isinstance(value, str):
                return await self._semantic_search(value, limit)

            # Otherwise, perform regular Firestore search
            query = self.collection

            # Apply field filter
            if operator == "==":
                query = query.where(field, "==", value)
            elif operator == "!=":
                query = query.where(field, "!=", value)
            elif operator == ">":
                query = query.where(field, ">", value)
            elif operator == ">=":
                query = query.where(field, ">=", value)
            elif operator == "<":
                query = query.where(field, "<", value)
            elif operator == "<=":
                query = query.where(field, "<=", value)
            elif operator == "array-contains":
                query = query.where(field, "array_contains", value)
            elif operator == "in":
                query = query.where(field, "in", value)
            elif operator == "array-contains-any":
                query = query.where(field, "array_contains_any", value)

            # Apply limit
            query = query.limit(limit)

            # Execute the query
            docs = query.stream()

            # Process results
            results = []
            current_time = int(time.time())

            for doc in docs:
                data = doc.to_dict()

                # Check if the item has expired
                if "expires_at" in data and data["expires_at"] < current_time:
                    # Skip expired items
                    continue

                # Add the document ID as a field
                data["id"] = doc.id
                results.append(data)

            logger.debug(
                f"Found {len(results)} items matching {field} {operator} {value} in Vertex AI"
            )
            return results
        except Exception as e:
            logger.error(f"Error searching in Vertex AI: {e}")
            return []

    async def _semantic_search(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using Vertex AI Vector Search.

        Args:
            query: The query text
            limit: Maximum number of results to return

        Returns:
            List of matching items
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)

            if not query_embedding:
                logger.error(f"Failed to generate embedding for query: {query}")
                return []

            # In a production implementation, you would use the
            # Vertex AI Matching Engine API to search for similar vectors
            # For now, we'll simulate this with a Firestore query

            # Get all documents (limited)
            docs = self.collection.limit(limit * 5).stream()

            # Process results
            results = []
            current_time = int(time.time())

            for doc in docs:
                data = doc.to_dict()

                # Check if the item has expired
                if "expires_at" in data and data["expires_at"] < current_time:
                    # Skip expired items
                    continue

                # Skip items without embeddings
                if "embedding" not in data:
                    continue

                # Calculate cosine similarity (simplified)
                # In a real implementation, this would be done by Vertex AI
                similarity = 0.7  # Placeholder similarity score

                # Add the document ID and similarity score
                data["id"] = doc.id
                data["similarity"] = similarity
                results.append(data)

            # Sort by similarity (descending)
            results.sort(key=lambda x: x["similarity"], reverse=True)

            # Limit results
            results = results[:limit]

            logger.debug(
                f"Found {len(results)} items semantically matching query: {query}"
            )
            return results
        except Exception as e:
            logger.error(f"Error performing semantic search in Vertex AI: {e}")
            return []

    async def update(self, key: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item in Vertex AI.

        Args:
            key: The key of the item to update
            updates: The fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add update timestamp
            updates["updated_at"] = firestore.SERVER_TIMESTAMP

            # Check if content is being updated
            content_updated = "content" in updates or "text" in updates

            if content_updated:
                # If content is updated, we need to regenerate the embedding
                # Retrieve the current document
                doc = self.collection.document(key).get()
                if not doc.exists:
                    logger.debug(f"No item found with key {key} in Vertex AI")
                    return False

                # Get the current data
                data = doc.to_dict()

                # Update the data
                data.update(updates)

                # Extract text for embedding
                text = ""
                if "content" in data and isinstance(data["content"], str):
                    text = data["content"]
                elif "text" in data and isinstance(data["text"], str):
                    text = data["text"]
                else:
                    # Convert the entire document to a string
                    text = json.dumps(data)

                # Generate new embedding
                embedding = await self._generate_embedding(text)

                if not embedding:
                    logger.error(f"Failed to generate embedding for key {key}")
                    return False

                # Add embedding to updates
                updates["embedding"] = embedding

            # Update in Firestore
            self.collection.document(key).update(updates)

            # In a production implementation, you would also update
            # the vector in Vertex AI Vector Search

            logger.debug(f"Updated item with key {key} in Vertex AI")
            return True
        except Exception as e:
            logger.error(f"Error updating item in Vertex AI: {e}")
            return False

    async def clear_all(self) -> bool:
        """
        Clear all items from Vertex AI.

        Returns:
            True if successful, False otherwise
        """
        try:
            batch_size = 500
            docs = self.collection.limit(batch_size).stream()
            deleted = 0

            # Delete in batches
            for doc in docs:
                doc.reference.delete()
                deleted += 1

            if deleted >= batch_size:
                # If we deleted a full batch, there might be more
                return await self.clear_all()

            # In a production implementation, you would also clear
            # the vectors from Vertex AI Vector Search

            logger.debug(f"Cleared {deleted} items from Vertex AI")
            return True
        except Exception as e:
            logger.error(f"Error clearing items from Vertex AI: {e}")
            return False
