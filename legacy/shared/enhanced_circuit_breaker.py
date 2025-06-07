import asyncio
#!/usr/bin/env python3
"""
"""
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    """
    """
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0,
            "state_changes": []
        }
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        """Change circuit state and record metrics"""
            self.metrics["state_changes"].append({
                "from": old_state.value,
                "to": new_state.value,
                "timestamp": self._last_state_change.isoformat()
            })
            
            logger.info(f"Circuit breaker '{self.name}' state changed: {old_state.value} -> {new_state.value}")
            
            # Notify monitoring
            if self.monitoring_callback:
                self.monitoring_callback(self.name, old_state, new_state)
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        """
        """
        self.metrics["total_calls"] += 1
        
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._change_state(CircuitState.HALF_OPEN)
            self._success_count = 0
        
        # Reject if circuit is open
        if self._state == CircuitState.OPEN:
            self.metrics["rejected_calls"] += 1
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )
        
        try:

        
            pass
            # Execute the function
            result = func(*args, **kwargs)
            
            # Handle success
            self._on_success()
            return result
            
        except Exception:

            
            pass
            # Handle expected failure
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        """
        self.metrics["total_calls"] += 1
        
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._change_state(CircuitState.HALF_OPEN)
            self._success_count = 0
        
        # Reject if circuit is open
        if self._state == CircuitState.OPEN:
            self.metrics["rejected_calls"] += 1
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )
        
        try:

        
            pass
            # Execute the async function
            result = await func(*args, **kwargs)
            
            # Handle success
            self._on_success()
            return result
            
        except Exception:

            
            pass
            # Handle expected failure
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.metrics["successful_calls"] += 1
        
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._change_state(CircuitState.CLOSED)
                self._failure_count = 0
        
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.metrics["failed_calls"] += 1
        self._last_failure_time = datetime.now()
        
        if self._state == CircuitState.HALF_OPEN:
            self._change_state(CircuitState.OPEN)
        
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._change_state(CircuitState.OPEN)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
            "current_state": self._state.value,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "last_state_change": self._last_state_change.isoformat()
        }
    
    def reset(self):
        """Manually reset the circuit breaker"""
        logger.info(f"Circuit breaker '{self.name}' manually reset")

def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception,
    success_threshold: int = 2
):
    """
    """
        breaker_name = name or f"{func.__module__}.{func.__name__}"
        breaker = EnhancedCircuitBreaker(
            name=breaker_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            success_threshold=success_threshold
        )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        
        # Attach breaker for monitoring
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.circuit_breaker = breaker
        
        return wrapper
    
    return decorator

class CircuitBreakerManager:
    """
    """
            "total_breakers": 0,
            "open_breakers": 0,
            "half_open_breakers": 0,
            "closed_breakers": 0
        }
    
    def register_breaker(self, breaker: EnhancedCircuitBreaker):
        """Register a circuit breaker for monitoring"""
        """Handle circuit breaker state changes"""
            logger.warning(f"⚠️ Circuit breaker '{name}' is now OPEN - service degraded")
        elif old_state == CircuitState.OPEN and new_state == CircuitState.CLOSED:
            logger.info(f"✅ Circuit breaker '{name}' recovered - service restored")
    
    def _update_global_metrics(self):
        """Update global metrics"""
        self.global_metrics["total_breakers"] = len(self.breakers)
        self.global_metrics["open_breakers"] = sum(
            1 for b in self.breakers.values() if b.state == CircuitState.OPEN
        )
        self.global_metrics["half_open_breakers"] = sum(
            1 for b in self.breakers.values() if b.state == CircuitState.HALF_OPEN
        )
        self.global_metrics["closed_breakers"] = sum(
            1 for b in self.breakers.values() if b.state == CircuitState.CLOSED
        )
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all circuit breakers"""
            "global": self.global_metrics,
            "breakers": {
                name: breaker.get_metrics()
                for name, breaker in self.breakers.items()
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        total = self.global_metrics["total_breakers"]
        if total == 0:
            return {"status": "unknown", "message": "No circuit breakers registered"}
        
        open_percentage = (self.global_metrics["open_breakers"] / total) * 100
        
        if open_percentage == 0:
            status = "healthy"
            message = "All services operational"
        elif open_percentage < 25:
            status = "degraded"
            message = f"{self.global_metrics['open_breakers']} services experiencing issues"
        elif open_percentage < 50:
            status = "warning"
            message = f"{open_percentage:.0f}% of services are down"
        else:
            status = "critical"
            message = f"Major outage: {open_percentage:.0f}% of services are down"
        
        return {
            "status": status,
            "message": message,
            "metrics": self.global_metrics
        }

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Example usage
if __name__ == "__main__":
    import random
    
    # Example service with circuit breaker
    @circuit_breaker(
        name="example_service",
        failure_threshold=3,
        recovery_timeout=10
    )
    def unreliable_service():
        """Simulated unreliable service"""
            raise Exception("Service failed")
        return "Success"
    
    # Test the circuit breaker
    for i in range(20):
        try:

            pass
            result = unreliable_service()
            print(f"Call {i+1}: {result}")
        except Exception:

            pass
            print(f"Call {i+1}: Circuit breaker OPEN - {e}")
        except Exception:

            pass
            print(f"Call {i+1}: Service failed - {e}")
        
        await asyncio.sleep(1)
    
    # Print metrics
    print("\nCircuit Breaker Metrics:")
    print(unreliable_service.circuit_breaker.get_metrics())