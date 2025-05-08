# MCP Memory Implementation Plan

Based on the review of the MCP memory structure, this implementation plan outlines specific changes needed to address the identified inconsistencies, redundancies, and conflicts. The plan is organized into phases, with each phase building on the previous one to create a more consistent, maintainable memory architecture.

## Phase 1: Core Interfaces and Models

### 1.1 Unified Storage Interface

Create a standardized storage interface that all implementations must follow:

```python
# mcp_server/interfaces/storage.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from ..models.memory import MemoryEntry

class IMemoryStorage(ABC):
    """Base interface for all memory storage implementations."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        pass
    
    @abstractmethod
    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend."""
        pass
```

### 1.2 Standardized Memory Models

Define consistent model classes for memory entries and metadata:

```python
# mcp_server/models/memory.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import time
import json
import hashlib

class MemoryType(str, Enum):
    """Memory type classification."""
    SHARED = "shared"
    TOOL_SPECIFIC = "tool_specific"

class MemoryScope(str, Enum):
    """Memory scope classification."""
    SESSION = "session"
    GLOBAL = "global"

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
    HOT = "hot"      # Real-time layer (Redis)
    WARM = "warm"    # Recent but not critical (Redis with longer TTL)
    COLD = "cold"    # Historical content (AlloyDB/PostgreSQL)

@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""
    source_tool: str
    last_modified: float
    access_count: int = 0
    context_relevance: float = 0.5
    last_accessed: float = field(default_factory=time.time)
    version: int = 1
    sync_status: Dict[str, int] = field(default_factory=dict)
    content_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "source_tool": self.source_tool,
            "last_modified": self.last_modified,
            "access_count": self.access_count,
            "context_relevance": self.context_relevance,
            "last_accessed": self.last_accessed,
            "version": self.version,
            "sync_status": self.sync_status,
            "content_hash": self.content_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryMetadata':
        """Create metadata from dictionary."""
        return cls(
            source_tool=data["source_tool"],
            last_modified=data["last_modified"],
            access_count=data.get("access_count", 0),
            context_relevance=data.get("context_relevance", 0.5),
            last_accessed=data.get("last_accessed", time.time()),
            version=data.get("version", 1),
            sync_status=data.get("sync_status", {}),
            content_hash=data.get("content_hash")
        )

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
            "metadata": self.metadata.to_dict(),
            "storage_tier": self.storage_tier
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create a memory entry from a dictionary."""
        metadata = MemoryMetadata.from_dict(data["metadata"])
        
        return cls(
            memory_type=data["memory_type"],
            scope=data["scope"],
            priority=data["priority"],
            compression_level=data["compression_level"],
            ttl_seconds=data["ttl_seconds"],
            content=data["content"],
            metadata=metadata,
            storage_tier=data.get("storage_tier", StorageTier.HOT)
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
```

### 1.3 Tool Adapter Interface

Create a standardized interface for tool adapters:

```python
# mcp_server/interfaces/tool_adapter.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..models.memory import MemoryEntry

class IToolAdapter(ABC):
    """Interface for tool-specific adapters."""
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Get the name of the tool."""
        pass
    
    @property
    @abstractmethod
    def context_window_size(self) -> int:
        """Get the context window size for this tool."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the tool adapter."""
        pass
    
    @abstractmethod
    async def sync_create(self, key: str, entry: MemoryEntry) -> bool:
        """Sync a newly created memory entry to the tool."""
        pass
    
    @abstractmethod
    async def sync_update(self, key: str, entry: MemoryEntry) -> bool:
        """Sync an updated memory entry to the tool."""
        pass
    
    @abstractmethod
    async def sync_delete(self, key: str) -> bool:
        """Sync a deleted memory entry to the tool."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the tool adapter."""
        pass
```

## Phase 2: Storage Implementations

### 2.1 In-Memory Storage Implementation

Implement the in-memory storage interface:

```python
# mcp_server/storage/in_memory_storage.py

from typing import Dict, List, Optional, Any
from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry

class InMemoryStorage(IMemoryStorage):
    """In-memory implementation of memory storage."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize in-memory storage."""
        self.config = config or {}
        self.data: Dict[str, MemoryEntry] = {}
        self.hash_map: Dict[str, str] = {}  # Maps content hashes to keys
    
    async def initialize(self) -> bool:
        """Initialize the storage backend."""
        return True
    
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to in-memory storage."""
        # Update the hash before saving
        entry.update_hash()
        self.data[key] = entry
        
        # Update the hash map
        if entry.metadata.content_hash:
            self.hash_map[entry.metadata.content_hash] = key
        
        return True
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from in-memory storage."""
        if key not in self.data:
            return None
        
        entry = self.data[key]
        
        # Update access metadata
        entry.update_access()
        return entry
    
    async def delete(self, key: str) -> bool:
        """Delete a memory entry from in-memory storage."""
        if key not in self.data:
            return False
        
        entry = self.data[key]
        
        # Remove from hash map if needed
        if entry.metadata.content_hash and entry.metadata.content_hash in self.hash_map:
            del self.hash_map[entry.metadata.content_hash]
        
        del self.data[key]
        return True
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        return [key for key in self.data.keys() if key.startswith(prefix)]
    
    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        if content_hash not in self.hash_map:
            return None
        
        key = self.hash_map[content_hash]
        return await self.get(key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend."""
        return {
            "status": "healthy",
            "entries": len(self.data),
            "hashes": len(self.hash_map)
        }
```

### 2.2 File-Based Storage Implementation

Implement the file-based storage interface:

```python
# mcp_server/storage/file_storage.py

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry, MemoryMetadata

class FileStorage(IMemoryStorage):
    """File-based implementation of memory storage."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize file storage."""
        self.config = config
        self.storage_path = Path(config.get("storage_path", "./.mcp_memory"))
        self.cache_enabled = config.get("enable_cache", True)
        self.memory_cache = {} if self.cache_enabled else None
    
    async def initialize(self) -> bool:
        """Initialize the storage backend."""
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(exist_ok=True, parents=True)
        
        # Load existing memory items if caching is enabled
        if self.cache_enabled:
            try:
                memory_files = list(self.storage_path.glob("*.json"))
                for memory_file in memory_files:
                    try:
                        with open(memory_file, "r") as f:
                            data = json.load(f)
                            
                            # Check if the memory item has expired
                            if "expiry" in data:
                                expiry_time = datetime.fromisoformat(data["expiry"])
                                if expiry_time < datetime.now():
                                    # Memory item has expired, delete it
                                    memory_file.unlink()
                                    continue
                            
                            # Add memory item to cache
                            key = memory_file.stem
                            entry = MemoryEntry.from_dict(data["entry"])
                            self.memory_cache[key] = entry
                    except Exception as e:
                        print(f"Error loading memory file {memory_file}: {e}")
            except Exception as e:
                print(f"Error loading memory: {e}")
                return False
        
        return True
    
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to file storage."""
        # Update the hash
        entry.update_hash()
        
        # Add to cache if enabled
        if self.cache_enabled:
            self.memory_cache[key] = entry
        
        # Calculate expiry time
        expiry_time = datetime.now() + timedelta(seconds=entry.ttl_seconds)
        
        # Prepare data for storage
        data = {
            "entry": entry.to_dict(),
            "expiry": expiry_time.isoformat()
        }
        
        # Write to file
        file_path = self.storage_path / f"{key}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error writing memory file {file_path}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from file storage."""
        # Check cache first if enabled
        if self.cache_enabled and key in self.memory_cache:
            entry = self.memory_cache[key]
            entry.update_access()
            return entry
        
        # Check file system
        file_path = self.storage_path / f"{key}.json"
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                
                # Check if expired
                if "expiry" in data:
                    expiry_time = datetime.fromisoformat(data["expiry"])
                    if expiry_time < datetime.now():
                        # Memory item has expired, delete it
                        file_path.unlink()
                        return None
                
                # Create memory entry
                entry = MemoryEntry.from_dict(data["entry"])
                
                # Update access metadata
                entry.update_access()
                
                # Cache if enabled
                if self.cache_enabled:
                    self.memory_cache[key] = entry
                
                return entry
        except Exception as e:
            print(f"Error reading memory file {file_path}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a memory entry from file storage."""
        # Remove from cache if enabled
        if self.cache_enabled and key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from file system
        file_path = self.storage_path / f"{key}.json"
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                print(f"Error deleting memory file {file_path}: {e}")
                return False
        
        return True
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        # If cache is enabled, use it for faster listing
        if self.cache_enabled:
            return [key for key in self.memory_cache.keys() if key.startswith(prefix)]
        
        # Otherwise scan the directory
        try:
            files = list(self.storage_path.glob("*.json"))
            keys = [f.stem for f in files]
            return [key for key in keys if key.startswith(prefix)]
        except Exception as e:
            print(f"Error listing keys: {e}")
            return []
    
    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        # If cache is enabled, scan it for the hash
        if self.cache_enabled:
            for key, entry in self.memory_cache.items():
                if entry.metadata.content_hash == content_hash:
                    return entry
        
        # Otherwise scan all files
        try:
            files = list(self.storage_path.glob("*.json"))
            for file_path in files:
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        entry = MemoryEntry.from_dict(data["entry"])
                        if entry.metadata.content_hash == content_hash:
                            return entry
                except Exception:
                    continue
        except Exception as e:
            print(f"Error searching by hash: {e}")
        
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend."""
        try:
            files = list(self.storage_path.glob("*.json"))
            return {
                "status": "healthy",
                "files": len(files),
                "cache_enabled": self.cache_enabled,
                "cached_entries": len(self.memory_cache) if self.cache_enabled else 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
```

## Phase 3: Memory Manager Implementation

### 3.1 Memory Manager Interface

```python
# mcp_server/interfaces/memory_manager.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from ..models.memory import MemoryEntry

class IMemoryManager(ABC):
    """Interface for memory managers."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the memory manager."""
        pass
    
    @abstractmethod
    async def create_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Create a new memory entry."""
        pass
    
    @abstractmethod
    async def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool."""
        pass
    
    @abstractmethod
    async def update_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Update an existing memory entry."""
        pass
    
    @abstractmethod
    async def delete_memory(self, key: str, source_tool: str) -> bool:
        """Delete a memory entry."""
        pass
    
    @abstractmethod
    async def optimize_context_window(self, tool: str, required_keys: Optional[List[str]] = None) -> int:
        """Optimize the context window for a specific tool."""
        pass
    
    @abstractmethod
    async def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system."""
        pass
```

### 3.2 Standard Memory Manager Implementation

```python
# mcp_server/managers/standard_memory_manager.py

from typing import Dict, List, Optional, Any, Union
from ..interfaces.memory_manager import IMemoryManager
from ..interfaces.storage import IMemoryStorage
from ..interfaces.tool_adapter import IToolAdapter
from ..models.memory import MemoryEntry, MemoryType, MemoryScope, CompressionLevel, StorageTier
import time

class StandardMemoryManager(IMemoryManager):
    """Standard implementation of memory manager."""
    
    def __init__(self, storage: IMemoryStorage, config: Dict[str, Any] = None):
        """Initialize the standard memory manager."""
        self.storage = storage
        self.config = config or {}
        self.tools: Dict[str, IToolAdapter] = {}
        self.token_budget_per_tool: Dict[str, int] = {}
    
    async def initialize(self) -> bool:
        """Initialize the memory manager."""
        # Initialize storage
        success = await self.storage.initialize()
        if not success:
            return False
        
        # Initialize tools
        for tool_name, adapter in self.tools.items():
            await adapter.initialize()
        
        return True
    
    def register_tool(self, tool: IToolAdapter, token_budget: int) -> None:
        """Register a tool with the memory manager."""
        self.tools[tool.tool_name] = tool
        self.token_budget_per_tool[tool.tool_name] = token_budget
    
    async def create_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Create a new memory entry."""
        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.update_hash()
        
        # Save to storage
        success = await self.storage.save(key, entry)
        
        if success and source_tool in self.tools:
            # For each registered tool, sync the memory
            for tool_name, adapter in self.tools.items():
                if tool_name != source_tool:
                    # Compress if necessary for the target tool
                    compressed_entry = self._compress_for_tool(entry, tool_name)
                    await adapter.sync_create(key, compressed_entry or entry)
        
        return success
    
    async def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry for a specific tool."""
        entry = await self.storage.get(key)
        
        if not entry:
            return None
        
        # If the tool is different from the source, compress if needed
        if tool != entry.metadata.source_tool and tool in self.token_budget_per_tool:
            # Check if the entry would fit in the tool's context window
            token_estimate = self._estimate_tokens(entry)
            available_budget = self.token_budget_per_tool[tool]
            
            if token_estimate > available_budget:
                # Try to compress
                compressed_entry = self._compress_for_tool(entry, tool)
                if compressed_entry:
                    return compressed_entry
        
        return entry
    
    async def update_memory(self, key: str, entry: MemoryEntry, source_tool: str) -> bool:
        """Update an existing memory entry."""
        # Get the existing entry
        existing = await self.storage.get(key)
        
        if not existing:
            return await self.create_memory(key, entry, source_tool)
        
        # Update entry metadata
        entry.metadata.source_tool = source_tool
        entry.metadata.last_modified = time.time()
        entry.metadata.version = existing.metadata.version + 1
        entry.update_hash()
        
        # Save to storage
        success = await self.storage.save(key, entry)
        
        if success and source_tool in self.tools:
            # For each registered tool, sync the memory
            for tool_name, adapter in self.tools.items():
                if tool_name != source_tool:
                    # Compress if necessary for the target tool
                    compressed_entry = self._compress_for_tool(entry, tool_name)
                    await adapter.sync_update(key, compressed_entry or entry)
        
        return success
    
    async def delete_memory(self, key: str, source_tool: str) -> bool:
        """Delete a memory entry."""
        # Get the existing entry before deletion
        existing = await self.storage.get(key)
        
        if not existing:
            return False
        
        # Delete from storage
        success = await self.storage.delete(key)
        
        if success and source_tool in self.tools:
            # For each registered tool, sync the deletion
            for tool_name, adapter in self.tools.items():
                if tool_name != source_tool:
                    await adapter.sync_delete(key)
        
        return success
    
    async def optimize_context_window(self, tool: str, required_keys: Optional[List[str]] = None) -> int:
        """Optimize the context window for a specific tool."""
        if tool not in self.token_budget_per_tool:
            return 0
        
        # Get available budget
        available_budget = self.token_budget_per_tool[tool]
        
        # Get all keys
        all_keys = await self.storage.list_keys()
        entries = []
        
        # Get entries for required keys first
        if required_keys:
            for key in required_keys:
                if key in all_keys:
                    entry = await self.storage.get(key)
                    if entry and not entry.is_expired():
                        entries.append((key, entry))
                        available_budget -= self._estimate_tokens(entry)
        
        # Get other entries within budget
        other_keys = [k for k in all_keys if required_keys is None or k not in required_keys]
        
        # Sort by priority and relevance
        other_entries = []
        for key in other_keys:
            entry = await self.storage.get(key)
            if entry and not entry.is_expired():
                other_entries.append((key, entry))
        
        other_entries.sort(key=lambda x: (x[1].priority, x[1].metadata.context_relevance), reverse=True)
        
        # Add entries until budget is exhausted
        optimized_entries = entries
        
        for key, entry in other_entries:
            token_estimate = self._estimate_tokens(entry)
            
            if token_estimate <= available_budget:
                # Entry fits as-is
                optimized_entries.append((key, entry))
                available_budget -= token_estimate
            else:
                # Try to compress
                compressed_entry = self._compress_for_tool(entry, tool)
                if compressed_entry:
                    compressed_tokens = self._estimate_tokens(compressed_entry)
                    if compressed_tokens <= available_budget:
                        optimized_entries.append((key, compressed_entry))
                        available_budget -= compressed_tokens
        
        return len(optimized_entries)
    
    async def get_memory_status(self) -> Dict[str, Any]:
        """Get the status of the memory system."""
        all_keys = await self.storage.list_keys()
        entry_count = len(all_keys)
        
        # Count entries by tool, scope, and type
        tool_counts = {}
        scope_counts = {}
        type_counts = {}
        compression_counts = {}
        
        for key in all_keys:
            entry = await self.storage.get(key)
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
        
        # Get storage health
        storage_health = await self.storage.health_check()
        
        # Get tool status
        tool_status = {}
        for tool_name, adapter in self.tools.items():
            tool_status[tool_name] = await adapter.get_status()
        
        return {
            "entry_count": entry_count,
            "tool_counts": tool_counts,
            "scope_counts": scope_counts,
            "type_counts": type_counts,
            "compression_counts": compression_counts,
            "storage": storage_health,
            "tools": tool_status
        }
    
    def _estimate_tokens(self, entry: MemoryEntry) -> int:
        """Estimate the number of tokens for a memory entry."""
        # Simple estimation based on string length
        # In a real implementation, this would use a tokenizer
        import json
        content_str = json.dumps(entry.content)
        # Rough approximation: 4 characters per token
        return len(content_str) // 4
    
    def _compress_for_tool(self, entry: MemoryEntry, tool: str) -> Optional[MemoryEntry]:
        """Compress an entry to fit in a tool's context window."""
        if tool not in self.token_budget_per_tool:
            return None
        
        available_budget = self.token_budget_per_tool[tool]
        
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
                storage_tier=entry.storage_tier
            )
            
            # Apply compression based on level
            compressed_entry = self._apply_compression(compressed_entry)
            
            # Check if it fits
            token_estimate = self._estimate_tokens(compressed_entry)
            if token_estimate <= available_budget:
                return compressed_entry
        
        return None
    
    def _apply_compression(self, entry: MemoryEntry) -> MemoryEntry:
        """Apply compression to a memory entry based on its compression level."""
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
                    sentences = entry.content.split('. ')
                    if len(sentences) > 5:
                        important_sentences = sentences[:2] + ["..."] + sentences[-2:]
                        compressed_entry.content = '. '.join(important_sentences)
            
            elif entry.compression_level == CompressionLevel.HIGH:
                # High compression: keep only first and last paragraph
                if len(entry.content) > 300:
                    paragraphs = entry.content.split('\n\n')
                    if len(paragraphs) > 2:
                        compressed_entry.content = paragraphs[0] + "\n\n...
