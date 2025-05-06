#!/usr/bin/env python3
"""
Validation script that tests only the InMemoryMemoryManager implementation.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memory-validation")

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))


async def test_memory_adapter():
    """Test the memory manager implementations."""
    try:
        # Import the necessary modules
        from packages.shared.src.memory.memory_manager import InMemoryMemoryManager
        from packages.shared.src.models.base_models import MemoryItem

        # Create a test namespace
        namespace = f"memory-validation-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Use in-memory manager for validation
        logger.info("Testing with InMemoryMemoryManager")
        adapter = InMemoryMemoryManager(namespace=namespace)

        # Test initialization
        logger.info("Initializing memory manager...")
        await adapter.initialize()
        logger.info("Initialization successful!")

        # Test health check
        logger.info("Performing health check...")
        health = await adapter.health_check()
        logger.info(f"Health check status: {health['status']}")

        # Create test memory item
        test_item = MemoryItem(
            user_id="test_user",
            session_id="test_session",
            item_type="message",
            persona_active="test_persona",
            text_content="This is a test message from the validation script",
            timestamp=datetime.utcnow(),
            metadata={
                "source": "validation_script",
                "test": True
            }
        )

        # Test adding a memory item
        logger.info("Adding test memory item...")
        item_id = await adapter.add_memory_item(test_item)
        logger.info(f"Added memory item with ID: {item_id}")

        # Test retrieving conversation history
        logger.info("Retrieving conversation history...")
        history = await adapter.get_conversation_history(
            user_id="test_user",
            limit=10
        )
        logger.info(f"Retrieved {len(history)} memory items")

        # Verify the test item was retrieved
        for item in history:
            if item.text_content == "This is a test message from the validation script":
                logger.info("Successfully retrieved test memory item!")
                logger.info(f"Item metadata: {item.metadata}")
                break
        else:
            logger.error("Failed to retrieve test memory item!")

        # Close the adapter
        logger.info("Closing memory manager...")
        await adapter.close()
        logger.info("Memory manager closed successfully")

        # Summary
        logger.info("Memory system validation PASSED!")
        return True

    except Exception as e:
        logger.error(f"Memory system validation FAILED: {e}", exc_info=True)
        return False


async def main():
    """Main entry point."""
    # Run the test
    logger.info("Starting memory system validation...")
    success = await test_memory_adapter()

    if success:
        logger.info("All memory system tests PASSED!")
        return 0
    else:
        logger.error("Memory system tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
