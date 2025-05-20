#!/usr/bin/env python3
"""
Example script demonstrating the new memory management components.

This script shows how to use the new memory management components, including
the configuration system, factory, and telemetry integration.
"""

import asyncio
import logging
import os
import sys
from typing import List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.shared.src.memory.config import (
    MemoryConfig,
    MemoryBackendType,
    FirestoreConfig,
    VectorSearchConfig,
    VectorSearchType,
    TelemetryConfig,
)
from packages.shared.src.memory.factory import MemoryManagerFactory
from packages.shared.src.memory.telemetry import (
    configure_telemetry,
    trace_operation,
    log_operation,
)
from packages.shared.src.models.base_models import MemoryItem


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memory_example")


@trace_operation("example_add_memory_items")
async def add_memory_items(memory_manager, items: List[MemoryItem]) -> List[str]:
    """
    Add memory items to the memory manager.

    Args:
        memory_manager: Memory manager instance
        items: List of memory items to add

    Returns:
        List of item IDs
    """
    item_ids = []
    for item in items:
        item_id = await memory_manager.add_memory_item(item)
        item_ids.append(item_id)
        log_operation(
            logging.INFO,
            f"Added memory item {item_id}",
            "add_memory_item",
            user_id=item.user_id,
            item_id=item_id,
        )
    return item_ids


@trace_operation("example_semantic_search")
async def perform_semantic_search(
    memory_manager, user_id: str, query_embedding: List[float], top_k: int = 5
) -> List[MemoryItem]:
    """
    Perform semantic search using the memory manager.

    Args:
        memory_manager: Memory manager instance
        user_id: User ID to search for
        query_embedding: Query embedding vector
        top_k: Maximum number of results to return

    Returns:
        List of memory items
    """
    results = await memory_manager.semantic_search(
        user_id=user_id, query_embedding=query_embedding, top_k=top_k
    )

    log_operation(
        logging.INFO,
        f"Performed semantic search for user {user_id}, found {len(results)} results",
        "semantic_search",
        user_id=user_id,
        result_count=len(results),
    )

    return results


async def example_with_config():
    """Example using explicit configuration."""
    logger.info("Starting example with explicit configuration")

    # Create configuration
    config = MemoryConfig(
        backend=MemoryBackendType.FIRESTORE,
        firestore=FirestoreConfig(namespace="example", connection_pool_size=5),
        vector_search=VectorSearchConfig(provider=VectorSearchType.IN_MEMORY),
        telemetry=TelemetryConfig(enabled=True, log_level="INFO"),
    )

    # Configure telemetry
    configure_telemetry(config.telemetry)

    # Create memory manager
    memory_manager = await MemoryManagerFactory.create_memory_manager(config)

    try:
        # Create sample memory items
        items = [
            MemoryItem(
                user_id="user123",
                text_content="This is a test memory item",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 153,  # 765-dimensional vector
            ),
            MemoryItem(
                user_id="user123",
                text_content="Another test memory item",
                embedding=[0.2, 0.3, 0.4, 0.5, 0.6] * 153,  # 765-dimensional vector
            ),
        ]

        # Add memory items
        item_ids = await add_memory_items(memory_manager, items)
        logger.info(f"Added {len(item_ids)} memory items: {item_ids}")

        # Perform semantic search
        query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55] * 153  # 765-dimensional vector
        results = await perform_semantic_search(
            memory_manager, user_id="user123", query_embedding=query_embedding, top_k=2
        )

        logger.info(f"Search results:")
        for i, item in enumerate(results):
            logger.info(f"  {i+1}. ID: {item.id}, Content: {item.text_content}")

    finally:
        # Close memory manager
        await memory_manager.close()
        logger.info("Memory manager closed")


async def example_from_env():
    """Example using configuration from environment variables."""
    logger.info("Starting example with configuration from environment variables")

    # Set environment variables
    os.environ["MEMORY_BACKEND"] = "firestore"
    os.environ["VECTOR_SEARCH_PROVIDER"] = "in_memory"

    # Create memory manager from environment variables
    memory_manager = await MemoryManagerFactory.create_memory_manager()

    try:
        # Get available backends and vector search providers
        available_backends = MemoryManagerFactory.get_available_backends()
        available_providers = (
            MemoryManagerFactory.get_available_vector_search_providers()
        )

        logger.info(f"Available backends: {[b.value for b in available_backends]}")
        logger.info(
            f"Available vector search providers: {[p.value for p in available_providers]}"
        )

        # Check health
        health = await memory_manager.health_check()
        logger.info(f"Memory manager health: {health.status}")
        logger.info(f"Health details: {health.details}")

    finally:
        # Close memory manager
        await memory_manager.close()
        logger.info("Memory manager closed")


async def main():
    """Main entry point."""
    logger.info("Starting memory management example")

    # Run examples
    await example_with_config()
    logger.info("-" * 80)
    await example_from_env()

    logger.info("Memory management example completed")


if __name__ == "__main__":
    asyncio.run(main())
