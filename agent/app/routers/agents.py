from fastapi import APIRouter, HTTPException
from agent.app.services.agent_control import (
    get_agent_logs, restart_agent, get_agent_config, update_agent_config, get_agent_metrics
)

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("/{agent_id}/logs")
async def api_get_agent_logs(agent_id: str):
    """Get logs for a specific agent."""
    return get_agent_logs(agent_id)

@router.post("/{agent_id}/restart")
async def api_restart_agent(agent_id: str):
    """Restart a specific agent process."""
    return restart_agent(agent_id)

@router.get("/{agent_id}/config")
async def api_get_agent_config(agent_id: str):
    """Get agent configuration."""
    return get_agent_config(agent_id)

@router.put("/{agent_id}/config")
async def api_update_agent_config(agent_id: str, config: dict):
    """Update agent configuration."""
    return update_agent_config(agent_id, config)

@router.get("/{agent_id}/metrics")
async def api_get_agent_metrics(agent_id: str):
    """Get real-time metrics for a specific agent."""
    return get_agent_metrics(agent_id) 