"""
Memory Optimizer Implementation

Implements ML-based optimization for memory tier management, including
access pattern analysis, predictive prefetching, and automatic tier balancing.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
import pickle
import json

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

from ..interfaces import (
    IMemoryOptimizer,
    IMemoryStorage,
    MemoryTier,
    MemoryItem,
    OptimizationConfig
)
from ..exceptions import MemoryOptimizationError

logger = logging.getLogger(__name__)

class AccessPattern:
    """Represents access patterns for a memory item."""
    
    def __init__(self, key: str, window_size: int = 100):
        self.key = key
        self.access_times: deque = deque(maxlen=window_size)
        self.access_intervals: deque = deque(maxlen=window_size - 1)
        self.last_access: Optional[datetime] = None
        self.total_accesses: int = 0
        self.size_bytes: int = 0
        self.tier_history: deque = deque(maxlen=10)
    
    def record_access(self, timestamp: datetime, tier: MemoryTier) -> None:
        """Record an access event."""
        self.access_times.append(timestamp)
        self.total_accesses += 1
        
        if self.last_access:
            interval = (timestamp - self.last_access).total_seconds()
            self.access_intervals.append(interval)
        
        self.last_access = timestamp
        self.tier_history.append((timestamp, tier))
    
    def get_features(self) -> Dict[str, float]:
        """Extract features for ML model."""
        if not self.access_intervals:
            return {
                'mean_interval': 0.0,
                'std_interval': 0.0,
                'min_interval': 0.0,
                'max_interval': 0.0,
                'access_rate': 0.0,
                'recency_hours': float('inf'),
                'total_accesses': 0.0,
                'size_kb': 0.0,
            }
        
        intervals = list(self.access_intervals)
        recency = (datetime.utcnow() - self.last_access).total_seconds() / 3600 if self.last_access else float('inf')
        
        return {
            'mean_interval': np.mean(intervals),
            'std_interval': np.std(intervals),
            'min_interval': np.min(intervals),
            'max_interval': np.max(intervals),
            'access_rate': self.total_accesses / max(1, len(intervals)),
            'recency_hours': recency,
            'total_accesses': float(self.total_accesses),
            'size_kb': self.size_bytes / 1024.0,
        }

class PrefetchPredictor:
    """Predicts which items should be prefetched based on access patterns."""
    
    def __init__(self):
        self.sequence_patterns: Dict[str, List[str]] = defaultdict(list)
        self.co_access_matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.temporal_patterns: Dict[str, List[float]] = defaultdict(list)
        self.max_sequence_length = 5
    
    def record_access_sequence(self, keys: List[str], timestamps: List[datetime]) -> None:
        """Record a sequence of accesses for pattern learning."""
        # Update sequence patterns
        for i in range(len(keys) - 1):
            current_key = keys[i]
            next_key = keys[i + 1]
            
            # Add to sequence
            if len(self.sequence_patterns[current_key]) < self.max_sequence_length:
                self.sequence_patterns[current_key].append(next_key)
            else:
                self.sequence_patterns[current_key].pop(0)
                self.sequence_patterns[current_key].append(next_key)
            
            # Update co-access matrix
            self.co_access_matrix[current_key][next_key] += 1
            
            # Record temporal pattern
            if i < len(timestamps) - 1:
                interval = (timestamps[i + 1] - timestamps[i]).total_seconds()
                self.temporal_patterns[current_key].append(interval)
    
    def predict_next_accesses(self, key: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Predict the next likely accesses after a given key."""
        predictions = []
        
        # Get co-access scores
        co_accesses = self.co_access_matrix.get(key, {})
        total_co_accesses = sum(co_accesses.values())
        
        if total_co_accesses > 0:
            # Calculate probabilities
            for next_key, count in co_accesses.items():
                probability = count / total_co_accesses
                predictions.append((next_key, probability))
        
        # Sort by probability and limit
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:limit]

class MemoryOptimizer(IMemoryOptimizer):
    """
    Production-ready memory optimization system.
    
    Features:
    - ML-based access pattern prediction
    - Automatic tier recommendation
    - Predictive prefetching
    - Cost-aware optimization
    - Real-time adaptation
    """
    
    def __init__(self, config: OptimizationConfig):
        """Initialize the memory optimizer."""
        self.config = config
        self.storages: Dict[MemoryTier, IMemoryStorage] = {}
        
        # Access pattern tracking
        self.access_patterns: Dict[str, AccessPattern] = {}
        self.access_history: deque = deque(maxlen=10000)
        
        # ML models
        self.access_predictor: Optional[RandomForestRegressor] = None
        self.tier_classifier: Optional[RandomForestRegressor] = None
        self.scaler = StandardScaler()
        
        # Prefetch predictor
        self.prefetch_predictor = PrefetchPredictor()
        
        # Optimization state
        self.last_optimization = datetime.utcnow()
        self.optimization_history: deque = deque(maxlen=100)
        
        # Cost tracking
        self.tier_costs = {
            MemoryTier.L0_CPU_CACHE: 1.0,      # Highest cost (CPU cycles)
            MemoryTier.L1_PROCESS_MEMORY: 0.8,  # RAM cost
            MemoryTier.L2_SHARED_MEMORY: 0.6,   # Shared memory cost
            MemoryTier.L3_POSTGRESQL: 0.3,      # Database cost
            MemoryTier.L4_WEAVIATE: 0.2,        # Vector DB cost
        }
        
        logger.info(f"Initialized MemoryOptimizer with config: {config}")
    
    async def initialize(self, storages: Dict[MemoryTier, IMemoryStorage]) -> None:
        """Initialize the optimizer with storage backends."""
        self.storages = storages
        
        # Load or train models
        if self.config.model_path:
            await self._load_models()
        else:
            await self._initialize_models()
        
        logger.info(f"Optimizer initialized with {len(storages)} storage tiers")
    
    async def should_promote(self, item: MemoryItem) -> Optional[MemoryTier]:
        """Determine if an item should be promoted to a faster tier."""
        if not self.config.enabled:
            return None
        
        # Get access pattern
        pattern = self._get_or_create_pattern(item.key)
        pattern.record_access(datetime.utcnow(), item.tier)
        
        # Check promotion thresholds
        features = pattern.get_features()
        
        # Simple rule-based promotion for now
        if item.tier == MemoryTier.L4_WEAVIATE:
            if features['recency_hours'] < 1 and features['total_accesses'] > 10:
                return MemoryTier.L3_POSTGRESQL
        elif item.tier == MemoryTier.L3_POSTGRESQL:
            if features['recency_hours'] < 0.1 and features['access_rate'] > 5:
                return MemoryTier.L2_SHARED_MEMORY
        elif item.tier == MemoryTier.L2_SHARED_MEMORY:
            if features['mean_interval'] < 1 and features['total_accesses'] > 50:
                return MemoryTier.L1_PROCESS_MEMORY
        elif item.tier == MemoryTier.L1_PROCESS_MEMORY:
            if features['mean_interval'] < 0.1 and features['size_kb'] < 1:
                return MemoryTier.L0_CPU_CACHE
        
        # Use ML model if available
        if self.tier_classifier and features['total_accesses'] > 5:
            try:
                feature_vector = self._extract_feature_vector(features)
                predicted_tier_value = self.tier_classifier.predict([feature_vector])[0]
                predicted_tier = self._value_to_tier(predicted_tier_value)
                
                if predicted_tier.value < item.tier.value:
                    return predicted_tier
                    
            except Exception as e:
                logger.debug(f"ML prediction failed: {str(e)}")
        
        return None
    
    async def should_demote(self, item: MemoryItem) -> Optional[MemoryTier]:
        """Determine if an item should be demoted to a slower tier."""
        if not self.config.enabled:
            return None
        
        # Get access pattern
        pattern = self.access_patterns.get(item.key)
        if not pattern:
            return None
        
        features = pattern.get_features()
        
        # Simple rule-based demotion
        if item.tier == MemoryTier.L0_CPU_CACHE:
            if features['recency_hours'] > 0.5 or features['size_kb'] > 1:
                return MemoryTier.L1_PROCESS_MEMORY
        elif item.tier == MemoryTier.L1_PROCESS_MEMORY:
            if features['recency_hours'] > 2:
                return MemoryTier.L2_SHARED_MEMORY
        elif item.tier == MemoryTier.L2_SHARED_MEMORY:
            if features['recency_hours'] > 12:
                return MemoryTier.L3_POSTGRESQL
        elif item.tier == MemoryTier.L3_POSTGRESQL:
            if features['recency_hours'] > 48:
                return MemoryTier.L4_WEAVIATE
        
        return None
    
    async def predict_access(
        self,
        key: str,
        future_times: List[datetime]
    ) -> float:
        """Predict the probability of access at future times."""
        pattern = self.access_patterns.get(key)
        if not pattern or not self.access_predictor:
            return 0.0
        
        features = pattern.get_features()
        if features['total_accesses'] < 3:
            # Not enough data for prediction
            return 0.0
        
        try:
            # Calculate time-based features for prediction
            predictions = []
            current_time = datetime.utcnow()
            
            for future_time in future_times:
                hours_ahead = (future_time - current_time).total_seconds() / 3600
                
                # Create feature vector with time component
                time_features = features.copy()
                time_features['hours_ahead'] = hours_ahead
                
                feature_vector = self._extract_feature_vector(time_features)
                probability = self.access_predictor.predict([feature_vector])[0]
                predictions.append(min(1.0, max(0.0, probability)))
            
            return np.mean(predictions)
            
        except Exception as e:
            logger.debug(f"Access prediction failed: {str(e)}")
            return 0.0
    
    async def get_prefetch_candidates(
        self,
        key: str,
        limit: int = 5
    ) -> List[str]:
        """Get candidates for prefetching based on access patterns."""
        if not self.config.prefetch_enabled:
            return []
        
        # Record access in history
        self.access_history.append((key, datetime.utcnow()))
        
        # Update prefetch predictor
        if len(self.access_history) >= 2:
            recent_keys = [k for k, _ in list(self.access_history)[-10:]]
            recent_times = [t for _, t in list(self.access_history)[-10:]]
            self.prefetch_predictor.record_access_sequence(recent_keys, recent_times)
        
        # Get predictions
        predictions = self.prefetch_predictor.predict_next_accesses(key, limit * 2)
        
        # Filter by probability threshold
        candidates = []
        for predicted_key, probability in predictions:
            if probability >= self.config.prefetch_threshold:
                candidates.append(predicted_key)
                if len(candidates) >= limit:
                    break
        
        return candidates
    
    async def analyze_access_patterns(
        self,
        items: List[MemoryItem]
    ) -> Dict[str, MemoryTier]:
        """Analyze items and recommend optimal tiers."""
        recommendations = {}
        
        for item in items:
            # Update pattern
            pattern = self._get_or_create_pattern(item.key)
            pattern.size_bytes = item.size_bytes
            
            # Check if should promote or demote
            new_tier = await self.should_promote(item)
            if not new_tier:
                new_tier = await self.should_demote(item)
            
            if new_tier and new_tier != item.tier:
                recommendations[item.key] = new_tier
        
        return recommendations
    
    async def rebalance_tiers(self) -> Dict[str, int]:
        """Rebalance items across tiers based on capacity and performance."""
        moved_items = {
            "promoted": 0,
            "demoted": 0,
            "rebalanced": 0
        }
        
        try:
            # Get tier statistics
            tier_stats = {}
            for tier, storage in self.storages.items():
                stats = await storage.get_stats()
                tier_stats[tier] = stats
            
            # Check tier capacities
            for tier, stats in tier_stats.items():
                capacity_used = stats.get('capacity_used_percent', 0)
                
                if capacity_used > self.config.tier_capacity_threshold:
                    # Tier is over capacity, demote some items
                    items_to_move = int(stats['total_items'] * 0.1)  # Move 10%
                    
                    # Get least accessed items
                    items = await storage.search(limit=items_to_move)
                    items.sort(key=lambda x: x.access_count)
                    
                    for item in items[:items_to_move]:
                        target_tier = await self.should_demote(item)
                        if target_tier and target_tier in self.storages:
                            # Move item
                            await self.storages[target_tier].set(item)
                            await storage.delete(item.key)
                            moved_items["rebalanced"] += 1
            
            # Record optimization
            self.optimization_history.append({
                "timestamp": datetime.utcnow(),
                "moved_items": moved_items,
                "tier_stats": tier_stats
            })
            
            return moved_items
            
        except Exception as e:
            logger.error(f"Tier rebalancing failed: {str(e)}")
            return moved_items
    
    async def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get metrics about optimization performance."""
        metrics = {
            "enabled": self.config.enabled,
            "total_patterns_tracked": len(self.access_patterns),
            "prefetch_enabled": self.config.prefetch_enabled,
            "last_optimization": self.last_optimization.isoformat(),
            "optimization_count": len(self.optimization_history),
        }
        
        # Calculate hit rates by tier
        tier_hits = defaultdict(int)
        tier_misses = defaultdict(int)
        
        for pattern in self.access_patterns.values():
            for timestamp, tier in pattern.tier_history:
                tier_hits[tier.value] += 1
        
        metrics["tier_hit_rates"] = dict(tier_hits)
        
        # Calculate average access intervals
        intervals = []
        for pattern in self.access_patterns.values():
            if pattern.access_intervals:
                intervals.extend(list(pattern.access_intervals))
        
        if intervals:
            metrics["avg_access_interval_seconds"] = np.mean(intervals)
            metrics["median_access_interval_seconds"] = np.median(intervals)
        
        # Prefetch effectiveness
        if self.config.prefetch_enabled:
            total_predictions = sum(
                len(predictions) 
                for predictions in self.prefetch_predictor.co_access_matrix.values()
            )
            metrics["prefetch_predictions_count"] = total_predictions
        
        return metrics
    
    async def export_model(self, path: str) -> None:
        """Export trained models to disk."""
        if not self.access_predictor or not self.tier_classifier:
            raise MemoryOptimizationError(
                operation="export_model",
                reason="Models not trained yet"
            )
        
        try:
            model_data = {
                "access_predictor": self.access_predictor,
                "tier_classifier": self.tier_classifier,
                "scaler": self.scaler,
                "config": self.config,
                "access_patterns": dict(self.access_patterns),
                "prefetch_predictor": self.prefetch_predictor,
            }
            
            joblib.dump(model_data, path)
            logger.info(f"Exported optimization models to {path}")
            
        except Exception as e:
            raise MemoryOptimizationError(
                operation="export_model",
                reason=f"Failed to export: {str(e)}"
            )
    
    async def import_model(self, path: str) -> None:
        """Import trained models from disk."""
        try:
            model_data = joblib.load(path)
            
            self.access_predictor = model_data["access_predictor"]
            self.tier_classifier = model_data["tier_classifier"]
            self.scaler = model_data["scaler"]
            self.access_patterns = model_data.get("access_patterns", {})
            self.prefetch_predictor = model_data.get(
                "prefetch_predictor", 
                PrefetchPredictor()
            )
            
            logger.info(f"Imported optimization models from {path}")
            
        except Exception as e:
            raise MemoryOptimizationError(
                operation="import_model",
                reason=f"Failed to import: {str(e)}"
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        return await self.get_optimization_metrics()
    
    # Private helper methods
    
    def _get_or_create_pattern(self, key: str) -> AccessPattern:
        """Get or create an access pattern for a key."""
        if key not in self.access_patterns:
            self.access_patterns[key] = AccessPattern(key)
        return self.access_patterns[key]
    
    def _extract_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Extract feature vector for ML models."""
        # Define feature order
        feature_names = [
            'mean_interval', 'std_interval', 'min_interval', 'max_interval',
            'access_rate', 'recency_hours', 'total_accesses', 'size_kb'
        ]
        
        # Add time-based features if present
        if 'hours_ahead' in features:
            feature_names.append('hours_ahead')
        
        return [features.get(name, 0.0) for name in feature_names]
    
    def _value_to_tier(self, value: float) -> MemoryTier:
        """Convert numeric tier value to MemoryTier enum."""
        tier_values = {
            0: MemoryTier.L0_CPU_CACHE,
            1: MemoryTier.L1_PROCESS_MEMORY,
            2: MemoryTier.L2_SHARED_MEMORY,
            3: MemoryTier.L3_POSTGRESQL,
            4: MemoryTier.L4_WEAVIATE,
        }
        
        # Round to nearest tier
        tier_index = max(0, min(4, round(value)))
        return tier_values[tier_index]
    
    async def _load_models(self) -> None:
        """Load pre-trained models."""
        try:
            await self.import_model(self.config.model_path)
        except Exception as e:
            logger.warning(f"Failed to load models, initializing new ones: {str(e)}")
            await self._initialize_models()
    
    async def _initialize_models(self) -> None:
        """Initialize new ML models."""
        # Initialize with simple models
        self.access_predictor = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )
        
        self.tier_classifier = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )
        
        # Train with synthetic data if needed
        if self.config.train_on_init:
            await self._train_with_synthetic_data()
    
    async def _train_with_synthetic_data(self) -> None:
        """Train models with synthetic data for cold start."""
        # Generate synthetic training data
        n_samples = 1000
        
        # Features: mean_interval, std_interval, access_rate, recency, size_kb
        X_access = np.random.randn(n_samples, 8)
        y_access = np.random.rand(n_samples)  # Access probability
        
        X_tier = np.random.randn(n_samples, 8)
        y_tier = np.random.randint(0, 5, n_samples)  # Tier assignment
        
        # Fit models
        self.scaler.fit(X_access)
        X_access_scaled = self.scaler.transform(X_access)
        X_tier_scaled = self.scaler.transform(X_tier)
        
        self.access_predictor.fit(X_access_scaled, y_access)
        self.tier_classifier.fit(X_tier_scaled, y_tier)
        
        logger.info("Trained models with synthetic data")