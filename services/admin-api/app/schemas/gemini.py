"""
Schema models for Gemini LLM interactions.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class FunctionCall(BaseModel):
    """
    Schema for a function call made by Gemini.
    """

    name: str = Field(..., description="Name of the function called")
    arguments: Dict[str, Any] = Field(
        ..., description="Arguments passed to the function"
    )
    result: Optional[Any] = Field(None, description="Result of the function call")


class CommandRequest(BaseModel):
    """
    Schema for a natural language command request.
    """

    command: str = Field(
        ...,
        min_length=1,
        max_length=32768,
        description="Natural language command to execute",
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the command"
    )


class CommandResponse(BaseModel):
    """
    Schema for a natural language command response.
    """

    response: str = Field(..., description="Response message from Gemini")
    function_calls: List[FunctionCall] = Field(
        default_factory=list,
        description="List of function calls made during command execution",
    )
    successful: bool = Field(
        ..., description="Whether the command was executed successfully"
    )


class AnalysisRequest(BaseModel):
    """
    Schema for a content analysis request.
    """

    content: str = Field(
        ...,
        min_length=1,
        max_length=1000000,  # Generous limit for large log files
        description="Content to analyze",
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the analysis"
    )
    analysis_type: str = Field(
        "general",
        description="Type of analysis to perform (e.g., 'general', 'logs', 'metrics', 'memory')",
    )


class AnalysisResponse(BaseModel):
    """
    Schema for a content analysis response.
    """

    analysis: Dict[str, Any] = Field(..., description="Analysis results")
    successful: bool = Field(..., description="Whether the analysis was successful")
