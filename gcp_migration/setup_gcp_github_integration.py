#!/usr/bin/env python3
"""
GCP-GitHub Integration Setup Tool

This script provides a comprehensive CLI for setting up and managing
the integration between Google Cloud Platform and GitHub, including:
- Authentication configuration
- Workload Identity Federation setup
- Bidirectional secret synchronization
- Deployment workflow configuration
- End-to-end verification

Usage:
  python setup_gcp_github_integration.py setup --project-id=PROJECT_ID [options]
  python setup_gcp_github_integration.py sync-secrets --direction=DIRECTION [options]
  python setup_gcp_github_integration.py verify [options]
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Local modules
from gcp_migration.secure_auth import (
    GCPAuth, GCPConfig, GitHubAuth, GitHubConfig, AuthMethod
)
from gcp_migration.secure_secret_sync import (
    SecureSyncConfig, SecretSynchronizer, SyncDirection, SyncLevel, SecretSyncAuditor
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gcp_github_integration.log")
    ]
)
logger = logging.getLogger("gcp-github-integration")


class Command(Enum):
    """Command types for the integration tool."""
    SETUP = "setup"
    SYNC_SECRETS = "sync-secrets"
    VERIFY = "verify"
    HELP = "help"


class SetupStage(Enum):
    """Stages of the setup process."""
    AUTHENTICATION = "authentication"
    WORKLOAD_IDENTITY = "workload-identity"
    SECRET_SYNC = "secret-sync"
    WORKFLOWS = "workflows"
    VERIFICATION = "verification"
    ALL = "all"


class IntegrationConfig:
    """Configuration for the integration setup."""
    
    def __init__(
        self,
        command: Command,
        stage: Optional[SetupStage] = None,
        gcp_project_id: str = "",
        gcp_region: str = "us-central1",
        github_org: str = "",
        github_repo: Optional[str] = None,
        service_account_name: str = "github-actions",
        pool_id: str = "github-actions-pool",
        provider_id: str = "github-actions-provider",
        sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        sync_level: SyncLevel = SyncLevel.ORGANIZATION,
        workload_identity_only: bool = False,
        dry_run: bool = False,
        verbose: bool = False
    ):
        """Initialize integration configuration.
        
        Args:
            command: Command to execute
            stage: Setup stage to execute
            gcp_project_id: GCP project ID
            gcp_region: GCP region
            github_org: GitHub organization
            github_repo: GitHub repository (org/repo format)
            service_account_name: Service account name for WIF
            pool_id: Workload identity pool ID
            provider_id: Workload identity provider ID
            sync_direction: Direction of secret synchronization
            sync_level: Level of GitHub secret synchronization
            workload_identity_only: Whether to only set up WIF
            dry_run: Don't actually make changes
            verbose: Enable verbose logging
        """
        self.command = command
        self.stage = stage
        self.gcp_project_id = gcp_project_id
        self.gcp_region = gcp_region
        self.github_org = github_org
        self.github_repo = github_repo
        self.service_account_name = service_account_name
        self.pool_id = pool_id
        self.provider_id = provider_id
        self.sync_direction = sync_direction
        self.sync_level = sync_level
        self.workload_identity_only = workload_identity_only
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Set log level
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Working directory for templates and configs
        self.work_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        self.template_dir = self.work_dir / "templates"
        self.workflow_dir = self.work_dir / ".github" / "workflows"


class IntegrationSetup:
    """Manages the setup and configuration of GCP-GitHub integration."""
    
    def __init__(self, config: IntegrationConfig):
        """Initialize integration setup.
        
        Args:
            config: Integration configuration
        """
        self.config = config
        
        # Credentials from environment
        self.master_service_key = os.environ.get("GCP_MASTER_SERVICE_JSON", "")
        self.secret_management_key = os.environ.get("GCP_SECRET_MANAGEMENT_KEY", "")
        self.github_classic_token = os.environ.get("GH_CLASSIC_PAT_TOKEN", "")
        self.github_fine_grained_token = os.environ.get("GH_FINE_GRAINED_TOKEN", "")
        
        # Derived values
        self.service_account_email = f"{config.service_account_name}@{config.gcp_project_id}.iam.gserviceaccount.com"
        self.full_pool_name = None
        self.full_provider_name = None
        
        # Clients
        self.gcp_auth = None
        self.github_auth = None
    
    def run(self) -> int:
        """Run the integration setup based on the configured command.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            if self.config.command == Command.SETUP:
                return self.run_setup()
            elif self.config.command == Command.SYNC_SECRETS:
                return self.run_sync_secrets()
            elif self.config.command == Command.VERIFY:
                return self.run_verification()
            elif self.config.command == Command.HELP:
                self.show_help()
                return 0
            else:
                logger.error(f"Unknown command: {self.config.command}")
                return 1
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            return 130
        except Exception as e:
            logger.error(f"Error during {self.config.command.value}: {e}", exc_info=True)
            return 1
    
    def run_setup(self) -> int:
        """Run the setup process.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        logger.info("Starting GCP-GitHub integration setup")
        
        if not self.config.stage:
            self.config.stage = SetupStage.ALL
        
        stages_to_run = []
        
        if self.config.stage == SetupStage.ALL:
            # Run all stages
            stages_to_run = [
                SetupStage.AUTHENTICATION,
                SetupStage.WORKLOAD_IDENTITY,
                SetupStage.SECRET_SYNC,
                SetupStage.WORKFLOWS,
                SetupStage.VERIFICATION
            ]
        elif self.config.workload_identity_only:
            # Only run Workload Identity Federation setup
            stages_to_run = [
                SetupStage.AUTHENTICATION,
                SetupStage.WORKLOAD_IDENTITY,
                SetupStage.VERIFICATION
            ]
        else:
            # Run the specified stage
            stages_to_run = [self.config.stage]
        
        # Execute each stage
        for stage in stages_to_run:
            logger.info(f"Executing stage: {stage.value}")
            
            if stage == SetupStage.AUTHENTICATION:
                if not self.setup_authentication():
                    return 1
            elif stage == SetupStage.WORKLOAD_IDENTITY:
                if not self.setup_workload_identity():
                    return 1
            elif stage == SetupStage.SECRET_SYNC:
                if not self.setup_secret_sync():
                    return 1
            elif stage == SetupStage.WORKFLOWS:
                if not self.setup_workflows():
                    return 1
            elif stage == SetupStage.VERIFICATION:
                if not self.verify_setup():
                    return 1
        
        logger.info("GCP-GitHub integration setup completed successfully")
        return 0
    
    def run_sync_secrets(self) -> int:
        """Run the secret synchronization process.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        logger.info("Starting GCP-GitHub secret synchronization")
        
        # Set up authentication
        if not self.setup_authentication():
            return 1
        
        # Perform secret sync
        return self.sync_secrets()
    
    def run_verification(self) -> int:
        """Run verification of the GCP-GitHub integration.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        logger.info("Starting GCP-GitHub integration verification")
        
        # Set up authentication
        if not self.setup_authentication():
            return 1
        
        # Perform verification
        return self.verify_setup()
    
    def setup_authentication(self) -> bool:
        """Set up authentication with GCP and GitHub.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Setting up authentication")
        
        # Check for required credentials
        if not self.master_service_key:
            logger.error("GCP_MASTER_SERVICE_JSON environment variable not set")
            return False
        
        if not self.github_classic_token and not self.github_fine_grained_token:
            logger.error("Neither GH_CLASSIC_PAT_TOKEN nor GH_FINE_GRAINED_TOKEN environment variable is set")
            return False
        
        # Configure GCP authentication
        gcp_config = GCPConfig(
            project_id=self.config.gcp_project_id,
            region=self.config.gcp_region
        )
        
        self.gcp_auth = GCPAuth(
            gcp_config=gcp_config,
            auth_method=AuthMethod.SERVICE_ACCOUNT_KEY,
            service_account_key=self.master_service_key
        )
        
        # Authenticate with GCP
        if not self.gcp_auth.authenticate():
            logger.error("GCP authentication failed")
            return False
        
        logger.info("GCP authentication successful")
        
        # Configure GitHub authentication
        github_token = self.github_fine_grained_token or self.github_classic_token
        use_fine_grained = bool(self.github_fine_grained_token)
        
        github_config = GitHubConfig(
            org_name=self.config.github_org,
            repo_name=self.config.github_repo,
            token=github_token,
            use_fine_grained_token=use_fine_grained
        )
        
        self.github_auth = GitHubAuth(github_config=github_config)
        
        # Authenticate with GitHub
        if not self.github_auth.authenticate():
            logger.error("GitHub authentication failed")
            return False
        
        logger.info("GitHub authentication successful")
        return True
    
    def setup_workload_identity(self) -> bool:
        """Set up Workload Identity Federation for GitHub Actions.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Setting up Workload Identity Federation")
        
        if self.config.dry_run:
            logger.info("[DRY RUN] Would set up Workload Identity Federation")
            return True
        
        try:
            # Enable required APIs
            self._enable_required_apis()
            
            # Create Workload Identity Pool
            pool_name = self._create_workload_identity_pool()
            if not pool_name:
                return False
            
            # Create Workload Identity Provider
            provider_name = self._create_workload_identity_provider()
            if not provider_name:
                return False
            
            # Create service account
            if not self._create_service_account():
                return False
            
            # Configure IAM policies
            if not self._configure_iam_policies():
                return False
            
            # Add provider details to GitHub secrets
            if not self._update_github_secrets_with_provider():
                return False
            
            logger.info("Workload Identity Federation setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up Workload Identity Federation: {e}", exc_info=True)
            return False
    
    def _enable_required_apis(self) -> bool:
        """Enable required GCP APIs.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Enabling required GCP APIs")
        
        # List of required APIs
        apis = [
            "iamcredentials.googleapis.com",
            "iam.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "secretmanager.googleapis.com",
            "artifactregistry.googleapis.com",
            "run.googleapis.com"
        ]
        
        cmd = [
            "gcloud", "services", "enable",
            *apis,
            f"--project={self.config.gcp_project_id}"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("All required APIs enabled successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to enable APIs: {e.stderr}")
            return False
    
    def _create_workload_identity_pool(self) -> Optional[str]:
        """Create Workload Identity Pool for GitHub Actions.
        
        Returns:
            Full pool name if successful, None otherwise
        """
        logger.info(f"Creating Workload Identity Pool: {self.config.pool_id}")
        
        # Check if pool already exists
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "workload-identity-pools", "describe",
                    self.config.pool_id,
                    "--location=global",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Pool already exists
                self.full_pool_name = self._extract_full_name(result.stdout)
                logger.info(f"Workload Identity Pool already exists: {self.full_pool_name}")
                return self.full_pool_name
        except Exception:
            # Pool doesn't exist or other error, proceed with creation
            pass
        
        # Create new pool
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "workload-identity-pools", "create",
                    self.config.pool_id,
                    "--location=global",
                    "--display-name=GitHub Actions Pool",
                    "--description=Identity pool for GitHub Actions workflows",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get the full pool name
            describe_result = subprocess.run(
                [
                    "gcloud", "iam", "workload-identity-pools", "describe",
                    self.config.pool_id,
                    "--location=global",
                    "--format=value(name)",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.full_pool_name = describe_result.stdout.strip()
            logger.info(f"Created Workload Identity Pool: {self.full_pool_name}")
            return self.full_pool_name
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Workload Identity Pool: {e.stderr}")
            return None
    
    def _extract_full_name(self, description: str) -> str:
        """Extract full resource name from description output.
        
        Args:
            description: Description output from gcloud
            
        Returns:
            Full resource name
        """
        for line in description.splitlines():
            if line.strip().startswith("name:"):
                return line.strip()[5:].strip()
        return ""
    
    def _create_workload_identity_provider(self) -> Optional[str]:
        """Create Workload Identity Provider for GitHub Actions.
        
        Returns:
            Full provider name if successful, None otherwise
        """
        logger.info(f"Creating Workload Identity Provider: {self.config.provider_id}")
        
        # Check if provider already exists
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "workload-identity-pools", "providers", "describe",
                    self.config.provider_id,
                    "--location=global",
                    f"--workload-identity-pool={self.config.pool_id}",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Provider already exists
                self.full_provider_name = self._extract_full_name(result.stdout)
                logger.info(f"Workload Identity Provider already exists: {self.full_provider_name}")
                return self.full_provider_name
        except Exception:
            # Provider doesn't exist or other error, proceed with creation
            pass
        
        # Create new provider
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "workload-identity-pools", "providers", "create-oidc",
                    self.config.provider_id,
                    "--location=global",
                    f"--workload-identity-pool={self.config.pool_id}",
                    "--display-name=GitHub Provider",
                    "--attribute-mapping=google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner",
                    "--issuer-uri=https://token.actions.githubusercontent.com",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get the full provider name
            describe_result = subprocess.run(
                [
                    "gcloud", "iam", "workload-identity-pools", "providers", "describe",
                    self.config.provider_id,
                    "--location=global",
                    f"--workload-identity-pool={self.config.pool_id}",
                    "--format=value(name)",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.full_provider_name = describe_result.stdout.strip()
            logger.info(f"Created Workload Identity Provider: {self.full_provider_name}")
            return self.full_provider_name
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Workload Identity Provider: {e.stderr}")
            return None
    
    def _create_service_account(self) -> bool:
        """Create service account for GitHub Actions.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating service account: {self.service_account_email}")
        
        # Check if service account already exists
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "service-accounts", "describe",
                    self.service_account_email,
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Service account already exists
                logger.info(f"Service account already exists: {self.service_account_email}")
                return True
        except Exception:
            # Service account doesn't exist or other error, proceed with creation
            pass
        
        # Create new service account
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "service-accounts", "create",
                    self.config.service_account_name,
                    f"--display-name={self.config.service_account_name} for GitHub Actions",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Created service account: {self.service_account_email}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create service account: {e.stderr}")
            return False
    
    def _configure_iam_policies(self) -> bool:
        """Configure IAM policies for service account.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Configuring IAM policies")
        
        # Roles to grant to the service account
        roles = [
            "roles/artifactregistry.writer",
            "roles/run.admin",
            "roles/secretmanager.secretAccessor",
            "roles/storage.admin"
        ]
        
        # Grant roles to the service account
        for role in roles:
            try:
                result = subprocess.run(
                    [
                        "gcloud", "projects", "add-iam-policy-binding",
                        self.config.gcp_project_id,
                        f"--member=serviceAccount:{self.service_account_email}",
                        f"--role={role}"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Granted {role} to {self.service_account_email}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to grant {role} to {self.service_account_email}: {e.stderr}")
                return False
        
        # Allow GitHub Actions to impersonate the service account
        if self.config.github_repo:
            # Repository-level binding
            principal = f"principalSet://iam.googleapis.com/{self.full_pool_name}/attribute.repository/{self.config.github_org}/{self.config.github_repo}"
        else:
            # Organization-level binding
            principal = f"principalSet://iam.googleapis.com/{self.full_pool_name}/attribute.repository_owner/{self.config.github_org}"
        
        try:
            result = subprocess.run(
                [
                    "gcloud", "iam", "service-accounts", "add-iam-policy-binding",
                    self.service_account_email,
                    "--role=roles/iam.workloadIdentityUser",
                    f"--member={principal}",
                    f"--project={self.config.gcp_project_id}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Granted workload identity user role to {principal}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to grant workload identity user role: {e.stderr}")
            return False
    
    def _update_github_secrets_with_provider(self) -> bool:
        """Update GitHub secrets with Workload Identity Provider details.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Updating GitHub secrets with Workload Identity Provider details")
        
        # Use GitHub CLI to update secrets
        secrets = {
            "GCP_PROJECT_ID": self.config.gcp_project_id,
            "GCP_REGION": self.config.gcp_region,
            "GCP_WORKLOAD_IDENTITY_PROVIDER": self.full_provider_name,
            "GCP_SERVICE_ACCOUNT": self.service_account_email
        }
        
        # Add artifact registry if available
        try:
            registry_result = subprocess.run(
                [
                    "gcloud", "artifacts", "repositories", "list",
                    "--format=value(name)",
                    f"--project={self.config.gcp_project_id}",
                    f"--location={self.config.gcp_region}"
                ],
                capture_output=True,
                text=True
            )
            
            if registry_result.returncode == 0 and registry_result.stdout.strip():
                registry_name = registry_result.stdout.splitlines()[0].strip()
                if registry_name:
                    secrets["GCP_ARTIFACT_REGISTRY"] = registry_name
                    logger.info(f"Found artifact registry: {registry_name}")
        except Exception as e:
            logger.warning(f"Failed to get artifact registries: {e}")
        
        # Set organization or repository secrets
        for name, value in secrets.items():
            try:
                if self.config.github_repo:
                    # Repository-level secrets
                    result = subprocess.run(
                        [
                            "gh", "secret", "set", name,
                            "--repo", self.config.github_repo,
                            "--body", value
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                else:
                    # Organization-level secrets
                    result = subprocess.run(
                        [
                            "gh", "secret", "set", name,
                            "--org", self.config.github_org,
                            "--visibility", "all",
                            "--body", value
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                
                logger.info(f"Updated GitHub secret: {name}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to update GitHub secret {name}: {e.stderr}")
                return False
        
        return True
    
    def setup_secret_sync(self) -> bool:
        """Set up bidirectional secret synchronization.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Setting up secret synchronization")
        
        if self.config.dry_run:
            logger.info("[DRY RUN] Would set up secret synchronization")
            return True
        
        # Perform initial secret sync
        return self.sync_secrets()
    
    def sync_secrets(self) -> bool:
        """Synchronize secrets between GitHub and GCP.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Synchronizing secrets")
        
        try:
            # Create auditor
            audit_log_path = "secret_sync_audit.log"
            auditor = SecretSyncAuditor(log_path=audit_log_path)
            
            # Create sync configuration
            sync_config = SecureSyncConfig(
                gcp_config=self.gcp_auth.gcp_config,
                github_config=self.github_auth.github_config,
                sync_direction=self.config.sync_direction,
                sync_level=self.config.sync_level,
                secret_prefix="github-",
                dry_run=self.config.dry_run,
                audit_log_path=audit_log_path,
                verbose=self.config.verbose
            )
            
            # Create synchronizer
            synchronizer = SecretSynchronizer(
                config=sync_config,
                gcp_auth=self.gcp_auth,
                github_auth=self.github_auth,
                auditor=auditor
            )
            
            # Perform synchronization
            results = synchronizer.sync(
                repo_name=self.config.github_repo
            )
            
            # Check results
            if isinstance(results, dict):
                # Bidirectional results
                github_to_gcp = results["github_to_gcp"]
                gcp_to_github = results["gcp_to_github"]
                
                logger.info("\nSync Summary:")
                logger.info("GitHub to GCP:")
                logger.info(f"  Total: {len(github_to_gcp)}")
                logger.info(f"  Success: {sum(1 for r in github_to_gcp if r.success)}")
                logger.info(f"  Failure: {sum(1 for r in github_to_gcp if not r.success)}")
                
                logger.info("\nGCP to GitHub:")
                logger.info(f"  Total: {len(gcp_to_github)}")
                logger.info(f"  Success: {sum(1 for r in gcp_to_github if r.success)}")
                logger.info(f"  Failure: {sum(1 for r in gcp_to_github if not r.success)}")
                
                # Consider success if there were no failures or if they were all placeholders
                success = all(r.success or "placeholder" in r.message.lower() 
                              for r in github_to_gcp + gcp_to_github)
            else:
                # Unidirectional results
                logger.info("\nSync Summary:")
                logger.info(f"Total: {len(results)}")
                logger.info(f"Success: {sum(1 for r in results if r.success)}")
                logger.info(f"Failure: {sum(1 for r in results if not r.success)}")
                
                # Consider success if there were no failures or if they were all placeholders
                success = all(r.success or "placeholder" in r.message.lower() for r in results)
            
            if success:
                logger.info("Secret synchronization completed successfully")
                return True
            else:
                logger.error("Secret synchronization completed with errors")
                return False
        
        except Exception as e:
            logger.error(f"Error during secret synchronization: {e}", exc_info=True)
            return False
    
    def setup_workflows(self) -> bool:
        """Set up GitHub Actions workflows for deployment.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Setting up GitHub Actions workflows")
        
        if self.config.dry_run:
            logger.info("[DRY RUN] Would set up GitHub Actions workflows")
            return True
        
        try:
            # Create workflow directories if they don't exist
            workflow_dir = Path(".github/workflows")
            os.makedirs(workflow_dir, exist_ok=True)
            
            # Copy template workflow files
            source_dir = self.config.workflow_dir
            if source_dir.exists():
                for workflow_file in source_dir.glob("*.yml"):
                    dest_file = workflow_dir / workflow_file.name
                    shutil.copy(workflow_file, dest_file)
                    logger.info(f"Copied workflow file: {workflow_file.name}")
            else:
                logger.warning(f"Workflow template directory not found: {source_dir}")
                return False
            
            logger.info("GitHub Actions workflows setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up GitHub Actions workflows: {e}", exc_info=True)
            return False
    
    def verify_setup(self) -> bool:
        """Verify the GCP-GitHub integration setup.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Verifying GCP-GitHub integration setup")
        
        try:
            success = True
            
            # Verify Workload Identity Pool exists
            if not self.full_pool_name:
                try:
                    result = subprocess.run(
                        [
                            "gcloud", "iam", "workload-identity-pools", "describe",
                            self.config.pool_id,
                            "--location=global",
                            f"--project={self.config.gcp_project_id}"
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    self.full_pool_name = self._extract_full_name(result.stdout)
                    logger.info(f"Verified Workload Identity Pool: {self.full_pool_name}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Workload Identity Pool verification failed: {e.stderr}")
                    success = False
            
            # Verify Workload Identity Provider exists
            if not self.full_provider_name:
                try:
                    result = subprocess.run(
                        [
                            "gcloud", "iam", "workload-identity-pools", "providers", "describe",
                            self.config.provider_id,
                            "--location=global",
                            f"--workload-identity-pool={self.config.pool_id}",
                            f"--project={self.config.gcp_project_id}"
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    self.full_provider_name = self._extract_full_name(result.stdout)
                    logger.info(f"Verified Workload Identity Provider: {self.full_provider_name}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Workload Identity Provider verification failed: {e.stderr}")
                    success = False
            
            # Verify service account exists
            try:
                result = subprocess.run(
                    [
                        "gcloud", "iam", "service-accounts", "describe",
                        self.service_account_email,
                        f"--project={self.config.gcp_project_id}"
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Verified service account: {self.service_account_email}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Service account verification failed: {e.stderr}")
                success = False
            
            # Verify GitHub secrets exist
            secrets_to_check = [
                "GCP_PROJECT_ID",
                "GCP_REGION",
                "GCP_WORKLOAD_IDENTITY_PROVIDER",
                "GCP_SERVICE_ACCOUNT"
            ]
            
            for secret in secrets_to_check:
                try:
                    if self.config.github_repo:
                        # Repository-level secrets
                        result = subprocess.run(
                            [
                                "gh", "secret", "list",
                                "--repo", self.config.github_repo
                            ],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                    else:
                        # Organization-level secrets
                        result = subprocess.run(
                            [
                                "gh", "secret", "list",
                                "--org", self.config.github_org
                            ],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                    
                    if secret in result.stdout:
                        logger.info(f"Verified GitHub secret exists: {secret}")
                    else:
                        logger.warning(f"GitHub secret not found: {secret}")
                        success = False
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to verify GitHub secrets: {e.stderr}")
                    success = False
            
            # Verify GitHub workflows exist
            workflow_dir = Path(".github/workflows")
            if workflow_dir.exists() and any(workflow_dir.glob("*.yml")):
                logger.info(f"Verified GitHub workflow files exist in {workflow_dir}")
            else:
                logger.warning("No GitHub workflow files found")
                success = False
            
            if success:
                logger.info("GCP-GitHub integration verification completed successfully")
            else:
                logger.error("GCP-GitHub integration verification completed with errors")
            
            return success
        except Exception as e:
            logger.error(f"Error during verification: {e}", exc_info=True)
            return False
    
    def show_help(self) -> None:
        """Show help information for the tool."""
        print("\nGCP-GitHub Integration Setup Tool\n")
        print("Commands:")
        print("  setup              Set up GCP-GitHub integration")
        print("  sync-secrets       Synchronize secrets between GitHub and GCP")
        print("  verify             Verify the GCP-GitHub integration setup")
        print("  help               Show this help message")
        print("\nSetup Stages:")
        print("  authentication     Set up authentication with GCP and GitHub")
        print("  workload-identity  Set up Workload Identity Federation")
        print("  secret-sync        Set up secret synchronization")
        print("  workflows          Set up GitHub Actions workflows")
        print("  verification       Verify the setup")
        print("  all                Run all stages (default)")
        print("\nOptions:")
        print("  --project-id       GCP project ID")
        print("  --region           GCP region (default: us-central1)")
        print("  --github-org       GitHub organization name")
        print("  --github-repo      GitHub repository name (org/repo format)")
        print("  --service-account  Service account name (default: github-actions)")
        print("  --pool-id          Workload identity pool ID (default: github-actions-pool)")
        print("  --provider-id      Workload identity provider ID (default: github-actions-provider)")
        print("  --direction        Secret sync direction (github_to_gcp, gcp_to_github, bidirectional)")
        print("  --sync-level       GitHub secret sync level (organization, repository, environment)")
        print("  --wif-only         Only set up Workload Identity Federation")
        print("  --dry-run          Don't actually make changes")
        print("  --verbose          Enable verbose logging")
        print("\nEnvironment Variables:")
        print("  GCP_MASTER_SERVICE_JSON      GCP service account key with admin permissions")
        print("  GCP_SECRET_MANAGEMENT_KEY    GCP service account key for secret management")
        print("  GH_CLASSIC_PAT_TOKEN         GitHub classic PAT with admin:org, repo, workflow scope")
        print("  GH_FINE_GRAINED_TOKEN        GitHub fine-grained token with repository permissions")
        print("\nExamples:")
        print("  python setup_gcp_github_integration.py setup --project-id=my-project --github-org=my-org")
        print("  python setup_gcp_github_integration.py sync-secrets --direction=bidirectional")
        print("  python setup_gcp_github_integration.py verify")


def parse_args() -> IntegrationConfig:
    """Parse command-line arguments.
    
    Returns:
        Integration configuration
    """
    parser = argparse.ArgumentParser(description="GCP-GitHub Integration Setup Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up GCP-GitHub integration")
    setup_parser.add_argument("--stage", choices=[s.value for s in SetupStage], 
                           default=SetupStage.ALL.value, help="Setup stage to execute")
    setup_parser.add_argument("--project-id", required=True, help="GCP project ID")
    setup_parser.add_argument("--region", default="us-central1", help="GCP region")
    setup_parser.add_argument("--github-org", required=True, help="GitHub organization name")
    setup_parser.add_argument("--github-repo", help="GitHub repository name (org/repo format)")
    setup_parser.add_argument("--service-account", default="github-actions", help="Service account name")
    setup_parser.add_argument("--pool-id", default="github-actions-pool", help="Workload identity pool ID")
    setup_parser.add_argument("--provider-id", default="github-actions-provider", help="Workload identity provider ID")
    setup_parser.add_argument("--wif-only", action="store_true", help="Only set up Workload Identity Federation")
    setup_parser.add_argument("--dry-run", action="store_true", help="Don't actually make changes")
    setup_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # Sync secrets command
    sync_parser = subparsers.add_parser("sync-secrets", help="Synchronize secrets between GitHub and GCP")
    sync_parser.add_argument("--project-id", required=True, help="GCP project ID")
    sync_parser.add_argument("--region", default="us-central1", help="GCP region")
    sync_parser.add_argument("--github-org", required=True, help="GitHub organization name")
    sync_parser.add_argument("--github-repo", help="GitHub repository name (org/repo format)")
    sync_parser.add_argument("--direction", choices=[d.value for d in SyncDirection], 
                          default=SyncDirection.BIDIRECTIONAL.value, help="Sync direction")
    sync_parser.add_argument("--level", choices=[l.value for l in SyncLevel], 
                          default=SyncLevel.ORGANIZATION.value, help="Sync level")
    sync_parser.add_argument("--dry-run", action="store_true", help="Don't actually make changes")
    sync_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify the GCP-GitHub integration setup")
    verify_parser.add_argument("--project-id", required=True, help="GCP project ID")
    verify_parser.add_argument("--region", default="us-central1", help="GCP region")
    verify_parser.add_argument("--github-org", required=True, help="GitHub organization name")
    verify_parser.add_argument("--github-repo", help="GitHub repository name (org/repo format)")
    verify_parser.add_argument("--service-account", default="github-actions", help="Service account name")
    verify_parser.add_argument("--pool-id", default="github-actions-pool", help="Workload identity pool ID")
    verify_parser.add_argument("--provider-id", default="github-actions-provider", help="Workload identity provider ID")
    verify_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # Help command
    subparsers.add_parser("help", help="Show help information")
    
    args = parser.parse_args()
    
    # Handle help command
    if not args.command or args.command == "help":
        return IntegrationConfig(command=Command.HELP)
    
    # Convert arguments to configuration
    if args.command == "setup":
        return IntegrationConfig(
            command=Command.SETUP,
            stage=SetupStage(args.stage),
            gcp_project_id=args.project_id,
            gcp_region=args.region,
            github_org=args.github_org,
            github_repo=args.github_repo,
            service_account_name=args.service_account,
            pool_id=args.pool_id,
            provider_id=args.provider_id,
            workload_identity_only=args.wif_only,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
    elif args.command == "sync-secrets":
        return IntegrationConfig(
            command=Command.SYNC_SECRETS,
            gcp_project_id=args.project_id,
            gcp_region=args.region,
            github_org=args.github_org,
            github_repo=args.github_repo,
            sync_direction=SyncDirection(args.direction),
            sync_level=SyncLevel(args.level),
            dry_run=args.dry_run,
            verbose=args.verbose
        )
    elif args.command == "verify":
        return IntegrationConfig(
            command=Command.VERIFY,
            gcp_project_id=args.project_id,
            gcp_region=args.region,
            github_org=args.github_org,
            github_repo=args.github_repo,
            service_account_name=args.service_account,
            pool_id=args.pool_id,
            provider_id=args.provider_id,
            verbose=args.verbose
        )
    else:
        return IntegrationConfig(command=Command.HELP)


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command-line arguments
    config = parse_args()
    
    # Create and run the integration setup
    integration = IntegrationSetup(config)
    return integration.run()


if __name__ == "__main__":
    sys.exit(main())