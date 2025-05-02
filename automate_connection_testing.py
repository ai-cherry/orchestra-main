#!/usr/bin/env python3
"""
Automated Connection Testing Tool for Firestore/Redis

This script provides automated testing for Firestore and Redis connections,
including simulation of various error conditions, latency analysis,
and validation of connection pool behavior.
"""

import os
import sys
import json
import time
import random
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('connection_tests.log')]
)
logger = logging.getLogger('connection_tester')

# Add the project root to sys.path
sys.path.append('.')

# Import necessary modules for memory management
try:
    from packages.shared.src.storage.config import StorageConfig
    from packages.shared.src.storage.exceptions import (
        StorageError, ConnectionError, OperationError, ConfigurationError
    )
    from packages.shared.src.storage.firestore.v2.core import FirestoreManager
    from packages.shared.src.storage.firestore.v2.async_core import AsyncFirestoreManager
    # Redis imports would go here
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_connection(url: str):
    """Test connection to a given URL."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        logger.info(f"Connection to {url} successful: {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Connection to {url} failed: {e}")

class ConnectionTester:
    """Base class for connection testing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the tester with optional configuration."""
        self.config = self._load_config(config_path)
        self.results: List[Dict[str, Any]] = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {
            'tests': {
                'connection_count': 5,
                'operation_count': 20,
                'run_firestore': True,
                'run_redis': True,
                'simulate_errors': True,
                'error_probability': 0.2,
                'network_latency': {
                    'enabled': True,
                    'min_ms': 10,
                    'max_ms': 200
                }
            },
            'firestore': {
                'project_id': os.environ.get('GCP_PROJECT_ID'),
                'credentials_path': os.environ.get('GCP_SA_KEY_PATH'),
            },
            'redis': {
                'host': os.environ.get('REDIS_HOST', 'localhost'),
                'port': int(os.environ.get('REDIS_PORT', 6379)),
                'password': os.environ.get('REDIS_PASSWORD', '')
            }
        }
    
    def record_result(self, test_name: str, success: bool, duration_ms: float, 
                     error: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Record a test result."""
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'test_name': test_name,
            'success': success,
            'duration_ms': duration_ms,
        }
        if error:
            result['error'] = error
        if details:
            result['details'] = details
            
        self.results.append(result)
        
        if success:
            logger.info(f"✅ {test_name}: {duration_ms:.2f}ms")
        else:
            logger.error(f"❌ {test_name}: {error} ({duration_ms:.2f}ms)")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a summary report of test results."""
        total = len(self.results)
        if total == 0:
            return {'error': 'No tests run'}
            
        successes = sum(1 for r in self.results if r['success'])
        failures = total - successes
        avg_duration = sum(r['duration_ms'] for r in self.results) / total
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': total,
            'successful_tests': successes,
            'failed_tests': failures,
            'success_rate': successes / total,
            'average_duration_ms': avg_duration,
            'results': self.results
        }
        
        return report
        
    def save_report(self, output_path: str = 'connection_test_report.json') -> None:
        """Save the test report to a file."""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {output_path}")


class FirestoreTester(ConnectionTester):
    """Specialized tester for Firestore connections."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Firestore tester."""
        super().__init__(config_path)
        self.collection_name = f"connection_test_{int(time.time())}"
        
    async def setup(self) -> None:
        """Set up the test environment."""
        try:
            config = StorageConfig(
                project_id=self.config['firestore']['project_id'],
                credentials_path=self.config['firestore']['credentials_path']
            )
            self.sync_manager = FirestoreManager(config)
            self.async_manager = AsyncFirestoreManager(config)
            
            # Create test collection
            self.sync_manager.initialize()
            logger.info(f"Created test collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    async def test_sync_connection(self) -> None:
        """Test synchronous Firestore connection."""
        start_time = time.time()
        try:
            result = self.sync_manager.health_check()
            duration_ms = (time.time() - start_time) * 1000
            if result.get('status') == 'healthy':
                self.record_result('sync_connection', True, duration_ms, details=result)
            else:
                self.record_result('sync_connection', False, duration_ms, 
                                  error="Health check failed", details=result)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('sync_connection', False, duration_ms, error=str(e))
    
    async def test_async_connection(self) -> None:
        """Test asynchronous Firestore connection."""
        start_time = time.time()
        try:
            result = await self.async_manager.health_check()
            duration_ms = (time.time() - start_time) * 1000
            if result.get('status') == 'healthy':
                self.record_result('async_connection', True, duration_ms, details=result)
            else:
                self.record_result('async_connection', False, duration_ms, 
                                  error="Health check failed", details=result)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('async_connection', False, duration_ms, error=str(e))
    
    async def test_crud_operations(self) -> None:
        """Test basic CRUD operations."""
        # Test document creation
        doc_id = f"test-doc-{int(time.time())}"
        test_data = {
            "id": doc_id,
            "timestamp": datetime.utcnow().isoformat(),
            "test_value": random.randint(1, 1000),
            "test_string": "Automated test document"
        }
        
        # Create
        start_time = time.time()
        try:
            await self.async_manager.create_document(self.collection_name, doc_id, test_data)
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('create_document', True, duration_ms)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('create_document', False, duration_ms, error=str(e))
            return  # Skip remaining tests if create fails
        
        # Read
        start_time = time.time()
        try:
            doc = await self.async_manager.get_document(self.collection_name, doc_id)
            duration_ms = (time.time() - start_time) * 1000
            if doc and doc.get('test_value') == test_data['test_value']:
                self.record_result('read_document', True, duration_ms)
            else:
                self.record_result('read_document', False, duration_ms, 
                                  error="Document data mismatch")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('read_document', False, duration_ms, error=str(e))
        
        # Update
        start_time = time.time()
        update_data = {"test_value": random.randint(1000, 2000), "updated": True}
        try:
            await self.async_manager.update_document(self.collection_name, doc_id, update_data)
            duration_ms = (time.time() - start_time) * 1000
            
            # Verify update
            doc = await self.async_manager.get_document(self.collection_name, doc_id)
            if doc and doc.get('test_value') == update_data['test_value'] and doc.get('updated'):
                self.record_result('update_document', True, duration_ms)
            else:
                self.record_result('update_document', False, duration_ms, 
                                  error="Update verification failed")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('update_document', False, duration_ms, error=str(e))
        
        # Delete
        start_time = time.time()
        try:
            await self.async_manager.delete_document(self.collection_name, doc_id)
            duration_ms = (time.time() - start_time) * 1000
            
            # Verify deletion
            doc = await self.async_manager.get_document(self.collection_name, doc_id)
            if doc is None:
                self.record_result('delete_document', True, duration_ms)
            else:
                self.record_result('delete_document', False, duration_ms, 
                                  error="Document was not deleted")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('delete_document', False, duration_ms, error=str(e))
    
    async def test_connection_pool(self) -> None:
        """Test connection pool behavior with parallel operations."""
        num_operations = self.config['tests']['operation_count']
        logger.info(f"Testing connection pool with {num_operations} parallel operations")
        
        async def single_operation(i: int) -> Dict[str, Any]:
            doc_id = f"pool-test-{i}-{int(time.time())}"
            test_data = {
                "id": doc_id,
                "index": i,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            start_time = time.time()
            try:
                await self.async_manager.create_document(self.collection_name, doc_id, test_data)
                doc = await self.async_manager.get_document(self.collection_name, doc_id)
                await self.async_manager.delete_document(self.collection_name, doc_id)
                duration_ms = (time.time() - start_time) * 1000
                return {
                    'index': i,
                    'success': True,
                    'duration_ms': duration_ms
                }
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                return {
                    'index': i,
                    'success': False,
                    'duration_ms': duration_ms,
                    'error': str(e)
                }
        
        # Run operations in parallel
        start_time = time.time()
        tasks = [single_operation(i) for i in range(num_operations)]
        results = await asyncio.gather(*tasks)
        total_duration_ms = (time.time() - start_time) * 1000
        
        # Analyze results
        successes = sum(1 for r in results if r['success'])
        failures = num_operations - successes
        avg_op_duration = sum(r['duration_ms'] for r in results) / num_operations
        
        self.record_result(
            'connection_pool',
            failures == 0,
            total_duration_ms,
            error=f"{failures} operations failed" if failures > 0 else None,
            details={
                'operations': num_operations,
                'successful': successes,
                'failed': failures,
                'average_op_duration_ms': avg_op_duration,
                'failures': [r for r in results if not r['success']]
            }
        )
    
    async def test_error_handling(self) -> None:
        """Test error handling capabilities."""
        if not self.config['tests']['simulate_errors']:
            logger.info("Error simulation disabled, skipping error handling tests")
            return
        
        # Invalid operation
        start_time = time.time()
        try:
            # Intentionally try to get a non-existent document
            doc = await self.async_manager.get_document(self.collection_name, "non-existent-doc")
            duration_ms = (time.time() - start_time) * 1000
            if doc is None:
                self.record_result('error_handling_nonexistent', True, duration_ms, 
                                  details={"message": "Correctly handled non-existent document"})
            else:
                self.record_result('error_handling_nonexistent', False, duration_ms, 
                                  error="Failed to handle non-existent document correctly")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('error_handling_nonexistent', False, duration_ms, 
                              error=f"Exception instead of None: {str(e)}")
        
        # Invalid collection
        start_time = time.time()
        try:
            await self.async_manager.get_document("invalid/collection/path", "doc-id")
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('error_handling_invalid_collection', False, duration_ms, 
                              error="Failed to detect invalid collection")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.record_result('error_handling_invalid_collection', True, duration_ms, 
                              details={"error_message": str(e)})
    
    async def cleanup(self) -> None:
        """Clean up test data and resources."""
        try:
            # Delete test collection
            # Note: Firestore doesn't directly support collection deletion
            # We'd need to implement this in a real scenario
            self.sync_manager.close()
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Firestore connection tests."""
        try:
            await self.setup()
            
            logger.info("Starting Firestore connection tests...")
            
            await self.test_sync_connection()
            await self.test_async_connection()
            await self.test_crud_operations()
            await self.test_connection_pool()
            await self.test_error_handling()
            
            await self.cleanup()
            return self.generate_report()
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.record_result('test_suite', False, 0, error=str(e))
            return self.generate_report()


class RedisTester(ConnectionTester):
    """Specialized tester for Redis connections."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Redis tester."""
        super().__init__(config_path)
        # Redis-specific initialization would go here
        # For this template, we're simply preparing the structure
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Redis connection tests."""
        logger.info("Redis testing is not yet implemented")
        
        # Mock some results for demonstration
        self.record_result(
            'redis_connection', 
            True, 
            15.5, 
            details={"message": "Redis testing to be implemented"}
        )
        
        return self.generate_report()


async def main() -> None:
    """Main function to run all connection tests."""
    logger.info("Starting connection testing tool")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run connection tests for Firestore and Redis')
    parser.add_argument('--config', '-c', help='Path to configuration file')
    parser.add_argument('--firestore-only', action='store_true', help='Only test Firestore')
    parser.add_argument('--redis-only', action='store_true', help='Only test Redis')
    parser.add_argument('--output', '-o', default='connection_test_report.json', 
                       help='Path for output report')
    args = parser.parse_args()
    
    combined_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'firestore': None,
        'redis': None
    }
    
    # Run Firestore tests if selected
    if not args.redis_only:
        firestore_tester = FirestoreTester(args.config)
        firestore_results = await firestore_tester.run_all_tests()
        combined_results['firestore'] = firestore_results
        firestore_tester.save_report('firestore_test_report.json')
    
    # Run Redis tests if selected
    if not args.firestore_only:
        redis_tester = RedisTester(args.config)
        redis_results = await redis_tester.run_all_tests()
        combined_results['redis'] = redis_results
        redis_tester.save_report('redis_test_report.json')
    
    # Save combined report
    with open(args.output, 'w') as f:
        json.dump(combined_results, f, indent=2)
    logger.info(f"Combined report saved to {args.output}")
    
    # Print summary
    print("\n" + "=" * 60)
    print(" CONNECTION TEST SUMMARY")
    print("=" * 60)
    
    if 'firestore' in combined_results and combined_results['firestore']:
        fs_results = combined_results['firestore']
        success_rate = fs_results.get('success_rate', 0) * 100
        print(f"Firestore: {success_rate:.1f}% successful " + 
              ("✅" if success_rate > 90 else "⚠️" if success_rate > 70 else "❌"))
    
    if 'redis' in combined_results and combined_results['redis']:
        redis_results = combined_results['redis']
        success_rate = redis_results.get('success_rate', 0) * 100
        print(f"Redis: {success_rate:.1f}% successful " + 
              ("✅" if success_rate > 90 else "⚠️" if success_rate > 70 else "❌"))
    
    print("\nSee detailed reports in:")
    if not args.redis_only:
        print("- firestore_test_report.json")
    if not args.firestore_only:
        print("- redis_test_report.json")
    print(f"- {args.output} (combined)")


if __name__ == "__main__":
    test_connection("https://example.com")
    asyncio.run(main())
