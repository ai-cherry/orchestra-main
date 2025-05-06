"""
Credential dependencies for FastAPI.

This module provides FastAPI dependencies for credential management.
"""

import logging
import os
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status

from core.security.credential_manager import CredentialManager, ServiceAccountInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@lru_cache()
def get_credential_manager() -> CredentialManager:
    """
    Get a cached instance of the CredentialManager.
    
    This function is cached to ensure that only one instance of the
    CredentialManager is created, which helps with performance and
    resource management.
    
    Returns:
        CredentialManager: An instance of the credential manager
    """
    logger.info("Initializing CredentialManager")
    return CredentialManager()


def get_service_account_info(
    credential_manager: CredentialManager = Depends(get_credential_manager),
) -> ServiceAccountInfo:
    """
    Get the service account information.
    
    This dependency provides the service account information to FastAPI routes.
    If the service account information is not available, it raises an HTTP 500 error.
    
    Args:
        credential_manager: The credential manager instance
        
    Returns:
        ServiceAccountInfo: The service account information
        
    Raises:
        HTTPException: If the service account information is not available
    """
    service_account_info = credential_manager.get_service_account_key()
    if not service_account_info:
        logger.error("Service account information not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service account information not available",
        )
    return service_account_info


def get_service_account_path(
    credential_manager: CredentialManager = Depends(get_credential_manager),
) -> str:
    """
    Get the path to the service account key file.
    
    This dependency provides the path to a temporary file containing the
    service account key to FastAPI routes. If the service account key is
    not available, it raises an HTTP 500 error.
    
    Args:
        credential_manager: The credential manager instance
        
    Returns:
        str: The path to the service account key file
        
    Raises:
        HTTPException: If the service account key is not available
    """
    service_account_path = credential_manager.get_service_account_key_path()
    if not service_account_path:
        logger.error("Service account key path not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service account key path not available",
        )
    return service_account_path


def get_project_id(
    credential_manager: CredentialManager = Depends(get_credential_manager),
) -> str:
    """
    Get the GCP project ID.
    
    This dependency provides the GCP project ID to FastAPI routes.
    If the project ID is not available, it raises an HTTP 500 error.
    
    Args:
        credential_manager: The credential manager instance
        
    Returns:
        str: The GCP project ID
        
    Raises:
        HTTPException: If the project ID is not available
    """
    project_id = credential_manager.get_project_id()
    if not project_id:
        logger.error("Project ID not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project ID not available",
        )
    return project_id


def get_environment() -> str:
    """
    Get the current environment.
    
    This dependency provides the current environment (e.g., development,
    staging, production) to FastAPI routes.
    
    Returns:
        str: The current environment
    """
    return os.environ.get("ENVIRONMENT", "development")