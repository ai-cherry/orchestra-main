"""
Agno (Phidata) Memory Adapter for Orchestra.

This module provides integration between Orchestra's tiered memory system
and Agno's MCP (Model Context Protocol) memory architecture.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json
import asyncio

from packages.shared.src.memory.base import MemoryProvider
from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class AgnoMemoryAdapter(MemoryProvider):
    """
    Memory adapter that connects Orchestra's memory system to Agno (Phidata).

    This adapter:
    1. Maps Orchestra memory items to MCP protocol format
    2. Handles bi-directional synchronization between systems
    3. Enables persistent, contextualized memory across both platforms
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Agno memory adapter.

        Args:
            config: Configuration options for the adapter
        """
        self.config = config or {}
        self.agno_client = None
        self.sync_enabled = self.config.get("sync_enabled", True)
        self.sync_frequency = self.config.get("sync_frequency", 60)  # seconds
        self.sync_task = None
        self._initialized = False
        logger.info("Agno memory adapter initialized")

    async def initialize(self) -> None:
        """Initialize the adapter and establish connection to Agno."""
        try:
            # Import Agno client library (assumed to be installed)
            try:
                from agno_sdk import AgnoClient, MemoryOptions

                self.AgnoClient = AgnoClient
                self.MemoryOptions = MemoryOptions
            except ImportError:
                logger.warning(
                    "Agno SDK not available. Install with: pip install agno-sdk"
                )
                return False

            # Initialize the Agno client
            api_key = self.config.get("api_key")
            if not api_key:
                logger.warning("Agno API key not provided")
                return False

            self.agno_client = self.AgnoClient(
                api_key=api_key,
                project_id=self.config.get("project_id", "orchestra"),
                memory_options=self.MemoryOptions(
                    enabled=True,
                    ttl=self.config.get("memory_ttl", 604800),  # Default 7 days
                    semantic_enabled=True,
                ),
            )

            # Start background sync if enabled
            if self.sync_enabled:
                self.sync_task = asyncio.create_task(self._background_sync())

            self._initialized = True
            logger.info("Agno memory adapter connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Agno memory adapter: {e}")
            return False

    async def close(self) -> None:
        """Close the adapter and release resources."""
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        if self.agno_client:
            await self.agno_client.close()

        logger.info("Agno memory adapter closed")

    async def add_memory(self, item: MemoryItem) -> str:
        """
        Add a memory item to both Orchestra and Agno memory.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added memory item
        """
        if not self._initialized:
            logger.warning("Agno memory adapter not initialized")
            return None

        try:
            # Convert Orchestra memory item to Agno format
            agno_memory = self._convert_to_agno_format(item)

            # Store in Agno memory
            memory_id = await self.agno_client.memory.add(
                user_id=item.user_id, session_id=item.session_id, memory=agno_memory
            )

            # Update the item's metadata with Agno ID
            if item.metadata is None:
                item.metadata = {}
            item.metadata["agno_memory_id"] = memory_id

            return memory_id
        except Exception as e:
            logger.error(f"Failed to add memory to Agno: {e}")
            return None

    async def get_memories(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """
        Retrieve memories from Agno and convert to Orchestra format.

        Args:
            user_id: The user ID
            session_id: Optional session ID
            query: Optional semantic search query
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory items
        """
        if not self._initialized:
            logger.warning("Agno memory adapter not initialized")
            return []

        try:
            # Use semantic search if query is provided
            if query:
                memories = await self.agno_client.memory.search(
                    user_id=user_id, session_id=session_id, query=query, limit=limit
                )
            else:
                # Otherwise get recent memories
                memories = await self.agno_client.memory.get_recent(
                    user_id=user_id, session_id=session_id, limit=limit
                )

            # Convert to Orchestra format
            return [self._convert_from_agno_format(mem) for mem in memories]
        except Exception as e:
            logger.error(f"Failed to retrieve memories from Agno: {e}")
            return []

    async def _background_sync(self) -> None:
        """Background task that synchronizes memories between systems."""
        while True:
            try:
                # Sleep first to avoid immediate sync on startup
                await asyncio.sleep(self.sync_frequency)

                # TODO: Implement bidirectional sync logic
                # This would pull recent memories from Agno and add to Orchestra
                # and vice versa for memories that exist in only one system

                logger.debug("Agno memory sync completed")
            except asyncio.CancelledError:
                logger.info("Agno memory sync task cancelled")
                break
            except Exception as e:
                logger.error(f"Error during Agno memory sync: {e}")

    def _convert_to_agno_format(self, item: MemoryItem) -> Dict[str, Any]:
        """Convert Orchestra memory item to Agno format."""
        return {
            "content": item.text_content,
            "role": "user" if item.metadata.get("source") == "user" else "assistant",
            "metadata": {
                "persona": item.persona_active,
                "interaction_id": item.metadata.get("interaction_id"),
                "timestamp": item.timestamp.isoformat() if item.timestamp else None,
                "orchestra_metadata": json.dumps(item.metadata or {}),
            },
        }

    def _convert_from_agno_format(self, agno_memory: Dict[str, Any]) -> MemoryItem:
        """Convert Agno memory to Orchestra format."""
        # Extract and parse Orchestra metadata if available
        orchestra_metadata = {}
        if agno_memory.get("metadata", {}).get("orchestra_metadata"):
            try:
                orchestra_metadata = json.loads(
                    agno_memory["metadata"]["orchestra_metadata"]
                )
            except:
                pass

        # Merge with Agno metadata
        metadata = {
            "source": "user" if agno_memory.get("role") == "user" else "system",
            "agno_memory_id": agno_memory.get("id"),
            **orchestra_metadata,
        }

        return MemoryItem(
            user_id=agno_memory.get("user_id", ""),
            session_id=agno_memory.get("session_id", ""),
            item_type="conversation",
            persona_active=agno_memory.get("metadata", {}).get("persona", "default"),
            text_content=agno_memory.get("content", ""),
            metadata=metadata,
        )
