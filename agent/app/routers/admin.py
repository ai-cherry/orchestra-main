"""Admin API endpoints for the Admin UI."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from agent.app.services.real_agents import get_all_agents, get_system_metrics, run_agent_task

router = APIRouter(prefix="/api", tags=["admin"])


# Simple API key authentication
def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Verify API key authentication."""
    expected_key = "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


class Agent(BaseModel):
    """Agent model for the UI."""

    id: str
    name: str
    type: str
    status: str
    lastRun: str
    description: str = ""
    memory_usage: float = 0.0
    tasks_completed: int = 0
    current_task: Optional[str] = None


class QueryRequest(BaseModel):
    """Query request model."""

    query: str


class QueryResponse(BaseModel):
    """Query response model."""

    response: str
    agent_id: str
    timestamp: str
    tokens_used: int = 0


@router.get("/agents", response_model=List[Agent])
async def get_agents(api_key: str = Depends(verify_api_key)) -> List[Agent]:
    """Get list of all agents - REAL agents doing REAL work."""
    # Get actual agents from the real agent service
    agents_data = await get_all_agents()

    # Convert to API model
    return [Agent(**agent_data) for agent_data in agents_data]


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, api_key: str = Depends(verify_api_key)) -> QueryResponse:
    """Process a query through the orchestrator - actually run tasks on agents."""
    from datetime import datetime

    # Determine which agent should handle this query
    query_lower = request.query.lower()

    if "cpu" in query_lower or "memory" in query_lower or "disk" in query_lower or "system" in query_lower:
        agent_id = "sys-001"
    elif "analyze" in query_lower or "count" in query_lower or "data" in query_lower:
        agent_id = "analyze-001"
    elif "check" in query_lower or "monitor" in query_lower or "alert" in query_lower:
        agent_id = "monitor-001"
    else:
        # Default to system agent
        agent_id = "sys-001"

    try:
        # Actually run the task on the agent
        result = await run_agent_task(agent_id, request.query)
        response_text = result["result"]
    except Exception as e:
        response_text = f"Error processing query: {str(e)}"
        agent_id = "error"

    return QueryResponse(
        response=response_text,
        agent_id=agent_id,
        timestamp=datetime.now().isoformat(),
        tokens_used=len(request.query.split()) * 3,  # Rough estimate
    )


@router.post("/upload")
async def upload_file(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """Handle file uploads."""
    # Placeholder for file upload functionality
    return {
        "status": "success",
        "message": "File upload endpoint ready",
        "supported_formats": ["txt", "pdf", "json", "csv"],
        "max_size": "10MB",
    }


@router.get("/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """Get REAL system metrics from the ACTUAL running system."""
    # Get real metrics from the system
    return await get_system_metrics()
