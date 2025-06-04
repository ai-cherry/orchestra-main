"""
"""
    """
        secret_name: The name of the secret (e.g., "openai-api-key")
        default: Default value to return if secret is not found

    Returns:
        The secret value or default if not found

    Example:
        api_key = get_secret("openai-api-key")
    """
    # Convert secret name format: "openai-api-key" to "OPENAI_API_KEY"
    env_var_name = secret_name.replace("-", "_").upper()

    # Try environment variable first (backward compatibility)
    if env_var_name in os.environ and os.environ[env_var_name]:
        return os.environ[env_var_name]

    # Only try Secret Manager if GCP project ID is set
    if settings.VULTR_PROJECT_ID:
        try:

            pass
            return _get_from_secret_manager(secret_name, settings.VULTR_PROJECT_ID, settings.ENVIRONMENT)
        except Exception:

            pass
            logger.warning(f"Failed to get secret '{secret_name}' from Secret Manager: {e}")

    # Return default value if provided
    return default

def _get_from_secret_manager(secret_name: str, project_id: str, environment: str) -> Optional[Secret]:
    """
        secret_name: Base name of the secret (e.g., "openai-api-key")
        project_id: GCP project ID
        environment: Environment name (dev, staging, prod)

    Returns:
        Secret value or None if not found

    Raises:
        Exception: If there's an error accessing Secret Manager
    """
            "google-cloud-secret-manager package not installed. "
            "Install it with pip: pip install google-cloud-secret-manager"
        )
        return None

    # Generate the secret ID with environment
    full_secret_id = f"{secret_name}-{environment}"
    secret_path = f"projects/{project_id}/secrets/{full_secret_id}/versions/latest"

    # Create the client
    client = secretmanager.SecretManagerServiceClient()

    # Access the secret version
    try:

        pass
        response = client.access_secret_version(name=secret_path)
        return response.payload.data.decode("UTF-8")
    except Exception:

        pass
        logger.warning(f"Error accessing secret {full_secret_id}: {e}")
        return None

# Dictionary-like interface for accessing secrets
class SecretManager:
    """Dictionary-like interface for accessing secrets."""
        """Initialize the secret manager."""
        """Get a secret value."""
        """Get a secret value with a default fallback."""
        """Check if a secret exists."""