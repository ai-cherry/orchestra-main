"""
Factory module for creating LLM router instances.

This module provides factory functions that ensure proper async
initialization of router instances.
"""

import asyncio
from typing import Optional, TypeVar, Type, Dict
from contextlib import asynccontextmanager

from core.llm_types import RouterConfig
from core.llm_router_base import BaseLLMRouter
from core.config import get_settings

# Type variable for router types
T = TypeVar('T', bound=BaseLLMRouter)

# Global router instances
_router_instances: Dict[Type[BaseLLMRouter], BaseLLMRouter] = {}
_lock = asyncio.Lock()


async def create_router(
    router_class: Type[T],
    config: Optional[RouterConfig] = None,
    **kwargs
) -> T:
    """
    Create and initialize a router instance.
    
    Args:
        router_class: The router class to instantiate
        config: Optional router configuration
        **kwargs: Additional arguments for the router
    
    Returns:
        Initialized router instance
    """
    # Create router instance
    router = router_class(config=config, **kwargs)
    
    # Initialize async components
    await router.initialize()
    
    return router


async def get_router(
    router_class: Type[T],
    config: Optional[RouterConfig] = None,
    **kwargs
) -> T:
    """
    Get or create a singleton router instance.
    
    Args:
        router_class: The router class to get/create
        config: Optional router configuration (only used on first call)
        **kwargs: Additional arguments (only used on first call)
    
    Returns:
        Singleton router instance
    """
    async with _lock:
        if router_class not in _router_instances:
            # Create new instance
            router = await create_router(router_class, config, **kwargs)
            _router_instances[router_class] = router
        
        return _router_instances[router_class]


@asynccontextmanager
async def router_context(
    router_class: Type[T],
    config: Optional[RouterConfig] = None,
    **kwargs
):
    """
    Context manager for router lifecycle management.
    
    Usage:
        async with router_context(MyRouter) as router:
            response = await router.complete("Hello")
    
    Args:
        router_class: The router class to use
        config: Optional router configuration
        **kwargs: Additional arguments for the router
    
    Yields:
        Initialized router instance
    """
    router = await create_router(router_class, config, **kwargs)
    
    try:
        yield router
    finally:
        await router.close()


async def close_all_routers():
    """Close all singleton router instances"""
    async with _lock:
        for router in _router_instances.values():
            await router.close()
        
        _router_instances.clear()


# Forward declarations for concrete implementations
async def get_unified_router(config: Optional[RouterConfig] = None):
    """Get or create the unified LLM router"""
    from core.llm_router import UnifiedLLMRouter
    return await get_router(UnifiedLLMRouter, config)


async def get_dynamic_router(
    config: Optional[RouterConfig] = None,
    db_url: Optional[str] = None
):
    """Get or create the dynamic LLM router"""
    from core.llm_router_dynamic import DynamicLLMRouter
    return await get_router(DynamicLLMRouter, config, db_url=db_url)


# Convenience function for backward compatibility
async def get_llm_router(
    dynamic: bool = True,
    config: Optional[RouterConfig] = None
) -> BaseLLMRouter:
    """
    Get the appropriate LLM router.
    
    Args:
        dynamic: Whether to use dynamic (database-driven) router
        config: Optional router configuration
    
    Returns:
        Router instance
    """
    if dynamic:
        return await get_dynamic_router(config)
    else:
        return await get_unified_router(config)