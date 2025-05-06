"""
Unit tests for the new FirestoreMemoryManagerV2 implementation.

This module contains tests for the new Firestore memory manager implementation,
verifying that it correctly handles storage and retrieval operations.
"""

import asyncio
import os
import unittest
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.storage.firestore.v2 import FirestoreMemoryManagerV2

# Check if GCP credentials are available for testing
HAS_GCP_CREDENTIALS = (os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None or
                       os.environ.get("GOOGLE_CLOUD_PROJECT") is not None)


class TestFirestoreMemoryManagerV2(unittest.TestCase):
    """Test cases for the FirestoreMemoryManagerV2 implementation."""

    def setUp(self):
        """Set up test resources."""
        # Only initialize the Firestore memory manager if credentials are available
        if not HAS_GCP_CREDENTIALS:
            self.skipTest("Skipping Firestore tests: GCP credentials not available")
            
        self.memory_manager = FirestoreMemoryManagerV2(
            namespace="test_namespace"
        )
        
        # Create a clean event loop for each test
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Initialize the memory manager
        self.loop.run_until_complete(self.memory_manager.initialize())
        
        # Create test user ID
        self.test_user_id = f"test_user_{datetime.utcnow().timestamp()}"
        
    def tearDown(self):
        """Clean up test resources."""
        if hasattr(self, 'memory_manager') and self.memory_manager._is_initialized:
            # Close the memory manager
            self.loop.run_until_complete(self.memory_manager.close())
            
        # Close the event loop
        self.loop.close()
        
    def test_add_and_retrieve_memory_item(self):
        """Test adding and retrieving a memory item."""
        if not HAS_GCP_CREDENTIALS:
            self.skipTest("Skipping Firestore tests: GCP credentials not available")
            
        # Create a test item
        test_item = MemoryItem(
            user_id=self.test_user_id,
            item_type="message",
            text_content="Test message content"
        )
        
        # Add the item
        item_id = self.loop.run_until_complete(self.memory_manager.add_memory_item(test_item))
        self.assertIsNotNone(item_id)
        
        # Retrieve the item
        retrieved_item = self.loop.run_until_complete(self.memory_manager.get_memory_item(item_id))
        
        # Verify the item was retrieved correctly
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, item_id)
        self.assertEqual(retrieved_item.user_id, self.test_user_id)
        self.assertEqual(retrieved_item.text_content, "Test message content")
        
    def test_health_check(self):
        """Test the health check functionality."""
        if not HAS_GCP_CREDENTIALS:
            self.skipTest("Skipping Firestore tests: GCP credentials not available")
            
        # Check health
        health = self.loop.run_until_complete(self.memory_manager.health_check())
        
        # Verify health information
        self.assertEqual(health["status"], "healthy")
        self.assertTrue(health["firestore"])
        self.assertFalse(health["redis"])  # This implementation doesn't use Redis
        
    def test_get_conversation_history(self):
        """Test retrieving conversation history."""
        if not HAS_GCP_CREDENTIALS:
            self.skipTest("Skipping Firestore tests: GCP credentials not available")
            
        # Create and add a few items
        items = []
        for i in range(3):
            item = MemoryItem(
                user_id=self.test_user_id,
                item_type="conversation",
                text_content=f"Message {i}"
            )
            item_id = self.loop.run_until_complete(self.memory_manager.add_memory_item(item))
            items.append(item_id)
            
        # Retrieve conversation history
        history = self.loop.run_until_complete(
            self.memory_manager.get_conversation_history(self.test_user_id)
        )
        
        # Verify items were retrieved
        self.assertEqual(len(history), 3)
        
        # Clean up test items
        # Note: In a real test suite, this would be handled by a cleanup fixture
        for item_id in items:
            self.loop.run_until_complete(
                self.memory_manager.firestore.delete_document(
                    self.memory_manager.firestore.config.get_collection_name("memory_items"),
                    item_id
                )
            )


if __name__ == "__main__":
    unittest.main()
