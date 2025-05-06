"""
Tests for the Portkey integration with Redis client.

This test suite validates that the Portkey integration
with our Redis client works correctly.
"""

import os
import json
import unittest
import asyncio
from unittest import mock
from datetime import datetime, timedelta

# Create the mock classes first
class MockPortkeyClient:
    """Mock implementation of Portkey client for testing."""
    
    def __init__(self, *args, **kwargs):
        self.strategy = "fallback"
        self.fallbacks = []
        self.cache_enabled = False
        self.cache_ttl = 3600
        self.cache_data = {}
    
    def set_strategy(self, strategy):
        """Set the strategy."""
        self.strategy = strategy
        return True
        
    def set_fallbacks(self, fallbacks):
        """Set fallback configurations."""
        self.fallbacks = fallbacks
        return True
        
    def enable_cache(self, ttl=3600):
        """Enable caching with TTL."""
        self.cache_enabled = True
        self.cache_ttl = ttl
        return True
        
    def get_from_cache(self, prompt, cache_key=None):
        """Get an item from cache."""
        key = cache_key or f"cache:{prompt}"
        return self.cache_data.get(key)
        
    def store_in_cache(self, prompt, response, cache_key=None, ttl=None):
        """Store an item in cache."""
        key = cache_key or f"cache:{prompt}"
        self.cache_data[key] = response
        return True
        
    def clear_cache(self):
        """Clear all cache."""
        self.cache_data = {}
        return True


class MockRedis:
    """Mock Redis client for testing."""
    
    def __init__(self, *args, **kwargs):
        self.data = {}
        self.hash_data = {}
        
    async def set(self, key, value, ex=None):
        """Set a key-value pair."""
        self.data[key] = value
        return True
        
    async def get(self, key):
        """Get a value by key."""
        return self.data.get(key)
        
    async def delete(self, key):
        """Delete a key."""
        if key in self.data:
            del self.data[key]
        return True
        
    async def hset(self, key, field, value):
        """Set a hash field."""
        if key not in self.hash_data:
            self.hash_data[key] = {}
        self.hash_data[key][field] = value
        return True
        
    async def hget(self, key, field):
        """Get a hash field."""
        if key not in self.hash_data:
            return None
        return self.hash_data[key].get(field)
        
    async def hgetall(self, key):
        """Get all hash fields."""
        return self.hash_data.get(key, {})
        
    async def close(self):
        """Close the connection."""
        return True


# Mock modules
mock_redis = mock.MagicMock()
mock_redis.Redis = MockRedis

mock_portkey = mock.MagicMock()
mock_portkey.Portkey = MockPortkeyClient
mock_portkey.exceptions = mock.MagicMock()
mock_portkey.exceptions.PortkeyError = Exception

# Mock PortkeyManager
class MockPortkeyManager:
    """Mock implementation of PortkeyManager for testing."""
    
    def __init__(self, api_key=None, cache_ttl=3600):
        self._api_key = api_key
        self._cache_ttl = cache_ttl
        self._client = MockPortkeyClient(api_key=api_key)
        
    async def setup_config(self, strategy, fallbacks=None, cache_enabled=True):
        """Configure Portkey settings."""
        self._client.set_strategy(strategy)
        if fallbacks:
            self._client.set_fallbacks(fallbacks)
        if cache_enabled:
            self._client.enable_cache(ttl=self._cache_ttl)
        return True
        
    async def semantic_cache_get(self, query, cache_key=None):
        """Get from semantic cache."""
        key = cache_key or f"cache:{query}"
        return self._client.get_from_cache(query, cache_key=key)
        
    async def semantic_cache_store(self, query, response, cache_key=None, ttl=None):
        """Store in semantic cache."""
        key = cache_key or f"cache:{query}"
        ttl = ttl or self._cache_ttl
        self._client.store_in_cache(query, response, cache_key=key, ttl=ttl)
        return True
        
    async def clear_cache(self):
        """Clear all cache."""
        self._client.clear_cache()
        return True
        
    def is_initialized(self):
        """Check if initialized."""
        return self._client is not None
        
    async def close(self):
        """Clean up resources."""
        pass

# Set up module patches
@mock.patch('packages.shared.src.storage.redis_client.redis', mock_redis)
@mock.patch('packages.shared.src.storage.redis_client.Redis', MockRedis)
@mock.patch('packages.shared.src.storage.redis_client.PortkeyManager', MockPortkeyManager)
@mock.patch('packages.shared.src.storage.redis_client.PortkeyError', Exception)
class TestPortkeyIntegration(unittest.TestCase):
    """Test suite for Portkey integration with Redis client."""
    
    def setUp(self):
        """Set up the test environment."""
        # Import within test to use the patched modules
        from packages.shared.src.storage.redis_client import RedisClient
        
        # Create a Redis client with Portkey enabled
        self.redis_client = RedisClient(
            host="localhost", 
            port=6379, 
            use_portkey=True,
            portkey_api_key="test_api_key",
            portkey_cache_ttl=3600
        )
        
    def tearDown(self):
        """Clean up resources."""
        # Run the close method to clean up resources
        asyncio.run(self.redis_client.close())
    
    def test_portkey_initialization(self):
        """Test that Portkey is correctly initialized."""
        # Check if Portkey is enabled
        self.assertTrue(self.redis_client._use_portkey)
        self.assertIsNotNone(self.redis_client._portkey_client)
        self.assertEqual(self.redis_client._portkey_api_key, "test_api_key")
        self.assertEqual(self.redis_client._portkey_cache_ttl, 3600)
    
    def test_portkey_config(self):
        """Test Portkey configuration."""
        # Configure Portkey with different settings
        fallbacks = [
            {"provider": "openai", "model": "gpt-4", "api_key": "test-key-1"},
            {"provider": "anthropic", "model": "claude-3-sonnet", "api_key": "test-key-2"}
        ]
        
        # Set configuration
        asyncio.run(self.redis_client.setup_portkey_config(
            strategy="loadbalance",
            fallbacks=fallbacks,
            cache_enabled=True
        ))
        
        # Check if configuration was set correctly
        portkey_client = self.redis_client._portkey_client
        self.assertEqual(portkey_client.strategy, "loadbalance")
        self.assertEqual(len(portkey_client.fallbacks), 2)
        self.assertTrue(portkey_client.cache_enabled)
        
    def test_semantic_cache_operations(self):
        """Test semantic cache operations with Portkey."""
        # Test data
        test_query = "What is the capital of France?"
        test_response = {"answer": "The capital of France is Paris."}
        cache_key = "test_semantic_key"
        
        # Cache miss first
        cached = asyncio.run(self.redis_client.portkey_semantic_cache(
            query=test_query,
            cache_key=cache_key
        ))
        self.assertIsNone(cached)
        
        # Store in cache
        result = asyncio.run(self.redis_client.portkey_store_semantic_cache(
            query=test_query,
            response=test_response,
            cache_key=cache_key
        ))
        self.assertTrue(result)
        
        # Cache hit now
        cached = asyncio.run(self.redis_client.portkey_semantic_cache(
            query=test_query,
            cache_key=cache_key
        ))
        self.assertEqual(cached, test_response)
        
        # Clear cache
        result = asyncio.run(self.redis_client.clear_portkey_cache())
        self.assertTrue(result)
        
        # Should be a miss again
        cached = asyncio.run(self.redis_client.portkey_semantic_cache(
            query=test_query,
            cache_key=cache_key
        ))
        self.assertIsNone(cached)
    
    def test_portkey_disabled_errors(self):
        """Test proper error handling when Portkey is disabled."""
        # Import within test to use the patched modules
        from packages.shared.src.storage.redis_client import RedisClient
        
        # Create a client with Portkey disabled
        client = RedisClient(host="localhost", port=6379, use_portkey=False)
        
        # Methods should raise RuntimeError
        with self.assertRaises(RuntimeError):
            asyncio.run(client.setup_portkey_config())
            
        with self.assertRaises(RuntimeError):
            asyncio.run(client.portkey_semantic_cache("test"))
            
        with self.assertRaises(RuntimeError):
            asyncio.run(client.portkey_store_semantic_cache("test", {}))
            
        with self.assertRaises(RuntimeError):
            asyncio.run(client.clear_portkey_cache())
    
    def test_is_portkey_enabled(self):
        """Test checking if Portkey is enabled."""
        # Import within test to use the patched modules
        from packages.shared.src.storage.redis_client import RedisClient
        
        # Create clients with Portkey enabled and disabled
        client_enabled = RedisClient(host="localhost", port=6379, use_portkey=True, portkey_api_key="test")
        client_disabled = RedisClient(host="localhost", port=6379, use_portkey=False)
        
        # Check status
        self.assertTrue(asyncio.run(client_enabled.is_portkey_enabled()))
        self.assertFalse(asyncio.run(client_disabled.is_portkey_enabled()))
    
    def test_standard_redis_with_portkey(self):
        """Test that standard Redis operations work with Portkey enabled."""
        # Test data
        test_key = "test_key"
        test_value = "test_value"
        test_json = {"name": "test", "value": 123}
        
        # Test Redis operations
        asyncio.run(self.redis_client.set_cache(test_key, test_value))
        result = asyncio.run(self.redis_client.get_cache(test_key))
        self.assertEqual(result, test_value)
        
        # Test JSON operations
        asyncio.run(self.redis_client.set_json(f"{test_key}_json", test_json))
        result = asyncio.run(self.redis_client.get_json(f"{test_key}_json"))
        self.assertEqual(result, test_json)
        
        # Test delete
        asyncio.run(self.redis_client.delete_cache(test_key))
        result = asyncio.run(self.redis_client.get_cache(test_key))
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
