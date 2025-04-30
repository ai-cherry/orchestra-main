"""
Memory Manager for AI Orchestration System.

This module provides the main MemoryManager class which acts as a factory
and orchestrator for different concrete memory implementations.
It selects and delegates operations to the appropriate backend
(e.g., Firestore V1, Firestore V2, etc.) based on configuration.
"""

import logging
from typing import Any, Dict, List, Optional, Union, TypedDict

from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig
from packages.shared.src.memory.memory_interface import MemoryInterface
from packages.shared.src.memory.memory_types import MemoryHealth
from packages.shared.src.memory.base_memory_manager import BaseMemoryManager
from packages.shared.src.memory.concrete_memory_manager import FirestoreV1MemoryManager # Assuming this is the refactored name
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager # Need to import the V1 storage class to instantiate it

# Set up logger
logger = logging.getLogger(__name__)

class MemoryManager(MemoryInterface): # The main MemoryManager should implement the interface
    """
    Main Memory Manager class.

    This class acts as a factory and orchestrator for different concrete
    memory implementations, delegating operations based on configuration.
    """
    def __init__(
        self,
        memory_backend_type: str = "firestore_v1", # Configuration parameter
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_password: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour default
        # Add parameters for other backends as needed
    ):
        """
        Initialize the main memory manager.

        Args:
            memory_backend_type: The type of memory backend to use (e.g., "firestore_v1").
            project_id: Optional Google Cloud project ID for Firestore.
            credentials_json: Optional JSON string for Firestore credentials.
            credentials_path: Optional path for Firestore credentials file.
            redis_host: Optional Redis host.
            redis_port: Optional Redis port.
            redis_password: Optional Redis password.
            cache_ttl: Cache TTL in seconds for Redis.
        """
        self._backend: BaseMemoryManager # The chosen concrete backend

        if memory_backend_type == "firestore_v1":
            # Need to instantiate FirestoreMemoryManager first, then pass it to FirestoreV1MemoryManager
            firestore_v1_storage = FirestoreMemoryManager(
                 project_id=project_id,
                 credentials_json=credentials_json,
                 credentials_path=credentials_path,
            )
            self._backend = FirestoreV1MemoryManager(
                firestore_memory=firestore_v1_storage,
                redis_host=redis_host,
                redis_port=redis_port,
                redis_password=redis_password,
                cache_ttl=cache_ttl,
            )
        # Add logic for other backend types here (e.g., "firestore_v2")
        # elif memory_backend_type == "firestore_v2":
        #     self._backend = FirestoreV2MemoryManager(...)
        else:
            raise ValueError(f"Unknown memory backend type: {memory_backend_type}")

        logger.info(f"MemoryManager initialized with backend: {memory_backend_type}")

    async def initialize(self) -> None:
        """Initialize the selected memory backend."""
        await self._backend.initialize()

    async def close(self) -> None:
        """Close the selected memory backend."""
        await self._backend.close()

    async def add_memory_item(self, item: MemoryItem) -> str:
        """Add a memory item to storage via the selected backend."""
        return await self._backend.add_memory_item(item)

    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory item by ID via the selected backend."""
        return await self._backend.get_memory_item(item_id)

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """Retrieve conversation history for a user via the selected backend."""
        return await self._backend.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            filters=filters,
        )

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """Perform semantic search via the selected backend."""
        return await self._backend.semantic_search(
            user_id=user_id,
            query_embedding=query_embedding,
            persona_context=persona_context,
            top_k=top_k,
        )

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """Store raw agent data via the selected backend."""
        return await self._backend.add_raw_agent_data(data)

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """Check if a memory item already exists via the selected backend."""
        return await self._backend.check_duplicate(item)

    async def cleanup_expired_items(self) -> int:
        """Remove expired items via the selected backend."""
        return await self._backend.cleanup_expired_items()

    async def health_check(self) -> MemoryHealth:
        """Check the health of the selected memory backend."""
        return await self._backend.health_check()

    # Add other methods from MemoryInterface here, delegating to self._backend
    # async def add_message_to_conversation(self, conversation_id: str, message: dict):
    #     await self._backend.add_message_to_conversation(conversation_id, message)
