"""
Memory Manager stubs for AI Orchestration System.

This module provides simplified memory manager implementations for development
and testing purposes. These implementations are designed to be lightweight
and easy to use, with minimal dependencies.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig


class InMemoryMemoryManagerStub(MemoryManager):
    """
    Simple in-memory implementation of the MemoryManager interface for testing.

    This implementation stores memory items and agent data in memory,
    making it suitable for development and testing purposes where
    persistence is not required.
    """

    def __init__(self):
        """Initialize the in-memory memory manager stub."""
        self.memory_items = []
        self.agent_data = []
        self.hashes = set()
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize the memory manager."""
        self._is_initialized = True

    def close(self) -> None:
        """Close the memory manager and release resources."""
        self.memory_items = []
        self.agent_data = []
        self.hashes = set()
        self._is_initialized = False

    def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.

        Args:
            item: The memory item to store

        Returns:
            The ID of the created memory item
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")

        # Create a copy with a generated ID if one isn't provided
        if not item.id:
            item_id = f"memory_{uuid.uuid4().hex}"
            item = MemoryItem(
                id=item_id,
                user_id=item.user_id,
                session_id=item.session_id,
                timestamp=item.timestamp or datetime.utcnow(),
                item_type=item.item_type,
                persona_active=item.persona_active,
                text_content=item.text_content,
                embedding=item.embedding,
                metadata=item.metadata,
                expiration=item.expiration,
            )

        # Store the item
        self.memory_items.append(item)

        # Add content hash to set if it exists
        content_hash = item.metadata.get("content_hash")
        if content_hash:
            self.hashes.add(content_hash)

        return item.id

    def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a specific memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item if found, None otherwise
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")

        # Find the item
        for item in self.memory_items:
            if item.id == item_id:
                return item

        return None

    def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history for a user.

        Args:
            user_id: The user ID to get history for
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            filters: Optional filters to apply

        Returns:
            List of memory items representing the conversation history
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")

        # Filter by user ID
        items = [item for item in self.memory_items if item.user_id == user_id]

        # Filter by session ID if provided
        if session_id:
            items = [item for item in items if item.session_id == session_id]

        # Sort by timestamp (newest first)
        items.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        return items[:limit]

    def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings.

        This stub implementation returns an empty list.

        Args:
            user_id: The user ID to search memories for
            query_embedding: The vector embedding of the query
            persona_context: Optional persona context for personalized results
            top_k: Maximum number of results to return

        Returns:
            Empty list (stub implementation)
        """
        return []

    def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.

        Args:
            data: The agent data to store

        Returns:
            The ID of the stored data
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")

        # Create a copy with a generated ID if one isn't provided
        if not data.id:
            data_id = f"agent_data_{uuid.uuid4().hex}"
            data = AgentData(
                id=data_id,
                agent_id=data.agent_id,
                timestamp=data.timestamp or datetime.utcnow(),
                data_type=data.data_type,
                content=data.content,
                metadata=data.metadata,
                expiration=data.expiration,
            )

        # Store the data
        self.agent_data.append(data)

        return data.id

    def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in storage.

        Args:
            item: The memory item to check for duplicates

        Returns:
            True if a duplicate exists, False otherwise
        """
        # Check if content hash exists in hashes set
        content_hash = item.metadata.get("content_hash")
        if not content_hash:
            return False

        return content_hash in self.hashes

    def cleanup_expired_items(self) -> int:
        """
        Remove expired items from storage.

        Returns:
            Number of items removed
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")

        now = datetime.utcnow()

        # Count expired items
        expired_count = sum(
            1
            for item in self.memory_items
            if item.expiration and item.expiration <= now
        )

        # Remove expired items
        self.memory_items = [
            item
            for item in self.memory_items
            if not item.expiration or item.expiration > now
        ]
        self.agent_data = [
            data
            for data in self.agent_data
            if not data.expiration or data.expiration > now
        ]

        return expired_count
        
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the memory manager.

        Returns:
            Dict with health status information
        """
        return {
            "status": "healthy",
            "provider": "in_memory",
            "items_count": len(self.memory_items),
            "agent_data_count": len(self.agent_data)
        }
