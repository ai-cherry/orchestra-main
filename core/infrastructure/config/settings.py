"""
Centralized configuration management for Orchestra AI.

This module provides a unified configuration system using Pydantic
for type safety and validation.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseSettings, Field, HttpUrl, SecretStr, validator


class Environment(str, Enum):
    """Application environment."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    TEST = "test"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ServiceSettings(BaseSettings):
    """Base settings for external services."""

    enabled: bool = True
    connection_timeout: int = Field(
        default=5000, description="Connection timeout in ms"
    )
    request_timeout: int = Field(default=30000, description="Request timeout in ms")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(
        default=1.0, description="Initial retry delay in seconds"
    )


class MongoDBSettings(ServiceSettings):
    """MongoDB configuration."""

    uri: SecretStr = Field(..., env="MONGODB_URI")
    database: str = Field(default="orchestra", env="MONGODB_DATABASE")
    max_pool_size: int = Field(default=100, env="MONGODB_MAX_POOL_SIZE")
    min_pool_size: int = Field(default=10, env="MONGODB_MIN_POOL_SIZE")

    class Config:
        env_prefix = "MONGODB_"


class DragonflySettings(ServiceSettings):
    """DragonflyDB (Redis-compatible) configuration."""

    uri: SecretStr = Field(..., env="DRAGONFLY_URI")
    decode_responses: bool = Field(default=True, env="DRAGONFLY_DECODE_RESPONSES")
    max_connections: int = Field(default=50, env="DRAGONFLY_MAX_CONNECTIONS")

    class Config:
        env_prefix = "DRAGONFLY_"


class WeaviateSettings(ServiceSettings):
    """Weaviate vector database configuration."""

    url: HttpUrl = Field(..., env="WEAVIATE_URL")
    api_key: SecretStr = Field(..., env="WEAVIATE_API_KEY")
    timeout_config: Dict[str, int] = Field(
        default={"timeout": 60, "startup": 30}, env="WEAVIATE_TIMEOUT_CONFIG"
    )

    class Config:
        env_prefix = "WEAVIATE_"


class LLMProviderSettings(ServiceSettings):
    """LLM provider configuration."""

    openai_api_key: Optional[SecretStr] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[SecretStr] = Field(None, env="ANTHROPIC_API_KEY")
    openrouter_api_key: Optional[SecretStr] = Field(None, env="OPENROUTER_API_KEY")
    portkey_api_key: Optional[SecretStr] = Field(None, env="PORTKEY_API_KEY")

    default_provider: str = Field(default="openrouter", env="LLM_DEFAULT_PROVIDER")
    default_model: str = Field(default="gpt-4", env="LLM_DEFAULT_MODEL")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")

    class Config:
        env_prefix = "LLM_"


class DeploymentSettings(BaseSettings):
    """Deployment configuration."""

    provider: str = Field(default="digitalocean", env="DEPLOYMENT_PROVIDER")
    region: str = Field(default="sfo3", env="DEPLOYMENT_REGION")
    environment: Environment = Field(default=Environment.DEV, env="ENVIRONMENT")

    # DigitalOcean specific
    digitalocean_token: Optional[SecretStr] = Field(None, env="DIGITALOCEAN_TOKEN")
    droplet_size: str = Field(default="s-2vcpu-4gb", env="DROPLET_SIZE")

    # Pulumi specific
    pulumi_access_token: Optional[SecretStr] = Field(None, env="PULUMI_ACCESS_TOKEN")
    pulumi_stack: str = Field(default="dev", env="PULUMI_STACK")

    class Config:
        env_prefix = "DEPLOYMENT_"


class APISettings(BaseSettings):
    """API server configuration."""

    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8080, env="API_PORT")
    workers: int = Field(default=4, env="API_WORKERS")
    reload: bool = Field(default=False, env="API_RELOAD")

    cors_origins: List[str] = Field(default=["*"], env="API_CORS_ORIGINS")
    cors_credentials: bool = Field(default=True, env="API_CORS_CREDENTIALS")
    cors_methods: List[str] = Field(default=["*"], env="API_CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="API_CORS_HEADERS")

    class Config:
        env_prefix = "API_"


class FeatureFlags(BaseSettings):
    """Feature flags for gradual rollout."""

    use_new_memory_service: bool = Field(default=False, env="FF_USE_NEW_MEMORY_SERVICE")
    use_unified_registry: bool = Field(default=True, env="FF_USE_UNIFIED_REGISTRY")
    enable_shadow_testing: bool = Field(default=False, env="FF_ENABLE_SHADOW_TESTING")
    enable_cost_optimization: bool = Field(
        default=True, env="FF_ENABLE_COST_OPTIMIZATION"
    )
    enable_advanced_routing: bool = Field(
        default=False, env="FF_ENABLE_ADVANCED_ROUTING"
    )

    class Config:
        env_prefix = "FF_"


class Settings(BaseSettings):
    """Main application settings."""

    # Application
    app_name: str = Field(default="Orchestra AI", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEV, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")

    # Services
    mongodb: MongoDBSettings = MongoDBSettings()
    dragonfly: DragonflySettings = DragonflySettings()
    weaviate: WeaviateSettings = WeaviateSettings()
    llm: LLMProviderSettings = LLMProviderSettings()

    # Deployment
    deployment: DeploymentSettings = DeploymentSettings()

    # API
    api: APISettings = APISettings()

    # Feature flags
    features: FeatureFlags = FeatureFlags()

    # Security
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")

    @validator("environment", pre=True)
    def validate_environment(cls, v: str) -> Environment:
        """Validate and convert environment string."""
        try:
            return Environment(v.lower())
        except ValueError:
            return Environment.DEV

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PROD

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEV

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode."""
        return self.environment == Environment.TEST

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings

    if _settings is None:
        _settings = Settings()

    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
