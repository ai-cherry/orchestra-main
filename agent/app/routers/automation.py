from fastapi import APIRouter
from agent.app.services.automation import trigger_backup, run_healthcheck, trigger_deploy, snapshot_env

router = APIRouter(prefix="/api/automation", tags=["automation"])

@router.post("/backup")
async def api_trigger_backup():
    """Trigger a backup of code, config, and/or DB."""
    return trigger_backup()

@router.post("/healthcheck")
async def api_run_healthcheck():
    """Run a health check and auto-restart failed agents."""
    return run_healthcheck()

@router.post("/deploy")
async def api_trigger_deploy():
    """Trigger a UI/API redeploy."""
    return trigger_deploy()

@router.get("/env/snapshot")
async def api_snapshot_env():
    """Export full environment config for disaster recovery."""
    return snapshot_env()
