"""
Pydantic models for the AI Orchestra API.

This module defines the data models used for request/response validation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    version: str
    environment: str
    gcp_project: str


class ModelType(str, Enum):
    """Supported model types."""
    
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"
    AUDIO = "audio"


class VertexModel(BaseModel):
    """Vertex AI model information."""
    
    id: str
    display_name: str
    model_type: ModelType
    version: Optional[str] = None
    description: Optional[str] = None


class VertexPredictionRequest(BaseModel):
    """Request model for Vertex AI predictions."""
    
    model_id: str = Field(..., description="The ID of the model to use for prediction")
    instances: List[Dict[str, Any]] = Field(
        ..., description="The instances to predict"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Additional parameters for the prediction"
    )


class VertexPredictionResponse(BaseModel):
    """Response model for Vertex AI predictions."""
    
    model_id: str
    predictions: List[Dict[str, Any]]
    deployed_model_id: Optional[str] = None
    model_version_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GeminiRequest(BaseModel):
    """Request model for Gemini API."""
    
    prompt: str = Field(..., description="The prompt to send to Gemini")
    max_tokens: Optional[int] = Field(
        1024, description="Maximum number of tokens to generate"
    )
    temperature: Optional[float] = Field(
        0.7, description="Temperature for text generation"
    )
    top_p: Optional[float] = Field(
        0.95, description="Top-p sampling parameter"
    )
    top_k: Optional[int] = Field(
        40, description="Top-k sampling parameter"
    )


class GeminiResponse(BaseModel):
    """Response model for Gemini API."""
    
    text: str
    usage: Dict[str, int]
    model: str
    finish_reason: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str
    code: Optional[str] = None
    path: Optional[str] = None


class ModelListResponse(BaseModel):
    """Response model for listing available models."""
    
    models: List[VertexModel]
    total_count: int


class OrchestrationRequest(BaseModel):
    """Request model for AI orchestration."""
    
    workflow_id: str = Field(..., description="The ID of the workflow to execute")
    input_data: Dict[str, Any] = Field(
        ..., description="Input data for the workflow"
    )
    config: Optional[Dict[str, Any]] = Field(
        None, description="Configuration for the workflow"
    )


class OrchestrationResponse(BaseModel):
    """Response model for AI orchestration."""
    
    workflow_id: str
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    
    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None