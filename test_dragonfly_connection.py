#!/usr/bin/env python3
"""
Test script for DragonflyDB connection and performance.

This script verifies:
- DragonflyDB connectivity
- CRUD operations
- Performance benchmarking
- Connection pooling
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.config.dragonfly_config import log_dragonfly_config, validate_dragonfly_config
from mcp_server.memory.base import MemoryEntry, MemoryMetadata
from mcp_server.memory.dragonfly_cache import DragonflyCache

class DragonflyConnectionTest:
    """Test suite for DragonflyDB connection and operations."""

    def __init__(self):
        self.cache = DragonflyCache()
        self.test_results: Dict[str, Any] = {}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("=" * 60)
        print("DragonflyDB Connection Test Suite")
        print("=" * 60)

        # Validate configuration
        print("\n1. Validating configuration...")
        if not validate_dragonfly_config():
            print("❌ Configuration validation failed")
            return {"error": "Invalid configuration"}
        print("✅ Configuration valid")

        # Initialize connection
        print("\n2. Testing connection...")
        success = await self.test_connection()
        if not success:
            return self.test_results

        # Test CRUD operations
        print("\n3. Testing CRUD operations...")
        await self.test_crud_operations()

        # Test batch operations
        print("\n4. Testing batch operations...")
        await self.test_batch_operations()

        # Performance benchmarks
        print("\n5. Running performance benchmarks...")
        await self.test_performance()

        # Connection pool test
        print("\n6. Testing connection pooling...")
        await self.test_connection_pool()

        # Health check
        print("\n7. Testing health check...")
        await self.test_health_check()

        return self.test_results

    async def test_connection(self) -> bool:
        """Test basic connection to DragonflyDB."""
        try:
            start = time.time()
            initialized = await self.cache.initialize()
            init_time = (time.time() - start) * 1000

            if initialized:
                print(f"✅ Connected successfully (init time: {init_time:.2f}ms)")
                self.test_results["connection"] = {
                    "status": "success",
                    "init_time_ms": init_time,
                }
                return True
            else:
                print("❌ Failed to initialize connection")
                self.test_results["connection"] = {"status": "failed"}
                return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            self.test_results["connection"] = {"status": "error", "error": str(e)}
            return False

    async def test_crud_operations(self) -> None:
        """Test Create, Read, Update, Delete operations."""
        results = {}

        try:
            # Create/Save test
            test_entry = MemoryEntry(
                key="test_key_1",
                content={
                    "message": "Hello DragonflyDB!",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                metadata=MemoryMetadata(tags=["test", "crud"], source="test_script", ttl_seconds=300),  # 5 minutes
            )

            start = time.time()
            save_success = await self.cache.save(test_entry)
            save_time = (time.time() - start) * 1000

            if save_success:
                print(f"  ✅ Save: Success ({save_time:.2f}ms)")
                results["save"] = {"status": "success", "time_ms": save_time}
            else:
                print("  ❌ Save: Failed")
                results["save"] = {"status": "failed"}

            # Read test
            start = time.time()
            retrieved = await self.cache.get("test_key_1")
            get_time = (time.time() - start) * 1000

            if retrieved and retrieved.content == test_entry.content:
                print(f"  ✅ Get: Success ({get_time:.2f}ms)")
                results["get"] = {"status": "success", "time_ms": get_time}
            else:
                print("  ❌ Get: Failed")
                results["get"] = {"status": "failed"}

            # Update test (save with same key)
            test_entry.content["message"] = "Updated message!"
            start = time.time()
            update_success = await self.cache.save(test_entry)
            update_time = (time.time() - start) * 1000

            if update_success:
                print(f"  ✅ Update: Success ({update_time:.2f}ms)")
                results["update"] = {"status": "success", "time_ms": update_time}
            else:
                print("  ❌ Update: Failed")
                results["update"] = {"status": "failed"}

            # Delete test
            start = time.time()
            delete_success = await self.cache.delete("test_key_1")
            delete_time = (time.time() - start) * 1000

            if delete_success:
                print(f"  ✅ Delete: Success ({delete_time:.2f}ms)")
                results["delete"] = {"status": "success", "time_ms": delete_time}
            else:
                print("  ❌ Delete: Failed")
                results["delete"] = {"status": "failed"}

            # Verify deletion
            verify = await self.cache.get("test_key_1")
            if verify is None:
                print("  ✅ Delete verification: Confirmed")
            else:
                print("  ❌ Delete verification: Failed")

        except Exception as e:
            print(f"  ❌ CRUD test error: {e}")
            results["error"] = str(e)

        self.test_results["crud"] = results

    async def test_batch_operations(self) -> None:
        """Test batch save and get operations."""
        results = {}

        try:
            # Create test entries
            entries = []
            for i in range(100):
                entry = MemoryEntry(
                    key=f"batch_test_{i}",
                    content={"index": i, "data": f"Batch entry {i}"},
                    metadata=MemoryMetadata(tags=["batch", "test"], ttl_seconds=300),
                )
                entries.append(entry)

            # Batch save
            start = time.time()
            save_results = await self.cache.batch_save(entries)
            batch_save_time = (time.time() - start) * 1000

            success_count = sum(1 for success in save_results.values() if success)
            print(f"  ✅ Batch save: {success_count}/100 succeeded ({batch_save_time:.2f}ms)")
            print(f"     Rate: {(100 / (batch_save_time / 1000)):.0f} ops/sec")

            results["batch_save"] = {
                "success_count": success_count,
                "total": 100,
                "time_ms": batch_save_time,
                "ops_per_sec": 100 / (batch_save_time / 1000),
            }

            # Batch get
            keys = [f"batch_test_{i}" for i in range(100)]
            start = time.time()
            get_results = await self.cache.batch_get(keys)
            batch_get_time = (time.time() - start) * 1000

            found_count = sum(1 for entry in get_results.values() if entry is not None)
            print(f"  ✅ Batch get: {found_count}/100 found ({batch_get_time:.2f}ms)")
            print(f"     Rate: {(100 / (batch_get_time / 1000)):.0f} ops/sec")

            results["batch_get"] = {
                "found_count": found_count,
                "total": 100,
                "time_ms": batch_get_time,
                "ops_per_sec": 100 / (batch_get_time / 1000),
            }

            # Cleanup
            await self.cache.clear(prefix="batch_test_")

        except Exception as e:
            print(f"  ❌ Batch operations error: {e}")
            results["error"] = str(e)

        self.test_results["batch_operations"] = results

    async def test_performance(self) -> None:
        """Run performance benchmarks."""
        results = {}

        try:
            # Single operation latency test
            latencies = []
            for i in range(100):
                entry = MemoryEntry(
                    key=f"perf_test_{i}",
                    content={"test": "performance", "index": i},
                    metadata=MemoryMetadata(ttl_seconds=60),
                )

                start = time.time()
                await self.cache.save(entry)
                latency = (time.time() - start) * 1000
                latencies.append(latency)

            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

            print("  📊 Write latency:")
            print(f"     Average: {avg_latency:.2f}ms")
            print(f"     Min: {min_latency:.2f}ms")
            print(f"     Max: {max_latency:.2f}ms")
            print(f"     P99: {p99_latency:.2f}ms")

            results["write_latency"] = {
                "avg_ms": avg_latency,
                "min_ms": min_latency,
                "max_ms": max_latency,
                "p99_ms": p99_latency,
            }

            # Read latency test
            read_latencies = []
            for i in range(100):
                start = time.time()
                await self.cache.get(f"perf_test_{i}")
                latency = (time.time() - start) * 1000
                read_latencies.append(latency)

            avg_read_latency = sum(read_latencies) / len(read_latencies)
            min_read_latency = min(read_latencies)
            max_read_latency = max(read_latencies)
            p99_read_latency = sorted(read_latencies)[int(len(read_latencies) * 0.99)]

            print("  📊 Read latency:")
            print(f"     Average: {avg_read_latency:.2f}ms")
            print(f"     Min: {min_read_latency:.2f}ms")
            print(f"     Max: {max_read_latency:.2f}ms")
            print(f"     P99: {p99_read_latency:.2f}ms")

            results["read_latency"] = {
                "avg_ms": avg_read_latency,
                "min_ms": min_read_latency,
                "max_ms": max_read_latency,
                "p99_ms": p99_read_latency,
            }

            # Throughput test
            start = time.time()
            tasks = []
            for i in range(1000):
                entry = MemoryEntry(
                    key=f"throughput_test_{i}",
                    content={"test": "throughput", "index": i},
                    metadata=MemoryMetadata(ttl_seconds=60),
                )
                tasks.append(self.cache.save(entry))

            await asyncio.gather(*tasks)
            duration = time.time() - start
            throughput = 1000 / duration

            print(f"  📊 Throughput: {throughput:.0f} ops/sec")

            results["throughput"] = {
                "ops_per_sec": throughput,
                "total_ops": 1000,
                "duration_sec": duration,
            }

            # Cleanup
            await self.cache.clear(prefix="perf_test_")
            await self.cache.clear(prefix="throughput_test_")

        except Exception as e:
            print(f"  ❌ Performance test error: {e}")
            results["error"] = str(e)

        self.test_results["performance"] = results

    async def test_connection_pool(self) -> None:
        """Test connection pooling behavior."""
        results = {}

        try:
            # Concurrent operations to test pooling
            async def concurrent_operation(index: int) -> float:
                entry = MemoryEntry(
                    key=f"pool_test_{index}",
                    content={"test": "pool", "index": index},
                    metadata=MemoryMetadata(ttl_seconds=60),
                )
                start = time.time()
                await self.cache.save(entry)
                return (time.time() - start) * 1000

            # Run 200 concurrent operations (matching pool size)
            start = time.time()
            tasks = [concurrent_operation(i) for i in range(200)]
            latencies = await asyncio.gather(*tasks)
            total_time = (time.time() - start) * 1000

            avg_latency = sum(latencies) / len(latencies)

            print("  ✅ Connection pool test:")
            print(f"     200 concurrent operations in {total_time:.2f}ms")
            print(f"     Average latency: {avg_latency:.2f}ms")
            print(f"     Effective parallelism: {(sum(latencies) / total_time):.1f}x")

            results["pool_test"] = {
                "concurrent_ops": 200,
                "total_time_ms": total_time,
                "avg_latency_ms": avg_latency,
                "parallelism": sum(latencies) / total_time,
            }

            # Cleanup
            await self.cache.clear(prefix="pool_test_")

        except Exception as e:
            print(f"  ❌ Connection pool test error: {e}")
            results["error"] = str(e)

        self.test_results["connection_pool"] = results

    async def test_health_check(self) -> None:
        """Test health check functionality."""
        try:
            health = await self.cache.health_check()

            print("  ✅ Health check:")
            print(f"     Status: {health.get('status', 'unknown')}")
            print(f"     Latency: {health.get('latency_ms', 'N/A')}ms")
            print(f"     Version: {health.get('version', 'unknown')}")
            print(f"     DB Index: {health.get('db_index', 'unknown')}")
            print(f"     Dev Mode: {health.get('is_dev_mode', False)}")

            self.test_results["health_check"] = health

        except Exception as e:
            print(f"  ❌ Health check error: {e}")
            self.test_results["health_check"] = {"error": str(e)}

    async def cleanup(self) -> None:
        """Clean up test data and close connections."""
        try:
            # Clear all test data
            prefixes = [
                "test_",
                "batch_test_",
                "perf_test_",
                "throughput_test_",
                "pool_test_",
            ]
            for prefix in prefixes:
                await self.cache.clear(prefix=prefix)

            # Close connections
            await self.cache.close()

        except Exception as e:
            print(f"Warning: Cleanup error: {e}")

async def main():
    """Run the test suite."""
    tester = DragonflyConnectionTest()

    try:
        # Show configuration
        print("\nConfiguration:")
        log_dragonfly_config()

        # Run tests
        results = await tester.run_all_tests()

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        # Pretty print results
        print(json.dumps(results, indent=2, default=str))

        # Overall status
        all_passed = all(
            result.get("status") == "success" or (isinstance(result, dict) and not result.get("error"))
            for result in results.values()
            if isinstance(result, dict)
        )

        if all_passed:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed. Check the results above.")

    finally:
        # Cleanup
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
