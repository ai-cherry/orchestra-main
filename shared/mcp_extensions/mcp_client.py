#!/usr/bin/env python3
"""
mcp_client.py - Simple MCP Client for Tool Registry

This module provides a simplified client for interacting with the MCP server,
focusing on the basic operations needed by the Tool Registry.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-client")


class MCPClient:
    """Simple client for interacting with MCP server."""

    def __init__(self, base_url: str = "http://localhost:8080/api", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key or os.environ.get("MCP_API_KEY")
        self.session = requests.Session()

        # Add API key to all requests if available
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def get(self, key: str) -> Optional[Any]:
        """Get a value from MCP memory.

        Args:
            key: The key to retrieve

        Returns:
            The value or None if not found
        """
        try:
            response = self.session.get(f"{self.base_url}/memory", params={"key": key})

            if response.status_code == 200:
                data = response.json()
                if "content" in data:
                    return data["content"]

            return None
        except Exception as e:
            logger.error(f"Error getting key {key}: {str(e)}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """Set a value in MCP memory.

        Args:
            key: The key to set
            value: The value to store

        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "key": key,
                "content": value,
                "memory_type": "shared",
                "scope": "session",
            }

            response = self.session.post(f"{self.base_url}/memory", json=data)

            if response.status_code in (200, 201):
                return True

            logger.error(f"Error setting key {key}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error setting key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from MCP memory.

        Args:
            key: The key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(f"{self.base_url}/memory", params={"key": key})

            if response.status_code == 200:
                return True

            logger.error(f"Error deleting key {key}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List keys in MCP memory.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of matching keys
        """
        try:
            params = {}
            if prefix:
                params["prefix"] = prefix

            response = self.session.get(f"{self.base_url}/memory/keys", params=params)

            if response.status_code == 200:
                return response.json().get("keys", [])

            logger.error(f"Error listing keys: {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error listing keys: {str(e)}")
            return []

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search MCP memory.

        Args:
            query: Search query

        Returns:
            List of matching memory items
        """
        try:
            response = self.session.get(f"{self.base_url}/memory/search", params={"query": query})

            if response.status_code == 200:
                return response.json().get("results", [])

            logger.error(f"Error searching memory: {response.text}")
            return []
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}")
            return []
