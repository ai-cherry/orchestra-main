#!/usr/bin/env python3
"""
MCP Server for AI Agent Orchestration
Manages agent modes, workflows, and task execution
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Orchestrator MCP Server",
    description="AI agent orchestration and workflow management",
    version="1.0.0",
)

# Load mode definitions
MODE_DEFINITIONS_PATH = os.getenv(
    "MODE_DEFINITIONS_PATH",
    "/home/paperspace/orchestra-main/config/mode_definitions.yaml",
)
AGENTS_CONFIG_PATH = os.getenv("AGENTS_CONFIG_PATH", "/home/paperspace/orchestra-main/config/agents.yaml")

# Global state
current_mode = "standard"
active_workflows = {}
agent_states = {}
task_queue = asyncio.Queue()
mode_definitions = {}
agents_config = {}


class AgentMode(str, Enum):
    """Available agent modes"""

    STANDARD = "standard"
    CODE = "code"
    DEBUG = "debug"
    ARCHITECT = "architect"
    STRATEGY = "strategy"
    ASK = "ask"
    CREATIVE = "creative"
    PERFORMANCE = "performance"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    params: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class Workflow(BaseModel):
    """Workflow model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    steps: List[Dict[str, Any]]
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    results: List[Any] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ModeSwitch(BaseModel):
    """Mode switch request"""

    mode: AgentMode
    agent_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Workflow execution request"""

    name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


class MCPToolDefinition(BaseModel):
    """MCP tool definition"""

    name: str
    description: str
    parameters: Dict[str, Any]


def load_configurations():
    """Load mode definitions and agent configurations"""
    global mode_definitions, agents_config

    try:
        # Load mode definitions
        if os.path.exists(MODE_DEFINITIONS_PATH):
            with open(MODE_DEFINITIONS_PATH, "r") as f:
                mode_definitions = yaml.safe_load(f)
                logger.info(f"Loaded {len(mode_definitions.get('modes', {}))} mode definitions")

        # Load agents config
        if os.path.exists(AGENTS_CONFIG_PATH):
            with open(AGENTS_CONFIG_PATH, "r") as f:
                agents_config = yaml.safe_load(f)
                logger.info(f"Loaded {len(agents_config.get('agents', {}))} agent configurations")

    except Exception as e:
        logger.error(f"Failed to load configurations: {e}")


# Load configurations on startup
load_configurations()


async def execute_task(task: Task):
    """Execute a single task"""
    try:
        task.status = "running"
        logger.info(f"Executing task {task.id}: {task.name}")

        # Simulate task execution based on type
        if task.name == "analyze_code":
            # Code analysis task
            await asyncio.sleep(2)
            task.result = {
                "files_analyzed": 42,
                "issues_found": 3,
                "suggestions": ["Consider refactoring", "Add type hints"],
            }
        elif task.name == "generate_tests":
            # Test generation task
            await asyncio.sleep(3)
            task.result = {"tests_generated": 15, "coverage": 0.85}
        elif task.name == "optimize_performance":
            # Performance optimization
            await asyncio.sleep(4)
            task.result = {"optimizations_applied": 7, "performance_gain": "23%"}
        else:
            # Generic task
            await asyncio.sleep(1)
            task.result = {
                "status": "completed",
                "output": f"Task {task.name} executed",
            }

        task.status = "completed"
        task.completed_at = datetime.utcnow()
        logger.info(f"Task {task.id} completed successfully")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        task.completed_at = datetime.utcnow()
        logger.error(f"Task {task.id} failed: {e}")


async def task_worker():
    """Background worker to process tasks"""
    while True:
        try:
            task = await task_queue.get()
            await execute_task(task)
        except Exception as e:
            logger.error(f"Error in task worker: {e}")
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup"""
    logger.info("Starting Orchestrator MCP Server...")

    # Start task worker
    asyncio.create_task(task_worker())

    logger.info("Orchestrator MCP Server started successfully")


@app.get("/mcp/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available orchestration tools"""
    return [
        MCPToolDefinition(
            name="switch_mode",
            description="Switch agent to a different operational mode",
            parameters={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": [
                            "standard",
                            "code",
                            "debug",
                            "architect",
                            "strategy",
                            "ask",
                            "creative",
                            "performance",
                        ],
                        "description": "Target mode",
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Agent to switch (optional)",
                    },
                    "context": {
                        "type": "object",
                        "description": "Mode-specific context",
                    },
                },
                "required": ["mode"],
            },
        ),
        MCPToolDefinition(
            name="execute",
            description="Execute a predefined workflow",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Workflow name"},
                    "params": {"type": "object", "description": "Workflow parameters"},
                    "priority": {"type": "integer", "description": "Priority (1-10)"},
                },
                "required": ["name"],
            },
        ),
        MCPToolDefinition(
            name="execute_task",
            description="Execute a specific task",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Task name"},
                    "description": {
                        "type": "string",
                        "description": "Task description",
                    },
                    "params": {"type": "object", "description": "Task parameters"},
                    "priority": {"type": "integer", "description": "Priority (1-10)"},
                },
                "required": ["name", "description"],
            },
        ),
        MCPToolDefinition(
            name="get_status",
            description="Get current orchestrator status",
            parameters={
                "type": "object",
                "properties": {
                    "include_workflows": {
                        "type": "boolean",
                        "description": "Include workflow details",
                    },
                    "include_tasks": {
                        "type": "boolean",
                        "description": "Include task queue status",
                    },
                },
            },
        ),
    ]


@app.post("/mcp/switch_mode")
async def switch_mode(request: ModeSwitch) -> Dict[str, Any]:
    """Switch agent mode"""
    global current_mode

    previous_mode = current_mode
    current_mode = request.mode.value

    # Update agent state if specified
    if request.agent_id:
        agent_states[request.agent_id] = {
            "mode": current_mode,
            "context": request.context,
            "switched_at": datetime.utcnow().isoformat(),
        }

    # Get mode configuration
    mode_config = mode_definitions.get("modes", {}).get(current_mode, {})

    logger.info(f"Switched mode from {previous_mode} to {current_mode}")

    return {
        "status": "success",
        "previous_mode": previous_mode,
        "current_mode": current_mode,
        "mode_config": mode_config,
        "agent_id": request.agent_id,
        "message": f"Successfully switched to {current_mode} mode",
    }


import hashlib
import hmac

SECRET = os.getenv("MCP_SHARED_SECRET", "secret")


async def verify_signature(req: Request):
    body = await req.body()
    signature = req.headers.get("X-MCP-Signature", "")
    expected = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="Invalid signature")


@app.post("/mcp/execute")
async def run_workflow(
    request: WorkflowRequest, background_tasks: BackgroundTasks, _: None = Depends(verify_signature)
) -> Dict[str, Any]:
    """Execute a workflow"""
    # Create workflow instance
    workflow = Workflow(
        name=request.name,
        description=f"Automated workflow: {request.name}",
        steps=get_workflow_steps(request.name),
        context=request.params,
    )

    # Store workflow
    active_workflows[workflow.id] = workflow

    # Execute workflow in background
    background_tasks.add_task(execute_workflow, workflow)

    logger.info(f"Started workflow {workflow.id}: {workflow.name}")

    return {
        "status": "success",
        "workflow_id": workflow.id,
        "name": workflow.name,
        "total_steps": len(workflow.steps),
        "message": f"Workflow {workflow.name} started",
    }


def get_workflow_steps(workflow_name: str) -> List[Dict[str, Any]]:
    """Get workflow steps based on name"""
    workflows = {
        "code_review": [
            {"name": "analyze_code", "type": "task"},
            {"name": "check_style", "type": "task"},
            {"name": "generate_report", "type": "task"},
        ],
        "test_automation": [
            {"name": "analyze_code", "type": "task"},
            {"name": "generate_tests", "type": "task"},
            {"name": "run_tests", "type": "task"},
            {"name": "coverage_report", "type": "task"},
        ],
        "performance_optimization": [
            {"name": "profile_code", "type": "task"},
            {"name": "identify_bottlenecks", "type": "task"},
            {"name": "optimize_performance", "type": "task"},
            {"name": "benchmark", "type": "task"},
        ],
        "deployment": [
            {"name": "run_tests", "type": "task"},
            {"name": "build_image", "type": "task"},
            {"name": "deploy_staging", "type": "task"},
            {"name": "smoke_test", "type": "task"},
            {"name": "deploy_production", "type": "task"},
        ],
    }

    return workflows.get(workflow_name, [{"name": "generic_task", "type": "task"}])


async def execute_workflow(workflow: Workflow):
    """Execute workflow steps"""
    try:
        workflow.status = WorkflowStatus.RUNNING

        for i, step in enumerate(workflow.steps):
            workflow.current_step = i

            # Create task for step
            task = Task(
                name=step["name"],
                description=f"Step {i+1} of workflow {workflow.name}",
                params={**workflow.context, **step.get("params", {})},
            )

            # Execute task
            await execute_task(task)

            # Store result
            workflow.results.append(task.result)

            # Check if task failed
            if task.status == "failed":
                workflow.status = WorkflowStatus.FAILED
                logger.error(f"Workflow {workflow.id} failed at step {i+1}")
                return

        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.utcnow()
        logger.info(f"Workflow {workflow.id} completed successfully")

    except Exception as e:
        workflow.status = WorkflowStatus.FAILED
        logger.error(f"Workflow {workflow.id} failed: {e}")


@app.post("/mcp/execute_task")
async def execute_task_endpoint(
    name: str,
    description: str,
    params: Dict[str, Any] = {},
    priority: int = 5,
    agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Queue a task for execution"""
    # Create task
    task = Task(
        name=name,
        description=description,
        params=params,
        priority=priority,
        agent_id=agent_id,
    )

    # Add to queue
    await task_queue.put(task)

    logger.info(f"Queued task {task.id}: {task.name}")

    return {
        "status": "success",
        "task_id": task.id,
        "name": task.name,
        "priority": task.priority,
        "queue_size": task_queue.qsize(),
        "message": f"Task {task.name} queued for execution",
    }


@app.post("/mcp/get_status")
async def get_orchestrator_status(include_workflows: bool = True, include_tasks: bool = True) -> Dict[str, Any]:
    """Get current orchestrator status"""
    status = {
        "current_mode": current_mode,
        "active_agents": len(agent_states),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if include_workflows:
        status["workflows"] = {
            "active": sum(1 for w in active_workflows.values() if w.status == WorkflowStatus.RUNNING),
            "completed": sum(1 for w in active_workflows.values() if w.status == WorkflowStatus.COMPLETED),
            "failed": sum(1 for w in active_workflows.values() if w.status == WorkflowStatus.FAILED),
            "recent": [
                {
                    "id": w.id,
                    "name": w.name,
                    "status": w.status,
                    "progress": f"{w.current_step}/{len(w.steps)}",
                    "created_at": w.created_at.isoformat(),
                }
                for w in sorted(active_workflows.values(), key=lambda x: x.created_at, reverse=True)[:5]
            ],
        }

    if include_tasks:
        status["tasks"] = {
            "queue_size": task_queue.qsize(),
            "pending": task_queue.qsize(),
            "processing": 1 if task_queue.qsize() > 0 else 0,
        }

    status["agent_states"] = agent_states

    return status


@app.get("/mcp/workflows")
async def list_workflows() -> List[Dict[str, Any]]:
    """List all workflows"""
    return [
        {
            "id": w.id,
            "name": w.name,
            "status": w.status,
            "steps": len(w.steps),
            "current_step": w.current_step,
            "created_at": w.created_at.isoformat(),
            "completed_at": w.completed_at.isoformat() if w.completed_at else None,
        }
        for w in active_workflows.values()
    ]


@app.get("/mcp/workflow/{workflow_id}")
async def get_workflow_details(workflow_id: str) -> Dict[str, Any]:
    """Get detailed workflow information"""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    workflow = active_workflows[workflow_id]

    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "current_step": workflow.current_step,
        "total_steps": len(workflow.steps),
        "steps": workflow.steps,
        "results": workflow.results,
        "context": workflow.context,
        "created_at": workflow.created_at.isoformat(),
        "completed_at": (workflow.completed_at.isoformat() if workflow.completed_at else None),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator-mcp",
        "current_mode": current_mode,
        "active_workflows": len([w for w in active_workflows.values() if w.status == WorkflowStatus.RUNNING]),
        "queue_size": task_queue.qsize(),
        "configurations_loaded": bool(mode_definitions) and bool(agents_config),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
