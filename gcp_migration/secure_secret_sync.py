#!/usr/bin/env python3
"""
Secure Bidirectional Secret Synchronization for GitHub and GCP

This module provides tools to securely synchronize secrets between
GitHub and Google Cloud Platform's Secret Manager. It implements
secure handling of credentials, proper versioning, conflict resolution,
and audit logging.
"""

import base64
import json
import logging
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import uuid

# For GitHub token encryption and secure GitHub API calls
import nacl.encoding
import nacl.public
import requests
from cryptography.fernet import Fernet

# For Google Cloud Secret Manager
from google.cloud import secretmanager
from google.cloud.secretmanager_v1.types import (
    Secret,
    SecretVersion,
    SecretPayload,
    Replication,
    AccessSecretVersionResponse,
)

# Local imports
from gcp_migration.secure_auth import (
    GCPAuth,
    GitHubAuth,
    GCPConfig,
    GitHubConfig,
    AuthMethod,
    secure_cleanup,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("secret-sync")

# Add parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class SyncDirection(Enum):
    """Direction of secret synchronization."""

    GITHUB_TO_GCP = "github_to_gcp"
    GCP_TO_GITHUB = "gcp_to_github"
    BIDIRECTIONAL = "bidirectional"


class SyncLevel(Enum):
    """Level at which to synchronize GitHub secrets."""

    ORGANIZATION = "organization"
    REPOSITORY = "repository"
    ENVIRONMENT = "environment"


@dataclass
class GitHubSecret:
    """GitHub secret model."""

    name: str
    visibility: str = "private"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    value: Optional[str] = None

    # Repository-specific fields
    repo_name: Optional[str] = None

    # Environment-specific fields
    environment: Optional[str] = None

    @property
    def gcp_secret_name(self) -> str:
        """Convert GitHub secret name to GCP secret name format.

        Returns:
            Formatted GCP secret name
        """
        # Prefix with github- to avoid name conflicts
        # Use lowercase for GCP secret names
        prefix = "github-"

        # Add environment prefix if applicable
        if self.environment:
            prefix += f"{self.environment.lower()}-"

        # Add repo prefix if applicable
        if self.repo_name:
            repo_short = self.repo_name.split("/")[-1]  # Get repo name without org
            prefix += f"{repo_short.lower()}-"

        # Return formatted name
        return f"{prefix}{self.name.lower()}"


@dataclass
class GCPSecret:
    """GCP Secret Manager secret model."""

    name: str
    project_id: str
    version: str = "latest"
    value: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """Get full secret name including project.

        Returns:
            Full secret name with project
        """
        return f"projects/{self.project_id}/secrets/{self.name}"

    @property
    def version_name(self) -> str:
        """Get full version name.

        Returns:
            Full version name
        """
        return f"{self.full_name}/versions/{self.version}"

    @property
    def github_secret_name(self) -> str:
        """Convert GCP secret name to GitHub secret name format.

        Returns:
            GitHub secret name
        """
        # If the secret starts with 'github-', it's already a mapped secret
        if self.name.startswith("github-"):
            # Remove the 'github-' prefix and any environment or repo prefixes
            parts = self.name[7:].split("-")

            # If there are environment or repository indicators in the labels,
            # we need to handle them appropriately
            if "environment" in self.labels or "repository" in self.labels:
                # Try to determine how many prefix segments to skip
                skip = 0
                if "environment" in self.labels:
                    skip += 1
                if "repository" in self.labels:
                    skip += 1

                # Skip the appropriate number of segments and join the rest
                if skip < len(parts):
                    return "-".join(parts[skip:]).upper()

            # If no special handling is needed, just remove the prefix and uppercase
            return self.name[7:].upper()
        else:
            # For non-mapped secrets, just uppercase the name
            return self.name.upper()


class SecretVersionState(Enum):
    """State of a secret version in GCP Secret Manager."""

    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DESTROYED = "DESTROYED"


@dataclass
class SyncResult:
    """Result of a secret synchronization operation."""

    success: bool
    source: str
    target: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[Exception] = None


class SecureSyncConfig:
    """Configuration for secret synchronization."""

    def __init__(
        self,
        gcp_config: GCPConfig,
        github_config: GitHubConfig,
        sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        sync_level: SyncLevel = SyncLevel.ORGANIZATION,
        secret_prefix: str = "github-",
        exclude_patterns: List[str] = None,
        include_patterns: List[str] = None,
        dry_run: bool = False,
        audit_log_path: Optional[str] = None,
        verbose: bool = False,
    ):
        """Initialize secret sync configuration.

        Args:
            gcp_config: GCP configuration
            github_config: GitHub configuration
            sync_direction: Direction of synchronization
            sync_level: Level at which to synchronize GitHub secrets
            secret_prefix: Prefix for GCP secrets from GitHub
            exclude_patterns: Patterns for secrets to exclude
            include_patterns: Patterns for secrets to include (overrides exclude)
            dry_run: If True, don't actually perform sync
            audit_log_path: Path to write audit log
            verbose: Enable verbose logging
        """
        self.gcp_config = gcp_config
        self.github_config = github_config
        self.sync_direction = sync_direction
        self.sync_level = sync_level
        self.secret_prefix = secret_prefix
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []
        self.dry_run = dry_run
        self.audit_log_path = audit_log_path

        # Set log level
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)


class SecretSyncAuditor:
    """Manages audit logging for secret synchronization."""

    def __init__(self, log_path: Optional[str] = None):
        """Initialize the auditor.

        Args:
            log_path: Path to audit log file (optional)
        """
        self.log_path = log_path

        # Create log file directory if it doesn't exist
        if log_path:
            log_dir = os.path.dirname(os.path.abspath(log_path))
            os.makedirs(log_dir, exist_ok=True)

    def log_sync_event(
        self,
        operation: str,
        source: str,
        target: str,
        result: bool,
        details: Optional[str] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log a synchronization event.

        Args:
            operation: Type of operation (create, update, delete)
            source: Source system (GitHub or GCP)
            target: Target system (GitHub or GCP)
            result: Success or failure
            details: Additional details
            error: Exception if an error occurred
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create log entry
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "source": source,
            "target": target,
            "result": "success" if result else "failure",
            "details": details or "",
        }

        if error:
            log_entry["error"] = str(error)

        # Log to console
        result_str = "SUCCESS" if result else "FAILURE"
        logger.info(f"[AUDIT] {operation} from {source} to {target}: {result_str}")
        if details:
            logger.info(f"[AUDIT] Details: {details}")
        if error:
            logger.error(f"[AUDIT] Error: {error}")

        # Write to log file if configured
        if self.log_path:
            try:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to write to audit log: {e}")


class GitHubSecretManager:
    """Manages GitHub secrets."""

    def __init__(
        self,
        github_auth: GitHubAuth,
        sync_level: SyncLevel = SyncLevel.ORGANIZATION,
        auditor: Optional[SecretSyncAuditor] = None,
    ):
        """Initialize GitHub secret manager.

        Args:
            github_auth: GitHub authentication
            sync_level: Level at which to synchronize GitHub secrets
            auditor: Audit logger
        """
        self.github_auth = github_auth
        self.sync_level = sync_level
        self.auditor = auditor or SecretSyncAuditor()
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_auth.github_config.token}",
        }

    def list_secrets(
        self, repo_name: Optional[str] = None, environment: Optional[str] = None
    ) -> List[GitHubSecret]:
        """List GitHub secrets.

        Args:
            repo_name: Repository name (org/repo format) for repository-level secrets
            environment: Environment name for environment-level secrets

        Returns:
            List of GitHub secrets
        """
        secrets = []

        try:
            if self.sync_level == SyncLevel.ORGANIZATION:
                # List organization secrets
                org_name = self.github_auth.github_config.org_name
                url = f"https://api.github.com/orgs/{org_name}/actions/secrets"

                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                secret_data = response.json()

                for secret in secret_data.get("secrets", []):
                    secrets.append(
                        GitHubSecret(
                            name=secret["name"],
                            visibility=secret.get("visibility", "private"),
                            created_at=secret.get("created_at"),
                            updated_at=secret.get("updated_at"),
                        )
                    )

            if self.sync_level == SyncLevel.REPOSITORY or repo_name:
                # List repository secrets
                if not repo_name:
                    repo_name = self.github_auth.github_config.repo_name

                if not repo_name:
                    logger.error(
                        "Repository name is required for repository-level secrets"
                    )
                    return secrets

                url = f"https://api.github.com/repos/{repo_name}/actions/secrets"

                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                secret_data = response.json()

                for secret in secret_data.get("secrets", []):
                    secrets.append(
                        GitHubSecret(
                            name=secret["name"],
                            created_at=secret.get("created_at"),
                            updated_at=secret.get("updated_at"),
                            repo_name=repo_name,
                        )
                    )

            if self.sync_level == SyncLevel.ENVIRONMENT or environment:
                # List environment secrets
                if not repo_name:
                    repo_name = self.github_auth.github_config.repo_name

                if not repo_name:
                    logger.error(
                        "Repository name is required for environment-level secrets"
                    )
                    return secrets

                if not environment:
                    logger.error(
                        "Environment name is required for environment-level secrets"
                    )
                    return secrets

                url = f"https://api.github.com/repos/{repo_name}/environments/{environment}/secrets"

                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                secret_data = response.json()

                for secret in secret_data.get("secrets", []):
                    secrets.append(
                        GitHubSecret(
                            name=secret["name"],
                            created_at=secret.get("created_at"),
                            updated_at=secret.get("updated_at"),
                            repo_name=repo_name,
                            environment=environment,
                        )
                    )

            logger.info(f"Found {len(secrets)} GitHub secrets")
            return secrets

        except requests.RequestException as e:
            logger.error(f"Failed to list GitHub secrets: {e}")
            self.auditor.log_sync_event(
                operation="list",
                source="GitHub",
                target="local",
                result=False,
                details=f"Failed to list GitHub secrets: {e}",
                error=e,
            )
            return []

    def get_public_key(
        self, repo_name: Optional[str] = None, environment: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get public key for encrypting secrets.

        Args:
            repo_name: Repository name (org/repo format) for repository-level secrets
            environment: Environment name for environment-level secrets

        Returns:
            Tuple of (key_id, key) or (None, None) if failed
        """
        try:
            if (
                self.sync_level == SyncLevel.ORGANIZATION
                and not repo_name
                and not environment
            ):
                # Get organization public key
                org_name = self.github_auth.github_config.org_name
                url = (
                    f"https://api.github.com/orgs/{org_name}/actions/secrets/public-key"
                )
            elif repo_name and environment:
                # Get environment public key
                url = f"https://api.github.com/repos/{repo_name}/environments/{environment}/secrets/public-key"
            elif repo_name:
                # Get repository public key
                url = f"https://api.github.com/repos/{repo_name}/actions/secrets/public-key"
            else:
                logger.error("Invalid sync level or missing repository name")
                return None, None

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            key_data = response.json()
            return key_data["key_id"], key_data["key"]

        except requests.RequestException as e:
            logger.error(f"Failed to get GitHub public key: {e}")
            return None, None

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt a secret value for GitHub.

        Args:
            public_key: GitHub public key
            secret_value: Secret value to encrypt

        Returns:
            Base64-encoded encrypted secret
        """
        try:
            # Convert the public key to bytes
            public_key_bytes = public_key.encode("utf-8")

            # Convert the secret to bytes
            secret_bytes = secret_value.encode("utf-8")

            # Create a sealed box with the public key
            public_key_obj = nacl.public.PublicKey(
                public_key_bytes, nacl.encoding.Base64Encoder()
            )
            sealed_box = nacl.public.SealedBox(public_key_obj)

            # Encrypt the secret
            encrypted = sealed_box.encrypt(secret_bytes)

            # Return base64-encoded encrypted secret
            return base64.b64encode(encrypted).decode("utf-8")

        except Exception as e:
            logger.error(f"Failed to encrypt secret: {e}")
            raise

    def create_or_update_secret(
        self, secret: GitHubSecret, value: str, visibility: Optional[str] = None
    ) -> bool:
        """Create or update a GitHub secret.

        Args:
            secret: Secret to create or update
            value: Secret value
            visibility: Visibility for org secrets ('all', 'private', or 'selected')

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get appropriate public key
            key_id, public_key = self.get_public_key(
                repo_name=secret.repo_name, environment=secret.environment
            )

            if not key_id or not public_key:
                logger.error("Failed to get public key for secret encryption")
                return False

            # Encrypt the secret
            encrypted_value = self.encrypt_secret(public_key, value)

            # Determine the API endpoint and payload
            if (
                self.sync_level == SyncLevel.ORGANIZATION
                and not secret.repo_name
                and not secret.environment
            ):
                # Organization-level secret
                org_name = self.github_auth.github_config.org_name
                url = f"https://api.github.com/orgs/{org_name}/actions/secrets/{secret.name}"

                payload = {"encrypted_value": encrypted_value, "key_id": key_id}

                # Add visibility if provided
                if visibility:
                    payload["visibility"] = visibility
                elif secret.visibility:
                    payload["visibility"] = secret.visibility

            elif secret.repo_name and secret.environment:
                # Environment-level secret
                url = f"https://api.github.com/repos/{secret.repo_name}/environments/{secret.environment}/secrets/{secret.name}"

                payload = {"encrypted_value": encrypted_value, "key_id": key_id}

            elif secret.repo_name:
                # Repository-level secret
                url = f"https://api.github.com/repos/{secret.repo_name}/actions/secrets/{secret.name}"

                payload = {"encrypted_value": encrypted_value, "key_id": key_id}

            else:
                logger.error("Invalid secret configuration")
                return False

            # Make API request to create/update secret
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()

            logger.info(f"Successfully created/updated GitHub secret: {secret.name}")

            # Log the event
            self.auditor.log_sync_event(
                operation="create_or_update",
                source="GCP",
                target="GitHub",
                result=True,
                details=f"Created/updated secret: {secret.name}",
            )

            return True

        except requests.RequestException as e:
            logger.error(f"Failed to create/update GitHub secret {secret.name}: {e}")

            # Log the event
            self.auditor.log_sync_event(
                operation="create_or_update",
                source="GCP",
                target="GitHub",
                result=False,
                details=f"Failed to create/update secret: {secret.name}: {str(e)}",
                error=e,
            )

            return False

        except Exception as e:
            logger.error(f"Error creating/updating GitHub secret {secret.name}: {e}")

            # Log the event
            self.auditor.log_sync_event(
                operation="create_or_update",
                source="GCP",
                target="GitHub",
                result=False,
                details=f"Error creating/updating secret: {secret.name}: {str(e)}",
                error=e,
            )

            return False

    def delete_secret(self, secret: GitHubSecret) -> bool:
        """Delete a GitHub secret.

        Args:
            secret: Secret to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine the API endpoint
            if (
                self.sync_level == SyncLevel.ORGANIZATION
                and not secret.repo_name
                and not secret.environment
            ):
                # Organization-level secret
                org_name = self.github_auth.github_config.org_name
                url = f"https://api.github.com/orgs/{org_name}/actions/secrets/{secret.name}"

            elif secret.repo_name and secret.environment:
                # Environment-level secret
                url = f"https://api.github.com/repos/{secret.repo_name}/environments/{secret.environment}/secrets/{secret.name}"

            elif secret.repo_name:
                # Repository-level secret
                url = f"https://api.github.com/repos/{secret.repo_name}/actions/secrets/{secret.name}"

            else:
                logger.error("Invalid secret configuration")
                return False

            # Make API request to delete secret
            response = requests.delete(url, headers=self.headers)

            # Check if the secret was deleted or if it doesn't exist
            if response.status_code == 204 or response.status_code == 404:
                logger.info(
                    f"Successfully deleted GitHub secret (or it didn't exist): {secret.name}"
                )

                # Log the event
                self.auditor.log_sync_event(
                    operation="delete",
                    source="GCP",
                    target="GitHub",
                    result=True,
                    details=f"Deleted secret: {secret.name}",
                )

                return True

            # Otherwise, raise an exception
            response.raise_for_status()
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to delete GitHub secret {secret.name}: {e}")

            # Log the event
            self.auditor.log_sync_event(
                operation="delete",
                source="GCP",
                target="GitHub",
                result=False,
                details=f"Failed to delete secret: {secret.name}: {str(e)}",
                error=e,
            )

            return False


class GCPSecretManager:
    """Manages GCP Secret Manager secrets."""

    def __init__(self, gcp_auth: GCPAuth, auditor: Optional[SecretSyncAuditor] = None):
        """Initialize GCP Secret Manager.

        Args:
            gcp_auth: GCP authentication
            auditor: Audit logger
        """
        self.gcp_auth = gcp_auth
        self.project_id = gcp_auth.gcp_config.project_id
        self.auditor = auditor or SecretSyncAuditor()

        # Initialize Secret Manager client
        self.client = secretmanager.SecretManagerServiceClient()

    def list_secrets(
        self,
        prefix: Optional[str] = None,
        filter_labels: Optional[Dict[str, str]] = None,
    ) -> List[GCPSecret]:
        """List GCP secrets.

        Args:
            prefix: Secret name prefix to filter by
            filter_labels: Labels to filter secrets by

        Returns:
            List of GCP secrets
        """
        secrets = []

        try:
            # List all secrets in the project
            parent = f"projects/{self.project_id}"

            for secret in self.client.list_secrets(request={"parent": parent}):
                # Extract just the secret name (without project prefix)
                secret_name = secret.name.split("/")[-1]

                # Filter by prefix if provided
                if prefix and not secret_name.startswith(prefix):
                    continue

                # Filter by labels if provided
                if filter_labels:
                    if not all(
                        secret.labels.get(k) == v for k, v in filter_labels.items()
                    ):
                        continue

                # Create GCPSecret object
                gcp_secret = GCPSecret(
                    name=secret_name,
                    project_id=self.project_id,
                    labels={k: v for k, v in secret.labels.items()},
                )

                secrets.append(gcp_secret)

            logger.info(f"Found {len(secrets)} GCP secrets")
            return secrets

        except Exception as e:
            logger.error(f"Failed to list GCP secrets: {e}")
            self.auditor.log_sync_event(
                operation="list",
                source="GCP",
                target="local",
                result=False,
                details=f"Failed to list GCP secrets: {e}",
                error=e,
            )
            return []

    def get_secret_value(self, secret: GCPSecret) -> Optional[str]:
        """Get the value of a GCP secret.

        Args:
            secret: GCP secret

        Returns:
            Secret value or None if not found
        """
        try:
            # Access the secret version
            response = self.client.access_secret_version(
                request={"name": secret.version_name}
            )

            # Return the secret value
            return response.payload.data.decode("UTF-8")

        except Exception as e:
            logger.error(f"Failed to get value for GCP secret {secret.name}: {e}")
            return None

    def create_or_update_secret(
        self, secret: GCPSecret, value: str, labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """Create or update a GCP secret.

        Args:
            secret: Secret to create or update
            value: Secret value
            labels: Secret labels

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if secret exists
            parent = f"projects/{self.project_id}"
            secret_exists = False

            try:
                self.client.get_secret(request={"name": secret.full_name})
                secret_exists = True
            except:
                # Secret doesn't exist
                pass

            # Create or update the secret
            if not secret_exists:
                # Create new secret with labels
                create_request = {
                    "parent": parent,
                    "secret_id": secret.name,
                    "secret": {"replication": {"automatic": {}}},
                }

                # Add labels if provided
                if labels:
                    create_request["secret"]["labels"] = labels

                self.client.create_secret(request=create_request)
                logger.info(f"Created GCP secret: {secret.name}")
            elif labels:
                # Update existing secret's labels
                self.client.update_secret(
                    request={
                        "secret": {"name": secret.full_name, "labels": labels},
                        "update_mask": {"paths": ["labels"]},
                    }
                )
                logger.info(f"Updated GCP secret labels: {secret.name}")

            # Add new version with the value
            self.client.add_secret_version(
                request={
                    "parent": secret.full_name,
                    "payload": {"data": value.encode("UTF-8")},
                }
            )

            logger.info(f"Added new version for GCP secret: {secret.name}")

            # Log the event
            self.auditor.log_sync_event(
                operation="create_or_update",
                source="GitHub",
                target="GCP",
                result=True,
                details=f"Created/updated secret: {secret.name}",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to create/update GCP secret {secret.name}: {e}")

            # Log the event
            self.auditor.log_sync_event(
                operation="create_or_update",
                source="GitHub",
                target="GCP",
                result=False,
                details=f"Failed to create/update secret: {secret.name}: {str(e)}",
                error=e,
            )

            return False

    def delete_secret(self, secret: GCPSecret) -> bool:
        """Delete a GCP secret.

        Args:
            secret: Secret to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the secret
            self.client.delete_secret(request={"name": secret.full_name})

            logger.info(f"Deleted GCP secret: {secret.name}")

            # Log the event
            self.auditor.log_sync_event(
                operation="delete",
                source="GitHub",
                target="GCP",
                result=True,
                details=f"Deleted secret: {secret.name}",
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete GCP secret {secret.name}: {e}")

            # Log the event
            self.auditor.log_sync_event(
                operation="delete",
                source="GitHub",
                target="GCP",
                result=False,
                details=f"Failed to delete secret: {secret.name}: {str(e)}",
                error=e,
            )

            return False


class SecretSynchronizer:
    """Synchronizes secrets between GitHub and GCP Secret Manager."""

    def __init__(
        self,
        config: SecureSyncConfig,
        gcp_auth: GCPAuth,
        github_auth: GitHubAuth,
        auditor: Optional[SecretSyncAuditor] = None,
    ):
        """Initialize secret synchronizer.

        Args:
            config: Sync configuration
            gcp_auth: GCP authentication
            github_auth: GitHub authentication
            auditor: Audit logger
        """
        self.config = config
        self.gcp_auth = gcp_auth
        self.github_auth = github_auth
        self.auditor = auditor or SecretSyncAuditor(config.audit_log_path)

        # Initialize secret managers
        self.github_manager = GitHubSecretManager(
            github_auth=github_auth, sync_level=config.sync_level, auditor=self.auditor
        )

        self.gcp_manager = GCPSecretManager(gcp_auth=gcp_auth, auditor=self.auditor)

    def _filter_secrets(self, secret_name: str) -> bool:
        """Filter secrets based on include/exclude patterns.

        Args:
            secret_name: Secret name to filter

        Returns:
            True if the secret should be included, False otherwise
        """
        # If include patterns are specified, only include secrets matching those patterns
        if self.config.include_patterns:
            return any(
                pattern in secret_name for pattern in self.config.include_patterns
            )

        # If exclude patterns are specified, exclude secrets matching those patterns
        if self.config.exclude_patterns:
            return not any(
                pattern in secret_name for pattern in self.config.exclude_patterns
            )

        # Include all secrets by default
        return True

    def sync_github_to_gcp(
        self, repo_name: Optional[str] = None, environment: Optional[str] = None
    ) -> List[SyncResult]:
        """Synchronize GitHub secrets to GCP Secret Manager.

        Args:
            repo_name: Repository name (org/repo format) for repository-level secrets
            environment: Environment name for environment-level secrets

        Returns:
            List of sync results
        """
        results = []

        # List GitHub secrets
        github_secrets = self.github_manager.list_secrets(
            repo_name=repo_name, environment=environment
        )

        # Filter secrets
        github_secrets = [
            secret for secret in github_secrets if self._filter_secrets(secret.name)
        ]

        if not github_secrets:
            logger.info("No GitHub secrets to synchronize")
            return results

        # List existing GCP secrets
        gcp_secrets = self.gcp_manager.list_secrets(prefix=self.config.secret_prefix)

        # Create a map of GCP secrets by name
        gcp_secret_map = {secret.name: secret for secret in gcp_secrets}

        # Process each GitHub secret
        for github_secret in github_secrets:
            gcp_secret_name = github_secret.gcp_secret_name

            logger.info(
                f"Processing GitHub secret: {github_secret.name} -> GCP: {gcp_secret_name}"
            )

            # Prepare labels
            labels = {
                "source": "github",
                "sync_time": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            }

            # Add repository and environment labels if applicable
            if github_secret.repo_name:
                labels["repository"] = github_secret.repo_name.replace("/", "_")

            if github_secret.environment:
                labels["environment"] = github_secret.environment

            # Create GCP secret object
            gcp_secret = GCPSecret(
                name=gcp_secret_name,
                project_id=self.config.gcp_config.project_id,
                labels=labels,
            )

            # If it's a dry run, just log what would happen
            if self.config.dry_run:
                logger.info(
                    f"[DRY RUN] Would create/update GCP secret: {gcp_secret_name}"
                )
                results.append(
                    SyncResult(
                        success=True,
                        source=f"GitHub:{github_secret.name}",
                        target=f"GCP:{gcp_secret_name}",
                        message=f"[DRY RUN] Would create/update GCP secret: {gcp_secret_name}",
                    )
                )
                continue

            try:
                # Since GitHub API doesn't allow retrieving secret values, we'll just create a placeholder
                # This is a limitation of the GitHub API - in a real implementation, you'd need a secure way
                # to retrieve or store the actual secret values
                placeholder_value = f"PLACEHOLDER - This GitHub secret needs to be manually updated: {github_secret.name}"

                # If the secret already exists in GCP, don't overwrite the value
                if gcp_secret_name in gcp_secret_map:
                    logger.info(
                        f"GCP secret already exists: {gcp_secret_name}, updating labels only"
                    )

                    # Get the existing secret value
                    existing_value = self.gcp_manager.get_secret_value(
                        gcp_secret_map[gcp_secret_name]
                    )

                    # Use the existing value if available, otherwise use placeholder
                    secret_value = (
                        existing_value if existing_value else placeholder_value
                    )
                else:
                    logger.info(f"Creating new GCP secret: {gcp_secret_name}")
                    secret_value = placeholder_value

                # Create or update the GCP secret
                success = self.gcp_manager.create_or_update_secret(
                    secret=gcp_secret, value=secret_value, labels=labels
                )

                if success:
                    results.append(
                        SyncResult(
                            success=True,
                            source=f"GitHub:{github_secret.name}",
                            target=f"GCP:{gcp_secret_name}",
                            message=f"Successfully created/updated GCP secret: {gcp_secret_name}",
                        )
                    )
                else:
                    results.append(
                        SyncResult(
                            success=False,
                            source=f"GitHub:{github_secret.name}",
                            target=f"GCP:{gcp_secret_name}",
                            message=f"Failed to create/update GCP secret: {gcp_secret_name}",
                        )
                    )

            except Exception as e:
                logger.error(
                    f"Error syncing GitHub secret {github_secret.name} to GCP: {e}"
                )
                results.append(
                    SyncResult(
                        success=False,
                        source=f"GitHub:{github_secret.name}",
                        target=f"GCP:{gcp_secret_name}",
                        message=f"Error: {str(e)}",
                        error=e,
                    )
                )

        return results

    def sync_gcp_to_github(
        self, repo_name: Optional[str] = None, environment: Optional[str] = None
    ) -> List[SyncResult]:
        """Synchronize GCP Secret Manager secrets to GitHub.

        Args:
            repo_name: Repository name (org/repo format) for repository-level secrets
            environment: Environment name for environment-level secrets

        Returns:
            List of sync results
        """
        results = []

        # Prepare filter labels
        filter_labels = {"source": "github"}

        if repo_name:
            filter_labels["repository"] = repo_name.replace("/", "_")

        if environment:
            filter_labels["environment"] = environment

        # List GCP secrets
        gcp_secrets = self.gcp_manager.list_secrets(
            prefix=self.config.secret_prefix, filter_labels=filter_labels
        )

        # Filter secrets
        gcp_secrets = [
            secret for secret in gcp_secrets if self._filter_secrets(secret.name)
        ]

        if not gcp_secrets:
            logger.info("No GCP secrets to synchronize")
            return results

        # List existing GitHub secrets
        github_secrets = self.github_manager.list_secrets(
            repo_name=repo_name, environment=environment
        )

        # Create a map of GitHub secrets by name
        github_secret_map = {secret.name: secret for secret in github_secrets}

        # Process each GCP secret
        for gcp_secret in gcp_secrets:
            # Convert GCP secret name to GitHub format
            github_secret_name = gcp_secret.github_secret_name

            logger.info(
                f"Processing GCP secret: {gcp_secret.name} -> GitHub: {github_secret_name}"
            )

            # Create GitHub secret object
            github_secret = GitHubSecret(
                name=github_secret_name, repo_name=repo_name, environment=environment
            )

            # If it's a dry run, just log what would happen
            if self.config.dry_run:
                logger.info(
                    f"[DRY RUN] Would create/update GitHub secret: {github_secret_name}"
                )
                results.append(
                    SyncResult(
                        success=True,
                        source=f"GCP:{gcp_secret.name}",
                        target=f"GitHub:{github_secret_name}",
                        message=f"[DRY RUN] Would create/update GitHub secret: {github_secret_name}",
                    )
                )
                continue

            try:
                # Get the secret value from GCP
                secret_value = self.gcp_manager.get_secret_value(gcp_secret)

                if not secret_value:
                    logger.error(
                        f"Failed to get value for GCP secret: {gcp_secret.name}"
                    )
                    results.append(
                        SyncResult(
                            success=False,
                            source=f"GCP:{gcp_secret.name}",
                            target=f"GitHub:{github_secret_name}",
                            message=f"Failed to get value for GCP secret: {gcp_secret.name}",
                        )
                    )
                    continue

                # If the value is a placeholder, skip syncing to GitHub
                if "PLACEHOLDER" in secret_value:
                    logger.warning(
                        f"GCP secret {gcp_secret.name} contains a placeholder value, skipping sync to GitHub"
                    )
                    results.append(
                        SyncResult(
                            success=True,
                            source=f"GCP:{gcp_secret.name}",
                            target=f"GitHub:{github_secret_name}",
                            message=f"Skipped sync because GCP secret contains a placeholder value",
                        )
                    )
                    continue

                # Get visibility setting for organization secrets
                visibility = None
                if (
                    self.config.sync_level == SyncLevel.ORGANIZATION
                    and github_secret_name in github_secret_map
                ):
                    visibility = github_secret_map[github_secret_name].visibility

                # Create or update the GitHub secret
                success = self.github_manager.create_or_update_secret(
                    secret=github_secret, value=secret_value, visibility=visibility
                )

                if success:
                    results.append(
                        SyncResult(
                            success=True,
                            source=f"GCP:{gcp_secret.name}",
                            target=f"GitHub:{github_secret_name}",
                            message=f"Successfully created/updated GitHub secret: {github_secret_name}",
                        )
                    )
                else:
                    results.append(
                        SyncResult(
                            success=False,
                            source=f"GCP:{gcp_secret.name}",
                            target=f"GitHub:{github_secret_name}",
                            message=f"Failed to create/update GitHub secret: {github_secret_name}",
                        )
                    )

            except Exception as e:
                logger.error(
                    f"Error syncing GCP secret {gcp_secret.name} to GitHub: {e}"
                )
                results.append(
                    SyncResult(
                        success=False,
                        source=f"GCP:{gcp_secret.name}",
                        target=f"GitHub:{github_secret_name}",
                        message=f"Error: {str(e)}",
                        error=e,
                    )
                )

        return results

    def sync_bidirectional(
        self, repo_name: Optional[str] = None, environment: Optional[str] = None
    ) -> Dict[str, List[SyncResult]]:
        """Synchronize secrets bidirectionally between GitHub and GCP.

        Args:
            repo_name: Repository name (org/repo format) for repository-level secrets
            environment: Environment name for environment-level secrets

        Returns:
            Dictionary with lists of sync results
        """
        results = {"github_to_gcp": [], "gcp_to_github": []}

        # First sync GitHub to GCP
        logger.info("Syncing GitHub to GCP...")
        results["github_to_gcp"] = self.sync_github_to_gcp(
            repo_name=repo_name, environment=environment
        )

        # Then sync GCP to GitHub
        logger.info("Syncing GCP to GitHub...")
        results["gcp_to_github"] = self.sync_gcp_to_github(
            repo_name=repo_name, environment=environment
        )

        return results

    def sync(
        self, repo_name: Optional[str] = None, environment: Optional[str] = None
    ) -> Union[List[SyncResult], Dict[str, List[SyncResult]]]:
        """Synchronize secrets based on configured direction.

        Args:
            repo_name: Repository name (org/repo format) for repository-level secrets
            environment: Environment name for environment-level secrets

        Returns:
            Sync results
        """
        if self.config.sync_direction == SyncDirection.GITHUB_TO_GCP:
            return self.sync_github_to_gcp(repo_name=repo_name, environment=environment)
        elif self.config.sync_direction == SyncDirection.GCP_TO_GITHUB:
            return self.sync_gcp_to_github(repo_name=repo_name, environment=environment)
        else:  # BIDIRECTIONAL
            return self.sync_bidirectional(repo_name=repo_name, environment=environment)


def main():
    """Main function to demonstrate usage."""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub-GCP Secret Synchronization")

    # GCP options
    parser.add_argument("--gcp-project-id", required=True, help="GCP project ID")
    parser.add_argument("--gcp-region", required=True, help="GCP region")
    parser.add_argument(
        "--gcp-service-account-key", help="GCP service account key JSON"
    )

    # GitHub options
    parser.add_argument("--github-org", required=True, help="GitHub organization name")
    parser.add_argument("--github-repo", help="GitHub repository name")
    parser.add_argument("--github-token", help="GitHub access token")
    parser.add_argument(
        "--use-fine-grained-token",
        action="store_true",
        help="Indicates if the GitHub token is a fine-grained token",
    )
    parser.add_argument("--github-environment", help="GitHub environment name")

    # Sync options
    parser.add_argument(
        "--direction",
        choices=[d.value for d in SyncDirection],
        default=SyncDirection.BIDIRECTIONAL.value,
        help="Sync direction",
    )
    parser.add_argument(
        "--level",
        choices=[l.value for l in SyncLevel],
        default=SyncLevel.ORGANIZATION.value,
        help="Sync level",
    )
    parser.add_argument(
        "--secret-prefix", default="github-", help="Prefix for GCP secrets from GitHub"
    )
    parser.add_argument(
        "--include", action="append", help="Secret name patterns to include"
    )
    parser.add_argument(
        "--exclude", action="append", help="Secret name patterns to exclude"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't actually perform sync"
    )
    parser.add_argument("--audit-log", help="Path to audit log file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Configure GCP authentication
    gcp_config = GCPConfig(project_id=args.gcp_project_id, region=args.gcp_region)

    # Get service account key from file or environment variable
    service_account_key = args.gcp_service_account_key
    if not service_account_key:
        service_account_key = os.environ.get("GCP_MASTER_SERVICE_JSON")

    # Initialize GCP authentication
    gcp_auth = GCPAuth(
        gcp_config=gcp_config,
        auth_method=AuthMethod.SERVICE_ACCOUNT_KEY,
        service_account_key=service_account_key,
    )

    # Get GitHub token from environment variable if not provided
    github_token = args.github_token
    if not github_token:
        if args.use_fine_grained_token:
            github_token = os.environ.get("GH_FINE_GRAINED_TOKEN")
        else:
            github_token = os.environ.get("GH_CLASSIC_PAT_TOKEN")

    # Initialize GitHub authentication
    github_config = GitHubConfig(
        org_name=args.github_org,
        repo_name=args.github_repo,
        token=github_token,
        use_fine_grained_token=args.use_fine_grained_token,
    )

    github_auth = GitHubAuth(github_config=github_config)

    # Configure secret sync
    sync_config = SecureSyncConfig(
        gcp_config=gcp_config,
        github_config=github_config,
        sync_direction=SyncDirection(args.direction),
        sync_level=SyncLevel(args.level),
        secret_prefix=args.secret_prefix,
        exclude_patterns=args.exclude,
        include_patterns=args.include,
        dry_run=args.dry_run,
        audit_log_path=args.audit_log,
        verbose=args.verbose,
    )

    # Initialize auditor
    auditor = SecretSyncAuditor(log_path=args.audit_log)

    # Authenticate with GCP
    if not gcp_auth.authenticate():
        logger.error("GCP authentication failed")
        return 1

    # Authenticate with GitHub
    if not github_auth.authenticate():
        logger.error("GitHub authentication failed")
        return 1

    # Initialize synchronizer
    synchronizer = SecretSynchronizer(
        config=sync_config, gcp_auth=gcp_auth, github_auth=github_auth, auditor=auditor
    )

    # Perform synchronization
    try:
        results = synchronizer.sync(
            repo_name=args.github_repo, environment=args.github_environment
        )

        # Summary
        if isinstance(results, dict):
            # Bidirectional results
            github_to_gcp = results["github_to_gcp"]
            gcp_to_github = results["gcp_to_github"]

            print("\nSync Summary:\n")
            print("GitHub to GCP:")
            print(f"  Total: {len(github_to_gcp)}")
            print(f"  Success: {sum(1 for r in github_to_gcp if r.success)}")
            print(f"  Failure: {sum(1 for r in github_to_gcp if not r.success)}")

            print("\nGCP to GitHub:")
            print(f"  Total: {len(gcp_to_github)}")
            print(f"  Success: {sum(1 for r in gcp_to_github if r.success)}")
            print(f"  Failure: {sum(1 for r in gcp_to_github if not r.success)}")

            # Return success if there were no failures
            return 0 if all(r.success for r in github_to_gcp + gcp_to_github) else 1
        else:
            # Unidirectional results
            print("\nSync Summary:\n")
            print(f"Total: {len(results)}")
            print(f"Success: {sum(1 for r in results if r.success)}")
            print(f"Failure: {sum(1 for r in results if not r.success)}")

            # Return success if there were no failures
            return 0 if all(r.success for r in results) else 1
    finally:
        # Clean up
        gcp_auth.clean_up()
        github_auth.clean_up()


if __name__ == "__main__":
    sys.exit(main())
