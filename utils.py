"""
Utility functions for Orchestra AI
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

class APIKeyManager:
    """Manages API keys for various services."""
    
    def __init__(self):
        self.keys: Dict[str, Optional[str]] = {}
        self.load_keys()
    
    def load_keys(self):
        """Load API keys from environment variables."""
        services = ["OPENAI", "ANTHROPIC", "GOOGLE", "GEMINI", "OPENROUTER", "GROK", "PERPLEXITY"]
        for service in services:
            key_name = f"{service}_API_KEY"
            self.keys[service.lower()] = os.getenv(key_name)
            if self.keys[service.lower()]:
                logger.info(f"Loaded API key for {service}")
            else:
                logger.warning(f"No API key found for {service} (looking for {key_name})")

    def get_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        return self.keys.get(service.lower())
    
    def has_key(self, service: str) -> bool:
        """Check if API key exists for a service."""
        return bool(self.get_key(service))
    
    def set_key(self, service: str, key: str):
        """Set API key for a service (runtime only)."""
        self.keys[service.lower()] = key
        logger.info(f"Updated API key for {service}")

def get_LAMBDA_PROJECT_ID() -> str:
    """Get the Lambda project ID from environment or default."""
    project_id = os.getenv("LAMBDA_PROJECT_ID")
    if not project_id:
        logger.warning("LAMBDA_PROJECT_ID not set, using default 'cherry-ai-project'")
        return "cherry-ai-project"
    return project_id

def setup_logging(level: str = "INFO"):
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def load_env_file(env_file: str = ".env"):
    """Load environment variables from a .env file if it exists."""
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
            logger.info(f"Loaded environment from {env_file}")
        except Exception as e:
            logger.error(f"Failed to load {env_file}: {e}")
    else:
        logger.warning(f"No {env_file} file found") 