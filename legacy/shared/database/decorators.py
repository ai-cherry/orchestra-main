"""
"""
    """
            # agent_create({"name": "Agent", "type": "assistant"})
            # or
            # agent_create(name="Agent", type="assistant")
    """
            kwargs = args[0]
            args = ()
        
        # If called with positional args, convert to kwargs based on signature
        elif args and params:
            for i, (arg, param) in enumerate(zip(args, params)):
                if param not in kwargs:  # Don't override explicit kwargs
                    kwargs[param] = arg
            args = ()
        
        # Call the original function
        return await func(self, **kwargs)
    
    return wrapper

def ensure_dict_param(param_name: str = 'data') -> Callable:
    """
    """
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