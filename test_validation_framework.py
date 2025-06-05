#!/usr/bin/env python3
"""
Test Validation Framework for Orchestra Implementation
Provides comprehensive testing and validation for all architectural components
"""

import json
import os
import sys
import subprocess
import unittest
import asyncio
import time
import psutil
import tracemalloc
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a test execution"""
    test_name: str
    passed: bool
    duration: float
    memory_usage: float
    error: Optional[str] = None
    recommendation: Optional[str] = None

class PerformanceMonitor:
    """Monitor performance metrics during tests"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        tracemalloc.start()
    
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.start_memory = tracemalloc.get_traced_memory()[0]
    
    def stop(self) -> Tuple[float, float]:
        """Stop monitoring and return duration and memory usage"""
        duration = time.time() - self.start_time
        current_memory = tracemalloc.get_traced_memory()[0]
        memory_usage = (current_memory - self.start_memory) / 1024 / 1024  # MB
        return duration, memory_usage

class SecurityValidator:
    """Validate security requirements"""
    
    def test_no_hardcoded_credentials(self) -> TestResult:
        """Test for hardcoded credentials"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            suspicious_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]
            
            found_issues = []
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                for line_num, line in enumerate(content.split('\n'), 1):
                                    for pattern in suspicious_patterns:
                                        if any(keyword in line.lower() for keyword in ['password', 'api_key', 'secret', 'token']):
                                            if '=' in line and ('os.getenv' not in line and 'os.environ' not in line):
                                                found_issues.append(f"{file_path}:{line_num}")
                        except Exception as e:
                            logger.error(f"Unexpected error: {e}")
                            pass
            
            duration, memory = monitor.stop()
            
            if found_issues:
                return TestResult(
                    test_name="No Hardcoded Credentials",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error=f"Found {len(found_issues)} hardcoded credentials",
                    recommendation="Replace all hardcoded credentials with environment variables"
                )
            
            return TestResult(
                test_name="No Hardcoded Credentials",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="No Hardcoded Credentials",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_environment_variables(self) -> TestResult:
        """Test environment variable configuration"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            env_files = ['.env', '.env.template', '.env.example']
            found = any(os.path.exists(f) for f in env_files)
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Environment Variables Configuration",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No environment configuration file found",
                    recommendation="Create .env.template with all required environment variables"
                )
            
            return TestResult(
                test_name="Environment Variables Configuration",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Environment Variables Configuration",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_sql_injection_prevention(self) -> TestResult:
        """Test for SQL injection vulnerabilities"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            vulnerable_patterns = [
                r'\.execute\s*\(\s*["\'].*%s.*["\'].*%',
                r'\.execute\s*\(\s*f["\']',
                r'\.execute\s*\(\s*["\'].*\+.*["\']'
            ]
            
            found_issues = []
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if '.execute(' in content:
                                    # Check for string concatenation in SQL
                                    lines = content.split('\n')
                                    for i, line in enumerate(lines):
                                        if '.execute(' in line and ('+' in line or 'f"' in line or "f'" in line):
                                            found_issues.append(f"{file_path}:{i+1}")
                        except:
                            pass
            
            duration, memory = monitor.stop()
            
            if found_issues:
                return TestResult(
                    test_name="SQL Injection Prevention",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error=f"Found {len(found_issues)} potential SQL injection vulnerabilities",
                    recommendation="Use parameterized queries for all database operations"
                )
            
            return TestResult(
                test_name="SQL Injection Prevention",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="SQL Injection Prevention",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )

class PerformanceValidator:
    """Validate performance requirements"""
    
    def test_database_connection_pooling(self) -> TestResult:
        """Test database connection pooling configuration"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            pool_indicators = ['pool_size', 'max_overflow', 'QueuePool', 'pool_pre_ping']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if any(indicator in content for indicator in pool_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Database Connection Pooling",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No connection pooling configuration found",
                    recommendation="Configure SQLAlchemy with connection pooling (pool_size=10, max_overflow=20)"
                )
            
            return TestResult(
                test_name="Database Connection Pooling",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Database Connection Pooling",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_async_implementation(self) -> TestResult:
        """Test async/await implementation"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            async_indicators = ['async def', 'await ', 'asyncio', 'aiohttp']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if any(indicator in content for indicator in async_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Async Implementation",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No async implementation found",
                    recommendation="Use async/await for I/O-bound operations"
                )
            
            return TestResult(
                test_name="Async Implementation",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Async Implementation",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_caching_implementation(self) -> TestResult:
        """Test caching implementation"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            cache_indicators = ['redis', 'memcached', 'lru_cache', '@cache', 'cache.get', 'cache.set']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read().lower()
                                if any(indicator in content for indicator in cache_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Caching Implementation",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No caching implementation found",
                    recommendation="Implement Redis caching for frequently accessed data"
                )
            
            return TestResult(
                test_name="Caching Implementation",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Caching Implementation",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )

class ErrorHandlingValidator:
    """Validate error handling implementation"""
    
    def test_structured_logging(self) -> TestResult:
        """Test structured logging implementation"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            logging_indicators = ['logging.getLogger', 'logger =', 'structlog', 'loguru']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if any(indicator in content for indicator in logging_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Structured Logging",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No structured logging found",
                    recommendation="Implement structured logging with proper log levels"
                )
            
            return TestResult(
                test_name="Structured Logging",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Structured Logging",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_retry_policies(self) -> TestResult:
        """Test retry policy implementation"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            retry_indicators = ['retry', 'backoff', 'tenacity', '@retry', 'max_retries']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read().lower()
                                if any(indicator in content for indicator in retry_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Retry Policies",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No retry policies found",
                    recommendation="Implement retry policies with exponential backoff for external calls"
                )
            
            return TestResult(
                test_name="Retry Policies",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Retry Policies",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_exception_handling(self) -> TestResult:
        """Test proper exception handling"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            bare_except_count = 0
            proper_except_count = 0
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                lines = f.readlines()
                                for line in lines:
                                    if line.strip() == 'except:':
                                        bare_except_count += 1
                                    elif 'except ' in line and ' as ' in line:
                                        proper_except_count += 1
                        except:
                            pass
            
            duration, memory = monitor.stop()
            
            if bare_except_count > 0:
                return TestResult(
                    test_name="Exception Handling",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error=f"Found {bare_except_count} bare except clauses",
                    recommendation="Replace bare except with specific exception types"
                )
            
            return TestResult(
                test_name="Exception Handling",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Exception Handling",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )

class ArchitectureValidator:
    """Validate architecture compliance"""
    
    def test_layered_architecture(self) -> TestResult:
        """Test layered architecture structure"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            expected_layers = ['api', 'services', 'domain', 'infrastructure', 'core']
            found_layers = []
            
            for item in os.listdir('.'):
                if os.path.isdir(item) and item in expected_layers:
                    found_layers.append(item)
            
            duration, memory = monitor.stop()
            
            if len(found_layers) < 3:
                return TestResult(
                    test_name="Layered Architecture",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error=f"Only found {len(found_layers)} architectural layers",
                    recommendation="Implement proper layered architecture with api, services, domain, and infrastructure layers"
                )
            
            return TestResult(
                test_name="Layered Architecture",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Layered Architecture",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_dependency_injection(self) -> TestResult:
        """Test dependency injection patterns"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            di_indicators = ['inject', 'provider', 'container', '__init__', 'dependency']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                # Look for constructor injection patterns
                                if '__init__' in content and 'self.' in content:
                                    lines = content.split('\n')
                                    for i, line in enumerate(lines):
                                        if 'def __init__' in line and i + 1 < len(lines):
                                            # Check if constructor has parameters
                                            if ',' in line or (')' not in line and ':' not in line):
                                                found = True
                                                break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Dependency Injection",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No dependency injection patterns found",
                    recommendation="Use constructor injection for better testability"
                )
            
            return TestResult(
                test_name="Dependency Injection",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Dependency Injection",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )

class IntegrationValidator:
    """Validate integration points"""
    
    def test_database_connectivity(self) -> TestResult:
        """Test database connectivity"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            # Check for database configuration
            db_indicators = ['postgresql', 'postgres', 'DATABASE_URL', 'create_engine']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith(('.py', '.env', '.yml', '.yaml')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if any(indicator in content for indicator in db_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="Database Connectivity",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No database configuration found",
                    recommendation="Configure PostgreSQL connection with proper credentials"
                )
            
            return TestResult(
                test_name="Database Connectivity",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="Database Connectivity",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )
    
    def test_api_endpoints(self) -> TestResult:
        """Test API endpoint definitions"""
        monitor = PerformanceMonitor()
        monitor.start()
        
        try:
            api_indicators = ['@app.route', '@router', 'FastAPI', 'Flask', 'endpoint', 'api/']
            found = False
            
            for root, dirs, files in os.walk('.'):
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if any(indicator in content for indicator in api_indicators):
                                    found = True
                                    break
                        except:
                            pass
                
                if found:
                    break
            
            duration, memory = monitor.stop()
            
            if not found:
                return TestResult(
                    test_name="API Endpoints",
                    passed=False,
                    duration=duration,
                    memory_usage=memory,
                    error="No API endpoints found",
                    recommendation="Define RESTful API endpoints for the application"
                )
            
            return TestResult(
                test_name="API Endpoints",
                passed=True,
                duration=duration,
                memory_usage=memory
            )
            
        except Exception as e:
            duration, memory = monitor.stop()
            return TestResult(
                test_name="API Endpoints",
                passed=False,
                duration=duration,
                memory_usage=memory,
                error=str(e)
            )

class TestOrchestrator:
    """Orchestrate all validation tests"""
    
    def __init__(self):
        self.validators = {
            'Security': SecurityValidator(),
            'Performance': PerformanceValidator(),
            'Error Handling': ErrorHandlingValidator(),
            'Architecture': ArchitectureValidator(),
            'Integration': IntegrationValidator()
        }
        self.results: List[TestResult] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        print("🧪 Running Orchestra Implementation Tests")
        print("=" * 50)
        
        for category, validator in self.validators.items():
            print(f"\n📋 {category} Tests:")
            
            # Get all test methods
            test_methods = [method for method in dir(validator) 
                          if method.startswith('test_') and callable(getattr(validator, method))]
            
            for test_method in test_methods:
                method = getattr(validator, test_method)
                result = method()
                self.results.append(result)
                
                status = "✅" if result.passed else "❌"
                print(f"  {status} {result.test_name}")
                if result.error:
                    print(f"     Error: {result.error}")
                if result.recommendation:
                    print(f"     💡 {result.recommendation}")
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(r.duration for r in self.results)
        total_memory = sum(r.memory_usage for r in self.results)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_duration': total_duration,
                'total_memory_mb': total_memory
            },
            'results': [
                {
                    'test': r.test_name,
                    'passed': r.passed,
                    'duration': r.duration,
                    'memory_mb': r.memory_usage,
                    'error': r.error,
                    'recommendation': r.recommendation
                }
                for r in self.results
            ],
            'failed_tests': [
                {
                    'test': r.test_name,
                    'error': r.error,
                    'recommendation': r.recommendation
                }
                for r in self.results if not r.passed
            ]
        }
        
        return report

def main():
    """Main execution function"""
    orchestrator = TestOrchestrator()
    report = orchestrator.run_all_tests()
    
    # Save report
    report_filename = f"test_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  Total Tests: {report['summary']['total_tests']}")
    print(f"  Passed: {report['summary']['passed']}")
    print(f"  Failed: {report['summary']['failed']}")
    print(f"  Pass Rate: {report['summary']['pass_rate']:.1%}")
    print(f"  Total Duration: {report['summary']['total_duration']:.2f}s")
    print(f"  Memory Usage: {report['summary']['total_memory_mb']:.2f} MB")
    
    if report['failed_tests']:
        print("\n⚠️  Failed Tests:")
        for test in report['failed_tests']:
            print(f"\n  ❌ {test['test']}")
            if test['error']:
                print(f"     Error: {test['error']}")
            if test['recommendation']:
                print(f"     💡 {test['recommendation']}")
    
    print(f"\n📄 Full report saved to: {report_filename}")
    
    # Return exit code based on test results
    return 0 if report['summary']['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())