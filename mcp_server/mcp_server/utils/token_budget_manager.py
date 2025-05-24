# import os  # Removed unused import

"""
token_budget_manager.py - Optimized Token Budget Manager

This module provides an optimized token budget manager for estimating and tracking
token usage across different tools. It uses caching and heuristics for efficient
token estimation without requiring a full tokenizer.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

# Import from relative paths
from ..models.memory import MemoryEntry

logger = logging.getLogger(__name__)


class TokenBudgetManager:
    """Optimized token budget manager with caching and heuristics."""

    def __init__(self, tool_budgets: Dict[str, int]):
        """Initialize with token budgets for each tool.

        Args:
            tool_budgets: Dictionary mapping tool names to their token budgets
        """
        self.tool_budgets = tool_budgets
        self.current_usage = {tool: 0 for tool in tool_budgets}
        self.token_cache: Dict[str, int] = {}  # Cache for token counts
        self.max_cache_size = 10000  # Maximum number of entries to cache

        # Regex patterns for quick estimation
        self.word_pattern = re.compile(r"\b\w+\b")
        self.special_char_pattern = re.compile(r"[^\w\s]")
        self.whitespace_pattern = re.compile(r"\s+")

        logger.info(f"Initialized TokenBudgetManager with budgets: {tool_budgets}")

    def estimate_tokens(self, entry: MemoryEntry) -> int:
        """Estimate tokens with caching and heuristics.

        Args:
            entry: The memory entry to estimate tokens for

        Returns:
            int: Estimated token count
        """
        # Check cache first if content hash is available
        if entry.metadata.content_hash and entry.metadata.content_hash in self.token_cache:
            return self.token_cache[entry.metadata.content_hash]

        # Convert content to string
        if isinstance(entry.content, str):
            content_str = entry.content
        else:
            try:
                content_str = json.dumps(entry.content)
            except (TypeError, ValueError):
                # Fallback for non-serializable content
                content_str = str(entry.content)

        # Use heuristics for estimation:
        # 1. Count words (approx 0.75 tokens per word)
        # 2. Count special characters (approx 1 token per special char)
        # 3. Count whitespace (approx 0.25 tokens per whitespace)
        # 4. Add overhead for structure

        word_count = len(self.word_pattern.findall(content_str))
        special_char_count = len(self.special_char_pattern.findall(content_str))
        whitespace_count = len(self.whitespace_pattern.findall(content_str))

        # Calculate token estimate
        token_estimate = int(word_count * 0.75 + special_char_count + whitespace_count * 0.25 + 4)

        # Cache the result if content hash is available
        if entry.metadata.content_hash:
            # Manage cache size
            if len(self.token_cache) >= self.max_cache_size:
                # Simple strategy: clear half the cache when it gets full
                keys_to_remove = list(self.token_cache.keys())[: self.max_cache_size // 2]
                for key in keys_to_remove:
                    del self.token_cache[key]
                logger.debug(f"Token cache cleared to {len(self.token_cache)} entries")

            self.token_cache[entry.metadata.content_hash] = token_estimate

        return token_estimate

    def can_fit_entry(self, entry: MemoryEntry, tool: str) -> bool:
        """Check if an entry can fit in a tool's token budget.

        Args:
            entry: The memory entry to check
            tool: The tool to check against

        Returns:
            bool: True if the entry can fit, False otherwise
        """
        if tool not in self.tool_budgets:
            logger.warning(f"Tool {tool} not found in budget configuration")
            return False

        tokens = self.estimate_tokens(entry)
        return (self.current_usage[tool] + tokens) <= self.tool_budgets[tool]

    def add_entry(self, entry: MemoryEntry, tool: str) -> bool:
        """Add an entry to a tool's token usage.

        Args:
            entry: The memory entry to add
            tool: The tool to add the entry to

        Returns:
            bool: True if the entry was added, False if it couldn't fit
        """
        if not self.can_fit_entry(entry, tool):
            logger.warning(f"Entry {entry.metadata.content_hash} doesn't fit in {tool}'s budget")
            return False

        tokens = self.estimate_tokens(entry)
        self.current_usage[tool] += tokens
        logger.debug(f"Added {tokens} tokens to {tool}, new usage: {self.current_usage[tool]}")
        return True

    def remove_entry(self, entry: MemoryEntry, tool: str) -> None:
        """Remove an entry from a tool's token usage.

        Args:
            entry: The memory entry to remove
            tool: The tool to remove the entry from
        """
        if tool not in self.tool_budgets:
            logger.warning(f"Tool {tool} not found in budget configuration")
            return

        tokens = self.estimate_tokens(entry)
        self.current_usage[tool] = max(0, self.current_usage[tool] - tokens)
        logger.debug(f"Removed {tokens} tokens from {tool}, new usage: {self.current_usage[tool]}")

    def get_available_budget(self, tool: str) -> int:
        """Get the available token budget for a tool.

        Args:
            tool: The tool to get the budget for

        Returns:
            int: Available token budget (0 if tool not found)
        """
        if tool not in self.tool_budgets:
            logger.warning(f"Tool {tool} not found in budget configuration")
            return 0

        return self.tool_budgets[tool] - self.current_usage[tool]

    def reset_usage(self, tool: Optional[str] = None) -> None:
        """Reset token usage for a specific tool or all tools.

        Args:
            tool: The tool to reset, or None to reset all tools
        """
        if tool:
            if tool in self.current_usage:
                self.current_usage[tool] = 0
                logger.debug(f"Reset token usage for {tool}")
            else:
                logger.warning(f"Tool {tool} not found in budget configuration")
        else:
            self.current_usage = {tool: 0 for tool in self.tool_budgets}
            logger.debug("Reset token usage for all tools")

    def get_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get token usage statistics for all tools.

        Returns:
            Dict: Token usage statistics
        """
        stats = {}
        for tool in self.tool_budgets:
            used = self.current_usage.get(tool, 0)
            total = self.tool_budgets[tool]
            stats[tool] = {
                "used": used,
                "total": total,
                "available": total - used,
                "percentage": round((used / total) * 100, 2) if total > 0 else 0,
            }

        return stats
