"""
Base data models for the orchestration system.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """Base model for memory items stored by agents and personas."""

    id: str = Field(description="Unique identifier for the memory item")
    content: str = Field(description="The content of the memory")
    timestamp: float = Field(description="When the memory was created/modified")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AgentData(BaseModel):
    """Data model for agent configuration and state."""

    id: str = Field(description="Unique identifier for the agent")
    name: str = Field(description="Human-readable name for the agent")
    description: Optional[str] = Field(
        None, description="Optional description of the agent's purpose"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="List of agent capabilities"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )


class PersonaConfig(BaseModel):
    """Configuration for a persona used by agents."""

    id: str = Field(description="Unique identifier for the persona")
    name: str = Field(description="Human-readable name for the persona")
    description: str = Field(
        description="Description of the persona's personality and behavior"
    )
    traits: Dict[str, Any] = Field(
        default_factory=dict, description="Personality traits"
    )
    system_prompt: Optional[str] = Field(
        None, description="System prompt to define the persona"
    )
    knowledge_base: Optional[str] = Field(
        None, description="Optional reference to a knowledge base"
    )
