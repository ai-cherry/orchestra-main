"""
Advanced Memory Management System for Cherry-AI Production
High-performance memory architecture with intelligent caching and optimization
"""

import asyncio
import redis.asyncio as redis
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import numpy as np
from collections import defaultdict, OrderedDict
import logging
import pickle
import zlib
from enum import Enum
import uuid

class MemoryTier(Enum):
    """Memory storage tiers for performance optimization"""
    HOT = "hot"          # In-memory cache (Redis)
    WARM = "warm"        # SSD storage (PostgreSQL)
    COLD = "cold"        # Archive storage (S3/Object storage)

class CompressionType(Enum):
    """Memory compression algorithms"""
    NONE = "none"
    ZLIB = "zlib"
    GZIP = "gzip"
    LZ4 = "lz4"

@dataclass
class MemoryConfig:
    """Memory system configuration"""
    # Cache configuration
    redis_url: str = "redis://cache.cherry-ai.com:6379"
    max_memory_mb: int = 2048
    eviction_policy: str = "allkeys-lru"
    
    # Performance settings
    batch_size: int = 100
    compression_threshold: int = 1024  # bytes
    default_compression: CompressionType = CompressionType.ZLIB
    
    # Retention policies
    hot_retention_hours: int = 24
    warm_retention_days: int = 90
    cold_retention_years: int = 7
    
    # Vector search settings
    embedding_dimension: int = 1536
    similarity_threshold: float = 0.8
    max_search_results: int = 50

@dataclass
class MemoryItem:
    """Individual memory item with metadata"""
    id: str
    content: str
    persona_id: str
    memory_type: str
    privacy_level: int
    
    # Performance metadata
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    size_bytes: int = 0
    compression_type: CompressionType = CompressionType.NONE
    
    # Semantic metadata
    importance_score: float = 0.5
    emotional_valence: float = 0.0
    confidence_score: float = 1.0
    keywords: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    
    # Relationships
    related_memory_ids: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.size_bytes == 0:
            self.size_bytes = len(self.content.encode('utf-8'))

class MemoryCache:
    """High-performance Redis-based memory cache"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logging.getLogger(__name__)
        
        # Local LRU cache for frequently accessed items
        self.local_cache: OrderedDict = OrderedDict()
        self.local_cache_size = 1000
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.compression_savings = 0
    
    async def initialize(self) -> None:
        """Initialize Redis connection and configure memory policies"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Handle binary data
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Configure Redis memory policies
            await self.redis_client.config_set("maxmemory", f"{self.config.max_memory_mb}mb")
            await self.redis_client.config_set("maxmemory-policy", self.config.eviction_policy)
            
            # Test connection
            await self.redis_client.ping()
            self.logger.info("Memory cache initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Memory cache initialization failed: {e}")
            raise
    
    def _compress_data(self, data: bytes) -> Tuple[bytes, CompressionType]:
        """Compress data if it exceeds threshold"""
        if len(data) < self.config.compression_threshold:
            return data, CompressionType.NONE
        
        if self.config.default_compression == CompressionType.ZLIB:
            compressed = zlib.compress(data)
            self.compression_savings += len(data) - len(compressed)
            return compressed, CompressionType.ZLIB
        
        return data, CompressionType.NONE
    
    def _decompress_data(self, data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data based on compression type"""
        if compression_type == CompressionType.ZLIB:
            return zlib.decompress(data)
        return data
    
    async def store(self, memory_item: MemoryItem, ttl_seconds: Optional[int] = None) -> bool:
        """Store memory item in cache with optional TTL"""
        try:
            # Serialize memory item
            serialized = pickle.dumps(memory_item)
            compressed_data, compression_type = self._compress_data(serialized)
            
            # Store in Redis with metadata
            key = f"memory:{memory_item.id}"
            metadata_key = f"meta:{memory_item.id}"
            
            # Store compressed data
            await self.redis_client.set(key, compressed_data, ex=ttl_seconds)
            
            # Store metadata separately for quick access
            metadata = {
                "persona_id": memory_item.persona_id,
                "memory_type": memory_item.memory_type,
                "privacy_level": memory_item.privacy_level,
                "importance_score": memory_item.importance_score,
                "size_bytes": len(compressed_data),
                "compression_type": compression_type.value,
                "created_at": memory_item.created_at.isoformat(),
                "last_accessed": memory_item.last_accessed.isoformat()
            }
            
            await self.redis_client.hset(metadata_key, mapping=metadata)
            
            # Update local cache
            self._update_local_cache(memory_item.id, memory_item)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store memory {memory_item.id}: {e}")
            return False
    
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve memory item from cache"""
        # Check local cache first
        if memory_id in self.local_cache:
            self.cache_hits += 1
            self._update_local_cache(memory_id, self.local_cache[memory_id])
            return self.local_cache[memory_id]
        
        try:
            # Get from Redis
            key = f"memory:{memory_id}"
            metadata_key = f"meta:{memory_id}"
            
            data = await self.redis_client.get(key)
            if not data:
                self.cache_misses += 1
                return None
            
            # Get metadata for decompression
            metadata = await self.redis_client.hgetall(metadata_key)
            if not metadata:
                self.cache_misses += 1
                return None
            
            # Decompress and deserialize
            compression_type = CompressionType(metadata.get(b'compression_type', b'none').decode())
            decompressed_data = self._decompress_data(data, compression_type)
            memory_item = pickle.loads(decompressed_data)
            
            # Update access metadata
            memory_item.last_accessed = datetime.utcnow()
            memory_item.access_count += 1
            
            # Update local cache
            self._update_local_cache(memory_id, memory_item)
            
            self.cache_hits += 1
            return memory_item
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            self.cache_misses += 1
            return None
    
    def _update_local_cache(self, memory_id: str, memory_item: MemoryItem) -> None:
        """Update local LRU cache"""
        if memory_id in self.local_cache:
            del self.local_cache[memory_id]
        
        self.local_cache[memory_id] = memory_item
        
        # Maintain cache size
        while len(self.local_cache) > self.local_cache_size:
            self.local_cache.popitem(last=False)
    
    async def search_by_persona(self, persona_id: str, limit: int = 10) -> List[str]:
        """Search memory IDs by persona"""
        try:
            pattern = f"meta:*"
            memory_ids = []
            
            async for key in self.redis_client.scan_iter(match=pattern):
                metadata = await self.redis_client.hgetall(key)
                if metadata.get(b'persona_id', b'').decode() == persona_id:
                    memory_id = key.decode().replace('meta:', '')
                    memory_ids.append(memory_id)
                    
                    if len(memory_ids) >= limit:
                        break
            
            return memory_ids
            
        except Exception as e:
            self.logger.error(f"Failed to search memories for persona {persona_id}: {e}")
            return []
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            redis_info = await self.redis_client.info("memory")
            
            total_requests = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate_percent": round(hit_rate, 2),
                "compression_savings_bytes": self.compression_savings,
                "redis_memory_used": redis_info.get("used_memory_human", "0"),
                "redis_memory_peak": redis_info.get("used_memory_peak_human", "0"),
                "local_cache_size": len(self.local_cache)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {}

class VectorSearchEngine:
    """Advanced vector search for semantic memory retrieval"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # In-memory vector index for hot data
        self.vector_index: Dict[str, np.ndarray] = {}
        self.metadata_index: Dict[str, Dict[str, Any]] = {}
    
    def add_vector(self, memory_id: str, embedding: np.ndarray, metadata: Dict[str, Any]) -> None:
        """Add vector to search index"""
        self.vector_index[memory_id] = embedding
        self.metadata_index[memory_id] = metadata
    
    def remove_vector(self, memory_id: str) -> None:
        """Remove vector from search index"""
        self.vector_index.pop(memory_id, None)
        self.metadata_index.pop(memory_id, None)
    
    def search_similar(self, query_embedding: np.ndarray, 
                      persona_id: Optional[str] = None,
                      memory_type: Optional[str] = None,
                      limit: int = 10) -> List[Tuple[str, float]]:
        """Search for similar vectors using cosine similarity"""
        if not self.vector_index:
            return []
        
        results = []
        
        for memory_id, embedding in self.vector_index.items():
            # Apply filters
            metadata = self.metadata_index.get(memory_id, {})
            
            if persona_id and metadata.get('persona_id') != persona_id:
                continue
            
            if memory_type and metadata.get('memory_type') != memory_type:
                continue
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity >= self.config.similarity_threshold:
                results.append((memory_id, float(similarity)))
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get vector index statistics"""
        return {
            "total_vectors": len(self.vector_index),
            "index_size_mb": sum(v.nbytes for v in self.vector_index.values()) / (1024 * 1024),
            "embedding_dimension": self.config.embedding_dimension
        }

class MemoryManager:
    """Advanced memory management system with multi-tier storage"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.cache = MemoryCache(config)
        self.vector_search = VectorSearchEngine(config)
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.operation_times = defaultdict(list)
        self.memory_usage_mb = 0
    
    async def initialize(self) -> None:
        """Initialize memory management system"""
        await self.cache.initialize()
        self.logger.info("Memory management system initialized")
    
    async def store_memory(self, memory_item: MemoryItem) -> bool:
        """Store memory with intelligent tier placement"""
        try:
            start_time = datetime.utcnow()
            
            # Determine storage tier based on importance and recency
            tier = self._determine_storage_tier(memory_item)
            
            # Store in appropriate tier
            success = False
            if tier == MemoryTier.HOT:
                ttl = int(timedelta(hours=self.config.hot_retention_hours).total_seconds())
                success = await self.cache.store(memory_item, ttl_seconds=ttl)
                
                # Add to vector index if embedding exists
                if memory_item.embedding is not None:
                    metadata = {
                        'persona_id': memory_item.persona_id,
                        'memory_type': memory_item.memory_type,
                        'importance_score': memory_item.importance_score
                    }
                    self.vector_search.add_vector(memory_item.id, memory_item.embedding, metadata)
            
            # Track performance
            operation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.operation_times['store'].append(operation_time)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            return False
    
    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve memory with automatic tier promotion"""
        try:
            start_time = datetime.utcnow()
            
            # Try cache first (hot tier)
            memory_item = await self.cache.retrieve(memory_id)
            
            if memory_item:
                # Promote frequently accessed memories
                if memory_item.access_count > 10:
                    await self._promote_to_hot_tier(memory_item)
            
            # Track performance
            operation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.operation_times['retrieve'].append(operation_time)
            
            return memory_item
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    
    async def search_memories(self, query: str, persona_id: Optional[str] = None,
                            memory_type: Optional[str] = None,
                            use_vector_search: bool = True,
                            limit: int = 10) -> List[MemoryItem]:
        """Advanced memory search with multiple strategies"""
        try:
            start_time = datetime.utcnow()
            results = []
            
            if use_vector_search and hasattr(self, 'query_embedding'):
                # Vector similarity search
                similar_ids = self.vector_search.search_similar(
                    self.query_embedding, persona_id, memory_type, limit
                )
                
                for memory_id, similarity in similar_ids:
                    memory_item = await self.retrieve_memory(memory_id)
                    if memory_item:
                        memory_item.context['similarity_score'] = similarity
                        results.append(memory_item)
            
            else:
                # Fallback to cache search
                memory_ids = await self.cache.search_by_persona(persona_id or "", limit)
                
                for memory_id in memory_ids:
                    memory_item = await self.retrieve_memory(memory_id)
                    if memory_item and (not memory_type or memory_item.memory_type == memory_type):
                        results.append(memory_item)
            
            # Track performance
            operation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.operation_times['search'].append(operation_time)
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to search memories: {e}")
            return []
    
    def _determine_storage_tier(self, memory_item: MemoryItem) -> MemoryTier:
        """Determine optimal storage tier for memory item"""
        # High importance or recent memories go to hot tier
        if (memory_item.importance_score > 0.7 or 
            (datetime.utcnow() - memory_item.created_at).hours < 24):
            return MemoryTier.HOT
        
        # Medium importance goes to warm tier
        if memory_item.importance_score > 0.3:
            return MemoryTier.WARM
        
        # Low importance goes to cold tier
        return MemoryTier.COLD
    
    async def _promote_to_hot_tier(self, memory_item: MemoryItem) -> None:
        """Promote memory to hot tier for faster access"""
        ttl = int(timedelta(hours=self.config.hot_retention_hours).total_seconds())
        await self.cache.store(memory_item, ttl_seconds=ttl)
    
    async def optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize memory usage and clean up old data"""
        try:
            start_time = datetime.utcnow()
            
            # Get current stats
            cache_stats = await self.cache.get_cache_stats()
            vector_stats = self.vector_search.get_index_stats()
            
            # Cleanup operations would go here
            # (archiving old memories, compacting indexes, etc.)
            
            optimization_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "optimization_time_ms": optimization_time,
                "cache_stats": cache_stats,
                "vector_stats": vector_stats,
                "memory_usage_mb": self.memory_usage_mb
            }
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
            return {}
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {}
        
        for operation, times in self.operation_times.items():
            if times:
                metrics[f"{operation}_avg_ms"] = sum(times) / len(times)
                metrics[f"{operation}_max_ms"] = max(times)
                metrics[f"{operation}_min_ms"] = min(times)
                metrics[f"{operation}_count"] = len(times)
        
        # Add cache and vector search stats
        metrics.update(await self.cache.get_cache_stats())
        metrics.update(self.vector_search.get_index_stats())
        
        return metrics

# Global memory manager instance
memory_config = MemoryConfig()
memory_manager = MemoryManager(memory_config)

async def initialize_memory_system():
    """Initialize the production memory system"""
    await memory_manager.initialize()

async def get_memory_manager():
    """Get memory manager instance"""
    return memory_manager

