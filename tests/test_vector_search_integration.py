"""
Tests for the vector search integration with FirestoreMemoryManagerV2.

This module tests the integration between FirestoreMemoryManagerV2 and
the vector search implementations, ensuring that:
1. The in-memory vector search implementation works correctly
2. Semantic search functionality works with the vector search implementation
3. Storing and retrieving embeddings works correctly
4. Fallback to Firestore search works when vector search is not available
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Optional, Tuple

import pytest

from packages.shared.src.models.base_models import MemoryItem, PersonaConfig
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
from packages.shared.src.storage.vector.base import AbstractVectorSearch
from packages.shared.src.storage.vector.in_memory_vector_search import InMemoryVectorSearch
from packages.shared.src.storage.vector.factory import VectorSearchFactory
from packages.shared.src.storage.vector.vertex_vector_search import VertexVectorSearchAdapter
from packages.shared.src.storage.exceptions import StorageError, ValidationError


class TestVectorSearchIntegration(unittest.TestCase):
    """Test the integration between FirestoreMemoryManagerV2 and vector search implementations."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock for AsyncFirestoreStorageManager
        self.mock_firestore = AsyncMock()
        self.mock_firestore.initialize_async = AsyncMock()
        self.mock_firestore.close_async = AsyncMock()
        self.mock_firestore.set_document = AsyncMock(return_value=True)
        self.mock_firestore.get_document = AsyncMock(return_value=None)
        self.mock_firestore.query_documents = AsyncMock(return_value=[])
        self.mock_firestore.delete_document = AsyncMock(return_value=True)
        self.mock_firestore.check_health = AsyncMock(return_value={"connection": True, "details": {}})
        self.mock_firestore.config = MagicMock()
        self.mock_firestore.config.get_collection_name = MagicMock(return_value="memory_items")

        # Create a patch for the AsyncFirestoreStorageManager
        self.firestore_patch = patch(
            "packages.shared.src.storage.firestore.v2.adapter.AsyncFirestoreStorageManager",
            return_value=self.mock_firestore
        )

        # Create a sample memory item for testing
        self.sample_memory_item = MemoryItem(
            user_id="test_user",
            text_content="This is a test memory item",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 153,  # 765-dimensional embedding
            metadata={"source": "test", "importance": "high"}
        )

        # Create a sample query embedding
        self.query_embedding = [0.2, 0.3, 0.4, 0.5, 0.6] * 153  # 765-dimensional embedding

    async def async_setup(self):
        """Async setup for tests."""
        # Start the patches
        self.firestore_mock = self.firestore_patch.start()

    async def async_teardown(self):
        """Async teardown for tests."""
        # Stop the patches
        self.firestore_patch.stop()

    def run_async(self, coro):
        """Helper method to run async tests."""
        return asyncio.run(coro)

    def test_setup(self):
        """Test that the setup works correctly."""
        self.run_async(self.async_setup())
        self.run_async(self.async_teardown())

    @pytest.mark.asyncio
    async def test_in_memory_vector_search_initialization(self):
        """Test that the in-memory vector search can be initialized."""
        # Set up
        await self.async_setup()

        # Create an in-memory vector search
        vector_search = InMemoryVectorSearch(dimensions=765)
        
        # Initialize the vector search
        await vector_search.initialize()
        
        # Verify it's initialized
        health = await vector_search.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertTrue(health["vector_search"])
        self.assertEqual(health["details"]["provider"], "in_memory_vector_search")
        self.assertEqual(health["details"]["dimensions"], 765)
        
        # Clean up
        await vector_search.close()
        await self.async_teardown()

    @pytest.mark.asyncio
    async def test_memory_manager_with_in_memory_vector_search(self):
        """Test that FirestoreMemoryManagerV2 can be initialized with in-memory vector search."""
        # Set up
        await self.async_setup()

        # Create a memory manager with in-memory vector search
        memory_manager = FirestoreMemoryManagerV2(
            project_id="test-project",
            namespace="test-namespace",
            vector_search_provider="in_memory"
        )
        
        # Initialize the memory manager
        await memory_manager.initialize()
        
        # Verify it's initialized
        self.assertTrue(memory_manager._is_initialized)
        
        # Clean up
        await memory_manager.close()
        await self.async_teardown()

    @pytest.mark.asyncio
    async def test_store_and_retrieve_embedding(self):
        """Test storing and retrieving embeddings with in-memory vector search."""
        # Set up
        await self.async_setup()

        # Create a mock for the vector search
        mock_vector_search = AsyncMock(spec=AbstractVectorSearch)
        mock_vector_search.initialize = AsyncMock()
        mock_vector_search.close = AsyncMock()
        mock_vector_search.store_embedding = AsyncMock()
        mock_vector_search.find_similar = AsyncMock(return_value=[("test_id", 0.95)])
        mock_vector_search.delete_embedding = AsyncMock(return_value=True)
        mock_vector_search.health_check = AsyncMock(return_value={"status": "healthy", "vector_search": True})

        # Patch the VectorSearchFactory to return our mock
        with patch.object(
            VectorSearchFactory, 
            "create_vector_search", 
            return_value=mock_vector_search
        ):
            # Create a memory manager with the mocked vector search
            memory_manager = FirestoreMemoryManagerV2(
                project_id="test-project",
                namespace="test-namespace",
                vector_search_provider="in_memory"
            )
            
            # Initialize the memory manager
            await memory_manager.initialize()
            
            # Mock the document returned by Firestore for the memory item
            memory_item_doc = {
                "id": "test_id",
                "user_id": "test_user",
                "text_content": "This is a test memory item",
                "embedding": self.sample_memory_item.embedding,
                "metadata": {"source": "test", "importance": "high"}
            }
            self.mock_firestore.get_document.return_value = memory_item_doc
            
            # Add a memory item with embedding
            item_id = await memory_manager.add_memory_item(self.sample_memory_item)
            
            # Verify the embedding was stored
            mock_vector_search.store_embedding.assert_called_once()
            
            # Clean up
            await memory_manager.close()
        
        await self.async_teardown()

    @pytest.mark.asyncio
    async def test_semantic_search_with_vector_search(self):
        """Test semantic search using vector search."""
        # Set up
        await self.async_setup()

        # Create a mock for the vector search
        mock_vector_search = AsyncMock(spec=AbstractVectorSearch)
        mock_vector_search.initialize = AsyncMock()
        mock_vector_search.close = AsyncMock()
        mock_vector_search.store_embedding = AsyncMock()
        mock_vector_search.find_similar = AsyncMock(return_value=[("test_id", 0.95)])
        mock_vector_search.delete_embedding = AsyncMock(return_value=True)
        mock_vector_search.health_check = AsyncMock(return_value={"status": "healthy", "vector_search": True})

        # Patch the VectorSearchFactory to return our mock
        with patch.object(
            VectorSearchFactory, 
            "create_vector_search", 
            return_value=mock_vector_search
        ):
            # Create a memory manager with the mocked vector search
            memory_manager = FirestoreMemoryManagerV2(
                project_id="test-project",
                namespace="test-namespace",
                vector_search_provider="in_memory"
            )
            
            # Initialize the memory manager
            await memory_manager.initialize()
            
            # Mock the document returned by Firestore for the memory item
            memory_item_doc = {
                "id": "test_id",
                "user_id": "test_user",
                "text_content": "This is a test memory item",
                "embedding": self.sample_memory_item.embedding,
                "metadata": {"source": "test", "importance": "high"}
            }
            self.mock_firestore.get_document.return_value = memory_item_doc
            
            # Set up the query_documents mock to return our test document
            self.mock_firestore.query_documents.return_value = [memory_item_doc]
            
            # Perform semantic search
            results = await memory_manager.semantic_search(
                user_id="test_user",
                query_embedding=self.query_embedding
            )
            
            # Verify vector search was used
            mock_vector_search.find_similar.assert_called_once()
            
            # Verify we got results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].text_content, "This is a test memory item")
            
            # Clean up
            await memory_manager.close()
        
        await self.async_teardown()

    @pytest.mark.asyncio
    async def test_fallback_to_firestore_search(self):
        """Test fallback to Firestore search when vector search is not available."""
        # Set up
        await self.async_setup()

        # Create a mock for the vector search that raises an exception
        mock_vector_search = AsyncMock(spec=AbstractVectorSearch)
        mock_vector_search.initialize = AsyncMock(side_effect=StorageError("Vector search unavailable"))
        mock_vector_search.close = AsyncMock()
        mock_vector_search.find_similar = AsyncMock(side_effect=StorageError("Vector search unavailable"))
        mock_vector_search.health_check = AsyncMock(return_value={"status": "error", "vector_search": False})

        # Patch the VectorSearchFactory to return our mock
        with patch.object(
            VectorSearchFactory, 
            "create_vector_search", 
            return_value=mock_vector_search
        ):
            # Create a memory manager with the mocked vector search
            memory_manager = FirestoreMemoryManagerV2(
                project_id="test-project",
                namespace="test-namespace",
                vector_search_provider="in_memory"
            )
            
            # Initialize the memory manager (should not fail even though vector search fails)
            await memory_manager.initialize()
            
            # Mock the document returned by Firestore for the memory item
            memory_item_doc = {
                "id": "test_id",
                "user_id": "test_user",
                "text_content": "This is a test memory item",
                "embedding": self.sample_memory_item.embedding,
                "metadata": {"source": "test", "importance": "high"}
            }
            
            # Set up the query_documents mock to return our test document
            self.mock_firestore.query_documents.return_value = [memory_item_doc]
            
            # Perform semantic search (should fall back to Firestore)
            results = await memory_manager.semantic_search(
                user_id="test_user",
                query_embedding=self.query_embedding
            )
            
            # Verify Firestore was queried
            self.mock_firestore.query_documents.assert_called_once()
            
            # Verify we got results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].text_content, "This is a test memory item")
            
            # Clean up
            await memory_manager.close()
        
        await self.async_teardown()

    @pytest.mark.asyncio
    async def test_vertex_vector_search_adapter_mocked(self):
        """Test the VertexVectorSearchAdapter with mocked Vertex AI."""
        # Set up
        await self.async_setup()

        # Mock the Vertex AI client
        with patch("google.cloud.aiplatform.init"), \
             patch("google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint.MatchingEngineIndexEndpoint") as mock_endpoint:
            
            # Set up the mock endpoint
            mock_endpoint_instance = MagicMock()
            mock_endpoint_instance.deployed_indexes = [
                MagicMock(index="test-index-id", id="deployed-index-id")
            ]
            mock_endpoint_instance.match.return_value = [
                [MagicMock(id="test_id", distance=0.05)]  # 0.05 distance = 0.95 similarity
            ]
            mock_endpoint.get.return_value = mock_endpoint_instance
            
            # Create a VertexVectorSearchAdapter
            vector_search = VertexVectorSearchAdapter(
                project_id="test-project",
                location="us-west4",
                index_endpoint_id="test-endpoint-id",
                index_id="test-index-id"
            )
            
            # Initialize the vector search
            await vector_search.initialize()
            
            # Test find_similar
            results = await vector_search.find_similar(
                query_embedding=self.query_embedding,
                top_k=5
            )
            
            # Verify results
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], "test_id")
            self.assertAlmostEqual(results[0][1], 0.95)  # 1.0 - 0.05 = 0.95
            
            # Clean up
            await vector_search.close()
        
        await self.async_teardown()

    @pytest.mark.asyncio
    async def test_memory_manager_with_vertex_vector_search(self):
        """Test FirestoreMemoryManagerV2 with Vertex Vector Search."""
        # Set up
        await self.async_setup()

        # Create a mock for the vector search
        mock_vector_search = AsyncMock(spec=AbstractVectorSearch)
        mock_vector_search.initialize = AsyncMock()
        mock_vector_search.close = AsyncMock()
        mock_vector_search.store_embedding = AsyncMock()
        mock_vector_search.find_similar = AsyncMock(return_value=[("test_id", 0.95)])
        mock_vector_search.delete_embedding = AsyncMock(return_value=True)
        mock_vector_search.health_check = AsyncMock(return_value={"status": "healthy", "vector_search": True})

        # Patch the VectorSearchFactory to return our mock
        with patch.object(
            VectorSearchFactory, 
            "create_vector_search", 
            return_value=mock_vector_search
        ):
            # Create a memory manager with the mocked vector search
            memory_manager = FirestoreMemoryManagerV2(
                project_id="test-project",
                namespace="test-namespace",
                vector_search_provider="vertex",
                vector_search_config={
                    "project_id": "test-project",
                    "location": "us-west4",
                    "index_endpoint_id": "test-endpoint-id",
                    "index_id": "test-index-id"
                }
            )
            
            # Initialize the memory manager
            await memory_manager.initialize()
            
            # Mock the document returned by Firestore for the memory item
            memory_item_doc = {
                "id": "test_id",
                "user_id": "test_user",
                "text_content": "This is a test memory item",
                "embedding": self.sample_memory_item.embedding,
                "metadata": {"source": "test", "importance": "high"}
            }
            self.mock_firestore.get_document.return_value = memory_item_doc
            
            # Add a memory item with embedding
            item_id = await memory_manager.add_memory_item(self.sample_memory_item)
            
            # Verify the embedding was stored
            mock_vector_search.store_embedding.assert_called_once()
            
            # Clean up
            await memory_manager.close()
        
        await self.async_teardown()


if __name__ == "__main__":
    unittest.main()