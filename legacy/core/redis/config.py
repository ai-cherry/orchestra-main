#!/usr/bin/env python3
"""
Redis Configuration and Connection Management
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class RedisMode(Enum):
    """Redis deployment modes"""
    STANDALONE = "standalone"
    SENTINEL = "sentinel"
    CLUSTER = "cluster"


@dataclass
class RedisConfig:
    """Redis configuration"""
    # Connection settings
    url: str = "redis://localhost:6379"
    mode: RedisMode = RedisMode.STANDALONE
    
    # Connection pool settings
    max_connections: int = 50
    min_idle_connections: int = 10
    connection_timeout: int = 5
    socket_timeout: int = 5
    socket_keepalive: bool = True
    retry_on_timeout: bool = True
    
    # Health check settings
    health_check_interval: int = 30
    
    # Circuit breaker settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60
    circuit_breaker_half_open_requests: int = 3
    
    # Retry settings
    max_retries: int = 3
    retry_backoff_base: float = 0.1
    retry_backoff_max: float = 10.0
    
    # Sentinel settings (for HA)
    sentinel_hosts: Optional[List[tuple]] = None
    sentinel_service_name: Optional[str] = None
    sentinel_password: Optional[str] = None
    
    # Cluster settings
    cluster_nodes: Optional[List[str]] = None
    cluster_skip_full_coverage_check: bool = False
    
    # Cache settings
    default_ttl: int = 300  # 5 minutes
    max_ttl: int = 86400    # 24 hours
    
    # Memory settings
    max_memory: Optional[str] = "2gb"
    max_memory_policy: str = "allkeys-lru"
    
    # Performance settings
    enable_pipelining: bool = True
    pipeline_size: int = 100
    
    # Monitoring
    enable_metrics: bool = True
    metrics_prefix: str = "redis"
    
    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create config from environment variables"""
        config = cls()
        
        # Basic connection
        config.url = os.getenv("REDIS_URL", config.url)
        
        # Mode
        mode_str = os.getenv("REDIS_MODE", "standalone").lower()
        config.mode = RedisMode(mode_str)
        
        # Connection pool
        if val := os.getenv("REDIS_MAX_CONNECTIONS"):
            config.max_connections = int(val)
        if val := os.getenv("REDIS_CONNECTION_TIMEOUT"):
            config.connection_timeout = int(val)
        if val := os.getenv("REDIS_SOCKET_TIMEOUT"):
            config.socket_timeout = int(val)
            
        # Circuit breaker
        if val := os.getenv("REDIS_CIRCUIT_BREAKER_ENABLED"):
            config.circuit_breaker_enabled = val.lower() == "true"
        if val := os.getenv("REDIS_CIRCUIT_BREAKER_THRESHOLD"):
            config.circuit_breaker_failure_threshold = int(val)
            
        # Sentinel
        if val := os.getenv("REDIS_SENTINEL_HOSTS"):
            # Format: host1:port1,host2:port2
            config.sentinel_hosts = [
                (h.split(":")[0], int(h.split(":")[1]))
                for h in val.split(",")
            ]
        config.sentinel_service_name = os.getenv("REDIS_SENTINEL_SERVICE", "mymaster")
        config.sentinel_password = os.getenv("REDIS_SENTINEL_PASSWORD")
        
        # Cluster
        if val := os.getenv("REDIS_CLUSTER_NODES"):
            config.cluster_nodes = val.split(",")
            
        # Cache
        if val := os.getenv("REDIS_DEFAULT_TTL"):
            config.default_ttl = int(val)
        if val := os.getenv("REDIS_MAX_TTL"):
            config.max_ttl = int(val)
            
        # Memory
        config.max_memory = os.getenv("REDIS_MAX_MEMORY", config.max_memory)
        config.max_memory_policy = os.getenv("REDIS_MAX_MEMORY_POLICY", config.max_memory_policy)
        
        return config
    
    def to_connection_kwargs(self) -> Dict[str, Any]:
        """Convert to Redis connection kwargs"""
        kwargs = {
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.connection_timeout,
            "socket_keepalive": self.socket_keepalive,
            "socket_keepalive_options": {},
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
        }
        
        # Add decode_responses for string handling
        kwargs["decode_responses"] = True
        
        return kwargs


# Predefined configurations for different environments
REDIS_CONFIGS = {
    "development": RedisConfig(
        url="redis://localhost:6379",
        max_connections=20,
        circuit_breaker_enabled=False,
        enable_metrics=False
    ),
    
    "testing": RedisConfig(
        url="redis://localhost:6379",
        max_connections=10,
        circuit_breaker_enabled=True,
        circuit_breaker_failure_threshold=3,
        default_ttl=60
    ),
    
    "staging": RedisConfig(
        url="redis://redis-staging:6379",
        max_connections=50,
        circuit_breaker_enabled=True,
        enable_metrics=True,
        mode=RedisMode.SENTINEL,
        sentinel_hosts=[
            ("sentinel-1", 26379),
            ("sentinel-2", 26379),
            ("sentinel-3", 26379)
        ],
        sentinel_service_name="redis-master"
    ),
    
    "production": RedisConfig(
        url="redis://redis-prod:6379",
        max_connections=100,
        min_idle_connections=20,
        circuit_breaker_enabled=True,
        enable_metrics=True,
        mode=RedisMode.CLUSTER,
        cluster_nodes=[
            "redis-node-1:6379",
            "redis-node-2:6379",
            "redis-node-3:6379"
        ],
        max_memory="4gb",
        max_memory_policy="volatile-lru"
    )
}


def get_redis_config(env: Optional[str] = None) -> RedisConfig:
    """Get Redis configuration for environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")
    
    # Start with predefined config
    if env in REDIS_CONFIGS:
        config = REDIS_CONFIGS[env]
    else:
        config = RedisConfig()
    
    # Override with environment variables
    env_config = RedisConfig.from_env()
    
    # Merge configurations (env vars take precedence)
    for field in config.__dataclass_fields__:
        env_value = getattr(env_config, field)
        default_value = getattr(RedisConfig(), field)
        if env_value != default_value:
            setattr(config, field, env_value)
    
    return config