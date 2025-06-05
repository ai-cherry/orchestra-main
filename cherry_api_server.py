#!/usr/bin/env python3
"""
Cherry AI API Server
Simple FastAPI server to handle orchestrator endpoints
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cherry AI API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Agent(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    status: str = "active"
    capabilities: List[str] = []
    created_at: Optional[datetime] = None

class Orchestration(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    agents: List[str] = []
    workflow: Dict[str, Any] = {}
    status: str = "draft"
    created_at: Optional[datetime] = None

class Workflow(BaseModel):
    id: Optional[str] = None
    name: str
    steps: List[Dict[str, Any]] = []
    triggers: List[str] = []
    status: str = "inactive"
    created_at: Optional[datetime] = None

class SearchRequest(BaseModel):
    query: str
    type: str = "web"  # "web" or "domain"

# In-memory storage (replace with database in production)
agents_db: Dict[str, Agent] = {
    "agent-1": Agent(
        id="agent-1",
        name="Data Processor",
        type="processor",
        status="active",
        capabilities=["data_extraction", "data_transformation", "data_validation"],
        created_at=datetime.now()
    ),
    "agent-2": Agent(
        id="agent-2",
        name="Web Scraper",
        type="scraper",
        status="active",
        capabilities=["web_scraping", "api_integration", "data_collection"],
        created_at=datetime.now()
    ),
    "agent-3": Agent(
        id="agent-3",
        name="AI Analyzer",
        type="analyzer",
        status="active",
        capabilities=["nlp", "sentiment_analysis", "entity_extraction"],
        created_at=datetime.now()
    )
}

orchestrations_db: Dict[str, Orchestration] = {
    "orch-1": Orchestration(
        id="orch-1",
        name="Customer Feedback Pipeline",
        description="Automated pipeline for processing customer feedback",
        agents=["agent-1", "agent-3"],
        workflow={"steps": ["collect", "process", "analyze", "report"]},
        status="active",
        created_at=datetime.now()
    )
}

workflows_db: Dict[str, Workflow] = {
    "wf-1": Workflow(
        id="wf-1",
        name="Daily Data Sync",
        steps=[
            {"name": "Extract", "agent": "agent-2"},
            {"name": "Transform", "agent": "agent-1"},
            {"name": "Load", "agent": "agent-1"}
        ],
        triggers=["schedule:daily", "event:data_updated"],
        status="active",
        created_at=datetime.now()
    )
}

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Cherry AI API Server", "status": "running"}

@app.get("/api/agents")
async def get_agents():
    """Get all agents"""
    return list(agents_db.values())

@app.post("/api/agents")
async def create_agent(agent: Agent):
    """Create a new agent"""
    agent_id = f"agent-{len(agents_db) + 1}"
    agent.id = agent_id
    agent.created_at = datetime.now()
    agents_db[agent_id] = agent
    logger.info(f"Created agent: {agent.name}")
    return agent

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    deleted_agent = agents_db.pop(agent_id)
    logger.info(f"Deleted agent: {deleted_agent.name}")
    return {"message": "Agent deleted", "id": agent_id}

@app.get("/api/orchestrations")
async def get_orchestrations():
    """Get all orchestrations"""
    return list(orchestrations_db.values())

@app.post("/api/orchestrations")
async def create_orchestration(orchestration: Orchestration):
    """Create a new orchestration"""
    orch_id = f"orch-{len(orchestrations_db) + 1}"
    orchestration.id = orch_id
    orchestration.created_at = datetime.now()
    orchestrations_db[orch_id] = orchestration
    logger.info(f"Created orchestration: {orchestration.name}")
    return orchestration

@app.get("/api/workflows")
async def get_workflows():
    """Get all workflows"""
    return list(workflows_db.values())

@app.post("/api/workflows")
async def create_workflow(workflow: Workflow):
    """Create a new workflow"""
    wf_id = f"wf-{len(workflows_db) + 1}"
    workflow.id = wf_id
    workflow.created_at = datetime.now()
    workflows_db[wf_id] = workflow
    logger.info(f"Created workflow: {workflow.name}")
    return workflow

@app.post("/api/search")
async def search(request: SearchRequest):
    """Handle search requests"""
    logger.info(f"Search request: {request.query} (type: {request.type})")
    
    # Mock search results
    if request.type == "domain":
        # This would integrate with Weaviate in production
        return {
            "results": [
                {
                    "title": "Domain Knowledge Result 1",
                    "content": f"Result for query: {request.query}",
                    "relevance": 0.95,
                    "source": "knowledge_base"
                },
                {
                    "title": "Domain Knowledge Result 2",
                    "content": f"Additional information about: {request.query}",
                    "relevance": 0.87,
                    "source": "documentation"
                }
            ],
            "count": 2,
            "query": request.query
        }
    else:
        # Web search mock
        return {
            "results": [
                {
                    "title": "Web Search Result 1",
                    "url": f"https://example.com/search?q={request.query}",
                    "snippet": f"Web result for: {request.query}",
                    "source": "web"
                }
            ],
            "count": 1,
            "query": request.query
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "weaviate": "connected"
        }
    }

def main():
    """Main entry point"""
    logger.info("Starting Cherry AI API Server...")
    
    # Save PID for process management
    pid_file = Path("/tmp/cherry_api.pid")
    pid_file.write_text(str(os.getpid()))
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    import os
    main()