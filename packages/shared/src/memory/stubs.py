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


class PatrickMemoryManager(MemoryManager):
    """
    Single-user memory manager specifically designed for Patrick.
    
    This implementation is a simplified version of InMemoryMemoryManager,
    hardcoded for a single user (patrick) to reduce complexity. It's
    suitable for the initial development phase where multi-user
    functionality is not needed.
    """
    
    def __init__(self):
        """Initialize the Patrick-specific memory manager."""
        self._items = []
        self._agent_data = []
        self._is_initialized = False
        self._patrick_user_id = "patrick"  # Hardcoded user ID
    
    def initialize(self) -> None:
        """Initialize the memory manager."""
        self._items = []
        self._agent_data = []
        self._is_initialized = True
    
    def close(self) -> None:
        """Close the memory manager and release resources."""
        self._items = []
        self._agent_data = []
        self._is_initialized = False
    
    def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.
        
        This implementation always sets the user_id to "patrick" regardless
        of what was provided in the item.
        
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
                user_id=self._patrick_user_id,  # Always use patrick's user ID
                session_id=item.session_id,
                timestamp=item.timestamp or datetime.utcnow(),
                item_type=item.item_type,
                persona_active=item.persona_active,
                text_content=item.text_content,
                embedding=item.embedding,
                metadata=item.metadata,
                expiration=item.expiration
            )
        else:
            # If ID is provided, ensure the user_id is patrick's
            item = MemoryItem(
                id=item.id,
                user_id=self._patrick_user_id,  # Override with patrick's user ID
                session_id=item.session_id,
                timestamp=item.timestamp,
                item_type=item.item_type,
                persona_active=item.persona_active,
                text_content=item.text_content,
                embedding=item.embedding,
                metadata=item.metadata,
                expiration=item.expiration
            )
        
        # Store the item
        self._items.append(item)
        
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
        for item in self._items:
            if item.id == item_id:
                return item
        
        return None
    
    def get_conversation_history(
        self,
        user_id: str = None,  # Made optional since we always use patrick's ID
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history for Patrick.
        
        This implementation ignores the user_id parameter and always returns
        items for the hardcoded "patrick" user ID.
        
        Args:
            user_id: Ignored (always uses patrick's ID)
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            filters: Optional filters to apply
            
        Returns:
            List of memory items representing the conversation history
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        # We already know the user is patrick, so no need to filter by user ID
        items = self._items
        
        # Filter by session ID if provided
        if session_id:
            items = [item for item in items if item.session_id == session_id]
        
        # Apply additional filters if provided
        if filters:
            # Filter by persona
            if "persona_active" in filters:
                items = [item for item in items if item.persona_active == filters["persona_active"]]
            
            # Filter by item type
            if "item_type" in filters:
                items = [item for item in items if item.item_type == filters["item_type"]]
        
        # Sort by timestamp (newest first)
        items.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        return items[:limit]
    
    def semantic_search(
        self,
        user_id: str = None,  # Made optional since we always use patrick's ID
        query_embedding: List[float] = None,
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """
        Simplified semantic search implementation.
        
        This stub implementation returns the most recent items that match
        the persona, ignoring the vector embedding search for simplicity.
        
        Args:
            user_id: Ignored (always uses patrick's ID)
            query_embedding: Ignored in this simplified implementation
            persona_context: Optional persona to filter by
            top_k: Maximum number of results to return
            
        Returns:
            List of recent memory items, optionally filtered by persona
        """
        # Ensure the manager is initialized
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        # We already know the user is patrick, so no need to filter by user ID
        items = self._items
        
        # Filter by persona if provided
        if persona_context:
            items = [item for item in items if item.persona_active == persona_context.name]
        
        # Sort by timestamp (newest first)
        items.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Return top-k items
        return items[:top_k]
    
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
                metadata=data.metadata
            )
        
        # Store the data
        self._agent_data.append(data)
        
        return data.id
    
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
        expired_count = sum(1 for item in self._items if item.expiration and item.expiration <= now)
        
        # Remove expired items
        self._items = [item for item in self._items if not item.expiration or item.expiration > now]
        self._agent_data = [data for data in self._agent_data if not data.expiration or data.expiration > now]
        
        return expired_count
