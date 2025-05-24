"""
LangChain memory integration wrapper.

This module provides LangChain-compatible memory interfaces that wrap
our three-tier memory system, enabling seamless integration with
LangChain agents and chains.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from langchain.memory.chat_memory import BaseChatMemory
    from langchain.memory.chat_message_histories import ChatMessageHistory
    from langchain.memory.summary_buffer import ConversationSummaryBufferMemory
    from langchain.memory.utils import get_prompt_input_key
    from langchain.schema import AIMessage, BaseMemory, BaseMessage, HumanMessage

    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    BaseChatMemory = object
    BaseMemory = object
    BaseMessage = object
    HumanMessage = object
    AIMessage = object
    ChatMessageHistory = object
    ConversationSummaryBufferMemory = object

from ..utils.structured_logging import get_logger
from .base import MemoryEntry, MemoryMetadata, MemoryTier
from .dragonfly_cache import DragonflyCache
from .firestore_episodic import FirestoreEpisodicMemory
from .qdrant_semantic import QdrantSemanticMemory

logger = get_logger(__name__)


class LangChainMemoryWrapper(BaseChatMemory):
    """
    LangChain-compatible wrapper for our three-tier memory system.

    This wrapper provides:
    - ChatMessageHistory interface for conversation memory
    - Automatic tiering based on message age and importance
    - Vector embeddings for semantic search
    - Performance-optimized storage and retrieval
    """

    def __init__(
        self,
        memory_key: str = "history",
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        return_messages: bool = True,
        dragonfly_config: Optional[Dict[str, Any]] = None,
        firestore_config: Optional[Dict[str, Any]] = None,
        qdrant_config: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize LangChain memory wrapper.

        Args:
            memory_key: Key to store conversation history
            input_key: Key for input messages
            output_key: Key for output messages
            return_messages: Whether to return messages or strings
            dragonfly_config: Configuration for DragonflyDB cache
            firestore_config: Configuration for Firestore episodic memory
            qdrant_config: Configuration for Qdrant semantic memory
            session_id: Optional session identifier for isolation
        """
        if not HAS_LANGCHAIN:
            raise ImportError("langchain not installed. Install with: pip install langchain")

        super().__init__(**kwargs)

        self.memory_key = memory_key
        self.input_key = input_key
        self.output_key = output_key
        self.return_messages = return_messages
        self.session_id = session_id or "default"

        # Initialize memory tiers
        self.hot_memory = DragonflyCache(dragonfly_config)
        self.warm_memory = FirestoreEpisodicMemory(firestore_config)
        self.cold_memory = QdrantSemanticMemory(qdrant_config)

        # Message history cache
        self._message_cache: List[BaseMessage] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all memory backends."""
        if self._initialized:
            return

        try:
            # Initialize all tiers
            hot_ok = await self.hot_memory.initialize()
            warm_ok = await self.warm_memory.initialize()
            cold_ok = await self.cold_memory.initialize()

            if not hot_ok:
                logger.error("Failed to initialize hot memory tier")
            if not warm_ok:
                logger.error("Failed to initialize warm memory tier")
            if not cold_ok:
                logger.warning("Cold memory tier not initialized (stub)")

            self._initialized = hot_ok and warm_ok

            # Load recent messages into cache
            await self._load_recent_messages()

            logger.info("LangChain memory wrapper initialized")

        except Exception as e:
            logger.error(f"Failed to initialize LangChain memory: {e}")
            raise

    async def _load_recent_messages(self, limit: int = 100) -> None:
        """Load recent messages from storage into cache."""
        try:
            # Try hot tier first
            keys = await self.hot_memory.list_keys(prefix=f"{self.session_id}:")

            # Get messages
            messages = []
            for key in keys[-limit:]:  # Get last N keys
                entry = await self.hot_memory.get(key)
                if entry and isinstance(entry.content, dict):
                    msg_type = entry.content.get("type", "human")
                    msg_content = entry.content.get("content", "")

                    if msg_type == "human":
                        messages.append(HumanMessage(content=msg_content))
                    elif msg_type == "ai":
                        messages.append(AIMessage(content=msg_content))

            self._message_cache = messages

        except Exception as e:
            logger.error(f"Failed to load recent messages: {e}")

    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables for LangChain."""
        if not self._initialized:
            # Synchronous fallback - not ideal but required by LangChain interface
            import asyncio

            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.initialize())

        if self.return_messages:
            return {self.memory_key: self._message_cache}
        else:
            # Convert messages to string
            messages_str = "\n".join([f"{msg.__class__.__name__}: {msg.content}" for msg in self._message_cache])
            return {self.memory_key: messages_str}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to memory (synchronous wrapper)."""
        import asyncio

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.asave_context(inputs, outputs))

    async def asave_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to memory asynchronously."""
        await self.initialize()

        try:
            # Extract input and output
            input_key = self.input_key or get_prompt_input_key(inputs, self.memory_variables)
            output_key = self.output_key or list(outputs.keys())[0]

            human_message = inputs.get(input_key, "")
            ai_message = outputs.get(output_key, "")

            # Create memory entries
            timestamp = datetime.utcnow()

            # Save human message
            if human_message:
                human_entry = MemoryEntry(
                    key=f"{self.session_id}:human:{timestamp.isoformat()}",
                    content={
                        "type": "human",
                        "content": human_message,
                        "timestamp": timestamp.isoformat(),
                        "session_id": self.session_id,
                    },
                    metadata=MemoryMetadata(
                        tags=["conversation", "human", self.session_id],
                        source="langchain",
                        ttl_seconds=3600,  # 1 hour in hot tier
                    ),
                )

                await self.hot_memory.save(human_entry)
                self._message_cache.append(HumanMessage(content=human_message))

            # Save AI message
            if ai_message:
                ai_entry = MemoryEntry(
                    key=f"{self.session_id}:ai:{timestamp.isoformat()}",
                    content={
                        "type": "ai",
                        "content": ai_message,
                        "timestamp": timestamp.isoformat(),
                        "session_id": self.session_id,
                    },
                    metadata=MemoryMetadata(
                        tags=["conversation", "ai", self.session_id],
                        source="langchain",
                        ttl_seconds=3600,  # 1 hour in hot tier
                    ),
                )

                await self.hot_memory.save(ai_entry)
                self._message_cache.append(AIMessage(content=ai_message))

            # Trim cache if too large
            if len(self._message_cache) > 1000:
                self._message_cache = self._message_cache[-500:]

            # Trigger background migration if needed
            asyncio.create_task(self._migrate_old_messages())

        except Exception as e:
            logger.error(f"Failed to save context: {e}")

    async def _migrate_old_messages(self) -> None:
        """Migrate old messages from hot to warm tier."""
        try:
            # Get all session keys
            keys = await self.hot_memory.list_keys(prefix=f"{self.session_id}:")

            for key in keys:
                entry = await self.hot_memory.get(key)
                if not entry:
                    continue

                # Check if should migrate
                target_tier = self.hot_memory.should_migrate(entry)
                if target_tier == MemoryTier.WARM:
                    # Save to warm tier
                    entry.metadata.tier = MemoryTier.WARM
                    entry.metadata.ttl_seconds = 86400  # 24 hours

                    if await self.warm_memory.save(entry):
                        # Delete from hot tier
                        await self.hot_memory.delete(key)
                        logger.debug(f"Migrated {key} to warm tier")

        except Exception as e:
            logger.error(f"Failed to migrate messages: {e}")

    def clear(self) -> None:
        """Clear memory (synchronous wrapper)."""
        import asyncio

        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.aclear())

    async def aclear(self) -> None:
        """Clear memory asynchronously."""
        await self.initialize()

        try:
            # Clear all tiers for this session
            hot_count = await self.hot_memory.clear(prefix=f"{self.session_id}:")
            warm_count = await self.warm_memory.clear(prefix=f"{self.session_id}:")
            cold_count = await self.cold_memory.clear(prefix=f"{self.session_id}:")

            # Clear cache
            self._message_cache.clear()

            logger.info(f"Cleared session {self.session_id}: " f"hot={hot_count}, warm={warm_count}, cold={cold_count}")

        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        tiers: Optional[List[MemoryTier]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search across memory tiers.

        Args:
            query: Search query
            limit: Maximum results per tier
            tiers: Specific tiers to search (default: all)

        Returns:
            List of search results with metadata
        """
        await self.initialize()

        results = []
        search_tiers = tiers or [MemoryTier.HOT, MemoryTier.WARM, MemoryTier.COLD]

        try:
            # Search each tier
            if MemoryTier.HOT in search_tiers:
                hot_results = await self.hot_memory.search(query, limit, {"prefix": self.session_id})
                results.extend(
                    [
                        {
                            "tier": "hot",
                            "entry": r.entry,
                            "score": r.score,
                        }
                        for r in hot_results
                    ]
                )

            if MemoryTier.WARM in search_tiers:
                warm_results = await self.warm_memory.search(query, limit, {"tags": [self.session_id]})
                results.extend(
                    [
                        {
                            "tier": "warm",
                            "entry": r.entry,
                            "score": r.score,
                        }
                        for r in warm_results
                    ]
                )

            if MemoryTier.COLD in search_tiers:
                cold_results = await self.cold_memory.search(query, limit, {"tags": [self.session_id]})
                results.extend(
                    [
                        {
                            "tier": "cold",
                            "entry": r.entry,
                            "score": r.score,
                        }
                        for r in cold_results
                    ]
                )

            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)

            return results[:limit]

        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        await self.initialize()

        try:
            hot_stats = await self.hot_memory.stats()
            warm_stats = await self.warm_memory.stats()
            cold_stats = await self.cold_memory.stats()

            return {
                "session_id": self.session_id,
                "message_cache_size": len(self._message_cache),
                "tiers": {
                    "hot": hot_stats,
                    "warm": warm_stats,
                    "cold": cold_stats,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


class ConversationSummaryBufferMemoryWrapper(ConversationSummaryBufferMemory):
    """
    Enhanced ConversationSummaryBufferMemory with three-tier storage.

    This wrapper extends LangChain's ConversationSummaryBufferMemory with:
    - Automatic summarization when buffer exceeds token limit
    - Storage of summaries in warm/cold tiers
    - Retrieval of relevant summaries based on context
    """

    def __init__(
        self,
        llm: Any,  # LangChain LLM instance
        max_token_limit: int = 2000,
        moving_summary_buffer: str = "",
        memory_wrapper: Optional[LangChainMemoryWrapper] = None,
        **kwargs,
    ):
        """
        Initialize summary buffer memory.

        Args:
            llm: LangChain LLM for generating summaries
            max_token_limit: Maximum tokens before summarization
            moving_summary_buffer: Initial summary buffer
            memory_wrapper: Optional existing memory wrapper
        """
        super().__init__(
            llm=llm, max_token_limit=max_token_limit, moving_summary_buffer=moving_summary_buffer, **kwargs
        )

        # Use provided wrapper or create new one
        self.memory_wrapper = memory_wrapper or LangChainMemoryWrapper()

    async def asave_summary(self, summary: str) -> None:
        """Save summary to warm tier."""
        await self.memory_wrapper.initialize()

        try:
            summary_entry = MemoryEntry(
                key=f"{self.memory_wrapper.session_id}:summary:{datetime.utcnow().isoformat()}",
                content={
                    "type": "summary",
                    "content": summary,
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_id": self.memory_wrapper.session_id,
                    "token_count": len(summary.split()),  # Rough estimate
                },
                metadata=MemoryMetadata(
                    tags=["summary", self.memory_wrapper.session_id],
                    source="langchain_summary",
                    tier=MemoryTier.WARM,
                    ttl_seconds=86400 * 7,  # 7 days
                ),
            )

            await self.memory_wrapper.warm_memory.save(summary_entry)
            logger.info(f"Saved conversation summary ({len(summary)} chars)")

        except Exception as e:
            logger.error(f"Failed to save summary: {e}")

    async def aget_relevant_summaries(self, query: str, limit: int = 3) -> List[str]:
        """Retrieve relevant summaries based on query."""
        await self.memory_wrapper.initialize()

        try:
            # Search for relevant summaries
            results = await self.memory_wrapper.warm_memory.search(
                query,
                limit,
                {
                    "tags": ["summary", self.memory_wrapper.session_id],
                },
            )

            summaries = []
            for result in results:
                if result.entry.content.get("type") == "summary":
                    summaries.append(result.entry.content.get("content", ""))

            return summaries

        except Exception as e:
            logger.error(f"Failed to get relevant summaries: {e}")
            return []
