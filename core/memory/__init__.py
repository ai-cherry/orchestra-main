"""
Orchestra AI Memory System

A high-performance, unified memory management system following SOLID principles
and clean architecture patterns.

This module provides:
- Unified memory interface with multiple storage tiers
- Automatic tier optimization based on access patterns
- Predictive prefetching for optimal performance
- Comprehensive error handling and recovery
- Full observability and monitoring

Author: Orchestra AI Team
Version: 1.0.0
"""

from .interfaces import (
    IMemoryStorage,
    IMemoryManager,
    IMemoryOptimizer,
    IMemoryMetrics,
    MemoryTier,
    MemoryItem,
    MemoryOperation,
    MemoryResult,
)

from .implementations import (
    UnifiedMemoryManager,
    MemoryStorageFactory,
    MemoryOptimizer,
    MemoryMetricsCollector,
)

from .exceptions import (
    MemoryException,
    MemoryNotFoundError,
    MemoryStorageError,
    MemoryTierError,
    MemoryOptimizationError,
)

__all__ = [
    # Interfaces
    "IMemoryStorage",
    "IMemoryManager",
    "IMemoryOptimizer",
    "IMemoryMetrics",
    
    # Data Models
    "MemoryTier",
    "MemoryItem",
    "MemoryOperation",
    "MemoryResult",
    
    # Implementations
    "UnifiedMemoryManager",
    "MemoryStorageFactory",
    "MemoryOptimizer",
    "MemoryMetricsCollector",
    
    # Exceptions
    "MemoryException",
    "MemoryNotFoundError",
    "MemoryStorageError",
    "MemoryTierError",
    "MemoryOptimizationError",
]

# Version information
__version__ = "1.0.0"
__author__ = "Orchestra AI Team"
__license__ = "MIT"