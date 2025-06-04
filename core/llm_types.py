"""
"""
    """Defined use cases with specific model requirements"""
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    CHAT_CONVERSATION = "chat_conversation"
    MEMORY_PROCESSING = "memory_processing"
    WORKFLOW_COORDINATION = "workflow_coordination"
    GENERAL_PURPOSE = "general_purpose"

class ModelTier(str, Enum):
    """Model tiers for cost optimization"""
    PREMIUM = "premium"  # Most capable, highest cost
    STANDARD = "standard"  # Balanced performance/cost
    ECONOMY = "economy"  # Fast, low cost

class RouterConfig(BaseModel):
    """Configuration for the unified LLM router"""
    portkey_api_key: str = Field(default="", description="Portkey API key")
    portkey_config: str = Field(default="", description="Portkey configuration")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    enable_fallback: bool = Field(default=True, description="Enable fallback routing")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    enable_monitoring: bool = Field(default=True, description="Enable metrics monitoring")

    # Performance optimizations
    connection_pool_size: int = Field(default=2, description="HTTP connection pool size")
    connection_pool_overflow: int = Field(default=3, description="Maximum overflow connections")
    cache_max_size: int = Field(default=1000, description="Maximum cache entries")
    cache_memory_limit_mb: int = Field(default=100, description="Cache memory limit in MB")

    # Database configuration
    database_url: Optional[str] = Field(default=None, description="PostgreSQL connection URL")
    db_pool_size: int = Field(default=2, description="Database connection pool size")
    db_pool_overflow: int = Field(default=3, description="Database pool overflow")

    class Config:
        """Pydantic configuration"""
        extra = "forbid"

class ModelMapping(BaseModel):
    """Model mapping for each use case and tier"""
        """Pydantic configuration"""
    """Standard request format for LLM operations"""
    """Standard response format for LLM operations"""
    """Provider health status"""
    """Overall router health status"""
    status: str  # "healthy", "degraded", "unhealthy"
    providers: List[ProviderStatus]
    cache_hit_rate: float
    total_requests: int
    success_rate: float
    uptime_seconds: float
