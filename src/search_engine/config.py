"""
Search Engine Configuration
"""

# Default search settings
DEFAULT_SEARCH_SETTINGS = {
    "max_results": 50,
    "timeout_seconds": 30,
    "similarity_threshold": 0.7,
    "enable_caching": True,
    "cache_ttl_seconds": 3600
}

# Mode-specific settings
MODE_SETTINGS = {
    "normal": {
        "max_results": 20,
        "timeout_seconds": 10,
        "temperature": 0.5
    },
    "creative": {
        "max_results": 30,
        "timeout_seconds": 20,
        "temperature": 0.8
    },
    "deep": {
        "max_results": 50,
        "timeout_seconds": 60,
        "temperature": 0.5
    },
    "super_deep": {
        "max_results": 100,
        "timeout_seconds": 120,
        "temperature": 0.6
    },
    "uncensored": {
        "max_results": 100,
        "timeout_seconds": 30,
        "temperature": 0.7
    }
}
