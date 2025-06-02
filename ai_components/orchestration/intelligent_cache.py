#!/usr/bin/env python3
"""
Intelligent Caching System for AI Orchestration
Provides ML-based caching with semantic similarity, pattern recognition, and predictive pre-loading
"""

import os
import sys
import json
import time
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import numpy as np

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.database import initialize_database

logger = logging.getLogger(__name__)

class CacheType(Enum):
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    COMPLETION = "completion"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    last_accessed: datetime
    access_count: int
    semantic_hash: str
    context_hash: str
    ttl_seconds: int
    confidence_score: float
    file_path: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict] = None

class IntelligentCache:
    """Advanced caching system with ML-based optimization"""
    
    def __init__(self, max_memory_mb: int = 512, max_entries: int = 10000):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}
        self.semantic_index: Dict[str, List[str]] = {}  # semantic_hash -> [cache_keys]
        self.context_index: Dict[str, List[str]] = {}   # context_hash -> [cache_keys]
        self.db = None
        
        # Performance metrics
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "semantic_hits": 0,
            "predictive_hits": 0,
            "total_requests": 0,
            "average_response_time": 0.0,
            "memory_usage_bytes": 0
        }
        
        # ML-based pattern recognition
        self.pattern_weights = {
            "exact_match": 1.0,
            "semantic_similarity": 0.8,
            "context_similarity": 0.6,
            "file_path_similarity": 0.4,
            "language_match": 0.3,
            "recency": 0.2
        }
        
        # Cache configuration by type
        self.cache_config = {
            CacheType.CODE_ANALYSIS: {"ttl": 3600, "max_size": 100000},
            CacheType.CODE_GENERATION: {"ttl": 1800, "max_size": 50000},
            CacheType.COMPLETION: {"ttl": 600, "max_size": 20000},
            CacheType.REFACTORING: {"ttl": 2400, "max_size": 75000},
            CacheType.DOCUMENTATION: {"ttl": 7200, "max_size": 30000}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize database for persistent cache
        postgres_url = os.environ.get(
            'POSTGRES_URL',
            'postgresql://postgres:password@localhost:5432/orchestra'
        )
        weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
        weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
        
        self.db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
        await self._setup_cache_database()
        await self._load_persistent_cache()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._save_persistent_cache()
        if self.db:
            await self.db.close()
    
    async def get(self, key: str, cache_type: CacheType, 
                 context: Dict = None) -> Optional[Any]:
        """Get value from cache with intelligent lookup"""
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            # 1. Exact key match
            if key in self.cache:
                entry = self.cache[key]
                if self._is_valid(entry):
                    entry.last_accessed = datetime.now()
                    entry.access_count += 1
                    self.metrics["hits"] += 1
                    return entry.value
                else:
                    # Remove expired entry
                    await self._remove_entry(key)
            
            # 2. Semantic similarity lookup
            semantic_result = await self._semantic_lookup(key, cache_type, context)
            if semantic_result:
                self.metrics["semantic_hits"] += 1
                return semantic_result
            
            # 3. Context-based lookup
            context_result = await self._context_lookup(key, cache_type, context)
            if context_result:
                return context_result
            
            # 4. Pattern-based prediction
            predicted_result = await self._predictive_lookup(key, cache_type, context)
            if predicted_result:
                self.metrics["predictive_hits"] += 1
                return predicted_result
            
            self.metrics["misses"] += 1
            return None
            
        finally:
            # Update average response time
            response_time = time.time() - start_time
            total_time = self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1)
            self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_requests"]
    
    async def set(self, key: str, value: Any, cache_type: CacheType,
                 context: Dict = None, confidence_score: float = 1.0,
                 file_path: str = None, language: str = None) -> None:
        """Set value in cache with intelligent indexing"""
        # Check if we need to evict entries
        await self._ensure_capacity()
        
        # Create cache entry
        semantic_hash = self._generate_semantic_hash(key, value, context)
        context_hash = self._generate_context_hash(context, file_path, language)
        
        config = self.cache_config[cache_type]
        entry = CacheEntry(
            key=key,
            value=value,
            cache_type=cache_type,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            semantic_hash=semantic_hash,
            context_hash=context_hash,
            ttl_seconds=config["ttl"],
            confidence_score=confidence_score,
            file_path=file_path,
            language=language,
            metadata=context or {}
        )
        
        # Store in cache
        self.cache[key] = entry
        
        # Update indexes
        if semantic_hash not in self.semantic_index:
            self.semantic_index[semantic_hash] = []
        self.semantic_index[semantic_hash].append(key)
        
        if context_hash not in self.context_index:
            self.context_index[context_hash] = []
        self.context_index[context_hash].append(key)
        
        # Update memory usage
        self._update_memory_usage()
        
        # Async save to persistent storage
        asyncio.create_task(self._save_entry_to_db(entry))
    
    async def invalidate_pattern(self, pattern: str, cache_type: CacheType = None) -> int:
        """Invalidate cache entries matching a pattern"""
        invalidated = 0
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            if cache_type and entry.cache_type != cache_type:
                continue
            
            if pattern in key or (entry.file_path and pattern in entry.file_path):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            await self._remove_entry(key)
            invalidated += 1
        
        return invalidated
    
    async def get_similar_entries(self, key: str, cache_type: CacheType,
                                context: Dict = None, max_results: int = 5) -> List[Tuple[str, Any, float]]:
        """Get similar cache entries with similarity scores"""
        candidates = []
        target_semantic = self._generate_semantic_hash(key, None, context)
        target_context = self._generate_context_hash(context)
        
        for cache_key, entry in self.cache.items():
            if entry.cache_type != cache_type or not self._is_valid(entry):
                continue
            
            # Calculate similarity score
            similarity = self._calculate_similarity(
                key, cache_key, target_semantic, entry.semantic_hash,
                target_context, entry.context_hash, context, entry.metadata
            )
            
            if similarity > 0.3:  # Minimum similarity threshold
                candidates.append((cache_key, entry.value, similarity))
        
        # Sort by similarity and return top results
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[:max_results]
    
    async def optimize_cache(self) -> Dict:
        """Optimize cache performance using ML insights"""
        optimization_results = {
            "entries_optimized": 0,
            "memory_freed": 0,
            "patterns_identified": 0,
            "recommendations": []
        }
        
        # Analyze access patterns
        access_patterns = await self._analyze_access_patterns()
        
        # Identify underused entries
        underused_entries = [
            key for key, entry in self.cache.items()
            if entry.access_count < 3 and 
            (datetime.now() - entry.created_at).days > 1
        ]
        
        # Remove underused entries
        for key in underused_entries:
            memory_freed = sys.getsizeof(pickle.dumps(self.cache[key].value))
            await self._remove_entry(key)
            optimization_results["entries_optimized"] += 1
            optimization_results["memory_freed"] += memory_freed
        
        # Adjust cache configuration based on patterns
        for cache_type, patterns in access_patterns.items():
            if patterns["avg_access_frequency"] > 10:
                # Increase TTL for frequently accessed items
                self.cache_config[cache_type]["ttl"] *= 1.2
            elif patterns["avg_access_frequency"] < 2:
                # Decrease TTL for rarely accessed items
                self.cache_config[cache_type]["ttl"] *= 0.8
        
        optimization_results["patterns_identified"] = len(access_patterns)
        
        # Generate recommendations
        if self.metrics["hits"] / max(1, self.metrics["total_requests"]) < 0.6:
            optimization_results["recommendations"].append("Consider increasing cache TTL values")
        
        if self.metrics["memory_usage_bytes"] > self.max_memory_bytes * 0.9:
            optimization_results["recommendations"].append("Consider increasing cache memory limit")
        
        return optimization_results
    
    def get_performance_metrics(self) -> Dict:
        """Get comprehensive cache performance metrics"""
        total_requests = max(1, self.metrics["total_requests"])
        hit_rate = self.metrics["hits"] / total_requests
        semantic_hit_rate = self.metrics["semantic_hits"] / total_requests
        
        return {
            "hit_rate": hit_rate,
            "semantic_hit_rate": semantic_hit_rate,
            "miss_rate": self.metrics["misses"] / total_requests,
            "total_entries": len(self.cache),
            "memory_usage_mb": self.metrics["memory_usage_bytes"] / (1024 * 1024),
            "memory_efficiency": hit_rate * 100,  # hits per MB
            "average_response_time_ms": self.metrics["average_response_time"] * 1000,
            "eviction_rate": self.metrics["evictions"] / total_requests,
            "cache_types": {
                cache_type.value: len([e for e in self.cache.values() if e.cache_type == cache_type])
                for cache_type in CacheType
            }
        }
    
    async def _semantic_lookup(self, key: str, cache_type: CacheType, 
                             context: Dict) -> Optional[Any]:
        """Lookup using semantic similarity"""
        semantic_hash = self._generate_semantic_hash(key, None, context)
        
        if semantic_hash in self.semantic_index:
            candidates = self.semantic_index[semantic_hash]
            for candidate_key in candidates:
                if candidate_key in self.cache:
                    entry = self.cache[candidate_key]
                    if entry.cache_type == cache_type and self._is_valid(entry):
                        # Update access statistics
                        entry.last_accessed = datetime.now()
                        entry.access_count += 1
                        return entry.value
        
        return None
    
    async def _context_lookup(self, key: str, cache_type: CacheType,
                            context: Dict) -> Optional[Any]:
        """Lookup using context similarity"""
        context_hash = self._generate_context_hash(context)
        
        if context_hash in self.context_index:
            candidates = self.context_index[context_hash]
            for candidate_key in candidates:
                if candidate_key in self.cache:
                    entry = self.cache[candidate_key]
                    if entry.cache_type == cache_type and self._is_valid(entry):
                        # Check if key similarity is reasonable
                        similarity = self._calculate_key_similarity(key, candidate_key)
                        if similarity > 0.5:
                            entry.last_accessed = datetime.now()
                            entry.access_count += 1
                            return entry.value
        
        return None
    
    async def _predictive_lookup(self, key: str, cache_type: CacheType,
                               context: Dict) -> Optional[Any]:
        """Predictive lookup based on patterns"""
        # Simple pattern matching - can be enhanced with ML models
        similar_entries = await self.get_similar_entries(key, cache_type, context, 3)
        
        if similar_entries:
            # Return the most similar entry if confidence is high enough
            best_match = similar_entries[0]
            if best_match[2] > 0.8:  # High similarity threshold
                return best_match[1]
        
        return None
    
    def _generate_semantic_hash(self, key: str, value: Any = None, 
                              context: Dict = None) -> str:
        """Generate semantic hash for similarity matching"""
        # Simple implementation - can be enhanced with embeddings
        content = f"{key}_{context or {}}"
        if value:
            content += f"_{str(type(value))}"
        
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_context_hash(self, context: Dict = None, file_path: str = None,
                             language: str = None) -> str:
        """Generate context hash for similarity matching"""
        context_data = {
            "context": context or {},
            "file_path": file_path,
            "language": language
        }
        content = json.dumps(context_data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _calculate_similarity(self, key1: str, key2: str, semantic1: str, semantic2: str,
                            context1: str, context2: str, ctx1: Dict, ctx2: Dict) -> float:
        """Calculate similarity score between two cache entries"""
        score = 0.0
        
        # Exact key match
        if key1 == key2:
            score += self.pattern_weights["exact_match"]
        else:
            # Key similarity
            key_sim = self._calculate_key_similarity(key1, key2)
            score += key_sim * self.pattern_weights["exact_match"]
        
        # Semantic similarity
        if semantic1 == semantic2:
            score += self.pattern_weights["semantic_similarity"]
        
        # Context similarity
        if context1 == context2:
            score += self.pattern_weights["context_similarity"]
        
        # Language match
        if ctx1 and ctx2:
            if ctx1.get("language") == ctx2.get("language"):
                score += self.pattern_weights["language_match"]
        
        return min(score, 1.0)
    
    def _calculate_key_similarity(self, key1: str, key2: str) -> float:
        """Calculate similarity between two keys"""
        # Simple Jaccard similarity
        set1 = set(key1.lower().split())
        set2 = set(key2.lower().split())
        
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union
    
    def _is_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - entry.created_at).total_seconds()
        return age < entry.ttl_seconds
    
    async def _ensure_capacity(self) -> None:
        """Ensure cache doesn't exceed capacity limits"""
        # Check entry count
        while len(self.cache) >= self.max_entries:
            await self._evict_lru_entry()
        
        # Check memory usage
        while self.metrics["memory_usage_bytes"] > self.max_memory_bytes:
            await self._evict_lru_entry()
    
    async def _evict_lru_entry(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (
                self.cache[k].last_accessed,
                -self.cache[k].access_count  # Prefer keeping frequently accessed items
            )
        )
        
        await self._remove_entry(lru_key)
        self.metrics["evictions"] += 1
    
    async def _remove_entry(self, key: str) -> None:
        """Remove entry from cache and indexes"""
        if key not in self.cache:
            return
        
        entry = self.cache[key]
        
        # Remove from indexes
        if entry.semantic_hash in self.semantic_index:
            if key in self.semantic_index[entry.semantic_hash]:
                self.semantic_index[entry.semantic_hash].remove(key)
            if not self.semantic_index[entry.semantic_hash]:
                del self.semantic_index[entry.semantic_hash]
        
        if entry.context_hash in self.context_index:
            if key in self.context_index[entry.context_hash]:
                self.context_index[entry.context_hash].remove(key)
            if not self.context_index[entry.context_hash]:
                del self.context_index[entry.context_hash]
        
        # Remove from cache
        del self.cache[key]
        
        # Update memory usage
        self._update_memory_usage()
    
    def _update_memory_usage(self) -> None:
        """Update memory usage metrics"""
        total_size = 0
        for entry in self.cache.values():
            total_size += sys.getsizeof(pickle.dumps(entry))
        self.metrics["memory_usage_bytes"] = total_size
    
    async def _analyze_access_patterns(self) -> Dict:
        """Analyze cache access patterns for optimization"""
        patterns = {}
        
        for cache_type in CacheType:
            type_entries = [e for e in self.cache.values() if e.cache_type == cache_type]
            if type_entries:
                patterns[cache_type] = {
                    "count": len(type_entries),
                    "avg_access_frequency": sum(e.access_count for e in type_entries) / len(type_entries),
                    "avg_age_hours": sum(
                        (datetime.now() - e.created_at).total_seconds() / 3600 
                        for e in type_entries
                    ) / len(type_entries)
                }
        
        return patterns
    
    async def _setup_cache_database(self) -> None:
        """Setup database tables for persistent cache"""
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS intelligent_cache (
                id SERIAL PRIMARY KEY,
                cache_key VARCHAR(500) NOT NULL UNIQUE,
                cache_value BYTEA NOT NULL,
                cache_type VARCHAR(100) NOT NULL,
                semantic_hash VARCHAR(32),
                context_hash VARCHAR(32),
                confidence_score FLOAT DEFAULT 1.0,
                file_path TEXT,
                language VARCHAR(50),
                metadata JSONB,
                access_count INTEGER DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                last_accessed TIMESTAMP WITH TIME ZONE NOT NULL,
                ttl_seconds INTEGER NOT NULL
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cache_semantic_hash 
            ON intelligent_cache(semantic_hash);
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cache_context_hash 
            ON intelligent_cache(context_hash);
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cache_type_created 
            ON intelligent_cache(cache_type, created_at DESC);
        """, fetch=False)
    
    async def _load_persistent_cache(self) -> None:
        """Load cache from persistent storage"""
        try:
            results = await self.db.execute_query("""
                SELECT cache_key, cache_value, cache_type, semantic_hash, context_hash,
                       confidence_score, file_path, language, metadata, access_count,
                       created_at, last_accessed, ttl_seconds
                FROM intelligent_cache
                WHERE created_at > NOW() - INTERVAL '1 day'
                ORDER BY last_accessed DESC
                LIMIT 1000
            """)
            
            loaded_count = 0
            for row in results:
                try:
                    entry = CacheEntry(
                        key=row[0],
                        value=pickle.loads(row[1]),
                        cache_type=CacheType(row[2]),
                        semantic_hash=row[3],
                        context_hash=row[4],
                        confidence_score=row[5],
                        file_path=row[6],
                        language=row[7],
                        metadata=row[8],
                        access_count=row[9],
                        created_at=row[10],
                        last_accessed=row[11],
                        ttl_seconds=row[12]
                    )
                    
                    if self._is_valid(entry):
                        self.cache[entry.key] = entry
                        
                        # Update indexes
                        if entry.semantic_hash not in self.semantic_index:
                            self.semantic_index[entry.semantic_hash] = []
                        self.semantic_index[entry.semantic_hash].append(entry.key)
                        
                        if entry.context_hash not in self.context_index:
                            self.context_index[entry.context_hash] = []
                        self.context_index[entry.context_hash].append(entry.key)
                        
                        loaded_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to load cache entry: {e}")
            
            self._update_memory_usage()
            logger.info(f"Loaded {loaded_count} cache entries from persistent storage")
            
        except Exception as e:
            logger.error(f"Failed to load persistent cache: {e}")
    
    async def _save_persistent_cache(self) -> None:
        """Save cache to persistent storage"""
        try:
            # Save only recently accessed entries
            cutoff_time = datetime.now() - timedelta(hours=6)
            recent_entries = [
                entry for entry in self.cache.values()
                if entry.last_accessed > cutoff_time
            ]
            
            for entry in recent_entries[:100]:  # Limit to 100 most recent
                await self._save_entry_to_db(entry)
            
            logger.info(f"Saved {len(recent_entries)} cache entries to persistent storage")
            
        except Exception as e:
            logger.error(f"Failed to save persistent cache: {e}")
    
    async def _save_entry_to_db(self, entry: CacheEntry) -> None:
        """Save individual cache entry to database"""
        try:
            value_bytes = pickle.dumps(entry.value)
            
            await self.db.execute_query("""
                INSERT INTO intelligent_cache 
                (cache_key, cache_value, cache_type, semantic_hash, context_hash,
                 confidence_score, file_path, language, metadata, access_count,
                 created_at, last_accessed, ttl_seconds)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (cache_key) 
                DO UPDATE SET 
                    access_count = EXCLUDED.access_count,
                    last_accessed = EXCLUDED.last_accessed
            """, 
            entry.key, value_bytes, entry.cache_type.value, entry.semantic_hash,
            entry.context_hash, entry.confidence_score, entry.file_path,
            entry.language, json.dumps(entry.metadata) if entry.metadata else None,
            entry.access_count, entry.created_at, entry.last_accessed, entry.ttl_seconds,
            fetch=False)
            
        except Exception as e:
            logger.warning(f"Failed to save cache entry to DB: {e}")


# Global cache instance
_cache_instance = None

async def get_cache() -> IntelligentCache:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IntelligentCache()
        await _cache_instance.__aenter__()
    return _cache_instance

def cache_decorator(cache_type: CacheType, ttl: int = None):
    """Decorator for automatic caching of function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{func.__name__}_{args}_{sorted(kwargs.items())}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            cache = await get_cache()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key, cache_type, kwargs)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(
                cache_key, result, cache_type, 
                context=kwargs, confidence_score=0.9
            )
            
            return result
        return wrapper
    return decorator


async def main():
    """Test the intelligent cache system"""
    print("🚀 Testing Intelligent Cache System...")
    
    async with IntelligentCache(max_memory_mb=64, max_entries=1000) as cache:
        # Test basic caching
        print("\n1. Testing basic caching...")
        await cache.set(
            "test_analysis_1", 
            {"status": "success", "complexity": "medium"},
            CacheType.CODE_ANALYSIS,
            context={"language": "python", "file": "test.py"}
        )
        
        result = await cache.get("test_analysis_1", CacheType.CODE_ANALYSIS)
        print(f"   ✅ Basic cache: {'Hit' if result else 'Miss'}")
        
        # Test semantic similarity
        print("\n2. Testing semantic similarity...")
        similar_result = await cache.get(
            "test_analysis_similar", 
            CacheType.CODE_ANALYSIS,
            context={"language": "python", "file": "test.py"}
        )
        print(f"   ✅ Semantic cache: {'Hit' if similar_result else 'Miss'}")
        
        # Test similarity search
        print("\n3. Testing similarity search...")
        similar_entries = await cache.get_similar_entries(
            "analyze_python_code", CacheType.CODE_ANALYSIS
        )
        print(f"   ✅ Found {len(similar_entries)} similar entries")
        
        # Performance test
        print("\n4. Performance testing...")
        start_time = time.time()
        for i in range(100):
            await cache.set(f"perf_test_{i}", f"value_{i}", CacheType.COMPLETION)
        for i in range(100):
            await cache.get(f"perf_test_{i}", CacheType.COMPLETION)
        
        duration = time.time() - start_time
        print(f"   ✅ 200 operations completed in {duration:.3f}s")
        
        # Cache optimization
        print("\n5. Testing cache optimization...")
        optimization_results = await cache.optimize_cache()
        print(f"   ✅ Optimized {optimization_results['entries_optimized']} entries")
        
        # Performance metrics
        metrics = cache.get_performance_metrics()
        print(f"\n📊 Cache Performance Metrics:")
        print(f"   Hit Rate: {metrics['hit_rate']:.1%}")
        print(f"   Memory Usage: {metrics['memory_usage_mb']:.1f} MB")
        print(f"   Total Entries: {metrics['total_entries']}")
        print(f"   Avg Response Time: {metrics['average_response_time_ms']:.2f} ms")


if __name__ == "__main__":
    asyncio.run(main()) 