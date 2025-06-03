# TODO: Consider adding connection pooling configuration
"""
Orchestra AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""
    """Types of memory available in the system."""
    SHORT_TERM = "short_term"  # Redis-based, fast access, limited retention
    MID_TERM = "mid_term"  # Firestore-based, structured data
    LONG_TERM = "long_term"  # Vector-based semantic search (Vertex AI)

class MemoryItem(BaseModel):
    """Base model for items stored in memory."""
    content_type: str = "text"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    memory_type: MemoryType = MemoryType.MID_TERM

    class Config:
        arbitrary_types_allowed = True

class ConversationMemoryItem(MemoryItem):
    """Memory item for conversation history."""
    role: str  # "user", "assistant", "system", etc.
    content_type: str = "text"

    @classmethod
    def from_message(cls, conversation_id: str, role: str, content: str, **kwargs):
        """Create a memory item from a conversation message."""
        return cls(conversation_id=conversation_id, role=role, content=content, content_type="text", **kwargs)

class VectorMemoryItem(MemoryItem):
    """Memory item with vector embedding for semantic search."""
    content_type: str = "text"

    @classmethod
    def from_text(cls, text: str, **kwargs):
        """Create a vector memory item from text."""
        return cls(content=text, content_type="text", **kwargs)

class MemorySearchResult(BaseModel):
    """Result of a memory search operation."""
    source: str = "unknown"
