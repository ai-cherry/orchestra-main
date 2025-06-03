"""
"""
    "Settings",
    "get_settings",
    "get_router_config",
    "settings",
]

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    portkey_api_key: str = Field(default="", env="PORTKEY_API_KEY")
    portkey_config: str = Field(default="", env="PORTKEY_CONFIG")
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://localhost/orchestra", env="DATABASE_URL"
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

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses async driver"""
        if v and "postgresql://" in v and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    @field_validator("portkey_api_key", "openrouter_api_key")
    @classmethod
    def validate_api_keys(cls, v, info):
        """Ensure at least one API key is provided"""
        if not v and info.field_name == "portkey_api_key":
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
            if not openrouter_key:
                raise ValueError(
                    "At least one API key (Portkey or OpenRouter) must be provided"
                )
        return v

    def to_router_config(self) -> RouterConfig:  # type: ignore[name-defined]
        """Convert settings to RouterConfig"""
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "validate_assignment": True,
        "extra": "allow",
    }

@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    """Return RouterConfig built from settings."""