#!/usr/bin/env python3
"""
Tests for the AsyncMemoryStore class.
"""

import os
import json
import tempfile
import unittest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_server.storage.async_memory_store import AsyncMemoryStore


class TestAsyncMemoryStore(unittest.IsolatedAsyncioTestCase):
    """Test cases for the AsyncMemoryStore class."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = {
            "storage_path": self.temp_dir.name,
            "ttl_seconds": 3600,
            "max_items_per_key": 100,
            "enable_compression": True,
        }
        self.memory_store = AsyncMemoryStore(self.config)
        
        # Wait for initialization to complete
        await asyncio.sleep(0.1)
    
    async def asyncTearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    async def test_set_and_get(self):
        """Test setting and getting a memory item."""
        # Set a memory item
        key = "test_key"
        content = {"test": "value"}
        result = await self.memory_store.set(key, content)
        self.assertTrue(result)
        
        # Get the memory item
        retrieved = await self.memory_store.get(key)
        self.assertEqual(retrieved, content)
        
        # Check that the file was created
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        self.assertTrue(memory_file.exists())
        
        # Check file content
        with open(memory_file, "r") as f:
            data = json.load(f)
            self.assertEqual(data["content"], content)
    
    async def test_get_with_scope_and_tool(self):
        """Test getting a memory item with scope and tool."""
        # Set a memory item with scope and tool
        key = "test_key"
        content = {"test": "value"}
        scope = "global"
        tool = "roo"
        result = await self.memory_store.set(key, content, scope, tool)
        self.assertTrue(result)
        
        # Get the memory item with scope and tool
        retrieved = await self.memory_store.get(key, scope, tool)
        self.assertEqual(retrieved, content)
        
        # Check that the file was created with the correct name
        memory_file = Path(self.temp_dir.name) / f"{scope}:{tool}:{key}.json"
        self.assertTrue(memory_file.exists())
    
    async def test_delete(self):
        """Test deleting a memory item."""
        # Set a memory item
        key = "test_key"
        content = {"test": "value"}
        await self.memory_store.set(key, content)
        
        # Delete the memory item
        result = await self.memory_store.delete(key)
        self.assertTrue(result)
        
        # Check that the item is gone
        retrieved = await self.memory_store.get(key)
        self.assertIsNone(retrieved)
        
        # Check that the file was deleted
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        self.assertFalse(memory_file.exists())
    
    async def test_sync(self):
        """Test syncing a memory item between tools."""
        # Set a memory item for source tool
        key = "test_key"
        content = {"test": "value"}
        source_tool = "roo"
        target_tool = "cline"
        await self.memory_store.set(key, content, tool=source_tool)
        
        # Sync to target tool
        result = await self.memory_store.sync(key, source_tool, target_tool)
        self.assertTrue(result)
        
        # Check that the item was synced
        retrieved = await self.memory_store.get(key, tool=target_tool)
        self.assertEqual(retrieved, content)
        
        # Check that both files exist
        source_file = Path(self.temp_dir.name) / f"session:{source_tool}:{key}.json"
        target_file = Path(self.temp_dir.name) / f"session:{target_tool}:{key}.json"
        self.assertTrue(source_file.exists())
        self.assertTrue(target_file.exists())
    
    async def test_ttl_expiration(self):
        """Test TTL expiration of memory items."""
        # Set a memory item with a short TTL
        key = "test_key"
        content = {"test": "value"}
        ttl = 1  # 1 second
        await self.memory_store.set(key, content, ttl=ttl)
        
        # Wait for the item to expire
        await asyncio.sleep(2)
        
        # Try to get the expired item
        retrieved = await self.memory_store.get(key)
        self.assertIsNone(retrieved)
        
        # Check that the file was deleted
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        self.assertFalse(memory_file.exists())
    
    async def test_load_memory(self):
        """Test loading memory items from storage."""
        # Create a memory file directly
        key = "test_key"
        content = {"test": "value"}
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        
        # Calculate expiry time (1 hour from now)
        import datetime
        expiry_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        # Create memory data
        memory_data = {
            "content": content,
            "scope": "session",
            "tool": None,
            "created": datetime.datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
        }
        
        # Write to file
        with open(memory_file, "w") as f:
            json.dump(memory_data, f)
        
        # Create a new memory store to load the file
        new_memory_store = AsyncMemoryStore(self.config)
        
        # Wait for initialization to complete
        await asyncio.sleep(0.1)
        
        # Check that the item was loaded
        retrieved = await new_memory_store.get(key)
        self.assertEqual(retrieved, content)
    
    async def test_load_expired_memory(self):
        """Test loading expired memory items from storage."""
        # Create an expired memory file directly
        key = "test_key"
        content = {"test": "value"}
        memory_file = Path(self.temp_dir.name) / f"session:{key}.json"
        
        # Calculate expiry time (1 hour ago)
        import datetime
        expiry_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        
        # Create memory data
        memory_data = {
            "content": content,
            "scope": "session",
            "tool": None,
            "created": datetime.datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
        }
        
        # Write to file
        with open(memory_file, "w") as f:
            json.dump(memory_data, f)
        
        # Create a new memory store to load the file
        new_memory_store = AsyncMemoryStore(self.config)
        
        # Wait for initialization to complete
        await asyncio.sleep(0.1)
        
        # Check that the expired item was not loaded
        retrieved = await new_memory_store.get(key)
        self.assertIsNone(retrieved)
        
        # Check that the file was deleted
        self.assertFalse(memory_file.exists())
    
    async def test_concurrent_operations(self):
        """Test concurrent operations on the memory store."""
        # Create a list of keys and values
        keys = [f"key_{i}" for i in range(10)]
        values = [{"value": i} for i in range(10)]
        
        # Set items concurrently
        tasks = [self.memory_store.set(key, value) for key, value in zip(keys, values)]
        results = await asyncio.gather(*tasks)
        
        # Check that all operations succeeded
        self.assertTrue(all(results))
        
        # Get items concurrently
        tasks = [self.memory_store.get(key) for key in keys]
        results = await asyncio.gather(*tasks)
        
        # Check that all items were retrieved correctly
        for i, result in enumerate(results):
            self.assertEqual(result, values[i])
        
        # Delete items concurrently
        tasks = [self.memory_store.delete(key) for key in keys]
        results = await asyncio.gather(*tasks)
        
        # Check that all operations succeeded
        self.assertTrue(all(results))
        
        # Check that all items were deleted
        tasks = [self.memory_store.get(key) for key in keys]
        results = await asyncio.gather(*tasks)
        
        # Check that all items are gone
        self.assertTrue(all(result is None for result in results))
    
    @patch("asyncio.to_thread")
    async def test_file_io_with_to_thread(self, mock_to_thread):
        """Test that file I/O operations use asyncio.to_thread."""
        # Mock the to_thread function to return a known value
        mock_to_thread.return_value = '{"content": {"test": "value"}, "expiry": "2099-01-01T00:00:00"}'
        
        # Get a memory item
        key = "test_key"
        await self.memory_store.get(key)
        
        # Check that to_thread was called
        mock_to_thread.assert_called()


if __name__ == "__main__":
    unittest.main()