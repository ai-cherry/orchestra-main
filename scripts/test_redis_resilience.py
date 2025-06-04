#!/usr/bin/env python3
"""
Test Redis Resilience - Demonstrates circuit breaker, fallback, and monitoring
"""

import asyncio
import time
import logging
from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.redis import (
    setup_redis,
    ResilientRedisClient,
    AsyncResilientRedisClient,
    RedisHealthMonitor,
    CacheWarmer,
    WarmingStrategy,
    CacheEntry,
    redis_cache,
    redis_health_check
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisResilienceDemo:
    """Demonstrate Redis resilience features"""
    
    def __init__(self):
        # Setup Redis with all features
        self.client, self.monitor, self.warmer = setup_redis(
            env="development",
            enable_monitoring=True,
            enable_cache_warming=True
        )
        
    async def test_basic_operations(self):
        """Test basic Redis operations with resilience"""
        print("\n=== Testing Basic Operations ===")
        
        # Test set/get
        key = "test:basic:1"
        value = {"data": "test value", "timestamp": time.time()}
        
        success = self.client.set(key, value, ex=300)
        print(f"Set operation: {'Success' if success else 'Failed'}")
        
        retrieved = self.client.get(key)
        print(f"Get operation: {retrieved}")
        
        # Test exists
        exists = self.client.exists(key)
        print(f"Key exists: {exists}")
        
        # Test delete
        deleted = self.client.delete(key)
        print(f"Delete operation: {deleted} keys deleted")
        
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        print("\n=== Testing Circuit Breaker ===")
        
        # Simulate Redis failure by using invalid connection
        failed_client = ResilientRedisClient(
            redis_url="redis://invalid-host:6379",
            circuit_breaker_config={
                "failure_threshold": 3,
                "recovery_timeout": 5
            }
        )
        
        # Try operations that will fail
        for i in range(5):
            try:
                failed_client.get(f"test:key:{i}")
                print(f"Attempt {i+1}: Success (unexpected)")
            except Exception as e:
                print(f"Attempt {i+1}: Failed - {type(e).__name__}")
                
            # Check circuit breaker state
            metrics = failed_client.get_metrics()
            print(f"  Circuit breaker state: {metrics['circuit_breaker_state']}")
            
        print("\nWaiting for circuit breaker recovery...")
        await asyncio.sleep(6)
        
        # Try again after recovery timeout
        try:
            failed_client.get("test:recovery")
            print("Recovery attempt: Success")
        except Exception as e:
            print(f"Recovery attempt: Failed - {type(e).__name__}")
            
    async def test_fallback_mechanism(self):
        """Test fallback to in-memory cache"""
        print("\n=== Testing Fallback Mechanism ===")
        
        # Create client with custom fallback
        from core.redis import InMemoryFallback
        fallback = InMemoryFallback(max_size=100, ttl=60)
        
        client = ResilientRedisClient(
            redis_url="redis://invalid-host:6379",
            fallback_handler=fallback
        )
        
        # Operations will use fallback
        key = "test:fallback:1"
        value = "fallback test value"
        
        # Set will use fallback
        success = client.set(key, value, ex=60)
        print(f"Set with fallback: {'Success' if success else 'Failed'}")
        
        # Get will retrieve from fallback
        retrieved = client.get(key)
        print(f"Get from fallback: {retrieved}")
        
        # Check metrics
        metrics = client.get_metrics()
        print(f"Fallback invocations: {metrics['fallback_used']}")
        
    async def test_health_monitoring(self):
        """Test health monitoring"""
        print("\n=== Testing Health Monitoring ===")
        
        # Perform health check
        health = await redis_health_check()
        
        print(f"Health Status: {health['status']}")
        print("Health Checks:")
        for check, result in health['checks'].items():
            print(f"  {check}: {result}")
            
        print("\nMetrics:")
        metrics = health['metrics']
        print(f"  Circuit breaker state: {metrics['circuit_breaker_state']}")
        print(f"  Commands executed: {metrics['commands_executed']}")
        print(f"  Commands failed: {metrics['commands_failed']}")
        print(f"  Fallback used: {metrics['fallback_used']}")
        
        # Get monitoring stats
        if self.monitor:
            current_health = self.monitor.get_current_health()
            print(f"\nMonitor Status: {current_health['status']}")
            
            # Get metrics summary
            summary = self.monitor.get_metrics_summary(window_minutes=5)
            if summary:
                print(f"Metrics Summary (last 5 minutes):")
                print(f"  Average latency: {summary['averages']['command_latency_ms']:.2f}ms")
                print(f"  Total commands: {summary['totals']['commands_executed']}")
                
    async def test_cache_warming(self):
        """Test cache warming strategies"""
        print("\n=== Testing Cache Warming ===")
        
        if not self.warmer:
            print("Cache warming not enabled")
            return
            
        # Register data loaders
        def user_loader(key: str) -> Dict[str, Any]:
            """Simulate loading user data"""
            user_id = key.split(":")[-1]
            return {
                "id": user_id,
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com",
                "loaded_at": time.time()
            }
            
        self.warmer.register_loader("user:*", user_loader)
        
        # Create entries to warm
        entries = [
            CacheEntry(
                key=f"user:{i}",
                value=None,
                ttl=300,
                priority=i,
                warming_strategy=WarmingStrategy.EAGER
            )
            for i in range(1, 6)
        ]
        
        # Warm cache
        results = await self.warmer.warm_cache(entries)
        print(f"Cache warming results: {results}")
        
        # Verify warmed entries
        for i in range(1, 6):
            key = f"user:{i}"
            value = self.client.get(key)
            if value:
                print(f"  {key}: Warmed successfully")
            else:
                print(f"  {key}: Not found")
                
        # Get warming stats
        stats = self.warmer.get_stats()
        print(f"\nWarming Statistics:")
        print(f"  Total warmed: {stats['total_warmed']}")
        print(f"  Failed warmings: {stats['failed_warmings']}")
        print(f"  Average warming time: {stats['average_warming_time_ms']:.2f}ms")
        
    async def test_decorated_caching(self):
        """Test decorator-based caching"""
        print("\n=== Testing Decorated Caching ===")
        
        @redis_cache(key_prefix="compute", ttl=60)
        def expensive_computation(n: int) -> int:
            """Simulate expensive computation"""
            print(f"  Computing factorial({n})...")
            result = 1
            for i in range(1, n + 1):
                result *= i
            return result
            
        # First call - will compute
        result1 = expensive_computation(10)
        print(f"First call result: {result1}")
        
        # Second call - should use cache
        result2 = expensive_computation(10)
        print(f"Second call result: {result2} (from cache)")
        
        # Different argument - will compute
        result3 = expensive_computation(5)
        print(f"Different argument result: {result3}")
        
    async def test_async_operations(self):
        """Test async Redis operations"""
        print("\n=== Testing Async Operations ===")
        
        from core.redis import get_async_redis_client
        async_client = get_async_redis_client()
        
        # Async set/get
        key = "test:async:1"
        value = {"async": True, "timestamp": time.time()}
        
        success = await async_client.set(key, value, expire=300)
        print(f"Async set: {'Success' if success else 'Failed'}")
        
        retrieved = await async_client.get(key)
        print(f"Async get: {retrieved}")
        
        # Cleanup
        await async_client.close()
        
    async def run_all_tests(self):
        """Run all resilience tests"""
        print("=== Redis Resilience Test Suite ===")
        print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
        
        try:
            await self.test_basic_operations()
            await self.test_circuit_breaker()
            await self.test_fallback_mechanism()
            await self.test_health_monitoring()
            await self.test_cache_warming()
            await self.test_decorated_caching()
            await self.test_async_operations()
            
            print("\n=== All Tests Completed ===")
            
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
            
        finally:
            # Cleanup
            if self.monitor:
                self.monitor.stop_monitoring()
            if self.client:
                self.client.close()


async def main():
    """Main entry point"""
    demo = RedisResilienceDemo()
    await demo.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())