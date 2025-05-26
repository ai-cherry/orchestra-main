"""
Service for interacting with Google Cloud Platform services.
"""

import asyncio
from functools import lru_cache
from typing import Any, Dict

from google.cloud import aiplatform, resourcemanager_v3
from google.cloud.firestore import AsyncClient as FirestoreAsyncClient

from app.config import settings


class GcpService:
    """
    Service for interacting with Google Cloud Platform services.
    """

    def __init__(self, project_id: str):
        """
        Initialize the GCP service.

        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.resource_client = resourcemanager_v3.ProjectsClient()
        self.firestore_client = FirestoreAsyncClient(project=project_id)

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=settings.REGION)

    async def get_project_info(self) -> Dict[str, Any]:
        """
        Get GCP project information.

        Returns:
            Dict[str, Any]: Project information
        """
        # Resource Manager calls are synchronous, so run in a thread pool
        project_name = f"projects/{self.project_id}"
        loop = asyncio.get_event_loop()
        project = await loop.run_in_executor(
            None, lambda: self.resource_client.get_project(name=project_name)
        )

        # Get Firestore stats
        memory_collection = self.firestore_client.collection(
            settings.FIRESTORE_COLLECTION
        )
        memory_docs = await memory_collection.count().get()
        memory_count = memory_docs[0][0].value

        # Get Vertex AI models
        vertex_models = await loop.run_in_executor(
            None,
            lambda: aiplatform.Model.list(
                filter="display_name=*",
                project=self.project_id,
                location=settings.GEMINI_LOCATION,
            ),
        )

        return {
            "project_id": self.project_id,
            "project_name": project.display_name,
            "project_number": project.name.split("/")[1],
            "create_time": project.create_time.isoformat(),
            "state": project.state.name,
            "memory_documents_count": memory_count,
            "vertex_ai": {
                "models_count": len(vertex_models),
                "gemini_model": settings.GEMINI_MODEL_ID,
                "location": settings.GEMINI_LOCATION,
            },
        }


@lru_cache()
def get_gcp_service() -> GcpService:
    """
    Factory function for GcpService instances.
    Used as a FastAPI dependency.

    Returns:
        GcpService: The GCP service instance
    """
    return GcpService(project_id=settings.PROJECT_ID)
