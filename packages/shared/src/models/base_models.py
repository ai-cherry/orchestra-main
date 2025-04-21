"""
Base model definitions for the AI Orchestration System.

This module contains the core data models used throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# Note: Pydantic might need to be installed if not present
try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback to dataclasses if pydantic is not available
    from dataclasses import dataclass, field
    BaseModel = object
    
    def Field(*args, **kwargs):
        return field(default=None)


class PersonaConfig(BaseModel):
    """
    Configuration for a persona in the system.
    
    Personas shape how the orchestrator interacts with the user.
    """
    
    name: str
    description: str
    traits: Dict[str, float] = {}
    prompt_template: Optional[str] = None
    metadata: Dict[str, Any] = {}


class MemoryItem(BaseModel):
    """
    Represents a single memory item stored in the system.
    
    Memory items are the core storage unit for conversation history,
    user preferences, and other contextual information.
    """
    
    id: Optional[str] = None
    user_id: str
    session_id: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    item_type: str
    persona_active: Optional[str] = None
    text_content: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
    expiration: Optional[datetime] = None


class AgentData(BaseModel):
    """
    Represents data produced or consumed by an agent.
    
    Agent data can include intermediate processing results,
    state information, or other agent-specific data.
    """
    
    id: Optional[str] = None
    agent_id: str
    timestamp: datetime = datetime.utcnow()
    data_type: str
    content: Any
    metadata: Dict[str, Any] = {}
    expiration: Optional[datetime] = None
