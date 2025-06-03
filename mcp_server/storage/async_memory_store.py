#!/usr/bin/env python3
"""Asynchronous memory store for MCP server."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("mcp-async-memory-store")


class AsyncMemoryStore:
    """Asynchronous memory store for MCP server."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the async memory store.
        
        Args:
            config: Configuration dictionary with storage settings
        """
        self.storage_path = Path(config.get("storage_path", "./memory_store"))
        self.ttl_seconds = config.get("ttl_seconds", 3600)
        self.max_items = config.get("max_items_per_key", 100)
        self.enable_compression = config.get("enable_compression", False)

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(exist_ok=True, parents=True)

        # Initialize memory cache
        self.memory_cache = {}

        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        # Flag to track initialization
        self._initialized = False

    async def _load_memory(self):
        """Load existing memory items from storage."""
        try:
            memory_files = list(self.storage_path.glob("*.json"))
            logger.info(f"Loading {len(memory_files)} memory files from storage")

            for memory_file in memory_files:
                try:
                    # Use asyncio.to_thread for file I/O to avoid blocking
                    content = await asyncio.to_thread(self._read_file, memory_file)
                    if content:
                        memory_data = json.loads(content)

                        # Check if the memory item has expired
                        if "expiry" in memory_data:
                            expiry_time = datetime.fromisoformat(memory_data["expiry"])
                            if expiry_time < datetime.now():
                                # Memory item has expired, delete it
                                await asyncio.to_thread(memory_file.unlink)
                                continue

                        # Add memory item to cache
                        async with self.lock:
                            key = memory_file.stem
                            self.memory_cache[key] = memory_data["content"]
                except Exception as e:
                    logger.error(f"Error loading memory file {memory_file}: {e}")
        except Exception as e:
            logger.error(f"Error loading memory: {e}")

    def _read_file(self, path: Path) -> str:
        """Read file content synchronously.
        
        Args:
            path: Path to the file
            
        Returns:
            File content as string
        """
        with open(path, "r") as f:
            return f.read()

    def _write_file(self, path: Path, content: str) -> bool:
        """Write content to file synchronously.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing to file {path}: {e}")
            return False

    async def _cleanup_task(self):
        """Background task to clean up expired memory items."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                memory_files = list(self.storage_path.glob("*.json"))
                for memory_file in memory_files:
                    try:
                        content = await asyncio.to_thread(self._read_file, memory_file)
                        if content:
                            memory_data = json.loads(content)

                            # Check if the memory item has expired
                            if "expiry" in memory_data:
                                expiry_time = datetime.fromisoformat(memory_data["expiry"])
                                if expiry_time < datetime.now():
                                    # Memory item has expired, delete it
                                    await asyncio.to_thread(memory_file.unlink)

                                    # Remove from cache if present
                                    async with self.lock:
                                        key = memory_file.stem
                                        if key in self.memory_cache:
                                            del self.memory_cache[key]
                    except Exception as e:
                        logger.error(f"Error checking memory file {memory_file}: {e}")
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def get(self, key: str, scope: str = "session", tool: Optional[str] = None) -> Optional[Any]:
        """Get a memory item.
        
        Args:
            key: The memory key
            scope: The scope of the memory item (default: "session")
            tool: Optional tool identifier

        Returns:
            The memory item content if found, None otherwise
        """
        full_key = self._get_full_key(key, scope, tool)
        
        # Check cache first
        async with self.lock:
            if full_key in self.memory_cache:
                return self.memory_cache[full_key]
        
        # Check storage
        memory_file = self.storage_path / f"{full_key}.json"
        if memory_file.exists():
            try:
                content = await asyncio.to_thread(self._read_file, memory_file)
                if content:
                    memory_data = json.loads(content)

                    # Check if the memory item has expired
                    if "expiry" in memory_data:
                        expiry_time = datetime.fromisoformat(memory_data["expiry"])
                        if expiry_time < datetime.now():
                            # Memory item has expired, delete it
                            await asyncio.to_thread(memory_file.unlink)
                            return None

                    # Add to cache and return
                    async with self.lock:
                        self.memory_cache[full_key] = memory_data["content"]
                    return memory_data["content"]
            except Exception as e:
                logger.error(f"Error reading memory file {memory_file}: {e}")

        return None

    async def set(
        self,
        key: str,
        content: Any,
        scope: str = "session",
        tool: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set a memory item.
        
        Args:
            key: The memory key
            content: The content to store
            scope: The scope of the memory item (default: "session")
            tool: Optional tool identifier
            ttl: Optional time-to-live in seconds (overrides default)

        Returns:
            True if successful, False otherwise
        """
        full_key = self._get_full_key(key, scope, tool)
        
        # Calculate expiry time
        ttl_seconds = ttl if ttl is not None else self.ttl_seconds
        expiry_time = datetime.now() + timedelta(seconds=ttl_seconds)
        
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
        json_content = json.dumps(memory_data, indent=2)
        success = await asyncio.to_thread(self._write_file, memory_file, json_content)
        
        if success:
            # Update cache
            async with self.lock:
                self.memory_cache[full_key] = content

        return success

    async def delete(self, key: str, scope: str = "session", tool: Optional[str] = None) -> bool:
        """Delete a memory item.
        
        Args:
            key: The memory key
            scope: The scope of the memory item (default: "session")
            tool: Optional tool identifier

        Returns:
            True if successful, False otherwise
        """
        full_key = self._get_full_key(key, scope, tool)
        
        # Remove from cache
        async with self.lock:
            if full_key in self.memory_cache:
                del self.memory_cache[full_key]
        
        # Remove from storage
        memory_file = self.storage_path / f"{full_key}.json"
        if memory_file.exists():
            try:
                await asyncio.to_thread(memory_file.unlink)
                return True
            except Exception as e:
                logger.error(f"Error deleting memory file {memory_file}: {e}")
                return False

        return True

    async def sync(self, key: str, source_tool: str, target_tool: str, scope: str = "session") -> bool:
        """Sync memory between tools.
        
        Args:
            key: The memory key
            source_tool: Source tool identifier
            target_tool: Target tool identifier
            scope: The scope of the memory item (default: "session")

        Returns:
            True if successful, False otherwise
        """
        # Get content from source
        content = await self.get(key, scope, source_tool)
        if content is not None:
            # Set content to target
            return await self.set(key, content, scope, target_tool)
        return False

    def _get_full_key(self, key: str, scope: str, tool: Optional[str]) -> str:
        """Generate full key for storage.
        
        Args:
            key: The memory key
            scope: The scope
            tool: Optional tool identifier
            
        Returns:
            Full key string
        """
        if tool:
            return f"{scope}:{tool}:{key}"
        return f"{scope}:{key}"
    
    async def initialize(self):
        """Initialize async components."""
        if self._initialized:
            return
            
        # Load existing memory items
        asyncio.create_task(self._load_memory())

        # Start background cleanup task
        asyncio.create_task(self._cleanup_task())
        
        self._initialized = True
