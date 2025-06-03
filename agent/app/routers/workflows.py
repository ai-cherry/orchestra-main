from fastapi import APIRouter
from agent.app.services.workflow_runner import (
    run_workflow,
    get_workflow_history,
    get_workflow_schedule,
    set_workflow_schedule,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

@router.post("/{workflow_id}/run")
async def api_run_workflow(workflow_id: str):
    """Trigger a workflow on demand."""
@router.get("/{workflow_id}/history")
async def api_get_workflow_history(workflow_id: str):
    """View execution history/results for a workflow."""
@router.get("/schedule")
async def api_get_workflow_schedule():
    """Get all workflow schedules."""
@router.post("/schedule")
async def api_set_workflow_schedule(schedule: dict):
    """Set a workflow schedule (cron-like)."""