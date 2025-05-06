"""
Tiered Memory Manager for Orchestra.

This module provides a tiered memory management system that combines multiple 
memory storage backends with different performance and retention characteristics.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Set
import time
from datetime import datetime, timedelta

from packages.shared.src.memory.base import MemoryProvider, MemoryManager
from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.memory.integrations.agno_memory_adapter import AgnoMemoryAdapter

# Configure logging
logger = logging.getLogger(__name__)

class TieredMemoryManager(MemoryManager):
    """
    Tiered memory manager that combines multiple memory systems.
    
    This class implements a tiered memory architecture with:
    1. Short-term memory (fast, limited retention)
    2. Medium-term memory (balanced)
    3. Long-term memory (persistent, with semantic retrieval)
    
    It coordinates between Orchestra's native memory system and external 
    systems like Agno (Phidata) with MCP support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tiered memory manager.
        
        Args:
            config: Configuration for the memory manager
        """
        self.config = config or {}
        self.short_term_provider = None   # Fast, in-memory storage
        self.medium_term_provider = None  # Database storage
        self.long_term_provider = None    # Persistent storage with semantic search
        self._initialized = False
        logger.info("TieredMemoryManager initialized with config")
        
    async def initialize(self) -> None:
        """Initialize all memory tiers."""
        try:
            # Initialize short-term memory (typically in-memory)
            from packages.shared.src.memory.providers import InMemoryProvider
            self.short_term_provider = InMemoryProvider(
                config={"max_items": self.config.get("short_term_max_items", 1000)}
            )
            await self.short_term_provider.initialize()
            
            # Initialize medium-term memory (typically database)
            if self.config.get("medium_term_enabled", True):
                from packages.shared.src.memory.providers import DatabaseProvider
                self.medium_term_provider = DatabaseProvider(
                    config=self.config.get("medium_term_config", {})
                )
                await self.medium_term_provider.initialize()
            
            # Initialize long-term memory (Agno MCP integration)
            if self.config.get("long_term_enabled", True):
                self.long_term_provider = AgnoMemoryAdapter(
                    config=self.config.get("agno_config", {})
                )
                await self.long_term_provider.initialize()
                
            self._initialized = True
            logger.info("All memory tiers initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize tiered memory: {e}", exc_info=True)
            return False
            
    async def close(self) -> None:
        """Close all memory providers and release resources."""
        try:
            if self.short_term_provider:
                await self.short_term_provider.close()
                
            if self.medium_term_provider:
                await self.medium_term_provider.close()
                
            if self.long_term_provider:
                await self.long_term_provider.close()
                
            logger.info("All memory tiers closed")
        except Exception as e:
            logger.error(f"Error closing memory tiers: {e}", exc_info=True)
            
    async def add_memory(self, item: MemoryItem) -> str:
        """
        Add a memory item to appropriate tiers.
        
        Args:
            item: The memory item to add
            
        Returns:
            ID of the memory item
        """
        if not self._initialized:
            logger.warning("TieredMemoryManager not initialized")
            return None
            
        # Always add to short-term memory
        short_term_id = await self.short_term_provider.add_memory(item)
        
        # Add to medium-term if available
        medium_term_id = None
        if self.medium_term_provider:
            medium_term_id = await self.medium_term_provider.add_memory(item)
            
        # Determine if this memory should go to long-term storage based on importance
        long_term_id = None
        if self.long_term_provider and self._should_store_long_term(item):
            long_term_id = await self.long_term_provider.add_memory(item)
            
        # Update metadata with storage info
        if item.metadata is None:
            item.metadata = {}
            
        item.metadata["storage"] = {
            "short_term_id": short_term_id,
            "medium_term_id": medium_term_id,
            "long_term_id": long_term_id
        }
        
        # Return the primary ID (preference: medium > short > long)
        return medium_term_id or short_term_id or long_term_id
        
    async def get_conversation_history(
        self, 
        user_id: str, 
        session_id: str,
        limit: int = 20
    ) -> List[MemoryItem]:
        """
        Get recent conversation history for a user session.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            limit: Maximum number of items to retrieve
            
        Returns:
            List of memory items in chronological order
        """
        if not self._initialized:
            logger.warning("TieredMemoryManager not initialized")
            return []
            
        # Try short-term memory first (fastest)
        memories = await self.short_term_provider.get_memories(
            user_id=user_id, 
            session_id=session_id, 
            limit=limit
        )
        
        # If not enough items, try medium-term
        if self.medium_term_provider and len(memories) < limit:
            medium_memories = await self.medium_term_provider.get_memories(
                user_id=user_id,
                session_id=session_id,
                limit=limit
            )
            
            # Merge and deduplicate
            memories = self._merge_memories(memories, medium_memories, limit)
            
        # If still not enough relevant context, try long-term semantic search
        if self.long_term_provider and len(memories) < limit:
            # Use the most recent message as a query if available
            query = None
            if memories and len(memories) > 0:
                query = memories[0].text_content
                
            long_term_memories = await self.long_term_provider.get_memories(
                user_id=user_id,
                session_id=session_id,
                query=query,
                limit=limit - len(memories)
            )
            
            # Merge with existing memories
            memories = self._merge_memories(memories, long_term_memories, limit)
            
        return memories
        
    async def search_memories(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Search for relevant memories using semantic search.
        
        Args:
            user_id: The user ID
            query: Search query
            session_id: Optional session ID to limit search scope
            limit: Maximum number of results
            
        Returns:
            Relevant memory items
        """
        if not self._initialized or not self.long_term_provider:
            logger.warning("Semantic search unavailable: tiered memory not initialized or long-term provider missing")
            return []
            
        # Delegate semantic search to long-term provider (Agno)
        return await self.long_term_provider.get_memories(
            user_id=user_id,
            session_id=session_id,
            query=query,
            limit=limit
        )
        
    def _merge_memories(
        self,
        existing: List[MemoryItem],
        additional: List[MemoryItem],
        limit: int
    ) -> List[MemoryItem]:
        """
        Merge two lists of memories with deduplication.
        
        Args:
            existing: Existing memory items
            additional: Additional memory items
            limit: Maximum items to return
            
        Returns:
            Merged and deduplicated list
        """
        # Track seen memory IDs for deduplication
        seen_ids = set()
        
        # Add existing memories to results and track IDs
        result = []
        for item in existing:
            item_id = self._get_memory_identifier(item)
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                result.append(item)
                
        # Add additional memories if not already seen
        for item in additional:
            if len(result) >= limit:
                break
                
            item_id = self._get_memory_identifier(item)
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                result.append(item)
                
        # Sort by timestamp (newest first, then oldest first for conversation history)
        return sorted(result, key=lambda x: x.timestamp or datetime.min, reverse=True)
        
    def _get_memory_identifier(self, item: MemoryItem) -> str:
        """
        Get a unique identifier for a memory item.
        
        This uses available IDs in order of preference:
        1. Agno memory ID
        2. Medium-term storage ID
        3. Short-term storage ID
        4. Fallback to text content hash + timestamp
        """
        if item.metadata:
            # Check Agno ID first
            if item.metadata.get("agno_memory_id"):
                return f"agno:{item.metadata['agno_memory_id']}"
                
            # Check storage metadata
            if item.metadata.get("storage"):
                storage = item.metadata["storage"]
                if storage.get("medium_term_id"):
                    return f"medium:{storage['medium_term_id']}"
                if storage.get("short_term_id"):
                    return f"short:{storage['short_term_id']}"
                    
        # Fallback to content hash + timestamp
        timestamp_str = item.timestamp.isoformat() if item.timestamp else ""
        content_hash = hash(item.text_content or "")
        return f"hash:{content_hash}:{timestamp_str}"
        
    def _should_store_long_term(self, item: MemoryItem) -> bool:
        """
        Determine if a memory item should be stored in long-term memory.
        
        This implements a heuristic to identify important memories:
        1. All user messages (for context)
        2. System messages that meet importance criteria
        3. Messages with explicit long-term flags
        
        Args:
            item: Memory item to evaluate
            
        Returns:
            True if the item should be stored long-term
        """
        # Always store user messages
        if item.metadata and item.metadata.get("source") == "user":
            return True
            
        # Check for explicit long-term flag
        if item.metadata and item.metadata.get("long_term_storage") == True:
            return True
            
        # Check content length (longer responses may be more important)
        if item.text_content and len(item.text_content) > 100:
            return True
            
        # Check confidence score for system messages (high confidence = better to store)
        if item.metadata and item.metadata.get("confidence", 0) > 0.7:
            return True
            
        # Default to not storing
        return False