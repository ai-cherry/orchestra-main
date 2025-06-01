"""
Centralized configuration management for the LLM routing system.

This module provides a single source of truth for all configuration,
with validation, environment variable loading, and default values.
"""

import os
from typing import Optional, Dict, Any
from functools import lru_cache
from pydantic import BaseSettings, validator, Field
from core.llm_types import RouterConfig


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables with
    the same name in uppercase (e.g., portkey_api_key -> PORTKEY_API_KEY).
    """
    
    # API Keys
    portkey_api_key: str = Field(default="", env="PORTKEY_API_KEY")
    portkey_config: str = Field(default="", env="PORTKEY_CONFIG")
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://localhost/orchestra",
        env="DATABASE_URL"
    )
    
    # Performance settings
    connection_pool_size: int = Field(default=2, env="CONNECTION_POOL_SIZE")
    connection_pool_overflow: int = Field(default=3, env="CONNECTION_POOL_OVERFLOW")
    db_pool_size: int = Field(default=2, env="DB_POOL_SIZE")
    db_pool_overflow: int = Field(default=3, env="DB_POOL_OVERFLOW")
    
    # Cache settings
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    cache_memory_limit_mb: int = Field(default=100, env="CACHE_MEMORY_LIMIT_MB")
    
    # Feature flags
    enable_fallback: bool = Field(default=True, env="ENABLE_FALLBACK")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    enable_batching: bool = Field(default=False, env="ENABLE_BATCHING")
    
    # Request settings
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    batch_timeout_ms: int = Field(default=100, env="BATCH_TIMEOUT_MS")
    
    # Health check settings
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    
    # Monitoring settings
    metrics_retention_days: int = Field(default=30, env="METRICS_RETENTION_DAYS")
    metrics_aggregation_interval: int = Field(default=3600, env="METRICS_AGGREGATION_INTERVAL")
    
    # Application metadata
    app_name: str = Field(default="Orchestra AI", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    @validator("database_url")
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses async driver"""
        if v and "postgresql://" in v and "+asyncpg" not in v:
            # Convert to async URL
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v
    
    @validator("portkey_api_key", "openrouter_api_key")
    def validate_api_keys(cls, v: str, field) -> str:
        """Validate API keys are present"""
        if not v and field.name == "portkey_api_key":
            # At least one API key should be present
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
            if not openrouter_key:
                raise ValueError("At least one API key (Portkey or OpenRouter) must be provided")
        return v
    
    def to_router_config(self) -> RouterConfig:
        """Convert settings to RouterConfig"""
        return RouterConfig(
            portkey_api_key=self.portkey_api_key,
            portkey_config=self.portkey_config,
            openrouter_api_key=self.openrouter_api_key,
            enable_fallback=self.enable_fallback,
            enable_caching=self.enable_caching,
            cache_ttl=self.cache_ttl,
            max_retries=self.max_retries,
            timeout=self.timeout,
            enable_monitoring=self.enable_monitoring,
            connection_pool_size=self.connection_pool_size,
            connection_pool_overflow=self.connection_pool_overflow,
            cache_max_size=self.cache_max_size,
            cache_memory_limit_mb=self.cache_memory_limit_mb,
            database_url=self.database_url,
            db_pool_size=self.db_pool_size,
            db_pool_overflow=self.db_pool_overflow
        )
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function returns a singleton instance of Settings,
    ensuring configuration is loaded only once.
    """
    return Settings()


def get_router_config() -> RouterConfig:
    """Get router configuration from settings"""
    return get_settings().to_router_config()


# Export commonly used settings
settings = get_settings()