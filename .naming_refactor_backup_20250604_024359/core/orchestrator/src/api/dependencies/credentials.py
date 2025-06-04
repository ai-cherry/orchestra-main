"""
"""
    """
    """
    logger.info("Initializing CredentialManager")
    return CredentialManager()

def get_service_account_info(
    credential_manager: CredentialManager = Depends(get_credential_manager),
) -> ServiceAccountInfo:
    """
    """
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
    """
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
    """
        logger.error("Project ID not available")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project ID not available",
        )
    return project_id

def get_environment() -> str:
    """
    """
    return os.environ.get("ENVIRONMENT", "development")
