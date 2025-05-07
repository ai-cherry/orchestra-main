"""
Dependency injection for the AI Orchestra API.

This module provides dependencies that can be injected into FastAPI route functions.
"""

import logging
from typing import Any, Dict, Generator, Optional

from fastapi import Depends, HTTPException, status
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


def get_vertex_client(
    settings: Settings = Depends(get_settings)
) -> aiplatform.gapic.PredictionServiceClient:
    """
    Get a Vertex AI prediction client.
    
    Args:
        settings: Application settings
        
    Returns:
        aiplatform.gapic.PredictionServiceClient: Vertex AI prediction client
    
    Raises:
        HTTPException: If client initialization fails
    """
    try:
        # Initialize Vertex AI
        aiplatform.init(project=settings.project_id, location=settings.vertex_location)
        
        # Create prediction client
        client = aiplatform.gapic.PredictionServiceClient(
            client_options={"api_endpoint": f"{settings.vertex_location}-aiplatform.googleapis.com"}
        )
        
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI client: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable",
        )


def get_vertex_endpoint(
    endpoint_id: str,
    settings: Settings = Depends(get_settings)
) -> str:
    """
    Get the full path to a Vertex AI endpoint.
    
    Args:
        endpoint_id: The ID of the endpoint
        settings: Application settings
        
    Returns:
        str: Full endpoint path
    """
    return f"projects/{settings.project_id}/locations/{settings.vertex_location}/endpoints/{endpoint_id}"


async def get_firestore_client() -> Generator:
    """
    Get a Firestore client.
    
    Yields:
        google.cloud.firestore.Client: Firestore client
    """
    from google.cloud import firestore
    
    try:
        client = firestore.Client()
        yield client
    except Exception as e:
        logger.error(f"Failed to initialize Firestore client: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is currently unavailable",
        )
    finally:
        # No explicit cleanup needed for Firestore client
        pass


async def get_secret_manager_client(
    settings: Settings = Depends(get_settings)
) -> Generator:
    """
    Get a Secret Manager client.
    
    Args:
        settings: Application settings
        
    Yields:
        google.cloud.secretmanager.SecretManagerServiceClient: Secret Manager client
    """
    from google.cloud import secretmanager
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        yield client
    except Exception as e:
        logger.error(f"Failed to initialize Secret Manager client: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Secret Manager service is currently unavailable",
        )
    finally:
        # No explicit cleanup needed for Secret Manager client
        pass


def get_secret(
    secret_id: str,
    version_id: str = "latest",
    settings: Settings = Depends(get_settings),
    client: secretmanager.SecretManagerServiceClient = Depends(get_secret_manager_client),
) -> str:
    """
    Get a secret from Secret Manager.
    
    Args:
        secret_id: The ID of the secret
        version_id: The version of the secret (default: "latest")
        settings: Application settings
        client: Secret Manager client
        
    Returns:
        str: Secret value
        
    Raises:
        HTTPException: If secret retrieval fails
    """
    try:
        name = f"projects/{settings.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve required configuration",
        )