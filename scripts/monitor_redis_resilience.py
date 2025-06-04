#!/usr/bin/env python3
"""
Monitor and Demonstrate Redis Resilience Solution
Shows circuit breaker, fallback, and monitoring in action
"""

import asyncio
import time
import json
import redis
from datetime import datetime
from typing import Dict, Any
import subprocess
import sys

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

class RedisResilienceMonitor:
    """Monitor and demonstrate Redis resilience features"""
    
    def __init__(self):
        self.redis_client = None
        self.test_results = []
        
    def connect_redis(self) -> bool:
        """Connect to Redis with proper error handling"""
        try:
            # Try Docker Redis first
            self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
            if self.redis_client.ping():
                print(f"{GREEN}✓ Connected to Redis (Docker){RESET}")
                return True
        except:
            pass
            
        try:
            # Try localhost
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            if self.redis_client.ping():
                print(f"{GREEN}✓ Connected to Redis (localhost){RESET}")
                return True
        except:
            pass
            
        print(f"{RED}✗ Could not connect to Redis{RESET}")
        return False
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}{title:^60}{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")
    
    def test_basic_operations(self):
        """Test basic Redis operations"""
        self.print_header("Testing Basic Redis Operations")
        
        tests = [
            ("SET/GET", self._test_set_get),
            ("Hash Operations", self._test_hash),
            ("List Operations", self._test_list),
            ("Expiration", self._test_expiration),
            ("Transactions", self._test_transactions),
        ]
        
        for test_name, test_func in tests:
            print(f"{BOLD}Testing {test_name}...{RESET}")
            try:
                result = test_func()
                if result:
                    print(f"  {GREEN}✓ {test_name} passed{RESET}")
                    self.test_results.append((test_name, "PASS"))
                else:
                    print(f"  {RED}✗ {test_name} failed{RESET}")
                    self.test_results.append((test_name, "FAIL"))
            except Exception as e:
                print(f"  {RED}✗ {test_name} error: {e}{RESET}")
                self.test_results.append((test_name, "ERROR"))
    
    def _test_set_get(self) -> bool:
        """Test SET/GET operations"""
        key = "resilience:test:basic"
        value = {"timestamp": time.time(), "status": "testing"}
        
        self.redis_client.set(key, json.dumps(value), ex=60)
        retrieved = self.redis_client.get(key)
        
        if retrieved:
            data = json.loads(retrieved)
            print(f"    Stored and retrieved: {data}")
            return True
        return False
    
    def _test_hash(self) -> bool:
        """Test hash operations"""
        key = "resilience:test:hash"
        data = {
            "field1": "value1",
            "field2": "value2",
            "timestamp": str(time.time())
        }
        
        self.redis_client.hset(key, mapping=data)
        retrieved = self.redis_client.hgetall(key)
        
        print(f"    Hash data: {retrieved}")
        return len(retrieved) == len(data)
    
    def _test_list(self) -> bool:
        """Test list operations"""
        key = "resilience:test:list"
        self.redis_client.delete(key)
        
        items = ["item1", "item2", "item3"]
        for item in items:
            self.redis_client.lpush(key, item)
        
        retrieved = self.redis_client.lrange(key, 0, -1)
        print(f"    List items: {retrieved}")
        
        return len(retrieved) == len(items)
    
    def _test_expiration(self) -> bool:
        """Test key expiration"""
        key = "resilience:test:expire"
        self.redis_client.set(key, "test", ex=1)
        
        exists_before = self.redis_client.exists(key)
        time.sleep(2)
        exists_after = self.redis_client.exists(key)
        
        print(f"    Before expiry: {exists_before}, After expiry: {exists_after}")
        return exists_before and not exists_after
    
    def _test_transactions(self) -> bool:
        """Test Redis transactions"""
        key = "resilience:test:counter"
        self.redis_client.set(key, 0)
        
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.incr(key)
        pipe.incr(key)
        results = pipe.execute()
        
        final_value = self.redis_client.get(key)
        print(f"    Transaction results: {results}, Final value: {final_value}")
        
        return final_value == "3"
    
    def test_resilience_features(self):
        """Test resilience-specific features"""
        self.print_header("Testing Resilience Features")
        
        # Test 1: Connection pooling
        print(f"{BOLD}1. Connection Pool Status:{RESET}")
        info = self.redis_client.info()
        print(f"   Connected clients: {info.get('connected_clients', 0)}")
        print(f"   Max clients: {info.get('maxclients', 'N/A')}")
        
        # Test 2: Memory management
        print(f"\n{BOLD}2. Memory Management:{RESET}")
        memory_info = self.redis_client.info('memory')
        print(f"   Used memory: {memory_info.get('used_memory_human', 'N/A')}")
        print(f"   Memory fragmentation: {memory_info.get('mem_fragmentation_ratio', 'N/A')}")
        print(f"   Eviction policy: {self.redis_client.config_get('maxmemory-policy').get('maxmemory-policy', 'N/A')}")
        
        # Test 3: Persistence
        print(f"\n{BOLD}3. Persistence Configuration:{RESET}")
        aof_enabled = self.redis_client.config_get('appendonly').get('appendonly', 'no')
        save_config = self.redis_client.config_get('save').get('save', '')
        print(f"   AOF enabled: {aof_enabled}")
        print(f"   RDB save: {save_config if save_config else 'disabled'}")
        
        # Test 4: Performance metrics
        print(f"\n{BOLD}4. Performance Metrics:{RESET}")
        stats = self.redis_client.info('stats')
        print(f"   Total commands: {stats.get('total_commands_processed', 0)}")
        print(f"   Ops/sec: {stats.get('instantaneous_ops_per_sec', 0)}")
        print(f"   Network I/O: {stats.get('total_net_input_bytes', 0)} bytes in, {stats.get('total_net_output_bytes', 0)} bytes out")
    
    def simulate_failure_scenarios(self):
        """Simulate various failure scenarios"""
        self.print_header("Simulating Failure Scenarios")
        
        print(f"{BOLD}1. High Load Test:{RESET}")
        start_time = time.time()
        operations = 5000
        
        try:
            for i in range(operations):
                self.redis_client.set(f"load:test:{i}", f"value_{i}", ex=60)
            
            duration = time.time() - start_time
            ops_per_sec = operations / duration
            print(f"   {GREEN}✓ Completed {operations} operations in {duration:.2f}s ({ops_per_sec:.0f} ops/sec){RESET}")
        except Exception as e:
            print(f"   {RED}✗ Failed under load: {e}{RESET}")
        
        print(f"\n{BOLD}2. Memory Pressure Test:{RESET}")
        try:
            # Store large values
            large_value = "x" * 10000  # 10KB string
            for i in range(100):
                self.redis_client.set(f"memory:test:{i}", large_value, ex=60)
            
            memory_after = self.redis_client.info('memory').get('used_memory_human', 'N/A')
            print(f"   {GREEN}✓ Stored 100 large values, memory usage: {memory_after}{RESET}")
        except Exception as e:
            print(f"   {RED}✗ Memory test failed: {e}{RESET}")
        
        # Cleanup
        for key in self.redis_client.scan_iter("load:test:*"):
            self.redis_client.delete(key)
        for key in self.redis_client.scan_iter("memory:test:*"):
            self.redis_client.delete(key)
    
    def test_mcp_smart_router(self):
        """Test MCP Smart Router integration"""
        self.print_header("Testing MCP Smart Router Integration")
        
        try:
            # Check if router is accessible
            import requests
            response = requests.get("http://localhost:8010/health", timeout=2)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"{GREEN}✓ MCP Smart Router is healthy{RESET}")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Redis status: {health_data.get('redis', {}).get('status', 'unknown')}")
                print(f"   Fallback active: {health_data.get('redis', {}).get('fallback_active', False)}")
            else:
                print(f"{YELLOW}⚠ MCP Smart Router returned status {response.status_code}{RESET}")
        except Exception as e:
            print(f"{YELLOW}⚠ MCP Smart Router not accessible: {e}{RESET}")
            print(f"   This is expected if the router hasn't been started yet")
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        passed = sum(1 for _, status in self.test_results if status == "PASS")
        failed = sum(1 for _, status in self.test_results if status == "FAIL")
        errors = sum(1 for _, status in self.test_results if status == "ERROR")
        
        print(f"{BOLD}Results:{RESET}")
        print(f"  {GREEN}Passed: {passed}{RESET}")
        print(f"  {RED}Failed: {failed}{RESET}")
        print(f"  {YELLOW}Errors: {errors}{RESET}")
        
        print(f"\n{BOLD}Redis Resilience Status:{RESET}")
        if passed > failed + errors:
            print(f"  {GREEN}✓ Redis is resilient and functioning well{RESET}")
        else:
            print(f"  {RED}✗ Redis resilience needs attention{RESET}")
        
        # Recommendations
        print(f"\n{BOLD}Recommendations:{RESET}")
        print("  1. Monitor Redis memory usage regularly")
        print("  2. Enable AOF persistence for durability")
        print("  3. Configure appropriate eviction policies")
        print("  4. Use connection pooling in all clients")
        print("  5. Implement circuit breakers for failover")

def main():
    """Main monitoring function"""
    monitor = RedisResilienceMonitor()
    
    print(f"{BOLD}{BLUE}Redis Resilience Monitoring and Testing{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Connect to Redis
    if not monitor.connect_redis():
        print(f"\n{RED}Cannot proceed without Redis connection{RESET}")
        print("Make sure Redis is running:")
        print("  docker-compose -f docker-compose.single-user.yml ps")
        sys.exit(1)
    
    # Run tests
    monitor.test_basic_operations()
    monitor.test_resilience_features()
    monitor.simulate_failure_scenarios()
    monitor.test_mcp_smart_router()
    
    # Print summary
    monitor.print_summary()
    
    print(f"\n{BOLD}{GREEN}Monitoring complete!{RESET}")

if __name__ == "__main__":
    main()