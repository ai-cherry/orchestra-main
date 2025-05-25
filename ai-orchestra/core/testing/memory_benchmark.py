"""
Memory benchmarking system for AI Orchestra.

This module provides tools for benchmarking memory provider performance
under different load conditions.
"""

import asyncio
import statistics
import time
from typing import Any, Dict, List, Optional, Tuple

from ai_orchestra.core.interfaces.memory import MemoryProvider


class MemoryBenchmark:
    """Benchmark for memory providers."""

    def __init__(
        self,
        memory_provider: MemoryProvider,
        concurrency: int = 10,
        operation_count: int = 1000,
    ):
        """
        Initialize the benchmark.

        Args:
            memory_provider: The memory provider to benchmark
            concurrency: Number of concurrent operations
            operation_count: Total number of operations to perform
        """
        self.memory_provider = memory_provider
        self.concurrency = concurrency
        self.operation_count = operation_count

    async def _run_operation(
        self,
        operation: str,
        key: str,
        value: Optional[Any] = None,
    ) -> Tuple[bool, float]:
        """
        Run an operation and measure its latency.

        Args:
            operation: The operation to run (store, retrieve, delete, exists)
            key: The key to use
            value: The value to use (for store)

        Returns:
            Tuple of (success, latency)
        """
        start_time = time.time()
        success = True

        try:
            if operation == "store":
                await self.memory_provider.store(key, value)
            elif operation == "retrieve":
                await self.memory_provider.retrieve(key)
            elif operation == "delete":
                await self.memory_provider.delete(key)
            elif operation == "exists":
                await self.memory_provider.exists(key)
            else:
                raise ValueError(f"Unknown operation: {operation}")
        except Exception:
            success = False

        latency = time.time() - start_time
        return success, latency

    async def _worker(
        self,
        worker_id: int,
        operations_per_worker: int,
        operation: str,
        results: List[Tuple[bool, float]],
    ) -> None:
        """
        Worker for running operations.

        Args:
            worker_id: The worker ID
            operations_per_worker: Number of operations to perform
            operation: The operation to run
            results: List to store results
        """
        for i in range(operations_per_worker):
            key = f"benchmark:{worker_id}:{i}"
            value = {"data": f"value-{i}", "timestamp": time.time()}

            # For non-store operations, ensure the key exists
            if operation != "store":
                await self.memory_provider.store(key, value)

            # Run the operation
            success, latency = await self._run_operation(operation, key, value)
            results.append((success, latency))

            # Clean up
            if operation != "delete":
                await self.memory_provider.delete(key)

    async def benchmark_operation(
        self,
        operation: str,
    ) -> Dict[str, Any]:
        """
        Benchmark a specific operation.

        Args:
            operation: The operation to benchmark

        Returns:
            Benchmark results
        """
        results: List[Tuple[bool, float]] = []

        # Calculate operations per worker
        operations_per_worker = self.operation_count // self.concurrency

        # Create and run workers
        workers = [
            self._worker(i, operations_per_worker, operation, results)
            for i in range(self.concurrency)
        ]

        start_time = time.time()
        await asyncio.gather(*workers)
        total_time = time.time() - start_time

        # Calculate statistics
        success_count = sum(1 for success, _ in results if success)
        success_rate = success_count / len(results) if results else 0

        latencies = [latency for success, latency in results if success]

        return {
            "operation": operation,
            "concurrency": self.concurrency,
            "operation_count": len(results),
            "success_rate": success_rate,
            "total_time": total_time,
            "operations_per_second": len(results) / total_time if total_time > 0 else 0,
            "latency": {
                "min": min(latencies) if latencies else None,
                "max": max(latencies) if latencies else None,
                "mean": statistics.mean(latencies) if latencies else None,
                "median": statistics.median(latencies) if latencies else None,
                "p95": (
                    statistics.quantiles(latencies, n=20)[18]
                    if len(latencies) >= 20
                    else None
                ),
                "p99": (
                    statistics.quantiles(latencies, n=100)[98]
                    if len(latencies) >= 100
                    else None
                ),
            },
        }

    async def run_benchmarks(self) -> Dict[str, Any]:
        """
        Run benchmarks for all operations.

        Returns:
            Benchmark results
        """
        operations = ["store", "retrieve", "exists", "delete"]

        # Run benchmarks
        results = {}
        for operation in operations:
            results[operation] = await self.benchmark_operation(operation)

        # Calculate combined statistics
        total_operations = sum(result["operation_count"] for result in results.values())
        total_time = sum(result["total_time"] for result in results.values())

        return {
            "provider": self.memory_provider.__class__.__name__,
            "concurrency": self.concurrency,
            "total_operations": total_operations,
            "total_time": total_time,
            "operations_per_second": (
                total_operations / total_time if total_time > 0 else 0
            ),
            "operations": results,
        }


# Command-line interface
if __name__ == "__main__":
    import argparse
    import json

    async def main():
        parser = argparse.ArgumentParser(description="Benchmark memory providers")
        parser.add_argument(
            "--provider",
            choices=["firestore", "redis", "failover"],
            default="firestore",
            help="Memory provider to benchmark",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=10,
            help="Number of concurrent operations",
        )
        parser.add_argument(
            "--operations",
            type=int,
            default=1000,
            help="Total number of operations to perform",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Output file for benchmark results (JSON)",
        )

        args = parser.parse_args()

        # Create the memory provider
        if args.provider == "firestore":
            from ai_orchestra.infrastructure.persistence.firestore_memory import (
                FirestoreMemoryProvider,
            )

            provider = FirestoreMemoryProvider()
        elif args.provider == "redis":
            from ai_orchestra.core.memory.redis_pool import RedisClient

            RedisClient()
            # Would need a Redis memory provider implementation
            raise NotImplementedError("Redis memory provider not implemented")
        elif args.provider == "failover":
            from ai_orchestra.infrastructure.persistence.failover_memory import (
                FailoverMemoryProvider,
            )
            from ai_orchestra.infrastructure.persistence.firestore_memory import (
                FirestoreMemoryProvider,
            )

            primary = FirestoreMemoryProvider()
            secondary = FirestoreMemoryProvider(collection_name="memory_backup")
            provider = FailoverMemoryProvider(
                [
                    (primary, "primary"),
                    (secondary, "secondary"),
                ]
            )
        else:
            raise ValueError(f"Unknown provider: {args.provider}")

        # Create and run the benchmark
        benchmark = MemoryBenchmark(
            memory_provider=provider,
            concurrency=args.concurrency,
            operation_count=args.operations,
        )

        print(
            f"Running benchmark for {args.provider} with concurrency={args.concurrency}, operations={args.operations}..."
        )
        results = await benchmark.run_benchmarks()

        # Print results
        print(f"\nBenchmark results for {results['provider']}:")
        print(f"Total operations: {results['total_operations']}")
        print(f"Total time: {results['total_time']:.2f} seconds")
        print(f"Overall throughput: {results['operations_per_second']:.2f} ops/sec")

        for operation, result in results["operations"].items():
            print(f"\n{operation.upper()}:")
            print(f"  Success rate: {result['success_rate'] * 100:.2f}%")
            print(f"  Throughput: {result['operations_per_second']:.2f} ops/sec")
            print("  Latency (seconds):")
            print(f"    Min: {result['latency']['min']:.6f}")
            print(f"    Max: {result['latency']['max']:.6f}")
            print(f"    Mean: {result['latency']['mean']:.6f}")
            print(f"    Median: {result['latency']['median']:.6f}")
            print(f"    P95: {result['latency']['p95']:.6f}")
            print(f"    P99: {result['latency']['p99']:.6f}")

        # Save results to file if specified
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
                print(f"\nResults saved to {args.output}")

    asyncio.run(main())
