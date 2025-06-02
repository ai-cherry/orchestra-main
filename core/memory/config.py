"""
Memory System Configuration

Centralized configuration management for the memory system with
validation, environment variable support, and type safety.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from enum import Enum
import json
from pathlib import Path

from .exceptions import MemoryConfigurationError

class Environment(Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    
    @classmethod
    def from_string(cls, value: str) -> 'Environment':
        """Create from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            raise MemoryConfigurationError(
                config_section="environment",
                parameter="ORCHESTRA_ENV",
                value=value,
                reason=f"Invalid environment. Must be one of: {', '.join(e.value for e in cls)}"
            )

@dataclass
class TierConfig:
    """Configuration for a single memory tier."""
    enabled: bool = True
    max_size_bytes: int = 1_073_741_824  # 1GB default
    max_items: int = 1_000_000
    ttl_seconds: Optional[int] = None
    eviction_policy: str = "lru"  # lru, lfu, fifo
    
    def validate(self, tier_name: str) -> None:
        """Validate tier configuration."""
        if self.max_size_bytes <= 0:
            raise MemoryConfigurationError(
                config_section=f"tier.{tier_name}",
                parameter="max_size_bytes",
                value=self.max_size_bytes,
                reason="Must be positive"
            )
            
        if self.max_items <= 0:
            raise MemoryConfigurationError(
                config_section=f"tier.{tier_name}",
                parameter="max_items",
                value=self.max_items,
                reason="Must be positive"
            )
            
        valid_policies = {"lru", "lfu", "fifo"}
        if self.eviction_policy not in valid_policies:
            raise MemoryConfigurationError(
                config_section=f"tier.{tier_name}",
                parameter="eviction_policy",
                value=self.eviction_policy,
                reason=f"Must be one of: {', '.join(valid_policies)}"
            )

@dataclass
class PostgreSQLConfig:
    """PostgreSQL configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "orchestra"
    user: str = "orchestra"
    password: str = ""
    pool_size_min: int = 10
    pool_size_max: int = 50
    connection_timeout: int = 10
    command_timeout: int = 30
    ssl_mode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    
    # Performance settings
    statement_cache_size: int = 1000
    max_queries: int = 50000
    
    def validate(self) -> None:
        """Validate PostgreSQL configuration."""
        if not self.host:
            raise MemoryConfigurationError(
                config_section="postgresql",
                parameter="host",
                value=self.host,
                reason="Host cannot be empty"
            )
            
        if not 1 <= self.port <= 65535:
            raise MemoryConfigurationError(
                config_section="postgresql",
                parameter="port",
                value=self.port,
                reason="Port must be between 1 and 65535"
            )
            
        if self.pool_size_min > self.pool_size_max:
            raise MemoryConfigurationError(
                config_section="postgresql",
                parameter="pool_size",
                value=f"min={self.pool_size_min}, max={self.pool_size_max}",
                reason="Minimum pool size cannot exceed maximum"
            )
            
        valid_ssl_modes = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
        if self.ssl_mode not in valid_ssl_modes:
            raise MemoryConfigurationError(
                config_section="postgresql",
                parameter="ssl_mode",
                value=self.ssl_mode,
                reason=f"Must be one of: {', '.join(valid_ssl_modes)}"
            )
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/"
            f"{self.database}?sslmode={self.ssl_mode}"
        )

@dataclass
class WeaviateConfig:
    """Weaviate configuration."""
    url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    startup_period: int = 0
    connection_pool_size: int = 100
    batch_size: int = 1000
    
    # Schema settings
    schema_name: str = "OrchestraMemory"
    replication_factor: int = 1
    
    def validate(self) -> None:
        """Validate Weaviate configuration."""
        if not self.url:
            raise MemoryConfigurationError(
                config_section="weaviate",
                parameter="url",
                value=self.url,
                reason="URL cannot be empty"
            )
            
        if self.batch_size <= 0:
            raise MemoryConfigurationError(
                config_section="weaviate",
                parameter="batch_size",
                value=self.batch_size,
                reason="Batch size must be positive"
            )

@dataclass
class RedisConfig:
    """Redis configuration for shared memory tier."""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    max_connections: int = 100
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    
    # Cluster settings
    cluster_enabled: bool = False
    cluster_nodes: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate Redis configuration."""
        if not self.host and not self.cluster_nodes:
            raise MemoryConfigurationError(
                config_section="redis",
                parameter="host",
                value=self.host,
                reason="Host or cluster nodes must be specified"
            )
            
        if not 0 <= self.database <= 15:
            raise MemoryConfigurationError(
                config_section="redis",
                parameter="database",
                value=self.database,
                reason="Database must be between 0 and 15"
            )

@dataclass
class OptimizationConfig:
    """Memory optimization configuration."""
    enabled: bool = True
    
    # Access pattern analysis
    access_history_size: int = 1000
    promotion_threshold: int = 10  # Access count before promotion
    demotion_threshold_hours: int = 24  # Hours without access before demotion
    
    # Prefetching
    prefetch_enabled: bool = True
    prefetch_limit: int = 10
    prefetch_probability_threshold: float = 0.7
    
    # Background tasks
    optimization_interval_seconds: int = 300  # 5 minutes
    cleanup_interval_seconds: int = 3600  # 1 hour
    
    def validate(self) -> None:
        """Validate optimization configuration."""
        if self.promotion_threshold <= 0:
            raise MemoryConfigurationError(
                config_section="optimization",
                parameter="promotion_threshold",
                value=self.promotion_threshold,
                reason="Must be positive"
            )
            
        if not 0.0 <= self.prefetch_probability_threshold <= 1.0:
            raise MemoryConfigurationError(
                config_section="optimization",
                parameter="prefetch_probability_threshold",
                value=self.prefetch_probability_threshold,
                reason="Must be between 0.0 and 1.0"
            )

@dataclass
class MetricsConfig:
    """Metrics collection configuration."""
    enabled: bool = True
    
    # Prometheus settings
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    # Retention
    metrics_retention_hours: int = 168  # 7 days
    
    # Sampling
    sampling_rate: float = 1.0  # 1.0 = 100% sampling
    
    def validate(self) -> None:
        """Validate metrics configuration."""
        if not 0.0 <= self.sampling_rate <= 1.0:
            raise MemoryConfigurationError(
                config_section="metrics",
                parameter="sampling_rate",
                value=self.sampling_rate,
                reason="Must be between 0.0 and 1.0"
            )

@dataclass
class MemoryConfig:
    """
    Complete memory system configuration.
    
    This is the root configuration object that contains all subsystem configs.
    """
    environment: Environment = Environment.DEVELOPMENT
    
    # Tier configurations
    tiers: Dict[str, TierConfig] = field(default_factory=lambda: {
        "l0_cpu_cache": TierConfig(max_size_bytes=10_485_760, max_items=10_000),  # 10MB
        "l1_process": TierConfig(max_size_bytes=1_073_741_824, max_items=100_000),  # 1GB
        "l2_shared": TierConfig(max_size_bytes=4_294_967_296, max_items=1_000_000),  # 4GB
        "l3_postgresql": TierConfig(max_size_bytes=107_374_182_400, max_items=10_000_000),  # 100GB
        "l4_weaviate": TierConfig(max_size_bytes=1_099_511_627_776, max_items=100_000_000),  # 1TB
    })
    
    # Backend configurations
    postgresql: PostgreSQLConfig = field(default_factory=PostgreSQLConfig)
    weaviate: WeaviateConfig = field(default_factory=WeaviateConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # Feature configurations
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    
    # Global settings
    default_ttl_seconds: Optional[int] = None
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    
    # Performance settings
    max_concurrent_operations: int = 1000
    operation_timeout_seconds: int = 30
    
    def validate(self) -> None:
        """Validate entire configuration."""
        # Validate tier configs
        for tier_name, tier_config in self.tiers.items():
            tier_config.validate(tier_name)
            
        # Validate backend configs
        self.postgresql.validate()
        self.weaviate.validate()
        self.redis.validate()
        
        # Validate feature configs
        self.optimization.validate()
        self.metrics.validate()
        
        # Validate global settings
        if self.encryption_enabled and not self.encryption_key:
            raise MemoryConfigurationError(
                config_section="global",
                parameter="encryption_key",
                value="None",
                reason="Encryption key required when encryption is enabled"
            )
            
        if self.max_concurrent_operations <= 0:
            raise MemoryConfigurationError(
                config_section="global",
                parameter="max_concurrent_operations",
                value=self.max_concurrent_operations,
                reason="Must be positive"
            )
    
    @classmethod
    def from_env(cls) -> 'MemoryConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Environment
        if env := os.getenv("ORCHESTRA_ENV"):
            config.environment = Environment.from_string(env)
            
        # PostgreSQL
        if host := os.getenv("POSTGRES_HOST"):
            config.postgresql.host = host
        if port := os.getenv("POSTGRES_PORT"):
            config.postgresql.port = int(port)
        if db := os.getenv("POSTGRES_DB"):
            config.postgresql.database = db
        if user := os.getenv("POSTGRES_USER"):
            config.postgresql.user = user
        if password := os.getenv("POSTGRES_PASSWORD"):
            config.postgresql.password = password
            
        # Weaviate
        if url := os.getenv("WEAVIATE_URL"):
            config.weaviate.url = url
        if api_key := os.getenv("WEAVIATE_API_KEY"):
            config.weaviate.api_key = api_key
            
        # Redis
        if host := os.getenv("REDIS_HOST"):
            config.redis.host = host
        if port := os.getenv("REDIS_PORT"):
            config.redis.port = int(port)
        if password := os.getenv("REDIS_PASSWORD"):
            config.redis.password = password
            
        # Encryption
        if key := os.getenv("ORCHESTRA_ENCRYPTION_KEY"):
            config.encryption_enabled = True
            config.encryption_key = key
            
        return config
    
    @classmethod
    def from_file(cls, path: Path) -> 'MemoryConfig':
        """Load configuration from JSON file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            raise MemoryConfigurationError(
                config_section="file",
                parameter="path",
                value=str(path),
                reason=f"Failed to load configuration file: {str(e)}",
                cause=e
            )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryConfig':
        """Create configuration from dictionary."""
        # This would need proper deserialization logic
        # For now, keeping it simple
        config = cls()
        
        if "environment" in data:
            config.environment = Environment.from_string(data["environment"])
            
        # Update other fields as needed
        # ... (implementation details)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "tiers": {
                name: {
                    "enabled": tier.enabled,
                    "max_size_bytes": tier.max_size_bytes,
                    "max_items": tier.max_items,
                    "ttl_seconds": tier.ttl_seconds,
                    "eviction_policy": tier.eviction_policy,
                }
                for name, tier in self.tiers.items()
            },
            "postgresql": {
                "host": self.postgresql.host,
                "port": self.postgresql.port,
                "database": self.postgresql.database,
                "user": self.postgresql.user,
                # Don't include password in dict
                "pool_size_min": self.postgresql.pool_size_min,
                "pool_size_max": self.postgresql.pool_size_max,
            },
            "weaviate": {
                "url": self.weaviate.url,
                "batch_size": self.weaviate.batch_size,
                "schema_name": self.weaviate.schema_name,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "database": self.redis.database,
                "max_connections": self.redis.max_connections,
            },
            "optimization": {
                "enabled": self.optimization.enabled,
                "promotion_threshold": self.optimization.promotion_threshold,
                "prefetch_enabled": self.optimization.prefetch_enabled,
            },
            "metrics": {
                "enabled": self.metrics.enabled,
                "prometheus_enabled": self.metrics.prometheus_enabled,
                "sampling_rate": self.metrics.sampling_rate,
            },
            "global": {
                "default_ttl_seconds": self.default_ttl_seconds,
                "compression_enabled": self.compression_enabled,
                "encryption_enabled": self.encryption_enabled,
                "max_concurrent_operations": self.max_concurrent_operations,
            }
        }

# Global configuration instance
_config: Optional[MemoryConfig] = None

def get_config() -> MemoryConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = MemoryConfig.from_env()
        _config.validate()
    return _config

def set_config(config: MemoryConfig) -> None:
    """Set the global configuration instance."""
    global _config
    config.validate()
    _config = config

def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = None