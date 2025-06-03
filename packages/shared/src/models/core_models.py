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
    """
    """
    name: str = Field(description="The name of the persona")
    age: int = Field(description="The age of the persona")
    background: str = Field(description="Background information about the persona")
    traits: Dict[str, Any] = Field(
        description="Dictionary of traits with associated values (e.g., {'sarcasm': 50, 'strategy': 80})"
    )
    interaction_style: str = Field(description="Style of interaction (e.g., 'playful', 'logical', 'assertive')")
    voice_description: Optional[str] = Field(
        default=None,
        description="Description of the persona's voice for potential text-to-speech use",
    )

class UserInteraction(BaseModel):
    """
    """
    interaction_id: str = Field(description="Unique identifier for the interaction, possibly a UUID")
    user_id: str = Field(description="Identifier for the user, likely 'Patrick'")
    session_id: Optional[str] = Field(default=None, description="Optional identifier for the session")
    input_text: str = Field(description="The text input by the user")
    active_persona: str = Field(description="Name of the persona used for this interaction")
    response_text: Optional[str] = Field(default=None, description="The system's response to the user input")
    timestamp_utc: datetime = Field(description="When the interaction occurred (in UTC)")
    feedback: Optional[int] = Field(
        default=None,
        description="Optional user feedback (e.g., 1 for thumbs up, -1 for thumbs down)",
    )

class AgentData(BaseModel):
    """
    """
    data_id: str = Field(description="Unique identifier for the data, possibly a UUID")
    source_agent: str = Field(description="Name of the agent that generated this data")
    data_type: str = Field(
        description="Type of data (e.g., 'research_finding', 'deduplicated_contact', 'stock_analysis')"
    )
    content: Dict[str, Any] = Field(description="The actual data payload as a dictionary")
    timestamp_utc: datetime = Field(description="When the data was generated (in UTC)")
    context_tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags for categorization (e.g., ['PayReady', 'ClinicalTrial', 'Stage3'])",
    )
