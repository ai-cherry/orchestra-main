#!/usr/bin/env python3
"""
Test script for the optimized memory components with bridge adapter.

This script tests the basic functionality of the optimized memory storage
with the bridge adapter and the performance memory manager working together.
"""

from mcp_server.utils.performance_monitor import get_performance_monitor
from mcp_server.managers.performance_memory_manager import PerformanceMemoryManager
from mcp_server.storage.memory_adapter import StorageBridgeAdapter
from mcp_server.storage.optimized_memory_storage import OptimizedMemoryStorage
import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("memory-test")

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_memory_components():
    """Test the basic functionality of memory components."""
    logger.info("Starting memory components test with bridge adapter...")

    # Initialize performance monitor
    perf = get_performance_monitor()

    # Create memory storage configuration
    storage_config = {
        "max_keys_per_scope": 1000,
        "enable_search_index": True,
        "persistence_path": "./test_memory_data.json",
        "persist_on_change": True,
        "auto_load": True
    }

    # Create optimized memory storage
    logger.info("Creating optimized memory storage...")
    optimized_storage = OptimizedMemoryStorage(storage_config)

    # Create bridge adapter
    logger.info("Creating storage bridge adapter...")
    storage_adapter = StorageBridgeAdapter(optimized_storage)

    # Create performance memory manager
    logger.info("Creating performance memory manager...")
    memory_manager = PerformanceMemoryManager(
        config=storage_config,
        storage=storage_adapter,
        performance_monitor=perf
    )

    # Initialize memory manager
    logger.info("Initializing memory manager...")
    init_result = await memory_manager.initialize()
    logger.info(f"Initialization result: {init_result}")

    # Test storing data
    logger.info("Testing data storage...")
    store_data = {
        "test_value": "This is a test value",
        "timestamp": time.time(),
        "metadata": {
            "source": "test_script",
            "version": "1.0"
        }
    }

    store_result = await memory_manager.store(
        key="test_key",
        content=store_data,
        tool_name="memory_test",
        ttl_seconds=3600
    )
    logger.info(f"Store result: {store_result}")

    # Test retrieving data
    logger.info("Testing data retrieval...")
    retrieve_result = await memory_manager.retrieve(key="test_key")
    logger.info(f"Retrieve result type: {type(retrieve_result)}")
    logger.info(
        f"Retrieve result: {json.dumps(retrieve_result, indent=2) if retrieve_result else None}")

    # Test search functionality
    logger.info("Testing search functionality...")
    search_result = await memory_manager.search(query="test_value")
    logger.info(f"Search results: {len(search_result)} items found")
    for item in search_result:
        logger.info(
            f"  - {item.get('key', 'unknown')}: {json.dumps(item.get('content', {}), indent=2)}")

    # Test health check
    logger.info("Testing health check...")
    health = await memory_manager.health_check()
    logger.info(f"Health check result: {json.dumps(health, indent=2)}")

    # Test deleting data
    logger.info("Testing data deletion...")
    delete_result = await memory_manager.delete(key="test_key")
    logger.info(f"Delete result: {delete_result}")

    # Verify deletion
    logger.info("Verifying deletion...")
    verify_result = await memory_manager.retrieve(key="test_key")
    logger.info(f"Retrieve after delete: {verify_result}")

    logger.info("Memory components test with bridge adapter complete.")
    return True

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_memory_components())
