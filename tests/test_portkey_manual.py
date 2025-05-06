"""
Manual test script for Portkey integration.

This script demonstrates how to use the Portkey integration with Redis client
in a real-world scenario.

Usage:
    python -m tests.test_portkey_manual

Requirements:
    - Redis server running (or use the mock option)
    - Portkey API key set as PORTKEY_API_KEY environment variable
"""

import os
import asyncio
import json
from datetime import datetime
import unittest.mock as mock

# Check if we should use mock mode (no real Redis or Portkey API calls)
USE_MOCK = os.environ.get("USE_MOCK", "true").lower() == "true"

# Create mock classes
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


class MockRedisModule:
    def __init__(self):
        self.Redis = MockRedis
        
    class RedisError(Exception):
        pass

class MockPortkeyModule:
    def __init__(self):
        self.Portkey = MockPortkeyClient
        
    class exceptions:
        class PortkeyError(Exception):
            pass

# Create a mock PortkeyManager for the refactored Redis client
class MockPortkeyManager:
    """Mock implementation of PortkeyManager for testing."""
    
    def __init__(self, api_key=None, cache_ttl=3600):
        self._client = MockPortkeyClient(api_key=api_key)
        self._cache_ttl = cache_ttl
    
    async def setup_config(self, strategy="fallback", fallbacks=None, cache_enabled=True):
        """Configure Portkey settings."""
        self._client.set_strategy(strategy)
        if fallbacks:
            self._client.set_fallbacks(fallbacks)
        if cache_enabled:
            self._client.enable_cache(ttl=self._cache_ttl)
        return True
    
    async def semantic_cache_get(self, query, cache_key=None):
        """Get from semantic cache."""
        return self._client.get_from_cache(prompt=query, cache_key=cache_key)
    
    async def semantic_cache_store(self, query, response, cache_key=None, ttl=None):
        """Store in semantic cache."""
        return self._client.store_in_cache(
            prompt=query, 
            response=response, 
            cache_key=cache_key,
            ttl=ttl or self._cache_ttl
        )
    
    async def clear_cache(self):
        """Clear cache."""
        return self._client.clear_cache()
        
    def is_initialized(self):
        """Check if initialized."""
        return self._client is not None
        
    async def close(self):
        """Close resources."""
        return True
            

# Apply patches if in mock mode
if USE_MOCK:
    print("Running in mock mode (no real Redis or Portkey API calls)")
    
    # Create mock modules
    mock_redis = MockRedisModule()
    mock_portkey = MockPortkeyModule()
    
    # Apply patches
    redis_patch = mock.patch('packages.shared.src.storage.redis_client.redis', mock_redis)
    redis_class_patch = mock.patch('packages.shared.src.storage.redis_client.Redis', MockRedis)
    
    # Patch the PortkeyManager import
    portkey_manager_patch = mock.patch('packages.shared.src.storage.redis_client.PortkeyManager', MockPortkeyManager)
    
    # Start patches
    redis_patch.start()
    redis_class_patch.start()
    portkey_manager_patch.start()

# Import after patching
from packages.shared.src.storage.redis_client import RedisClient


async def test_portkey_features():
    """Test the Portkey features with the Redis client."""
    # Get API key from environment
    api_key = os.environ.get("PORTKEY_API_KEY", "test_api_key" if USE_MOCK else None)
    
    if not api_key and not USE_MOCK:
        print("Error: PORTKEY_API_KEY environment variable not set")
        return
    
    # Initialize Redis client with Portkey enabled
    print("\n1. Initializing Redis client with Portkey")
    redis_client = RedisClient(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        use_portkey=True,
        portkey_api_key=api_key,
        portkey_cache_ttl=3600
    )
    
    print(f"Portkey enabled: {await redis_client.is_portkey_enabled()}")
    
    # Configure Portkey
    print("\n2. Configuring Portkey with fallback strategy")
    fallbacks = [
        {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "api_key": os.environ.get("OPENAI_API_KEY", "test_api_key_1")
        },
        {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "api_key": os.environ.get("ANTHROPIC_API_KEY", "test_api_key_2")
        }
    ]
    
    await redis_client.setup_portkey_config(
        strategy="fallback",
        fallbacks=fallbacks,
        cache_enabled=True
    )
    print("Portkey configured successfully")
    
    # Test semantic cache operations
    print("\n3. Testing semantic cache operations")
    test_query = "What is the capital of France?"
    test_response = {
        "answer": "The capital of France is Paris.",
        "timestamp": datetime.now().isoformat()
    }
    
    # Check for cache hit (should be a miss first time)
    cached = await redis_client.portkey_semantic_cache(query=test_query)
    if cached:
        print("Cache hit (unexpected):", cached)
    else:
        print("Cache miss (expected for first query)")
    
    # Store in semantic cache
    print("\nStoring response in semantic cache")
    result = await redis_client.portkey_store_semantic_cache(
        query=test_query,
        response=test_response
    )
    print(f"Store result: {result}")
    
    # Should be a cache hit now
    print("\nChecking cache again")
    cached = await redis_client.portkey_semantic_cache(query=test_query)
    if cached:
        print("Cache hit (expected):", cached)
    else:
        print("Cache miss (unexpected)")
    
    # Slightly different query should still match semantically
    print("\nTesting with slightly different query")
    similar_query = "Tell me the capital city of France?"
    cached = await redis_client.portkey_semantic_cache(query=similar_query)
    if cached:
        print("Semantic match found (expected):", cached)
    else:
        print("No semantic match (only expected if using real Portkey API)")
    
    # Clear cache
    print("\n4. Clearing semantic cache")
    result = await redis_client.clear_portkey_cache()
    print(f"Cache cleared: {result}")
    
    # Should be a miss again
    print("\nChecking cache after clearing")
    cached = await redis_client.portkey_semantic_cache(query=test_query)
    if cached:
        print("Cache hit (unexpected):", cached)
    else:
        print("Cache miss (expected after clearing)")
    
    # Test standard Redis operations
    print("\n5. Testing standard Redis operations with Portkey enabled")
    await redis_client.set_cache("test_key", "test_value")
    result = await redis_client.get_cache("test_key")
    print(f"Redis get result: {result}")
    
    # Test JSON operations
    print("\nTesting JSON operations")
    test_data = {"name": "test", "value": 123, "timestamp": datetime.now().isoformat()}
    await redis_client.set_json("test_json", test_data)
    result = await redis_client.get_json("test_json")
    print(f"Redis JSON result: {result}")
    
    # Clean up
    print("\n6. Cleaning up")
    await redis_client.delete_cache("test_key")
    await redis_client.delete_cache("test_json")
    await redis_client.close()
    print("Test completed successfully")


if __name__ == "__main__":
    try:
        asyncio.run(test_portkey_features())
    finally:
        # Stop patches if in mock mode
        if USE_MOCK:
            redis_patch.stop()
            redis_class_patch.stop()
            portkey_manager_patch.stop()