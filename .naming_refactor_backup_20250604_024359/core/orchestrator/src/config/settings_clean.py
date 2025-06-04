# TODO: Consider adding connection pooling configuration
"""
"""
    """Application settings loaded from environment variables."""
    ENVIRONMENT: str = "development"
    DEFAULT_LLM_MODEL: str = "gpt-4"
    DEFAULT_LLM_MODEL_PRIMARY: str = "openai/gpt-4o"
    DEFAULT_LLM_MODEL_FALLBACK_OPENAI: Optional[str] = "gpt-4o"
    DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC: Optional[str] = "claude-3-5-sonnet-20240620"

    # API keys
    OPENROUTER_API_KEY: Optional[str] = None
    PORTKEY_API_KEY: Optional[str] = None

    # External Services (Non-GCP)
    DRAGONFLY_URI: Optional[str] = None  # Aiven DragonflyDB
    MONGODB_URI: Optional[str] = None  # MongoDB Atlas
    WEAVIATE_URL: Optional[str] = None  # Weaviate Cloud
    WEAVIATE_API_KEY: Optional[str] = None

    # Redis Cache Settings (Local or External)
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_AUTH_SECRET: Optional[str] = None
    REDIS_CACHE_TTL: int = 3600
    REDIS_CACHE_ENABLED: bool = False

    # Vector Search Settings
    VECTOR_DIMENSION: int = 1536
    VECTOR_DISTANCE_TYPE: str = "COSINE"

    # OpenRouter Configuration
    OPENROUTER_HEADERS: Optional[str] = None
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-3.5-turbo"
    OPENROUTER_FREE_FALLBACKS: Optional[str] = None
    PREFERRED_LLM_PROVIDER: str = "openrouter"

    # Mode and Agent model mappings
    MODE_MODEL_MAP: Optional[str] = None
    AGENT_MODEL_MAP: Optional[str] = None

    # LLM request parameters
    LLM_REQUEST_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0
    LLM_RETRY_MAX_DELAY: float = 60.0
    LLM_RETRYABLE_ERRORS: str = "connection_error,timeout_error,rate_limit_error,service_error"

    # Semantic caching
    LLM_SEMANTIC_CACHE_ENABLED: bool = False
    LLM_SEMANTIC_CACHE_THRESHOLD: float = 0.85
    LLM_SEMANTIC_CACHE_TTL: int = 3600

    # Portkey configuration
    TRACE_ID: Optional[str] = None
    MASTER_PORTKEY_ADMIN_KEY: Optional[str] = None
    PORTKEY_CONFIG_ID: Optional[str] = None
    PORTKEY_STRATEGY: str = "fallback"
    PORTKEY_CACHE_ENABLED: bool = False

    # Portkey Virtual Keys
    PORTKEY_VIRTUAL_KEY_OPENAI: Optional[str] = None
    PORTKEY_VIRTUAL_KEY_ANTHROPIC: Optional[str] = None
    PORTKEY_VIRTUAL_KEY_MISTRAL: Optional[str] = None
    PORTKEY_VIRTUAL_KEY_OPENROUTER: Optional[str] = None

    # Site information
    SITE_URL: str = "http://localhost"
    SITE_TITLE: str = "cherry_ai-Main Development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    def get_openrouter_headers(self) -> Dict[str, str]:
        """Get OpenRouter custom headers."""
            "HTTP-Referer": self.SITE_URL,
            "X-Title": self.SITE_TITLE,
        }
        if self.OPENROUTER_FREE_FALLBACKS:
            free_models = self.OPENROUTER_FREE_FALLBACKS.replace(" ", "").split(",")
            if free_models:
                headers["fallback_providers"] = ":".join(free_models)
        if self.OPENROUTER_HEADERS:
            try:

                pass
                custom_headers = json.loads(self.OPENROUTER_HEADERS)
                headers.update(custom_headers)
            except Exception:

                pass
                logging.error(f"Failed to parse OPENROUTER_HEADERS: {e}")
        return headers

def get_settings() -> Settings:
    """Get application settings."""