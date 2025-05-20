#!/usr/bin/env python3
"""
memory_sync_engine.py - MCP Memory Synchronization Engine

This module implements the Enhanced Memory Synchronization Engine described in the
strategic analysis for multi-tool AI integration. It provides bi-directional memory
synchronization between different AI tools through a unified schema and intelligent
context window management, supporting the Single Source of Truth (SSOT) architecture.

Key features:
- Unified memory schema across all tools
- Bi-directional synchronization with conflict resolution
- Token budget management and context optimization
- Tiered storage with hot/warm/cold memory partitioning
- Adaptive compression strategies
"""

import os
import json
import time
import logging
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mcp-memory-sync-engine")


class MemoryType(str, Enum):
    """Memory type classification."""

    SHARED = "shared"
    TOOL_SPECIFIC = "tool_specific"


class MemoryScope(str, Enum):
    """Memory scope classification - simplified for single-user project."""

    SESSION = "session"  # Keep session scope for basic functionality
    GLOBAL = "global"  # Keep global scope for shared data


class ToolType(str, Enum):
    """Supported AI tools."""

    ROO = "roo"
    CLINE = "cline"
    GEMINI = "gemini"
    COPILOT = "copilot"


class CompressionLevel(int, Enum):
    """Memory compression levels."""

    NONE = 0
    LIGHT = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4
    REFERENCE_ONLY = 5


class StorageTier(str, Enum):
    """Memory storage tiers."""

    HOT = "hot"  # Frequently accessed, high-priority content
    WARM = "warm"  # Recent but not critical content
    COLD = "cold"  # Historical content, primarily in large context tools


@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""

    source_tool: ToolType
    last_modified: float
    access_count: int = 0
    context_relevance: float = 0.5
    last_accessed: float = field(default_factory=time.time)
    version: int = 1
    sync_status: Dict[str, int] = field(default_factory=dict)
    content_hash: Optional[str] = None


@dataclass
class MemoryEntry:
    """Unified memory entry conforming to the schema."""

    memory_type: MemoryType
    scope: MemoryScope
    priority: int
    compression_level: CompressionLevel
    ttl_seconds: int
    content: Any
    metadata: MemoryMetadata
    storage_tier: StorageTier = StorageTier.HOT

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory entry to a dictionary."""
        return {
            "memory_type": self.memory_type,
            "scope": self.scope,
            "priority": self.priority,
            "compression_level": self.compression_level,
            "ttl_seconds": self.ttl_seconds,
            "content": self.content,
            "metadata": {
                "source_tool": self.metadata.source_tool,
                "last_modified": self.metadata.last_modified,
                "access_count": self.metadata.access_count,
                "context_relevance": self.metadata.context_relevance,
                "last_accessed": self.metadata.last_accessed,
                "version": self.metadata.version,
                "sync_status": self.metadata.sync_status,
                "content_hash": self.metadata.content_hash,
            },
            "storage_tier": self.storage_tier,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create a memory entry from a dictionary."""
        metadata = MemoryMetadata(
            source_tool=data["metadata"]["source_tool"],
            last_modified=data["metadata"]["last_modified"],
            access_count=data["metadata"]["access_count"],
            context_relevance=data["metadata"]["context_relevance"],
            last_accessed=data["metadata"].get("last_accessed", time.time()),
            version=data["metadata"].get("version", 1),
            sync_status=data["metadata"].get("sync_status", {}),
            content_hash=data["metadata"].get("content_hash"),
        )

        return cls(
            memory_type=data["memory_type"],
            scope=data["scope"],
            priority=data["priority"],
            compression_level=data["compression_level"],
            ttl_seconds=data["ttl_seconds"],
            content=data["content"],
            metadata=metadata,
            storage_tier=data.get("storage_tier", StorageTier.HOT),
        )

    def is_expired(self) -> bool:
        """Check if the memory entry has expired."""
        age = time.time() - self.metadata.last_modified
        return age > self.ttl_seconds

    def update_access(self) -> None:
        """Update the access metadata."""
        self.metadata.access_count += 1
        self.metadata.last_accessed = time.time()

    def compute_hash(self) -> str:
        """Compute a hash of the content."""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def update_hash(self) -> None:
        """Update the content hash."""
        self.metadata.content_hash = self.compute_hash()


class MemoryCompressionEngine:
    """Handles memory compression and decompression."""

    @staticmethod
    def compress(entry: MemoryEntry) -> MemoryEntry:
        """Compress a memory entry based on its compression level."""
        if entry.compression_level == CompressionLevel.NONE:
            return entry

        compressed_entry = entry

        if isinstance(entry.content, str):
            if entry.compression_level == CompressionLevel.LIGHT:
                # Basic compression: truncate long strings with ellipsis
                if len(entry.content) > 1000:
                    compressed_entry.content = entry.content[:900] + "... [compressed]"

            elif entry.compression_level == CompressionLevel.MEDIUM:
                # Medium compression: extract key sentences
                if len(entry.content) > 500:
                    sentences = entry.content.split(". ")
                    if len(sentences) > 5:
                        important_sentences = sentences[:2] + ["..."] + sentences[-2:]
                        compressed_entry.content = ". ".join(important_sentences)

            elif entry.compression_level == CompressionLevel.HIGH:
                # High compression: keep only first and last paragraph
                if len(entry.content) > 300:
                    paragraphs = entry.content.split("\n\n")
                    if len(paragraphs) > 2:
                        compressed_entry.content = (
                            paragraphs[0]
                            + "\n\n... [highly compressed] ...\n\n"
                            + paragraphs[-1]
                        )

            elif entry.compression_level == CompressionLevel.EXTREME:
                # Extreme compression: keep only first paragraph
                if len(entry.content) > 100:
                    paragraphs = entry.content.split("\n\n")
                    compressed_entry.content = (
                        paragraphs[0] + " ... [extremely compressed]"
                    )

            elif entry.compression_level == CompressionLevel.REFERENCE_ONLY:
                # Reference only: keep only a reference to the original content
                compressed_entry.content = (
                    f"[Reference: memory with hash {entry.metadata.content_hash}]"
                )

        elif isinstance(entry.content, dict):
            if entry.compression_level == CompressionLevel.LIGHT:
                # For dictionaries, keep only key fields
                important_keys = set(list(entry.content.keys())[:5])
                compressed_entry.content = {
                    k: v for k, v in entry.content.items() if k in important_keys
                }
                if len(entry.content) > len(compressed_entry.content):
                    compressed_entry.content["_compressed"] = True

            elif entry.compression_level == CompressionLevel.MEDIUM:
                # Keep only 3 key fields
                important_keys = set(list(entry.content.keys())[:3])
                compressed_entry.content = {
                    k: v for k, v in entry.content.items() if k in important_keys
                }
                compressed_entry.content["_compressed"] = True

            elif entry.compression_level in [
                CompressionLevel.HIGH,
                CompressionLevel.EXTREME,
                CompressionLevel.REFERENCE_ONLY,
            ]:
                # Keep only key names for higher compression levels
                compressed_entry.content = {
                    "_compressed": True,
                    "_keys": list(entry.content.keys()),
                }

        # Update the compression metadata
        if entry.content != compressed_entry.content:
            logger.debug(
                f"Compressed memory entry from {len(str(entry.content))} to {len(str(compressed_entry.content))} chars"
            )

        return compressed_entry

    @staticmethod
    def decompress(
        entry: MemoryEntry, original_storage: "MemoryStorage"
    ) -> MemoryEntry:
        """Attempt to decompress a memory entry if possible."""
        if entry.compression_level == CompressionLevel.NONE:
            return entry

        # For REFERENCE_ONLY, try to retrieve the original
        if (
            entry.compression_level == CompressionLevel.REFERENCE_ONLY
            and entry.metadata.content_hash
        ):
            original = original_storage.get_by_hash(entry.metadata.content_hash)
            if original:
                # Create a new entry with the original content but keep current metadata
                decompressed = MemoryEntry(
                    memory_type=entry.memory_type,
                    scope=entry.scope,
                    priority=entry.priority,
                    compression_level=CompressionLevel.NONE,  # Mark as uncompressed
                    ttl_seconds=entry.ttl_seconds,
                    content=original.content,
                    metadata=entry.metadata,
                    storage_tier=entry.storage_tier,
                )
                return decompressed

        # For now, we can't fully decompress other compression levels
        # In a real implementation, we might store the original separately
        return entry


class TokenBudgetManager:
    """Manages token budgets for different tools."""

    def __init__(self, tool_budgets: Dict[ToolType, int]):
        """Initialize with token budgets for each tool."""
        self.tool_budgets = tool_budgets
        self.current_usage = {tool: 0 for tool in tool_budgets}

    def estimate_tokens(self, entry: MemoryEntry) -> int:
        """Estimate the number of tokens for a memory entry."""
        # Simple estimation based on string length
        # In a real implementation, this would use a tokenizer
        content_str = json.dumps(entry.content)
        # Rough approximation: 4 characters per token
        return len(content_str) // 4

    def can_fit_entry(self, entry: MemoryEntry, tool: ToolType) -> bool:
        """Check if an entry can fit in a tool's token budget."""
        if tool not in self.tool_budgets:
            return False

        tokens = self.estimate_tokens(entry)
        return (self.current_usage[tool] + tokens) <= self.tool_budgets[tool]

    def add_entry(self, entry: MemoryEntry, tool: ToolType) -> bool:
        """Add an entry to a tool's token usage."""
        if not self.can_fit_entry(entry, tool):
            return False

        tokens = self.estimate_tokens(entry)
        self.current_usage[tool] += tokens
        return True

    def remove_entry(self, entry: MemoryEntry, tool: ToolType) -> None:
        """Remove an entry from a tool's token usage."""
        tokens = self.estimate_tokens(entry)
        self.current_usage[tool] = max(0, self.current_usage[tool] - tokens)

    def get_available_budget(self, tool: ToolType) -> int:
        """Get the available token budget for a tool."""
        if tool not in self.tool_budgets:
            return 0

        return self.tool_budgets[tool] - self.current_usage[tool]

    def optimize_for_tool(
        self, entries: List[MemoryEntry], tool: ToolType
    ) -> List[MemoryEntry]:
        """Optimize a list of entries to fit within a tool's budget."""
        if tool not in self.tool_budgets:
            return []

        # Sort entries by priority (high to low)
        sorted_entries = sorted(
            entries,
            key=lambda e: (e.priority, e.metadata.context_relevance),
            reverse=True,
        )

        optimized_entries = []
        current_tokens = 0
        budget = self.tool_budgets[tool]

        for entry in sorted_entries:
            tokens = self.estimate_tokens(entry)

            if (current_tokens + tokens) <= budget:
                # Entry fits as-is
                optimized_entries.append(entry)
                current_tokens += tokens
            else:
                # Try to compress the entry to make it fit
                for level in CompressionLevel:
                    if level == CompressionLevel.NONE:
                        continue

                    compressed_entry = MemoryEntry(
                        memory_type=entry.memory_type,
                        scope=entry.scope,
                        priority=entry.priority,
                        compression_level=level,
                        ttl_seconds=entry.ttl_seconds,
                        content=entry.content,
                        metadata=entry.metadata,
                        storage_tier=entry.storage_tier,
                    )

                    compressed_entry = MemoryCompressionEngine.compress(
                        compressed_entry
                    )
                    compressed_tokens = self.estimate_tokens(compressed_entry)

                    if (current_tokens + compressed_tokens) <= budget:
                        optimized_entries.append(compressed_entry)
                        current_tokens += compressed_tokens
                        break

        return optimized_entries


class MemoryStorage:
    """Base class for memory storage backends."""

    def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry."""
        raise NotImplementedError

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        raise NotImplementedError

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        raise NotImplementedError

    def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        raise NotImplementedError


class InMemoryStorage(MemoryStorage):
    """In-memory implementation of memory storage."""

    def __init__(self):
        """Initialize in-memory storage."""
        self.data: Dict[str, MemoryEntry] = {}
        self.hash_map: Dict[str, str] = {}  # Maps content hashes to keys

    def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to in-memory storage."""
        # Update the hash before saving
        entry.update_hash()
        self.data[key] = entry

        # Update the hash map
        if entry.metadata.content_hash:
            self.hash_map[entry.metadata.content_hash] = key

        return True

    def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from in-memory storage."""
        if key not in self.data:
            return None

        entry = self.data[key]

        # Update access metadata
        entry.update_access()
        return entry

    def delete(self, key: str) -> bool:
        """Delete a memory entry from in-memory storage."""
        if key not in self.data:
            return False

        entry = self.data[key]

        # Remove from hash map if needed
        if entry.metadata.content_hash and entry.metadata.content_hash in self.hash_map:
            del self.hash_map[entry.metadata.content_hash]

        del self.data[key]
        return True

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        return [key for key in self.data.keys() if key.startswith(prefix)]

    def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        if content_hash not in self.hash_map:
            return None

        key = self.hash_map[content_hash]
        return self.get(key)


class SyncEvent(Enum):
    """Types of synchronization events."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    ACCESSED = "accessed"


@dataclass
class SyncOperation:
    """Represents a synchronization operation."""

    event_type: SyncEvent
    key: str
    entry: Optional[MemoryEntry] = None
    source_tool: Optional[ToolType] = None
    target_tools: List[ToolType] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class MemorySyncEngine:
    """Core memory synchronization engine."""

    def __init__(
        self,
        storage: MemoryStorage,
        tools: List[ToolType],
        token_budgets: Dict[ToolType, int],
    ):
        """Initialize the memory synchronization engine."""
        self.storage = storage
        self.tools = tools
        self.token_budget_manager = TokenBudgetManager(token_budgets)
        self.compression_engine = MemoryCompressionEngine()
        self.pending_operations: List[SyncOperation] = []
        self.tool_adapters: Dict[ToolType, Any] = {}  # Tool-specific adapters

    def register_tool_adapter(self, tool: ToolType, adapter: Any) -> None:
        """Register a tool-specific adapter."""
        self.tool_adapters[tool] = adapter

    def create_memory(
        self, key: str, entry: MemoryEntry, source_tool: ToolType
    ) -> bool:
        """Create a new memory entry - simplified for single-user project."""
        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()

        # Skip hash computation for performance in single-user context
        # entry.update_hash()

        # Save to storage
        success = self.storage.save(key, entry)

        if success:
            # Simplified logging without complex sync operations
            logger.info(f"Created memory: {key} from {source_tool}")

        return success

    def update_memory(
        self, key: str, entry: MemoryEntry, source_tool: ToolType
    ) -> bool:
        """Update an existing memory entry - simplified for single-user project."""
        # Get the existing entry
        existing = self.storage.get(key)

        if not existing:
            return self.create_memory(key, entry, source_tool)

        # Update entry metadata - simplified without conflict resolution
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.metadata.version = existing.metadata.version + 1

        # Save to storage
        success = self.storage.save(key, entry)

        if success:
            logger.info(f"Updated memory: {key} from {source_tool}")

        return success

    def get_memory(self, key: str, tool: ToolType) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool."""
        entry = self.storage.get(key)

        if not entry:
            return None

        # Create an access sync operation
        operation = SyncOperation(
            event_type=SyncEvent.ACCESSED,
            key=key,
            entry=entry,
            source_tool=tool,
            target_tools=[],  # Access events don't sync to other tools
        )
        self.pending_operations.append(operation)

        # Optimize for the tool's context window
        if tool != entry.metadata.source_tool:
            # Compress if necessary for the target tool
            if not self.token_budget_manager.can_fit_entry(entry, tool):
                # Try to compress
                compressed_entry = MemoryEntry(
                    memory_type=entry.memory_type,
                    scope=entry.scope,
                    priority=entry.priority,
                    compression_level=CompressionLevel.LIGHT,  # Start with light compression
                    ttl_seconds=entry.ttl_seconds,
                    content=entry.content,
                    metadata=entry.metadata,
                    storage_tier=entry.storage_tier,
                )

                compressed_entry = self.compression_engine.compress(compressed_entry)

                # If still doesn't fit, try higher compression
                if not self.token_budget_manager.can_fit_entry(compressed_entry, tool):
                    for level in [
                        CompressionLevel.MEDIUM,
                        CompressionLevel.HIGH,
                        CompressionLevel.EXTREME,
                        CompressionLevel.REFERENCE_ONLY,
                    ]:
                        compressed_entry.compression_level = level
                        compressed_entry = self.compression_engine.compress(
                            compressed_entry
                        )
                        if self.token_budget_manager.can_fit_entry(
                            compressed_entry, tool
                        ):
                            break

                return compressed_entry

        return entry

    def delete_memory(self, key: str, source_tool: ToolType) -> bool:
        """Delete a memory entry - simplified for single-user project."""
        # Get the existing entry before deletion
        existing = self.storage.get(key)

        if not existing:
            return False

        # Delete from storage - simplified without sync operations
        success = self.storage.delete(key)

        if success:
            logger.info(f"Deleted memory: {key} from {source_tool}")

        return success

    def _resolve_conflict(
        self,
        key: str,
        existing: MemoryEntry,
        new_entry: MemoryEntry,
        source_tool: ToolType,
    ) -> bool:
        """Resolve a conflict between two memory entries."""
        logger.warning(
            f"Conflict detected for key {key} between "
            f"{existing.metadata.source_tool} and {source_tool}"
        )

        # Simple resolution strategy: most recent wins
        if new_entry.metadata.last_modified > existing.metadata.last_modified:
            # New entry is newer, it wins
            new_entry.metadata.version = existing.metadata.version + 1
            return self.storage.save(key, new_entry)
        else:
            # Existing entry is newer, keep it
            return False

    def process_pending_operations(self) -> int:
        """Process all pending synchronization operations."""
        if not self.pending_operations:
            return 0

        count = 0
        remaining_operations = []

        for operation in self.pending_operations:
            if self._process_operation(operation):
                count += 1
            else:
                # Operation failed or partially completed, keep for next run
                remaining_operations.append(operation)

        self.pending_operations = remaining_operations
        return count

    def _process_operation(self, operation: SyncOperation) -> bool:
        """Process a single synchronization operation."""
        if operation.event_type == SyncEvent.ACCESSED:
            # Access events don't require syncing to other tools
            return True

        success = True

        for tool in operation.target_tools:
            if tool not in self.tool_adapters:
                logger.warning(f"No adapter registered for tool {tool}")
                success = False
                continue

            adapter = self.tool_adapters[tool]

            if operation.event_type == SyncEvent.CREATED and operation.entry:
                # Check if the entry can fit in this tool's context window
                if not self.token_budget_manager.can_fit_entry(operation.entry, tool):
                    # Compress the entry to fit
                    compressed_entry = self._compress_for_tool(operation.entry, tool)
                    if compressed_entry:
                        # Sync the compressed entry
                        if not adapter.sync_create(operation.key, compressed_entry):
                            success = False
                    else:
                        # Couldn't compress enough to fit
                        logger.warning(
                            f"Entry {operation.key} too large for {tool} even after compression"
                        )
                        success = False
                else:
                    # Sync the entry as-is
                    if not adapter.sync_create(operation.key, operation.entry):
                        success = False

            elif operation.event_type == SyncEvent.UPDATED and operation.entry:
                # Similar logic for updates
                if not self.token_budget_manager.can_fit_entry(operation.entry, tool):
                    compressed_entry = self._compress_for_tool(operation.entry, tool)
                    if compressed_entry:
                        if not adapter.sync_update(operation.key, compressed_entry):
                            success = False
                    else:
                        success = False
                else:
                    if not adapter.sync_update(operation.key, operation.entry):
                        success = False

            elif operation.event_type == SyncEvent.DELETED:
                # Sync deletion
                if not adapter.sync_delete(operation.key):
                    success = False

        return success

    def _compress_for_tool(
        self, entry: MemoryEntry, tool: ToolType
    ) -> Optional[MemoryEntry]:
        """Compress an entry to fit in a tool's context window."""
        for level in CompressionLevel:
            if level == CompressionLevel.NONE:
                continue

            compressed_entry = MemoryEntry(
                memory_type=entry.memory_type,
                scope=entry.scope,
                priority=entry.priority,
                compression_level=level,
                ttl_seconds=entry.ttl_seconds,
                content=entry.content,
                metadata=entry.metadata,
                storage_tier=entry.storage_tier,
            )

            compressed_entry = self.compression_engine.compress(compressed_entry)

            if self.token_budget_manager.can_fit_entry(compressed_entry, tool):
                return compressed_entry

        return None

    def optimize_context_window(
        self, tool: ToolType, required_keys: Optional[List[str]] = None
    ) -> int:
        """Optimize the context window for a specific tool."""
        # Get all active memory entries
        all_keys = self.storage.list_keys()
        entries = []

        for key in all_keys:
            entry = self.storage.get(key)
            if entry and not entry.is_expired():
                entries.append((key, entry))

        # Sort by priority and relevance
        entries.sort(
            key=lambda x: (x[1].priority, x[1].metadata.context_relevance), reverse=True
        )

        # Ensure required keys are at the top
        if required_keys:
            # Move required keys to the top
            required_entries = [(k, e) for k, e in entries if k in required_keys]
            other_entries = [(k, e) for k, e in entries if k not in required_keys]
            entries = required_entries + other_entries

        # Apply budget optimization
        optimized_entries = []
        current_budget = self.token_budget_manager.get_available_budget(tool)

        for key, entry in entries:
            tokens = self.token_budget_manager.estimate_tokens(entry)

            if tokens <= current_budget:
                # Entry fits as-is
                optimized_entries.append((key, entry))
                current_budget -= tokens
            else:
                # Try to compress
                compressed_entry = self._compress_for_tool(entry, tool)
                if compressed_entry:
                    compressed_tokens = self.token_budget_manager.estimate_tokens(
                        compressed_entry
                    )
                    if compressed_tokens <= current_budget:
                        optimized_entries.append((key, compressed_entry))
                        current_budget -= compressed_tokens

        return len(optimized_entries)

    def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system."""
        all_keys = self.storage.list_keys()
        entry_count = len(all_keys)

        # Count entries by tool, scope, and type
        tool_counts = {}
        scope_counts = {}
        type_counts = {}
        compression_counts = {}

        for key in all_keys:
            entry = self.storage.get(key)
            if not entry:
                continue

            tool = entry.metadata.source_tool
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

            scope = entry.scope
            scope_counts[scope] = scope_counts.get(scope, 0) + 1

            mem_type = entry.memory_type
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

            compression = entry.compression_level
            compression_counts[compression] = compression_counts.get(compression, 0) + 1

        # Get token usage by tool
        token_usage = {
            tool: self.token_budget_manager.current_usage.get(tool, 0)
            for tool in self.tools
        }

        return {
            "entry_count": entry_count,
            "tool_counts": tool_counts,
            "scope_counts": scope_counts,
            "type_counts": type_counts,
            "compression_counts": compression_counts,
            "token_usage": token_usage,
            "pending_operations": len(self.pending_operations),
        }
