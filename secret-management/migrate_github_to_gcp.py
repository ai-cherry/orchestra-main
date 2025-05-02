#!/usr/bin/env python3
"""
GitHub Secrets to GCP Secret Manager Migration Tool

This script automates the migration of GitHub repository secrets to 
Google Cloud Secret Manager with support for:
- Conditional access policies
- Appropriate IAM permissions
- Secret organization and labeling
- Validation and reporting

Usage:
    python migrate_github_to_gcp.py --project-id=PROJECT_ID --repo=OWNER/REPO 
    
Requirements:
    - PyGithub
    - google-cloud-secret-manager
    - python-dotenv
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Third-party imports
try:
    from dotenv import load_dotenv
    from github import Github, GithubException, Auth
    from google.cloud import secretmanager
    from google.api_core import exceptions as gcp_exceptions
except ImportError:
    print("Required dependencies not installed. Run:")
    print("pip install PyGithub google-cloud-secret-manager python-dotenv")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("github_to_gcp_migration.log"),
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
load_dotenv()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate GitHub repository secrets to GCP Secret Manager"
    )
    
    # Required arguments
    parser.add_argument(
        "--project-id", 
        required=True,
        help="GCP Project ID where secrets will be stored"
    )
    
    # GitHub repository specification
    parser.add_argument(
        "--repo",
        help="GitHub repository in the format 'owner/repo'"
    )
    
    parser.add_argument(
        "--org",
        help="GitHub organization (for org secrets instead of repo secrets)"
    )
    
    # Authentication options
    parser.add_argument(
        "--github-token",
        help="GitHub Personal Access Token (or set GITHUB_TOKEN env var)"
    )
    
    # Secret filtering
    parser.add_argument(
        "--include",
        help="Only include secrets matching these prefixes (comma-separated)"
    )
    
    parser.add_argument(
        "--exclude",
        help="Exclude secrets matching these prefixes (comma-separated)"
    )
    
    # IAM and access control
    parser.add_argument(
        "--service-accounts",
        help="Comma-separated list of service accounts to grant access"
    )
    
    parser.add_argument(
        "--labels",
        help="Labels to apply to secrets in format key1=value1,key2=value2"
    )
    
    parser.add_argument(
        "--time-condition",
        action="store_true",
        help="Apply time-based conditions to restrict access to business hours"
    )
    
    # Output options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes"
    )
    
    parser.add_argument(
        "--output-csv",
        help="Output a CSV report of the migration"
    )
    
    return parser.parse_args()


def init_github_client(token: Optional[str] = None) -> Github:
    """Initialize GitHub client with auth token."""
    # Get token from args, env var, or prompt
    github_token = token or os.environ.get("GITHUB_TOKEN")
    
    if not github_token:
        github_token = input("Enter GitHub Personal Access Token: ").strip()
        
    if not github_token:
        logger.error("GitHub token not provided")
        sys.exit(1)
    
    try:
        # Create an auth object
        auth = Auth.Token(github_token)
        # Create a Github instance
        return Github(auth=auth)
    except Exception as e:
        logger.error(f"Failed to initialize GitHub client: {e}")
        sys.exit(1)


def init_gcp_client(project_id: str) -> secretmanager.SecretManagerServiceClient:
    """Initialize GCP Secret Manager client."""
    try:
        return secretmanager.SecretManagerServiceClient()
    except Exception as e:
        logger.error(f"Failed to initialize GCP Secret Manager client: {e}")
        sys.exit(1)


def get_github_secrets(
    github_client: Github, 
    repo_name: Optional[str] = None,
    org_name: Optional[str] = None,
    include_prefixes: Optional[List[str]] = None,
    exclude_prefixes: Optional[List[str]] = None
) -> Dict[str, Dict]:
    """
    Get secrets from GitHub repository or organization.
    
    Returns a dictionary of secret metadata (without values).
    """
    secrets = {}
    
    try:
        # Repository secrets
        if repo_name:
            logger.info(f"Fetching secrets from repository: {repo_name}")
            repo = github_client.get_repo(repo_name)
            repo_secrets = repo.get_secrets()
            
            for secret in repo_secrets:
                # Skip if secret should be excluded
                if exclude_prefixes and any(secret.name.startswith(p) for p in exclude_prefixes):
                    logger.debug(f"Skipping excluded secret: {secret.name}")
                    continue
                    
                # Skip if not in include list (when specified)
                if include_prefixes and not any(secret.name.startswith(p) for p in include_prefixes):
                    logger.debug(f"Skipping non-included secret: {secret.name}")
                    continue
                
                secrets[secret.name] = {
                    "name": secret.name,
                    "created_at": secret.created_at,
                    "updated_at": secret.updated_at,
                    "source": f"repository/{repo_name}",
                }
        
        # Organization secrets
        if org_name:
            logger.info(f"Fetching secrets from organization: {org_name}")
            org = github_client.get_organization(org_name)
            org_secrets = org.get_secrets()
            
            for secret in org_secrets:
                # Skip if secret should be excluded
                if exclude_prefixes and any(secret.name.startswith(p) for p in exclude_prefixes):
                    logger.debug(f"Skipping excluded secret: {secret.name}")
                    continue
                    
                # Skip if not in include list (when specified)
                if include_prefixes and not any(secret.name.startswith(p) for p in include_prefixes):
                    logger.debug(f"Skipping non-included secret: {secret.name}")
                    continue
                
                secrets[secret.name] = {
                    "name": secret.name,
                    "created_at": secret.created_at,
                    "updated_at": secret.updated_at,
                    "source": f"organization/{org_name}",
                    "visibility": getattr(secret, "visibility", "private"),
                }
        
        logger.info(f"Found {len(secrets)} GitHub secrets")
        return secrets
        
    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fetching GitHub secrets: {e}")
        sys.exit(1)


def get_secret_value_from_github(
    github_client: Github,
    secret_name: str,
    repo_name: Optional[str] = None,
    org_name: Optional[str] = None,
) -> Optional[str]:
    """
    Prompt user for the secret value since GitHub API doesn't allow direct retrieval.
    
    Note: GitHub API doesn't allow retrieving secret values, so we need to prompt
    the user to enter them manually. In a real-world scenario, you'd want to have
    these secrets backed up somewhere else or retrieve them from a secure source.
    """
    source = f"repository {repo_name}" if repo_name else f"organization {org_name}"
    print(f"\nSecret: {secret_name} (from {source})")
    print("GitHub API doesn't allow retrieving secret values.")
    print("You'll need to enter it manually.")
    
    # Prompt for secret value
    value = input(f"Enter value for secret '{secret_name}' (press Enter to skip): ")
    return value if value.strip() else None


def create_gcp_secret(
    client: secretmanager.SecretManagerServiceClient,
    project_id: str,
    secret_id: str,
    secret_value: str,
    labels: Dict[str, str] = None,
    service_accounts: List[str] = None,
    time_condition: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Create a secret in GCP Secret Manager with appropriate IAM bindings.
    
    Returns information about the created secret.
    """
    result = {
        "name": secret_id,
        "created": False,
        "error": None,
        "version_created": False,
        "iam_bindings": [],
    }
    
    if dry_run:
        logger.info(f"[DRY RUN] Would create secret: {secret_id}")
        result["created"] = True
        result["version_created"] = True
        return result
        
    # Construct the parent resource
    parent = f"projects/{project_id}"
    
    try:
        # Check if secret already exists
        secret_path = f"{parent}/secrets/{secret_id}"
        try:
            client.get_secret(request={"name": secret_path})
            logger.info(f"Secret {secret_id} already exists, updating it")
            result["created"] = True
            result["already_existed"] = True
        except gcp_exceptions.NotFound:
            # Create the secret resource
            logger.info(f"Creating new secret: {secret_id}")
            
            # Clean up labels (GCP has strict requirements for labels)
            clean_labels = {}
            if labels:
                for k, v in labels.items():
                    # Make sure keys and values follow GCP label requirements
                    k = k.lower().replace("_", "-")[:63]
                    v = v.lower().replace("_", "-")[:63]
                    clean_labels[k] = v
            
            # Add default labels
            clean_labels.update({
                "migrated-from": "github",
                "migration-date": datetime.now().strftime("%Y-%m-%d"),
            })
            
            secret = client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                        "labels": clean_labels,
                    },
                }
            )
            result["created"] = True
            logger.info(f"Created secret: {secret.name}")
    
        # Add the secret version
        version = client.add_secret_version(
            request={
                "parent": f"{parent}/secrets/{secret_id}",
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        result["version_created"] = True
        logger.info(f"Added version: {version.name}")
        
        # Add IAM bindings for service accounts if specified
        if service_accounts:
            for sa in service_accounts:
                # Clean up the service account email
                if not sa.startswith("serviceAccount:"):
                    sa_member = f"serviceAccount:{sa}"
                else:
                    sa_member = sa
                
                # Add IAM binding
                policy = client.get_iam_policy(request={"resource": secret_path})
                
                # Create a new binding with time condition if requested
                binding = {
                    "role": "roles/secretmanager.secretAccessor",
                    "members": [sa_member],
                }
                
                # Add time-based condition if requested
                if time_condition:
                    binding["condition"] = {
                        "title": "business_hours_only",
                        "description": "Only allow access during business hours (9 AM - 5 PM UTC on weekdays)",
                        "expression": """
                            request.time.getHours() >= 9 &&
                            request.time.getHours() < 17 &&
                            request.time.getDayOfWeek() >= 1 &&
                            request.time.getDayOfWeek() <= 5
                        """,
                    }
                
                # Add the binding to the policy
                policy.bindings.append(binding)
                
                # Update the policy
                updated_policy = client.set_iam_policy(
                    request={"resource": secret_path, "policy": policy}
                )
                
                result["iam_bindings"].append({
                    "service_account": sa,
                    "role": "roles/secretmanager.secretAccessor",
                    "time_condition": time_condition,
                })
                
                logger.info(f"Added IAM binding for {sa_member} to {secret_id}")
                
        return result
        
    except Exception as e:
        logger.error(f"Error creating GCP secret {secret_id}: {e}")
        result["error"] = str(e)
        return result


def migrate_secrets(
    github_client: Github,
    gcp_client: secretmanager.SecretManagerServiceClient,
    project_id: str,
    secrets: Dict[str, Dict],
    repo_name: Optional[str] = None,
    org_name: Optional[str] = None,
    service_accounts: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None,
    time_condition: bool = False,
    dry_run: bool = False,
) -> List[Dict]:
    """
    Migrate secrets from GitHub to GCP Secret Manager.
    
    Returns a list of migration results for reporting.
    """
    results = []
    total_secrets = len(secrets)
    
    logger.info(f"Starting migration of {total_secrets} secrets to GCP Secret Manager")
    
    for i, (secret_name, metadata) in enumerate(secrets.items(), 1):
        logger.info(f"Processing secret {i}/{total_secrets}: {secret_name}")
        
        # Get the secret value from GitHub (via user input)
        secret_value = get_secret_value_from_github(
            github_client, secret_name, repo_name, org_name
        )
        
        if secret_value is None:
            logger.warning(f"Skipping secret {secret_name} (no value provided)")
            results.append({
                "name": secret_name,
                "source": metadata.get("source", ""),
                "status": "skipped",
                "reason": "No value provided",
            })
            continue
        
        # Format the secret ID in GCP (ensure it meets requirements)
        # Secret IDs in GCP must consist of letters, numbers, dashes, and underscores
        gcp_secret_id = secret_name.replace("/", "_").replace(".", "_")
        
        # Create the secret in GCP
        result = create_gcp_secret(
            client=gcp_client,
            project_id=project_id,
            secret_id=gcp_secret_id,
            secret_value=secret_value,
            labels=labels,
            service_accounts=service_accounts,
            time_condition=time_condition,
            dry_run=dry_run,
        )
        
        # Track the result
        status = "created"
        if result.get("error"):
            status = "error"
        elif result.get("already_existed"):
            status = "updated"
            
        results.append({
            "name": secret_name,
            "gcp_name": gcp_secret_id,
            "source": metadata.get("source", ""),
            "status": status,
            "error": result.get("error"),
            "iam_bindings": result.get("iam_bindings", []),
        })
        
        # Slight pause to avoid API rate limits
        if i < total_secrets:
            time.sleep(0.5)
    
    logger.info(f"Migration completed - {len(results)} secrets processed")
    
    # Print results summary
    success_count = len([r for r in results if r["status"] in ("created", "updated")])
    skipped_count = len([r for r in results if r["status"] == "skipped"])
    error_count = len([r for r in results if r["status"] == "error"])
    
    print("\nMigration Summary:")
    print(f"  - {success_count} secrets successfully migrated")
    print(f"  - {skipped_count} secrets skipped")
    print(f"  - {error_count} secrets had errors")
    
    return results


def save_report(results: List[Dict], filename: str) -> None:
    """Save migration report to a CSV file."""
    if not filename:
        return
        
    try:
        with open(filename, "w", newline="") as csvfile:
            fieldnames = [
                "name", "gcp_name", "source", "status", "error"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                # Filter to only include the fields we want
                row = {
                    field: result.get(field, "")
                    for field in fieldnames
                }
                writer.writerow(row)
                
        logger.info(f"Migration report saved to {filename}")
        
    except Exception as e:
        logger.error(f"Error saving report to {filename}: {e}")


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    if not args.repo and not args.org:
        logger.error("Either --repo or --org must be specified")
        sys.exit(1)
        
    # Initialize clients
    github_client = init_github_client(args.github_token)
    gcp_client = init_gcp_client(args.project_id)
    
    # Parse include/exclude prefixes
    include_prefixes = args.include.split(",") if args.include else None
    exclude_prefixes = args.exclude.split(",") if args.exclude else None
    
    # Parse service accounts
    service_accounts = args.service_accounts.split(",") if args.service_accounts else None
    
    # Parse labels
    labels = {}
    if args.labels:
        try:
            for item in args.labels.split(","):
                key, value = item.split("=")
                labels[key.strip()] = value.strip()
        except ValueError:
            logger.warning("Labels format incorrect, using default labels only")
    
    # Get GitHub secrets
    secrets = get_github_secrets(
        github_client,
        repo_name=args.repo,
        org_name=args.org,
        include_prefixes=include_prefixes,
        exclude_prefixes=exclude_prefixes,
    )
    
    if not secrets:
        logger.info("No secrets found to migrate")
        return
        
    # Migrate secrets to GCP
    results = migrate_secrets(
        github_client=github_client,
        gcp_client=gcp_client,
        project_id=args.project_id,
        secrets=secrets,
        repo_name=args.repo,
        org_name=args.org,
        service_accounts=service_accounts,
        labels=labels,
        time_condition=args.time_condition,
        dry_run=args.dry_run,
    )
    
    # Save report if requested
    if args.output_csv:
        save_report(results, args.output_csv)


if __name__ == "__main__":
    main()
