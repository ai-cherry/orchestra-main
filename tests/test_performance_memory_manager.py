"""
Integration tests for the PerformanceMemoryManager.

These tests verify that the memory manager works correctly with its storage backend.
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from mcp_server.managers.performance_memory_manager import PerformanceMemoryManager


@pytest.fixture
async def memory_manager():
    """Create and initialize a memory manager for testing."""
    manager = PerformanceMemoryManager({
        "max_cache_items": 100,
        "cache_ttl": 60
    })
    initialized = await manager.initialize()
    assert initialized, "Failed to initialize memory manager"
    yield manager


@pytest.mark.asyncio
async def test_store_and_retrieve(memory_manager: PerformanceMemoryManager):
    """Test storing and retrieving content."""
    # Test data
    key = "test_key"
    content = {"test": "data", "nested": {"value": 123}}
    tool_name = "test_tool"
    
    # Store content
    success = await memory_manager.store(key, content, tool_name)
    assert success, "Failed to store content"
    
    # Retrieve content
    retrieved = await memory_manager.retrieve(key)
    assert retrieved is not None, "Failed to retrieve content"
    assert retrieved == content, "Retrieved content does not match stored content"


@pytest.mark.asyncio
async def test_delete(memory_manager: PerformanceMemoryManager):
    """Test deleting content."""
    # Store content
    key = "delete_test_key"
    content = {"test": "delete_me"}
    await memory_manager.store(key, content, "test_tool")
    
    # Verify it exists
    retrieved = await memory_manager.retrieve(key)
    assert retrieved is not None, "Content should exist before deletion"
    
    # Delete content
    success = await memory_manager.delete(key)
    assert success, "Failed to delete content"
    
    # Verify it's gone
    retrieved = await memory_manager.retrieve(key)
    assert retrieved is None, "Content should not exist after deletion"


@pytest.mark.asyncio
async def test_search(memory_manager: PerformanceMemoryManager):
    """Test searching for content."""
    # Store multiple items
    await memory_manager.store("search_key1", {"content": "apple banana"}, "test_tool")
    await memory_manager.store("search_key2", {"content": "banana cherry"}, "test_tool")
    await memory_manager.store("search_key3", {"content": "cherry date"}, "test_tool")
    
    # Search for banana
    results = await memory_manager.search("banana")
    assert len(results) >= 2, "Search should find at least 2 results"
    
    # Search for cherry
    results = await memory_manager.search("cherry")
    assert len(results) >= 2, "Search should find at least 2 results"
    
    # Search for nonexistent term
    results = await memory_manager.search("nonexistent")
    assert len(results) == 0, "Search should find no results"


@pytest.mark.asyncio
async def test_cache_eviction(memory_manager: PerformanceMemoryManager):
    """Test that cache eviction works correctly."""
    # Override max cache items for testing
    memory_manager.max_cache_items = 5
    
    # Store more items than the cache can hold
    for i in range(10):
        key = f"cache_test_key_{i}"
        await memory_manager.store(key, {"value": i}, "test_tool")
    
    # Check cache size
    assert len(memory_manager.cache) <= memory_manager.max_cache_items, \
        "Cache should not exceed max size"


@pytest.mark.asyncio
async def test_cache_expiration(memory_manager: PerformanceMemoryManager):
    """Test that cache entries expire correctly."""
    # Override cache TTL for testing
    memory_manager.cache_ttl = 1  # 1 second
    
    # Store an item
    key = "expiration_test_key"
    await memory_manager.store(key, {"test": "expiration"}, "test_tool")
    
    # Verify it's in cache
    assert key in memory_manager.cache, "Item should be in cache"
    
    # Wait for expiration
    await asyncio.sleep(1.5)
    
    # Force cache cleanup
    await memory_manager._clean_cache_if_needed()
    
    # Verify it's removed from cache but still in storage
    assert key not in memory_manager.cache, "Item should be removed from cache"
    retrieved = await memory_manager.retrieve(key)
    assert retrieved is not None, "Item should still be in storage"


@pytest.mark.asyncio
async def test_health_check(memory_manager: PerformanceMemoryManager):
    """Test health check functionality."""
    health = await memory_manager.health_check()
    assert health["status"] in ["healthy", "degraded"], "Health status should be valid"
    assert "cache_items" in health, "Health should include cache items count"
    assert "storage" in health, "Health should include storage status"