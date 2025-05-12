#!/usr/bin/env python3
"""
Workload Identity Federation Setup CLI

This script provides a command-line interface for setting up
Workload Identity Federation for GCP with GitHub Actions.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config_models import GCPProjectConfig, GitHubConfig, RepositoryConfig, WIFImplementationConfig
from .enhanced_template_manager import EnhancedTemplateManager, create_template_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("wif_cli")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Set up Workload Identity Federation for GCP with GitHub Actions",
    )
    
    # GCP arguments
    parser.add_argument(
        "--project-id",
        required=True,
        help="GCP project ID",
    )
    parser.add_argument(
        "--project-number",
        help="GCP project number (if not provided, will be fetched using gcloud)",
    )
    parser.add_argument(
        "--region",
        default="us-central1",
        help="GCP region (default: us-central1)",
    )
    
    # GitHub arguments
    parser.add_argument(
        "--github-repo",
        help="GitHub repository in the format 'owner/name'",
    )
    parser.add_argument(
        "--github-token",
        help="GitHub token for API access",
    )
    
    # WIF arguments
    parser.add_argument(
        "--pool-id",
        default="github-pool",
        help="Workload Identity Pool ID (default: github-pool)",
    )
    parser.add_argument(
        "--provider-id",
        default="github-provider",
        help="Workload Identity Provider ID (default: github-provider)",
    )
    parser.add_argument(
        "--service-account-id",
        default="github-actions-sa",
        help="Service Account ID (default: github-actions-sa)",
    )
    
    # Output arguments
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("wif_output"),
        help="Output directory for generated files",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        help="Directory containing templates (default: built-in templates)",
    )
    
    # Other arguments
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no changes will be made)",
    )
    
    return parser.parse_args()


def get_project_number(project_id: str) -> Optional[str]:
    """
    Get the GCP project number using gcloud.
    
    Args:
        project_id: The GCP project ID
        
    Returns:
        The GCP project number or None if it could not be retrieved
    """
    import subprocess
    
    try:
        result = subprocess.run(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get project number: {e}")
        return None


def setup_github_secrets(
    config: WIFImplementationConfig,
    github_token: Optional[str] = None,
) -> bool:
    """
    Set up GitHub repository secrets using the GitHub CLI.
    
    Args:
        config: The WIF implementation configuration
        github_token: GitHub token for API access
        
    Returns:
        True if successful, False otherwise
    """
    import subprocess
    import os
    
    if not config.github.repositories:
        logger.error("No GitHub repositories configured")
        return False
    
    # Check if GitHub CLI is installed
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("GitHub CLI (gh) not found. Please install it and try again.")
        return False
    
    # Set GitHub token if provided
    env = os.environ.copy()
    if github_token:
        env["GITHUB_TOKEN"] = github_token
    
    success = True
    
    for repo in config.github.repositories:
        logger.info(f"Setting up GitHub secrets for repository: {repo.full_name}")
        
        # Get the WIF provider resource name
        provider_resource_name = config.workload_identity.get_provider_resource_name(config.gcp)
        service_account_email = config.workload_identity.get_service_account_email(config.gcp)
        
        # Set the secrets
        secrets = {
            "GCP_PROJECT_ID": config.gcp.project_id,
            "GCP_PROJECT_NUMBER": config.gcp.project_number or "",
            "GCP_REGION": config.gcp.region,
            "GCP_WORKLOAD_IDENTITY_PROVIDER": provider_resource_name,
            "GCP_SERVICE_ACCOUNT": service_account_email,
        }
        
        for name, value in secrets.items():
            try:
                logger.debug(f"Setting secret {name} for repository {repo.full_name}")
                subprocess.run(
                    ["gh", "secret", "set", name, "--repo", repo.full_name],
                    input=value,
                    text=True,
                    env=env,
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to set secret {name} for repository {repo.full_name}: {e}")
                success = False
    
    return success


def setup_terraform_files(
    template_manager: EnhancedTemplateManager,
    config: WIFImplementationConfig,
) -> List[Path]:
    """
    Generate Terraform files for WIF setup.
    
    Args:
        template_manager: The template manager
        config: The WIF implementation configuration
        
    Returns:
        List of paths to the generated files
    """
    logger.info("Generating Terraform files")
    
    repo_condition = config.github.repository_conditions()
    
    context = {
        "config": config,
        "github_condition": repo_condition,
        "repo_condition": repo_condition,
    }
    
    try:
        # Create the template if it doesn't exist
        if "terraform_wif.tf.j2" not in template_manager.list_templates():
            template_manager.create_default_templates()
        
        # Render the template
        output_path = config.output_dir / "terraform" / "wif.tf"
        file_path = template_manager.write_template_to_file(
            "terraform_wif.tf.j2",
            output_path,
            context,
            overwrite=True,
        )
        
        logger.info(f"Terraform file generated: {file_path}")
        return [file_path]
        
    except Exception as e:
        logger.error(f"Failed to generate Terraform files: {e}")
        return []


def setup_github_workflow(
    template_manager: EnhancedTemplateManager,
    config: WIFImplementationConfig,
) -> List[Path]:
    """
    Generate GitHub Actions workflow for WIF authentication.
    
    Args:
        template_manager: The template manager
        config: The WIF implementation configuration
        
    Returns:
        List of paths to the generated files
    """
    logger.info("Generating GitHub Actions workflow")
    
    context = {
        "workflow_name": "Deploy AI Orchestra with WIF",
        "branches": "main",
        "service_name": "ai-orchestra-api",
    }
    
    try:
        # Create the template if it doesn't exist
        if "github_workflow.yml.j2" not in template_manager.list_templates():
            template_manager.create_default_templates()
        
        # Render the template
        output_path = config.output_dir / "github" / "wif-deploy.yml"
        file_path = template_manager.write_template_to_file(
            "github_workflow.yml.j2",
            output_path,
            context,
            overwrite=True,
        )
        
        logger.info(f"GitHub Actions workflow generated: {file_path}")
        return [file_path]
        
    except Exception as e:
        logger.error(f"Failed to generate GitHub Actions workflow: {e}")
        return []


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
    
    if args.dry_run:
        logger.info("Dry run mode enabled")
    
    # Get project number if not provided
    project_number = args.project_number
    if not project_number:
        logger.info("Project number not provided, fetching from gcloud")
        project_number = get_project_number(args.project_id)
        if not project_number:
            logger.error("Failed to get project number. Please provide it manually with --project-number")
            return 1
    
    # Parse GitHub repository
    github_repositories = []
    if args.github_repo:
        try:
            owner, name = args.github_repo.split("/")
            github_repositories.append(RepositoryConfig(owner=owner, name=name))
        except ValueError:
            logger.error(f"Invalid GitHub repository format: {args.github_repo}. Use 'owner/name' format.")
            return 1
    
    # Create configuration
    config = WIFImplementationConfig(
        gcp=GCPProjectConfig(
            project_id=args.project_id,
            project_number=project_number,
            region=args.region,
        ),
        workload_identity=WorkloadIdentityConfig(
            pool_id=args.pool_id,
            provider_id=args.provider_id,
            service_account_id=args.service_account_id,
        ),
        github=GitHubConfig(
            repositories=github_repositories,
            token=args.github_token,
        ),
        template_dir=args.template_dir,
        output_dir=args.output_dir,
        debug=args.verbose,
    )
    
    # Create template manager
    template_manager = create_template_manager(config)
    
    # Generate Terraform files
    terraform_files = setup_terraform_files(template_manager, config)
    
    # Generate GitHub Actions workflow
    github_workflow_files = setup_github_workflow(template_manager, config)
    
    # Set up GitHub secrets
    if github_repositories and not args.dry_run:
        logger.info("Setting up GitHub secrets")
        if setup_github_secrets(config, args.github_token):
            logger.info("GitHub secrets set up successfully")
        else:
            logger.error("Failed to set up GitHub secrets")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info(f"- GCP Project ID: {config.gcp.project_id}")
    logger.info(f"- GCP Project Number: {config.gcp.project_number}")
    logger.info(f"- GCP Region: {config.gcp.region}")
    
    logger.info(f"- Workload Identity Pool ID: {config.workload_identity.pool_id}")
    logger.info(f"- Workload Identity Provider ID: {config.workload_identity.provider_id}")
    logger.info(f"- Service Account ID: {config.workload_identity.service_account_id}")
    
    if config.github.repositories:
        logger.info(f"- GitHub Repositories: {', '.join(repo.full_name for repo in config.github.repositories)}")
    
    logger.info("\nGenerated files:")
    for file_path in terraform_files + github_workflow_files:
        logger.info(f"- {file_path}")
    
    logger.info("\nNext steps:")
    logger.info("1. Apply the Terraform configuration to create the Workload Identity Federation resources:")
    logger.info(f"   cd {config.output_dir}/terraform && terraform init && terraform apply")
    logger.info("2. Place the generated GitHub workflow in the .github/workflows directory of your repository")
    logger.info("   or commit the changes made automatically")
    logger.info("3. Push to your repository to trigger the workflow")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())