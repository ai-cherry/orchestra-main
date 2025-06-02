"""Tests for the multi-layer cache system."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import aioredis
import asyncpg
import pytest

from factory_integration.cache_manager import (
    CacheEntry,
    CacheManager,
    CacheMetrics,
    L1Cache,
    L2Cache,
    L3Cache,
    create_cache_manager,
)

class TestCacheEntry:
    """Test cases for CacheEntry model."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(key="test_key", value={"data": "test"})

        assert entry.key == "test_key"
        assert entry.value == {"data": "test"}
        assert entry.access_count == 0
        assert entry.created_at > 0
        assert entry.last_accessed > 0
        assert entry.expires_at is None

class TestCacheMetrics:
    """Test cases for CacheMetrics model."""

    def test_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        metrics = CacheMetrics(
            l1_hits=50,
            l1_misses=10,
            l2_hits=30,
            l2_misses=5,
            l3_hits=10,
            l3_misses=5,
            total_requests=100,
        )

        assert metrics.hit_rate == 90.0  # (50+30+10)/100 * 100
        assert metrics.l1_hit_rate == pytest.approx(83.33, rel=0.01)  # 50/60 * 100

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests."""
        metrics = CacheMetrics()
        assert metrics.hit_rate == 0.0
        assert metrics.l1_hit_rate == 0.0

class TestL1Cache:
    """Test cases for L1 in-memory cache."""

    @pytest.fixture
    def l1_cache(self):
        """Create an L1 cache instance."""
        return L1Cache(max_size=3, ttl=1)

    async def test_set_and_get(self, l1_cache):
        """Test basic set and get operations."""
        await l1_cache.set("key1", {"value": 1})
        result = await l1_cache.get("key1")

        assert result == {"value": 1}
        assert l1_cache.hits == 1
        assert l1_cache.misses == 0

    async def test_get_nonexistent(self, l1_cache):
        """Test getting a non-existent key."""
        result = await l1_cache.get("nonexistent")

        assert result is None
        assert l1_cache.hits == 0
        assert l1_cache.misses == 1

    async def test_ttl_expiration(self, l1_cache):
        """Test TTL expiration."""
        await l1_cache.set("key1", "value1", ttl=0.1)

        # Should exist immediately
        assert await l1_cache.get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired
        assert await l1_cache.get("key1") is None

    async def test_lru_eviction(self, l1_cache):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        await l1_cache.set("key1", "value1")
        await l1_cache.set("key2", "value2")
        await l1_cache.set("key3", "value3")

        # Access key1 to make it recently used
        await l1_cache.get("key1")

        # Add new key, should evict key2 (least recently used)
        await l1_cache.set("key4", "value4")

        assert await l1_cache.get("key1") == "value1"  # Still exists
        assert await l1_cache.get("key2") is None  # Evicted
        assert await l1_cache.get("key3") == "value3"  # Still exists
        assert await l1_cache.get("key4") == "value4"  # New key

    async def test_delete(self, l1_cache):
        """Test deleting a key."""
        await l1_cache.set("key1", "value1")

        # Delete existing key
        assert await l1_cache.delete("key1") is True
        assert await l1_cache.get("key1") is None

        # Delete non-existent key
        assert await l1_cache.delete("nonexistent") is False

    async def test_clear(self, l1_cache):
        """Test clearing the cache."""
        await l1_cache.set("key1", "value1")
        await l1_cache.set("key2", "value2")

        await l1_cache.clear()

        assert len(l1_cache.cache) == 0
        assert l1_cache.hits == 0
        assert l1_cache.misses == 0

    def test_get_metrics(self, l1_cache):
        """Test getting cache metrics."""
        metrics = l1_cache.get_metrics()

        assert metrics["size"] == 0
        assert metrics["max_size"] == 3
        assert metrics["hits"] == 0
        assert metrics["misses"] == 0
        assert metrics["hit_rate"] == 0.0

class TestL2Cache:
    """Test cases for L2 Redis cache."""

    @pytest.fixture
    async def mock_redis(self):
        """Create a mock Redis client."""
        redis = AsyncMock(spec=aioredis.Redis)
        redis.get.return_value = None
        redis.setex.return_value = None
        redis.set.return_value = None
        redis.delete.return_value = 0
        redis.scan_iter.return_value.__aiter__.return_value = []
        return redis

    @pytest.fixture
    async def l2_cache(self, mock_redis):
        """Create an L2 cache instance with mock Redis."""
        cache = L2Cache("redis://localhost:6379", ttl=60)
        cache.redis = mock_redis
        return cache

    async def test_connect_disconnect(self):
        """Test Redis connection lifecycle."""
        with patch("factory_integration.cache_manager.aioredis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            cache = L2Cache("redis://localhost:6379")
            await cache.connect()

            assert cache.redis is not None
            mock_from_url.assert_called_once()

            await cache.disconnect()
            mock_redis.close.assert_called_once()

    async def test_get_hit(self, l2_cache, mock_redis):
        """Test cache hit."""
        mock_redis.get.return_value = json.dumps({"value": "test"})

        result = await l2_cache.get("key1")

        assert result == {"value": "test"}
        assert l2_cache.hits == 1
        assert l2_cache.misses == 0
        mock_redis.get.assert_called_once_with("factory:cache:key1")

    async def test_get_miss(self, l2_cache, mock_redis):
        """Test cache miss."""
        mock_redis.get.return_value = None

        result = await l2_cache.get("key1")

        assert result is None
        assert l2_cache.hits == 0
        assert l2_cache.misses == 1

    async def test_set_with_ttl(self, l2_cache, mock_redis):
        """Test setting value with TTL."""
        await l2_cache.set("key1", {"value": "test"}, ttl=30)

        mock_redis.setex.assert_called_once_with("factory:cache:key1", 30, json.dumps({"value": "test"}))

    async def test_set_without_ttl(self, l2_cache, mock_redis):
        """Test setting value without TTL (uses default)."""
        await l2_cache.set("key1", {"value": "test"})

        mock_redis.setex.assert_called_once_with("factory:cache:key1", 60, json.dumps({"value": "test"}))  # default TTL

    async def test_delete(self, l2_cache, mock_redis):
        """Test deleting a key."""
        mock_redis.delete.return_value = 1

        result = await l2_cache.delete("key1")

        assert result is True
        mock_redis.delete.assert_called_once_with("factory:cache:key1")

    async def test_clear_pattern(self, l2_cache, mock_redis):
        """Test clearing keys by pattern."""
        # Mock scan_iter to return some keys
        mock_redis.scan_iter.return_value.__aiter__.return_value = [
            "factory:cache:user:1",
            "factory:cache:user:2",
        ]
        mock_redis.delete.return_value = 2

        result = await l2_cache.clear_pattern("user:*")

        assert result == 2
        mock_redis.delete.assert_called_once_with("factory:cache:user:1", "factory:cache:user:2")

    async def test_error_handling(self, l2_cache, mock_redis):
        """Test error handling in Redis operations."""
        mock_redis.get.side_effect = Exception("Redis error")

        result = await l2_cache.get("key1")

        assert result is None
        assert l2_cache.misses == 1

class TestL3Cache:
    """Test cases for L3 PostgreSQL cache."""

    @pytest.fixture
    async def mock_db_pool(self):
        """Create a mock database pool."""
        pool = AsyncMock(spec=asyncpg.Pool)
        conn = AsyncMock()
        pool.acquire.return_value.__aenter__.return_value = conn
        pool.acquire.return_value.__aexit__.return_value = None
        return pool

    @pytest.fixture
    async def l3_cache(self, mock_db_pool):
        """Create an L3 cache instance."""
        cache = L3Cache(mock_db_pool, cleanup_interval=60)
        await cache.start()
        yield cache
        await cache.stop()

    async def test_get_hit(self, l3_cache, mock_db_pool):
        """Test cache hit from PostgreSQL."""
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = {"value": {"test": "data"}, "expires_at": None}

        result = await l3_cache.get("key1")

        assert result == {"test": "data"}
        assert l3_cache.hits == 1
        assert l3_cache.misses == 0
        assert conn.execute.called  # Access count update

    async def test_get_miss(self, l3_cache, mock_db_pool):
        """Test cache miss from PostgreSQL."""
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = None

        result = await l3_cache.get("key1")

        assert result is None
        assert l3_cache.hits == 0
        assert l3_cache.misses == 1

    async def test_set(self, l3_cache, mock_db_pool):
        """Test setting value in PostgreSQL."""
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value

        await l3_cache.set("key1", {"test": "data"}, ttl=3600)

        conn.execute.assert_called_once()
        call_args = conn.execute.call_args[0]
        assert "INSERT INTO factory_cache_entries" in call_args[0]
        assert call_args[1] == "key1"
        assert json.loads(call_args[2]) == {"test": "data"}

    async def test_delete(self, l3_cache, mock_db_pool):
        """Test deleting from PostgreSQL."""
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.execute.return_value = "DELETE 1"

        result = await l3_cache.delete("key1")

        assert result is True
        conn.execute.assert_called_once()

    async def test_cleanup_expired(self, l3_cache, mock_db_pool):
        """Test cleaning up expired entries."""
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.execute.return_value = "DELETE 5"

        result = await l3_cache.cleanup_expired()

        assert result == 5
        conn.execute.assert_called_once()

    async def test_cleanup_loop(self, l3_cache):
        """Test that cleanup loop runs."""
        # Mock cleanup_expired
        l3_cache.cleanup_expired = AsyncMock(return_value=0)

        # Let cleanup loop run once
        await asyncio.sleep(0.1)

        # Stop the cache
        await l3_cache.stop()

        # Cleanup task should be cancelled
        assert l3_cache._cleanup_task.cancelled()

class TestCacheManager:
    """Test cases for the unified CacheManager."""

    @pytest.fixture
    async def cache_manager(self, mock_db_pool):
        """Create a CacheManager instance."""
        with patch("factory_integration.cache_manager.aioredis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            config = {
                "l1": {"max_size": 10, "ttl": 60},
                "l2": {"redis_url": "redis://localhost:6379", "ttl": 300},
                "l3": {"db_pool": mock_db_pool, "cleanup_interval": 3600},
            }

            manager = CacheManager(
                l1_config=config["l1"],
                l2_config=config["l2"],
                l3_config=config["l3"],
            )

            # Mock Redis for L2
            manager.l2.redis = mock_redis

            await manager.start()
            yield manager
            await manager.stop()

    async def test_read_through_l1_hit(self, cache_manager):
        """Test read-through with L1 hit."""
        # Set value in L1
        await cache_manager.l1.set("key1", {"value": "l1"})

        result = await cache_manager.get("key1")

        assert result == {"value": "l1"}
        assert cache_manager.metrics.l1_hits == 1
        assert cache_manager.metrics.l2_hits == 0
        assert cache_manager.metrics.l3_hits == 0

    async def test_read_through_l2_hit(self, cache_manager):
        """Test read-through with L2 hit."""
        # Mock L2 to return value
        cache_manager.l2.get = AsyncMock(return_value={"value": "l2"})

        result = await cache_manager.get("key1")

        assert result == {"value": "l2"}
        assert cache_manager.metrics.l1_misses == 1
        assert cache_manager.metrics.l2_hits == 1
        assert cache_manager.metrics.l3_hits == 0

        # Value should be populated in L1
        assert await cache_manager.l1.get("key1") == {"value": "l2"}

    async def test_read_through_l3_hit(self, cache_manager):
        """Test read-through with L3 hit."""
        # Mock L2 miss and L3 hit
        cache_manager.l2.get = AsyncMock(return_value=None)
        cache_manager.l3.get = AsyncMock(return_value={"value": "l3"})

        result = await cache_manager.get("key1")

        assert result == {"value": "l3"}
        assert cache_manager.metrics.l1_misses == 1
        assert cache_manager.metrics.l2_misses == 1
        assert cache_manager.metrics.l3_hits == 1

        # Value should be populated in L1 and L2
        assert await cache_manager.l1.get("key1") == {"value": "l3"}

    async def test_read_through_all_miss(self, cache_manager):
        """Test read-through with all layers missing."""
        # Mock all misses
        cache_manager.l2.get = AsyncMock(return_value=None)
        cache_manager.l3.get = AsyncMock(return_value=None)

        result = await cache_manager.get("key1")

        assert result is None
        assert cache_manager.metrics.l1_misses == 1
        assert cache_manager.metrics.l2_misses == 1
        assert cache_manager.metrics.l3_misses == 1

    async def test_write_through(self, cache_manager):
        """Test write-through to all layers."""
        # Mock L2 and L3 set methods
        cache_manager.l2.set = AsyncMock()
        cache_manager.l3.set = AsyncMock()

        await cache_manager.set("key1", {"value": "test"}, ttl=300)

        # Verify all layers were written to
        assert await cache_manager.l1.get("key1") == {"value": "test"}
        cache_manager.l2.set.assert_called_once_with("key1", {"value": "test"}, 300)
        cache_manager.l3.set.assert_called_once_with("key1", {"value": "test"}, 300)

    async def test_delete_all_layers(self, cache_manager):
        """Test deleting from all layers."""
        # Set value in L1
        await cache_manager.l1.set("key1", "value1")

        # Mock L2 and L3 delete
        cache_manager.l2.delete = AsyncMock(return_value=True)
        cache_manager.l3.delete = AsyncMock(return_value=True)

        await cache_manager.delete("key1")

        # Verify all layers were deleted from
        assert await cache_manager.l1.get("key1") is None
        cache_manager.l2.delete.assert_called_once_with("key1")
        cache_manager.l3.delete.assert_called_once_with("key1")

    async def test_invalidate_pattern(self, cache_manager):
        """Test pattern-based invalidation."""
        # Mock L2 clear_pattern
        cache_manager.l2.clear_pattern = AsyncMock(return_value=5)

        await cache_manager.invalidate_pattern("user:*")

        # L1 should be cleared
        assert len(cache_manager.l1.cache) == 0

        # L2 pattern clear should be called
        cache_manager.l2.clear_pattern.assert_called_once_with("user:*")

    async def test_warm_cache(self, cache_manager):
        """Test cache warming."""
        # Mock L3 to return values
        cache_manager.l3.get = AsyncMock()
        cache_manager.l3.get.side_effect = [
            {"value": "warm1"},
            {"value": "warm2"},
            None,  # Third key not in L3
        ]

        # Mock L2 get to return None (force L3 lookup)
        cache_manager.l2.get = AsyncMock(return_value=None)

        await cache_manager.warm_cache(["key1", "key2", "key3"])

        # Verify keys were warmed in L1
        assert await cache_manager.l1.get("key1") == {"value": "warm1"}
        assert await cache_manager.l1.get("key2") == {"value": "warm2"}
        assert await cache_manager.l1.get("key3") is None

    async def test_get_metrics(self, cache_manager):
        """Test getting comprehensive metrics."""
        # Perform some operations
        await cache_manager.set("key1", "value1")
        await cache_manager.get("key1")  # L1 hit
        await cache_manager.get("key2")  # All miss

        metrics = await cache_manager.get_metrics()

        assert metrics["overall"]["total_requests"] == 2
        assert metrics["overall"]["hit_rate"] == 50.0  # 1 hit, 1 miss
        assert metrics["target_hit_rate"] == 85.0
        assert metrics["meets_target"] is False
        assert "l1" in metrics
        assert "l2" in metrics
        assert "l3" in metrics

    async def test_warm_cache_loop(self, cache_manager, mock_db_pool):
        """Test background cache warming loop."""
        # Mock database response for frequently accessed keys
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetch.return_value = [
            {"key": "frequent1"},
            {"key": "frequent2"},
        ]

        # Mock warm_cache method
        cache_manager.warm_cache = AsyncMock()

        # Trigger warm cache loop manually
        await cache_manager._warm_cache_loop()

        # Should not call warm_cache immediately (waits 5 minutes)
        cache_manager.warm_cache.assert_not_called()

class TestCreateCacheManager:
    """Test the factory function."""

    async def test_create_cache_manager(self, mock_db_pool):
        """Test creating cache manager with factory function."""
        with patch("factory_integration.cache_manager.aioredis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis

            config = {
                "l1": {"max_size": 100, "ttl": 300},
                "l2": {"redis_url": "redis://localhost:6379", "ttl": 3600},
                "l3": {"db_pool": mock_db_pool, "cleanup_interval": 86400},
            }

            manager = await create_cache_manager(config)

            assert isinstance(manager, CacheManager)
            assert manager._running is True

            await manager.stop()
