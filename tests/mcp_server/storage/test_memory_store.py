#!/usr/bin/env python3
"""
Tests for the MemoryStore class.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from mcp_server.storage.memory_store import MemoryStore

class TestMemoryStore(unittest.TestCase):
    """Test cases for the MemoryStore class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = {
            "storage_path": self.temp_dir.name,
            "ttl_seconds": 3600,
            "max_items_per_key": 100,
            "enable_compression": True,
        }
        self.memory_store = MemoryStore(self.config)
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_set_and_get(self):
        """Test setting and getting a memory item."""
        # Set a memory item
        key = "test_key"
        content = {"test": "value"}
        result = self.memory_store.set(key, content)
        self.assertTrue(result)
        
        # Get the memory item
        retrieved = self.memory_store.get(key)
        self.assertEqual(retrieved, content)
        
        # Check that the file was created
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        self.assertTrue(memory_file.exists())
        
        # Check file content
        with open(memory_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data["content"], content)
    
    def test_get_with_scope_and_tool(self):
        """Test getting a memory item with scope and tool."""
        # Set a memory item with scope and tool
        key = "test_key"
        content = {"test": "value"}
        scope = "global"
        tool = "roo"
        result = self.memory_store.set(key, content, scope, tool)
        self.assertTrue(result)
        
        # Get the memory item with scope and tool
        retrieved = self.memory_store.get(key, scope, tool)
        self.assertEqual(retrieved, content)
        
        # Check that the file was created with the correct name
        memory_file = Path(self.temp_dir.name) / f"{scope}:{tool}:{key}.json"
        self.assertTrue(memory_file.exists())
    
    def test_delete(self):
        """Test deleting a memory item."""
        # Set a memory item
        key = "test_key"
        content = {"test": "value"}
        self.memory_store.set(key, content)
        
        # Delete the memory item
        result = self.memory_store.delete(key)
        self.assertTrue(result)
        
        # Check that the item is gone
        retrieved = self.memory_store.get(key)
        self.assertIsNone(retrieved)
        
        # Check that the file was deleted
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        self.assertFalse(memory_file.exists())
    
    def test_sync(self):
        """Test syncing a memory item between tools."""
        # Set a memory item for source tool
        key = "test_key"
        content = {"test": "value"}
        source_tool = "roo"
        target_tool = "cline"
        self.memory_store.set(key, content, tool=source_tool)
        
        # Sync to target tool
        result = self.memory_store.sync(key, source_tool, target_tool)
        self.assertTrue(result)
        
        # Check that the item was synced
        retrieved = self.memory_store.get(key, tool=target_tool)
        self.assertEqual(retrieved, content)
        
        # Check that both files exist
        source_file = Path(self.temp_dir.name) / f"session:{source_tool}:{key}.json"
        target_file = Path(self.temp_dir.name) / f"session:{target_tool}:{key}.json"
        self.assertTrue(source_file.exists())
        self.assertTrue(target_file.exists())
    
    def test_ttl_expiration(self):
        """Test TTL expiration of memory items."""
        # Set a memory item with a short TTL
        key = "test_key"
        content = {"test": "value"}
        ttl = 1  # 1 second
        self.memory_store.set(key, content, ttl=ttl)
        
        # Wait for the item to expire
        import time
        time.sleep(2)
        
        # Try to get the expired item
        retrieved = self.memory_store.get(key)
        self.assertIsNone(retrieved)
        
        # Check that the file was deleted
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        self.assertFalse(memory_file.exists())
    
    def test_load_memory(self):
        """Test loading memory items from storage."""
        # Create a memory file directly
        key = "test_key"
        content = {"test": "value"}
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        
        # Calculate expiry time (1 hour from now)
        expiry_time = datetime.now() + timedelta(hours=1)
        
        # Create memory data
        memory_data = {
            "content": content,
            "scope": "session",
            "tool": None,
            "created": datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
        }
        
        # Write to file
        with open(memory_file, "w") as f:
            json.dump(memory_data, f)
        
        # Create a new memory store to load the file
        new_memory_store = MemoryStore(self.config)
        
        # Check that the item was loaded
        retrieved = new_memory_store.get(key)
        self.assertEqual(retrieved, content)
    
    def test_load_expired_memory(self):
        """Test loading expired memory items from storage."""
        # Create an expired memory file directly
        key = "test_key"
        content = {"test": "value"}
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        
        # Calculate expiry time (1 hour ago)
        expiry_time = datetime.now() - timedelta(hours=1)
        
        # Create memory data
        memory_data = {
            "content": content,
            "scope": "session",
            "tool": None,
            "created": datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
        }
        
        # Write to file
        with open(memory_file, "w") as f:
            json.dump(memory_data, f)
        
        # Create a new memory store to load the file
        new_memory_store = MemoryStore(self.config)
        
        # Check that the expired item was not loaded
        retrieved = new_memory_store.get(key)
        self.assertIsNone(retrieved)
        
        # Check that the file was deleted
        self.assertFalse(memory_file.exists())
    
    @patch("threading.Thread")
    def test_cleanup_thread(self, mock_thread):
        """Test that the cleanup thread is started."""
        # Create a memory store
        memory_store = MemoryStore(self.config)
        
        # Check that a thread was started
        mock_thread.assert_called_once()
        args, kwargs = mock_thread.call_args
        self.assertEqual(kwargs["daemon"], True)
        self.assertTrue(callable(kwargs["target"]))

if __name__ == "__main__":
    unittest.main()