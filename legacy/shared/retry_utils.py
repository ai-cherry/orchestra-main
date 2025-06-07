
import time
from functools import wraps
from typing import Callable, Any

def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:

                    pass
                    return func(*args, **kwargs)
                except Exception:

                    pass
                    attempts += 1
                    if attempts >= max_attempts:
                        raise e
                    
                    print(f"Attempt {attempts} failed, retrying in {current_delay}s...")
                    # TODO: Replace with asyncio.sleep() for async code
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator
