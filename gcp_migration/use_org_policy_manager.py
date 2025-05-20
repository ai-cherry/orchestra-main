#!/usr/bin/env python3
"""
Organization Policy Manager for AI Orchestra GCP Migration

This script utilizes the organization policy manager service account
to modify organization policies that are blocking Cloud Run and Vertex AI access.

Author: Roo
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def log(message: str) -> None:
    """Print a log message with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_command(cmd: str, env: Optional[Dict[str, str]] = None) -> Tuple[int, str]:
    """Run a shell command and return exit code and output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    print(f"Exit code: {result.returncode}")
    return result.returncode, result.stdout + result.stderr


def setup_service_account_auth(service_account_json: str) -> Dict[str, str]:
    """Set up authentication using service account JSON.

    Args:
        service_account_json: Service account JSON content or path to JSON file

    Returns:
        Environment dict with GOOGLE_APPLICATION_CREDENTIALS set
    """
    # Check if input is a path to a file
    if os.path.isfile(service_account_json):
        key_path = service_account_json
    else:
        # Create a temporary file with the JSON content
        fd, key_path = tempfile.mkstemp(suffix=".json")
        try:
            with open(fd, "w") as f:
                f.write(service_account_json)
        finally:
            os.close(fd)

    # Set up environment with credentials
    env = os.environ.copy()
    env["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

    # Test authentication
    log(f"Testing authentication with service account key at {key_path}")
    exit_code, output = run_command(
        'gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"',
        env=env,
    )
    if exit_code != 0:
        log(f"Authentication failed: {output}")
        return {}

    log("Authentication successful")
    return env


def check_org_policies(project_id: str, env: Dict[str, str]) -> List[str]:
    """Check organization policies affecting Cloud Run and Vertex AI.

    Args:
        project_id: GCP project ID
        env: Environment dict with authentication credentials

    Returns:
        List of policy constraints that need to be modified
    """
    log(f"Checking organization policies for project {project_id}")

    # List of policy constraints to check
    constraints_to_check = [
        "iam.allowedPolicyMemberDomains",
        "run.requireInvokerIam",
        "run.allowedIngress",
        "vertexai.allowedModels",
        "vertexai.allowedGenAIModels",
    ]

    # List policies
    exit_code, output = run_command(
        f"gcloud org-policies list --project={project_id} --format=json", env=env
    )
    if exit_code != 0:
        log(f"Failed to list org policies: {output}")
        return []

    # Parse the output
    try:
        policies = json.loads(output)
    except json.JSONDecodeError:
        log(f"Failed to parse policies output: {output}")
        return []

    # Extract policy constraints that are active
    active_policies = []
    policy_names = [policy.get("name", "") for policy in policies]

    for constraint in constraints_to_check:
        constraint_name = f"projects/{project_id}/policies/{constraint}"
        if any(constraint_name in policy_name for policy_name in policy_names):
            active_policies.append(constraint)
            # Get policy details
            run_command(
                f"gcloud org-policies describe {constraint} --project={project_id}",
                env=env,
            )

    return active_policies


def fix_cloud_run_policy(project_id: str, env: Dict[str, str]) -> bool:
    """Fix Cloud Run organization policies.

    Args:
        project_id: GCP project ID
        env: Environment dict with authentication credentials

    Returns:
        True if policy was fixed, False otherwise
    """
    log("Fixing Cloud Run organization policies")

    # Create policy file to disable run.requireInvokerIam
    policy_dir = Path("gcp_migration/policies")
    policy_dir.mkdir(exist_ok=True)

    # Create policy file
    policy_path = policy_dir / "run_invoker_policy.yaml"
    with open(policy_path, "w") as f:
        f.write(
            f"""name: projects/{project_id}/policies/run.requireInvokerIam
spec:
  rules:
  - enforce: false
"""
        )

    log(f"Created policy file at {policy_path}")

    # Apply the policy
    exit_code, output = run_command(
        f"gcloud org-policies set-policy {policy_path}", env=env
    )
    if exit_code != 0:
        log(f"Failed to apply Cloud Run policy: {output}")
        return False

    return True


def fix_vertex_ai_policy(project_id: str, env: Dict[str, str]) -> bool:
    """Fix Vertex AI organization policies.

    Args:
        project_id: GCP project ID
        env: Environment dict with authentication credentials

    Returns:
        True if policy was fixed, False otherwise
    """
    log("Fixing Vertex AI organization policies")

    # Create policy directory
    policy_dir = Path("gcp_migration/policies")
    policy_dir.mkdir(exist_ok=True)

    # Create policy for vertexai.allowedModels
    models_policy_path = policy_dir / "vertex_models_policy.yaml"
    with open(models_policy_path, "w") as f:
        f.write(
            f"""name: projects/{project_id}/policies/vertexai.allowedModels
spec:
  rules:
  - values:
      allowedValues:
      - resource://aiplatform.googleapis.com/projects/{project_id}/locations/*
"""
        )

    # Create policy for vertexai.allowedGenAIModels
    genai_policy_path = policy_dir / "vertex_genai_policy.yaml"
    with open(genai_policy_path, "w") as f:
        f.write(
            f"""name: projects/{project_id}/policies/vertexai.allowedGenAIModels
spec:
  rules:
  - values:
      allowedValues:
      - "*"
"""
        )

    # Apply Vertex AI models policy
    log(f"Applying Vertex AI models policy from {models_policy_path}")
    exit_code, output = run_command(
        f"gcloud org-policies set-policy {models_policy_path}", env=env
    )
    if exit_code != 0:
        log(f"Failed to apply Vertex AI models policy: {output}")
        return False

    # Apply Vertex AI GenAI policy
    log(f"Applying Vertex AI GenAI policy from {genai_policy_path}")
    exit_code, output = run_command(
        f"gcloud org-policies set-policy {genai_policy_path}", env=env
    )
    if exit_code != 0:
        log(f"Failed to apply Vertex AI GenAI policy: {output}")
        return False

    return True


def fix_allowed_member_domains_policy(project_id: str, env: Dict[str, str]) -> bool:
    """Fix allowed policy member domains organization policy.

    Args:
        project_id: GCP project ID
        env: Environment dict with authentication credentials

    Returns:
        True if policy was fixed, False otherwise
    """
    log("Fixing allowed policy member domains organization policy")

    # Create policy directory
    policy_dir = Path("gcp_migration/policies")
    policy_dir.mkdir(exist_ok=True)

    # Create policy file
    policy_path = policy_dir / "allowed_domains_policy.yaml"
    with open(policy_path, "w") as f:
        f.write(
            f"""name: projects/{project_id}/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - values:
      allowedValues:
      - "domain:cherry-ai.me"
      - "allUsers"
      - "allAuthenticatedUsers"
"""
        )

    # Apply the policy
    log(f"Applying allowed domains policy from {policy_path}")
    exit_code, output = run_command(
        f"gcloud org-policies set-policy {policy_path}", env=env
    )
    if exit_code != 0:
        log(f"Failed to apply allowed domains policy: {output}")
        return False

    return True


def update_cloud_run_service(
    project_id: str, service_name: str, region: str, env: Dict[str, str]
) -> bool:
    """Update Cloud Run service to allow unauthenticated access.

    Args:
        project_id: GCP project ID
        service_name: Name of the Cloud Run service
        region: GCP region
        env: Environment dict with authentication credentials

    Returns:
        True if service was updated, False otherwise
    """
    log(f"Updating Cloud Run service {service_name} to allow unauthenticated access")

    # Update service
    exit_code, output = run_command(
        f"gcloud run services update {service_name} --region={region} --allow-unauthenticated",
        env=env,
    )
    if exit_code != 0:
        log(f"Failed to update Cloud Run service: {output}")
        return False

    # Verify update
    exit_code, output = run_command(
        f"gcloud run services describe {service_name} --region={region} --format='value(status.url)'",
        env=env,
    )
    if exit_code != 0:
        log(f"Failed to get Cloud Run service status: {output}")
        return False

    service_url = output.strip()
    log(f"Cloud Run service URL: {service_url}")

    # Test the service
    exit_code, output = run_command(f"curl -s -i {service_url}/health", env=env)
    log(f"Service health check result: {output}")

    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Organization Policy Manager for AI Orchestra GCP Migration"
    )
    parser.add_argument(
        "--json-secret",
        default=os.environ.get("GCP_ORGANIZATION_POLICY_JSON", ""),
        help="Service account JSON content or path to JSON file (also can be set via GCP_ORGANIZATION_POLICY_JSON env var)",
    )
    parser.add_argument(
        "--project-id", default="cherry-ai-project", help="GCP project ID"
    )
    parser.add_argument(
        "--service-name", default="ai-orchestra-minimal", help="Cloud Run service name"
    )
    parser.add_argument("--region", default="us-central1", help="GCP region")

    args = parser.parse_args()

    # Validate inputs
    if not args.json_secret:
        print(
            "Error: Service account JSON is required. Please provide it via --json-secret or GCP_ORGANIZATION_POLICY_JSON env var."
        )
        return 1

    # Setup authentication
    env = setup_service_account_auth(args.json_secret)
    if not env:
        print("Error: Failed to set up authentication.")
        return 1

    # Check organization policies
    active_policies = check_org_policies(args.project_id, env)
    log(f"Active policies requiring modification: {active_policies}")

    # Fix organization policies
    success = True

    # Fix Cloud Run policy if needed
    if "run.requireInvokerIam" in active_policies:
        if not fix_cloud_run_policy(args.project_id, env):
            success = False

    # Fix Vertex AI policies if needed
    if (
        "vertexai.allowedModels" in active_policies
        or "vertexai.allowedGenAIModels" in active_policies
    ):
        if not fix_vertex_ai_policy(args.project_id, env):
            success = False

    # Fix allowed member domains policy if needed
    if "iam.allowedPolicyMemberDomains" in active_policies:
        if not fix_allowed_member_domains_policy(args.project_id, env):
            success = False

    # Update Cloud Run service
    if not update_cloud_run_service(
        args.project_id, args.service_name, args.region, env
    ):
        success = False

    # Final status check
    if success:
        log("Organization policies successfully updated!")
        return 0
    else:
        log("Some policy updates failed. Check the logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
