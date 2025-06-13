from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
import psutil
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task to update metrics
async def update_metrics():
    """Background task to update agent metrics"""
    while True:
        try:
            for agent in agents_db.values():
                if agent.status == "active":
                    # Simulate some activity
                    agent.requests_count += int(psutil.cpu_percent() / 10)
                    agent.memory_usage = min(90.0, agent.memory_usage + (psutil.cpu_percent() - 50) * 0.1)
                    agent.cpu_usage = max(0.0, min(100.0, psutil.cpu_percent() + (agent.requests_count % 10)))
                    agent.last_activity = datetime.now()
            
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            await asyncio.sleep(10)

# Background tasks
async def simulate_backup(backup_id: str):
    """Simulate backup process"""
    await asyncio.sleep(30)  # Simulate backup time
    
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="success",
        title="System backup completed",
        description=f"Backup {backup_id} completed successfully",
        component="backup-service",
        user=None
    ))

# Startup event
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the application"""
    initialize_sample_data()
    # Start background metrics updater
    asyncio.create_task(update_metrics())
    logger.info("Orchestra AI Admin API started successfully")
    yield
    # Cleanup code would go here
    logger.info("Orchestra AI Admin API shutting down")

# Create FastAPI app
app = FastAPI(
    title="Orchestra AI Admin API",
    description="Real admin API for Orchestra AI system management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class AgentStatus(BaseModel):
    id: str
    name: str
    status: str  # active, idle, error, stopped
    requests_count: int
    success_rate: float
    avg_response_time: float
    last_activity: datetime
    memory_usage: float
    cpu_usage: float

class SystemMetrics(BaseModel):
    active_agents: int
    api_requests_per_minute: int
    memory_usage_percent: float
    cpu_usage_percent: float
    success_rate: float
    uptime_hours: float
    disk_usage_percent: float
    network_io: Dict[str, float]

class WorkflowStatus(BaseModel):
    id: str
    name: str
    status: str  # active, paused, error, completed
    executions_today: int
    success_rate: float
    avg_execution_time: float
    last_run: datetime
    next_run: Optional[datetime]

class ActivityLog(BaseModel):
    id: str
    timestamp: datetime
    type: str  # info, warning, error, success
    title: str
    description: str
    component: str
    user: Optional[str]

class DeploymentRequest(BaseModel):
    agent_type: str
    name: str
    config: Dict[str, Any]

# In-memory storage (replace with real database)
agents_db: Dict[str, AgentStatus] = {}
workflows_db: Dict[str, WorkflowStatus] = {}
activity_logs: List[ActivityLog] = []
system_start_time = time.time()

# Initialize sample data
def initialize_sample_data():
    global agents_db, workflows_db, activity_logs
    
    # Sample agents
    agents_db = {
        "agent-001": AgentStatus(
            id="agent-001",
            name="Customer Support Agent",
            status="active",
            requests_count=247,
            success_rate=98.5,
            avg_response_time=1.2,
            last_activity=datetime.now(),
            memory_usage=45.2,
            cpu_usage=12.3
        ),
        "agent-002": AgentStatus(
            id="agent-002",
            name="Data Analysis Agent",
            status="active",
            requests_count=89,
            success_rate=94.1,
            avg_response_time=3.7,
            last_activity=datetime.now() - timedelta(minutes=5),
            memory_usage=67.8,
            cpu_usage=23.1
        ),
        "agent-003": AgentStatus(
            id="agent-003",
            name="Content Generator",
            status="idle",
            requests_count=12,
            success_rate=100.0,
            avg_response_time=5.1,
            last_activity=datetime.now() - timedelta(hours=2),
            memory_usage=23.4,
            cpu_usage=2.1
        ),
        "agent-004": AgentStatus(
            id="agent-004",
            name="Code Review Agent",
            status="error",
            requests_count=0,
            success_rate=0.0,
            avg_response_time=0.0,
            last_activity=datetime.now() - timedelta(hours=6),
            memory_usage=0.0,
            cpu_usage=0.0
        )
    }
    
    # Sample workflows
    workflows_db = {
        "workflow-001": WorkflowStatus(
            id="workflow-001",
            name="Customer Onboarding",
            status="active",
            executions_today=142,
            success_rate=98.2,
            avg_execution_time=2.3,
            last_run=datetime.now() - timedelta(minutes=2),
            next_run=datetime.now() + timedelta(minutes=5)
        ),
        "workflow-002": WorkflowStatus(
            id="workflow-002",
            name="Lead Qualification",
            status="active",
            executions_today=89,
            success_rate=94.7,
            avg_execution_time=1.8,
            last_run=datetime.now() - timedelta(minutes=8),
            next_run=datetime.now() + timedelta(minutes=12)
        ),
        "workflow-003": WorkflowStatus(
            id="workflow-003",
            name="Social Media Monitoring",
            status="paused",
            executions_today=0,
            success_rate=0.0,
            avg_execution_time=0.0,
            last_run=datetime.now() - timedelta(days=1),
            next_run=None
        )
    }
    
    # Sample activity logs
    activity_logs = [
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(minutes=2),
            type="success",
            title="Customer Support Agent deployed successfully",
            description="New agent instance started and handling requests",
            component="agent-manager",
            user="admin"
        ),
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(minutes=5),
            type="warning",
            title="High memory usage detected",
            description="Memory usage reached 68% - consider scaling",
            component="system-monitor",
            user=None
        ),
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(minutes=12),
            type="error",
            title="Code Review Agent failed to start",
            description="Connection timeout to external API service",
            component="agent-manager",
            user="admin"
        ),
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(hours=1),
            type="info",
            title="System backup completed",
            description="Daily backup of agent configurations and data",
            component="backup-service",
            user=None
        ),
        ActivityLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.now() - timedelta(hours=2),
            type="success",
            title="API Gateway updated",
            description="Rate limiting rules updated for better performance",
            component="api-gateway",
            user="admin"
        )
    ]

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Orchestra AI Admin API", "status": "operational", "version": "1.0.0"}

@app.get("/api/system/status", response_model=SystemMetrics)
async def get_system_status():
    """Get current system metrics and status"""
    try:
        # Get real system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Calculate derived metrics
        active_agents = len([a for a in agents_db.values() if a.status == "active"])
        total_requests = sum(a.requests_count for a in agents_db.values())
        avg_success_rate = sum(a.success_rate for a in agents_db.values()) / len(agents_db) if agents_db else 0
        uptime = (time.time() - system_start_time) / 3600  # hours
        
        return SystemMetrics(
            active_agents=active_agents,
            api_requests_per_minute=total_requests // 60 if total_requests > 0 else 0,
            memory_usage_percent=memory.percent,
            cpu_usage_percent=cpu_percent,
            success_rate=avg_success_rate,
            uptime_hours=uptime,
            disk_usage_percent=(disk.used / disk.total) * 100,
            network_io={
                "bytes_sent": float(network.bytes_sent),
                "bytes_recv": float(network.bytes_recv)
            }
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@app.get("/api/agents", response_model=List[AgentStatus])
async def get_agents():
    """Get all AI agents and their status"""
    return list(agents_db.values())

@app.get("/api/agents/{agent_id}", response_model=AgentStatus)
async def get_agent(agent_id: str):
    """Get specific agent details"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agents_db[agent_id]

@app.post("/api/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """Start an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agents_db[agent_id].status = "active"
    agents_db[agent_id].last_activity = datetime.now()
    
    # Log activity
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="success",
        title=f"Agent {agents_db[agent_id].name} started",
        description=f"Agent {agent_id} has been started successfully",
        component="agent-manager",
        user="admin"
    ))
    
    return {"message": f"Agent {agent_id} started successfully"}

@app.post("/api/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """Stop an agent"""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agents_db[agent_id].status = "stopped"
    agents_db[agent_id].cpu_usage = 0.0
    
    # Log activity
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="warning",
        title=f"Agent {agents_db[agent_id].name} stopped",
        description=f"Agent {agent_id} has been stopped",
        component="agent-manager",
        user="admin"
    ))
    
    return {"message": f"Agent {agent_id} stopped successfully"}

@app.post("/api/agents/deploy")
async def deploy_agent(deployment: DeploymentRequest, background_tasks: BackgroundTasks):
    """Deploy a new agent"""
    agent_id = f"agent-{str(uuid.uuid4())[:8]}"
    
    # Create new agent
    new_agent = AgentStatus(
        id=agent_id,
        name=deployment.name,
        status="active",
        requests_count=0,
        success_rate=100.0,
        avg_response_time=0.0,
        last_activity=datetime.now(),
        memory_usage=15.0,
        cpu_usage=5.0
    )
    
    agents_db[agent_id] = new_agent
    
    # Log activity
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="success",
        title=f"New agent deployed: {deployment.name}",
        description=f"Agent {agent_id} deployed with type {deployment.agent_type}",
        component="agent-manager",
        user="admin"
    ))
    
    return {"message": "Agent deployed successfully", "agent_id": agent_id}

@app.get("/api/workflows", response_model=List[WorkflowStatus])
async def get_workflows():
    """Get all workflows and their status"""
    return list(workflows_db.values())

@app.post("/api/workflows/{workflow_id}/start")
async def start_workflow(workflow_id: str):
    """Start a workflow"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflows_db[workflow_id].status = "active"
    workflows_db[workflow_id].last_run = datetime.now()
    workflows_db[workflow_id].next_run = datetime.now() + timedelta(minutes=30)
    
    return {"message": f"Workflow {workflow_id} started successfully"}

@app.post("/api/workflows/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause a workflow"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflows_db[workflow_id].status = "paused"
    workflows_db[workflow_id].next_run = None
    
    return {"message": f"Workflow {workflow_id} paused successfully"}

@app.get("/api/activity", response_model=List[ActivityLog])
async def get_activity_logs(limit: int = 50):
    """Get recent activity logs"""
    return sorted(activity_logs, key=lambda x: x.timestamp, reverse=True)[:limit]

@app.post("/api/system/backup")
async def create_backup(background_tasks: BackgroundTasks):
    """Create system backup"""
    backup_id = str(uuid.uuid4())
    
    # Log activity
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="info",
        title="System backup initiated",
        description=f"Backup {backup_id} started",
        component="backup-service",
        user="admin"
    ))
    
    # Simulate backup process
    background_tasks.add_task(simulate_backup, backup_id)
    
    return {"message": "Backup initiated", "backup_id": backup_id}

@app.post("/api/system/emergency-stop")
async def emergency_stop():
    """Emergency stop all agents and workflows"""
    # Stop all agents
    for agent in agents_db.values():
        agent.status = "stopped"
        agent.cpu_usage = 0.0
    
    # Pause all workflows
    for workflow in workflows_db.values():
        workflow.status = "paused"
        workflow.next_run = None
    
    # Log activity
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="error",
        title="Emergency stop activated",
        description="All agents and workflows have been stopped",
        component="system-manager",
        user="admin"
    ))
    
    return {"message": "Emergency stop completed - all systems halted"}

@app.post("/api/system/restart")
async def restart_system():
    """Restart all system components"""
    # Restart agents
    for agent in agents_db.values():
        if agent.status != "error":
            agent.status = "active"
            agent.last_activity = datetime.now()
    
    # Restart workflows
    for workflow in workflows_db.values():
        if workflow.status != "error":
            workflow.status = "active"
            workflow.next_run = datetime.now() + timedelta(minutes=5)
    
    # Log activity
    activity_logs.append(ActivityLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        type="success",
        title="System restart completed",
        description="All components have been restarted",
        component="system-manager",
        user="admin"
    ))
    
    return {"message": "System restart completed"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - system_start_time,
        "agents_count": len(agents_db),
        "workflows_count": len(workflows_db)
    }

# Functions defined after app creation

# Mount static files for local development
import os
from fastapi.staticfiles import StaticFiles

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "public")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"✅ Static files mounted from: {static_dir}")
else:
    print(f"❌ Static directory not found: {static_dir}")

# For Vercel deployment
handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 