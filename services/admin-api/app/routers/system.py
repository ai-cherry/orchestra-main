"""
Router for system-level API endpoints.
"""
from typing import Dict, Any
import platform
import psutil
from fastapi import APIRouter, Depends

from app.config import settings
from app.services.gcp_service import get_gcp_service

router = APIRouter()


@router.get("/stats")
async def get_system_stats() -> Dict[str, Any]:
    """
    Get system statistics including CPU, memory, and disk usage.

    Returns:
        Dict[str, Any]: System statistics
    """
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "environment": settings.ENV,
        "project_id": settings.PROJECT_ID,
        "region": settings.REGION,
    }


@router.get("/gcp")
async def get_gcp_info(gcp_service=Depends(get_gcp_service)) -> Dict[str, Any]:
    """
    Get GCP project information.

    Args:
        gcp_service: GCP service client

    Returns:
        Dict[str, Any]: GCP project information
    """
    return await gcp_service.get_project_info()
