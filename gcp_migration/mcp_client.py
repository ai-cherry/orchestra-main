#!/usr/bin/env python3
"""
Minimal MCP Client - Essential functionality only
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")


class MCPClient:
    """Basic MCP client for interacting with memory system."""

    def __init__(self, base_url=None, api_key=None):
        """Initialize client."""
        # Set up base URL
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "cherry-ai-project")
        self.base_url = base_url or f"https://mcp-api.{project_id}.cloud.goog/api"

        # Set up API key
        self.api_key = api_key or os.environ.get("MCP_API_KEY")

        # Import requests inside method to avoid global dependency
        try:
            import requests

            self.session = requests.Session()
            if self.api_key:
                self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            self.has_requests = True
        except ImportError:
            self.has_requests = False
            logger.warning("Requests library not available")

    def get(self, key: str) -> Optional[Any]:
        """Get a value from memory."""
        if not self.has_requests:
            return None

        try:
            response = self.session.get(
                f"{self.base_url}/memory", params={"key": key}, timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("content")
            return None
        except Exception as e:
            logger.error(f"Error getting key: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """Set a value in memory."""
        if not self.has_requests:
            return False

        try:
            data = {
                "key": key,
                "content": value,
                "memory_type": "shared",
                "scope": "session",
            }

            response = self.session.post(
                f"{self.base_url}/memory", json=data, timeout=10.0
            )

            return response.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Error setting key: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from memory."""
        if not self.has_requests:
            return False

        try:
            response = self.session.delete(
                f"{self.base_url}/memory", params={"key": key}, timeout=10.0
            )

            return response.status_code in (200, 204, 404)
        except Exception as e:
            logger.error(f"Error deleting key: {e}")
            return False

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys in memory."""
        if not self.has_requests:
            return []

        try:
            params = {}
            if prefix:
                params["prefix"] = prefix

            response = self.session.get(
                f"{self.base_url}/memory/keys", params=params, timeout=10.0
            )

            if response.status_code == 200:
                return response.json().get("keys", [])
            return []
        except Exception as e:
            logger.error(f"Error listing keys: {e}")
            return []


# Default client instance
_default_client = None


def get_client(base_url=None, api_key=None, force_new=False):
    """Get default client instance."""
    global _default_client

    if _default_client is None or force_new:
        _default_client = MCPClient(base_url=base_url, api_key=api_key)

    return _default_client


# Convenience functions
def get(key):
    """Get a value."""
    return get_client().get(key)


def set(key, value):
    """Set a value."""
    return get_client().set(key, value)


def delete(key):
    """Delete a value."""
    return get_client().delete(key)


def list_keys(prefix=None):
    """List keys."""
    return get_client().list_keys(prefix)
