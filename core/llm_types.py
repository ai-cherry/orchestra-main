"""
Shared types and models for the LLM routing system.

This module contains all shared enums, models, and type definitions
to prevent circular imports and maintain type safety across the system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field

class UseCase(str, Enum):
    """Defined use cases with specific model requirements"""

    CODE_GENERATION = "code_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    CHAT_CONVERSATION = "chat_conversation"
    MEMORY_PROCESSING = "memory_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
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

        validate_assignment = True
        extra = "forbid"

class ModelMapping(BaseModel):
    """Model mapping for each use case and tier"""

    use_case: UseCase
    tier: ModelTier
    primary_model: str
    fallback_models: List[str] = Field(default_factory=list)
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    temperature: float = Field(default=0.5, ge=0, le=2)
    system_prompt: Optional[str] = None

    class Config:
        """Pydantic configuration"""

        validate_assignment = True

class LLMRequest(BaseModel):
    """Standard request format for LLM operations"""

    messages: Union[str, List[Dict[str, str]]]
    use_case: UseCase = UseCase.GENERAL_PURPOSE
    tier: ModelTier = ModelTier.STANDARD
    model_override: Optional[str] = None
    temperature_override: Optional[float] = Field(None, ge=0, le=2)
    max_tokens_override: Optional[int] = Field(None, ge=1, le=32000)
    system_prompt_override: Optional[str] = None
    stream: bool = False
    cache: bool = True
    metadata: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    """Standard response format for LLM operations"""

    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
    created: int
    metadata: Optional[Dict[str, Any]] = None
    cached: bool = False
    latency_ms: Optional[float] = None

class ProviderStatus(BaseModel):
    """Provider health status"""

    name: str
    available: bool
    last_check: Optional[str] = None
    error_rate: float = 0.0
    avg_latency_ms: Optional[float] = None
    models_available: int = 0

class RouterHealth(BaseModel):
    """Overall router health status"""

    status: str  # "healthy", "degraded", "unhealthy"
    providers: List[ProviderStatus]
    cache_hit_rate: float
    total_requests: int
    success_rate: float
    uptime_seconds: float
