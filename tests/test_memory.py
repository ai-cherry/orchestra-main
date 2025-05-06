"""
Unit tests for memory management components.

This module contains tests for the memory manager implementations,
ensuring that they correctly store and retrieve memory items.
"""

import unittest
import uuid
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.memory.stubs import PatrickMemoryManager


class TestPatrickMemoryManager(unittest.TestCase):
    """Test cases for the PatrickMemoryManager implementation."""
    
    def setUp(self):
        """Set up a fresh memory manager for each test."""
        self.memory_manager = PatrickMemoryManager()
        self.memory_manager.initialize()
    
    def tearDown(self):
        """Clean up resources after each test."""
        self.memory_manager.close()
    
    def test_initialization(self):
        """Test that the memory manager initializes correctly."""
        # The memory manager should be initialized in setUp
        self.assertTrue(self.memory_manager._is_initialized)
        self.assertEqual(len(self.memory_manager._items), 0)
        self.assertEqual(len(self.memory_manager._agent_data), 0)
        self.assertEqual(self.memory_manager._patrick_user_id, "patrick")
    
    def test_add_memory_item(self):
        """Test adding a memory item."""
        # Create a test item
        test_item = MemoryItem(
            user_id="some_other_user",  # Should be overridden to "patrick"
            item_type="message",
            text_content="Hello, world!"
        )
        
        # Add the item
        item_id = self.memory_manager.add_memory_item(test_item)
        
        # Verify the item was added
        self.assertEqual(len(self.memory_manager._items), 1)
        
        # Verify the item has the expected properties
        stored_item = self.memory_manager._items[0]
        self.assertEqual(stored_item.id, item_id)
        self.assertEqual(stored_item.user_id, "patrick")  # Should be overridden
        self.assertEqual(stored_item.item_type, "message")
        self.assertEqual(stored_item.text_content, "Hello, world!")
    
    def test_add_memory_item_with_id(self):
        """Test adding a memory item with a predefined ID."""
        # Create a test item with an ID
        predefined_id = "test_id_123"
        test_item = MemoryItem(
            id=predefined_id,
            user_id="some_other_user",  # Should be overridden to "patrick"
            item_type="message",
            text_content="Item with predefined ID"
        )
        
        # Add the item
        item_id = self.memory_manager.add_memory_item(test_item)
        
        # Verify the item was added with the correct ID
        self.assertEqual(item_id, predefined_id)
        self.assertEqual(self.memory_manager._items[0].id, predefined_id)
        self.assertEqual(self.memory_manager._items[0].user_id, "patrick")  # Should be overridden
    
    def test_get_memory_item(self):
        """Test retrieving a memory item by ID."""
        # Add a test item
        test_item = MemoryItem(
            user_id="patrick",
            item_type="message",
            text_content="Item to retrieve"
        )
        item_id = self.memory_manager.add_memory_item(test_item)
        
        # Retrieve the item
        retrieved_item = self.memory_manager.get_memory_item(item_id)
        
        # Verify the item was retrieved correctly
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.id, item_id)
        self.assertEqual(retrieved_item.text_content, "Item to retrieve")
    
    def test_get_nonexistent_memory_item(self):
        """Test retrieving a memory item that doesn't exist."""
        # Retrieve a nonexistent item
        retrieved_item = self.memory_manager.get_memory_item("nonexistent_id")
        
        # Verify the item was not found
        self.assertIsNone(retrieved_item)
    
    def test_get_conversation_history(self):
        """Test retrieving conversation history."""
        # Add several test items
        for i in range(5):
            test_item = MemoryItem(
                user_id="patrick",
                item_type="message",
                text_content=f"Message {i}",
                timestamp=datetime.utcnow() - timedelta(minutes=i)  # Older as i increases
            )
            self.memory_manager.add_memory_item(test_item)
        
        # Retrieve conversation history
        history = self.memory_manager.get_conversation_history()
        
        # Verify the correct number of items were retrieved
        self.assertEqual(len(history), 5)
        
        # Verify the items are in the correct order (newest first)
        for i in range(4):
            self.assertTrue(history[i].timestamp >= history[i+1].timestamp)
        
        # Verify the content of the items
        self.assertEqual(history[0].text_content, "Message 0")  # Newest
        self.assertEqual(history[4].text_content, "Message 4")  # Oldest
    
    def test_get_conversation_history_with_limit(self):
        """Test retrieving conversation history with a limit."""
        # Add several test items
        for i in range(10):
            test_item = MemoryItem(
                user_id="patrick",
                item_type="message",
                text_content=f"Message {i}",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            self.memory_manager.add_memory_item(test_item)
        
        # Retrieve conversation history with a limit
        history = self.memory_manager.get_conversation_history(limit=3)
        
        # Verify the correct number of items were retrieved
        self.assertEqual(len(history), 3)
        
        # Verify the items are the newest ones
        self.assertEqual(history[0].text_content, "Message 0")
        self.assertEqual(history[2].text_content, "Message 2")
    
    def test_get_conversation_history_with_session(self):
        """Test retrieving conversation history filtered by session."""
        # Add items with different session IDs
        session_1 = "session_1"
        session_2 = "session_2"
        
        for i in range(3):
            test_item = MemoryItem(
                user_id="patrick",
                session_id=session_1,
                item_type="message",
                text_content=f"Session 1 - Message {i}"
            )
            self.memory_manager.add_memory_item(test_item)
        
        for i in range(2):
            test_item = MemoryItem(
                user_id="patrick",
                session_id=session_2,
                item_type="message",
                text_content=f"Session 2 - Message {i}"
            )
            self.memory_manager.add_memory_item(test_item)
        
        # Retrieve conversation history for session 1
        history_1 = self.memory_manager.get_conversation_history(session_id=session_1)
        
        # Verify the correct items were retrieved
        self.assertEqual(len(history_1), 3)
        for item in history_1:
            self.assertEqual(item.session_id, session_1)
            self.assertTrue(item.text_content.startswith("Session 1"))
        
        # Retrieve conversation history for session 2
        history_2 = self.memory_manager.get_conversation_history(session_id=session_2)
        
        # Verify the correct items were retrieved
        self.assertEqual(len(history_2), 2)
        for item in history_2:
            self.assertEqual(item.session_id, session_2)
            self.assertTrue(item.text_content.startswith("Session 2"))
    
    def test_get_conversation_history_with_persona(self):
        """Test retrieving conversation history filtered by persona."""
        # Add items with different personas
        for i in range(2):
            test_item = MemoryItem(
                user_id="patrick",
                persona_active="cherry",
                item_type="message",
                text_content=f"Cherry - Message {i}"
            )
            self.memory_manager.add_memory_item(test_item)
        
        for i in range(3):
            test_item = MemoryItem(
                user_id="patrick",
                persona_active="sophia",
                item_type="message",
                text_content=f"Sophia - Message {i}"
            )
            self.memory_manager.add_memory_item(test_item)
        
        # Retrieve conversation history filtered by persona
        history = self.memory_manager.get_conversation_history(
            filters={"persona_active": "sophia"}
        )
        
        # Verify the correct items were retrieved
        self.assertEqual(len(history), 3)
        for item in history:
            self.assertEqual(item.persona_active, "sophia")
            self.assertTrue(item.text_content.startswith("Sophia"))
    
    def test_semantic_search_persona_filter(self):
        """Test the simplified semantic search with persona filtering."""
        # Add items with different personas
        for i in range(3):
            test_item = MemoryItem(
                user_id="patrick",
                persona_active="cherry",
                item_type="message",
                text_content=f"Cherry - Message {i}",
                timestamp=datetime.utcnow() - timedelta(minutes=i)
            )
            self.memory_manager.add_memory_item(test_item)
        
        for i in range(2):
            test_item = MemoryItem(
                user_id="patrick",
                persona_active="sophia",
                item_type="message",
                text_content=f"Sophia - Message {i}",
                timestamp=datetime.utcnow() - timedelta(minutes=i+10)  # Older
            )
            self.memory_manager.add_memory_item(test_item)
        
        # Create a persona config
        persona = PersonaConfig(
            name="cherry",
            description="Cherry persona"
        )
        
        # Perform semantic search with persona filter
        results = self.memory_manager.semantic_search(
            persona_context=persona
        )
        
        # Verify the correct items were retrieved
        self.assertEqual(len(results), 3)
        for item in results:
            self.assertEqual(item.persona_active, "cherry")
            self.assertTrue(item.text_content.startswith("Cherry"))
        
        # Verify they are in the correct order (newest first)
        self.assertEqual(results[0].text_content, "Cherry - Message 0")
        self.assertEqual(results[2].text_content, "Cherry - Message 2")
    
    def test_add_raw_agent_data(self):
        """Test adding raw agent data."""
        # Create test agent data
        test_data = AgentData(
            agent_id="test_agent",
            data_type="log",
            content="Test log message"
        )
        
        # Add the data
        data_id = self.memory_manager.add_raw_agent_data(test_data)
        
        # Verify the data was added
        self.assertEqual(len(self.memory_manager._agent_data), 1)
        
        # Verify the data has the expected properties
        stored_data = self.memory_manager._agent_data[0]
        self.assertEqual(stored_data.id, data_id)
        self.assertEqual(stored_data.agent_id, "test_agent")
        self.assertEqual(stored_data.data_type, "log")
        self.assertEqual(stored_data.content, "Test log message")
    
    def test_cleanup_expired_items(self):
        """Test cleaning up expired items."""
        # Add some items, some of which are expired
        now = datetime.utcnow()
        
        # Expired items
        for i in range(3):
            expired_item = MemoryItem(
                user_id="patrick",
                item_type="message",
                text_content=f"Expired message {i}",
                expiration=now - timedelta(hours=1)  # 1 hour in the past
            )
            self.memory_manager.add_memory_item(expired_item)
        
        # Non-expired items
        for i in range(2):
            valid_item = MemoryItem(
                user_id="patrick",
                item_type="message",
                text_content=f"Valid message {i}",
                expiration=now + timedelta(hours=1)  # 1 hour in the future
            )
            self.memory_manager.add_memory_item(valid_item)
        
        # Items with no expiration
        for i in range(2):
            no_exp_item = MemoryItem(
                user_id="patrick",
                item_type="message",
                text_content=f"No expiration message {i}"
                # No expiration date
            )
            self.memory_manager.add_memory_item(no_exp_item)
        
        # Verify total item count before cleanup
        self.assertEqual(len(self.memory_manager._items), 7)
        
        # Clean up expired items
        removed_count = self.memory_manager.cleanup_expired_items()
        
        # Verify the correct number of items were removed
        self.assertEqual(removed_count, 3)
        
        # Verify remaining items
        self.assertEqual(len(self.memory_manager._items), 4)
        
        # Verify no expired items remain
        for item in self.memory_manager._items:
            self.assertTrue(
                item.expiration is None or item.expiration > now
            )


if __name__ == "__main__":
    unittest.main()
