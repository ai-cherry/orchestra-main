"""
Agent management API router for CRUD, bulk actions, and status.
Implements endpoints for listing, creating, updating, deleting, and bulk operations on agents.
"""

from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory agent store (replace with DB in production)
AGENT_STORE = {}


class AgentStatus(str):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AgentBase(BaseModel):
    name: str = Field(..., example="Content Creator")
    description: str = Field(..., example="Creates high-quality content")
    type: str = Field(..., example="content")


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    type: Optional[str]
    status: Optional[Literal["active", "inactive"]]


class Agent(AgentBase):
    id: str
    status: Literal["active", "inactive"]
    last_active: str
    conversations: int
    avg_response_time: str


@router.get("/", response_model=List[Agent])
def list_agents(
    search: Optional[str] = Query(None, description="Search by name or description"),
    status: Optional[Literal["active", "inactive", "all"]] = Query("all"),
    skip: int = 0,
    limit: int = 20,
):
    """
    List agents with optional search, status filter, and pagination.
    """
    agents = list(AGENT_STORE.values())
    if search:
        agents = [
            a
            for a in agents
            if search.lower() in a["name"].lower()
            or search.lower() in a["description"].lower()
        ]
    if status and status != "all":
        agents = [a for a in agents if a["status"] == status]
    return agents[skip : skip + limit]


@router.post("/", response_model=Agent)
def create_agent(agent: AgentCreate):
    """
    Create a new agent with validation.
    """
    # Example validation: name must be unique
    if any(a["name"].lower() == agent.name.lower() for a in AGENT_STORE.values()):
        raise HTTPException(status_code=400, detail="Agent name must be unique.")
    agent_id = str(uuid4())
    new_agent = {
        "id": agent_id,
        "name": agent.name,
        "description": agent.description,
        "type": agent.type,
        "status": AgentStatus.ACTIVE,
        "last_active": "never",
        "conversations": 0,
        "avg_response_time": "N/A",
    }
    AGENT_STORE[agent_id] = new_agent
    return new_agent


@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    """
    Get agent by ID.
    """
    agent = AGENT_STORE.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return agent


@router.put("/{agent_id}", response_model=Agent)
def update_agent(agent_id: str, update: AgentUpdate):
    """
    Update agent fields.
    """
    agent = AGENT_STORE.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    agent.update({k: v for k, v in update.dict(exclude_unset=True).items()})
    AGENT_STORE[agent_id] = agent
    return agent


@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    """
    Delete agent by ID.
    """
    if agent_id not in AGENT_STORE:
        raise HTTPException(status_code=404, detail="Agent not found.")
    del AGENT_STORE[agent_id]
    return {"detail": "Agent deleted."}


class BulkActionRequest(BaseModel):
    agent_ids: List[str]
    action: Literal["activate", "deactivate", "delete"]


@router.post("/bulk", response_model=dict)
def bulk_action(request: BulkActionRequest):
    """
    Perform bulk actions (activate, deactivate, delete) on agents.
    """
    updated = []
    for agent_id in request.agent_ids:
        agent = AGENT_STORE.get(agent_id)
        if not agent:
            continue
        if request.action == "activate":
            agent["status"] = AgentStatus.ACTIVE
        elif request.action == "deactivate":
            agent["status"] = AgentStatus.INACTIVE
        elif request.action == "delete":
            del AGENT_STORE[agent_id]
            continue
        AGENT_STORE[agent_id] = agent
        updated.append(agent_id)
    return {"updated": updated, "action": request.action}


@router.post("/validate", response_model=dict)
def validate_agent(agent: AgentCreate):
    """
    Validate agent configuration (e.g., name uniqueness).
    """
    if any(a["name"].lower() == agent.name.lower() for a in AGENT_STORE.values()):
        return {"valid": False, "reason": "Agent name must be unique."}
    return {"valid": True}


@router.post("/test", response_model=dict)
def test_agent(agent: AgentCreate):
    """
    Test agent configuration (mock implementation).
    """
    # In real implementation, test API keys, endpoints, etc.
    return {"success": True, "message": "Agent configuration test passed."}


@router.get("/{agent_id}/status", response_model=dict)
def agent_status(agent_id: str):
    """
    Get real-time status/health of an agent (mock).
    """
    agent = AGENT_STORE.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    # In real implementation, check agent process/heartbeat/logs
    return {"status": agent["status"], "last_active": agent["last_active"]}
