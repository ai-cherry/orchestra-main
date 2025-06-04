# TODO: Consider adding connection pooling configuration
"""
"""
    """Test configuration management."""
        """Test default settings."""
            "os.environ",
            {
                "SECRET_KEY": "test-secret",
                "MONGODB_URI": "mongodb://localhost",
                "DRAGONFLY_URI": "redis://localhost",
                "WEAVIATE_URL": "http://localhost:8080",
                "WEAVIATE_API_KEY": "test-key",
            },
        ):
            settings = Settings()

            assert settings.environment == Environment.DEV
            assert settings.app_name == "Cherry AI"
            assert settings.debug is False
            assert settings.api.port == 8080

    def test_environment_detection(self):
        """Test environment detection."""
            "os.environ",
            {
                "ENVIRONMENT": "prod",
                "SECRET_KEY": "test-secret",
                "MONGODB_URI": "mongodb://localhost",
                "DRAGONFLY_URI": "redis://localhost",
                "WEAVIATE_URL": "http://localhost:8080",
                "WEAVIATE_API_KEY": "test-key",
            },
        ):
            settings = Settings()
            assert settings.environment == Environment.PROD
            assert settings.is_production is True
            assert settings.is_development is False

class TestServiceRegistry:
    """Test service registry."""
        """Test registering and retrieving services."""
        registry.register_service("test_service", mock_service)

        # Retrieve service
        service = registry.get_service("test_service")
        assert service is mock_service

        # Check health
        health_results = await registry.health_check_all()
        assert "test_service" in health_results
        assert health_results["test_service"].status == ServiceStatus.HEALTHY

class TestEventBus:
    """Test event bus functionality."""
        """Test basic publish/subscribe."""
        event_bus.subscribe("test.event", handler)

        # Publish event
        await event_bus.publish("test.event", {"message": "Hello"})

        # Check event was received
        assert len(received_events) == 1
        assert received_events[0].name == "test.event"
        assert received_events[0].data["message"] == "Hello"

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test wildcard event subscription."""
        event_bus.subscribe("*", handler)

        # Publish different events
        await event_bus.publish("event.one", {"id": 1})
        await event_bus.publish("event.two", {"id": 2})

        # Check both events were received
        assert len(received_events) == 2
        assert received_events[0].name == "event.one"
        assert received_events[1].name == "event.two"

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test event priority ordering."""
            execution_order.append("high")

        async def normal_priority_handler(event: Event):
            execution_order.append("normal")

        async def low_priority_handler(event: Event):
            execution_order.append("low")

        event_bus.subscribe("test.event", low_priority_handler, priority=EventPriority.LOW)
        event_bus.subscribe("test.event", high_priority_handler, priority=EventPriority.HIGH)
        event_bus.subscribe("test.event", normal_priority_handler, priority=EventPriority.NORMAL)

        # Publish event
        await event_bus.publish("test.event", {})

        # Check execution order (high -> normal -> low)
        assert execution_order == ["high", "normal", "low"]

    def test_event_history(self):
        """Test event history tracking."""
            event_bus.publish_sync(f"event.{i}", {"index": i})

        # Check history (should only have last 5)
        history = event_bus.get_event_history()
        assert len(history) == 5
        assert history[0].name == "event.5"
        assert history[-1].name == "event.9"

    def test_statistics(self):
        """Test event bus statistics."""
        event_bus.subscribe("test.event", handler)

        # Publish events
        event_bus.publish_sync("test.event", {})
        event_bus.publish_sync("test.event", {})

        # Check stats
        stats = event_bus.get_stats()
        assert stats["events_published"] == 2
        assert stats["events_handled"] == 2
        assert stats["total_handlers"] == 1
        assert "test.event" in stats["event_types"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
