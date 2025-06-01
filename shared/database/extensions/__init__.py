"""
Database extensions for the unified PostgreSQL architecture.

This module provides mixins and extensions that add missing functionality
to the core database classes without modifying the original implementation.
"""

from .cache_extensions import CacheExtensionsMixin
from .session_extensions import SessionExtensionsMixin
from .memory_extensions import MemoryExtensionsMixin
from .pool_extensions import PoolExtensionsMixin

__all__ = [
    'CacheExtensionsMixin',
    'SessionExtensionsMixin', 
    'MemoryExtensionsMixin',
    'PoolExtensionsMixin'
]