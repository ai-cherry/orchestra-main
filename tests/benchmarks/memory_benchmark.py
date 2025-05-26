"""
Memory Manager Benchmark Tests.

This module provides benchmark tests for comparing the performance
of different memory manager implementations.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pytest

from packages.shared.src.memory.concrete_memory_manager import FirestoreV1MemoryManager
from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.storage.firestore.firestore_memory import (
    FirestoreMemoryManager,
)
from packages.shared.src.storage.firestore.v2 import FirestoreMemoryManagerV2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryBenchmark:
    """Benchmark for memory manager implementations."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
    ):
        """
        Initialize the benchmark.

        Args:
            project_id: Optional Google Cloud project ID
            credentials_path: Optional path to credentials file
            redis_host: Optional Redis host
            redis_port: Optional Redis port
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.redis_host = redis_host
        self.redis_port = redis_port

        self.v1_manager = None
        self.v2_manager = None
        self.test_user_id = f"benchmark-user-{int(time.time())}"

    async def setup(self):
        """Set up the benchmark."""
        logger.info("Setting up benchmark...")

        # Initialize V1 manager
        firestore_v1 = FirestoreMemoryManager(
            project_id=self.project_id,
            credentials_path=self.credentials_path,
        )

        self.v1_manager = FirestoreV1MemoryManager(
            firestore_memory=firestore_v1,
            redis_host=self.redis_host,
            redis_port=self.redis_port,
        )

        # Initialize V2 manager
        self.v2_manager = FirestoreMemoryManagerV2(
            project_id=self.project_id,
            credentials_path=self.credentials_path,
            connection_pool_size=10,
            batch_size=100,
        )

        # Initialize both managers
        await self.v1_manager.initialize()
        await self.v2_manager.initialize()

        logger.info("Benchmark setup complete")

    async def teardown(self):
        """Clean up after benchmark."""
        logger.info("Cleaning up benchmark...")

        # Close managers
        if self.v1_manager:
            await self.v1_manager.close()

        if self.v2_manager:
            await self.v2_manager.close()

        logger.info("Benchmark cleanup complete")

    async def generate_test_data(self, count: int = 100) -> List[MemoryItem]:
        """
        Generate test data for benchmarking.

        Args:
            count: Number of items to generate

        Returns:
            List of memory items
        """
        logger.info(f"Generating {count} test items...")

        items = []
        for i in range(count):
            # Generate a random embedding
            embedding = [np.random.random() for _ in range(768)]

            # Create a memory item
            item = MemoryItem(
                user_id=self.test_user_id,
                content=f"Test content {i}",
                metadata={
                    "type": "benchmark",
                    "index": i,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                embedding=embedding,
            )

            items.append(item)

        logger.info(f"Generated {len(items)} test items")
        return items

    async def run_add_benchmark(self, items: List[MemoryItem]) -> Dict[str, float]:
        """
        Benchmark adding items to memory.

        Args:
            items: List of memory items to add

        Returns:
            Dictionary with benchmark results
        """
        logger.info("Running add benchmark...")

        # Benchmark V1
        v1_start = time.time()
        for item in items:
            await self.v1_manager.add_memory_item(item)
        v1_duration = time.time() - v1_start

        # Benchmark V2
        v2_start = time.time()
        for item in items:
            await self.v2_manager.add_memory_item(item)
        v2_duration = time.time() - v2_start

        results = {
            "v1_duration": v1_duration,
            "v2_duration": v2_duration,
            "v1_items_per_second": len(items) / v1_duration,
            "v2_items_per_second": len(items) / v2_duration,
            "improvement_factor": (
                v1_duration / v2_duration if v2_duration > 0 else float("inf")
            ),
        }

        logger.info(f"Add benchmark results: {json.dumps(results, indent=2)}")
        return results

    async def run_get_benchmark(self, item_ids: List[str]) -> Dict[str, float]:
        """
        Benchmark getting items from memory.

        Args:
            item_ids: List of item IDs to get

        Returns:
            Dictionary with benchmark results
        """
        logger.info("Running get benchmark...")

        # Benchmark V1
        v1_start = time.time()
        for item_id in item_ids:
            await self.v1_manager.get_memory_item(item_id)
        v1_duration = time.time() - v1_start

        # Benchmark V2
        v2_start = time.time()
        for item_id in item_ids:
            await self.v2_manager.get_memory_item(item_id)
        v2_duration = time.time() - v2_start

        results = {
            "v1_duration": v1_duration,
            "v2_duration": v2_duration,
            "v1_items_per_second": len(item_ids) / v1_duration,
            "v2_items_per_second": len(item_ids) / v2_duration,
            "improvement_factor": (
                v1_duration / v2_duration if v2_duration > 0 else float("inf")
            ),
        }

        logger.info(f"Get benchmark results: {json.dumps(results, indent=2)}")
        return results

    async def run_search_benchmark(
        self, query_embedding: List[float], top_k: int = 5
    ) -> Dict[str, float]:
        """
        Benchmark semantic search.

        Args:
            query_embedding: Query embedding
            top_k: Number of results to return

        Returns:
            Dictionary with benchmark results
        """
        logger.info("Running search benchmark...")

        # Benchmark V1
        v1_start = time.time()
        v1_results = await self.v1_manager.semantic_search(
            user_id=self.test_user_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        v1_duration = time.time() - v1_start

        # Benchmark V2
        v2_start = time.time()
        v2_results = await self.v2_manager.semantic_search(
            user_id=self.test_user_id,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        v2_duration = time.time() - v2_start

        results = {
            "v1_duration": v1_duration,
            "v2_duration": v2_duration,
            "v1_result_count": len(v1_results),
            "v2_result_count": len(v2_results),
            "improvement_factor": (
                v1_duration / v2_duration if v2_duration > 0 else float("inf")
            ),
        }

        logger.info(f"Search benchmark results: {json.dumps(results, indent=2)}")
        return results

    async def run_history_benchmark(self, limit: int = 20) -> Dict[str, float]:
        """
        Benchmark getting conversation history.

        Args:
            limit: Maximum number of items to retrieve

        Returns:
            Dictionary with benchmark results
        """
        logger.info("Running history benchmark...")

        # Benchmark V1
        v1_start = time.time()
        v1_results = await self.v1_manager.get_conversation_history(
            user_id=self.test_user_id,
            limit=limit,
        )
        v1_duration = time.time() - v1_start

        # Benchmark V2
        v2_start = time.time()
        v2_results = await self.v2_manager.get_conversation_history(
            user_id=self.test_user_id,
            limit=limit,
        )
        v2_duration = time.time() - v2_start

        results = {
            "v1_duration": v1_duration,
            "v2_duration": v2_duration,
            "v1_result_count": len(v1_results),
            "v2_result_count": len(v2_results),
            "improvement_factor": (
                v1_duration / v2_duration if v2_duration > 0 else float("inf")
            ),
        }

        logger.info(f"History benchmark results: {json.dumps(results, indent=2)}")
        return results

    async def run_all_benchmarks(self, item_count: int = 100) -> Dict[str, Any]:
        """
        Run all benchmarks.

        Args:
            item_count: Number of items to use for benchmarks

        Returns:
            Dictionary with all benchmark results
        """
        logger.info(f"Running all benchmarks with {item_count} items...")

        try:
            # Set up
            await self.setup()

            # Generate test data
            items = await self.generate_test_data(item_count)

            # Run add benchmark
            add_results = await self.run_add_benchmark(items)

            # Get item IDs for get benchmark
            item_ids = [item.id for item in items[: min(20, len(items))]]

            # Run get benchmark
            get_results = await self.run_get_benchmark(item_ids)

            # Generate query embedding for search benchmark
            query_embedding = [np.random.random() for _ in range(768)]

            # Run search benchmark
            search_results = await self.run_search_benchmark(query_embedding)

            # Run history benchmark
            history_results = await self.run_history_benchmark()

            # Combine results
            all_results = {
                "add": add_results,
                "get": get_results,
                "search": search_results,
                "history": history_results,
                "timestamp": datetime.utcnow().isoformat(),
                "item_count": item_count,
            }

            logger.info("All benchmarks complete")
            return all_results

        finally:
            # Clean up
            await self.teardown()


@pytest.mark.asyncio
async def test_memory_benchmark():
    """Run the memory benchmark."""
    # Skip if running in CI
    import os

    if os.environ.get("CI") == "true":
        pytest.skip("Skipping benchmark in CI")

    # Run benchmark
    benchmark = MemoryBenchmark()
    results = await benchmark.run_all_benchmarks(item_count=10)

    # Check that V2 is faster than V1
    assert results["add"]["improvement_factor"] > 1.0
    assert results["get"]["improvement_factor"] > 1.0
    assert results["search"]["improvement_factor"] > 1.0
    assert results["history"]["improvement_factor"] > 1.0


if __name__ == "__main__":
    """Run the benchmark directly."""
    import argparse

    parser = argparse.ArgumentParser(description="Memory Manager Benchmark")
    parser.add_argument("--project-id", help="Google Cloud project ID")
    parser.add_argument("--credentials-path", help="Path to credentials file")
    parser.add_argument("--redis-host", help="Redis host")
    parser.add_argument("--redis-port", type=int, help="Redis port")
    parser.add_argument(
        "--item-count",
        type=int,
        default=100,
        help="Number of items to use for benchmarks",
    )
    args = parser.parse_args()

    # Run benchmark
    benchmark = MemoryBenchmark(
        project_id=args.project_id,
        credentials_path=args.credentials_path,
        redis_host=args.redis_host,
        redis_port=args.redis_port,
    )

    asyncio.run(benchmark.run_all_benchmarks(item_count=args.item_count))
