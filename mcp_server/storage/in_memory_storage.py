#!/usr/bin/env python3
"""
in_memory_storage.py - In-Memory Storage Implementation

This module implements the IMemoryStorage interface with an in-memory storage backend.
It's efficient for development and testing but does not persist data between restarts.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
import asyncio

from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry

logger = logging.getLogger(__name__)

class InMemoryStorage(IMemoryStorage):
    """In-memory implementation of memory storage."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize in-memory storage."""
        self.config = config or {}
        self.data: Dict[str, MemoryEntry] = {}
        self.hash_map: Dict[str, str] = {}  # Maps content hashes to keys
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the storage backend."""
        logger.info("Initializing in-memory storage")
        self.initialized = True
        return True
    
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to in-memory storage."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return False
        
        # Update the hash before saving
        entry.update_hash()
        self.data[key] = entry
        
        # Update the hash map
        if entry.metadata.content_hash:
            self.hash_map[entry.metadata.content_hash] = key
        
        logger.debug(f"Saved memory entry: {key}")
        return True
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from in-memory storage."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return None
        
        if key not in self.data:
            logger.debug(f"Memory entry not found: {key}")
            return None
        
        entry = self.data[key]
        
        # Check if the entry has expired
        if entry.is_expired():
            logger.debug(f"Memory entry expired: {key}")
            await self.delete(key)
            return None
        
        # Update access metadata
        entry.update_access()
        logger.debug(f"Retrieved memory entry: {key}")
        return entry
    
    async def delete(self, key: str) -> bool:
        """Delete a memory entry from in-memory storage."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return False
        
        if key not in self.data:
            logger.debug(f"Memory entry not found for deletion: {key}")
            return False
        
        entry = self.data[key]
        
        # Remove from hash map if needed
        if entry.metadata.content_hash and entry.metadata.content_hash in self.hash_map:
            del self.hash_map[entry.metadata.content_hash]
        
        del self.data[key]
        logger.debug(f"Deleted memory entry: {key}")
        return True
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return []
        
        filtered_keys = [key for key in self.data.keys() if key.startswith(prefix)]
        logger.debug(f"Listed {len(filtered_keys)} keys with prefix '{prefix}'")
        return filtered_keys
    
    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return None
        
        if content_hash not in self.hash_map:
            logger.debug(f"Memory entry not found for hash: {content_hash}")
            return None
        
        key = self.hash_map[content_hash]
        return await self.get(key)
    
    async def search(self, query: str, limit: int = 10) -> List[Tuple[str, MemoryEntry, float]]:
        """Search for memory entries matching the query.
        
        This is a basic implementation that does simple text matching.
        In a real implementation, this would use vector similarity search.
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return []
        
        results = []
        query = query.lower()
        
        for key, entry in self.data.items():
            # Skip expired entries
            if entry.is_expired():
                continue
            
            # Simple text matching for now
            if isinstance(entry.content, str):
                content_str = entry.content.lower()
                if query in content_str:
                    # Calculate a simple relevance score based on frequency of the query
                    score = content_str.count(query) / len(content_str)
                    results.append((key, entry, score))
            elif isinstance(entry.content, dict):
                # For dictionaries, convert to string and search
                content_str = json.dumps(entry.content).lower()
                if query in content_str:
                    score = content_str.count(query) / len(content_str)
                    results.append((key, entry, score))
        
        # Sort by score (descending) and limit results
        results.sort(key=lambda x: x[2], reverse=True)
        limited_results = results[:limit]
        
        logger.debug(f"Search for '{query}' found {len(limited_results)} results")
        return limited_results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend."""
        status = "healthy" if self.initialized else "not_initialized"
        
        # Count expired entries
        expired_count = 0
        for entry in self.data.values():
            if entry.is_expired():
                expired_count += 1
        
        return {
            "status": status,
            "entries": len(self.data),
            "hashes": len(self.hash_map),
            "expired_entries": expired_count
        }
