"""
Connection manager for efficient HTTP client pooling and reuse.

This module provides centralized management of HTTP connections with
automatic pooling, retry logic, and circuit breaker patterns.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for a provider"""
    provider: str
    failure_count: int = 0
    last_failure: Optional[float] = None
    is_open: bool = False
    half_open_retry_time: Optional[float] = None
    
    # Configuration
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_requests: int = 0
    half_open_successes: int = 0
    half_open_max: int = 3


class ConnectionManager:
    """
    Centralized HTTP connection management with pooling and resilience.
    
    Features:
    - Connection pooling per provider
    - Circuit breaker pattern
    - Exponential backoff with jitter
    - Request/response logging
    - Performance metrics
    """
    
    def __init__(
        self,
        pool_size: int = 2,
        pool_overflow: int = 3,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize connection manager.
        
        Args:
            pool_size: Base connection pool size
            pool_overflow: Maximum additional connections
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.pool_size = pool_size
        self.pool_overflow = pool_overflow
        self.timeout = timeout
        self.max_retries = max_retries
        
        # HTTP clients per provider
        self._clients: Dict[str, httpx.AsyncClient] = {}
        
        # Circuit breakers
        self._circuit_breakers: Dict[str, CircuitBreakerState] = {}
        
        # Metrics
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "retries": 0,
            "circuit_breaks": 0,
            "total_latency_ms": 0
        }
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def get_client(
        self,
        provider: str,
        base_url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.AsyncClient:
        """
        Get or create HTTP client for provider.
        
        Args:
            provider: Provider name (e.g., "portkey", "openrouter")
            base_url: Base URL for the provider
            headers: Default headers for requests
        
        Returns:
            Configured HTTP client
        """
        async with self._lock:
            if provider not in self._clients:
                # Create new client with connection pooling
                limits = httpx.Limits(
                    max_keepalive_connections=self.pool_size,
                    max_connections=self.pool_size + self.pool_overflow,
                    keepalive_expiry=30
                )
                
                self._clients[provider] = httpx.AsyncClient(
                    base_url=base_url,
                    headers=headers or {},
                    timeout=httpx.Timeout(self.timeout),
                    limits=limits,
                    follow_redirects=True
                )
                
                # Initialize circuit breaker
                self._circuit_breakers[provider] = CircuitBreakerState(provider=provider)
                
                logger.info(f"Created HTTP client for {provider}")
            
            return self._clients[provider]
    
    @asynccontextmanager
    async def request(
        self,
        provider: str,
        method: str,
        url: str,
        **kwargs
    ):
        """
        Make HTTP request with circuit breaker and retry logic.
        
        Args:
            provider: Provider name
            method: HTTP method
            url: Request URL (relative to base URL)
            **kwargs: Additional request parameters
        
        Yields:
            HTTP response
        
        Raises:
            Exception: If circuit is open or request fails after retries
        """
        # Check circuit breaker
        breaker = self._circuit_breakers.get(provider)
        if breaker and breaker.is_open:
            if time.time() < breaker.half_open_retry_time:
                self.metrics["circuit_breaks"] += 1
                raise Exception(f"Circuit breaker open for {provider}")
            else:
                # Try half-open state
                breaker.is_open = False
                breaker.half_open_requests = 0
                breaker.half_open_successes = 0
        
        start_time = time.time()
        self.metrics["requests"] += 1
        
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logger, logging.WARNING)
        )
        async def _make_request():
            """Inner function with retry logic"""
            self.metrics["retries"] += 1
            
            client = self._clients.get(provider)
            if not client:
                raise ValueError(f"No client configured for {provider}")
            
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        
        try:
            response = await _make_request()
            
            # Update metrics
            latency_ms = (time.time() - start_time) * 1000
            self.metrics["successes"] += 1
            self.metrics["total_latency_ms"] += latency_ms
            
            # Update circuit breaker on success
            if breaker:
                breaker.failure_count = 0
                if not breaker.is_open:
                    breaker.half_open_successes += 1
                    if breaker.half_open_successes >= breaker.half_open_max:
                        # Fully close circuit
                        breaker.half_open_requests = 0
                        breaker.half_open_successes = 0
            
            yield response
            
        except Exception as e:
            # Update metrics
            self.metrics["failures"] += 1
            
            # Update circuit breaker on failure
            if breaker:
                breaker.failure_count += 1
                breaker.last_failure = time.time()
                
                if breaker.failure_count >= breaker.failure_threshold:
                    breaker.is_open = True
                    breaker.half_open_retry_time = time.time() + breaker.recovery_timeout
                    logger.warning(f"Circuit breaker opened for {provider}")
            
            raise
    
    async def close(self):
        """Close all HTTP clients"""
        async with self._lock:
            for provider, client in self._clients.items():
                await client.aclose()
                logger.info(f"Closed HTTP client for {provider}")
            
            self._clients.clear()
            self._circuit_breakers.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection manager metrics"""
        avg_latency = (
            self.metrics["total_latency_ms"] / self.metrics["successes"]
            if self.metrics["successes"] > 0 else 0
        )
        
        success_rate = (
            self.metrics["successes"] / self.metrics["requests"]
            if self.metrics["requests"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "avg_latency_ms": avg_latency,
            "success_rate": success_rate,
            "active_clients": len(self._clients),
            "open_circuits": sum(1 for cb in self._circuit_breakers.values() if cb.is_open)
        }
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        status = {}
        
        for provider, breaker in self._circuit_breakers.items():
            status[provider] = {
                "is_open": breaker.is_open,
                "failure_count": breaker.failure_count,
                "last_failure": (
                    datetime.fromtimestamp(breaker.last_failure).isoformat()
                    if breaker.last_failure else None
                ),
                "recovery_time": (
                    datetime.fromtimestamp(breaker.half_open_retry_time).isoformat()
                    if breaker.half_open_retry_time else None
                )
            }
        
        return status


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


async def get_connection_manager(
    pool_size: Optional[int] = None,
    pool_overflow: Optional[int] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None
) -> ConnectionManager:
    """
    Get or create singleton connection manager.
    
    Args are only used on first call to create the instance.
    """
    global _connection_manager
    
    if _connection_manager is None:
        from core.config import settings
        
        _connection_manager = ConnectionManager(
            pool_size=pool_size or settings.connection_pool_size,
            pool_overflow=pool_overflow or settings.connection_pool_overflow,
            timeout=timeout or settings.timeout,
            max_retries=max_retries or settings.max_retries
        )
    
    return _connection_manager