# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        raise ValueError(f"Unsupported storage type: {storage_type}")
    return adapter_class

__all__ = [
    "PostgresAdapter",
    "WeaviateAdapter",
    "get_storage_adapter",
    "STORAGE_REGISTRY",
]