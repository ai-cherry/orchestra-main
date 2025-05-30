"""
Base models for AI Orchestra agent orchestration system.

This module defines the base data models used throughout the agent orchestration system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """Memory item stored by agents."""

    id: str = Field(..., description="Unique identifier for this memory item")
    content: str = Field(..., description="Content of the memory")
    source: str = Field(..., description="Source of the memory (e.g., agent ID)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when memory was created",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the memory")
    priority: float = Field(default=0.5, description="Priority of the memory (0.0-1.0)")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding of the memory content")


class AgentMessage(BaseModel):
    """Message exchanged between agents."""

    content: str = Field(..., description="Content of the message")
    sender: str = Field(..., description="ID of the sender agent")
    recipient: str = Field(..., description="ID of the recipient agent")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when message was created",
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the message")
    message_id: Optional[str] = Field(default=None, description="Unique message identifier")
    parent_id: Optional[str] = Field(default=None, description="ID of parent message if this is a reply")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the message")


class PersonaTraits(BaseModel):
    """Traits that define a persona."""

    adaptability: int = Field(
        default=50,
        ge=0,
        le=100,
        description="Ability to adapt to new situations (0-100)",
    )
    creativity: int = Field(default=50, ge=0, le=100, description="Creativity level (0-100)")
    resilience: int = Field(default=50, ge=0, le=100, description="Resilience to challenges (0-100)")
    detail_orientation: int = Field(default=50, ge=0, le=100, description="Attention to detail (0-100)")
    social_awareness: int = Field(default=50, ge=0, le=100, description="Awareness of social dynamics (0-100)")
    technical_depth: int = Field(default=50, ge=0, le=100, description="Depth of technical knowledge (0-100)")
    leadership: int = Field(default=50, ge=0, le=100, description="Leadership capabilities (0-100)")
    analytical_thinking: int = Field(default=50, ge=0, le=100, description="Analytical thinking ability (0-100)")


class PersonaConfig(BaseModel):
    """Configuration for a persona."""

    id: str = Field(..., description="Unique identifier for this persona")
    name: str = Field(..., description="Name of the persona")
    description: str = Field(..., description="Description of the persona")
    traits: PersonaTraits = Field(default_factory=PersonaTraits, description="Traits that define this persona")
    system_prompt: str = Field(..., description="System prompt to use for this persona")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for this persona")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the persona was created",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the persona was last updated",
    )


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    id: str = Field(..., description="Unique identifier for this agent")
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent")
    role: str = Field(..., description="Role of the agent")
    persona_id: Optional[str] = Field(default=None, description="ID of the persona to use (if any)")
    capabilities: List[str] = Field(default_factory=list, description="Capabilities of this agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for this agent")
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the agent was created",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp when the agent was last updated",
    )
