#!/usr/bin/env python3
"""
Redis Cache Warming Strategies
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class WarmingStrategy(Enum):
    """Cache warming strategies"""
    EAGER = "eager"          # Warm all keys immediately
    LAZY = "lazy"            # Warm on first miss
    SCHEDULED = "scheduled"  # Warm on schedule
    PREDICTIVE = "predictive"  # Warm based on usage patterns


@dataclass
class CacheEntry:
    """Cache entry metadata"""
    key: str
    value: Any
    ttl: int
    priority: int = 0
    access_count: int = 0
    last_access: Optional[datetime] = None
    warming_strategy: WarmingStrategy = WarmingStrategy.LAZY
    
    def should_warm(self, threshold_hours: int = 1) -> bool:
        """Check if entry should be warmed"""
        if self.warming_strategy == WarmingStrategy.EAGER:
            return True
        
        if self.warming_strategy == WarmingStrategy.PREDICTIVE:
            # Warm if accessed frequently
            if self.access_count > 10:
                return True
            
            # Warm if accessed recently
            if self.last_access:
                age = datetime.utcnow() - self.last_access
                if age < timedelta(hours=threshold_hours):
                    return True
                    
        return False


class CacheWarmer:
    """Redis cache warming implementation"""
    
    def __init__(
        self,
        redis_client,
        warming_strategy: WarmingStrategy = WarmingStrategy.LAZY,
        batch_size: int = 100,
        concurrent_warmers: int = 5
    ):
        self.redis_client = redis_client
        self.warming_strategy = warming_strategy
        self.batch_size = batch_size
        self.concurrent_warmers = concurrent_warmers
        
        # Track warming operations
        self.warming_queue: List[CacheEntry] = []
        self.warming_in_progress: Set[str] = set()
        self.warming_stats = {
            "total_warmed": 0,
            "failed_warmings": 0,
            "last_warming_time": None,
            "average_warming_time_ms": 0
        }
        
        # Data loaders registry
        self.data_loaders: Dict[str, Callable] = {}
        
    def register_loader(self, pattern: str, loader: Callable):
        """Register data loader for key pattern"""
        self.data_loaders[pattern] = loader
        logger.info(f"Registered data loader for pattern: {pattern}")
        
    async def warm_cache(self, entries: List[CacheEntry]) -> Dict[str, Any]:
        """Warm cache with specified entries"""
        start_time = datetime.utcnow()
        results = {
            "warmed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_ms": 0
        }
        
        # Filter entries based on strategy
        entries_to_warm = [
            entry for entry in entries
            if entry.should_warm() and entry.key not in self.warming_in_progress
        ]
        
        if not entries_to_warm:
            logger.info("No entries to warm")
            return results
            
        logger.info(f"Starting cache warming for {len(entries_to_warm)} entries")
        
        # Process in batches
        for i in range(0, len(entries_to_warm), self.batch_size):
            batch = entries_to_warm[i:i + self.batch_size]
            
            # Warm batch concurrently
            tasks = []
            for entry in batch:
                self.warming_in_progress.add(entry.key)
                tasks.append(self._warm_single_entry(entry))
                
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for entry, result in zip(batch, batch_results):
                self.warming_in_progress.discard(entry.key)
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to warm {entry.key}: {result}")
                    results["failed"] += 1
                elif result:
                    results["warmed"] += 1
                else:
                    results["skipped"] += 1
                    
        # Update stats
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        results["duration_ms"] = duration
        
        self.warming_stats["total_warmed"] += results["warmed"]
        self.warming_stats["failed_warmings"] += results["failed"]
        self.warming_stats["last_warming_time"] = datetime.utcnow()
        
        # Update average warming time
        if results["warmed"] > 0:
            avg_time = duration / results["warmed"]
            current_avg = self.warming_stats["average_warming_time_ms"]
            total_warmed = self.warming_stats["total_warmed"]
            
            # Weighted average
            self.warming_stats["average_warming_time_ms"] = (
                (current_avg * (total_warmed - results["warmed"]) + avg_time * results["warmed"])
                / total_warmed
            )
            
        logger.info(f"Cache warming completed: {results}")
        return results
        
    async def _warm_single_entry(self, entry: CacheEntry) -> bool:
        """Warm a single cache entry"""
        try:
            # Check if already cached
            if await self._is_cached(entry.key):
                logger.debug(f"Key {entry.key} already cached")
                return False
                
            # Find appropriate loader
            loader = self._find_loader(entry.key)
            if not loader:
                logger.warning(f"No loader found for key: {entry.key}")
                return False
                
            # Load data
            if asyncio.iscoroutinefunction(loader):
                data = await loader(entry.key)
            else:
                data = loader(entry.key)
                
            if data is None:
                logger.warning(f"Loader returned None for key: {entry.key}")
                return False
                
            # Cache data
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
                
            success = self.redis_client.set(entry.key, data, ex=entry.ttl)
            
            if success:
                logger.debug(f"Successfully warmed key: {entry.key}")
                return True
            else:
                logger.error(f"Failed to set key: {entry.key}")
                return False
                
        except Exception as e:
            logger.error(f"Error warming key {entry.key}: {e}")
            raise
            
    async def _is_cached(self, key: str) -> bool:
        """Check if key is already cached"""
        try:
            return self.redis_client.exists(key) > 0
        except Exception:
            return False
            
    def _find_loader(self, key: str) -> Optional[Callable]:
        """Find loader for key"""
        # Exact match
        if key in self.data_loaders:
            return self.data_loaders[key]
            
        # Pattern match
        for pattern, loader in self.data_loaders.items():
            if self._matches_pattern(key, pattern):
                return loader
                
        return None
        
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern"""
        # Simple wildcard matching
        if '*' in pattern:
            import fnmatch
            return fnmatch.fnmatch(key, pattern)
        return key == pattern
        
    def get_stats(self) -> Dict[str, Any]:
        """Get warming statistics"""
        return self.warming_stats.copy()


class PredictiveCacheWarmer(CacheWarmer):
    """Predictive cache warming based on usage patterns"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_patterns: Dict[str, List[datetime]] = {}
        self.prediction_window_hours = 24
        
    def track_access(self, key: str):
        """Track key access for prediction"""
        if key not in self.access_patterns:
            self.access_patterns[key] = []
            
        self.access_patterns[key].append(datetime.utcnow())
        
        # Keep only recent accesses
        cutoff = datetime.utcnow() - timedelta(hours=self.prediction_window_hours)
        self.access_patterns[key] = [
            ts for ts in self.access_patterns[key]
            if ts > cutoff
        ]
        
    def predict_next_access(self, key: str) -> Optional[datetime]:
        """Predict when key will be accessed next"""
        if key not in self.access_patterns or len(self.access_patterns[key]) < 2:
            return None
            
        accesses = self.access_patterns[key]
        
        # Calculate average interval between accesses
        intervals = []
        for i in range(1, len(accesses)):
            interval = (accesses[i] - accesses[i-1]).total_seconds()
            intervals.append(interval)
            
        avg_interval = sum(intervals) / len(intervals)
        
        # Predict next access
        last_access = accesses[-1]
        predicted_next = last_access + timedelta(seconds=avg_interval)
        
        return predicted_next
        
    async def warm_predicted_keys(self) -> Dict[str, Any]:
        """Warm keys predicted to be accessed soon"""
        entries_to_warm = []
        current_time = datetime.utcnow()
        
        for key, accesses in self.access_patterns.items():
            if len(accesses) < 2:
                continue
                
            predicted_time = self.predict_next_access(key)
            if not predicted_time:
                continue
                
            # Warm if predicted access is within threshold
            time_until_access = (predicted_time - current_time).total_seconds()
            if 0 < time_until_access < 300:  # Within 5 minutes
                entry = CacheEntry(
                    key=key,
                    value=None,  # Will be loaded by loader
                    ttl=3600,    # 1 hour default
                    priority=len(accesses),  # Higher access count = higher priority
                    warming_strategy=WarmingStrategy.PREDICTIVE
                )
                entries_to_warm.append(entry)
                
        # Sort by priority
        entries_to_warm.sort(key=lambda e: e.priority, reverse=True)
        
        # Warm top entries
        return await self.warm_cache(entries_to_warm[:self.batch_size])


class ScheduledCacheWarmer:
    """Scheduled cache warming"""
    
    def __init__(
        self,
        cache_warmer: CacheWarmer,
        schedule_interval_minutes: int = 30
    ):
        self.cache_warmer = cache_warmer
        self.schedule_interval = timedelta(minutes=schedule_interval_minutes)
        self.scheduled_entries: List[CacheEntry] = []
        self._running = False
        self._task = None
        
    def schedule_warming(self, entries: List[CacheEntry]):
        """Schedule entries for warming"""
        self.scheduled_entries.extend(entries)
        logger.info(f"Scheduled {len(entries)} entries for warming")
        
    async def start(self):
        """Start scheduled warming"""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._warming_loop())
        logger.info("Started scheduled cache warming")
        
    async def stop(self):
        """Stop scheduled warming"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped scheduled cache warming")
        
    async def _warming_loop(self):
        """Scheduled warming loop"""
        while self._running:
            try:
                if self.scheduled_entries:
                    # Warm scheduled entries
                    entries_to_warm = self.scheduled_entries[:self.cache_warmer.batch_size]
                    self.scheduled_entries = self.scheduled_entries[self.cache_warmer.batch_size:]
                    
                    await self.cache_warmer.warm_cache(entries_to_warm)
                    
                # Wait for next interval
                await asyncio.sleep(self.schedule_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduled warming error: {e}")
                await asyncio.sleep(60)  # Wait before retry


# Example data loaders
def create_user_data_loader(database):
    """Create user data loader"""
    async def loader(key: str) -> Optional[Dict[str, Any]]:
        # Extract user ID from key (e.g., "user:123")
        parts = key.split(":")
        if len(parts) != 2 or parts[0] != "user":
            return None
            
        user_id = parts[1]
        
        # Load from database
        query = "SELECT * FROM users WHERE id = $1"
        result = await database.fetch_one(query, user_id)
        
        if result:
            return dict(result)
        return None
        
    return loader


def create_computed_data_loader(compute_func: Callable):
    """Create loader for computed data"""
    async def loader(key: str) -> Optional[Any]:
        # Extract parameters from key
        params = key.split(":")
        
        # Compute result
        if asyncio.iscoroutinefunction(compute_func):
            result = await compute_func(*params)
        else:
            result = compute_func(*params)
            
        return result
        
    return loader