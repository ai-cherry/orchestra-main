"""
AI Collaboration API Package
FastAPI endpoints for the AI Collaboration Dashboard
"""

from .endpoints import router, ws_manager, get_service

__all__ = [
    "router",
    "ws_manager",
    "get_service"
]