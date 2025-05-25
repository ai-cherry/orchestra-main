"""
Endpoints for user interactions with the orchestration system.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from orchestrator.agents.agent_registry import get_agent, get_all_agents

router = APIRouter(tags=["interaction"])


class InteractionRequest(BaseModel):
    """Model for an interaction request."""

    text: str = Field(..., description="The input text from the user")
    agent_id: Optional[str] = Field(
        None, description="Specific agent ID to target, or None for default"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context for the interaction"
    )


class InteractionResponse(BaseModel):
    """Model for an interaction response."""

    response: str = Field(..., description="The response text")
    agent_id: Optional[str] = Field(
        None, description="ID of the agent that generated the response"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


@router.post("/interact", response_model=InteractionResponse)
async def interact(request: InteractionRequest):
    """
    Process a user interaction and generate a response.

    Args:
        request: The interaction request

    Returns:
        An interaction response

    Raises:
        HTTPException: If the requested agent is not found
    """
    agent_id = request.agent_id

    # If no specific agent is requested, use the first available one
    if not agent_id:
        agents = get_all_agents()
        if not agents:
            return InteractionResponse(
                response="No agents are currently available. Please try again later.",
                agent_id=None,
            )
        agent = agents[0]
    else:
        # Get the specified agent
        agent = get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    try:
        # Process the input with the selected agent
        response = await agent.process(request.text, context=request.context)

        return InteractionResponse(
            response=response, agent_id=agent.id, metadata={"agent_name": agent.name}
        )

    except Exception as e:
        # Handle any errors during processing
        return InteractionResponse(
            response=f"An error occurred while processing your request: {str(e)}",
            agent_id=agent.id if agent else None,
            metadata={"error": str(e)},
        )
