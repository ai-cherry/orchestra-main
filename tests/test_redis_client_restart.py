"""
Test script for Redis client start and restart functionality.

This script validates that the Redis client correctly handles:
1. Initial connection 
2. Graceful shutdown
3. Reconnection behavior
4. Error handling during reconnection attempts

Usage:
    python -m tests.test_redis_client_restart

Requirements:
    - Redis server running (or use the mock option)
    - Optional: Portkey API key set as PORTKEY_API_KEY environment variable
"""

import os
import time
import asyncio
import unittest.mock as mock
from typing import Optional, Dict

# Set mock mode (no real Redis/Portkey API calls unless explicitly turned off)
USE_MOCK = os.environ.get("USE_MOCK", "true").lower() == "true"

# Import mock classes from the test_portkey_manual.py to keep consistency
if USE_MOCK:
    from tests.test_portkey_manual import (
        MockRedisModule, 
        MockRedis, 
        MockPortkeyManager,
        redis_patch, 
        redis_class_patch, 
        portkey_manager_patch
    )

    # Start patches
    redis_patch.start()
    redis_class_patch.start()
    portkey_manager_patch.start()

# Import after patching
from packages.shared.src.storage.redis_client import RedisClient


class ConnectionTestInfo:
    """Track connection test information."""
    
    def __init__(self):
        self.init_count = 0
        self.close_count = 0
        self.recovery_attempts = 0
        self.current_errors = []
        self.portkey_init_count = 0
        self.portkey_close_count = 0
    
    def reset(self):
        """Reset counters."""
        self.__init__()
    
    def __str__(self):
        """String representation."""
        return (
            f"ConnectionTestInfo:\n"
            f"  Redis init count: {self.init_count}\n"
            f"  Redis close count: {self.close_count}\n"
            f"  Portkey init count: {self.portkey_init_count}\n"
            f"  Portkey close count: {self.portkey_close_count}\n"
            f"  Recovery attempts: {self.recovery_attempts}\n"
            f"  Current errors: {', '.join(self.current_errors) if self.current_errors else 'None'}"
        )


# Create a global test info object to track connection events
test_info = ConnectionTestInfo()


async def test_basic_start_stop():
    """Test basic start and stop functionality."""
    print("\n=== Testing Basic Start/Stop ===")
    
    # Create a fresh client
    client = RedisClient(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        use_portkey=False
    )
    
    # Store some data
    print("Setting test data")
    await client.set_cache("start_stop_test", "hello_world", ttl=60)
    
    # Verify data was stored
    value = await client.get_cache("start_stop_test")
    print(f"Stored value: {value}")
    assert value == "hello_world", "Failed to store and retrieve data"
    
    # Close the client
    print("Closing client")
    await client.close()
    print("Client closed successfully")
    
    # Create a new client to verify reconnection works
    print("\nReconnecting with a new client")
    client2 = RedisClient(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        use_portkey=False
    )
    
    # Verify we can still access the data
    value = await client2.get_cache("start_stop_test")
    print(f"Retrieved value after reconnect: {value}")
    assert value == "hello_world", "Failed to retrieve data after reconnection"
    
    # Cleanup
    await client2.delete_cache("start_stop_test")
    await client2.close()
    print("Basic start/stop test completed successfully")


async def test_portkey_integration_restart():
    """Test Portkey integration with restart."""
    print("\n=== Testing Portkey Integration Restart ===")
    
    # Skip this test if not using mock mode and no Portkey API key
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not USE_MOCK and not api_key:
        print("Skipping Portkey integration test (no API key available)")
        return
    
    # Create client with Portkey enabled
    client = RedisClient(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        use_portkey=True,
        portkey_api_key=api_key or "test_api_key"
    )
    
    # Verify Portkey is enabled
    portkey_enabled = await client.is_portkey_enabled()
    print(f"Portkey enabled: {portkey_enabled}")
    assert portkey_enabled, "Portkey should be enabled"
    
    # Configure Portkey
    await client.setup_portkey_config(
        strategy="fallback",
        fallbacks=[{"provider": "openai", "model": "gpt-4"}],
        cache_enabled=True
    )
    print("Portkey configured successfully")
    
    # Store a test entry in Portkey semantic cache
    test_query = "What color is the sky?"
    test_response = {"answer": "The sky is blue."}
    
    result = await client.portkey_store_semantic_cache(
        query=test_query,
        response=test_response
    )
    assert result, "Failed to store in semantic cache"
    
    # Verify cache entry
    cached = await client.portkey_semantic_cache(query=test_query)
    assert cached is not None, "Failed to retrieve from semantic cache"
    print("Verified semantic cache entry")
    
    # Close the client
    print("Closing client with Portkey enabled")
    await client.close()
    
    # Create a new client
    print("Reconnecting with a new client")
    client2 = RedisClient(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        use_portkey=True,
        portkey_api_key=api_key or "test_api_key"
    )
    
    # Reconfigure Portkey
    await client2.setup_portkey_config(
        strategy="fallback",
        fallbacks=[{"provider": "openai", "model": "gpt-4"}],
        cache_enabled=True
    )
    print("Portkey reconfigured successfully")
    
    # Verify we can still access the cache
    cached = await client2.portkey_semantic_cache(query=test_query)
    if cached is not None:
        print("Retrieved cache entry after reconnect")
    else:
        print("Note: Cache entry not found after restart (expected with real Portkey)")
        
    # Clear cache and close
    await client2.clear_portkey_cache()
    await client2.close()
    print("Portkey integration restart test completed")


async def test_error_handling():
    """Test error handling during connection failures."""
    print("\n=== Testing Error Handling ===")
    
    if not USE_MOCK:
        print("Error handling tests require mock mode, skipping")
        return
    
    # Patch the Redis class to simulate connection failure
    original_redis = mock.MagicMock()
    
    # Replace the mock Redis with one that fails on connect
    class FailingRedis:
        def __init__(self, *args, **kwargs):
            test_info.init_count += 1
            test_info.current_errors.append("Connection refused")
            raise ConnectionError("Connection refused")
            
        async def close(self):
            test_info.close_count += 1
    
    with mock.patch('packages.shared.src.storage.redis_client.Redis', FailingRedis):
        try:
            # Try to create a client that will fail
            client = RedisClient(
                host="invalid_host",
                port=9999,
                use_portkey=False
            )
        except ConnectionError as e:
            print(f"Correctly caught connection error: {e}")
        else:
            assert False, "Should have raised ConnectionError"
    
    print("Error handling test completed successfully")


async def main():
    """Run all tests."""
    print("\n=== Redis Client Start/Restart Tests ===")
    print(f"Mock mode: {'Enabled' if USE_MOCK else 'Disabled'}")
    
    try:
        # Run the tests
        await test_basic_start_stop()
        await test_portkey_integration_restart()
        await test_error_handling()
        
        print("\n=== All tests completed successfully ===")
        print(test_info)
        
    except Exception as e:
        print(f"\n!!! Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    finally:
        # Stop patches if in mock mode
        if USE_MOCK:
            redis_patch.stop()
            redis_class_patch.stop()
            portkey_manager_patch.stop()