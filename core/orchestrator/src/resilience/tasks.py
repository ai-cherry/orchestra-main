"""
Task Queue Integration for Agent Resilience.

This module provides integration with Google Cloud Tasks for scheduling
retry attempts with exponential backoff for failed agent operations.
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from google.protobuf import timestamp_pb2

from optional_integrations import tasks_v2  # Optional integration

# Configure logging
logger = logging.getLogger(__name__)

# Optional: Google Cloud Tasks integration


class TaskQueueManager:
    """
    Manager for scheduling retry tasks using Google Cloud Tasks.

    This class provides methods for creating and scheduling retry tasks
    for agent operations with exponential backoff.
    """

    def __init__(
        self,
        project_id: str,
        location_id: str,
        queue_name: str,
        service_url: str,
        service_account_email: Optional[str] = None,
    ):
        """
        Initialize task queue manager.

        Args:
            project_id: GCP project ID
            location_id: GCP location ID (e.g., us-west4)
            queue_name: Name of the Cloud Tasks queue
            service_url: URL of the service to receive the task
            service_account_email: Service account for authenticating to service (optional)
        """
        self.project_id = project_id
        self.location_id = location_id
        self.queue_name = queue_name
        self.service_url = service_url
        self.service_account_email = service_account_email
        self.client = tasks_v2.CloudTasksClient()

        # Create the fully qualified queue name
        self.queue_path = self.client.queue_path(project_id, location_id, queue_name)

        logger.info(
            f"Task Queue Manager initialized for project={project_id}, " f"location={location_id}, queue={queue_name}"
        )

    def schedule_retry(
        self,
        agent_id: str,
        operation_data: Dict[str, Any],
        retry_attempt: int = 0,
        delay_seconds: Optional[int] = None,
    ) -> str:
        """
        Schedule a retry task with exponential backoff.

        Args:
            agent_id: ID of the agent to retry
            operation_data: Data for the operation to retry
            retry_attempt: Current retry attempt number (starting from 0)
            delay_seconds: Optional override for delay calculation

        Returns:
            Task name if successful, None otherwise
        """
        try:
            # Calculate delay with exponential backoff if not provided
            if delay_seconds is None:
                # Base delay is 60 seconds, doubled for each retry with a maximum of 1 hour
                delay_seconds = min(60 * (2**retry_attempt), 3600)

            # Create a timestamp for when to run the task
            scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(scheduled_time)

            # Create the task payload
            task_data = {
                "agent_id": agent_id,
                "operation": operation_data,
                "retry_attempt": retry_attempt + 1,
                "scheduled_time": scheduled_time.isoformat(),
            }

            payload = json.dumps(task_data).encode("utf-8")

            # Create task
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"{self.service_url}/tasks/retry-agent",
                    "headers": {"Content-Type": "application/json"},
                    "body": payload,
                },
                "schedule_time": timestamp,
            }

            # Add service account if provided
            if self.service_account_email:
                task["http_request"]["oidc_token"] = {
                    "service_account_email": self.service_account_email,
                    "audience": self.service_url,
                }

            # Create the task
            response = self.client.create_task(request={"parent": self.queue_path, "task": task})

            task_name = response.name
            logger.info(
                f"Scheduled retry attempt #{retry_attempt + 1} for agent '{agent_id}' "
                f"with {delay_seconds}s delay. Task name: {task_name}"
            )

            return task_name

        except Exception as e:
            logger.error(f"Failed to schedule retry for agent '{agent_id}': {str(e)}")
            return None

    def cancel_retry_tasks(self, agent_id: str) -> int:
        """
        Cancel all pending retry tasks for an agent.

        Note: Cloud Tasks doesn't directly support querying by payload fields,
        so this is a best-effort implementation that may not cancel all tasks.

        Args:
            agent_id: ID of the agent

        Returns:
            Number of tasks cancelled
        """
        try:
            # We can't directly query for tasks by agent_id, so we have to list
            # all tasks and cancel matching ones. This is inefficient but works
            # for moderate usage.
            cancelled_count = 0

            # List tasks
            response = self.client.list_tasks(parent=self.queue_path)

            for task in response:
                # Skip if task doesn't have HTTP request or body
                if (
                    not hasattr(task, "http_request")
                    or not hasattr(task.http_request, "body")
                    or not task.http_request.body
                ):
                    continue

                # Decode task body
                try:
                    body_str = task.http_request.body.decode("utf-8")
                    body = json.loads(body_str)

                    # Check if task belongs to this agent
                    if body.get("agent_id") == agent_id:
                        # Cancel task
                        self.client.delete_task(name=task.name)
                        cancelled_count += 1
                        logger.info(f"Cancelled retry task for agent '{agent_id}': {task.name}")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Skip if we can't decode the body
                    continue

            return cancelled_count

        except Exception as e:
            logger.error(f"Failed to cancel retry tasks for agent '{agent_id}': {str(e)}")
            return 0


class VertexAiFallbackHandler:
    """
    Handler for falling back to Vertex AI when Phidata agents fail.

    This class provides methods for executing operations using the
    vertex-agent@cherry-ai-project service account as a fallback.
    """

    def __init__(
        self,
        service_account: str = "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
    ):
        """
        Initialize fallback handler.

        Args:
            service_account: Service account for Vertex AI
        """
        self.service_account = service_account
        self._client = None

        logger.info(f"Vertex AI Fallback Handler initialized with service account {service_account}")

    @property
    def client(self):
        """
        Get the Vertex AI client (lazy initialization).

        Returns:
            Vertex AI client
        """
        if self._client is None:
            # Import here to avoid circular imports
            from agent.core.vertex_operations import VertexAgent

            try:
                self._client = VertexAgent()
                logger.info("Initialized Vertex AI client for fallback operations")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {str(e)}")
                # We don't raise an exception here - will be handled when the client is used

        return self._client

    async def process(self, user_input: str) -> str:
        """
        Process user input using Vertex AI as a fallback.

        Args:
            user_input: User input to process

        Returns:
            Response from Vertex AI

        Raises:
            Exception: If processing fails
        """
        try:
            if not self.client:
                raise RuntimeError("Vertex AI client not initialized")

            # Log the fallback activation
            logger.info(f"Processing user input using Vertex AI fallback: '{user_input[:50]}...'")

            # Use the client to process the input
            # Depending on your VertexAgent implementation, you might need to adjust this
            result = await self.client.process(user_input)

            # Create incident report
            from core.orchestrator.src.resilience.monitoring import get_monitoring_client

            try:
                monitoring_client = get_monitoring_client()
                monitoring_client.create_incident_report(
                    agent_id="phidata",
                    incident_data={
                        "type": "fallback_activation",
                        "input": (user_input[:100] + "..." if len(user_input) > 100 else user_input),
                        "resolution": "processed_by_openai",
                    },
                )
            except Exception as log_err:
                logger.warning(f"Failed to create incident report: {str(log_err)}")

            return result

        except Exception as e:
            logger.error(f"Vertex AI fallback processing failed: {str(e)}")
            # Return a graceful error message if processing fails
            return (
                "I'm having trouble processing your request at the moment. "
                "Our systems are experiencing some issues, but the team has been notified. "
                "Please try again later or contact support if this persists."
            )


# Global instances
_task_queue_manager = None
_task_queue_lock = threading.Lock()

_fallback_handler = None
_fallback_handler_lock = threading.Lock()


def get_task_queue_manager() -> TaskQueueManager:
    """
    Get the global task queue manager instance.

    Returns:
        Global TaskQueueManager instance
    """
    global _task_queue_manager

    with _task_queue_lock:
        if _task_queue_manager is None:
            # Get settings from environment or config
            import os

            from core.orchestrator.src.config.config import get_settings

            settings = get_settings()

            project_id = os.environ.get(
                "GCP_PROJECT_ID",
                getattr(settings, "GCP_PROJECT_ID", "cherry-ai-project"),
            )

            location_id = os.environ.get(
                "TASK_QUEUE_LOCATION",
                getattr(settings, "TASK_QUEUE_LOCATION", "us-west4"),
            )

            queue_name = os.environ.get(
                "TASK_QUEUE_NAME",
                getattr(settings, "TASK_QUEUE_NAME", "agent-retry-queue"),
            )

            # Get service URL - in Cloud Run this is injected as environment variable
            service_url = os.environ.get("SERVICE_URL", getattr(settings, "SERVICE_URL", "http://localhost:8000"))

            # Service account for authentication
            service_account = os.environ.get(
                "TASK_QUEUE_SERVICE_ACCOUNT",
                getattr(
                    settings,
                    "TASK_QUEUE_SERVICE_ACCOUNT",
                    "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
                ),
            )

            _task_queue_manager = TaskQueueManager(
                project_id=project_id,
                location_id=location_id,
                queue_name=queue_name,
                service_url=service_url,
                service_account_email=service_account,
            )

            logger.info(f"Created global Task Queue Manager for project {project_id}")

        return _task_queue_manager


def get_fallback_handler() -> VertexAiFallbackHandler:
    """
    Get the global Vertex AI fallback handler instance.

    Returns:
        Global VertexAiFallbackHandler instance
    """
    global _fallback_handler

    with _fallback_handler_lock:
        if _fallback_handler is None:
            # Get service account from environment or config
            import os

            from core.orchestrator.src.config.config import get_settings

            settings = get_settings()

            service_account = os.environ.get(
                "OPENAI_FALLBACK_SERVICE_ACCOUNT",
                getattr(
                    settings,
                    "OPENAI_FALLBACK_SERVICE_ACCOUNT",
                    "vertex-agent@cherry-ai-project.iam.gserviceaccount.com",
                ),
            )

            _fallback_handler = VertexAiFallbackHandler(service_account=service_account)

            logger.info(f"Created global Vertex AI Fallback Handler with service account {service_account}")

        return _fallback_handler
