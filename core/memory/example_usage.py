# TODO: Consider adding connection pooling configuration
"""
"""
    """Demonstrate basic memory operations."""
    logger.info("=== Basic Usage Example ===")
    
    # Initialize memory manager with default config
    memory = UnifiedMemoryManager()
    await memory.initialize()
    
    try:

    
        pass
        # Store some data
        await memory.set("user:123", {"name": "John Doe", "age": 30})
        await memory.set("config:app", {"theme": "dark", "language": "en"})
        await memory.set("cache:products", ["laptop", "phone", "tablet"], ttl_seconds=300)
        
        # Retrieve data
        user_data = await memory.get("user:123")
        logger.info(f"Retrieved user data: {user_data}")
        
        # Check existence
        exists = await memory.exists("user:123")
        logger.info(f"Key exists: {exists}")
        
        # Delete data
        deleted = await memory.delete("cache:products")
        logger.info(f"Deleted: {deleted}")
        
        # Get system stats
        stats = await memory.get_stats()
        logger.info(f"Memory stats: {json.dumps(stats, indent=2)}")
        
    finally:
        await memory.close()

async def advanced_tier_management():
    """Demonstrate advanced tier management features."""
    logger.info("=== Advanced Tier Management ===")
    
    # Create custom configuration
    config = MemoryConfig(
        environment=Environment.PRODUCTION,
        optimization={
            "enabled": True,
            "optimization_interval_seconds": 30,
            "tier_promotion_threshold": 5,
            "tier_demotion_threshold": 300,
            "prefetch_enabled": True,
            "prefetch_threshold": 0.7,
            "prefetch_limit": 10,
        }
    )
    
    memory = UnifiedMemoryManager(config)
    await memory.initialize()
    
    try:

    
        pass
        # Store data with tier hints
        await memory.set(
            "hot:data",
            {"status": "active", "count": 1000},
            tier_hint=MemoryTier.L1_PROCESS_MEMORY
        )
        
        await memory.set(
            "cold:archive",
            {"year": 2020, "data": "historical"},
            tier_hint=MemoryTier.L3_POSTGRESQL
        )
        
        # Simulate access patterns to trigger tier changes
        for i in range(10):
            # Frequently access hot data
            await memory.get("hot:data")
            await asyncio.sleep(0.1)
        
        # Run optimization manually
        optimization_results = await memory.optimize()
        logger.info(f"Optimization results: {optimization_results}")
        
        # Check where items are stored
        stats = await memory.get_stats()
        for tier, tier_stats in stats["tiers"].items():
            logger.info(f"Tier {tier}: {tier_stats.get('total_items', 0)} items")
        
    finally:
        await memory.close()

async def batch_operations_example():
    """Demonstrate batch operations for efficiency."""
    logger.info("=== Batch Operations Example ===")
    
    memory = UnifiedMemoryManager()
    await memory.initialize()
    
    try:

    
        pass
        # Prepare batch operations
        from core.memory.interfaces import MemoryOperation
        
        operations = [
            MemoryOperation(
                operation_type="set",
                key=f"batch:item:{i}",
                value={"index": i, "data": f"value_{i}"},
                ttl_seconds=3600
            )
            for i in range(100)
        ]
        
        # Execute batch
        results = await memory.batch_operations(operations)
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch set: {success_count}/{len(operations)} successful")
        
        # Batch get
        get_operations = [
            MemoryOperation(
                operation_type="get",
                key=f"batch:item:{i}"
            )
            for i in range(0, 100, 10)  # Get every 10th item
        ]
        
        get_results = await memory.batch_operations(get_operations)
        for i, result in enumerate(get_results):
            if result.success:
                logger.info(f"Retrieved batch item {i*10}: {result.value}")
        
    finally:
        await memory.close()

async def search_and_analytics():
    """Demonstrate search and analytics capabilities."""
    logger.info("=== Search and Analytics ===")
    
    memory = UnifiedMemoryManager()
    await memory.initialize()
    
    try:

    
        pass
        # Store various data types
        test_data = [
            ("product:laptop:1", {"name": "ThinkPad", "price": 1200, "category": "electronics"}),
            ("product:laptop:2", {"name": "MacBook", "price": 2000, "category": "electronics"}),
            ("product:phone:1", {"name": "iPhone", "price": 999, "category": "electronics"}),
            ("user:premium:1", {"name": "Alice", "tier": "premium", "joined": "2023-01-01"}),
            ("user:basic:1", {"name": "Bob", "tier": "basic", "joined": "2024-01-01"}),
        ]
        
        for key, value in test_data:
            await memory.set(key, value)
        
        # Search by pattern
        laptop_items = await memory.search(pattern="product:laptop:*", limit=10)
        logger.info(f"Found {len(laptop_items)} laptop items")
        
        # Search with metadata filter
        premium_users = await memory.search(
            pattern="user:*",
            metadata_filter={"tier": "premium"},
            limit=10
        )
        logger.info(f"Found {len(premium_users)} premium users")
        
        # Get metrics
        metrics = await memory.metrics.get_current_metrics()
        logger.info(f"Current metrics: {json.dumps(metrics, indent=2)}")
        
    finally:
        await memory.close()

async def performance_monitoring():
    """Demonstrate performance monitoring and alerting."""
    logger.info("=== Performance Monitoring ===")
    
    # Enable detailed metrics
    config = MemoryConfig(
        metrics={
            "enabled": True,
            "prometheus_enabled": True,
            "export_interval_seconds": 10,
        }
    )
    
    memory = UnifiedMemoryManager(config)
    await memory.initialize()
    
    try:

    
        pass
        # Set alert thresholds
        await memory.metrics.set_alert_threshold("latency_p99", 100)  # 100ms
        await memory.metrics.set_alert_threshold("error_rate", 0.01)   # 1%
        
        # Simulate various operations
        for i in range(100):
            key = f"perf:test:{i}"
            
            # Write
            start = asyncio.get_event_loop().time()
            await memory.set(key, {"index": i, "timestamp": datetime.utcnow().isoformat()})
            write_latency = (asyncio.get_event_loop().time() - start) * 1000
            
            # Read
            start = asyncio.get_event_loop().time()
            await memory.get(key)
            read_latency = (asyncio.get_event_loop().time() - start) * 1000
            
            if i % 10 == 0:
                logger.info(f"Operation {i}: write={write_latency:.2f}ms, read={read_latency:.2f}ms")
        
        # Export metrics
        metrics = await memory.metrics.export_metrics()
        logger.info("Performance Summary:")
        logger.info(f"- Total operations: {metrics['totals']['operations']}")
        logger.info(f"- Hit rate: {metrics['rates']['hit_rate']:.2%}")
        logger.info(f"- Error rate: {metrics['rates']['error_rate']:.2%}")
        
        # Check for alerts
        alerts = await memory.metrics.get_alerts()
        if alerts:
            logger.warning(f"Active alerts: {alerts}")
        
        # Get Prometheus metrics (if available)
        prom_metrics = await memory.metrics.get_prometheus_metrics()
        if prom_metrics:
            logger.info("Prometheus metrics available for export")
        
    finally:
        await memory.close()

async def error_handling_example():
    """Demonstrate error handling and recovery."""
    logger.info("=== Error Handling Example ===")
    
    memory = UnifiedMemoryManager()
    await memory.initialize()
    
    try:

    
        pass
        # Try to get non-existent key
        value = await memory.get("non:existent:key", default="NOT_FOUND")
        logger.info(f"Non-existent key returned: {value}")
        
        # Try to store very large value (might fail depending on tier)
        large_data = "x" * (10 * 1024 * 1024)  # 10MB string
        try:

            pass
            await memory.set("large:data", large_data)
            logger.info("Successfully stored large data")
        except Exception:

            pass
            logger.error(f"Failed to store large data: {e}")
        
        # Test TTL expiration
        await memory.set("temp:key", "temporary", ttl_seconds=2)
        logger.info("Stored temporary key")
        
        # Wait for expiration
        await asyncio.sleep(3)
        expired_value = await memory.get("temp:key", default="EXPIRED")
        logger.info(f"Expired key returned: {expired_value}")
        
        # Cleanup expired items
        cleaned = await memory.cleanup()
        logger.info(f"Cleaned up {cleaned} expired items")
        
    finally:
        await memory.close()

async def main():
    """Run all examples."""
            logger.error(f"Example {example.__name__} failed: {e}")
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())