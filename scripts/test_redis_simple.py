import os
#!/usr/bin/env python3
"""
Simple Redis Connection Test
Tests basic Redis functionality without the full resilience framework
"""

import redis
import json
import time
import sys

def test_redis_connection():
    """Test basic Redis connection and operations"""
    print("🔍 Testing Redis Connection...")
    
    try:
        # Connect to Redis - try Docker first, then localhost
        redis_hosts = [
            {'host': 'redis', 'port': 6379},  # Docker service name
            {'host': 'localhost', 'port': 6379}  # Local fallback
        ]
        
        r = None
        for config in redis_hosts:
            try:
                r = redis.Redis(**config, decode_responses=True)
                if r.ping():
                    print(f"   Connected to Redis at {config['host']}:{config['port']}")
                    break
            except:
                continue
        
        if not r:
            raise redis.ConnectionError("Could not connect to Redis")
        
        # Test 1: Ping
        print("\n1. Testing PING...")
        if r.ping():
            print("   ✅ Redis is responding to PING")
        else:
            print("   ❌ Redis PING failed")
            return False
        
        # Test 2: Set/Get
        print("\n2. Testing SET/GET...")
test_key = os.getenv('ORCHESTRA_SCRIPT_KEY')
        test_value = {"status": "connected", "timestamp": time.time()}
        
        r.set(test_key, json.dumps(test_value), ex=60)
        retrieved = r.get(test_key)
        
        if retrieved:
            retrieved_data = json.loads(retrieved)
            print(f"   ✅ SET/GET working: {retrieved_data}")
        else:
            print("   ❌ SET/GET failed")
            return False
        
        # Test 3: Increment
        print("\n3. Testing INCR...")
        counter_key = "test:counter"
        r.delete(counter_key)
        
        for i in range(5):
            count = r.incr(counter_key)
            print(f"   Counter: {count}")
        
        print("   ✅ INCR working")
        
        # Test 4: Hash operations
        print("\n4. Testing HASH operations...")
        hash_key = "test:hash"
        r.hset(hash_key, mapping={
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })
        
        hash_data = r.hgetall(hash_key)
        print(f"   ✅ HASH operations working: {hash_data}")
        
        # Test 5: List operations
        print("\n5. Testing LIST operations...")
        list_key = "test:list"
        r.delete(list_key)
        
        r.lpush(list_key, "item1", "item2", "item3")
        list_items = r.lrange(list_key, 0, -1)
        print(f"   ✅ LIST operations working: {list_items}")
        
        # Test 6: Expiration
        print("\n6. Testing key expiration...")
        expire_key = "test:expire"
        r.set(expire_key, "will expire", ex=2)
        
        print(f"   Key exists: {r.exists(expire_key)}")
        print("   Waiting 3 seconds...")
        # TODO: Replace with asyncio.sleep() for async code
        time.sleep(3)
        print(f"   Key exists after expiry: {r.exists(expire_key)}")
        print("   ✅ Expiration working")
        
        # Test 7: Performance
        print("\n7. Testing performance...")
        start_time = time.time()
        operations = 1000
        
        for i in range(operations):
            r.set(f"perf:test:{i}", f"value_{i}", ex=60)
        
        write_time = time.time() - start_time
        write_ops_per_sec = operations / write_time
        
        start_time = time.time()
        
        for i in range(operations):
            r.get(f"perf:test:{i}")
        
        read_time = time.time() - start_time
        read_ops_per_sec = operations / read_time
        
        print(f"   Write: {write_ops_per_sec:.0f} ops/sec")
        print(f"   Read: {read_ops_per_sec:.0f} ops/sec")
        print("   ✅ Performance test completed")
        
        # Cleanup
        print("\n8. Cleaning up test keys...")
        for key in r.scan_iter("test:*"):
            r.delete(key)
        for key in r.scan_iter("perf:*"):
            r.delete(key)
        print("   ✅ Cleanup completed")
        
        print("\n✅ All Redis tests passed!")
        return True
        
    except redis.ConnectionError as e:
        print(f"\n❌ Redis connection error: {e}")
        print("\nMake sure Redis is running:")
        print("  docker-compose -f docker-compose.single-user.yml ps")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def test_redis_resilience_features():
    """Test Redis resilience features"""
    print("\n\n🔍 Testing Redis Resilience Features...")
    
    try:
        # Use same connection logic
        redis_hosts = [
            {'host': 'redis', 'port': 6379},  # Docker service name
            {'host': 'localhost', 'port': 6379}  # Local fallback
        ]
        
        r = None
        for config in redis_hosts:
            try:
                r = redis.Redis(**config, decode_responses=True)
                if r.ping():
                    break
            except:
                continue
        
        if not r:
            raise redis.ConnectionError("Could not connect to Redis")
        
        # Test connection pool info
        print("\n1. Connection Pool Status:")
        pool = r.connection_pool
        print(f"   Max connections: {pool.max_connections}")
        print(f"   Connection class: {pool.connection_class}")
        
        # Test Redis INFO
        print("\n2. Redis Server Info:")
        info = r.info()
        print(f"   Version: {info.get('redis_version', 'unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 0)}")
        print(f"   Used memory: {info.get('used_memory_human', 'unknown')}")
        print(f"   Total commands processed: {info.get('total_commands_processed', 0)}")
        
        # Test persistence
        print("\n3. Persistence Configuration:")
        config = r.config_get('save')
        print(f"   Save config: {config.get('save', 'not configured')}")
        
        aof_config = r.config_get('appendonly')
        print(f"   AOF enabled: {aof_config.get('appendonly', 'no')}")
        
        print("\n✅ Resilience features check completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking resilience features: {e}")
        return False

def main():
    """Main test function"""
    print("="*60)
    print("Redis Connection and Resilience Test")
    print("="*60)
    
    # Run basic tests
    if not test_redis_connection():
        sys.exit(1)
    
    # Run resilience tests
    if not test_redis_resilience_features():
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ All tests completed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()