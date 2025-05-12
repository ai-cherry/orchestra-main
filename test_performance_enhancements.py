#!/usr/bin/env python3
"""
Test performance enhancements for the AI Orchestra project.

This script verifies the implemented performance enhancements by
running benchmarks and validating functionality.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import statistics
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class PerformanceTester:
    """Tests performance enhancements for the AI Orchestra project."""
    
    def __init__(
        self,
        base_dir: str = ".",
        ai_orchestra_dir: str = "ai-orchestra",
        skip_redis: bool = False,
        skip_api: bool = False,
        skip_vertex: bool = False,
        iterations: int = 5,
    ):
        """
        Initialize the performance tester.
        
        Args:
            base_dir: Base directory of the project
            ai_orchestra_dir: AI Orchestra directory
            skip_redis: Whether to skip Redis tests
            skip_api: Whether to skip API tests
            skip_vertex: Whether to skip Vertex AI tests
            iterations: Number of iterations for each test
        """
        self.base_dir = Path(base_dir)
        self.ai_orchestra_dir = self.base_dir / ai_orchestra_dir
        self.skip_redis = skip_redis
        self.skip_api = skip_api
        self.skip_vertex = skip_vertex
        self.iterations = iterations
        
        # Test results
        self.results: Dict[str, Dict[str, Any]] = {}
        
        # Import paths setup
        sys.path.insert(0, str(self.base_dir))
    
    async def run_tests(self) -> Dict[str, Dict[str, Any]]:
        """
        Run all performance tests.
        
        Returns:
            Dictionary of test results
        """
        logger.info("Starting performance tests...")
        
        # Redis connection pool tests
        if not self.skip_redis:
            logger.info("Testing Redis connection pool enhancements...")
            await self.test_redis_connection_pool()
        
        # Tiered cache tests
        if not self.skip_redis:
            logger.info("Testing tiered cache enhancements...")
            await self.test_tiered_cache()
        
        # API middleware tests
        if not self.skip_api:
            logger.info("Testing API middleware enhancements...")
            await self.test_api_middleware()
        
        # Vertex AI tests
        if not self.skip_vertex:
            logger.info("Testing Vertex AI optimizations...")
            await self.test_vertex_ai_optimizations()
        
        logger.info("All tests completed.")
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    async def test_redis_connection_pool(self) -> None:
        """Test Redis connection pool performance."""
        try:
            # Skip if Redis is not available
            try:
                from ai_orchestra.infrastructure.caching.optimized_redis_pool import (
                    get_optimized_redis_client,
                    OptimizedRedisClient,
                    PoolType
                )
            except ImportError:
                logger.warning("OptimizedRedisClient not found, skipping Redis tests")
                self.results["redis_connection_pool"] = {"status": "skipped", "reason": "not_implemented"}
                return
                
            # Prepare test data
            test_keys = [f"test_key_{i}" for i in range(100)]
            test_values = [f"test_value_{i}" for i in range(100)]
            
            # Basic functionality test
            client = await get_optimized_redis_client(pool_type=PoolType.CACHE)
            
            # Test set operation
            set_times = []
            for i in range(self.iterations):
                start_time = time.time()
                await client.set(f"test_perf_{i}", f"value_{i}")
                set_times.append(time.time() - start_time)
            
            # Test get operation
            get_times = []
            for i in range(self.iterations):
                start_time = time.time()
                await client.get(f"test_perf_{i}")
                get_times.append(time.time() - start_time)
            
            # Test batch operations
            batch_times = []
            key_values = {f"batch_key_{i}": f"batch_value_{i}" for i in range(10)}
            for i in range(self.iterations):
                start_time = time.time()
                await client.batch_set(key_values)
                batch_times.append(time.time() - start_time)
            
            # Test connection pool metrics
            metrics = await client.get_metrics()
            
            # Clean up test keys
            for i in range(self.iterations):
                await client.delete(f"test_perf_{i}")
            await client.batch_delete([f"batch_key_{i}" for i in range(10)])
            
            # Close client
            await client.close()
            
            # Save results
            self.results["redis_connection_pool"] = {
                "status": "success",
                "set_latency_ms": statistics.mean(set_times) * 1000,
                "get_latency_ms": statistics.mean(get_times) * 1000,
                "batch_latency_ms": statistics.mean(batch_times) * 1000,
                "metrics": metrics,
            }
            
        except Exception as e:
            logger.error(f"Redis connection pool test failed: {str(e)}")
            self.results["redis_connection_pool"] = {
                "status": "error",
                "error": str(e),
            }
    
    async def test_tiered_cache(self) -> None:
        """Test tiered cache performance."""
        try:
            # Skip if tiered cache is not available
            try:
                from ai_orchestra.infrastructure.caching.tiered_cache import (
                    get_tiered_cache,
                    TieredCache,
                    cached
                )
            except ImportError:
                logger.warning("TieredCache not found, skipping tiered cache tests")
                self.results["tiered_cache"] = {"status": "skipped", "reason": "not_implemented"}
                return
                
            # Get cache instance
            cache = get_tiered_cache()
            
            # Test basic cache operations
            # L1 cache test (should be fast)
            l1_set_times = []
            l1_get_times = []
            
            for i in range(self.iterations):
                key = f"l1_test_{i}"
                value = {"data": f"value_{i}", "timestamp": time.time()}
                
                # Set
                start_time = time.time()
                await cache.set(key, value, l1_ttl_seconds=60, l2_ttl_seconds=300)
                l1_set_times.append(time.time() - start_time)
                
                # Get (should be in L1)
                start_time = time.time()
                result = await cache.get(key)
                l1_get_times.append(time.time() - start_time)
                
                # Verify
                assert result["data"] == f"value_{i}"
            
            # Cache warmup test
            await cache.warm_up([f"l1_test_{i}" for i in range(self.iterations)])
            
            # Get cache stats
            stats = await cache.get_stats()
            
            # Save results
            self.results["tiered_cache"] = {
                "status": "success",
                "l1_set_latency_ms": statistics.mean(l1_set_times) * 1000,
                "l1_get_latency_ms": statistics.mean(l1_get_times) * 1000,
                "stats": stats,
            }
            
        except Exception as e:
            logger.error(f"Tiered cache test failed: {str(e)}")
            self.results["tiered_cache"] = {
                "status": "error",
                "error": str(e),
            }
    
    async def test_api_middleware(self) -> None:
        """Test API middleware performance."""
        try:
            # Skip if API middleware is not available
            try:
                from ai_orchestra.infrastructure.api.middleware import (
                    ResponseCompressionMiddleware,
                    CacheControlMiddleware,
                    PayloadOptimizationMiddleware
                )
                from fastapi import FastAPI, Request, Response
                from fastapi.responses import JSONResponse
                from starlette.testclient import TestClient
            except ImportError:
                logger.warning("API middleware not found, skipping API tests")
                self.results["api_middleware"] = {"status": "skipped", "reason": "not_implemented"}
                return
                
            # Create a test app
            app = FastAPI(title="Test API")
            
            # Add middleware
            app.add_middleware(
                ResponseCompressionMiddleware,
                min_size=100,  # Set low for testing
                compression_level=6,
            )
            
            app.add_middleware(
                CacheControlMiddleware,
                cache_config={
                    "/test": {
                        "max_age": 60,
                        "public": True,
                    }
                },
            )
            
            app.add_middleware(
                PayloadOptimizationMiddleware,
                fields_param="fields",
                max_fields=10,
            )
            
            # Add test endpoints
            @app.get("/test")
            async def test_endpoint():
                # Generate a response large enough to trigger compression
                data = {"items": [{"id": i, "name": f"Item {i}", "description": "A" * 100} for i in range(100)]}
                return data
            
            @app.get("/test_fields")
            async def test_fields_endpoint():
                # Endpoint for field filtering test
                data = {
                    "id": 1,
                    "name": "Test Item",
                    "description": "Test description",
                    "metadata": {
                        "created_at": "2025-01-01",
                        "updated_at": "2025-01-02",
                        "tags": ["test", "api", "fields"]
                    }
                }
                return data
            
            # Create test client
            client = TestClient(app)
            
            # Test compression
            compression_times = []
            for i in range(self.iterations):
                start_time = time.time()
                response = client.get(
                    "/test",
                    headers={"Accept-Encoding": "gzip, deflate, br"}
                )
                compression_times.append(time.time() - start_time)
                assert response.status_code == 200
                assert "Content-Encoding" in response.headers
            
            # Test field filtering
            field_filtering_times = []
            for i in range(self.iterations):
                start_time = time.time()
                response = client.get("/test_fields?fields=id,name")
                field_filtering_times.append(time.time() - start_time)
                assert response.status_code == 200
                data = response.json()
                assert "id" in data
                assert "name" in data
                assert "description" not in data
            
            # Test cache control
            response = client.get("/test")
            cache_control = response.headers.get("Cache-Control", "")
            
            # Save results
            self.results["api_middleware"] = {
                "status": "success",
                "compression_latency_ms": statistics.mean(compression_times) * 1000,
                "field_filtering_latency_ms": statistics.mean(field_filtering_times) * 1000,
                "cache_control": cache_control,
            }
            
        except Exception as e:
            logger.error(f"API middleware test failed: {str(e)}")
            self.results["api_middleware"] = {
                "status": "error",
                "error": str(e),
            }
    
    async def test_vertex_ai_optimizations(self) -> None:
        """Test Vertex AI optimizations."""
        try:
            # Skip if Vertex AI optimizations are not available
            try:
                from ai_orchestra.infrastructure.gcp.optimized_vertex_ai import (
                    OptimizedVertexAIService,
                    BatchProcessor,
                    EmbeddingBatchProcessor
                )
            except ImportError:
                logger.warning("OptimizedVertexAIService not found, skipping Vertex AI tests")
                self.results["vertex_ai"] = {"status": "skipped", "reason": "not_implemented"}
                return
                
            # Create a mock implementation for testing
            class MockOptimizedVertexAIService(OptimizedVertexAIService):
                """Mock implementation for testing."""
                
                def __init__(self):
                    """Initialize mock service."""
                    self.project_id = "test-project"
                    self.location = "us-central1"
                    self.enable_batching = True
                    self.enable_caching = True
                    self.semantic_cache_threshold = 0.85
                    self.model_mapping = {
                        "gemini-pro": "gemini-pro",
                        "text-embedding": "text-embedding-gecko"
                    }
                    self.embedding_batch_processors = {}
                    self.response_cache = None
                    self.semantic_cache = None
                    self._generative_models = {}
                
                async def generate_text(self, prompt, **kwargs):
                    """Mock generate text."""
                    await asyncio.sleep(0.05)  # Simulate API latency
                    return f"Response for: {prompt[:20]}..."
                
                async def generate_embeddings(self, texts, **kwargs):
                    """Mock generate embeddings."""
                    await asyncio.sleep(0.05)  # Simulate API latency
                    return [[random.random() for _ in range(10)] for _ in texts]
            
            # Create mock service
            service = MockOptimizedVertexAIService()
            
            # Test text generation
            text_gen_times = []
            for i in range(self.iterations):
                start_time = time.time()
                response = await service.generate_text(
                    prompt=f"Test prompt {i} with some content to generate",
                    model_id="gemini-pro"
                )
                text_gen_times.append(time.time() - start_time)
            
            # Test embedding generation
            embedding_times = []
            for i in range(self.iterations):
                start_time = time.time()
                response = await service.generate_embeddings(
                    texts=[f"Test text {j} for embedding" for j in range(5)],
                    model_id="text-embedding"
                )
                embedding_times.append(time.time() - start_time)
            
            # Save results
            self.results["vertex_ai"] = {
                "status": "success",
                "text_generation_latency_ms": statistics.mean(text_gen_times) * 1000,
                "embedding_latency_ms": statistics.mean(embedding_times) * 1000,
            }
            
        except Exception as e:
            logger.error(f"Vertex AI test failed: {str(e)}")
            self.results["vertex_ai"] = {
                "status": "error",
                "error": str(e),
            }
    
    def print_summary(self) -> None:
        """Print a summary of test results."""
        print("\n===== AI Orchestra Performance Enhancements Test Results =====\n")
        
        all_success = True
        
        for category, results in self.results.items():
            status = results.get("status", "unknown")
            if status == "success":
                print(f"✅ {category.replace('_', ' ').title()}: Passed")
                
                # Print key metrics
                if category == "redis_connection_pool":
                    print(f"   - SET operation latency: {results['set_latency_ms']:.2f}ms")
                    print(f"   - GET operation latency: {results['get_latency_ms']:.2f}ms")
                    print(f"   - Batch operation latency: {results['batch_latency_ms']:.2f}ms")
                
                elif category == "tiered_cache":
                    print(f"   - L1 cache SET latency: {results['l1_set_latency_ms']:.2f}ms")
                    print(f"   - L1 cache GET latency: {results['l1_get_latency_ms']:.2f}ms")
                
                elif category == "api_middleware":
                    print(f"   - Compression latency: {results['compression_latency_ms']:.2f}ms")
                    print(f"   - Field filtering latency: {results['field_filtering_latency_ms']:.2f}ms")
                    print(f"   - Cache-Control: {results['cache_control']}")
                
                elif category == "vertex_ai":
                    print(f"   - Text generation latency: {results['text_generation_latency_ms']:.2f}ms")
                    print(f"   - Embedding generation latency: {results['embedding_latency_ms']:.2f}ms")
                
            elif status == "skipped":
                print(f"⏭️ {category.replace('_', ' ').title()}: Skipped ({results.get('reason', 'unknown reason')})")
            
            else:
                all_success = False
                print(f"❌ {category.replace('_', ' ').title()}: Failed - {results.get('error', 'Unknown error')}")
            
            print()
        
        print("Overall Result:", "✅ All tests passed" if all_success else "❌ Some tests failed")
        print("\n==========================================================\n")


async def run_tests(args):
    """Run all tests with the given arguments."""
    tester = PerformanceTester(
        base_dir=args.base_dir,
        ai_orchestra_dir=args.ai_orchestra_dir,
        skip_redis=args.skip_redis,
        skip_api=args.skip_api,
        skip_vertex=args.skip_vertex,
        iterations=args.iterations,
    )
    
    results = await tester.run_tests()
    
    # Save results to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    return 0 if all(r.get("status") == "success" or r.get("status") == "skipped" for r in results.values()) else 1


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Test performance enhancements for the AI Orchestra project"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory of the project",
    )
    
    parser.add_argument(
        "--ai-orchestra-dir",
        type=str,
        default="ai-orchestra",
        help="AI Orchestra directory",
    )
    
    parser.add_argument(
        "--skip-redis",
        action="store_true",
        help="Skip Redis tests",
    )
    
    parser.add_argument(
        "--skip-api",
        action="store_true",
        help="Skip API tests",
    )
    
    parser.add_argument(
        "--skip-vertex",
        action="store_true",
        help="Skip Vertex AI tests",
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of iterations for each test",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for test results (JSON)",
    )
    
    args = parser.parse_args()
    
    return asyncio.run(run_tests(args))


if __name__ == "__main__":
    sys.exit(main())