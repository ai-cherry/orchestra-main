"""
"""
"""
"""
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,  # Will be loaded from Secret Manager in production
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "health_check_interval": 30,
    "max_connections": 20,
    "retry_on_timeout": True,
    "decode_responses": True,
    "maxmemory_policy": "allkeys-lru",
    "maxmemory_samples": 5,
    "timeout": 3600,
}

# mongodb configuration for warm memory tier
FIRESTORE_CONFIG: Dict[str, Any] = {
    "database": "memory-store",
    "collection": "memory_entries",
    "concurrency_mode": "OPTIMISTIC",
    "batch_size": 100,
    "max_batch_size": 500,
    "max_concurrent_operations": 10,
    "retry_attempts": 3,
    "retry_delay": 1.0,
}

# AlloyDB configuration for cold memory tier
ALLOYDB_CONFIG: Dict[str, Any] = {
    "host": "localhost",
    "port": 5432,
    "database": "memory_cold_storage",
    "user": "memory-admin",
    "password": None,  # Will be loaded from Secret Manager in production
    "min_connections": 1,
    "max_connections": 10,
    "connection_timeout": 5,
    "idle_timeout": 300,
    "retry_attempts": 3,
    "retry_delay": 1.0,
}

# Memory tier configuration
MEMORY_TIER_CONFIG: Dict[str, Any] = {
    "hot": {
        "storage_type": "redis",
        "config": REDIS_CONFIG,
        "ttl_seconds": 3600,  # 1 hour
        "max_size_bytes": 1024 * 1024 * 1024,  # 1 GB
        "priority_threshold": 8,  # Priority 8-10 goes to hot tier
    },
    "warm": {
        "storage_type": "mongodb",
        "config": FIRESTORE_CONFIG,
        "ttl_seconds": 86400,  # 1 day
        "max_size_bytes": 10 * 1024 * 1024 * 1024,  # 10 GB
        "priority_threshold": 5,  # Priority 5-7 goes to warm tier
    },
    "cold": {
        "storage_type": "alloydb",
        "config": ALLOYDB_CONFIG,
        "ttl_seconds": 2592000,  # 30 days
        "max_size_bytes": 100 * 1024 * 1024 * 1024,  # 100 GB
        "priority_threshold": 1,  # Priority 1-4 goes to cold tier
    },
}

# Compression configuration
COMPRESSION_CONFIG: Dict[str, Any] = {
    "text_threshold": 1000,  # Characters
    "json_threshold": 500,  # Characters
    "vector_quantization": True,
    "quantization_bits": 8,
    "levels": {
        "NONE": {
            "priority_threshold": 9,  # Priority 9-10 uses no compression
        },
        "LIGHT": {
            "priority_threshold": 7,  # Priority 7-8 uses light compression
            "text_ratio": 0.9,  # Keep 90% of text
            "json_fields_keep": 0.8,  # Keep 80% of JSON fields
        },
        "MEDIUM": {
            "priority_threshold": 5,  # Priority 5-6 uses medium compression
            "text_ratio": 0.7,  # Keep 70% of text
            "json_fields_keep": 0.6,  # Keep 60% of JSON fields
        },
        "HIGH": {
            "priority_threshold": 3,  # Priority 3-4 uses high compression
            "text_ratio": 0.5,  # Keep 50% of text
            "json_fields_keep": 0.4,  # Keep 40% of JSON fields
        },
        "EXTREME": {
            "priority_threshold": 2,  # Priority 2 uses extreme compression
            "text_ratio": 0.3,  # Keep 30% of text
            "json_fields_keep": 0.2,  # Keep 20% of JSON fields
        },
        "REFERENCE_ONLY": {
            "priority_threshold": 1,  # Priority 1 uses reference-only compression
            "text_ratio": 0.1,  # Keep 10% of text
            "json_fields_keep": 0.1,  # Keep 10% of JSON fields
        },
    },
}

# Token budget configuration
TOKEN_BUDGET_CONFIG: Dict[str, Any] = {
    "copilot": 5000,
    "gemini": 200000,
    "claude": 100000,
    "gpt4": 128000,
    "default": 10000,
}

# Performance optimization configuration
PERFORMANCE_CONFIG: Dict[str, Any] = {
    "cache_size": 10000,  # Maximum number of entries in memory cache
    "prefetch_enabled": True,
    "prefetch_threshold": 0.8,  # Prefetch when context relevance > 0.8
    "batch_size": 100,
    "parallel_operations": 10,
    "compression_threshold": 1000,  # Characters
    "deduplication_enabled": True,
    "vector_search_top_k": 20,
    "context_window_buffer": 0.1,  # 10% buffer for context window
}

# Environment-specific configuration
ENV_CONFIG: Dict[str, Dict[str, Any]] = {
    "dev": {
        "redis_host": "localhost",
        "firestore_emulator_host": "localhost:8080",
        "alloydb_host": "localhost",
    },
    "staging": {
        "redis_host": "10.0.0.1",
        "firestore_emulator_host": None,
        "alloydb_host": "10.0.0.2",
    },
    "prod": {
        "redis_host": "10.0.1.1",
        "firestore_emulator_host": None,
        "alloydb_host": "10.0.1.2",
    },
}
