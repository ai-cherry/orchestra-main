#!/usr/bin/env python3
"""
Secret Manager Validation Script for Orchestra

This script validates that:
1. Required secrets exist in Secret Manager
2. The application can access these secrets with proper credentials
3. Environment-specific secrets are correctly configured
4. Service account permissions are properly set up
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Set
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("secret_validator")

# Try importing Google Cloud libraries, with helpful error if missing
try:
    from google.cloud import secretmanager
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    logger.error("Google Cloud libraries not found. Install with: pip install google-cloud-secretmanager")
    sys.exit(1)

# Required secrets by category - these should be present in all environments
REQUIRED_SECRETS = {
    "llm_api_keys": {
        "openai-api-key",
        "anthropic-api-key",
        "openrouter-api-key",
    },
    "tool_api_keys": {
        "portkey-api-key",
        "tavily-api-key",
    },
    "infrastructure": {
        "redis-auth",
        "db-credentials",
    },
    "gcp_secrets": {
        "gcp-client-secret",
        "gcp-service-account-key",
    }
}

# Production-only secrets that should only exist in prod environment
PROD_ONLY_SECRETS = {
    "oauth-client-secret-prod",
    "vertex-agent-key-prod",
}

# Secrets that should NOT exist in production (development/test only)
NON_PROD_SECRETS = {
    "service-account-keys",
}

def get_project_id() -> Optional[str]:
    """Get GCP project ID from environment or credentials"""
    # Try environment variables first
    project_id = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        # Try to get from default credentials
        try:
            _, project_id = default()
        except DefaultCredentialsError:
            logger.error("Could not determine GCP project ID. Set GCP_PROJECT_ID environment variable.")
            return None
    
    return project_id

def list_available_secrets(project_id: str) -> List[str]:
    """List all secrets available in the project"""
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{project_id}"
    
    try:
        secrets = client.list_secrets(request={"parent": parent})
        return [secret.name.split('/')[-1] for secret in secrets]
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        return []

def test_secret_access(project_id: str, secret_id: str) -> bool:
    """Test if we can access a specific secret"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    try:
        # Just check if we can access it, don't actually use the value
        client.access_secret_version(request={"name": name})
        return True
    except Exception as e:
        logger.error(f"Cannot access secret {secret_id}: {e}")
        return False

def validate_environment_separation(secrets: List[str], env: str) -> bool:
    """Validate that environment-specific secrets are properly separated"""
    success = True
    
    # Check that we have the correct environment suffix on secrets
    for secret in secrets:
        if "-dev" in secret and env != "dev":
            logger.warning(f"Found dev secret {secret} in {env} environment")
            success = False
        elif "-prod" in secret and env != "prod":
            logger.warning(f"Found prod secret {secret} in {env} environment")
            success = False
    
    # Validate production-only secrets
    if env == "prod":
        for secret in PROD_ONLY_SECRETS:
            if secret not in secrets:
                logger.error(f"Missing required production secret: {secret}")
                success = False
        
        # Check that dev-only secrets are not in prod
        for secret in secrets:
            if any(non_prod in secret for non_prod in NON_PROD_SECRETS):
                logger.error(f"Development secret {secret} found in production environment")
                success = False
    
    return success

def check_required_secrets(project_id: str, available_secrets: List[str], env: str) -> bool:
    """Check that all required secrets exist and are accessible"""
    success = True
    
    for category, secret_set in REQUIRED_SECRETS.items():
        logger.info(f"Checking {category} secrets...")
        for base_secret in secret_set:
            secret_id = f"{base_secret}-{env}"
            
            if secret_id not in available_secrets:
                logger.error(f"Required secret {secret_id} not found")
                success = False
                continue
            
            # Test access to the secret
            if not test_secret_access(project_id, secret_id):
                logger.error(f"Cannot access required secret {secret_id}")
                success = False
    
    return success

def validate_cloud_run_service_access(project_id: str, service_name: str, env: str) -> bool:
    """Validate that a Cloud Run service has necessary permissions to access secrets"""
    import subprocess
    import json
    
    try:
        # Get the service account associated with the Cloud Run service
        result = subprocess.run(
            ["gcloud", "run", "services", "describe", f"{service_name}-{env}", 
             "--project", project_id, "--format", "json"],
            capture_output=True, text=True, check=True
        )
        
        service_info = json.loads(result.stdout)
        service_account = service_info.get("serviceAccountEmail", "")
        
        if not service_account:
            logger.error(f"Could not determine service account for {service_name}-{env}")
            return False
        
        logger.info(f"Service {service_name}-{env} uses service account: {service_account}")
        
        # Check if the service account has the secretmanager.secretAccessor role
        result = subprocess.run(
            ["gcloud", "projects", "get-iam-policy", project_id, 
             "--format", "json"],
            capture_output=True, text=True, check=True
        )
        
        policy = json.loads(result.stdout)
        
        # Check if service account has secret accessor role
        has_access = False
        for binding in policy.get("bindings", []):
            if binding.get("role") == "roles/secretmanager.secretAccessor":
                if f"serviceAccount:{service_account}" in binding.get("members", []):
                    has_access = True
                    break
        
        if not has_access:
            logger.error(f"Service account {service_account} does not have secretAccessor role")
            return False
            
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check Cloud Run service access: {e}")
        logger.error(f"Command output: {e.stdout} {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error validating Cloud Run service access: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate Secret Manager configuration")
    parser.add_argument("--env", default="dev", choices=["dev", "staging", "prod"],
                      help="Environment to validate (dev, staging, prod)")
    parser.add_argument("--project-id", help="GCP Project ID (defaults to environment variable)")
    parser.add_argument("--service", default="orchestra-api", 
                      help="Cloud Run service name to validate access for")
    
    args = parser.parse_args()
    
    # Get project ID
    project_id = args.project_id or get_project_id()
    if not project_id:
        logger.error("Could not determine GCP project ID")
        sys.exit(1)
    
    env = args.env
    logger.info(f"Validating Secret Manager in project {project_id} for {env} environment")
    
    # List all secrets
    available_secrets = list_available_secrets(project_id)
    if not available_secrets:
        logger.error("No secrets found or insufficient permissions")
        sys.exit(1)
    
    logger.info(f"Found {len(available_secrets)} secrets")
    
    # Check required secrets
    required_ok = check_required_secrets(project_id, available_secrets, env)
    if not required_ok:
        logger.warning("Some required secrets are missing or inaccessible")
    
    # Check environment separation
    env_ok = validate_environment_separation(available_secrets, env)
    if not env_ok:
        logger.warning("Environment separation issues detected")
    
    # Validate Cloud Run service access
    service_ok = validate_cloud_run_service_access(project_id, args.service, env)
    if not service_ok:
        logger.warning(f"Cloud Run service {args.service}-{env} may not have proper secret access")
    
    # Overall result
    if required_ok and env_ok and service_ok:
        logger.info("✅ All secret validations passed successfully!")
        return 0
    else:
        logger.error("❌ Some secret validations failed. See logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())