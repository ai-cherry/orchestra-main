"""
Utility classes and functions for the Orchestra system.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


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
    return os.getenv("GOOGLE_CLOUD_PROJECT", "cherry-ai-project")


def setup_logging(level: str = "INFO"):
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
