"""
Request models for Orchestra AI API.

This module defines Pydantic models for API request validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

class ConversationRequest(BaseModel):
    """Request for conversation endpoint."""

    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    persona_id: Optional[str] = Field(default=None, description="Specific persona to use")

class WorkflowExecutionRequest(BaseModel):
    """Request for workflow execution."""

    workflow_name: str = Field(..., description="Name of workflow to execute")
    inputs: Dict[str, Any] = Field(..., description="Workflow inputs")
    async_execution: bool = Field(default=False, description="Execute asynchronously")

class AgentMessageRequest(BaseModel):
    """Request to send message to an agent."""

    agent_id: str = Field(..., description="Target agent ID")
    message: str = Field(..., description="Message content")
    message_type: str = Field(default="text", description="Type of message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class AgentTaskRequest(BaseModel):
    """Request to assign task to an agent."""

    task: str = Field(..., description="Task description")
    required_capability: str = Field(..., description="Required agent capability")
    priority: Optional[str] = Field(default="normal", description="Task priority")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Task context")

class MemoryStoreRequest(BaseModel):
    """Request to store data in memory."""

    key: str = Field(..., description="Storage key")
    value: Any = Field(..., description="Value to store")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    ttl_seconds: Optional[int] = Field(default=None, description="Time to live in seconds")

class MemorySearchRequest(BaseModel):
    """Request to search memory."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    metadata_filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")

class PersonaCreateRequest(BaseModel):
    """Request to create a new persona."""

    id: str = Field(..., description="Unique persona ID")
    name: str = Field(..., description="Persona name")
    description: str = Field(..., description="Persona description")
    traits: List[str] = Field(default_factory=list, description="Persona traits")
    style: str = Field(default="conversational", description="Response style")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(default=2000, ge=1, le=8000, description="Maximum tokens")

class LLMCompletionRequest(BaseModel):
    """Request for LLM completion."""

    prompt: str = Field(..., description="Input prompt")
    provider: Optional[str] = Field(default=None, description="Specific LLM provider")
    model: Optional[str] = Field(default=None, description="Specific model")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")
    temperature: Optional[float] = Field(default=None, description="Temperature")
    persona_id: Optional[str] = Field(default=None, description="Persona to use")

class DocumentAnalysisRequest(BaseModel):
    """Request for document analysis."""

    document_id: str = Field(..., description="Document ID")
    document: str = Field(..., description="Document content")
    analysis_types: List[str] = Field(
        default=["summary", "entities", "keywords"],
        description="Types of analysis to perform",
    )

class ResearchRequest(BaseModel):
    """Request for research task."""

    topic: str = Field(..., description="Research topic")
    depth: str = Field(default="standard", description="Research depth: shallow, standard, deep")
    max_sources: int = Field(default=5, ge=1, le=20, description="Maximum sources to consult")
    output_format: str = Field(default="detailed", description="Output format: summary, detailed, raw")
