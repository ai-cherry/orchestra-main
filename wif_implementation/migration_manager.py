"""
Migration manager for the WIF implementation.

This module provides functionality to manage the migration from service account keys to WIF.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from .error_handler import WIFError, ErrorSeverity, handle_exception, safe_execute
from . import ImplementationPhase, TaskStatus, Task, ImplementationPlan

# Configure logging
logger = logging.getLogger("wif_implementation.migration_manager")


class MigrationError(WIFError):
    """Exception raised when there is a migration error."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: The error message
            details: Additional details about the error
            cause: The underlying exception that caused this error
        """
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details,
            cause=cause,
        )


class MigrationManager:
    """
    Manager for the migration from service account keys to WIF.

    This class provides functionality to manage the migration from service account keys to WIF.
    """

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize the migration manager.

        Args:
            base_path: The base path for the implementation
            verbose: Whether to show detailed output during processing
            dry_run: Whether to run in dry-run mode
        """
        # If base_path is not provided, use the current directory
        if base_path is None:
            base_path = Path(".")

        self.base_path = Path(base_path).resolve()
        self.verbose = verbose
        self.dry_run = dry_run

        if verbose:
            logger.setLevel(logging.DEBUG)

        logger.debug(f"Initialized migration manager with base path: {self.base_path}")

    def execute_task(self, task_name: str, plan: ImplementationPlan) -> bool:
        """
        Execute a task.

        Args:
            task_name: The name of the task to execute
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        # Get the task
        task = plan.get_task_by_name(task_name)
        if not task:
            logger.error(f"Task {task_name} not found")
            return False

        # Check if the task is in the migration phase
        if task.phase != ImplementationPhase.MIGRATION:
            logger.error(f"Task {task_name} is not in the migration phase")
            return False

        # Execute the task based on its name
        if task_name == "prepare_environment":
            return self._prepare_environment(plan)
        elif task_name == "create_backups":
            return self._create_backups(plan)
        elif task_name == "run_migration_dev":
            return self._run_migration_dev(plan)
        elif task_name == "verify_migration_dev":
            return self._verify_migration_dev(plan)
        elif task_name == "run_migration_prod":
            return self._run_migration_prod(plan)
        elif task_name == "verify_migration_prod":
            return self._verify_migration_prod(plan)
        elif task_name == "update_documentation":
            return self._update_documentation(plan)
        elif task_name == "cleanup_legacy":
            return self._cleanup_legacy(plan)
        else:
            logger.error(f"Unknown task: {task_name}")
            return False

    @handle_exception
    def _prepare_environment(self, plan: ImplementationPlan) -> bool:
        """
        Prepare the environment for migration.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Preparing the environment for migration")

        # Check if gcloud is available
        if not self._check_command("gcloud"):
            logger.error("gcloud command not found")
            return False

        # Check if the user is authenticated
        if self.dry_run:
            logger.info("Would check if the user is authenticated with gcloud")
        else:
            try:
                # Check if the user is authenticated
                subprocess.check_call(
                    ["gcloud", "auth", "list"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=self.base_path,
                )
            except subprocess.CalledProcessError:
                logger.error("User is not authenticated with gcloud")
                return False

        # Check if the project is set
        if self.dry_run:
            logger.info("Would check if the project is set")
        else:
            try:
                # Get the current project
                project = subprocess.check_output(
                    ["gcloud", "config", "get-value", "project"],
                    text=True,
                    cwd=self.base_path,
                ).strip()

                if not project:
                    logger.error("Project is not set")
                    return False

                logger.info(f"Using project: {project}")
            except subprocess.CalledProcessError:
                logger.error("Failed to get project")
                return False

        # Check if the Workload Identity Federation API is enabled
        if self.dry_run:
            logger.info(
                "Would check if the Workload Identity Federation API is enabled"
            )
        else:
            try:
                # Check if the API is enabled
                result = subprocess.check_output(
                    [
                        "gcloud",
                        "services",
                        "list",
                        "--format=value(NAME)",
                        "--filter=NAME:iam.googleapis.com",
                    ],
                    text=True,
                    cwd=self.base_path,
                ).strip()

                if not result:
                    logger.info("Enabling the IAM API")
                    subprocess.check_call(
                        ["gcloud", "services", "enable", "iam.googleapis.com"],
                        cwd=self.base_path,
                    )
            except subprocess.CalledProcessError:
                logger.error("Failed to check or enable the IAM API")
                return False

        logger.info("Environment prepared successfully")
        return True

    @handle_exception
    def _create_backups(self, plan: ImplementationPlan) -> bool:
        """
        Create backups of the current state.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Creating backups of the current state")

        # Create a backup directory
        backup_dir = self.base_path / "wif_migration_backup"

        if self.dry_run:
            logger.info(f"Would create backup directory: {backup_dir}")
        else:
            # Create the backup directory
            backup_dir.mkdir(exist_ok=True)
            logger.info(f"Created backup directory: {backup_dir}")

        # Backup service account keys
        if self.dry_run:
            logger.info("Would backup service account keys")
        else:
            # Find service account key files
            key_files = list(self.base_path.glob("**/*.json"))

            # Filter for service account key files
            service_account_key_files = []
            for key_file in key_files:
                try:
                    with open(key_file, "r") as f:
                        key_data = json.load(f)
                        if "type" in key_data and key_data["type"] == "service_account":
                            service_account_key_files.append(key_file)
                except (json.JSONDecodeError, UnicodeDecodeError, IOError):
                    # Not a valid JSON file or not readable
                    pass

            # Backup service account key files
            for key_file in service_account_key_files:
                # Create a relative path for the backup
                relative_path = key_file.relative_to(self.base_path)
                backup_path = backup_dir / relative_path

                # Create parent directories
                backup_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy the file
                shutil.copy2(key_file, backup_path)
                logger.info(f"Backed up service account key: {relative_path}")

        # Backup GitHub Actions workflow files
        if self.dry_run:
            logger.info("Would backup GitHub Actions workflow files")
        else:
            # Find GitHub Actions workflow files
            workflow_dir = self.base_path / ".github" / "workflows"
            if workflow_dir.exists():
                # Create the backup workflow directory
                backup_workflow_dir = backup_dir / ".github" / "workflows"
                backup_workflow_dir.mkdir(parents=True, exist_ok=True)

                # Copy workflow files
                for workflow_file in workflow_dir.glob("*.yml"):
                    shutil.copy2(
                        workflow_file, backup_workflow_dir / workflow_file.name
                    )
                    logger.info(f"Backed up workflow file: {workflow_file.name}")

        # Backup CI/CD configuration files
        if self.dry_run:
            logger.info("Would backup CI/CD configuration files")
        else:
            # Find CI/CD configuration files
            ci_files = []
            ci_files.extend(self.base_path.glob("**/cloudbuild.yaml"))
            ci_files.extend(self.base_path.glob("**/cloudbuild.yml"))
            ci_files.extend(self.base_path.glob("**/.gitlab-ci.yml"))
            ci_files.extend(self.base_path.glob("**/azure-pipelines.yml"))
            ci_files.extend(self.base_path.glob("**/Jenkinsfile"))

            # Backup CI/CD configuration files
            for ci_file in ci_files:
                # Create a relative path for the backup
                relative_path = ci_file.relative_to(self.base_path)
                backup_path = backup_dir / relative_path

                # Create parent directories
                backup_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy the file
                shutil.copy2(ci_file, backup_path)
                logger.info(f"Backed up CI/CD configuration file: {relative_path}")

        logger.info("Backups created successfully")
        return True

    @handle_exception
    def _run_migration_dev(self, plan: ImplementationPlan) -> bool:
        """
        Run the migration script in development.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Running the migration script in development")

        if self.dry_run:
            logger.info("Would run the migration script in development")
            return True

        # Check if the migration script exists
        migration_script = self.base_path / "scripts" / "migrate_to_wif.sh"
        if not migration_script.exists():
            logger.error(f"Migration script not found: {migration_script}")
            return False

        try:
            # Make the script executable
            os.chmod(migration_script, 0o755)

            # Run the migration script
            subprocess.check_call(
                [str(migration_script), "--env=dev"],
                cwd=self.base_path,
            )

            logger.info("Migration script executed successfully in development")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing migration script in development: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error running migration in development: {str(e)}")
            raise MigrationError(
                f"Failed to run migration in development",
                cause=e,
            )

    @handle_exception
    def _verify_migration_dev(self, plan: ImplementationPlan) -> bool:
        """
        Verify migration success in development.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Verifying migration success in development")

        if self.dry_run:
            logger.info("Would verify migration success in development")
            return True

        # Check if the verification script exists
        verification_script = self.base_path / "scripts" / "verify_wif.sh"
        if not verification_script.exists():
            logger.error(f"Verification script not found: {verification_script}")
            return False

        try:
            # Make the script executable
            os.chmod(verification_script, 0o755)

            # Run the verification script
            subprocess.check_call(
                [str(verification_script), "--env=dev"],
                cwd=self.base_path,
            )

            logger.info("Migration verified successfully in development")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error verifying migration in development: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying migration in development: {str(e)}")
            raise MigrationError(
                f"Failed to verify migration in development",
                cause=e,
            )

    @handle_exception
    def _run_migration_prod(self, plan: ImplementationPlan) -> bool:
        """
        Run the migration script in production.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Running the migration script in production")

        if self.dry_run:
            logger.info("Would run the migration script in production")
            return True

        # Check if the migration script exists
        migration_script = self.base_path / "scripts" / "migrate_to_wif.sh"
        if not migration_script.exists():
            logger.error(f"Migration script not found: {migration_script}")
            return False

        try:
            # Make the script executable
            os.chmod(migration_script, 0o755)

            # Run the migration script
            subprocess.check_call(
                [str(migration_script), "--env=prod"],
                cwd=self.base_path,
            )

            logger.info("Migration script executed successfully in production")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing migration script in production: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error running migration in production: {str(e)}")
            raise MigrationError(
                f"Failed to run migration in production",
                cause=e,
            )

    @handle_exception
    def _verify_migration_prod(self, plan: ImplementationPlan) -> bool:
        """
        Verify migration success in production.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Verifying migration success in production")

        if self.dry_run:
            logger.info("Would verify migration success in production")
            return True

        # Check if the verification script exists
        verification_script = self.base_path / "scripts" / "verify_wif.sh"
        if not verification_script.exists():
            logger.error(f"Verification script not found: {verification_script}")
            return False

        try:
            # Make the script executable
            os.chmod(verification_script, 0o755)

            # Run the verification script
            subprocess.check_call(
                [str(verification_script), "--env=prod"],
                cwd=self.base_path,
            )

            logger.info("Migration verified successfully in production")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error verifying migration in production: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying migration in production: {str(e)}")
            raise MigrationError(
                f"Failed to verify migration in production",
                cause=e,
            )

    @handle_exception
    def _update_documentation(self, plan: ImplementationPlan) -> bool:
        """
        Update documentation.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Updating documentation")

        if self.dry_run:
            logger.info("Would update documentation")
            return True

        # Check if the documentation directory exists
        docs_dir = self.base_path / "docs"
        if not docs_dir.exists():
            logger.warning(f"Documentation directory not found: {docs_dir}")
            docs_dir.mkdir(exist_ok=True)

        # Create or update the WIF documentation
        wif_doc_path = docs_dir / "WORKLOAD_IDENTITY_FEDERATION.md"

        # Create the documentation content
        doc_content = """# Workload Identity Federation (WIF)

## Overview

This document provides information about the Workload Identity Federation (WIF) implementation for the AI Orchestra project.

## What is Workload Identity Federation?

Workload Identity Federation allows applications to access Google Cloud resources without using service account keys. Instead, it uses a trust relationship between Google Cloud and an external identity provider.

## Benefits

- **Improved Security**: No need to manage and secure service account keys
- **Simplified Operations**: No need to rotate keys or manage key distribution
- **Reduced Risk**: No risk of key exposure or compromise
- **Audit Trail**: Better visibility into who is accessing what resources

## Implementation

The AI Orchestra project has been migrated from service account keys to Workload Identity Federation. This migration involved the following steps:

1. Creating a Workload Identity Pool
2. Creating a Workload Identity Provider
3. Creating service accounts for each workload
4. Granting IAM permissions to the service accounts
5. Configuring the workloads to use Workload Identity Federation
6. Removing service account keys

## Usage

### GitHub Actions

To use Workload Identity Federation in GitHub Actions, add the following to your workflow:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/auth@v1
        with:
          workload_identity_provider: 'projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'my-service-account@my-project.iam.gserviceaccount.com'
      - uses: google-github-actions/setup-gcloud@v1
```

### Local Development

For local development, use the gcloud CLI to authenticate:

```bash
gcloud auth login
```

## Troubleshooting

If you encounter issues with Workload Identity Federation, check the following:

1. Ensure the service account has the necessary IAM permissions
2. Ensure the Workload Identity Provider is configured correctly
3. Check the logs for error messages

## References

- [Google Cloud Workload Identity Federation Documentation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GitHub Actions with Workload Identity Federation](https://github.com/google-github-actions/auth)
"""

        # Write the documentation
        with open(wif_doc_path, "w") as f:
            f.write(doc_content)

        logger.info(f"Updated documentation: {wif_doc_path}")
        return True

    @handle_exception
    def _cleanup_legacy(self, plan: ImplementationPlan) -> bool:
        """
        Clean up legacy components.

        Args:
            plan: The implementation plan

        Returns:
            True if the task was executed successfully, False otherwise
        """
        logger.info("Cleaning up legacy components")

        if self.dry_run:
            logger.info("Would clean up legacy components")
            return True

        # Find service account key files
        key_files = list(self.base_path.glob("**/*.json"))

        # Filter for service account key files
        service_account_key_files = []
        for key_file in key_files:
            try:
                with open(key_file, "r") as f:
                    key_data = json.load(f)
                    if "type" in key_data and key_data["type"] == "service_account":
                        service_account_key_files.append(key_file)
            except (json.JSONDecodeError, UnicodeDecodeError, IOError):
                # Not a valid JSON file or not readable
                pass

        # Remove service account key files
        for key_file in service_account_key_files:
            # Create a relative path for logging
            relative_path = key_file.relative_to(self.base_path)

            # Remove the file
            key_file.unlink()
            logger.info(f"Removed service account key: {relative_path}")

        logger.info("Legacy components cleaned up successfully")
        return True

    def _check_command(self, command: str) -> bool:
        """
        Check if a command is available.

        Args:
            command: The command to check

        Returns:
            True if the command is available, False otherwise
        """
        try:
            subprocess.check_call(
                ["which", command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False
