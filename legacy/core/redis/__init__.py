#!/usr/bin/env python3
"""
Redis Integration Package - Resilient Redis with Circuit Breakers and Monitoring
"""

from .resilient_client import (
    ResilientRedisClient,
    AsyncResilientRedisClient,
    InMemoryFallback,
    get_redis_client,
    get_async_redis_client,
    redis_cache,
    redis_health_check
)

from .config import (
    RedisConfig,
    RedisMode,
    get_redis_config,
    REDIS_CONFIGS
)

from .monitoring import (
    RedisHealthMonitor,
    HealthStatus,
    HealthMetric,
    RedisMetrics,
    log_alert_handler,
    webhook_alert_handler
)

from .cache_warming import (
    CacheWarmer,
    PredictiveCacheWarmer,
    ScheduledCacheWarmer,
    WarmingStrategy,
    CacheEntry,
    create_user_data_loader,
    create_computed_data_loader
)

__all__ = [
    # Client
    'ResilientRedisClient',
    'AsyncResilientRedisClient',
    'InMemoryFallback',
    'get_redis_client',
    'get_async_redis_client',
    'redis_cache',
    'redis_health_check',
    
    # Config
    'RedisConfig',
    'RedisMode',
    'get_redis_config',
    'REDIS_CONFIGS',
    
    # Monitoring
    'RedisHealthMonitor',
    'HealthStatus',
    'HealthMetric',
    'RedisMetrics',
    'log_alert_handler',
    'webhook_alert_handler',
    
    # Cache Warming
    'CacheWarmer',
    'PredictiveCacheWarmer',
    'ScheduledCacheWarmer',
    'WarmingStrategy',
    'CacheEntry',
    'create_user_data_loader',
    'create_computed_data_loader'
]


# Quick setup function
def setup_redis(
    env: str = None,
    enable_monitoring: bool = True,
    enable_cache_warming: bool = True,
    fallback_handler=None
):
    """
    Quick setup for Redis with all features
    
    Args:
        env: Environment name (development, staging, production)
        enable_monitoring: Enable health monitoring
        enable_cache_warming: Enable cache warming
        fallback_handler: Custom fallback handler
        
    Returns:
        Tuple of (redis_client, monitor, warmer)
    """
    # Get configuration
    config = get_redis_config(env)
    
    # Create client with fallback
    if fallback_handler is None:
        fallback_handler = InMemoryFallback()
        
    client = ResilientRedisClient(
        redis_url=config.url,
        max_connections=config.max_connections,
        socket_timeout=config.socket_timeout,
        socket_connect_timeout=config.connection_timeout,
        retry_on_timeout=config.retry_on_timeout,
        health_check_interval=config.health_check_interval,
        circuit_breaker_config={
            "failure_threshold": config.circuit_breaker_failure_threshold,
            "recovery_timeout": config.circuit_breaker_recovery_timeout
        },
        fallback_handler=fallback_handler,
        sentinel_hosts=config.sentinel_hosts,
        sentinel_service_name=config.sentinel_service_name
    )
    
    # Setup monitoring
    monitor = None
    if enable_monitoring:
        monitor = RedisHealthMonitor()
        monitor.add_alert_handler(log_alert_handler)
        monitor.start_monitoring(client)
    
    # Setup cache warming
    warmer = None
    if enable_cache_warming:
        warmer = PredictiveCacheWarmer(
            redis_client=client,
            warming_strategy=WarmingStrategy.PREDICTIVE
        )
    
    return client, monitor, warmer