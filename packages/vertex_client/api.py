"""
FastAPI integration for Vertex AI Agent Manager.

This module provides REST API endpoints for triggering Vertex AI Agent tasks.
"""

from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .vertex_agent_manager import trigger_vertex_task

# Create FastAPI app
app = FastAPI(
    title="Orchestra Vertex AI Integration",
    description="API for triggering Vertex AI Agent tasks",
    version="1.0.0",
)


# Define request and response models
class VertexTaskRequest(BaseModel):
    """Request model for triggering a Vertex AI task."""

    task: str = Field(..., description="Task to execute")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional parameters for the task"
    )


class VertexTaskResponse(BaseModel):
    """Response model for Vertex AI task results."""

    status: str = Field(..., description="Status of the task execution")
    task: str = Field(..., description="Task that was executed")
    result: Dict[str, Any] = Field(..., description="Result of the task execution")


# Define background task function
async def execute_task_in_background(
    task: str, params: Optional[Dict[str, Any]] = None
):
    """
    Execute a Vertex AI task in the background.

    Args:
        task: Task to execute
        params: Additional parameters for the task
    """
    trigger_vertex_task(task, **(params or {}))


# Define API routes
@app.post("/vertex/trigger-task", response_model=VertexTaskResponse)
async def trigger_task(request: VertexTaskRequest, background_tasks: BackgroundTasks):
    """
    Trigger a Vertex AI Agent task.

    Args:
        request: Task request
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status and initial response
    """
    try:
        # Start executing the task in the background
        background_tasks.add_task(
            execute_task_in_background, request.task, request.params
        )

        return {
            "status": "accepted",
            "task": request.task,
            "result": {
                "message": "Task started in background",
                "params": request.params,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger task: {str(e)}")


@app.get("/vertex/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vertex-agent-manager"}


# Routes for specific task types
@app.post("/vertex/terraform/{workspace}")
async def apply_terraform(workspace: str, background_tasks: BackgroundTasks):
    """
    Apply Terraform configuration for a specific workspace.

    Args:
        workspace: Terraform workspace (dev, stage, prod)
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status
    """
    task = f"apply terraform {workspace}"

    try:
        # Start executing the task in the background
        background_tasks.add_task(execute_task_in_background, task)

        return {
            "status": "accepted",
            "task": task,
            "result": {
                "message": f"Started applying Terraform for workspace: {workspace}",
                "workspace": workspace,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to apply Terraform: {str(e)}"
        )


@app.post("/vertex/agent-teams/{team_name}")
async def create_agent_team(
    team_name: str, background_tasks: BackgroundTasks, roles: List[str] = None
):
    """
    Create and deploy an agent team.

    Args:
        team_name: Name of the team
        roles: List of roles for the team members
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status
    """
    task = f"create agent team {team_name}"
    params = {"roles": roles or ["planner", "doer", "reviewer"]}

    try:
        # Start executing the task in the background
        background_tasks.add_task(execute_task_in_background, task, params)

        return {
            "status": "accepted",
            "task": task,
            "result": {
                "message": f"Started creating agent team: {team_name}",
                "team_name": team_name,
                "roles": params["roles"],
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create agent team: {str(e)}"
        )


@app.post("/vertex/embeddings/{index_name}")
async def manage_embeddings(
    index_name: str, data: str, background_tasks: BackgroundTasks
):
    """
    Manage embeddings in Vertex AI Vector Search.

    Args:
        index_name: Vector index name
        data: Data to embed
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status
    """
    task = f"manage embeddings {index_name}"
    params = {"data": data}

    try:
        # Start executing the task in the background
        background_tasks.add_task(execute_task_in_background, task, params)

        return {
            "status": "accepted",
            "task": task,
            "result": {
                "message": f"Started managing embeddings for index: {index_name}",
                "index_name": index_name,
                "data_length": len(data),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to manage embeddings: {str(e)}"
        )


@app.post("/vertex/games/{game_type}/{session_id}")
async def manage_game_session(
    game_type: str,
    session_id: str,
    player_action: str = None,
    background_tasks: BackgroundTasks = None,
):
    """
    Manage a live game session.

    Args:
        game_type: Type of game (e.g., trivia, word_game)
        session_id: Unique session identifier
        player_action: Action taken by the player
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status
    """
    task = f"manage game session {game_type} {session_id} {player_action}"

    try:
        # Start executing the task in the background
        background_tasks.add_task(execute_task_in_background, task)

        return {
            "status": "accepted",
            "task": task,
            "result": {
                "message": f"Started managing game session: {game_type}/{session_id}",
                "game_type": game_type,
                "session_id": session_id,
                "player_action": player_action,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to manage game session: {str(e)}"
        )


@app.post("/vertex/monitor")
async def monitor_resources(background_tasks: BackgroundTasks):
    """
    Monitor GCP resource usage and costs.

    Args:
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status
    """
    task = "monitor resources"

    try:
        # Start executing the task in the background
        background_tasks.add_task(execute_task_in_background, task)

        return {
            "status": "accepted",
            "task": task,
            "result": {"message": "Started monitoring GCP resources"},
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to monitor resources: {str(e)}"
        )


@app.post("/vertex/init")
async def run_init_script(background_tasks: BackgroundTasks):
    """
    Run the infrastructure initialization script.

    Args:
        background_tasks: FastAPI background tasks

    Returns:
        Task execution status
    """
    task = "run init script"

    try:
        # Start executing the task in the background
        background_tasks.add_task(execute_task_in_background, task)

        return {
            "status": "accepted",
            "task": task,
            "result": {
                "message": "Started running infrastructure initialization script"
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to run init script: {str(e)}"
        )


# Run the application when executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
