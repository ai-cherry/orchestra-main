from fastapi import APIRouter
from agent.app.services.audit_log import get_audit_log, export_audit_log

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
async def api_get_audit_log():
    """Get all system and user activity logs."""
    return get_audit_log()


@router.get("/export")
async def api_export_audit_log():
    """Export logs for backup or analysis."""
    return export_audit_log()
