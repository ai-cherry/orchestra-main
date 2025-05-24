"""
GitHub to GCP Secret Manager migration utility.

This module provides functionality to migrate secrets from GitHub Actions
to Google Cloud Secret Manager with comprehensive error handling, validation,
and reporting capabilities.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

from .client import SecretClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("github_migration")


class GitHubSecretMigrator:
    """
    Utility for migrating secrets from GitHub Actions to GCP Secret Manager.

    Features:
    - Fetches GitHub organization/repository secrets
    - Maps GitHub secrets to GCP Secret Manager format
    - Creates or updates secrets in GCP Secret Manager
    - Validates successful migration
    - Generates migration report
    """

    # Default mapping of GitHub secret names to GCP Secret Manager format
    DEFAULT_MAPPING = {
        "ORG_GCP_CREDENTIALS": "gcp-service-account-key",
        "ORG_GCP_PROJECT_ID": "gcp-project-id",
        "ORG_GCP_PROJECT_NUMBER": "gcp-project-number",
        "ORG_VERTEX_KEY": "vertex-api-key",
        "ORG_GCP_SERVICE_ACCOUNT_KEY": "gcp-service-account-key",
        "ORG_GCP_REGION": "gcp-region",
        "ORG_GKE_CLUSTER_PROD": "gke-cluster-prod",
        "ORG_GKE_CLUSTER_STAGING": "gke-cluster-staging",
        "ORG_PORTKEY_API_KEY": "portkey-api-key",
        "ORG_TERRAFORM_API_KEY": "terraform-api-key",
        "ORG_TERRAFORM_ORGANIZATION_TOKEN": "terraform-organization-token",
        "ORG_REDIS_HOST": "redis-host",
        "ORG_REDIS_PORT": "redis-port",
        "ORG_REDIS_USER": "redis-user",
        "ORG_REDIS_PASSWORD": "redis-password",
        "ORG_ANTHROPIC_API_KEY": "anthropic-api-key",
        "ORG_OPENAI_API_KEY": "openai-api-key",
        "ORG_FIGMA_PAT": "figma-pat",
        "ORG_GITHUB_PAT": "github-pat",
    }

    def __init__(
        self,
        github_token: str,
        gcp_project_id: str,
        environment: str = "prod",
        custom_mapping: Optional[Dict[str, str]] = None,
        github_org: Optional[str] = None,
        github_repo: Optional[str] = None,
        secret_client: Optional[SecretClient] = None,
    ):
        """
        Initialize the GitHub to GCP Secret Manager migrator.

        Args:
            github_token: GitHub Personal Access Token with appropriate permissions
            gcp_project_id: GCP Project ID for Secret Manager
            environment: Environment suffix for secrets (e.g., 'dev', 'prod')
            custom_mapping: Custom mapping of GitHub secret names to GCP secret names
            github_org: GitHub organization name (required for org-level secrets)
            github_repo: GitHub repository name (required for repo-level secrets)
            secret_client: Optional existing SecretClient instance

        Note: Either github_org or github_repo must be provided
        """
        self.github_token = github_token
        self.gcp_project_id = gcp_project_id
        self.environment = environment
        self.github_org = github_org
        self.github_repo = github_repo

        if not github_org and not github_repo:
            raise ValueError("Either github_org or github_repo must be provided")

        # Set up Secret Manager client
        self.secret_client = secret_client or SecretClient(
            project_id=gcp_project_id,
            cache_ttl=0,  # Disable caching for migration
        )

        # Combine default mapping with custom mapping
        self.mapping = self.DEFAULT_MAPPING.copy()
        if custom_mapping:
            self.mapping.update(custom_mapping)

        # Track migration results
        self.results = {
            "total": 0,
            "migrated": 0,
            "skipped": 0,
            "failed": 0,
            "secrets": [],
        }

    def _check_github_cli(self) -> bool:
        """
        Check if GitHub CLI (gh) is installed and authenticated.

        Returns:
            bool: True if GitHub CLI is available and authenticated, False otherwise
        """
        try:
            # Check if gh is installed
            result = subprocess.run(
                ["gh", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                logger.error("GitHub CLI (gh) is not installed. Please install it first.")
                return False

            # Check authentication status
            result = subprocess.run(
                ["gh", "auth", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0 or "Logged in to" not in result.stdout:
                logger.error("Not authenticated with GitHub CLI. Please run 'gh auth login' first.")
                return False

            logger.info("GitHub CLI is installed and authenticated.")
            return True

        except FileNotFoundError:
            logger.error("GitHub CLI (gh) not found. Please install it first.")
            return False

    def _authenticate_with_token(self) -> bool:
        """
        Authenticate GitHub CLI with the provided token.

        Returns:
            bool: True if authentication succeeded, False otherwise
        """
        try:
            # Authenticate using the provided token
            process = subprocess.Popen(
                ["gh", "auth", "login", "--with-token"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate(input=self.github_token)

            if process.returncode != 0:
                logger.error(f"Failed to authenticate with GitHub token: {stderr}")
                return False

            logger.info("Successfully authenticated with GitHub token.")
            return True

        except Exception as e:
            logger.error(f"Error during GitHub authentication: {str(e)}")
            return False

    def _list_github_secrets(self) -> List[str]:
        """
        List all available GitHub secrets (organization or repository level).

        Returns:
            List[str]: List of secret names
        """
        try:
            if self.github_org:
                # List organization secrets
                cmd = ["gh", "api", f"orgs/{self.github_org}/actions/secrets"]
                target = f"organization '{self.github_org}'"
            else:
                # List repository secrets
                cmd = ["gh", "api", f"repos/{self.github_repo}/actions/secrets"]
                target = f"repository '{self.github_repo}'"

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to list secrets for {target}: {result.stderr}")
                return []

            # Parse JSON response
            secrets_data = json.loads(result.stdout)
            secret_names = [secret["name"] for secret in secrets_data.get("secrets", [])]

            logger.info(f"Found {len(secret_names)} secrets in {target}")
            return secret_names

        except Exception as e:
            logger.error(f"Error listing GitHub secrets: {str(e)}")
            return []

    def _get_github_secret_value(self, secret_name: str) -> Optional[str]:
        """
        Try to get the value of a GitHub secret.

        Note: GitHub does not allow direct retrieval of secret values through its API
        for security reasons. This method attempts to use environment variables or
        the GitHub CLI, but will likely not work for most secrets.

        Args:
            secret_name: Name of the GitHub secret

        Returns:
            Optional[str]: Secret value if available, None otherwise
        """
        # Option 1: Check if the secret is available in environment variables
        env_value = os.environ.get(secret_name)
        if env_value:
            logger.info(f"Found value for '{secret_name}' in environment variables")
            return env_value

        # Option 2: Inform user that direct access is not possible
        logger.warning(
            f"GitHub does not allow direct retrieval of secret values for '{secret_name}'.\n"
            f"You'll need to manually provide the value when prompted."
        )
        return None

    def _prompt_for_secret_value(self, secret_name: str, gcp_secret_name: str) -> Optional[str]:
        """
        Prompt the user to enter a secret value manually.

        Args:
            secret_name: Original GitHub secret name
            gcp_secret_name: Target GCP secret name

        Returns:
            Optional[str]: User-provided secret value or None if skipped
        """
        print(f"\nGitHub secret '{secret_name}' will be migrated to '{gcp_secret_name}-{self.environment}'")
        print("Enter the secret value (input will not be displayed) or press Enter to skip:")
        try:
            import getpass

            value = getpass.getpass("> ")
            if not value.strip():
                logger.info(f"Skipping empty value for '{secret_name}'")
                return None
            return value
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return None
        except Exception as e:
            logger.error(f"Error during input: {str(e)}")
            return None

    def _create_or_update_gcp_secret(
        self,
        secret_name: str,
        secret_value: str,
        description: str = "Migrated from GitHub Actions",
    ) -> bool:
        """
        Create or update a secret in GCP Secret Manager.

        Args:
            secret_name: Name of the secret without environment suffix
            secret_value: Value of the secret
            description: Description of the secret

        Returns:
            bool: True if successful, False otherwise
        """
        # Format the full secret ID with environment
        full_secret_id = f"{secret_name}-{self.environment}"

        try:
            # Check if secret exists
            parent = f"projects/{self.gcp_project_id}"
            secret_path = f"{parent}/secrets/{full_secret_id}"

            secret_exists = True
            try:
                self.secret_client.client.get_secret(name=secret_path)
                logger.info(f"Secret '{full_secret_id}' already exists, adding new version")
            except Exception:
                secret_exists = False
                logger.info(f"Creating new secret '{full_secret_id}'")

            # Create secret if it doesn't exist
            if not secret_exists:
                self.secret_client.client.create_secret(
                    parent=parent,
                    secret_id=full_secret_id,
                    secret={"replication": {"automatic": {}}},
                )

            # Add the secret version
            secret_data = secret_value.encode("UTF-8")
            response = self.secret_client.client.add_secret_version(parent=secret_path, payload={"data": secret_data})

            logger.info(f"Successfully stored '{full_secret_id}' (version: {response.name})")
            return True

        except Exception as e:
            logger.error(f"Failed to store secret '{full_secret_id}': {str(e)}")
            return False

    def _validate_secret_migration(self, gcp_secret_name: str) -> bool:
        """
        Validate that a secret was successfully migrated by attempting to access it.

        Args:
            gcp_secret_name: Name of the GCP secret without environment suffix

        Returns:
            bool: True if validation succeeds, False otherwise
        """
        full_secret_id = f"{gcp_secret_name}-{self.environment}"

        try:
            # Try to access the secret
            secret_path = f"projects/{self.gcp_project_id}/secrets/{full_secret_id}/versions/latest"
            self.secret_client.client.access_secret_version(name=secret_path)

            # If we get here, the secret exists and is accessible
            logger.info(f"Validated access to secret '{full_secret_id}'")
            return True

        except Exception as e:
            logger.error(f"Failed to validate secret '{full_secret_id}': {str(e)}")
            return False

    def migrate_secrets(self, interactive: bool = True, dry_run: bool = False) -> Dict[str, Any]:
        """
        Perform the migration from GitHub Actions secrets to GCP Secret Manager.

        Args:
            interactive: Whether to prompt for secret values or skip unmapped/unavailable secrets
            dry_run: If True, only simulate the migration without making changes

        Returns:
            Dict: Migration results summary
        """
        # Check GitHub CLI availability and authentication
        if not self._check_github_cli():
            if not self._authenticate_with_token():
                logger.error("Failed to authenticate with GitHub. Migration aborted.")
                return self.results

        # Get list of GitHub secrets
        secret_names = self._list_github_secrets()
        if not secret_names:
            logger.error("No GitHub secrets found or unable to access them. Migration aborted.")
            return self.results

        self.results["total"] = len(secret_names)
        logger.info(f"Starting migration of {len(secret_names)} secrets to GCP Secret Manager")

        # Process each secret
        for secret_name in secret_names:
            # Check if we have a mapping for this secret
            gcp_secret_name = self.mapping.get(secret_name)

            if not gcp_secret_name:
                logger.warning(f"No mapping defined for GitHub secret '{secret_name}', skipping")
                self.results["skipped"] += 1
                self.results["secrets"].append({"name": secret_name, "status": "skipped", "reason": "no_mapping"})
                continue

            # Try to get secret value or prompt user
            secret_value = self._get_github_secret_value(secret_name)

            if secret_value is None and interactive:
                secret_value = self._prompt_for_secret_value(secret_name, gcp_secret_name)

            if not secret_value:
                logger.warning(f"No value available for '{secret_name}', skipping")
                self.results["skipped"] += 1
                self.results["secrets"].append({"name": secret_name, "status": "skipped", "reason": "no_value"})
                continue

            # Create or update the secret in GCP Secret Manager
            if dry_run:
                logger.info(f"[DRY RUN] Would migrate '{secret_name}' to '{gcp_secret_name}-{self.environment}'")
                self.results["migrated"] += 1
                self.results["secrets"].append(
                    {
                        "name": secret_name,
                        "gcp_name": f"{gcp_secret_name}-{self.environment}",
                        "status": "simulated",
                    }
                )
                continue

            if self._create_or_update_gcp_secret(gcp_secret_name, secret_value):
                # Validate the migration
                if self._validate_secret_migration(gcp_secret_name):
                    self.results["migrated"] += 1
                    self.results["secrets"].append(
                        {
                            "name": secret_name,
                            "gcp_name": f"{gcp_secret_name}-{self.environment}",
                            "status": "success",
                        }
                    )
                else:
                    self.results["failed"] += 1
                    self.results["secrets"].append(
                        {
                            "name": secret_name,
                            "gcp_name": f"{gcp_secret_name}-{self.environment}",
                            "status": "validation_failed",
                        }
                    )
            else:
                self.results["failed"] += 1
                self.results["secrets"].append(
                    {
                        "name": secret_name,
                        "gcp_name": f"{gcp_secret_name}-{self.environment}",
                        "status": "failed",
                    }
                )

        return self.results

    def generate_report(self, include_secrets: bool = False) -> str:
        """
        Generate a report of the migration results.

        Args:
            include_secrets: Whether to include secret names in the report

        Returns:
            str: Formatted report
        """
        report = []
        report.append("\n=== GitHub to GCP Secret Manager Migration Report ===\n")
        report.append(f"Environment: {self.environment}")

        if self.github_org:
            report.append(f"GitHub Organization: {self.github_org}")
        else:
            report.append(f"GitHub Repository: {self.github_repo}")

        report.append(f"GCP Project: {self.gcp_project_id}")
        report.append(f"\nTotal secrets: {self.results['total']}")
        report.append(f"Successfully migrated: {self.results['migrated']}")
        report.append(f"Skipped: {self.results['skipped']}")
        report.append(f"Failed: {self.results['failed']}")

        if include_secrets and self.results["secrets"]:
            report.append("\nSecret details:")
            for secret in self.results["secrets"]:
                if secret["status"] == "success":
                    report.append(f"✅ {secret['name']} -> {secret['gcp_name']}")
                elif secret["status"] == "simulated":
                    report.append(f"🔄 {secret['name']} -> {secret['gcp_name']} (dry run)")
                elif secret["status"] == "skipped":
                    reason = secret.get("reason", "unknown")
                    report.append(f"⏭️ {secret['name']} (reason: {reason})")
                else:
                    report.append(f"❌ {secret['name']} -> {secret.get('gcp_name', 'N/A')}")

        report.append("\nNext steps:")
        report.append("1. Update your CI/CD workflows to use GCP Secret Manager")
        report.append("2. Consider removing the GitHub secrets once migration is complete")
        report.append("3. Ensure proper IAM permissions are set for accessing secrets")

        return "\n".join(report)


def main():
    """Command-line interface for the GitHub to GCP Secret Manager migration tool."""
    parser = argparse.ArgumentParser(description="Migrate secrets from GitHub Actions to GCP Secret Manager")

    parser.add_argument("--github-token", help="GitHub Personal Access Token")

    parser.add_argument("--gcp-project-id", required=True, help="GCP Project ID for Secret Manager")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--github-org", help="GitHub organization name (for org-level secrets)")
    group.add_argument("--github-repo", help="GitHub repository name (for repo-level secrets)")

    parser.add_argument(
        "--environment",
        default="prod",
        help="Environment suffix for secrets (e.g., 'dev', 'prod')",
    )

    parser.add_argument(
        "--mapping-file",
        help="Path to JSON file with custom mapping of GitHub secret names to GCP secret names",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Prompt for secret values when not available",
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip secrets when values are not available (don't prompt)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the migration without making changes",
    )

    parser.add_argument("--output", help="Output report to file")

    args = parser.parse_args()

    # Get GitHub token from environment if not provided
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        parser.error("GitHub token must be provided via --github-token or GITHUB_TOKEN environment variable")

    # Load custom mapping if provided
    custom_mapping = None
    if args.mapping_file:
        try:
            with open(args.mapping_file, "r") as f:
                custom_mapping = json.load(f)
        except Exception as e:
            parser.error(f"Failed to load mapping file: {str(e)}")

    # Initialize the migrator
    migrator = GitHubSecretMigrator(
        github_token=github_token,
        gcp_project_id=args.gcp_project_id,
        environment=args.environment,
        custom_mapping=custom_mapping,
        github_org=args.github_org,
        github_repo=args.github_repo,
    )

    # Run the migration
    migrator.migrate_secrets(interactive=not args.non_interactive, dry_run=args.dry_run)

    # Generate and output the report
    report = migrator.generate_report(include_secrets=True)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report written to {args.output}")
        except Exception as e:
            print(f"Failed to write report to file: {str(e)}")

    print(report)

    # Return success if no failures
    return 0 if migrator.results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
