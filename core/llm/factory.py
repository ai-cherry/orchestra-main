"""
LLM Router Factory for Orchestra AI
Provides factory functions and context management for LLM routers.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncGenerator

from .unified_router import UnifiedLLMRouter
from core.config.unified_config import get_llm_config, LLMConfig

logger = logging.getLogger(__name__)

# Global router instance
_router_instance: Optional[UnifiedLLMRouter] = None

def create_router(config: Optional[LLMConfig] = None) -> UnifiedLLMRouter:
    """Create a new LLM router instance."""
    if config is None:
        config = get_llm_config()
    
    return UnifiedLLMRouter(config)

def get_router(config: Optional[LLMConfig] = None) -> UnifiedLLMRouter:
    """Get or create the global router instance."""
    global _router_instance
    
    if _router_instance is None:
        _router_instance = create_router(config)
    
    return _router_instance

@asynccontextmanager
async def router_context(config: Optional[LLMConfig] = None) -> AsyncGenerator[UnifiedLLMRouter, None]:
    """Context manager for router lifecycle."""
    router = create_router(config)
    try:
        yield router
    finally:
        await router.close()


async def reset_router():
    """Reset the global router instance."""
    global _router_instance
    if _router_instance:
        await _router_instance.close()
        _router_instance = None 