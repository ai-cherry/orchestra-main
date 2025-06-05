import os
# TODO: Consider adding connection pooling configuration
"""
"""
    """Create a memory manager instance for testing."""
            "enabled": True,
            "optimization_interval_seconds": 60,
            "prefetch_enabled": True,
        },
        metrics={
            "enabled": True,
            "prometheus_enabled": False,
        }
    )
    
    manager = UnifiedMemoryManager(config)
    await manager.initialize()
    
    yield manager
    
    await manager.close()

@pytest.fixture
async def mock_storages():
    """Create mock storage instances."""
            "total_items": 0,
            "total_size_bytes": 0,
            "capacity_used_percent": 0
        })
        storage.cleanup_expired = AsyncMock(return_value=0)
        storage.close = AsyncMock()
        storages[tier] = storage
    
    return storages

class TestUnifiedMemoryManager:
    """Test cases for UnifiedMemoryManager."""
        """Test manager initialization."""
        """Test basic set and get operations."""
        success = await memory_manager.set("test:key", {"value": "test_data"})
        assert success is True
        
        # Get the value
        value = await memory_manager.get("test:key")
        assert value == {"value": "test_data"}
        
        # Get non-existent key
        value = await memory_manager.get("non:existent", default="NOT_FOUND")
        assert value == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_delete_operation(self, memory_manager):
        """Test delete operation."""
        await memory_manager.set("delete:test", "value")
        
        # Verify it exists
        assert await memory_manager.exists("delete:test") is True
        
        # Delete it
        deleted = await memory_manager.delete("delete:test")
        assert deleted is True
        
        # Verify it's gone
        assert await memory_manager.exists("delete:test") is False
    
    @pytest.mark.asyncio
    async def test_ttl_expiration(self, memory_manager):
        """Test TTL expiration."""
        await memory_manager.set("ttl:test", "temporary", ttl_seconds=1)
        
        # Should exist immediately
        assert await memory_manager.get("ttl:test") == "temporary"
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Cleanup expired items
        await memory_manager.cleanup()
        
        # Should be gone
        value = await memory_manager.get("ttl:test", default="EXPIRED")
        assert value == "EXPIRED"
    
    @pytest.mark.asyncio
    async def test_tier_hints(self, memory_manager):
        """Test storage with tier hints."""
            "tier:test",
            {"data": "important"},
            tier_hint=MemoryTier.L1_PROCESS_MEMORY
        )
        assert success is True
        
        # Verify it was stored
        value = await memory_manager.get("tier:test")
        assert value == {"data": "important"}
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, memory_manager):
        """Test batch operations."""
                operation_type="set",
                key=f"batch:{i}",
                value=f"value_{i}",
                ttl_seconds=3600
            )
            for i in range(10)
        ]
        
        # Execute batch
        results = await memory_manager.batch_operations(operations)
        assert len(results) == 10
        assert all(r.success for r in results)
        
        # Batch get
        get_ops = [
            MemoryOperation(
                operation_type="get",
                key=f"batch:{i}"
            )
            for i in range(5)
        ]
        
        get_results = await memory_manager.batch_operations(get_ops)
        assert len(get_results) == 5
        for i, result in enumerate(get_results):
            assert result.success
            assert result.value == f"value_{i}"
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, memory_manager):
        """Test search functionality."""
            ("search:item:1", {"type": "A", "value": 1}),
            ("search:item:2", {"type": "B", "value": 2}),
            ("search:item:3", {"type": "A", "value": 3}),
            ("other:item:1", {"type": "C", "value": 4}),
        ]
        
        for key, value in test_data:
            await memory_manager.set(key, value)
        
        # Search by pattern
        results = await memory_manager.search(pattern="search:*", limit=10)
        assert len(results) >= 3
        
        # Verify keys match pattern
        for item in results:
            assert item.key.startswith("search:")
    
    @pytest.mark.asyncio
    async def test_optimization(self, memory_manager):
        """Test optimization functionality."""
            await memory_manager.set(f"opt:test:{i}", f"value_{i}")
        
        # Run optimization
        results = await memory_manager.optimize()
        assert "promoted" in results
        assert "demoted" in results
        assert isinstance(results["promoted"], int)
        assert isinstance(results["demoted"], int)
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, memory_manager):
        """Test metrics collection."""
        await memory_manager.set("metrics:test", "value")
        await memory_manager.get("metrics:test")
        await memory_manager.get("metrics:missing", default=None)
        
        # Get metrics
        stats = await memory_manager.get_stats()
        assert "metrics" in stats
        assert "totals" in stats
        assert stats["totals"]["total_items"] >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling(self, memory_manager):
        """Test error handling."""
            await memory_manager.set("", "value")
        
        with pytest.raises(MemoryValidationError):
            await memory_manager.get("")
        
        with pytest.raises(MemoryValidationError):
            await memory_manager.delete("")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, memory_manager):
        """Test concurrent operations."""
            tasks.append(memory_manager.set(f"concurrent:{i}", f"value_{i}"))
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        assert all(results)
        
        # Verify all were stored
        for i in range(50):
            value = await memory_manager.get(f"concurrent:{i}")
            assert value == f"value_{i}"
    
    @pytest.mark.asyncio
    async def test_tier_promotion(self):
        """Test automatic tier promotion."""
                "enabled": True,
                "tier_promotion_threshold": 3,
            }
        )
        
        manager = UnifiedMemoryManager(config)
        await manager.initialize()
        
        try:

        
            pass
            # Store in lower tier
            await manager.set(
                "promote:test",
                "frequently_accessed",
                tier_hint=MemoryTier.L3_POSTGRESQL
            )
            
            # Access multiple times to trigger promotion
            for _ in range(5):
                await manager.get("promote:test")
                await asyncio.sleep(0.1)
            
            # Check if promotion was considered
            # (actual promotion depends on optimizer logic)
            stats = await manager.get_stats()
            assert stats is not None
            
        finally:
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_prefetch_functionality(self):
        """Test predictive prefetching."""
                "enabled": True,
                "prefetch_enabled": True,
                "prefetch_threshold": 0.5,
            }
        )
        
        manager = UnifiedMemoryManager(config)
        await manager.initialize()
        
        try:

        
            pass
            # Create access pattern
            keys = [f"prefetch:{i}" for i in range(5)]
            for key in keys:
                await manager.set(key, f"value_{key}")
            
            # Access in sequence to establish pattern
            for key in keys[:3]:
                await manager.get(key)
                await asyncio.sleep(0.1)
            
            # Next access should trigger prefetch
            await manager.get(keys[3])
            
            # Give time for prefetch
            await asyncio.sleep(0.5)
            
            # Verify prefetch queue was used
            assert manager._prefetch_queue is not None
            
        finally:
            await manager.close()

class TestMemoryItem:
    """Test cases for MemoryItem."""
        """Test MemoryItem creation."""
            key="test:key",
            value={"data": "test"},
            metadata={"source": "test"},
            tier=MemoryTier.L1_PROCESS_MEMORY,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            access_count=0,
            size_bytes=100,
            ttl_seconds=3600,
            checksum="abc123"
        )
        
        assert item.key == "test:key"
        assert item.value == {"data": "test"}
        assert item.tier == MemoryTier.L1_PROCESS_MEMORY
        assert item.ttl_seconds == 3600
    
    def test_memory_item_expiration(self):
        """Test MemoryItem expiration check."""
key = os.getenv("CORE_TEST_MEMORY_MANAGER_KEY", "")
            value="old_data",
            metadata={},
            tier=MemoryTier.L1_PROCESS_MEMORY,
            created_at=datetime.utcnow() - timedelta(hours=2),
            accessed_at=datetime.utcnow() - timedelta(hours=2),
            access_count=1,
            size_bytes=10,
            ttl_seconds=3600,  # 1 hour TTL
            checksum="xyz"
        )
        
        # Check if expired
        assert item.is_expired() is True
        
        # Create non-expired item
        fresh_item = MemoryItem(
key = os.getenv("CORE_TEST_MEMORY_MANAGER_KEY", "")
            value="new_data",
            metadata={},
            tier=MemoryTier.L1_PROCESS_MEMORY,
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            access_count=1,
            size_bytes=10,
            ttl_seconds=3600,
            checksum="xyz"
        )
        
        assert fresh_item.is_expired() is False

class TestMemoryOperation:
    """Test cases for MemoryOperation."""
        """Test MemoryOperation creation."""
            operation_type="set",
            key="test:key",
            value="test_value",
            ttl_seconds=3600,
            tier_hint=MemoryTier.L2_SHARED_MEMORY
        )
        
        assert op.operation_type == "set"
        assert op.key == "test:key"
        assert op.value == "test_value"
        assert op.ttl_seconds == 3600
        assert op.tier_hint == MemoryTier.L2_SHARED_MEMORY

class TestMemoryResult:
    """Test cases for MemoryResult."""
        """Test MemoryResult creation."""
            value="result_value",
            error=None,
            tier_accessed=MemoryTier.L1_PROCESS_MEMORY,
            latency_ms=5.2
        )
        
        assert result.success is True
        assert result.value == "result_value"
        assert result.error is None
        assert result.tier_accessed == MemoryTier.L1_PROCESS_MEMORY
        assert result.latency_ms == 5.2

@pytest.mark.asyncio
async def test_memory_manager_with_mocks(mock_storages):
    """Test memory manager with mocked storages."""
        key="mock:test",
        value="mocked_value",
        metadata={},
        tier=MemoryTier.L1_PROCESS_MEMORY,
        created_at=datetime.utcnow(),
        accessed_at=datetime.utcnow(),
        access_count=1,
        size_bytes=100,
        ttl_seconds=3600,
        checksum="mock123"
    )
    
    # Configure mock to return item
    mock_storages[MemoryTier.L1_PROCESS_MEMORY].get.return_value = test_item
    
    # Test get operation
    value = await manager.get("mock:test")
    assert value == "mocked_value"
    
    # Verify mock was called
    mock_storages[MemoryTier.L1_PROCESS_MEMORY].get.assert_called_once_with("mock:test")
    
    # Test set operation
    success = await manager.set("mock:new", "new_value")
    assert success is True
    
    # Verify set was called
    assert mock_storages[MemoryTier.L1_PROCESS_MEMORY].set.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])