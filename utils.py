"""
Utility classes and functions for the Orchestra system.
"""

import functools
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, delay: float = 1.0, exponential_backoff: float = 2.0):
    """Retry decorator with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = delay * (exponential_backoff**attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. " f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
            return None

        return wrapper

    return decorator

class APIKeyManager:
    """Manages API keys for various services."""

    def __init__(self):
        self.keys: Dict[str, Optional[str]] = {}
        self._load_keys()

    def _load_keys(self):
        """Load API keys from environment variables."""
        services = ["OPENAI", "ANTHROPIC", "GOOGLE", "GEMINI"]
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
        return service.lower() in self.keys and self.keys[service.lower()] is not None

    def set_key(self, service: str, key: str):
        """Set API key for a service (runtime only)."""
        self.keys[service.lower()] = key
        logger.info(f"Updated API key for {service}")

def get_project_id() -> str:
    """Get the GCP project ID from environment or default."""
    return os.getenv("VULTR_PROJECT_ID", "cherry-ai-project")

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
            with open(env_file) as f:
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
