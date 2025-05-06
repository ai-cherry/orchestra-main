#!/usr/bin/env python3
"""
Enable required GCP APIs for AI Orchestra.

This script enables the necessary Google Cloud Platform APIs for the AI Orchestra project.
"""

import argparse
import logging
import os
import sys
import time
from typing import List, Optional

# Google Cloud client libraries
from google.cloud import service_usage_v1
from google.api_core.exceptions import GoogleAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("enable_gcp_apis")

# List of required APIs
REQUIRED_APIS = [
    "run.googleapis.com",               # Cloud Run
    "artifactregistry.googleapis.com",  # Artifact Registry
    "firestore.googleapis.com",         # Firestore
    "secretmanager.googleapis.com",     # Secret Manager
    "aiplatform.googleapis.com",        # Vertex AI
    "redis.googleapis.com",             # Redis
    "cloudtasks.googleapis.com",        # Cloud Tasks
    "pubsub.googleapis.com",            # Pub/Sub
    "iam.googleapis.com",               # IAM
    "iamcredentials.googleapis.com",    # IAM Credentials
    "storage.googleapis.com",           # Cloud Storage
    "compute.googleapis.com",           # Compute Engine
    "logging.googleapis.com",           # Cloud Logging
    "monitoring.googleapis.com",        # Cloud Monitoring
]

def enable_api(project_id: str, api: str) -> bool:
    """
    Enable a GCP API using the Google Cloud Python client library.
    
    Args:
        project_id: GCP project ID
        api: API to enable
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Enabling API: {api}")
    
    try:
        # Create the Service Usage client
        client = service_usage_v1.ServiceUsageClient()
        
        # Format the service name
        service_name = f"projects/{project_id}/services/{api}"
        
        # Enable the service
        request = service_usage_v1.EnableServiceRequest(name=service_name)
        operation = client.enable_service(request=request)
        
        # Wait for the operation to complete
        logger.info(f"Waiting for API {api} to be enabled...")
        operation.result()
        
        logger.info(f"Successfully enabled API: {api}")
        return True
    except GoogleAPIError as e:
        logger.error(f"Failed to enable API {api}: {e}")
        return False

def check_api_status(project_id: str, api: str) -> bool:
    """
    Check if a GCP API is enabled using the Google Cloud Python client library.
    
    Args:
        project_id: GCP project ID
        api: API to check
    
    Returns:
        True if enabled, False otherwise
    """
    try:
        # Create the Service Usage client
        client = service_usage_v1.ServiceUsageClient()
        
        # Format the service name
        service_name = f"projects/{project_id}/services/{api}"
        
        # Get the service
        request = service_usage_v1.GetServiceRequest(name=service_name)
        service = client.get_service(request=request)
        
        # Check if the service is enabled
        return service.state == service_usage_v1.State.ENABLED
    except GoogleAPIError as e:
        logger.error(f"Failed to check API status for {api}: {e}")
        return False

def enable_apis(project_id: str, quiet: bool = False) -> bool:
    """
    Enable all required APIs.
    
    Args:
        project_id: GCP project ID
        quiet: Whether to suppress output
    
    Returns:
        True if all APIs were enabled successfully, False otherwise
    """
    success = True
    
    for api in REQUIRED_APIS:
        if check_api_status(project_id, api):
            if not quiet:
                logger.info(f"API already enabled: {api}")
        else:
            if not enable_api(project_id, api):
                success = False
    
    return success

def main() -> int:
    """
    Main function.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Enable required GCP APIs for AI Orchestra")
    parser.add_argument(
        "--project-id",
        type=str,
        default=os.environ.get("PROJECT_ID", "cherry-ai-project"),
        help="GCP project ID (default: cherry-ai-project)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output",
    )
    args = parser.parse_args()
    
    # Enable APIs
    if not enable_apis(args.project_id, args.quiet):
        logger.error("Failed to enable some APIs")
        return 1
    
    if not args.quiet:
        logger.info("All required APIs have been enabled")
    return 0

if __name__ == "__main__":
    sys.exit(main())