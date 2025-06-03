from fastapi import APIRouter
from agent.app.services.system_health import get_system_health, get_live_metrics, get_alerts

router = APIRouter(prefix="/api/system", tags=["system"])

@router.get("/health")
async def api_get_system_health():
    """Aggregated system health check."""
@router.get("/metrics/live")
async def api_get_live_metrics():
    """Real-time system metrics."""
@router.get("/alerts")
async def api_get_alerts():
    """List system/agent alerts."""