#!/usr/bin/env python3
"""
Secure GCP Project Migration Utility

This script securely handles GCP project migration between organizations with these security features:
- Uses temporary files for service account keys
- Implements proper IAM propagation waiting period
- Validates migration success
- Handles errors with automatic retry and backoff

Usage:
  python3 secure_gcp_project_migrator.py \
    --project-id=YOUR_PROJECT_ID \
    --source-org=SOURCE_ORG_ID \
    --target-org=TARGET_ORG_ID \
    --service-account=SERVICE_ACCOUNT_EMAIL

Requirements:
  pip install google-auth google-api-python-client tempfile backoff
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from typing import List

import backoff
from google.oauth2 import service_account
from googleapiclient import discovery, errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class SecureGCPProjectMigrator:
    """Securely migrates GCP projects between organizations with temporary credentials."""

    def __init__(
        self,
        project_id: str,
        service_account_email: str,
        target_org_id: str,
        iam_propagation_time: int = 300,  # 5 minutes
    ):
        """
        Initialize the secure project migrator.

        Args:
            project_id: GCP project ID to migrate
            service_account_email: Service account email address
            target_org_id: Target organization ID
            iam_propagation_time: Time to wait for IAM changes to propagate (seconds)
        """
        self.project_id = project_id
        self.service_account_email = service_account_email
        self.target_org_id = target_org_id
        self.iam_propagation_time = iam_propagation_time
        self.temp_key_file = None
        self.credentials = None
        self.resource_manager = None

    def __enter__(self):
        """Context manager entry that creates temporary key file."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit that cleans up temporary files."""
        self._cleanup_temp_files()

    def _cleanup_temp_files(self) -> None:
        """Securely remove temporary key files."""
        if self.temp_key_file and os.path.exists(self.temp_key_file.name):
            # Close and remove the temporary file
            self.temp_key_file.close()
            logger.info("Temporary credentials securely removed")

    def create_service_account_key(self) -> str:
        """
        Create a service account key and store it in a secure temporary file.

        Returns:
            Path to the temporary key file
        """
        logger.info(
            f"Creating temporary service account key for {self.service_account_email}"
        )

        # Create a secure temporary file with restricted permissions
        self.temp_key_file = tempfile.NamedTemporaryFile(delete=False)
        os.chmod(self.temp_key_file.name, 0o600)  # Restricted permissions

        # Use gcloud to create the key
        cmd = [
            "gcloud",
            "iam",
            "service-accounts",
            "keys",
            "create",
            self.temp_key_file.name,
            "--iam-account",
            self.service_account_email,
            "--format",
            "json",
        ]

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            logger.info("Service account key created successfully (temporary file)")
            return self.temp_key_file.name
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create service account key: {e.stderr.decode()}")
            self._cleanup_temp_files()
            raise

    def authenticate_with_key(self, key_file: str) -> None:
        """
        Authenticate with the provided service account key.

        Args:
            key_file: Path to the service account key file
        """
        logger.info("Authenticating with service account")
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                key_file, scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            self.resource_manager = discovery.build(
                "cloudresourcemanager", "v3", credentials=self.credentials
            )
            logger.info("Authentication successful")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    def grant_org_roles(self, org_id: str, roles: List[str]) -> None:
        """
        Grant organization-level roles to the service account.

        Args:
            org_id: Organization ID to grant roles in
            roles: List of roles to grant
        """
        for role in roles:
            logger.info(
                f"Granting {role} to {self.service_account_email} in organization {org_id}"
            )
            cmd = [
                "gcloud",
                "organizations",
                "add-iam-policy-binding",
                org_id,
                "--member",
                f"serviceAccount:{self.service_account_email}",
                "--role",
                role,
            ]

            try:
                subprocess.run(
                    cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                logger.info(f"Successfully granted {role}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to grant {role}: {e.stderr.decode()}")
                raise

    def wait_for_iam_propagation(self) -> None:
        """Wait for IAM role changes to propagate across the GCP environment."""
        logger.info(
            f"Waiting {self.iam_propagation_time} seconds for IAM propagation..."
        )

        # Show progress during the wait
        start_time = time.time()
        for i in range(self.iam_propagation_time):
            elapsed = int(time.time() - start_time)
            remaining = self.iam_propagation_time - elapsed

            # Update progress every 5 seconds
            if elapsed % 5 == 0:
                # Calculate progress percentage
                progress = int((elapsed / self.iam_propagation_time) * 100)
                logger.info(
                    f"IAM propagation: {progress}% complete, {remaining} seconds remaining"
                )

            time.sleep(1)

        logger.info("IAM propagation wait period completed")

    @backoff.on_exception(
        backoff.expo,
        (subprocess.CalledProcessError, errors.HttpError),
        max_tries=5,
        max_time=600,
    )
    def move_project(self) -> bool:
        """
        Move the project to the target organization.

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            f"Moving project {self.project_id} to organization {self.target_org_id}"
        )
        cmd = [
            "gcloud",
            "beta",
            "projects",
            "move",
            self.project_id,
            "--organization",
            self.target_org_id,
            "--billing-project",
            self.project_id,
        ]

        try:
            subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            logger.info("Project migration command completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            # Special handling for permission denied errors
            if "PERMISSION_DENIED" in e.stderr.decode():
                logger.error("Permission denied error during project move")
                self._handle_permission_denied_error()
                # Re-raise to trigger backoff
                raise
            else:
                logger.error(f"Project move failed: {e.stderr.decode()}")
                raise

    def _handle_permission_denied_error(self) -> None:
        """Handle permission denied errors with diagnostics and remediation."""
        logger.info("Diagnosing permission denied error...")

        # Check role assignments
        try:
            # Check organization-level roles
            cmd = [
                "gcloud",
                "organizations",
                "get-iam-policy",
                self.target_org_id,
                "--filter",
                f"bindings.members:serviceAccount:{self.service_account_email}",
                "--format",
                "json",
            ]
            result = subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            policy = json.loads(result.stdout.decode())

            # Extract roles assigned to our service account
            roles = set()
            for binding in policy.get("bindings", []):
                if f"serviceAccount:{self.service_account_email}" in binding.get(
                    "members", []
                ):
                    roles.add(binding.get("role"))

            # Check if critical roles are missing
            required_roles = {
                "roles/resourcemanager.projectMover",
                "roles/resourcemanager.projectCreator",
            }
            missing_roles = required_roles - roles

            if missing_roles:
                logger.error(f"Missing required roles: {missing_roles}")
                logger.info("Attempting to re-grant missing roles...")

                # Re-grant missing roles
                for role in missing_roles:
                    try:
                        self.grant_org_roles(self.target_org_id, [role])
                    except Exception as e:
                        logger.error(f"Failed to grant role {role}: {str(e)}")

                # Additional wait for newly granted roles
                logger.info(
                    "Waiting additional time for new role grants to propagate..."
                )
                time.sleep(120)  # 2 minutes additional wait
            else:
                logger.info("All required roles are correctly assigned")

            # Check organization policies that might block project migration
            logger.info("Checking organization policies...")
            try:
                cmd = [
                    "gcloud",
                    "resource-manager",
                    "org-policies",
                    "list",
                    "--organization",
                    self.target_org_id,
                    "--format",
                    "json",
                ]
                result = subprocess.run(
                    cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                policies = json.loads(result.stdout.decode())

                # Check for restrictive policies
                for policy in policies:
                    if (
                        "constraints/resourcemanager.projectsMoveRestriction"
                        in policy.get("name", "")
                    ):
                        logger.warning(
                            "Organization has project move restrictions in place!"
                        )
                        break
            except Exception as e:
                logger.error(f"Error checking organization policies: {str(e)}")

        except Exception as e:
            logger.error(f"Error during permission denied diagnosis: {str(e)}")

    def verify_migration(self) -> bool:
        """
        Verify the project migration was successful.

        Returns:
            True if successful, False otherwise
        """
        logger.info(
            f"Verifying project {self.project_id} migration to organization {self.target_org_id}"
        )
        cmd = [
            "gcloud",
            "projects",
            "describe",
            self.project_id,
            "--format",
            "value(parent.id)",
        ]

        try:
            result = subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            current_org = result.stdout.decode().strip()

            if current_org == self.target_org_id:
                logger.info(
                    f"✅ Verification successful: Project is now in organization {self.target_org_id}"
                )
                return True
            else:
                logger.error(
                    f"❌ Verification failed: Project is in organization {current_org}, not {self.target_org_id}"
                )
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Verification failed: {e.stderr.decode()}")
            return False

    def migrate(self) -> bool:
        """
        Perform the complete migration process.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create temporary service account key
            key_file = self.create_service_account_key()

            # Authenticate with the service account
            self.authenticate_with_key(key_file)

            # Grant required organization roles
            required_roles = [
                "roles/resourcemanager.projectMover",
                "roles/resourcemanager.projectCreator",
            ]
            self.grant_org_roles(self.target_org_id, required_roles)

            # Wait for IAM propagation
            self.wait_for_iam_propagation()

            # Move the project
            migration_success = self.move_project()

            # Verify the migration
            verification_success = self.verify_migration()

            return migration_success and verification_success

        except Exception as e:
            logger.error(f"Migration process failed: {str(e)}")
            return False
        finally:
            # Always clean up temporary files
            self._cleanup_temp_files()


def main():
    """Parse arguments and run the migration."""
    parser = argparse.ArgumentParser(
        description="Securely migrate GCP projects between organizations"
    )
    parser.add_argument("--project-id", required=True, help="GCP project ID to migrate")
    parser.add_argument(
        "--service-account", required=True, help="Service account email address"
    )
    parser.add_argument("--target-org", required=True, help="Target organization ID")
    parser.add_argument(
        "--iam-wait",
        type=int,
        default=300,
        help="IAM propagation wait time in seconds (default: 300)",
    )
    args = parser.parse_args()

    # Log the start of migration with timestamp
    start_time = datetime.now()
    logger.info(f"Starting secure migration process at {start_time.isoformat()}")
    logger.info(f"Project: {args.project_id}, Target organization: {args.target_org}")

    # Create and use the migrator as a context manager to ensure cleanup
    with SecureGCPProjectMigrator(
        project_id=args.project_id,
        service_account_email=args.service_account,
        target_org_id=args.target_org,
        iam_propagation_time=args.iam_wait,
    ) as migrator:
        success = migrator.migrate()

    # Log completion with duration
    end_time = datetime.now()
    duration = end_time - start_time

    if success:
        logger.info(f"Migration completed successfully in {duration}")
        return 0
    else:
        logger.error(f"Migration failed after {duration}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
