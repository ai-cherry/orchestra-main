#!/usr/bin/env python3
"""
Performance tuning utilities for the MCP memory system.

This module provides utilities for optimizing the performance of the memory system,
including token budget management, compression, and context window optimization.
"""

import time
import json
import logging
import copy
from typing import Dict, List, Optional, Any, Tuple, Set

from ..models.memory import MemoryEntry, MemoryType, MemoryScope, CompressionLevel, StorageTier
from ..config.memory_config import (
    COMPRESSION_CONFIG,
    TOKEN_BUDGET_CONFIG,
    PERFORMANCE_CONFIG,
    MEMORY_TIER_CONFIG,
)

logger = logging.getLogger(__name__)


class TokenBudgetManager:
    """Manages token budgets for different tools."""
    
    def __init__(self, tool_budgets: Optional[Dict[str, int]] = None):
        """
        Initialize the token budget manager.
        
        Args:
            tool_budgets: Optional dictionary mapping tool names to token budgets.
                          If not provided, defaults from config will be used.
        """
        self.tool_budgets = tool_budgets or TOKEN_BUDGET_CONFIG
        self.current_usage: Dict[str, int] = {tool: 0 for tool in self.tool_budgets}
    
    def estimate_tokens(self, entry: MemoryEntry) -> int:
        """
        Estimate the number of tokens for a memory entry.
        
        Args:
            entry: The memory entry to estimate tokens for
            
        Returns:
            The estimated number of tokens
        """
        # Simple estimation based on string length
        # In a real implementation, this would use a tokenizer
        if isinstance(entry.content, str):
            content_str = entry.content
        else:
            content_str = json.dumps(entry.content)
        
        # Rough approximation: 4 characters per token
        return len(content_str) // 4
    
    def can_fit_entry(self, entry: MemoryEntry, tool: str) -> bool:
        """
        Check if an entry can fit in a tool's token budget.
        
        Args:
            entry: The memory entry to check
            tool: The tool to check against
            
        Returns:
            True if the entry can fit, False otherwise
        """
        if tool not in self.tool_budgets:
            tool = "default"
        
        tokens = self.estimate_tokens(entry)
        return (self.current_usage[tool] + tokens) <= self.tool_budgets[tool]
    
    def add_entry(self, entry: MemoryEntry, tool: str) -> bool:
        """
        Add an entry to a tool's token usage.
        
        Args:
            entry: The memory entry to add
            tool: The tool to add the entry to
            
        Returns:
            True if the entry was added, False otherwise
        """
        if tool not in self.tool_budgets:
            tool = "default"
            
        if not self.can_fit_entry(entry, tool):
            return False
        
        tokens = self.estimate_tokens(entry)
        self.current_usage[tool] += tokens
        return True
    
    def remove_entry(self, entry: MemoryEntry, tool: str) -> None:
        """
        Remove an entry from a tool's token usage.
        
        Args:
            entry: The memory entry to remove
            tool: The tool to remove the entry from
        """
        if tool not in self.tool_budgets:
            tool = "default"
            
        tokens = self.estimate_tokens(entry)
        self.current_usage[tool] = max(0, self.current_usage[tool] - tokens)
    
    def get_available_budget(self, tool: str) -> int:
        """
        Get the available token budget for a tool.
        
        Args:
            tool: The tool to get the budget for
            
        Returns:
            The available token budget
        """
        if tool not in self.tool_budgets:
            tool = "default"
            
        return self.tool_budgets[tool] - self.current_usage[tool]


class MemoryCompressionEngine:
    """Handles memory compression and decompression."""
    
    @staticmethod
    def compress(entry: MemoryEntry) -> MemoryEntry:
        """
        Compress a memory entry based on its compression level.
        
        Args:
            entry: The memory entry to compress
            
        Returns:
            The compressed memory entry
        """
        if entry.compression_level == CompressionLevel.NONE:
            return entry
        
        # Create a copy to avoid modifying the original
        compressed_entry = copy.deepcopy(entry)
        
        # Get compression config for this level
        level_name = entry.compression_level.name
        level_config = COMPRESSION_CONFIG["levels"].get(level_name, {})
        
        if isinstance(entry.content, str):
            text_ratio = level_config.get("text_ratio", 1.0)
            text_threshold = COMPRESSION_CONFIG.get("text_threshold", 1000)
            
            if len(entry.content) > text_threshold:
                # Compress text based on the ratio
                keep_chars = int(len(entry.content) * text_ratio)
                if keep_chars < len(entry.content):
                    if entry.compression_level == CompressionLevel.REFERENCE_ONLY:
                        compressed_entry.content = f"[Reference: memory with hash {entry.metadata.content_hash}]"
                    else:
                        half_keep = keep_chars // 2
                        compressed_entry.content = (
                            entry.content[:half_keep] + 
                            f" ... [{level_name.lower()} compression: {len(entry.content) - keep_chars} chars removed] ... " + 
                            entry.content[-half_keep:]
                        )
        
        elif isinstance(entry.content, dict):
            json_ratio = level_config.get("json_fields_keep", 1.0)
            json_threshold = COMPRESSION_CONFIG.get("json_threshold", 500)
            
            if len(json.dumps(entry.content)) > json_threshold:
                # Compress JSON based on the ratio
                if entry.compression_level == CompressionLevel.REFERENCE_ONLY:
                    compressed_entry.content = {
                        "_compressed": True,
                        "_reference": entry.metadata.content_hash,
                        "_fields": list(entry.content.keys())
                    }
                else:
                    # Keep the most important fields based on the ratio
                    fields_to_keep = int(len(entry.content) * json_ratio)
                    if fields_to_keep < len(entry.content):
                        important_keys = list(entry.content.keys())[:fields_to_keep]
                        compressed_entry.content = {
                            k: v for k, v in entry.content.items() if k in important_keys
                        }
                        compressed_entry.content["_compressed"] = True
                        compressed_entry.content["_removed_fields"] = [
                            k for k in entry.content.keys() if k not in important_keys
                        ]
        
        return compressed_entry
    
    @staticmethod
    def decompress(entry: MemoryEntry, original_entry: Optional[MemoryEntry] = None) -> MemoryEntry:
        """
        Decompress a memory entry.
        
        Args:
            entry: The memory entry to decompress
            original_entry: The original entry if available
            
        Returns:
            The decompressed memory entry
        """
        if entry.compression_level == CompressionLevel.NONE:
            return entry
        
        # If we have the original entry, use it
        if original_entry is not None:
            return original_entry
        
        # Otherwise, we can only provide a partial decompression
        decompressed_entry = copy.deepcopy(entry)
        
        if isinstance(entry.content, dict) and entry.content.get("_compressed"):
            # For reference-only compression, we can't decompress without the original
            if "_reference" in entry.content:
                decompressed_entry.content = {
                    "warning": "This entry was compressed with REFERENCE_ONLY level and cannot be fully decompressed",
                    "hash": entry.content.get("_reference"),
                    "fields": entry.content.get("_fields", [])
                }
            # For other compression levels, we can at least remove the compression markers
            elif "_removed_fields" in entry.content:
                cleaned_content = {k: v for k, v in entry.content.items() 
                                 if k not in ["_compressed", "_removed_fields"]}
                decompressed_entry.content = cleaned_content
        
        # Set compression level to NONE to indicate it's been decompressed
        decompressed_entry.compression_level = CompressionLevel.NONE
        
        return decompressed_entry


class ContextWindowOptimizer:
    """Optimizes the context window for different tools."""
    
    def __init__(self, token_budget_manager: TokenBudgetManager):
        """
        Initialize the context window optimizer.
        
        Args:
            token_budget_manager: The token budget manager to use
        """
        self.token_budget_manager = token_budget_manager
        self.compression_engine = MemoryCompressionEngine()
    
    async def optimize_entries(
        self, 
        entries: List[Tuple[str, MemoryEntry]], 
        tool: str,
        required_keys: Optional[Set[str]] = None
    ) -> List[Tuple[str, MemoryEntry]]:
        """
        Optimize a list of memory entries to fit in a tool's context window.
        
        Args:
            entries: List of (key, entry) tuples to optimize
            tool: The tool to optimize for
            required_keys: Set of keys that must be included
            
        Returns:
            Optimized list of (key, entry) tuples
        """
        # Sort entries by priority and relevance
        entries.sort(
            key=lambda x: (x[1].priority, x[1].metadata.context_relevance), 
            reverse=True
        )
        
        # Separate required entries
        required_entries = []
        optional_entries = []
        
        if required_keys:
            for key, entry in entries:
                if key in required_keys:
                    required_entries.append((key, entry))
                else:
                    optional_entries.append((key, entry))
        else:
            optional_entries = entries
        
        # Add required entries first
        optimized_entries = []
        for key, entry in required_entries:
            # Try to add the entry as-is
            if self.token_budget_manager.add_entry(entry, tool):
                optimized_entries.append((key, entry))
                continue
                
            # If it doesn't fit, try to compress it
            for level in CompressionLevel:
                if level == CompressionLevel.NONE:
                    continue
                    
                compressed_entry = copy.deepcopy(entry)
                compressed_entry.compression_level = level
                compressed_entry = self.compression_engine.compress(compressed_entry)
                
                if self.token_budget_manager.add_entry(compressed_entry, tool):
                    optimized_entries.append((key, compressed_entry))
                    break
        
        # Add optional entries until budget is exhausted
        for key, entry in optional_entries:
            # Try to add the entry as-is
            if self.token_budget_manager.add_entry(entry, tool):
                optimized_entries.append((key, entry))
                continue
                
            # If it doesn't fit, try to compress it
            for level in CompressionLevel:
                if level == CompressionLevel.NONE:
                    continue
                    
                compressed_entry = copy.deepcopy(entry)
                compressed_entry.compression_level = level
                compressed_entry = self.compression_engine.compress(compressed_entry)
                
                if self.token_budget_manager.add_entry(compressed_entry, tool):
                    optimized_entries.append((key, compressed_entry))
                    break
        
        return optimized_entries


class MemoryTierManager:
    """Manages memory tiers for optimal performance."""
    
    def __init__(self):
        """Initialize the memory tier manager."""
        self.tier_config = MEMORY_TIER_CONFIG
    
    def determine_tier(self, entry: MemoryEntry) -> StorageTier:
        """
        Determine the appropriate storage tier for a memory entry.
        
        Args:
            entry: The memory entry to determine the tier for
            
        Returns:
            The appropriate storage tier
        """
        # Check priority thresholds
        if entry.priority >= self.tier_config["hot"]["priority_threshold"]:
            return StorageTier.HOT
        elif entry.priority >= self.tier_config["warm"]["priority_threshold"]:
            return StorageTier.WARM
        else:
            return StorageTier.COLD
    
    def should_promote(self, entry: MemoryEntry) -> bool:
        """
        Determine if a memory entry should be promoted to a higher tier.
        
        Args:
            entry: The memory entry to check
            
        Returns:
            True if the entry should be promoted, False otherwise
        """
        # Check access count and context relevance
        if entry.storage_tier == StorageTier.COLD:
            if (entry.metadata.access_count > 5 or 
                entry.metadata.context_relevance > 0.7):
                return True
        elif entry.storage_tier == StorageTier.WARM:
            if (entry.metadata.access_count > 10 or 
                entry.metadata.context_relevance > 0.9):
                return True
        
        return False
    
    def should_demote(self, entry: MemoryEntry) -> bool:
        """
        Determine if a memory entry should be demoted to a lower tier.
        
        Args:
            entry: The memory entry to check
            
        Returns:
            True if the entry should be demoted, False otherwise
        """
        # Check last accessed time
        current_time = time.time()
        if entry.storage_tier == StorageTier.HOT:
            if (current_time - entry.metadata.last_accessed > 
                self.tier_config["hot"]["ttl_seconds"]):
                return True
        elif entry.storage_tier == StorageTier.WARM:
            if (current_time - entry.metadata.last_accessed > 
                self.tier_config["warm"]["ttl_seconds"]):
                return True
        
        return False
    
    def promote_tier(self, entry: MemoryEntry) -> MemoryEntry:
        """
        Promote a memory entry to a higher tier.
        
        Args:
            entry: The memory entry to promote
            
        Returns:
            The promoted memory entry
        """
        promoted_entry = copy.deepcopy(entry)
        
        if entry.storage_tier == StorageTier.COLD:
            promoted_entry.storage_tier = StorageTier.WARM
        elif entry.storage_tier == StorageTier.WARM:
            promoted_entry.storage_tier = StorageTier.HOT
        
        return promoted_entry
    
    def demote_tier(self, entry: MemoryEntry) -> MemoryEntry:
        """
        Demote a memory entry to a lower tier.
        
        Args:
            entry: The memory entry to demote
            
        Returns:
            The demoted memory entry
        """
        demoted_entry = copy.deepcopy(entry)
        
        if entry.storage_tier == StorageTier.HOT:
            demoted_entry.storage_tier = StorageTier.WARM
        elif entry.storage_tier == StorageTier.WARM:
            demoted_entry.storage_tier = StorageTier.COLD
        
        return demoted_entry