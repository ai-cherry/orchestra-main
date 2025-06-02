"""
Advanced deduplication system for multi-channel data ingestion.

This module provides intelligent duplicate detection and resolution
across all data sources and upload methods.
"""

from .deduplication_engine import DeduplicationEngine
from .duplicate_resolver import DuplicateResolver
from .audit_logger import DeduplicationAuditLogger

__all__ = [
    "DeduplicationEngine",
    "DuplicateResolver",
    "DeduplicationAuditLogger",
]