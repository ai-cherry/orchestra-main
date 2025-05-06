"""
Health check and system status endpoints.
"""
from fastapi import APIRouter, Depends

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        A dictionary with status information
    """
    return {
        "status": "healthy",
        "service": "orchestrator",
        "mode": "standard" 
    }


@router.get("/status")
async def system_status():
    """
    Get detailed system status information.
    
    Returns:
        A dictionary with system status details
    """
    # This can be expanded later to include more detailed status information
    # such as connected services, available agents, etc.
    return {
        "status": "operational",
        "components": {
            "api": "online",
            "agents": "online",
            "memory": "online"
        },
        "version": "1.0.0"
    }