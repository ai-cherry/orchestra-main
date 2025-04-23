"""
GCP Authentication utilities for the AI Orchestration System.

This module provides utilities for authenticating with Google Cloud Platform
services, with support for different authentication methods and sources.
"""

import os
import json
import tempfile
import logging
import atexit
from typing import Optional, Any, Dict, List, Tuple

# Import Google Cloud libraries
try:
    from google.oauth2 import service_account
    from google.auth.exceptions import DefaultCredentialsError
    from google.auth import default as google_default
except ImportError:
    service_account = None
    DefaultCredentialsError = Exception
    
    def google_default(*args, **kwargs):
        raise ImportError("Google Cloud libraries not installed")

# Configure logger
logger = logging.getLogger(__name__)

# Store temporary file paths for cleanup
_temp_files = []


def _cleanup_temp_files():
    """Clean up any temporary credential files at exit."""
    for temp_file_path in _temp_files:
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary credentials file: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


# Register cleanup handler
atexit.register(_cleanup_temp_files)


def get_gcp_credentials(
    service_account_json: Optional[str] = None,
    service_account_file: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    project_id: Optional[str] = None
) -> Tuple[Any, str]:
    """
    Get Google Cloud credentials from various sources.
    
    Priority order:
    1. service_account_json (contents of a service account key JSON)
    2. service_account_file (path to a service account key file)
    3. GOOGLE_APPLICATION_CREDENTIALS environment variable
    4. Application Default Credentials
    
    Args:
        service_account_json: JSON string of service account key
        service_account_file: Path to service account key file
        scopes: Optional OAuth scopes to request
        project_id: Optional project ID override
        
    Returns:
        Tuple of (credentials object, project_id)
    """
    if service_account is None:
        raise ImportError(
            "Google Cloud libraries not installed. "
            "Install with: pip install google-auth google-cloud-core"
        )
    
    temp_file_path = None
    
    try:
        # Case 1: Service account JSON string provided
        if service_account_json:
            # Create a temporary file to hold the credentials
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
            temp_file_path = temp_file.name
            temp_file.write(service_account_json.encode('utf-8'))
            temp_file.flush()
            temp_file.close()
            
            # Add to cleanup list
            _temp_files.append(temp_file_path)
            
            logger.info("Using provided service account JSON content")
            credentials = service_account.Credentials.from_service_account_file(
                temp_file_path, scopes=scopes
            )
            
            # Extract project_id from the service account JSON if not provided
            if not project_id:
                try:
                    sa_info = json.loads(service_account_json)
                    project_id = sa_info.get('project_id')
                except (json.JSONDecodeError, KeyError):
                    logger.warning("Could not extract project_id from service account JSON")
            
            return credentials, project_id
            
        # Case 2: Service account file path provided
        if service_account_file:
            if not os.path.exists(service_account_file):
                raise FileNotFoundError(f"Service account file not found: {service_account_file}")
                
            logger.info(f"Using service account file: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=scopes
            )
            
            # Extract project_id from the service account file if not provided
            if not project_id:
                try:
                    with open(service_account_file, 'r') as f:
                        sa_info = json.load(f)
                        project_id = sa_info.get('project_id')
                except (json.JSONDecodeError, KeyError, IOError):
                    logger.warning("Could not extract project_id from service account file")
            
            return credentials, project_id
            
        # Case 3 & 4: Environment variable or application default credentials
        # Let the Google Auth library handle these cases
        credentials, detected_project_id = google_default(scopes=scopes)
        
        # Use the detected project_id if none was provided
        if not project_id:
            project_id = detected_project_id
            
        # If still no project_id, try to get it from environment variables
        if not project_id:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or \
                         os.environ.get('GCP_PROJECT_ID')
            
        logger.info(f"Using application default credentials for project: {project_id}")
        return credentials, project_id
            
    except (DefaultCredentialsError, FileNotFoundError) as e:
        logger.error(f"Error obtaining GCP credentials: {e}")
        raise


def setup_gcp_credentials_file() -> Optional[str]:
    """
    Set up GCP credentials from environment variables.
    
    Reads the GCP_SA_KEY_JSON environment variable, writes it to a temporary
    file, and sets GOOGLE_APPLICATION_CREDENTIALS to point to that file.
    
    Returns:
        Path to the credentials file or None if not set up
    """
    gcp_sa_key = os.environ.get('GCP_SA_KEY_JSON')
    if not gcp_sa_key:
        logger.info("GCP_SA_KEY_JSON environment variable not found")
        return None
        
    try:
        # Validate JSON format
        json.loads(gcp_sa_key)
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file_path = temp_file.name
        temp_file.write(gcp_sa_key.encode('utf-8'))
        temp_file.flush()
        temp_file.close()
        
        # Add to cleanup list
        _temp_files.append(temp_file_path)
        
        # Set environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file_path
        logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to {temp_file_path}")
        
        return temp_file_path
    except json.JSONDecodeError:
        logger.error("GCP_SA_KEY_JSON environment variable contains invalid JSON")
        return None
    except Exception as e:
        logger.error(f"Error setting up GCP credentials file: {e}")
        return None


def get_project_id() -> Optional[str]:
    """
    Get the Google Cloud project ID from environment variables.
    
    Returns:
        Project ID or None if not found
    """
    # Try several environment variables that might contain the project ID
    for env_var in ['GCP_PROJECT_ID', 'GOOGLE_CLOUD_PROJECT', 'GCLOUD_PROJECT']:
        project_id = os.environ.get(env_var)
        if project_id:
            return project_id
    
    # If no environment variable is set, try to extract from credentials
    try:
        # Check if GOOGLE_APPLICATION_CREDENTIALS points to a file
        creds_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_file and os.path.isfile(creds_file):
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
                if 'project_id' in creds_data:
                    return creds_data['project_id']
    except Exception as e:
        logger.debug(f"Failed to extract project ID from credentials file: {e}")
    
    # As a last resort, try to get it from Application Default Credentials
    try:
        _, project_id = google_default()
        if project_id:
            return project_id
    except Exception as e:
        logger.debug(f"Failed to get project ID from default credentials: {e}")
    
    return None


def initialize_gcp_auth() -> Dict[str, Any]:
    """
    Initialize GCP authentication for the application.
    
    This function sets up GCP credentials from environment variables
    and returns information about the authentication setup.
    
    Returns:
        Dictionary with authentication information
    """
    result = {
        'success': False,
        'method': None,
        'project_id': None,
        'service_account': None,
        'credentials_file': None,
    }
    
    # First, try to set up credentials from GCP_SA_KEY_JSON
    creds_file = setup_gcp_credentials_file()
    if creds_file:
        result['success'] = True
        result['method'] = 'service_account_json'
        result['credentials_file'] = creds_file
        
        # Try to extract project ID and service account from the credentials
        try:
            with open(creds_file, 'r') as f:
                creds_data = json.load(f)
                result['project_id'] = creds_data.get('project_id')
                result['service_account'] = creds_data.get('client_email')
        except Exception as e:
            logger.warning(f"Failed to extract information from credentials file: {e}")
    
    # If that didn't work, try to get project ID from environment
    if not result['project_id']:
        result['project_id'] = get_project_id()
        
    # If we found a project ID but no credentials file, we're using ADC
    if result['project_id'] and not creds_file:
        result['success'] = True
        result['method'] = 'application_default'
    
    # Log the results
    if result['success']:
        logger.info(
            f"GCP authentication initialized: method={result['method']}, "
            f"project_id={result['project_id']}, "
            f"service_account={result['service_account']}"
        )
    else:
        logger.warning("Failed to initialize GCP authentication")
    
    return result
