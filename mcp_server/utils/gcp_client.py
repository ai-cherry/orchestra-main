"""
Shared GCP client initialization and error handling utilities for MCP servers.
Ensures DRY, robust, and elegant integration with Google Cloud services.
"""

import logging
from typing import Optional
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

def init_gcp_client(client_cls, project_id: str, **kwargs):
    """
    Initialize a GCP client with standardized error handling.
    Args:
        client_cls: The GCP client class (e.g., secretmanager.SecretManagerServiceClient)
        project_id: The GCP project ID
        kwargs: Additional arguments for the client constructor
    Returns:
        An instance of the client, or None if initialization fails.
    """
    try:
        client = client_cls(project=project_id, **kwargs)
        logger.info(f"Initialized {client_cls.__name__} for project {project_id}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize {client_cls.__name__}: {e}")
        return None

def handle_gcp_error(e: Exception, context: str = "") -> str:
    """
    Standardized error formatting for GCP exceptions.
    Args:
        e: The exception instance
        context: Optional context string for logging
    Returns:
        A formatted error message string
    """
    if context:
        logger.error(f"{context}: {e}")
    else:
        logger.error(str(e))
    if isinstance(e, GoogleAPIError):
        return f"GCP API Error: {e.message}"
    return str(e)