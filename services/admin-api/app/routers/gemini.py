"""
Router for Gemini LLM-powered API endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.gemini import CommandRequest, CommandResponse
from app.services.gemini_service import get_gemini_service

router = APIRouter()


@router.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest, gemini_service=Depends(get_gemini_service)) -> CommandResponse:
    """
    Execute a natural language command using Gemini.

    This endpoint processes natural language instructions and executes them
    using Gemini's function calling capabilities.

    Args:
        request: The command request
        gemini_service: The Gemini service dependency

    Returns:
        CommandResponse: The result of the command execution

    Raises:
        HTTPException: If the command could not be processed
    """
    try:
        response = await gemini_service.process_command(request.command)
        return CommandResponse(
            response=response["response"],
            function_calls=response.get("function_calls", []),
            successful=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}")


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_content(request: Dict[str, Any], gemini_service=Depends(get_gemini_service)) -> Dict[str, Any]:
    """
    Analyze content (logs, metrics, etc.) using Gemini.

    Args:
        request: The analysis request containing the content to analyze
        gemini_service: The Gemini service dependency

    Returns:
        Dict[str, Any]: Analysis results

    Raises:
        HTTPException: If the analysis could not be performed
    """
    if "content" not in request:
        raise HTTPException(status_code=400, detail="Content field is required for analysis")

    try:
        analysis = await gemini_service.analyze_content(
            content=request["content"],
            context=request.get("context", {}),
            analysis_type=request.get("analysis_type", "general"),
        )
        return {"analysis": analysis, "successful": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing content: {str(e)}")


@router.get("/capabilities")
async def get_capabilities(
    gemini_service=Depends(get_gemini_service),
) -> Dict[str, Any]:
    """
    Get available Gemini capabilities and functions.

    Returns:
        Dict[str, Any]: Gemini capabilities info
    """
    return await gemini_service.get_capabilities()
