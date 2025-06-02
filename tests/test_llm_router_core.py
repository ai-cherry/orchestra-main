"""
Unit tests for core LLM router modules.

Tests cache manager, connection manager, health monitor, and routers.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from core.llm_types import UseCase, ModelTier, RouterConfig, ModelMapping
from core.cache_manager import CacheManager
from core.connection_manager import ConnectionManager, CircuitBreakerState
from core.health_monitor import HealthMonitor, HealthStatus
from core.llm_router_enhanced import UnifiedLLMRouter

class TestCacheManager:
    """Test cases for CacheManager"""

    @pytest.mark.asyncio
    async def test_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = CacheManager(max_size=10, memory_limit_mb=1)
        await cache.start()

        try:
            # Test set and get
            await cache.set("key1", "value1")
            assert await cache.get("key1") == "value1"

            # Test miss
            assert await cache.get("nonexistent") is None

            # Test delete
            await cache.delete("key1")
            assert await cache.get("key1") is None

            # Test metrics
            metrics = cache.get_metrics()
            assert metrics["hits"] == 1
            assert metrics["misses"] == 2

        finally:
            await cache.stop()

    @pytest.mark.asyncio
    async def test_cache_ttl(self):
        """Test cache TTL expiration"""
        cache = CacheManager(default_ttl=1)  # 1 second TTL
        await cache.start()

        try:
            await cache.set("key1", "value1")
            assert await cache.get("key1") == "value1"

            # Wait for expiration
            await asyncio.sleep(1.1)
            assert await cache.get("key1") is None

            metrics = cache.get_metrics()
            assert metrics["expirations"] == 1

        finally:
            await cache.stop()

    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Test cache eviction by size"""
        cache = CacheManager(max_size=3)
        await cache.start()

        try:
            # Fill cache
            for i in range(5):
                await cache.set(f"key{i}", f"value{i}")

            # First two should be evicted
            assert await cache.get("key0") is None
            assert await cache.get("key1") is None
            assert await cache.get("key2") == "value2"
            assert await cache.get("key3") == "value3"
            assert await cache.get("key4") == "value4"

            metrics = cache.get_metrics()
            assert metrics["evictions"] == 2

        finally:
            await cache.stop()

class TestConnectionManager:
    """Test cases for ConnectionManager"""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        """Test HTTP client creation"""
        manager = ConnectionManager()

        client = await manager.get_client(
            provider="test", base_url="https://api.test.com", headers={"Authorization": "Bearer test"}
        )

        assert client is not None
        assert "test" in manager._clients
        assert "test" in manager._circuit_breakers

        await manager.close()

    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        manager = ConnectionManager()

        # Create a client
        await manager.get_client("test", "https://api.test.com")

        # Simulate failures
        breaker = manager._circuit_breakers["test"]
        breaker.failure_count = 5  # Threshold
        breaker.is_open = True
        breaker.half_open_retry_time = time.time() + 60

        # Should raise exception when circuit is open
        with pytest.raises(Exception, match="Circuit breaker open"):
            async with manager.request("test", "GET", "/test"):
                pass

        assert manager.metrics["circuit_breaks"] == 1

        await manager.close()

    def test_circuit_breaker_state(self):
        """Test circuit breaker state transitions"""
        breaker = CircuitBreakerState(provider="test")

        assert not breaker.is_open
        assert breaker.failure_count == 0

        # Increment failures
        for _ in range(5):
            breaker.failure_count += 1

        # Should open after threshold
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.is_open = True
            breaker.half_open_retry_time = time.time() + 60

        assert breaker.is_open
        assert breaker.half_open_retry_time is not None

class TestHealthMonitor:
    """Test cases for HealthMonitor"""

    @pytest.mark.asyncio
    async def test_health_check_registration(self):
        """Test health check registration"""
        monitor = HealthMonitor(check_interval=60)
        await monitor.start()

        try:
            # Register a health check
            async def check_test():
                return True, None

            monitor.register_health_check("test", check_test)
            assert "test" in monitor._health_checks

        finally:
            await monitor.stop()

    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """Test provider health checking"""
        monitor = HealthMonitor()

        # Mock connection manager
        with patch("core.health_monitor.get_connection_manager") as mock_get_cm:
            mock_cm = AsyncMock()
            mock_get_cm.return_value = mock_cm

            # Simulate successful health check
            mock_cm.request.return_value.__aenter__.return_value = Mock()

            is_healthy, error = await monitor.check_provider_health("test", "/health")
            assert is_healthy
            assert error is None

    @pytest.mark.asyncio
    async def test_health_status_aggregation(self):
        """Test overall health status calculation"""
        monitor = HealthMonitor()
        await monitor.start()

        try:
            # Add some component statuses
            monitor._components["comp1"] = Mock(status=HealthStatus.HEALTHY)
            monitor._components["comp2"] = Mock(status=HealthStatus.HEALTHY)

            # Mock other dependencies
            with (
                patch("core.health_monitor.get_connection_manager") as mock_cm,
                patch("core.health_monitor.get_cache_manager") as mock_cache,
            ):

                mock_cm.return_value.get_metrics.return_value = {"requests": 100, "successes": 95, "success_rate": 0.95}

                mock_cache.return_value.get_metrics.return_value = {"hit_rate": 0.8}

                # Get health status
                health = await monitor.get_health_status()
                assert health.status == "healthy"

        finally:
            await monitor.stop()

class TestUnifiedLLMRouter:
    """Test cases for UnifiedLLMRouter"""

    @pytest.mark.asyncio
    async def test_model_mapping_retrieval(self):
        """Test getting model mappings"""
        config = RouterConfig(portkey_api_key="test_key", enable_caching=False)
        router = UnifiedLLMRouter(config)

        # Test standard mapping
        mapping = await router.get_model_mapping(UseCase.CODE_GENERATION, ModelTier.STANDARD)
        assert mapping.use_case == UseCase.CODE_GENERATION
        assert mapping.tier == ModelTier.STANDARD
        assert mapping.primary_model == "anthropic/claude-3-sonnet"

        # Test fallback to standard tier
        mapping = await router.get_model_mapping(UseCase.DOCUMENTATION, ModelTier.PREMIUM)
        assert mapping.tier == ModelTier.STANDARD  # Should fall back

        # Test ultimate fallback
        mapping = await router.get_model_mapping(UseCase.MEMORY_PROCESSING, ModelTier.PREMIUM)
        assert mapping is not None

    def test_custom_mapping(self):
        """Test adding custom mappings"""
        router = UnifiedLLMRouter()

        # Add custom mapping
        custom_mapping = ModelMapping(
            use_case=UseCase.DEBUGGING,
            tier=ModelTier.ECONOMY,
            primary_model="custom/model",
            fallback_models=["fallback/model"],
            max_tokens=1024,
            temperature=0.1,
        )

        router.add_custom_mapping(custom_mapping)

        # Verify it's used
        mapping = asyncio.run(router.get_model_mapping(UseCase.DEBUGGING, ModelTier.ECONOMY))
        assert mapping.primary_model == "custom/model"

        # Remove custom mapping
        router.remove_custom_mapping(UseCase.DEBUGGING, ModelTier.ECONOMY)

        # Should revert to default
        mapping = asyncio.run(router.get_model_mapping(UseCase.DEBUGGING, ModelTier.ECONOMY))
        assert mapping.primary_model != "custom/model"

    @pytest.mark.asyncio
    async def test_complete_with_mocks(self):
        """Test complete method with mocked dependencies"""
        config = RouterConfig(portkey_api_key="test_key", enable_caching=True)

        with (
            patch("core.llm_router_base.get_cache_manager") as mock_cache_mgr,
            patch("core.llm_router_base.get_connection_manager") as mock_conn_mgr,
            patch("core.llm_router_base.get_health_monitor") as mock_health,
        ):

            # Setup mocks
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None  # Cache miss
            mock_cache_mgr.return_value = mock_cache

            mock_conn = AsyncMock()
            mock_conn_mgr.return_value = mock_conn

            mock_health_monitor = AsyncMock()
            mock_health.return_value = mock_health_monitor

            # Mock the request
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "test-id",
                "model": "anthropic/claude-3-sonnet",
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"total_tokens": 100},
                "created": 1234567890,
            }

            mock_conn.request.return_value.__aenter__.return_value = mock_response

            # Create router and test
            router = UnifiedLLMRouter(config)
            await router.initialize()

            response = await router.complete("Test prompt", use_case=UseCase.CODE_GENERATION, tier=ModelTier.STANDARD)

            assert response.model == "anthropic/claude-3-sonnet"
            assert response.choices[0]["message"]["content"] == "Test response"
            assert response.usage["total_tokens"] == 100

            # Verify cache was checked and set
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()

class TestIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_router_lifecycle(self):
        """Test complete router lifecycle"""
        config = RouterConfig(portkey_api_key="test_key", enable_caching=True, enable_monitoring=True)

        with (
            patch("core.llm_router_base.get_cache_manager") as mock_cache_mgr,
            patch("core.llm_router_base.get_connection_manager") as mock_conn_mgr,
            patch("core.llm_router_base.get_health_monitor") as mock_health,
        ):

            # Setup minimal mocks
            mock_cache_mgr.return_value = AsyncMock()
            mock_conn_mgr.return_value = AsyncMock()
            mock_health.return_value = AsyncMock()

            router = UnifiedLLMRouter(config)

            # Test initialization
            await router.initialize()
            assert router._initialized

            # Test metrics
            metrics = router.get_metrics()
            assert metrics["requests"] == 0
            assert metrics["success_rate"] == 0

            # Test health status
            mock_health.return_value.get_detailed_status.return_value = {
                "overall": {"status": "healthy"},
                "components": {},
            }

            health = await router.get_health_status()
            assert health["overall"]["status"] == "healthy"

            # Test close
            await router.close()
            assert not router._initialized

            # Verify cleanup was called
            mock_cache_mgr.return_value.stop.assert_called_once()
            mock_conn_mgr.return_value.close.assert_called_once()
            mock_health.return_value.stop.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
