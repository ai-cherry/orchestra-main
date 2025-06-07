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
    """Base response model."""
    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(default=None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ConversationResponse(BaseResponse):
    """Response from conversation endpoint."""
    response: str = Field(..., description="AI response")
    intent: Optional[str] = Field(default=None, description="Detected intent")
    persona_used: Optional[str] = Field(default=None, description="Persona ID used")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for tracking")

class WorkflowExecutionResponse(BaseResponse):
    """Response from workflow execution."""
    workflow_id: UUID = Field(..., description="Workflow execution ID")
    workflow_name: str = Field(..., description="Workflow name")
    status: str = Field(..., description="Execution status")
    outputs: Optional[Dict[str, Any]] = Field(default=None, description="Workflow outputs")
    task_results: Optional[Dict[str, Any]] = Field(default=None, description="Individual task results")

class AgentResponse(BaseResponse):
    """Response from agent operations."""
    agent_id: str = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent name")
    status: str = Field(..., description="Agent status")
    result: Optional[Any] = Field(default=None, description="Operation result")

class AgentListResponse(BaseResponse):
    """Response listing agents."""
    agents: List[Dict[str, Any]] = Field(..., description="List of agents")
    total: int = Field(..., description="Total number of agents")

class MemoryResponse(BaseResponse):
    """Response from memory operations."""
    key: Optional[str] = Field(default=None, description="Memory key")
    value: Optional[Any] = Field(default=None, description="Stored value")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Search results")
    count: Optional[int] = Field(default=None, description="Number of results")

class PersonaResponse(BaseResponse):
    """Response from persona operations."""
    persona_id: str = Field(..., description="Persona ID")
    persona_name: str = Field(..., description="Persona name")
    persona_data: Optional[Dict[str, Any]] = Field(default=None, description="Persona configuration")

class PersonaListResponse(BaseResponse):
    """Response listing personas."""
    personas: List[Dict[str, Any]] = Field(..., description="List of personas")
    total: int = Field(..., description="Total number of personas")

class LLMCompletionResponse(BaseResponse):
    """Response from LLM completion."""
    text: str = Field(..., description="Generated text")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    latency_ms: float = Field(..., description="Response latency in milliseconds")

class DocumentAnalysisResponse(BaseResponse):
    """Response from document analysis."""
    document_id: str = Field(..., description="Document ID")
    summary: Optional[str] = Field(default=None, description="Document summary")
    entities: Optional[List[Dict[str, str]]] = Field(default=None, description="Extracted entities")
    keywords: Optional[List[str]] = Field(default=None, description="Generated keywords")
    workflow_id: Optional[UUID] = Field(default=None, description="Analysis workflow ID")

class ResearchResponse(BaseResponse):
    """Response from research task."""
    topic: str = Field(..., description="Research topic")
    synthesis: str = Field(..., description="Synthesized findings")
    queries: List[str] = Field(..., description="Research queries used")
    raw_findings: Optional[List[Dict[str, Any]]] = Field(default=None, description="Raw research data")
    depth: str = Field(..., description="Research depth used")

class HealthCheckResponse(BaseResponse):
    """Response from health check."""
    status: str = Field(..., description="System status")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Service health details")
    version: str = Field(..., description="API version")

class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
