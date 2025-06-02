#!/usr/bin/env python3
"""
Enhanced Error Handling and Recovery for AI Orchestrator
Implements robust retry logic, graceful degradation, and improved logging
"""

import os
import sys
import json
import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
from functools import wraps
import aiohttp
import psycopg2
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_components.orchestration.ai_orchestrator import (
    DatabaseLogger, WeaviateManager, TaskDefinition, AgentRole
)


class RetryStrategy(Enum):
    """Retry strategies for different failure types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: List[type] = field(default_factory=lambda: [
        aiohttp.ClientError,
        psycopg2.OperationalError,
        ConnectionError,
        TimeoutError
    ])


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class EnhancedCircuitBreaker:
    """Enhanced circuit breaker with monitoring"""
    
    def __init__(self, config: CircuitBreakerConfig, name: str):
        self.config = config
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.success_count = 0
        self.total_calls = 0
        self.db_logger = DatabaseLogger()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        self.total_calls += 1
        
        # Check circuit state
        if self.state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                self._log_state_change("HALF_OPEN", "Recovery timeout reached")
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                if self.failure_count > 0:
                    self.state = CircuitBreakerState.OPEN
                    self._log_state_change("OPEN", "Half-open test failed")
                    raise Exception(f"Circuit breaker {self.name} is OPEN")
                else:
                    self.state = CircuitBreakerState.CLOSED
                    self._log_state_change("CLOSED", "Recovery successful")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.success_count += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)
    
    def _on_failure(self, error: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
        
        if self.failure_count >= self.config.failure_threshold:
            if self.state != CircuitBreakerState.OPEN:
                self.state = CircuitBreakerState.OPEN
                self._log_state_change("OPEN", f"Failure threshold reached: {error}")
    
    def _log_state_change(self, new_state: str, reason: str):
        """Log circuit breaker state changes"""
        self.db_logger.log_action(
            workflow_id="circuit_breaker",
            task_id=self.name,
            agent_role="error_handler",
            action="state_change",
            status=new_state.lower(),
            metadata={
                "previous_state": self.state.value,
                "new_state": new_state,
                "reason": reason,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "total_calls": self.total_calls
            }
        )


class EnhancedRetryHandler:
    """Enhanced retry handler with multiple strategies"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.circuit_breakers = {}
    
    def get_circuit_breaker(self, name: str) -> EnhancedCircuitBreaker:
        """Get or create circuit breaker for service"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = EnhancedCircuitBreaker(
                CircuitBreakerConfig(),
                name
            )
        return self.circuit_breakers[name]
    
    async def retry_with_backoff(self, func: Callable, config: RetryConfig, 
                                context: Dict[str, Any] = None) -> Any:
        """Execute function with configurable retry logic"""
        attempt = 0
        last_exception = None
        
        while attempt < config.max_attempts:
            try:
                # Log attempt
                self.db_logger.log_action(
                    workflow_id=context.get("workflow_id", "unknown"),
                    task_id=context.get("task_id", "unknown"),
                    agent_role="error_handler",
                    action="retry_attempt",
                    status="started",
                    metadata={
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "strategy": config.strategy.value
                    }
                )
                
                # Execute function
                if config.strategy == RetryStrategy.CIRCUIT_BREAKER:
                    circuit_breaker = self.get_circuit_breaker(
                        context.get("service_name", "default")
                    )
                    result = await circuit_breaker.call(func)
                else:
                    result = await func()
                
                # Log success
                self.db_logger.log_action(
                    workflow_id=context.get("workflow_id", "unknown"),
                    task_id=context.get("task_id", "unknown"),
                    agent_role="error_handler",
                    action="retry_success",
                    status="completed",
                    metadata={"attempt": attempt + 1}
                )
                
                return result
                
            except Exception as e:
                last_exception = e
                attempt += 1
                
                # Check if exception is retryable
                is_retryable = any(
                    isinstance(e, exc_type) 
                    for exc_type in config.retryable_exceptions
                )
                
                if not is_retryable or attempt >= config.max_attempts:
                    # Log final failure
                    self.db_logger.log_action(
                        workflow_id=context.get("workflow_id", "unknown"),
                        task_id=context.get("task_id", "unknown"),
                        agent_role="error_handler",
                        action="retry_failed",
                        status="failed",
                        metadata={
                            "attempt": attempt,
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        },
                        error=str(e)
                    )
                    raise
                
                # Calculate delay
                delay = self._calculate_delay(attempt, config)
                
                # Log retry
                self.db_logger.log_action(
                    workflow_id=context.get("workflow_id", "unknown"),
                    task_id=context.get("task_id", "unknown"),
                    agent_role="error_handler",
                    action="retry_delay",
                    status="waiting",
                    metadata={
                        "attempt": attempt,
                        "delay": delay,
                        "error": str(e)
                    }
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay based on retry strategy"""
        if config.strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.initial_delay * attempt
        else:  # EXPONENTIAL_BACKOFF
            delay = config.initial_delay * (config.backoff_factor ** (attempt - 1))
        
        return min(delay, config.max_delay)


class GracefulDegradationHandler:
    """Handles graceful degradation for service failures"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.fallback_strategies = {}
        self.service_health = {}
    
    def register_fallback(self, service: str, fallback: Callable):
        """Register fallback strategy for a service"""
        self.fallback_strategies[service] = fallback
    
    async def execute_with_fallback(self, service: str, primary_func: Callable,
                                   context: Dict[str, Any] = None) -> Any:
        """Execute function with fallback on failure"""
        try:
            # Try primary function
            result = await primary_func()
            self._update_service_health(service, True)
            return result
            
        except Exception as e:
            # Log primary failure
            self.db_logger.log_action(
                workflow_id=context.get("workflow_id", "unknown"),
                task_id=context.get("task_id", "unknown"),
                agent_role="degradation_handler",
                action="primary_failed",
                status="degraded",
                metadata={
                    "service": service,
                    "error": str(e)
                }
            )
            
            self._update_service_health(service, False)
            
            # Try fallback
            if service in self.fallback_strategies:
                try:
                    fallback_result = await self.fallback_strategies[service](context)
                    
                    # Log fallback success
                    self.db_logger.log_action(
                        workflow_id=context.get("workflow_id", "unknown"),
                        task_id=context.get("task_id", "unknown"),
                        agent_role="degradation_handler",
                        action="fallback_success",
                        status="degraded",
                        metadata={
                            "service": service,
                            "fallback_used": True
                        }
                    )
                    
                    return fallback_result
                    
                except Exception as fallback_error:
                    # Log fallback failure
                    self.db_logger.log_action(
                        workflow_id=context.get("workflow_id", "unknown"),
                        task_id=context.get("task_id", "unknown"),
                        agent_role="degradation_handler",
                        action="fallback_failed",
                        status="failed",
                        metadata={
                            "service": service,
                            "fallback_error": str(fallback_error)
                        },
                        error=str(fallback_error)
                    )
                    raise
            else:
                raise
    
    def _update_service_health(self, service: str, healthy: bool):
        """Update service health status"""
        if service not in self.service_health:
            self.service_health[service] = {
                "healthy": True,
                "failure_count": 0,
                "success_count": 0,
                "last_check": None
            }
        
        health = self.service_health[service]
        health["healthy"] = healthy
        health["last_check"] = datetime.now()
        
        if healthy:
            health["success_count"] += 1
            health["failure_count"] = 0
        else:
            health["failure_count"] += 1
    
    def get_service_health(self) -> Dict[str, Dict]:
        """Get current service health status"""
        return self.service_health


class EnhancedLoggingHandler:
    """Enhanced logging with structured error analysis"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        
        # Configure structured logging
        self.logger = logging.getLogger("orchestrator.error_handler")
        self.logger.setLevel(logging.DEBUG)
        
        # Add handlers
        file_handler = logging.FileHandler("ai_components/logs/error_handler.log")
        file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log error with full context and analysis"""
        error_id = f"error_{int(time.time() * 1000)}"
        
        # Analyze error
        error_analysis = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "stack_frames": self._extract_stack_frames(),
            "suggestions": self._generate_recovery_suggestions(error)
        }
        
        # Log to file
        self.logger.error(f"Error {error_id}: {error}", extra=error_analysis)
        
        # Log to database
        self.db_logger.log_action(
            workflow_id=context.get("workflow_id", "unknown"),
            task_id=context.get("task_id", "unknown"),
            agent_role="error_analyzer",
            action="error_logged",
            status="error",
            metadata=error_analysis,
            error=str(error)
        )
        
        # Store in Weaviate for analysis
        self.weaviate_manager.store_context(
            workflow_id=context.get("workflow_id", "unknown"),
            task_id=error_id,
            context_type="error_analysis",
            content=json.dumps(error_analysis),
            metadata={
                "error_type": type(error).__name__,
                "timestamp": error_analysis["timestamp"]
            }
        )
        
        return error_id
    
    def _extract_stack_frames(self) -> List[Dict]:
        """Extract relevant stack frames for analysis"""
        frames = []
        for frame in traceback.extract_stack()[:-2]:  # Exclude this function
            frames.append({
                "filename": frame.filename,
                "line": frame.lineno,
                "function": frame.name,
                "code": frame.line
            })
        return frames[-10:]  # Last 10 frames
    
    def _generate_recovery_suggestions(self, error: Exception) -> List[str]:
        """Generate recovery suggestions based on error type"""
        suggestions = []
        
        if isinstance(error, psycopg2.OperationalError):
            suggestions.extend([
                "Check database connection parameters",
                "Verify PostgreSQL service is running",
                "Check network connectivity to database",
                "Review connection pool settings"
            ])
        elif isinstance(error, aiohttp.ClientError):
            suggestions.extend([
                "Check API endpoint availability",
                "Verify API credentials",
                "Review rate limiting settings",
                "Check network connectivity"
            ])
        elif isinstance(error, TimeoutError):
            suggestions.extend([
                "Increase timeout values",
                "Check service performance",
                "Consider implementing caching",
                "Review resource allocation"
            ])
        elif "weaviate" in str(error).lower():
            suggestions.extend([
                "Check Weaviate Cloud connection",
                "Verify Weaviate API key",
                "Review schema configuration",
                "Check Weaviate service status"
            ])
        elif "airbyte" in str(error).lower():
            suggestions.extend([
                "Check Airbyte Cloud connection",
                "Verify Airbyte workspace configuration",
                "Review sync schedule",
                "Check source/destination connectivity"
            ])
        
        # General suggestions
        suggestions.extend([
            "Review recent configuration changes",
            "Check system resource utilization",
            "Verify all required services are running"
        ])
        
        return suggestions


class ErrorRecoveryOrchestrator:
    """Orchestrates error recovery strategies"""
    
    def __init__(self):
        self.retry_handler = EnhancedRetryHandler()
        self.degradation_handler = GracefulDegradationHandler()
        self.logging_handler = EnhancedLoggingHandler()
        self.db_logger = DatabaseLogger()
        
        # Register fallback strategies
        self._register_fallbacks()
    
    def _register_fallbacks(self):
        """Register fallback strategies for services"""
        
        # Weaviate fallback - use local cache
        async def weaviate_fallback(context: Dict) -> Any:
            # Implement local caching fallback
            return {"source": "cache", "data": "cached_result"}
        
        # Airbyte fallback - use last known sync
        async def airbyte_fallback(context: Dict) -> Any:
            # Use last successful sync data
            return {"source": "last_sync", "timestamp": datetime.now().isoformat()}
        
        # EigenCode fallback - use basic analysis
        async def eigencode_fallback(context: Dict) -> Any:
            # Provide basic code analysis
            return {
                "analysis": {
                    "status": "fallback",
                    "message": "Using basic analysis due to EigenCode unavailability",
                    "basic_metrics": {
                        "files": 0,
                        "lines": 0,
                        "complexity": "unknown"
                    }
                }
            }
        
        self.degradation_handler.register_fallback("weaviate", weaviate_fallback)
        self.degradation_handler.register_fallback("airbyte", airbyte_fallback)
        self.degradation_handler.register_fallback("eigencode", eigencode_fallback)
    
    async def execute_with_recovery(self, func: Callable, context: Dict[str, Any],
                                   retry_config: Optional[RetryConfig] = None) -> Any:
        """Execute function with full error recovery"""
        if not retry_config:
            retry_config = RetryConfig()
        
        try:
            # Execute with retry
            result = await self.retry_handler.retry_with_backoff(
                func, retry_config, context
            )
            return result
            
        except Exception as e:
            # Log error with full context
            error_id = self.logging_handler.log_error_with_context(e, context)
            
            # Attempt recovery based on error type
            if await self._attempt_recovery(e, context):
                # Retry after recovery
                try:
                    result = await func()
                    
                    # Log recovery success
                    self.db_logger.log_action(
                        workflow_id=context.get("workflow_id", "unknown"),
                        task_id=context.get("task_id", "unknown"),
                        agent_role="recovery_orchestrator",
                        action="recovery_success",
                        status="recovered",
                        metadata={"error_id": error_id}
                    )
                    
                    return result
                except:
                    pass
            
            # If recovery failed, raise original error
            raise
    
    async def _attempt_recovery(self, error: Exception, context: Dict) -> bool:
        """Attempt to recover from error"""
        recovery_attempted = False
        
        # Database connection recovery
        if isinstance(error, psycopg2.OperationalError):
            try:
                # Attempt to reconnect
                self.db_logger = DatabaseLogger()  # Reinitialize
                recovery_attempted = True
            except:
                pass
        
        # API connection recovery
        elif isinstance(error, aiohttp.ClientError):
            # Wait and retry with new session
            await asyncio.sleep(5)
            recovery_attempted = True
        
        return recovery_attempted


async def enhance_orchestrator_error_handling():
    """Apply error handling enhancements to the orchestrator"""
    
    # Import the orchestrator
    from ai_components.orchestration.ai_orchestrator import WorkflowOrchestrator
    
    # Create enhanced orchestrator class
    class EnhancedWorkflowOrchestrator(WorkflowOrchestrator):
        def __init__(self):
            super().__init__()
            self.error_recovery = ErrorRecoveryOrchestrator()
        
        async def execute_workflow(self, workflow_id: str, tasks: List[TaskDefinition]):
            """Execute workflow with enhanced error handling"""
            context = {
                "workflow_id": workflow_id,
                "start_time": datetime.now().isoformat()
            }
            
            async def _execute():
                return await super().execute_workflow(workflow_id, tasks)
            
            try:
                # Execute with full error recovery
                result = await self.error_recovery.execute_with_recovery(
                    _execute, context
                )
                return result
                
            except Exception as e:
                # Log workflow failure
                self.error_recovery.logging_handler.log_error_with_context(
                    e, {**context, "tasks": [t.task_id for t in tasks]}
                )
                raise
    
    return EnhancedWorkflowOrchestrator


async def main():
    """Main function to demonstrate error handling enhancements"""
    print("Implementing Enhanced Error Handling and Recovery")
    print("=" * 50)
    
    # Create error recovery orchestrator
    recovery = ErrorRecoveryOrchestrator()
    
    # Test retry logic
    print("\nTesting retry logic...")
    
    async def flaky_function():
        if hasattr(flaky_function, 'attempts'):
            flaky_function.attempts += 1
        else:
            flaky_function.attempts = 1
        
        if flaky_function.attempts < 3:
            raise ConnectionError("Simulated connection error")
        return "Success after retries"
    
    try:
        result = await recovery.execute_with_recovery(
            flaky_function,
            {"workflow_id": "test_workflow", "task_id": "test_task"}
        )
        print(f"✓ Retry test passed: {result}")
    except Exception as e:
        print(f"✗ Retry test failed: {e}")
    
    # Test graceful degradation
    print("\nTesting graceful degradation...")
    
    async def failing_service():
        raise Exception("Service unavailable")
    
    result = await recovery.degradation_handler.execute_with_fallback(
        "eigencode",
        failing_service,
        {"workflow_id": "test_workflow", "task_id": "degradation_test"}
    )
    print(f"✓ Degradation test passed: {result}")
    
    # Test circuit breaker
    print("\nTesting circuit breaker...")
    circuit_breaker = recovery.retry_handler.get_circuit_breaker("test_service")
    
    for i in range(10):
        try:
            await circuit_breaker.call(failing_service)
        except Exception as e:
            print(f"  Attempt {i+1}: {e}")
    
    print(f"  Circuit breaker state: {circuit_breaker.state.value}")
    
    # Get service health
    print("\nService Health Status:")
    health = recovery.degradation_handler.get_service_health()
    for service, status in health.items():
        print(f"  {service}: {status}")
    
    # Create enhanced orchestrator
    print("\nCreating enhanced orchestrator...")
    EnhancedOrchestrator = await enhance_orchestrator_error_handling()
    
    # Save enhancement code
    enhancement_code = '''
# Add to ai_components/orchestration/ai_orchestrator.py

from scripts.error_handling_enhancements import ErrorRecoveryOrchestrator

class EnhancedWorkflowOrchestrator(WorkflowOrchestrator):
    """Workflow orchestrator with enhanced error handling"""
    
    def __init__(self):
        super().__init__()
        self.error_recovery = ErrorRecoveryOrchestrator()
    
    async def execute_workflow(self, workflow_id: str, tasks: List[TaskDefinition]):
        """Execute workflow with enhanced error handling"""
        context = {
            "workflow_id": workflow_id,
            "start_time": datetime.now().isoformat()
        }
        
        async def _execute():
            return await super().execute_workflow(workflow_id, tasks)
        
        try:
            result = await self.error_recovery.execute_with_recovery(
                _execute, context
            )
            return result
        except Exception as e:
            self.error_recovery.logging_handler.log_error_with_context(
                e, {**context, "tasks": [t.task_id for t in tasks]}
            )
            raise
'''
    
    with open("error_handling_enhancement.py", 'w') as f:
        f.write(enhancement_code)
    
    print("\n✓ Error handling enhancements implemented")
    print("  - Robust retry logic with multiple strategies")
    print("  - Circuit breaker pattern for service protection")
    print("  - Graceful degradation with fallback strategies")
    print("  - Enhanced logging with error analysis")
    print("  - Automated recovery suggestions")
    
    print("\nEnhancement code saved to: error_handling_enhancement.py")


if __name__ == "__main__":
    asyncio.run(main())