"""
Adapter for FirestoreMemoryManager to be compatible with the async MemoryManager interface.

This module provides an adapter class that wraps the FirestoreMemoryManager
to make it compatible with the async interface defined in MemoryManager.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from future.firestore_memory_manager import FirestoreMemoryManager
from packages.shared.src.memory.memory_manager import MemoryManager, MemoryHealth
from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig
from packages.shared.src.models.domain_models import MemoryRecord

# Configure logging
logger = logging.getLogger(__name__)


class FirestoreMemoryAdapter(MemoryManager):
    """
    Adapter for FirestoreMemoryManager to be compatible with MemoryManager interface.
    
    This class wraps the sync FirestoreMemoryManager to provide an async interface
    that conforms to the MemoryManager abstract base class.
    """

    def __init__(
        self, 
        project_id: Optional[str] = None, 
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        namespace: str = "default"
    ):
        """
        Initialize the Firestore memory manager adapter.
        
        Args:
            project_id: Optional Google Cloud project ID
            credentials_json: Optional JSON string containing service account credentials
            credentials_path: Optional path to service account credentials file
            namespace: Optional namespace for memory isolation
        """
        self.firestore_manager = FirestoreMemoryManager(
            project_id=project_id,
            credentials_json=credentials_json,
            credentials_path=credentials_path
        )
        self.namespace = namespace
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the memory manager."""
        if not self._is_initialized:
            # Run the synchronous initialize method in a thread pool
            await asyncio.to_thread(self.firestore_manager.initialize)
            self._is_initialized = True
            logger.info("FirestoreMemoryAdapter initialized")

    async def close(self) -> None:
        """Close the memory manager and release resources."""
        if self._is_initialized:
            await asyncio.to_thread(self.firestore_manager.close)
            self._is_initialized = False
            logger.info("FirestoreMemoryAdapter closed")

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.
        
        Args:
            item: The memory item to store
            
        Returns:
            The ID of the created memory item
        """
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        # Convert MemoryItem to MemoryRecord
        record = self._memory_item_to_record(item)
        
        # Save the record
        record_id = await asyncio.to_thread(self.firestore_manager.save_record, record)
        return record_id

    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a specific memory item by ID.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The memory item if found, None otherwise
        """
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        try:
            # Get the record
            record = await asyncio.to_thread(self.firestore_manager.get_record, item_id)
            
            # Convert to MemoryItem
            return self._record_to_memory_item(record)
        except ValueError:
            # Record not found
            return None
        except Exception as e:
            logger.error(f"Error retrieving memory item: {e}")
            return None

    async def get_conversation_history(
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
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        # Set up filters
        query_filters = {"context": user_id}
        
        # Add session filter if provided
        if session_id:
            query_filters["metadata.session_id"] = session_id
        
        # Add any additional filters
        if filters:
            for key, value in filters.items():
                query_filters[f"metadata.{key}"] = value
        
        # Query records
        records = await asyncio.to_thread(
            self.firestore_manager.query_records, 
            query_filters
        )
        
        # Convert records to memory items
        memory_items = [self._record_to_memory_item(record) for record in records]
        
        # Sort by timestamp and apply limit
        memory_items.sort(key=lambda x: x.timestamp, reverse=True)
        return memory_items[:limit]

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings.
        
        Note: This implementation doesn't support semantic search directly.
        
        Args:
            user_id: The user ID to search memories for
            query_embedding: The vector embedding of the query
            persona_context: Optional persona context for personalized results
            top_k: Maximum number of results to return
            
        Returns:
            Empty list (not implemented)
        """
        # Semantic search not supported in the FirestoreMemoryManager yet
        return []

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.
        
        Args:
            data: The agent data to store
            
        Returns:
            The ID of the stored data
        """
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        # Convert AgentData to MemoryRecord
        record = MemoryRecord(
            record_id=data.id or f"agent_data_{data.timestamp.isoformat()}",
            context=data.agent_id,
            persona="agent",
            content=str(data.content),
            timestamp=data.timestamp,
            metadata={
                **data.metadata,
                "data_type": data.data_type,
                "agent_id": data.agent_id,
                "record_type": "agent_data"
            }
        )
        
        # Save the record to the agent data collection
        record_id = await asyncio.to_thread(
            self.firestore_manager.save_record, 
            record, 
            "agent_data"
        )
        return record_id

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in storage.
        
        Args:
            item: The memory item to check for duplicates
            
        Returns:
            True if a duplicate exists, False otherwise
        """
        # Check if content hash exists in metadata
        content_hash = item.metadata.get("content_hash")
        if not content_hash:
            return False
        
        # Query for records with matching content hash
        query_filters = {"metadata.content_hash": content_hash}
        records = await asyncio.to_thread(
            self.firestore_manager.query_records, 
            query_filters
        )
        
        return len(records) > 0

    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items from storage.
        
        Returns:
            Number of items removed
        """
        if not self._is_initialized:
            raise RuntimeError("Memory manager is not initialized")
        
        # Query for expired records
        current_time = datetime.utcnow()
        query_filters = {
            "expiration": {
                "end": current_time
            }
        }
        
        # Get expired records
        expired_records = await asyncio.to_thread(
            self.firestore_manager.query_records, 
            query_filters
        )
        
        # Delete expired records
        count = 0
        for record in expired_records:
            success = await asyncio.to_thread(
                self.firestore_manager.delete_record, 
                record.record_id
            )
            if success:
                count += 1
        
        return count

    async def health_check(self) -> MemoryHealth:
        """
        Check the health of the memory system.
        
        Returns:
            Dictionary with health status information
        """
        if not self._is_initialized:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    "status": "error",
                    "firestore": False,
                    "redis": False,
                    "error_count": 1,
                    "last_error": str(e),
                    "details": {
                        "message": f"Failed to initialize: {e}"
                    }
                }
        
        # Run the synchronous health check in a thread pool
        try:
            fs_health = await asyncio.to_thread(self.firestore_manager.health_check)
            
            # Adapt to MemoryHealth format
            health: MemoryHealth = {
                "status": fs_health["status"],
                "firestore": fs_health["firestore"],
                "redis": False,  # Not using Redis
                "error_count": fs_health.get("error_count", 0),
                "details": {
                    "provider": "firestore",
                    "adapter": "FirestoreMemoryAdapter",
                    **fs_health.get("details", {})
                }
            }
            
            if "last_error" in fs_health:
                health["last_error"] = fs_health["last_error"]
                
            return health
        except Exception as e:
            return {
                "status": "error",
                "firestore": False,
                "redis": False,
                "error_count": 1,
                "last_error": str(e),
                "details": {
                    "message": f"Health check failed: {e}"
                }
            }

    def _memory_item_to_record(self, item: MemoryItem) -> MemoryRecord:
        """
        Convert a MemoryItem to a MemoryRecord for Firestore storage.
        
        Args:
            item: The MemoryItem to convert
            
        Returns:
            A MemoryRecord with equivalent data
        """
        # Generate a record ID if not provided
        record_id = item.id or f"memory_{item.timestamp.isoformat()}"
        
        # Create and return MemoryRecord
        return MemoryRecord(
            record_id=record_id,
            context=item.user_id,
            persona=item.persona_active or "default",
            content=item.text_content or "",
            timestamp=item.timestamp,
            metadata={
                **item.metadata,
                "item_type": item.item_type,
                "session_id": item.session_id,
                "record_type": "memory_item"
            }
        )

    def _record_to_memory_item(self, record: MemoryRecord) -> MemoryItem:
        """
        Convert a MemoryRecord from Firestore to a MemoryItem.
        
        Args:
            record: The MemoryRecord to convert
            
        Returns:
            A MemoryItem with equivalent data
        """
        # Extract metadata
        metadata = dict(record.metadata)
        item_type = metadata.pop("item_type", "message")
        session_id = metadata.pop("session_id", None)
        
        # Create and return MemoryItem
        return MemoryItem(
            id=record.record_id,
            user_id=record.context,
            session_id=session_id,
            timestamp=record.timestamp,
            item_type=item_type,
            persona_active=record.persona,
            text_content=record.content,
            embedding=None,  # Embeddings not currently stored in Firestore
            metadata=metadata,
            expiration=metadata.get("expiration")
        )
