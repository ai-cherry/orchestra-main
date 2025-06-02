#!/usr/bin/env python3
"""
memory_store.py - Persistent Memory Store for MCP Server

This module provides a persistent memory store implementation for the MCP server,
handling storage, retrieval, and management of memory items with TTL support.
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logger = logging.getLogger("mcp-memory-store")

class MemoryStore:
    """Persistent memory store for MCP server."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the memory store with configuration.

        Args:
            config: Dictionary containing configuration parameters:
                - storage_path: Path to store memory files
                - ttl_seconds: Default time-to-live for memory items
                - max_items_per_key: Maximum items to store per key
                - enable_compression: Whether to compress stored data
        """
        self.config = config
        self.storage_path = Path(config["storage_path"])
        self.ttl_seconds = config["ttl_seconds"]
        self.max_items = config["max_items_per_key"]
        self.enable_compression = config["enable_compression"]

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(exist_ok=True, parents=True)

        # Initialize memory cache
        self.memory_cache = {}

        # Load existing memory items
        self._load_memory()

        # Start background cleanup thread
        self._start_cleanup_thread()

    def _load_memory(self):
        """Load existing memory items from storage."""
        try:
            memory_files = list(self.storage_path.glob("*.json"))
            logger.info(f"Loading {len(memory_files)} memory files from storage")

            for memory_file in memory_files:
                try:
                    with open(memory_file, "r") as f:
                        memory_data = json.load(f)

                        # Check if the memory item has expired
                        if "expiry" in memory_data:
                            expiry_time = datetime.fromisoformat(memory_data["expiry"])
                            if expiry_time < datetime.now():
                                # Memory item has expired, delete it
                                memory_file.unlink()
                                continue

                        # Add memory item to cache
                        key = memory_file.stem
                        self.memory_cache[key] = memory_data["content"]
                except Exception as e:
                    logger.error(f"Error loading memory file {memory_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")

    def _start_cleanup_thread(self):
        """Start a background thread to clean up expired memory items."""

        def cleanup_task():
            while True:
                try:
                    # Sleep for a while before cleaning up
                    time.sleep(3600)  # Run every hour

                    # Find and delete expired memory files
                    memory_files = list(self.storage_path.glob("*.json"))
                    for memory_file in memory_files:
                        try:
                            with open(memory_file, "r") as f:
                                memory_data = json.load(f)

                                # Check if the memory item has expired
                                if "expiry" in memory_data:
                                    expiry_time = datetime.fromisoformat(memory_data["expiry"])
                                    if expiry_time < datetime.now():
                                        # Memory item has expired, delete it
                                        memory_file.unlink()

                                        # Remove from cache if present
                                        key = memory_file.stem
                                        if key in self.memory_cache:
                                            del self.memory_cache[key]
                        except Exception as e:
                            logger.error(f"Error checking memory file {memory_file}: {e}")
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        # Start the cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    def get(self, key: str, scope: str = "session", tool: Optional[str] = None) -> Optional[Any]:
        """Get a memory item.

        Args:
            key: The key to retrieve
            scope: The scope of the memory item (default: "session")
            tool: Optional tool identifier

        Returns:
            The memory item content if found, None otherwise
        """
        # Construct the full key based on scope and tool
        full_key = self._get_full_key(key, scope, tool)

        # Check if the memory item is in the cache
        if full_key in self.memory_cache:
            return self.memory_cache[full_key]

        # Check if the memory item is in storage
        memory_file = self.storage_path / f"{full_key}.json"
        if memory_file.exists():
            try:
                with open(memory_file, "r") as f:
                    memory_data = json.load(f)

                    # Check if the memory item has expired
                    if "expiry" in memory_data:
                        expiry_time = datetime.fromisoformat(memory_data["expiry"])
                        if expiry_time < datetime.now():
                            # Memory item has expired, delete it
                            memory_file.unlink()
                            return None

                    # Add to cache and return
                    self.memory_cache[full_key] = memory_data["content"]
                    return memory_data["content"]
            except Exception as e:
                logger.error(f"Error reading memory file {memory_file}: {e}")

        return None

    def set(
        self,
        key: str,
        content: Any,
        scope: str = "session",
        tool: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a memory item.

        Args:
            key: The key to store the item under
            content: The content to store
            scope: The scope of the memory item (default: "session")
            tool: Optional tool identifier
            ttl: Optional time-to-live in seconds (overrides default)

        Returns:
            True if successful, False otherwise
        """
        # Construct the full key based on scope and tool
        full_key = self._get_full_key(key, scope, tool)

        # Add to cache
        self.memory_cache[full_key] = content

        # Calculate expiry time
        ttl = ttl or self.ttl_seconds
        expiry_time = datetime.now() + timedelta(seconds=ttl)

        # Prepare memory data
        memory_data = {
            "content": content,
            "scope": scope,
            "tool": tool,
            "created": datetime.now().isoformat(),
            "expiry": expiry_time.isoformat(),
        }

        # Write to storage
        memory_file = self.storage_path / f"{full_key}.json"
        try:
            with open(memory_file, "w") as f:
                json.dump(memory_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing memory file {memory_file}: {e}")
            return False

    def delete(self, key: str, scope: str = "session", tool: Optional[str] = None) -> bool:
        """Delete a memory item.

        Args:
            key: The key to delete
            scope: The scope of the memory item (default: "session")
            tool: Optional tool identifier

        Returns:
            True if successful, False otherwise
        """
        # Construct the full key based on scope and tool
        full_key = self._get_full_key(key, scope, tool)

        # Remove from cache
        if full_key in self.memory_cache:
            del self.memory_cache[full_key]

        # Remove from storage
        memory_file = self.storage_path / f"{full_key}.json"
        if memory_file.exists():
            try:
                memory_file.unlink()
                return True
            except Exception as e:
                logger.error(f"Error deleting memory file {memory_file}: {e}")
                return False

        return True

    def sync(self, key: str, source_tool: str, target_tool: str, scope: str = "session") -> bool:
        """Sync a memory item between tools.

        Args:
            key: The key to sync
            source_tool: Source tool identifier
            target_tool: Target tool identifier
            scope: The scope of the memory item (default: "session")

        Returns:
            True if successful, False otherwise
        """
        # Get the memory item from the source tool
        source_content = self.get(key, scope, source_tool)
        if source_content is None:
            return False

        # Set the memory item for the target tool
        return self.set(key, source_content, scope, target_tool)

    def _get_full_key(self, key: str, scope: str, tool: Optional[str] = None) -> str:
        """Construct the full key based on scope and tool.

        Args:
            key: The base key
            scope: The scope of the memory item
            tool: Optional tool identifier

        Returns:
            The full key
        """
        if tool:
            return f"{scope}:{tool}:{key}"
        return f"{scope}:{key}"
