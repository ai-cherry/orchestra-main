"""
Data Ingestion System for Orchestra Platform

This module provides a comprehensive system for ingesting, processing, and querying
data from multiple enterprise sources including Slack, Gong.io, Salesforce, 
Looker, and HubSpot.

Key Components:
- Parser interfaces for hot-swappable source-specific parsers
- Storage adapters for PostgreSQL, Weaviate, and S3
- Processing pipeline with vector embedding
- Query engine with cross-source search capabilities
"""

from typing import Dict, Any

__version__ = "1.0.0"

# Module configuration
CONFIG: Dict[str, Any] = {
    "supported_sources": ["slack", "gong", "salesforce", "looker", "hubspot"],
    "max_file_size_mb": 500,
    "batch_size": 100,
    "vector_dimensions": 1536,
    "cache_ttl_hours": 1,
}

# Export key classes and functions
from .interfaces.parser import ParserInterface
from .interfaces.storage import StorageInterface
from .interfaces.processor import ProcessorInterface

__all__ = [
    "ParserInterface",
    "StorageInterface", 
    "ProcessorInterface",
    "CONFIG",
]