"""
Memory models for AI Orchestra.

This module defines the data models used by the memory system.
"""

import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MemoryType(Enum):
    """Types of memory available in the system."""

    SHORT_TERM = "short_term"  # Redis-based, fast access, limited retention
    MID_TERM = "mid_term"  # Firestore-based, structured data
    LONG_TERM = "long_term"  # Vector-based semantic search (Vertex AI)


class MemoryItem(BaseModel):
    """Base model for items stored in memory."""

    id: Optional[str] = None
    content: Any
    content_type: str = "text"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    memory_type: MemoryType = MemoryType.MID_TERM

    class Config:
        arbitrary_types_allowed = True


class ConversationMemoryItem(MemoryItem):
    """Memory item for conversation history."""

    conversation_id: str
    role: str  # "user", "assistant", "system", etc.
    content_type: str = "text"

    @classmethod
    def from_message(cls, conversation_id: str, role: str, content: str, **kwargs):
        """Create a memory item from a conversation message."""
        return cls(
            conversation_id=conversation_id,
            role=role,
            content=content,
            content_type="text",
            **kwargs
        )


class VectorMemoryItem(MemoryItem):
    """Memory item with vector embedding for semantic search."""

    embedding: Optional[List[float]] = None
    content_type: str = "text"

    @classmethod
    def from_text(cls, text: str, **kwargs):
        """Create a vector memory item from text."""
        return cls(content=text, content_type="text", **kwargs)


class MemorySearchResult(BaseModel):
    """Result of a memory search operation."""

    item: MemoryItem
    score: float = 0.0
    source: str = "unknown"
