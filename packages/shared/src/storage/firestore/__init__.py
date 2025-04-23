"""
Firestore storage implementations for the AI Orchestration System.

This module provides Firestore-based implementations for persistent
data storage and retrieval.
"""

from .firestore_memory import FirestoreMemoryManager

__all__ = ["FirestoreMemoryManager"]
