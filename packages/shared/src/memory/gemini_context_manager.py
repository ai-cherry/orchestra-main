"""
Gemini Context Manager for Cross-Agent Memory Sharing.

This module provides a shared context management system that leverages
Gemini 2.5's 2M token context window for efficient cross-agent memory sharing.
"""

import logging
import datetime
import json
from typing import Dict, List, Any, Optional, Union
import asyncio

from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class GeminiContextManager:
    """
    Manages a 2M token context window for cross-agent memory sharing.

    This manager maintains a shared context pool accessible to multiple agents,
    with priority-based memory management to optimize the use of the 2M token
    context window of Gemini 2.5.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Gemini Context Manager.

        Args:
            config: Configuration dictionary for the context manager
        """
        self.config = config or {}
        self.max_tokens = self.config.get("max_tokens", 2000000)  # 2M tokens
        self.current_tokens = 0
        self.context_items = []
        self.priority_threshold = self.config.get("priority_threshold", 0.7)
        self.token_estimator = self.config.get("token_estimator")
        self._initialized = False
        logger.info(
            f"GeminiContextManager initialized with {self.max_tokens} max tokens"
        )

    async def initialize(self) -> bool:
        """Initialize the context manager."""
        try:
            # Initialize token estimator if not provided
            if not self.token_estimator:
                from transformers import AutoTokenizer

                model_name = self.config.get("tokenizer_model", "google/gemini-2.5")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.token_estimator = lambda text: len(self.tokenizer.encode(text))

            self._initialized = True
            logger.info("GeminiContextManager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GeminiContextManager: {e}")
            return False

    async def add_to_context(
        self, memory_item: MemoryItem, priority: float = 0.5
    ) -> bool:
        """
        Add a memory item to the shared context pool with priority.

        Args:
            memory_item: The memory item to add to context
            priority: Priority score (0.0 to 1.0) with higher values indicating higher priority

        Returns:
            Whether the item was successfully added
        """
        if not self._initialized:
            logger.warning("GeminiContextManager not initialized")
            return False

        try:
            # Estimate token count
            token_count = self._estimate_tokens(memory_item)

            # If we're at capacity, manage the context window
            if self.current_tokens + token_count > self.max_tokens:
                freed_tokens = await self._prune_context(token_count)
                if freed_tokens < token_count:
                    logger.warning(
                        f"Could not free enough tokens for new context item: needed {token_count}, freed {freed_tokens}"
                    )
                    # Try adding anyway with whatever space we have

            # Add the item with metadata
            context_entry = {
                "item": memory_item,
                "priority": priority,
                "token_count": token_count,
                "added_at": datetime.datetime.now(),
                "access_count": 0,
                "last_accessed": datetime.datetime.now(),
            }

            self.context_items.append(context_entry)
            self.current_tokens += token_count

            logger.debug(
                f"Added item to context: {token_count} tokens, {self.current_tokens}/{self.max_tokens} total"
            )
            return True
        except Exception as e:
            logger.error(f"Error adding item to context: {e}")
            return False

    async def get_relevant_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """
        Get relevant context items for a given query.

        Args:
            query: The query to find relevant context for
            user_id: Optional user ID to filter context items
            session_id: Optional session ID to filter context items
            limit: Maximum number of context items to return

        Returns:
            List of relevant memory items
        """
        if not self._initialized:
            logger.warning("GeminiContextManager not initialized")
            return []

        try:
            # Find relevant items based on the query
            relevant_items = []

            # Filter by user and session if provided
            filtered_items = self.context_items
            if user_id:
                filtered_items = [
                    entry
                    for entry in filtered_items
                    if entry["item"].user_id == user_id
                ]
            if session_id:
                filtered_items = [
                    entry
                    for entry in filtered_items
                    if entry["item"].session_id == session_id
                ]

            # Sort by relevance - in a real implementation, this would use
            # semantic similarity with the query
            # Here we use a simple priority + recency score
            for entry in filtered_items:
                # Update access count and last accessed time
                entry["access_count"] += 1
                entry["last_accessed"] = datetime.datetime.now()

                # Add to relevant items
                relevant_items.append(entry["item"])

                if len(relevant_items) >= limit:
                    break

            logger.debug(f"Retrieved {len(relevant_items)} relevant context items")
            return relevant_items
        except Exception as e:
            logger.error(f"Error retrieving relevant context: {e}")
            return []

    async def clear_context(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> bool:
        """
        Clear context items, optionally filtered by user or session.

        Args:
            user_id: Optional user ID to filter items to clear
            session_id: Optional session ID to filter items to clear

        Returns:
            Whether the context was successfully cleared
        """
        if not self._initialized:
            logger.warning("GeminiContextManager not initialized")
            return False

        try:
            if user_id or session_id:
                # Filter items to keep
                items_to_keep = []
                cleared_tokens = 0

                for entry in self.context_items:
                    should_clear = True
                    if user_id and entry["item"].user_id != user_id:
                        should_clear = False
                    if session_id and entry["item"].session_id != session_id:
                        should_clear = False

                    if not should_clear:
                        items_to_keep.append(entry)
                    else:
                        cleared_tokens += entry["token_count"]

                # Update context items and token count
                self.context_items = items_to_keep
                self.current_tokens -= cleared_tokens

                logger.info(
                    f"Cleared {cleared_tokens} tokens from context for user_id={user_id}, session_id={session_id}"
                )
            else:
                # Clear all context
                self.context_items = []
                self.current_tokens = 0
                logger.info("Cleared all context")

            return True
        except Exception as e:
            logger.error(f"Error clearing context: {e}")
            return False

    async def _prune_context(self, required_tokens: int) -> int:
        """
        Remove lower priority items to make room for new items.

        Args:
            required_tokens: Number of tokens to free up

        Returns:
            Number of tokens freed
        """
        # Sort by priority (lowest first), then by last access time (oldest first)
        self.context_items.sort(key=lambda x: (x["priority"], x["last_accessed"]))

        # Remove items until we have enough space
        tokens_freed = 0
        removed_items = []

        for item in self.context_items:
            # Don't remove high priority items unless we have no choice
            if (
                tokens_freed < required_tokens
                and item["priority"] >= self.priority_threshold
            ):
                continue

            tokens_freed += item["token_count"]
            removed_items.append(item)

            if tokens_freed >= required_tokens:
                break

        # Remove the selected items
        for item in removed_items:
            self.context_items.remove(item)
            self.current_tokens -= item["token_count"]

        logger.debug(f"Pruned {len(removed_items)} items, freed {tokens_freed} tokens")
        return tokens_freed

    def _estimate_tokens(self, memory_item: MemoryItem) -> int:
        """
        Estimate the number of tokens in a memory item.

        Args:
            memory_item: The memory item to estimate tokens for

        Returns:
            Estimated token count
        """
        try:
            # Extract text content
            text = memory_item.text_content or ""

            # Add metadata as JSON
            if memory_item.metadata:
                metadata_str = json.dumps(memory_item.metadata)
                text += f" {metadata_str}"

            # Use token estimator if available
            if self.token_estimator:
                return self.token_estimator(text)

            # Fallback estimation (roughly 4 chars per token for English text)
            return len(text) // 4 + 1
        except Exception as e:
            logger.error(f"Error estimating tokens: {e}")
            # Return a conservative estimate
            return 1000
