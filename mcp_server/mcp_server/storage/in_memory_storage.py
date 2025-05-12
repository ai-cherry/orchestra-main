#!/usr/bin/env python3
"""
in_memory_storage.py - Optimized In-Memory Storage Implementation

This module implements the IMemoryStorage interface with an in-memory storage backend.
It's efficient for development and testing but does not persist data between restarts.
This implementation includes performance optimizations like background cleanup,
efficient indexing, and proper async patterns.
"""

import logging
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import heapq
from datetime import datetime, timedelta

from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry, MemoryType, MemoryScope

logger = logging.getLogger(__name__)

class InMemoryStorage(IMemoryStorage):
    """Optimized in-memory implementation of memory storage."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize in-memory storage with optimized data structures."""
        self.config = config or {}
        self.data: Dict[str, MemoryEntry] = {}
        self.hash_map: Dict[str, str] = {}  # Maps content hashes to keys
        
        # Performance optimizations
        self.expiry_heap: List[Tuple[float, str]] = []  # Min heap of (expiry_time, key)
        self.type_index: Dict[MemoryType, Set[str]] = defaultdict(set)  # Index by memory type
        self.scope_index: Dict[MemoryScope, Set[str]] = defaultdict(set)  # Index by scope
        self.text_index: Dict[str, Set[str]] = defaultdict(set)  # Simple text-based index
        
        # Cache settings
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes default
        self.cache_size = self.config.get("cache_size", 1000)  # Max entries in cache
        self.cleanup_interval = self.config.get("cleanup_interval", 60)  # Seconds
        
        self.initialized = False
        self.cleanup_task = None
    
    async def initialize(self) -> bool:
        """Initialize the storage backend with background cleanup task."""
        logger.info("Initializing optimized in-memory storage")
        self.initialized = True
        
        # Start background cleanup task
        self.cleanup_task = asyncio.create_task(self._background_cleanup())
        logger.info("Started background cleanup task")
        
        return True
    
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to in-memory storage with indexing."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return False
        
        # Remove old indexes if entry exists
        if key in self.data:
            await self._remove_from_indexes(key, self.data[key])
        
        # Update the hash before saving
        entry.update_hash()
        self.data[key] = entry
        
        # Update the hash map
        if entry.metadata.content_hash:
            self.hash_map[entry.metadata.content_hash] = key
        
        # Update indexes
        await self._add_to_indexes(key, entry)
        
        # Add to expiry heap if TTL is set
        expiry_time = time.time() + entry.ttl_seconds
        heapq.heappush(self.expiry_heap, (expiry_time, key))
        
        logger.debug(f"Saved memory entry: {key}")
        return True
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from in-memory storage with optimized expiry check."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return None
        
        if key not in self.data:
            logger.debug(f"Memory entry not found: {key}")
            return None
        
        entry = self.data[key]
        
        # Check if the entry has expired - this is now a quick check
        # since background cleanup should handle most expired entries
        if entry.is_expired():
            logger.debug(f"Memory entry expired: {key}")
            await self.delete(key)
            return None
        
        # Update access metadata
        entry.update_access()
        logger.debug(f"Retrieved memory entry: {key}")
        return entry
    
    async def delete(self, key: str) -> bool:
        """Delete a memory entry from in-memory storage and update indexes."""
        if not self.initialized:
            logger.error("Storage not initialized")
            return False
        
        if key not in self.data:
            logger.debug(f"Memory entry not found for deletion: {key}")
            return False
        
        entry = self.data[key]
        
        # Remove from indexes
        await self._remove_from_indexes(key, entry)
        
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
        """Search for memory entries matching the query with optimized text search.
        
        This implementation uses pre-built indexes for faster searching.
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return []
        
        # Tokenize the query for better matching
        query_tokens = self._tokenize_text(query.lower())
        
        # Use the text index for faster retrieval
        candidate_keys = set()
        for token in query_tokens:
            if token in self.text_index:
                candidate_keys.update(self.text_index[token])
        
        results = []
        for key in candidate_keys:
            if key not in self.data:
                continue
                
            entry = self.data[key]
            
            # Skip expired entries
            if entry.is_expired():
                continue
            
            # Calculate relevance score based on token matching
            score = self._calculate_relevance(entry, query_tokens)
            if score > 0:
                results.append((key, entry, score))
        
        # Sort by score (descending) and limit results
        results.sort(key=lambda x: x[2], reverse=True)
        limited_results = results[:limit]
        
        logger.debug(f"Optimized search for '{query}' found {len(limited_results)} results")
        return limited_results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend with detailed metrics."""
        status = "healthy" if self.initialized else "not_initialized"
        
        # Count expired entries
        expired_count = 0
        for entry in self.data.values():
            if entry.is_expired():
                expired_count += 1
        
        # Calculate memory usage (approximate)
        import sys
        memory_usage = sys.getsizeof(self.data) + sys.getsizeof(self.hash_map)
        memory_usage += sys.getsizeof(self.expiry_heap)
        memory_usage += sum(sys.getsizeof(idx) for idx in self.type_index.values())
        memory_usage += sum(sys.getsizeof(idx) for idx in self.scope_index.values())
        memory_usage += sum(sys.getsizeof(idx) for idx in self.text_index.values())
        
        # Get index statistics
        type_index_stats = {str(t): len(keys) for t, keys in self.type_index.items()}
        scope_index_stats = {str(s): len(keys) for s, keys in self.scope_index.items()}
        
        return {
            "status": status,
            "entries": len(self.data),
            "hashes": len(self.hash_map),
            "expired_entries": expired_count,
            "memory_usage_bytes": memory_usage,
            "type_index_stats": type_index_stats,
            "scope_index_stats": scope_index_stats,
            "text_index_size": len(self.text_index),
            "cleanup_task_running": self.cleanup_task is not None and not self.cleanup_task.done()
        }
    
    # Helper methods for optimized implementation
    
    async def _background_cleanup(self) -> None:
        """Background task to clean up expired entries."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self.initialized:
                    continue
                
                cleanup_start = time.time()
                cleaned_count = 0
                
                # Process the expiry heap
                current_time = time.time()
                while self.expiry_heap and self.expiry_heap[0][0] <= current_time:
                    expiry_time, key = heapq.heappop(self.expiry_heap)
                    
                    # Check if the key exists and is actually expired
                    if key in self.data and self.data[key].is_expired():
                        await self.delete(key)
                        cleaned_count += 1
                    
                    # Avoid spending too much time in cleanup
                    if time.time() - cleanup_start > 1.0:  # Max 1 second per cleanup
                        break
                
                if cleaned_count > 0:
                    logger.info(f"Background cleanup removed {cleaned_count} expired entries")
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in background cleanup task: {e}")
    
    async def _add_to_indexes(self, key: str, entry: MemoryEntry) -> None:
        """Add an entry to all indexes for faster retrieval."""
        # Add to type and scope indexes
        self.type_index[entry.memory_type].add(key)
        self.scope_index[entry.scope].add(key)
        
        # Add to text index for faster searching
        if isinstance(entry.content, str):
            tokens = self._tokenize_text(entry.content.lower())
            for token in tokens:
                self.text_index[token].add(key)
        elif isinstance(entry.content, dict):
            content_str = json.dumps(entry.content).lower()
            tokens = self._tokenize_text(content_str)
            for token in tokens:
                self.text_index[token].add(key)
    
    async def _remove_from_indexes(self, key: str, entry: MemoryEntry) -> None:
        """Remove an entry from all indexes."""
        # Remove from type and scope indexes
        if entry.memory_type in self.type_index:
            self.type_index[entry.memory_type].discard(key)
        if entry.scope in self.scope_index:
            self.scope_index[entry.scope].discard(key)
        
        # Remove from text index
        if isinstance(entry.content, str):
            tokens = self._tokenize_text(entry.content.lower())
            for token in tokens:
                if token in self.text_index:
                    self.text_index[token].discard(key)
        elif isinstance(entry.content, dict):
            content_str = json.dumps(entry.content).lower()
            tokens = self._tokenize_text(content_str)
            for token in tokens:
                if token in self.text_index:
                    self.text_index[token].discard(key)
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words for indexing and searching."""
        import re
        # Split on non-alphanumeric characters and filter out empty strings
        return [token for token in re.split(r'\W+', text) if token]
    
    def _calculate_relevance(self, entry: MemoryEntry, query_tokens: List[str]) -> float:
        """Calculate relevance score based on token matching."""
        if isinstance(entry.content, str):
            content_tokens = self._tokenize_text(entry.content.lower())
        elif isinstance(entry.content, dict):
            content_str = json.dumps(entry.content).lower()
            content_tokens = self._tokenize_text(content_str)
        else:
            return 0.0
        
        # Count matching tokens
        matching_tokens = set(query_tokens).intersection(set(content_tokens))
        
        if not matching_tokens:
            return 0.0
        
        # Calculate TF-IDF inspired score
        score = len(matching_tokens) / len(query_tokens)
        
        # Boost by priority and context relevance
        score *= (1.0 + 0.1 * entry.priority)
        score *= (1.0 + entry.metadata.context_relevance)
        
        return score
