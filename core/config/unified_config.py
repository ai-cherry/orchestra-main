"""
Unified Configuration System for Orchestra AI

This module provides a centralized, type-safe configuration system that replaces
all scattered configuration patterns throughout the codebase.

Key Features:
- Hierarchical configuration with environment-specific overrides
- Type-safe configuration classes with validation
- Consistent environment variable handling
- Hot-reloading for development
- Configuration schema documentation
"""

import os
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from functools import lru_cache
import json
import yaml

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Type variable for configuration classes
ConfigT = TypeVar('ConfigT', bound='BaseConfig')

class Environment(str, Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class LogLevel(str, Enum):
    """Supported log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class BaseConfig(BaseModel, ABC):
    """
    Abstract base class for all configuration sections.
    
    Provides common validation and serialization capabilities.
    """
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        validate_assignment = True
        arbitrary_types_allowed = True
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate configuration values and dependencies"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return self.dict(exclude_none=True)

class DatabaseConfig(BaseConfig):
    """Database configuration for PostgreSQL and Weaviate"""
    
    # PostgreSQL Configuration
    postgresql_host: str = Field(default="localhost", env="POSTGRESQL_HOST")
    postgresql_port: int = Field(default=5432, env="POSTGRESQL_PORT")
    postgresql_database: str = Field(default="orchestra", env="POSTGRESQL_DATABASE")
    postgresql_username: str = Field(default="postgres", env="POSTGRESQL_USERNAME")
    postgresql_password: str = Field(default="", env="POSTGRESQL_PASSWORD")
    postgresql_ssl_mode: str = Field(default="prefer", env="POSTGRESQL_SSL_MODE")
    postgresql_pool_size: int = Field(default=10, env="POSTGRESQL_POOL_SIZE")
    postgresql_max_overflow: int = Field(default=20, env="POSTGRESQL_MAX_OVERFLOW")
    
    # Weaviate Configuration  
    weaviate_host: str = Field(default="localhost", env="WEAVIATE_HOST")
    weaviate_port: int = Field(default=8080, env="WEAVIATE_PORT")
    weaviate_scheme: str = Field(default="http", env="WEAVIATE_SCHEME")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    weaviate_timeout: int = Field(default=30, env="WEAVIATE_TIMEOUT")
    
    # Connection Settings
    connection_timeout: int = Field(default=30, env="DB_CONNECTION_TIMEOUT")
    retry_attempts: int = Field(default=3, env="DB_RETRY_ATTEMPTS")
    
    @property
    def postgresql_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        password_part = f":{self.postgresql_password}" if self.postgresql_password else ""
        return (
            f"postgresql://{self.postgresql_username}{password_part}"
            f"@{self.postgresql_host}:{self.postgresql_port}/{self.postgresql_database}"
            f"?sslmode={self.postgresql_ssl_mode}"
        )
    
    @property
    def weaviate_url(self) -> str:
        """Generate Weaviate connection URL"""
        return f"{self.weaviate_scheme}://{self.weaviate_host}:{self.weaviate_port}"
    
    def validate_config(self) -> bool:
        """Validate database configuration"""
        if not self.postgresql_host or not self.postgresql_database:
            return False
        if not self.weaviate_host:
            return False
        return True

class LLMConfig(BaseConfig):
    """LLM provider configuration"""
    
    # Provider API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    portkey_api_key: Optional[str] = Field(default=None, env="PORTKEY_API_KEY")
    portkey_config: Optional[str] = Field(default=None, env="PORTKEY_CONFIG")
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    
    # Routing Configuration
    enable_fallback: bool = Field(default=True, env="LLM_ENABLE_FALLBACK")
    enable_caching: bool = Field(default=True, env="LLM_ENABLE_CACHING")
    cache_ttl: int = Field(default=3600, env="LLM_CACHE_TTL")
    max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    timeout: int = Field(default=30, env="LLM_TIMEOUT")
    
    # Model Defaults
    default_model: str = Field(default="anthropic/claude-3-sonnet", env="LLM_DEFAULT_MODEL")
    default_temperature: float = Field(default=0.7, env="LLM_DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=2048, env="LLM_DEFAULT_MAX_TOKENS")
    
    # Rate Limiting
    requests_per_minute: int = Field(default=60, env="LLM_REQUESTS_PER_MINUTE")
    tokens_per_minute: int = Field(default=100000, env="LLM_TOKENS_PER_MINUTE")
    
    def validate_config(self) -> bool:
        """Validate LLM configuration"""
        # At least one provider API key must be configured
        api_keys = [
            self.openai_api_key,
            self.anthropic_api_key,
            self.google_api_key,
            self.portkey_api_key,
            self.openrouter_api_key
        ]
        return any(key for key in api_keys)

class APIConfig(BaseConfig):
    """API server configuration"""
    
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="API_DEBUG")
    reload: bool = Field(default=False, env="API_RELOAD")
    workers: int = Field(default=1, env="API_WORKERS")
    
    # Security
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    secret_key: str = Field(default="dev-secret-key", env="API_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="API_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], env="API_CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="API_CORS_ALLOW_CREDENTIALS")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=1000, env="API_RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="API_RATE_LIMIT_WINDOW")
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v, info=None):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    def validate_config(self) -> bool:
        """Validate API configuration"""
        return self.port > 0 and self.port < 65536

class MonitoringConfig(BaseConfig):
    """Monitoring and observability configuration"""
    
    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    log_format: str = Field(default="text", env="LOG_FORMAT")  # text or json
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_rotation: bool = Field(default=True, env="LOG_ROTATION")
    log_max_size: str = Field(default="100MB", env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    metrics_path: str = Field(default="/metrics", env="METRICS_PATH")
    
    # Health Checks
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    
    # Tracing
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    jaeger_endpoint: Optional[str] = Field(default=None, env="JAEGER_ENDPOINT")
    
    def validate_config(self) -> bool:
        """Validate monitoring configuration"""
        return self.metrics_port > 0 and self.metrics_port < 65536

class MemoryConfig(BaseConfig):
    """Memory system configuration"""
    
    # Memory Backend
    backend: str = Field(default="hybrid", env="MEMORY_BACKEND")  # postgresql, weaviate, hybrid
    
    # Memory Limits
    max_context_length: int = Field(default=8192, env="MEMORY_MAX_CONTEXT_LENGTH")
    max_memories_per_session: int = Field(default=1000, env="MEMORY_MAX_MEMORIES_PER_SESSION")
    memory_cleanup_interval: int = Field(default=3600, env="MEMORY_CLEANUP_INTERVAL")
    
    # Embedding Configuration
    embedding_model: str = Field(default="openai/text-embedding-3-small", env="MEMORY_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, env="MEMORY_EMBEDDING_DIMENSIONS")
    
    # Similarity Search
    similarity_threshold: float = Field(default=0.7, env="MEMORY_SIMILARITY_THRESHOLD")
    max_search_results: int = Field(default=10, env="MEMORY_MAX_SEARCH_RESULTS")
    
    # Caching
    enable_memory_cache: bool = Field(default=True, env="MEMORY_ENABLE_CACHE")
    memory_cache_ttl: int = Field(default=1800, env="MEMORY_CACHE_TTL")
    
    def validate_config(self) -> bool:
        """Validate memory configuration"""
        valid_backends = ["postgresql", "weaviate", "hybrid"]
        return self.backend in valid_backends

class OrchestrationConfig(BaseConfig):
    """Orchestration system configuration"""
    
    # Agent Configuration
    max_concurrent_agents: int = Field(default=10, env="ORCHESTRATION_MAX_CONCURRENT_AGENTS")
    agent_timeout: int = Field(default=300, env="ORCHESTRATION_AGENT_TIMEOUT")
    agent_retry_attempts: int = Field(default=3, env="ORCHESTRATION_AGENT_RETRY_ATTEMPTS")
    
    # Workflow Configuration
    max_workflow_steps: int = Field(default=100, env="ORCHESTRATION_MAX_WORKFLOW_STEPS")
    workflow_timeout: int = Field(default=1800, env="ORCHESTRATION_WORKFLOW_TIMEOUT")
    
    # Event Processing
    event_queue_size: int = Field(default=1000, env="ORCHESTRATION_EVENT_QUEUE_SIZE")
    event_processing_interval: int = Field(default=1, env="ORCHESTRATION_EVENT_PROCESSING_INTERVAL")
    
    # Resource Limits
    max_memory_usage: str = Field(default="1GB", env="ORCHESTRATION_MAX_MEMORY_USAGE")
    max_cpu_usage: float = Field(default=0.8, env="ORCHESTRATION_MAX_CPU_USAGE")
    
    def validate_config(self) -> bool:
        """Validate orchestration configuration"""
        return (
            self.max_concurrent_agents > 0 and
            self.agent_timeout > 0 and
            self.max_workflow_steps > 0
        )

class UnifiedOrchestraConfig(BaseSettings):
    """
    Main configuration class that unifies all Orchestra AI settings.
    
    This class serves as the single source of truth for all configuration
    and provides environment-specific overrides.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="allow"
    )
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")
    
    # Project Information
    project_name: str = Field(default="Orchestra AI", env="PROJECT_NAME")
    project_version: str = Field(default="1.0.0", env="PROJECT_VERSION")
    project_description: str = Field(default="AI Orchestration Platform", env="PROJECT_DESCRIPTION")
    
    # Configuration Sections
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)
    
    # Feature Flags
    enable_mcp_integration: bool = Field(default=True, env="ENABLE_MCP_INTEGRATION")
    enable_voice_synthesis: bool = Field(default=False, env="ENABLE_VOICE_SYNTHESIS")
    enable_web_scraping: bool = Field(default=True, env="ENABLE_WEB_SCRAPING")
    enable_real_agents: bool = Field(default=True, env="ENABLE_REAL_AGENTS")
    
    def validate_all_configs(self) -> bool:
        """Validate all configuration sections"""
        validations = [
            self.database.validate_config(),
            self.llm.validate_config(),
            self.api.validate_config(),
            self.monitoring.validate_config(),
            self.memory.validate_config(),
            self.orchestration.validate_config()
        ]
        return all(validations)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "testing": self.testing,
            "project_name": self.project_name,
            "project_version": self.project_version,
            "database_configured": bool(self.database.postgresql_host and self.database.weaviate_host),
            "llm_providers_configured": self.llm.validate_config(),
            "api_port": self.api.port,
            "monitoring_enabled": self.monitoring.enable_metrics,
            "memory_backend": self.memory.backend,
            "feature_flags": {
                "mcp_integration": self.enable_mcp_integration,
                "voice_synthesis": self.enable_voice_synthesis,
                "web_scraping": self.enable_web_scraping,
                "real_agents": self.enable_real_agents
            }
        }

# Global configuration instance
_config_instance: Optional[UnifiedOrchestraConfig] = None

@lru_cache(maxsize=1)
def get_config() -> UnifiedOrchestraConfig:
    """
    Get the global configuration instance.
    
    This function provides a cached singleton configuration that can be
    imported and used throughout the application.
    
    Returns:
        UnifiedOrchestraConfig: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = UnifiedOrchestraConfig()
    return _config_instance

def reload_config() -> UnifiedOrchestraConfig:
    """
    Force reload of configuration from environment/files.
    
    Useful for development and testing scenarios where configuration
    might change at runtime.
    
    Returns:
        UnifiedOrchestraConfig: The reloaded configuration instance
    """
    global _config_instance
    get_config.cache_clear()
    _config_instance = None
    return get_config()

def create_config_from_dict(config_dict: Dict[str, Any]) -> UnifiedOrchestraConfig:
    """
    Create configuration instance from dictionary.
    
    Useful for testing and programmatic configuration.
    
    Args:
        config_dict: Configuration dictionary
        
    Returns:
        UnifiedOrchestraConfig: Configuration instance
    """
    return UnifiedOrchestraConfig(**config_dict)

def save_config_to_file(config: UnifiedOrchestraConfig, file_path: Path, format: str = "yaml") -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration instance to save
        file_path: Path to save configuration
        format: File format (yaml or json)
    """
    config_dict = config.dict(exclude_none=True)
    
    if format.lower() == "yaml":
        with open(file_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    elif format.lower() == "json":
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

def load_config_from_file(file_path: Path) -> UnifiedOrchestraConfig:
    """
    Load configuration from file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        UnifiedOrchestraConfig: Configuration instance
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    if file_path.suffix.lower() in ['.yaml', '.yml']:
        with open(file_path, 'r') as f:
            config_dict = yaml.safe_load(f)
    elif file_path.suffix.lower() == '.json':
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    return create_config_from_dict(config_dict)

# Convenience functions for accessing specific configuration sections
def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_config().database

def get_llm_config() -> LLMConfig:
    """Get LLM configuration"""
    return get_config().llm

def get_api_config() -> APIConfig:
    """Get API configuration"""
    return get_config().api

def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration"""
    return get_config().monitoring

def get_memory_config() -> MemoryConfig:
    """Get memory configuration"""
    return get_config().memory

def get_orchestration_config() -> OrchestrationConfig:
    """Get orchestration configuration"""
    return get_config().orchestration

# Export main configuration function
__all__ = [
    "UnifiedOrchestraConfig",
    "DatabaseConfig",
    "LLMConfig", 
    "APIConfig",
    "MonitoringConfig",
    "MemoryConfig",
    "OrchestrationConfig",
    "Environment",
    "LogLevel",
    "get_config",
    "reload_config",
    "get_database_config",
    "get_llm_config",
    "get_api_config",
    "get_monitoring_config",
    "get_memory_config",
    "get_orchestration_config"
] 