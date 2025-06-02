"""
Core interfaces for the data ingestion system.

These interfaces define the contracts that all implementations must follow,
ensuring modularity and hot-swappability of components.
"""

from .parser import ParserInterface, ParsedData
from .storage import StorageInterface, StorageResult
from .processor import ProcessorInterface, ProcessingResult

__all__ = [
    "ParserInterface",
    "ParsedData",
    "StorageInterface", 
    "StorageResult",
    "ProcessorInterface",
    "ProcessingResult",
]