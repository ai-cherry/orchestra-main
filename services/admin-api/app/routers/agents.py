"""
Router for agent management API endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.admin_functions import (
    get_agent_status,
    start_agent,
    stop_agent,
    list_agents,
)

router = APIRouter()


@router.get("/")
async def get_all_agents(
    status: Optional[str] = Query("all", description="Filter agents by status", enum=["running", "stopped", "all"])
) -> Dict[str, Any]:
    """
    Get a list of all agents, optionally filtered by status.

    Args:
        status: Filter by agent status (running, stopped, all)

    Returns:
        Dict[str, Any]: List of agents
    """
    return await list_agents(status=status)


@router.get("/{agent_id}")
async def get_agent_details(agent_id: str) -> Dict[str, Any]:
    """
    Get details for a specific agent.

    Args:
        agent_id: ID of the agent

    Returns:
        Dict[str, Any]: Agent details
    """
    result = await get_agent_status(agent_id=agent_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{agent_id}/start")
async def start_agent_endpoint(agent_id: str) -> Dict[str, Any]:
    """
    Start a specific agent.

    Args:
        agent_id: ID of the agent to start

    Returns:
        Dict[str, Any]: Result of the operation
    """
    result = await start_agent(agent_id=agent_id)
    if not result.get("success", False):
        status_code = 404 if "not found" in result.get("error", "") else 500
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))
    return result


@router.post("/{agent_id}/stop")
async def stop_agent_endpoint(agent_id: str) -> Dict[str, Any]:
    """
    Stop a running agent.

    Args:
        agent_id: ID of the agent to stop

    Returns:
        Dict[str, Any]: Result of the operation
    """
    result = await stop_agent(agent_id=agent_id)
    if not result.get("success", False):
        status_code = 404 if "not found" in result.get("error", "") else 500
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))
    return result
