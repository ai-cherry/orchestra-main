#!/usr/bin/env python3
"""
DragonflyDB configuration for MCP server memory system.

This module provides configuration for DragonflyDB connections with support for:
- Environment variable configuration
- Connection pooling with 200 connections
- Development mode with optional DB index
- Comprehensive logging
"""

import os
import sys
from typing import Dict, Any
from pathlib import Path

# Add parent directory to path to import dragonfly_config from root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from dragonfly_config import (
        DRAGONFLY_HOST,
        DRAGONFLY_PORT,
        DRAGONFLY_PASSWORD,
        DRAGONFLY_DB_INDEX,
        DRAGONFLY_CONNECTION_URI,
        log_dragonfly_config,
    )
except ImportError:
    # Fallback if root config not available
    DRAGONFLY_HOST = os.getenv("DRAGONFLY_HOST", "localhost")
    DRAGONFLY_PORT = int(os.getenv("DRAGONFLY_PORT", "6379"))
    DRAGONFLY_PASSWORD = os.getenv("DRAGONFLY_PASSWORD")
    DRAGONFLY_DB_INDEX = int(os.getenv("DRAGONFLY_DB_INDEX", "0"))
    DRAGONFLY_CONNECTION_URI = os.getenv("DRAGONFLY_CONNECTION_URI")
    
    def log_dragonfly_config():
        print("[DragonflyDB config loaded from: env]")
        print(f"  HOST: {'set' if DRAGONFLY_HOST else 'MISSING'}")
        print(f"  PORT: {DRAGONFLY_PORT}")
        print(f"  PASSWORD: {'set' if DRAGONFLY_PASSWORD else 'MISSING'}")
        print(f"  DB_INDEX: {DRAGONFLY_DB_INDEX}")
        print(f"  CONNECTION_URI: {'set' if DRAGONFLY_CONNECTION_URI else 'MISSING'}")


def get_dragonfly_config() -> Dict[str, Any]:
    """
    Get DragonflyDB configuration for Redis client.
    
    Returns:
        Dict containing Redis client configuration optimized for DragonflyDB
    """
    # Use connection URI if available, otherwise build from components
    if DRAGONFLY_CONNECTION_URI:
        redis_url = DRAGONFLY_CONNECTION_URI
    else:
        # Build connection URL
        auth_part = f":{DRAGONFLY_PASSWORD}@" if DRAGONFLY_PASSWORD else ""
        redis_url = f"redis://{auth_part}{DRAGONFLY_HOST}:{DRAGONFLY_PORT}/{DRAGONFLY_DB_INDEX}"
    
    config = {
        # Connection settings
        "redis_url": redis_url,
        "host": DRAGONFLY_HOST,
        "port": DRAGONFLY_PORT,
        "password": DRAGONFLY_PASSWORD,
        "db": DRAGONFLY_DB_INDEX,
        
        # Connection pool settings optimized for DragonflyDB
        "max_connections": 200,  # High connection pool for performance
        "min_connections": 10,   # Maintain minimum connections
        "connection_pool_kwargs": {
            "max_connections": 200,
            "socket_timeout": 5.0,
            "socket_connect_timeout": 5.0,
            "socket_keepalive": True,
            "socket_keepalive_options": {},
            "retry_on_timeout": True,
            "retry_on_error": [ConnectionError, TimeoutError],
            "health_check_interval": 30,
        },
        
        # DragonflyDB specific settings
        "decode_responses": True,
        "encoding": "utf-8",
        "encoding_errors": "strict",
        
        # Performance settings
        "single_connection_client": False,  # Use connection pooling
        "connection_pool_class": "redis.asyncio.BlockingConnectionPool",
        
        # Memory settings for DragonflyDB
        "maxmemory_policy": "allkeys-lru",
        "maxmemory_samples": 10,  # Higher sampling for better LRU accuracy
        
        # Persistence settings (DragonflyDB handles this internally)
        "save": "",  # Disable Redis save, DragonflyDB has its own persistence
        
        # Development mode support
        "is_dev_mode": DRAGONFLY_DB_INDEX == 1,
    }
    
    return config


def get_dragonfly_pool_config() -> Dict[str, Any]:
    """
    Get optimized connection pool configuration for DragonflyDB.
    
    Returns:
        Dict containing connection pool settings
    """
    return {
        "max_connections": 200,
        "min_idle_connections": 10,
        "max_idle_connections": 50,
        "idle_check_interval": 60,  # seconds
        "max_lifetime": 3600,  # 1 hour
        "retry_attempts": 3,
        "retry_delay": 0.1,  # seconds
        "retry_backoff": 2.0,  # exponential backoff multiplier
    }


def validate_dragonfly_config() -> bool:
    """
    Validate that required DragonflyDB configuration is present.
    
    Returns:
        bool: True if configuration is valid
    """
    if not DRAGONFLY_HOST:
        print("ERROR: DRAGONFLY_HOST is not configured")
        return False
    
    if DRAGONFLY_PORT <= 0 or DRAGONFLY_PORT > 65535:
        print(f"ERROR: Invalid DRAGONFLY_PORT: {DRAGONFLY_PORT}")
        return False
    
    # Password is optional but recommended
    if not DRAGONFLY_PASSWORD:
        print("WARNING: DRAGONFLY_PASSWORD is not set - connection is unprotected")
    
    # Log configuration (without exposing secrets)
    log_dragonfly_config()
    
    return True


# Export configuration
__all__ = [
    "get_dragonfly_config",
    "get_dragonfly_pool_config",
    "validate_dragonfly_config",
    "DRAGONFLY_HOST",
    "DRAGONFLY_PORT",
    "DRAGONFLY_DB_INDEX",
]