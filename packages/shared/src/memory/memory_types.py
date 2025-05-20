"""
Type definitions for the memory management system.

This module contains shared type definitions used across memory management components.
"""

from typing import Any, Dict, Optional, TypedDict


class MemoryHealth(TypedDict, total=False):
    """Type definition for memory system health status."""

    status: str  # 'healthy', 'degraded', or 'unhealthy'
    firestore: bool  # Firestore connection status
    redis: bool  # Redis connection status
    error_count: int  # Number of recent errors
    last_error: Optional[str]  # Last error message or timestamp
    details: Dict[str, Any]  # Additional details about the health status
