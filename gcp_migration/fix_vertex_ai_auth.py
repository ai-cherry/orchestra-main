#!/usr/bin/env python3
"""
Fix Vertex AI Authentication

This script creates a service account key and adds necessary IAM permissions
for accessing Vertex AI services.

Author: Roo
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


def run_command(cmd: str) -> Tuple[int, str]:
    """Run a shell command and return exit code and output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    return result.returncode, result.stdout + result.stderr


def log(message: str) -> None:
    """Print a log message with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def setup_vertex_ai_permissions(
    project_id: str, service_account: str, service_account_key_path: Optional[str] = None
) -> bool:
    """Set up Vertex AI permissions for the service account.
    
    Args:
        project_id: GCP project ID
        service_account: Service account email
        service_account_key_path: Path to save service account key (optional)
        
    Returns:
        True if successful, False otherwise
    """
    log(f"Setting up Vertex AI permissions for {service_account}")
    
    # Check if service account exists
    exit_code, output = run_command(
        f"gcloud iam service-accounts describe {service_account} --project={project_id}"
    )
    if exit_code != 0:
        log(f"Service account {service_account} does not exist")
        return False
    
    # Add required roles for Vertex AI
    roles = [
        "roles/aiplatform.user",
        "roles/aiplatform.serviceAgent",
        "roles/ml.developer",
        "roles/storage.objectViewer"
    ]
    
    for role in roles:
        log(f"Adding role {role} to {service_account}")
        exit_code, output = run_command(
            f"gcloud projects add-iam-policy-binding {project_id} "
            f"--member=serviceAccount:{service_account} --role={role}"
        )
        if exit_code != 0:
            log(f"Failed to add role {role}: {output}")
            return False
    
    # Create a service account key if path provided
    if service_account_key_path:
        key_path = Path(service_account_key_path)
        key_path.parent.mkdir(parents=True, exist_ok=True)
        
        log(f"Creating service account key at {key_path}")
        exit_code, output = run_command(
            f"gcloud iam service-accounts keys create {key_path} "
            f"--iam-account={service_account} --project={project_id}"
        )
        if exit_code != 0:
            log(f"Failed to create service account key: {output}")
            return False
    
    return True


def test_vertex_ai_connectivity(project_id: str, region: str, key_path: Optional[str] = None) -> bool:
    """Test connectivity to Vertex AI.
    
    Args:
        project_id: GCP project ID
        region: GCP region
        key_path: Path to service account key file (optional)
        
    Returns:
        True if successful, False otherwise
    """
    log("Testing Vertex AI connectivity")
    
    # Set up environment for test
    env = os.environ.copy()
    if key_path:
        env["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    
    # Create a simple test script
    test_script = """
import os
from google.cloud import aiplatform

# Print current auth details
print(f"Using credentials: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Default credentials')}")

# Initialize Vertex AI
aiplatform.init(project="{project}", location="{region}")

# List models (this will fail if permissions are not set correctly)
print("Listing models...")
models = list(aiplatform.Model.list())
print(f"Found {len(models)} models")

# List endpoints
print("Listing endpoints...")
endpoints = list(aiplatform.Endpoint.list())
print(f"Found {len(endpoints)} endpoints")

print("Vertex AI connectivity test passed!")
    """.format(project=project_id, region=region)
    
    # Write the test script to a temporary file
    test_script_path = "/tmp/test_vertex_ai.py"
    with open(test_script_path, "w") as f:
        f.write(test_script)
    
    # Run the test script
    cmd = f"python3 {test_script_path}"
    exit_code, output = run_command(cmd)
    
    if exit_code == 0:
        log("Vertex AI connectivity test passed!")
        return True
    else:
        log(f"Vertex AI connectivity test failed: {output}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Fix Vertex AI Authentication")
    parser.add_argument("--project-id", default="cherry-ai-project", help="GCP project ID")
    parser.add_argument("--region", default="us-central1", help="GCP region")
    parser.add_argument("--service-account", default=None, help="Service account email")
    parser.add_argument("--key-path", default=None, help="Path to save service account key")
    
    args = parser.parse_args()
    
    project_id = args.project_id
    region = args.region
    
    # If service account not provided, try to get from gcloud config
    service_account = args.service_account
    if not service_account:
        exit_code, output = run_command("gcloud config get-value account")
        if exit_code == 0 and output.strip():
            service_account = output.strip()
            if not service_account.endswith("@" + project_id + ".iam.gserviceaccount.com"):
                service_account = f"codespaces-powerful-sa@{project_id}.iam.gserviceaccount.com"
        else:
            service_account = f"codespaces-powerful-sa@{project_id}.iam.gserviceaccount.com"
    
    log(f"Using service account: {service_account}")
    
    # Setup permissions
    if not setup_vertex_ai_permissions(project_id, service_account, args.key_path):
        log("Failed to set up Vertex AI permissions")
        sys.exit(1)
    
    # Test connectivity
    if not test_vertex_ai_connectivity(project_id, region, args.key_path):
        log("Failed to connect to Vertex AI")
        sys.exit(1)
    
    log("Vertex AI authentication fixed successfully!")


if __name__ == "__main__":
    main()