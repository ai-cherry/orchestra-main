"""
Decorators for the unified PostgreSQL architecture.

Provides parameter transformation and other utility decorators to ensure
compatibility between different calling conventions.
"""

import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def param_transformer(func: Callable) -> Callable:
    """
    Decorator that transforms parameters between dict and keyword arguments.
    
    This decorator allows methods to accept both dictionary arguments and
    keyword arguments, automatically converting between them as needed.
    
    Example:
        @param_transformer
        async def agent_create(self, **kwargs):
            # Can be called as:
            # agent_create({"name": "Agent", "type": "assistant"})
            # or
            # agent_create(name="Agent", type="assistant")
    """
    
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())[1:]  # Skip 'self'
        
        # If called with a single dict argument, convert to kwargs
        if len(args) == 1 and isinstance(args[0], dict) and not kwargs:
            logger.debug(f"Converting dict argument to kwargs for {func.__name__}")
            kwargs = args[0]
            args = ()
        
        # If called with positional args, convert to kwargs based on signature
        elif args and params:
            logger.debug(f"Converting positional args to kwargs for {func.__name__}")
            for i, (arg, param) in enumerate(zip(args, params)):
                if param not in kwargs:  # Don't override explicit kwargs
                    kwargs[param] = arg
            args = ()
        
        # Call the original function
        return await func(self, **kwargs)
    
    return wrapper


def ensure_dict_param(param_name: str = 'data') -> Callable:
    """
    Decorator that ensures a specific parameter is always a dictionary.
    
    Args:
        param_name: Name of the parameter to ensure is a dict
        
    Example:
        @ensure_dict_param('agent_data')
        async def agent_create(self, agent_data: Dict[str, Any]):
            # agent_data is guaranteed to be a dict
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Check if param is in kwargs
            if param_name in kwargs:
                value = kwargs[param_name]
                if not isinstance(value, dict):
                    logger.warning(f"Converting {param_name} to dict in {func.__name__}")
                    # Try to convert to dict if possible
                    if hasattr(value, '__dict__'):
                        kwargs[param_name] = vars(value)
                    else:
                        kwargs[param_name] = {param_name: value}
            
            # Check positional args
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())[1:]  # Skip 'self'
            
            if param_name in params:
                param_index = params.index(param_name)
                if len(args) > param_index:
                    args_list = list(args)
                    value = args_list[param_index]
                    if not isinstance(value, dict):
                        logger.warning(f"Converting positional {param_name} to dict in {func.__name__}")
                        if hasattr(value, '__dict__'):
                            args_list[param_index] = vars(value)
                        else:
                            args_list[param_index] = {param_name: value}
                    args = tuple(args_list)
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def retry_on_connection_error(max_attempts: int = 3, backoff_factor: float = 1.0):
    """
    Decorator that retries database operations on connection errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor
        
    Example:
