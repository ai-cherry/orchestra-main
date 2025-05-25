"""
Service for system-level operations and GCP resource management.
"""

import logging
import os
import platform
import time
from functools import lru_cache
from typing import Any, Dict

import psutil
from google.api_core.exceptions import GoogleAPIError
from google.cloud import monitoring_v3, resourcemanager_v3

from app.config import settings

logger = logging.getLogger(__name__)


class SystemService:
    """
    Service for system monitoring and GCP resource management.
    Provides system stats, project information, and GCP resource metrics.
    """

    def __init__(self, project_id: str, region: str):
        """
        Initialize the system service.

        Args:
            project_id: GCP project ID
            region: GCP region
        """
        self.project_id = project_id
        self.region = region
        self.resource_client = resourcemanager_v3.ProjectsClient()
        self.monitoring_client = monitoring_v3.MetricServiceClient()

        # Cache initialization timestamp
        self.start_time = time.time()

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics including CPU, memory, disk usage and environment info.

        Returns:
            Dict[str, Any]: Dictionary of system statistics
        """
        try:
            # Get basic system info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Calculate uptime
            uptime_seconds = time.time() - self.start_time

            # Get environment information
            env_info = {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "environment": settings.ENV,
                "project_id": self.project_id,
                "region": self.region,
            }

            # Get process info
            process = psutil.Process(os.getpid())
            process_info = {
                "pid": process.pid,
                "memory_usage_mb": process.memory_info().rss / (1024 * 1024),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "threads": process.num_threads(),
                "created_time": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(process.create_time())
                ),
            }

            return {
                "timestamp": time.time(),
                "uptime_seconds": uptime_seconds,
                "cpu": {
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(logical=True),
                    "physical_cores": psutil.cpu_count(logical=False),
                },
                "memory": {
                    "total_mb": memory.total / (1024 * 1024),
                    "available_mb": memory.available / (1024 * 1024),
                    "used_mb": memory.used / (1024 * 1024),
                    "percent": memory.percent,
                },
                "disk": {
                    "total_gb": disk.total / (1024 * 1024 * 1024),
                    "used_gb": disk.used / (1024 * 1024 * 1024),
                    "free_gb": disk.free / (1024 * 1024 * 1024),
                    "percent": disk.percent,
                },
                "process": process_info,
                "environment": env_info,
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}", exc_info=True)
            return {"error": "Failed to retrieve system statistics", "reason": str(e)}

    async def get_project_info(self) -> Dict[str, Any]:
        """
        Get GCP project information.

        Returns:
            Dict[str, Any]: GCP project information
        """
        try:
            # Get project details
            start_time = time.time()
            project_name = f"projects/{self.project_id}"
            project = self.resource_client.get_project(name=project_name)

            # Get project labels
            labels = dict(project.labels) if project.labels else {}

            # Create a useful project info object
            project_info = {
                "project_id": self.project_id,
                "project_number": project.name.split("/")[1],
                "display_name": project.display_name,
                "create_time": project.create_time.isoformat(),
                "update_time": project.update_time.isoformat(),
                "state": project.state.name,
                "labels": labels,
                "query_time_ms": round((time.time() - start_time) * 1000, 2),
            }

            # Get any parent information if available
            if hasattr(project, "parent") and project.parent:
                project_info["parent"] = project.parent

            return {"success": True, "project": project_info}
        except GoogleAPIError as e:
            logger.error(f"GCP API error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "Failed to retrieve GCP project information",
                "reason": str(e),
            }
        except Exception as e:
            logger.error(f"Error getting project info: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "Failed to retrieve project information",
                "reason": str(e),
            }


@lru_cache()
def get_system_service() -> SystemService:
    """
    Factory function for SystemService instances.
    Used as a FastAPI dependency.

    Returns:
        SystemService: The system service instance
    """
    return SystemService(project_id=settings.PROJECT_ID, region=settings.REGION)


# Alias for backward compatibility with existing router
get_gcp_service = get_system_service
