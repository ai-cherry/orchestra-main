"""
VertexAI Bridge Module

This module provides a bridge for VertexAI integration that works consistently
from local development environments and cloud environments, enabling seamless AI
integration regardless of where the code is running.

It handles authentication, environment detection, and provides a unified interface
for VertexAI services.
"""

import os
import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Union

# Configure logging
logger = logging.getLogger(__name__)

class EnvironmentType(Enum):
    """Enum representing different execution environments."""

    UNKNOWN = "unknown"
    LOCAL_DEVELOPMENT = "local_development"
    CLOUD_WORKSTATION = "cloud_workstation"
    CLOUD_RUN = "cloud_run"
    KUBERNETES = "kubernetes"
    COMPUTE_ENGINE = "compute_engine"
    GITHUB_ACTIONS = "github_actions"

class VertexAIBridge:
    """
    Bridge for VertexAI integration across different environments.

    This class handles authentication and provides a unified interface for
    VertexAI services regardless of the execution environment.
    """

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        """
        Initialize the VertexAI bridge.

        Args:
            project_id: Google Cloud project ID. If None, will attempt to detect from environment.
            location: Google Cloud region for VertexAI services.
        """
        self.project_id = project_id or os.environ.get("VULTR_PROJECT_ID")
        self.location = location
        self.environment = self._detect_environment()
        self.authenticated = False
        self.client = None

        logger.info(f"Initialized VertexAI Bridge in {self.environment.value} environment")

        # Auto-authenticate if project_id is provided
        if self.project_id:
            self.authenticate()

    def _detect_environment(self) -> EnvironmentType:
        """
        Detect the current execution environment.

        Returns:
            EnvironmentType enum representing the detected environment.
        """
        # Check for Cloud Run environment variable
        if os.environ.get("K_SERVICE"):
            return EnvironmentType.CLOUD_RUN

        # Check for Kubernetes environment variable
        if os.environ.get("KUBERNETES_SERVICE_HOST"):
            return EnvironmentType.KUBERNETES

        # Check for Cloud Workstations environment variable
        if os.environ.get("CLOUD_WORKSTATIONS_AGENT", "").lower() == "true":
            return EnvironmentType.CLOUD_WORKSTATION

        # Check for Compute Engine metadata
        if os.path.exists("/var/run/metadata/computeMetadata"):
            return EnvironmentType.COMPUTE_ENGINE

        # Check for GitHub Actions environment variable
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            return EnvironmentType.GITHUB_ACTIONS

        # Default to local development if no other environment is detected
        return EnvironmentType.LOCAL_DEVELOPMENT

    def authenticate(self) -> bool:
        """
        Authenticate with Google Cloud based on the detected environment.

        Returns:
            True if authentication was successful, False otherwise.
        """
        if not self.project_id:
            logger.error("Project ID is required for authentication")
            return False

        try:
            if self.environment == EnvironmentType.CLOUD_WORKSTATION:
                self._authenticate_cloud_workstation()
            elif self.environment == EnvironmentType.CLOUD_RUN:
                self._authenticate_cloud_run()
            elif self.environment == EnvironmentType.GITHUB_ACTIONS:
                self._authenticate_github_actions()
            else:
                # Default authentication method for local development and other environments
                self._authenticate_default()

            self.authenticated = True
            logger.info(f"Successfully authenticated with VertexAI in {self.environment.value} environment")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def _authenticate_default(self) -> None:
        """
        Default authentication method using Application Default Credentials.

        This works in local development with gcloud auth application-default login
        and in GCP environments with attached service accounts.
        """
        try:
            # Import here to avoid hard dependency
            # Removed GCP import import aiplatform

            # Initialize the VertexAI SDK with ADC
            aiplatform.init(project=self.project_id, location=self.location)
            self.client = aiplatform
            logger.info("Authenticated using Application Default Credentials")
        except ImportError:
            logger.error("google-cloud-aiplatform package not installed")
            raise
        except Exception as e:
            logger.error(f"Default authentication failed: {str(e)}")
            raise

    def _authenticate_cloud_workstation(self) -> None:
        """Authenticate from Cloud Workstation using attached service account."""
        self._authenticate_default()

    def _authenticate_cloud_run(self) -> None:
        """Authenticate from Cloud Run using attached service account."""
        self._authenticate_default()

    def _authenticate_github_actions(self) -> None:
        """
        Authenticate from GitHub Actions using Workload Identity Federation.

        Requires proper OIDC setup in GitHub Actions workflow
        and proper ambient credentials in GitHub Actions.
        """
        try:
            # Import here to avoid hard dependency
            # Removed GCP import import aiplatform

            # Workload Identity should be configured in GitHub Actions
            # and proper ambient credentials should be available
            aiplatform.init(project=self.project_id, location=self.location)
            self.client = aiplatform
            logger.info("Authenticated using Workload Identity Federation")
        except Exception as e:
            logger.error(f"GitHub Actions authentication failed: {str(e)}")
            raise Exception(
                "No authentication method found for GitHub Actions. "
                "Please ensure Workload Identity Federation is configured properly."
            )

    def get_client(self):
        """
        Get the authenticated VertexAI client.

        Returns:
            The authenticated VertexAI client or None if not authenticated.
        """
        if not self.authenticated:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None
        return self.client

    def predict_text(self, prompt: str, model_name: str = "text-bison") -> Dict[str, Any]:
        """
        Generate text predictions using a VertexAI text model.

        Args:
            prompt: The text prompt to send to the model
            model_name: The name of the text model to use

        Returns:
            Dictionary containing the prediction results

        Raises:
            Exception: If not authenticated or prediction fails
        """
        if not self.authenticated:
            self.authenticate()

        try:
            # Import here to avoid hard dependency
            # Removed GCP import import aiplatform

            # Get the model
            model = aiplatform.TextGenerationModel.from_pretrained(model_name)

            # Generate prediction
            response = model.predict(prompt=prompt)

            return {"text": response.text, "safety_attributes": response.safety_attributes, "model": model_name}
        except Exception as e:
            logger.error(f"Text prediction failed: {str(e)}")
            raise

    def predict_chat(self, messages: List[Dict[str, str]], model_name: str = "chat-bison") -> Dict[str, Any]:
        """
        Generate chat predictions using a VertexAI chat model.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model_name: The name of the chat model to use

        Returns:
            Dictionary containing the prediction results

        Raises:
            Exception: If not authenticated or prediction fails
        """
        if not self.authenticated:
            self.authenticate()

        try:
            # Import here to avoid hard dependency
            # Removed GCP import import aiplatform

            # Get the model
            model = aiplatform.ChatModel.from_pretrained(model_name)

            # Convert messages to the format expected by the model
            chat_messages = []
            for msg in messages:
                role = msg.get("role", "user").lower()
                content = msg.get("content", "")

                if role == "system":
                    # System messages are handled differently in VertexAI
                    chat_messages.append(aiplatform.ChatMessage(role="user", content=content))
                else:
                    chat_messages.append(aiplatform.ChatMessage(role=role, content=content))

            # Generate prediction
            response = model.predict(messages=chat_messages)

            return {"text": response.text, "safety_attributes": response.safety_attributes, "model": model_name}
        except Exception as e:
            logger.error(f"Chat prediction failed: {str(e)}")
            raise

# Singleton instance for easy access
default_bridge = VertexAIBridge()

def authenticate(project_id: Optional[str] = None, location: str = "us-central1") -> bool:
    """
    Authenticate with VertexAI using the default bridge.

    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region

    Returns:
        True if authentication was successful, False otherwise
    """
    global default_bridge
    default_bridge = VertexAIBridge(project_id=project_id, location=location)
    return default_bridge.authenticate()

def predict_text(prompt: str, model_name: str = "text-bison") -> Dict[str, Any]:
    """
    Generate text predictions using the default bridge.

    Args:
        prompt: The text prompt to send to the model
        model_name: The name of the text model to use

    Returns:
        Dictionary containing the prediction results
    """
    return default_bridge.predict_text(prompt=prompt, model_name=model_name)

def predict_chat(messages: List[Dict[str, str]], model_name: str = "chat-bison") -> Dict[str, Any]:
    """
    Generate chat predictions using the default bridge.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model_name: The name of the chat model to use

    Returns:
        Dictionary containing the prediction results
    """
    return default_bridge.predict_chat(messages=messages, model_name=model_name)
