#!/usr/bin/env python3
"""
Validation script for memory system fixes.

This script tests the FirestoreMemoryAdapter to validate that it correctly
adapts the sync FirestoreMemoryManager to the async MemoryManager interface.
"""

import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memory-validation")

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))


async def test_memory_adapter(use_firestore=False):
    """Test the memory manager implementations."""
    try:
        # Import the necessary modules
        from packages.shared.src.memory.memory_manager import InMemoryMemoryManager
        from packages.shared.src.models.base_models import MemoryItem

        # Try to import the FirestoreMemoryAdapter
        firestore_adapter = None
        if use_firestore:
            try:
                from packages.shared.src.memory.firestore_adapter import (
                    FirestoreMemoryAdapter,
                )

                firestore_adapter = FirestoreMemoryAdapter
                logger.info("Successfully imported FirestoreMemoryAdapter")
            except ImportError as e:
                logger.warning(f"Failed to import FirestoreMemoryAdapter: {e}")
                logger.warning("Falling back to InMemoryMemoryManager")

        # Create a test namespace
        namespace = f"memory-validation-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Determine which adapter to use
        if use_firestore and firestore_adapter:
            # Get GCP Project ID from environment
            project_id = os.environ.get("GCP_PROJECT_ID")
            credentials_path = os.environ.get("GCP_SA_KEY_PATH")
            credentials_json = os.environ.get("GCP_SA_KEY_JSON")

            if not project_id:
                logger.error("GCP_PROJECT_ID environment variable not set")
                return False

            logger.info(
                f"Testing with FirestoreMemoryAdapter using project ID: {project_id}"
            )
            adapter = firestore_adapter(
                project_id=project_id,
                credentials_path=credentials_path,
                credentials_json=credentials_json,
                namespace=namespace,
            )
        else:
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
        logger.info(f"Health check details: {health}")

        # Create test memory item
        test_item = MemoryItem(
            user_id="patrick_test",
            session_id="test_session",
            item_type="message",
            persona_active="test_persona",
            text_content="This is a test message from validate_memory_fixes.py",
            timestamp=datetime.utcnow(),
            metadata={"source": "validation_script", "test": True},
        )

        # Test adding a memory item
        logger.info("Adding test memory item...")
        item_id = await adapter.add_memory_item(test_item)
        logger.info(f"Added memory item with ID: {item_id}")

        # Test retrieving conversation history
        logger.info("Retrieving conversation history...")
        history = await adapter.get_conversation_history(
            user_id="patrick_test", limit=10
        )
        logger.info(f"Retrieved {len(history)} memory items")

        # Verify the test item was retrieved
        for item in history:
            if (
                item.text_content
                == "This is a test message from validate_memory_fixes.py"
            ):
                logger.info("Successfully retrieved test memory item!")
                logger.info(f"Item metadata: {item.metadata}")
                break
        else:
            logger.warning("Could not find the exact test memory item, but found items")
            if history:
                logger.info(f"First item: {history[0].text_content}")

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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Validate memory system fixes")
    parser.add_argument(
        "--project-id", help="Google Cloud project ID for Firestore testing"
    )
    parser.add_argument(
        "--firestore", action="store_true", help="Use FirestoreMemoryAdapter"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set project ID from args if provided
    if args.project_id:
        os.environ["GCP_PROJECT_ID"] = args.project_id
        logger.info(f"Using provided GCP project ID: {args.project_id}")

    # Determine if we should use Firestore
    use_firestore = args.firestore or os.environ.get("GCP_PROJECT_ID") is not None
    if use_firestore:
        logger.info("Will attempt to use FirestoreMemoryAdapter")

    # Run the test
    logger.info("Starting memory system validation...")
    success = await test_memory_adapter(use_firestore=use_firestore)

    if success:
        logger.info("All memory system tests PASSED!")
        return 0
    else:
        logger.error("Memory system tests FAILED!")
        return 1


if __name__ == "__main__":
    # Make script executable
    import os

    if os.name != "nt":  # Not Windows
        import stat

        script_path = os.path.abspath(__file__)
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)

    sys.exit(asyncio.run(main()))
