# TODO: Consider adding connection pooling configuration
"""
Cherry AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""
    """
    """
    request_id: str = Field(description="Unique identifier for the request")
    user_id: str = Field(description="Identifier for the user making the request")
    query: str = Field(description="The primary question or command from the user")
    source: str = Field(description="The channel or platform where the request originated")
    content: str = Field(description="Additional content or context for the request")
    status: str = Field(default="pending", description="Current processing status of the request")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the request was received")

class AgentResponse(BaseModel):
    """
    """
    response_id: str = Field(description="Unique identifier for this response")
    request_id: str = Field(description="Identifier linking back to the original request")
    agent_id: str = Field(description="Identifier for the agent that generated this response")
    content: str = Field(description="The actual response content")
    status: str = Field(default="completed", description="Processing status of the response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the response was generated")

class MemoryRecord(BaseModel):
    """
    """
    record_id: str = Field(description="Unique identifier for the memory record")
    context: str = Field(description="Contextual information about where/how this memory was formed")
    persona: str = Field(description="The persona associated with this memory (if applicable)")
    content: str = Field(description="The actual content of the memory")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the memory was created or last updated",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured data about the memory")

class WorkflowState(BaseModel):
    """
    """
    workflow_id: str = Field(description="Unique identifier for the workflow instance")
    state: str = Field(description="Current state descriptor for the workflow")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="State data being passed between workflow steps",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this workflow state was last updated",
    )

class PayReadyContact(BaseModel):
    """
    """
    contact_id: str = Field(description="Unique identifier for the contact")
    name: str = Field(description="Full name of the contact")
    email: str = Field(description="Email address of the contact")
    phone: str = Field(description="Phone number of the contact")
    address: str = Field(description="Physical address of the contact")
    company: str = Field(description="Associated company name")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this contact record was created or updated",
    )

class PayReadyLead(BaseModel):
    """
    """
    lead_id: str = Field(description="Unique identifier for the lead")
    name: str = Field(description="Full name of the lead")
    email: str = Field(description="Email address of the lead")
    phone: str = Field(description="Phone number of the lead")
    status: str = Field(default="new", description="Current status of the lead in the sales pipeline")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this lead record was created or updated",
    )

class Configuration(BaseModel):
    """
    """
    config_id: str = Field(description="Unique identifier for this configuration entry")
    key: str = Field(description="The configuration parameter name")
    value: str = Field(description="The configuration parameter value")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this configuration was last updated",
    )
