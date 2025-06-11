"""
"""
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