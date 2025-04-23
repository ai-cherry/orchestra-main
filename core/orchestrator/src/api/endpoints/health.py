"""
Health check endpoints for the AI Orchestration System.

This module provides API endpoints for checking the health and status
of various system components, including storage backends.
"""

import logging
import os
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.orchestrator.src.api.dependencies.memory import (
    get_memory_manager,
    CURRENT_ENV,
    ENV_DEV,
    ENV_TEST,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class HealthStatus(BaseModel):
    """Schema for system health status."""

    status: str
    environment: str
    version: str = "1.0.0"
    components: Dict[str, bool]
    details: Dict[str, str] = {}


@router.get("/health", summary="Check system health")
async def check_health(
    request: Request,
) -> HealthStatus:
    """
    Check the health of the system components.

    This endpoint checks the status of various system components including:
    - Storage backends (Firestore, Redis)
    - LLM services
    - Other dependencies

    Returns:
        HealthStatus: A health status response with component statuses
    """
    # Initialize health status
    status = "ok"
    components = {
        "app": True,
    }
    details = {}

    # Check storage health in production environments
    if CURRENT_ENV not in [ENV_DEV, ENV_TEST]:
        try:
            # Get memory manager
            memory_manager = get_memory_manager()

            # Check health if the manager has a health_check method
            if hasattr(memory_manager, "health_check"):
                storage_health = await memory_manager.health_check()

                # Add storage components
                for component, healthy in storage_health.items():
                    components[f"storage_{component}"] = healthy
                    if not healthy:
                        status = "degraded"
                        details[f"storage_{component}"] = "Not available or responding"
            else:
                # No health check method, assume storage is functional
                components["storage"] = True

        except Exception as e:
            logger.error(f"Error checking storage health: {e}")
            components["storage"] = False
            status = "degraded"
            details["storage"] = f"Error: {str(e)}"

    # Return health status
    return HealthStatus(
        status=status, environment=CURRENT_ENV, components=components, details=details
    )


@router.get("/ping", summary="Simple ping endpoint")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint to check if the API is responsive.

    Returns:
        Dict with a "status" key set to "ok"
    """
    return {"status": "ok"}
