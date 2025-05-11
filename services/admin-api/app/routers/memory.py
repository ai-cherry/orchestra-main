"""
Router for memory management API endpoints.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body

from app.services.admin_functions import (
    get_memory_stats,
    prune_memory,
    promote_memory
)

router = APIRouter()


@router.get("/stats/{agent_id}")
async def get_agent_memory_stats(
    agent_id: str = Path(..., description="ID of the agent to get memory stats for")
) -> Dict[str, Any]:
    """
    Get memory statistics for a specific agent.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        Dict[str, Any]: Memory statistics
    """
    result = await get_memory_stats(agent_id=agent_id)
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@router.post("/prune/{agent_id}")
async def prune_agent_memory(
    agent_id: str = Path(..., description="ID of the agent to prune memory for"),
    older_than_days: int = Query(..., description="Prune memories older than this many days", ge=1)
) -> Dict[str, Any]:
    """
    Prune old memories for a specific agent.
    
    Args:
        agent_id: ID of the agent
        older_than_days: Prune memories older than this many days
        
    Returns:
        Dict[str, Any]: Result of the pruning operation
    """
    result = await prune_memory(agent_id=agent_id, older_than_days=older_than_days)
    if not result.get("success", False):
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    return result


@router.post("/promote/{memory_id}")
async def promote_memory_endpoint(
    memory_id: str = Path(..., description="ID of the memory to promote"),
    tier: str = Query(
        ...,
        description="Target tier to promote to",
        enum=["working", "long_term", "core"]
    )
) -> Dict[str, Any]:
    """
    Promote a memory to a higher tier.
    
    Args:
        memory_id: ID of the memory
        tier: Target tier to promote to
        
    Returns:
        Dict[str, Any]: Result of the promotion operation
    """
    result = await promote_memory(memory_id=memory_id, tier=tier)
    if not result.get("success", False):
        status_code = 404 if "not found" in result.get("error", "") else 500
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))
    return result