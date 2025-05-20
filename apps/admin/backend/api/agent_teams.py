from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uuid

router = APIRouter()

# In-memory storage for demo purposes
agent_teams_db: Dict[str, Dict] = {}


class AgentTeamCreate(BaseModel):
    name: str
    agents: List[str]


class AgentTeam(BaseModel):
    id: str
    name: str
    agents: List[str]


@router.post("/agent-teams", response_model=AgentTeam)
async def create_agent_team(team: AgentTeamCreate):
    team_id = str(uuid.uuid4())
    agent_team = {"id": team_id, "name": team.name, "agents": team.agents}
    agent_teams_db[team_id] = agent_team
    return agent_team


@router.get("/agent-teams", response_model=List[AgentTeam])
async def list_agent_teams():
    return list(agent_teams_db.values())


@router.delete("/agent-teams/{team_id}")
async def delete_agent_team(team_id: str):
    if team_id not in agent_teams_db:
        raise HTTPException(status_code=404, detail="Agent team not found")
    del agent_teams_db[team_id]
    return {"detail": "Agent team deleted"}
