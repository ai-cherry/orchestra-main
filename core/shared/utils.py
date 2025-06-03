"""Shared utility functions to reduce code duplication"""
    """Load configuration from JSON file"""
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}

def get_env_var(var_name: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default"""
        raise ValueError(f"Environment variable {var_name} not set")
    return value

def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """Validate configuration has required keys"""
        logger.error(f"Missing required config keys: {missing_keys}")
        return False
    return True

async def run_with_timeout(coro, timeout: int = 30):
    """Run coroutine with timeout"""
        logger.error(f"Operation timed out after {timeout} seconds")
        raise

def to_dict(obj: Any) -> Dict[str, Any]:
    """Convert object to dictionary representation"""
    """Format error for logging"""
    return f"{error.__class__.__name__}: {str(error)}"
