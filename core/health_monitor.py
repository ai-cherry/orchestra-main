"""
Health monitoring system for LLM providers and router components.

This module provides background health checks, availability tracking,
and system status reporting for high availability.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

from core.llm_types import ProviderStatus, RouterHealth
from core.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Overall health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status for a single component"""
    name: str
    status: HealthStatus
    last_check: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """
    System health monitoring with background checks.
    
    Features:
    - Periodic provider health checks
    - Component status tracking
    - Automatic degradation detection
    - Health endpoint data
    """
    
    def __init__(
        self,
        check_interval: int = 60,
        check_timeout: int = 10,
        failure_threshold: int = 3
    ):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Seconds between health checks
            check_timeout: Timeout for individual checks
            failure_threshold: Failures before marking unhealthy
        """
        self.check_interval = check_interval
        self.check_timeout = check_timeout
        self.failure_threshold = failure_threshold
        
        # Component health tracking
        self._components: Dict[str, ComponentHealth] = {}
        self._provider_failures: Dict[str, int] = {}
        
        # Monitoring task
        self._monitor_task: Optional[asyncio.Task] = None
        self._start_time = time.time()
        
        # Health check callbacks
        self._health_checks: Dict[str, Callable] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Start health monitoring"""
        if self._monitor_task is None:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("Health monitoring started")
    
    async def stop(self):
        """Stop health monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            logger.info("Health monitoring stopped")
    
    def register_health_check(self, name: str, check_func: Callable):
        """
        Register a custom health check function.
        
        Args:
            name: Component name
            check_func: Async function that returns (is_healthy, error_message)
        """
        self._health_checks[name] = check_func
        logger.info(f"Registered health check for {name}")
    
    async def check_provider_health(self, provider: str, test_url: str) -> Tuple[bool, Optional[str]]:
        """
        Check health of an LLM provider.
        
        Args:
            provider: Provider name
            test_url: URL to test (e.g., /models endpoint)
        
        Returns:
            Tuple of (is_healthy, error_message)
        """
        try:
            conn_manager = await get_connection_manager()
            
            # Use short timeout for health checks
            async with asyncio.timeout(self.check_timeout):
                async with conn_manager.request(provider, "GET", test_url) as response:
                    return True, None
                    
        except asyncio.TimeoutError:
            return False, "Health check timed out"
        except Exception as e:
            return False, str(e)
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self._run_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def _run_health_checks(self):
        """Run all registered health checks"""
        tasks = []
        
        # Check LLM providers
        providers = {
            "portkey": "/models",
            "openrouter": "/models"
        }
        
        for provider, test_url in providers.items():
            task = asyncio.create_task(self._check_and_update_provider(provider, test_url))
            tasks.append(task)
        
        # Run custom health checks
        for name, check_func in self._health_checks.items():
            task = asyncio.create_task(self._check_and_update_component(name, check_func))
            tasks.append(task)
        
        # Wait for all checks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_and_update_provider(self, provider: str, test_url: str):
        """Check and update provider health status"""
        is_healthy, error_msg = await self.check_provider_health(provider, test_url)
        
        async with self._lock:
            if not is_healthy:
                self._provider_failures[provider] = self._provider_failures.get(provider, 0) + 1
                
                if self._provider_failures[provider] >= self.failure_threshold:
                    status = HealthStatus.UNHEALTHY
                else:
                    status = HealthStatus.DEGRADED
            else:
                self._provider_failures[provider] = 0
                status = HealthStatus.HEALTHY
            
            self._components[f"provider_{provider}"] = ComponentHealth(
                name=f"provider_{provider}",
                status=status,
                last_check=time.time(),
                error_message=error_msg,
                metadata={
                    "failure_count": self._provider_failures[provider]
                }
            )
    
    async def _check_and_update_component(self, name: str, check_func: Callable):
        """Check and update component health status"""
        try:
            is_healthy, error_msg = await check_func()
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            error_msg = str(e)
        
        async with self._lock:
            self._components[name] = ComponentHealth(
                name=name,
                status=status,
                last_check=time.time(),
                error_message=error_msg
            )
    
    async def get_health_status(self) -> RouterHealth:
        """Get overall system health status"""
        async with self._lock:
            # Determine overall status
            statuses = [comp.status for comp in self._components.values()]
            
            if all(s == HealthStatus.HEALTHY for s in statuses):
                overall_status = HealthStatus.HEALTHY
            elif any(s == HealthStatus.UNHEALTHY for s in statuses):
                overall_status = HealthStatus.UNHEALTHY
            else:
                overall_status = HealthStatus.DEGRADED
            
            # Get provider statuses
            providers = []
            for name, component in self._components.items():
                if name.startswith("provider_"):
                    provider_name = name.replace("provider_", "")
                    providers.append(ProviderStatus(
                        name=provider_name,
                        available=component.status == HealthStatus.HEALTHY,
                        last_check=datetime.fromtimestamp(component.last_check).isoformat(),
                        error_rate=component.metadata.get("failure_count", 0) / self.failure_threshold
                    ))
            
            # Get metrics from connection manager
            conn_manager = await get_connection_manager()
            conn_metrics = conn_manager.get_metrics()
            
            # Get cache metrics
            from core.cache_manager import get_cache_manager
            cache_manager = await get_cache_manager()
            cache_metrics = cache_manager.get_metrics()
            
            return RouterHealth(
                status=overall_status.value,
                providers=providers,
                cache_hit_rate=cache_metrics["hit_rate"],
                total_requests=conn_metrics["requests"],
                success_rate=conn_metrics["success_rate"],
                uptime_seconds=time.time() - self._start_time
            )
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed health information"""
        health = await self.get_health_status()
        
        async with self._lock:
            components = {
                name: {
                    "status": comp.status.value,
                    "last_check": datetime.fromtimestamp(comp.last_check).isoformat(),
                    "error": comp.error_message,
                    "metadata": comp.metadata
                }
                for name, comp in self._components.items()
            }
        
        # Get connection manager status
        conn_manager = await get_connection_manager()
        circuit_breakers = conn_manager.get_circuit_breaker_status()
        
        return {
            "overall": health.dict(),
            "components": components,
            "circuit_breakers": circuit_breakers,
            "last_check": datetime.utcnow().isoformat()
        }


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


async def get_health_monitor(
    check_interval: Optional[int] = None,
    check_timeout: Optional[int] = None
) -> HealthMonitor:
    """
    Get or create singleton health monitor.
    
    Args are only used on first call to create the instance.
    """
    global _health_monitor
    
    if _health_monitor is None:
        from core.config import settings
        
        _health_monitor = HealthMonitor(
            check_interval=check_interval or settings.health_check_interval,
            check_timeout=check_timeout or settings.health_check_timeout
        )
        await _health_monitor.start()
    
    return _health_monitor