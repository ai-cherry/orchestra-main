"""Makes core.llm a package"""

from .unified_router import (
    UnifiedLLMRouter,
    LLMRequest,
    LLMResponse, 
    UseCase,
    ModelTier,
    Provider,
    LLMError,
    RateLimitError,
    ModelUnavailableError,
    ConfigurationError,
    get_llm_router,
    reset_router,
    complete,
    chat,
    stream_chat
)

from .factory import (
    create_router,
    get_router,
    router_context,
)

__all__ = [
    "UnifiedLLMRouter",
    "LLMRequest",
    "LLMResponse", 
    "UseCase",
    "ModelTier",
    "Provider",
    "LLMError",
    "RateLimitError",
    "ModelUnavailableError",
    "ConfigurationError",
    "get_llm_router",
    "reset_router",
    "complete",
    "chat",
    "stream_chat",
    "create_router",
    "get_router",
    "router_context",
] 