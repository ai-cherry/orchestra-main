"""
Secret Manager Service Implementation for GCP Migration.

This module provides specialized Secret Manager functionality for migrating
secrets from GitHub to GCP Secret Manager, with additional features for
validation, encryption, and secret organization.
"""

import base64
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

from gcp_migration.domain.exceptions import (
    ResourceNotFoundError,
    SecretError,
    ValidationError,
)
from gcp_migration.domain.interfaces import ISecretService
from gcp_migration.domain.models import Secret
from gcp_migration.infrastructure.extended_gcp_service import ExtendedGCPService

# Configure logging
logger = logging.getLogger(__name__)


class SecretManagerService(ISecretService):
    """
    Service for managing secrets with enhanced functionality for migration.
    Implements the ISecretService interface and leverages ExtendedGCPService.
    """

    def __init__(self, gcp_service: Optional[ExtendedGCPService] = None):
        """
        Initialize the Secret Manager service.

        Args:
            gcp_service: Optional ExtendedGCPService instance (will create one if None)
        """
        self.gcp_service = gcp_service or ExtendedGCPService()
        # Prefix used for organizing migrated GitHub secrets in GCP
        self.github_secret_prefix = "github_"
        # Set of sensitive keywords to identify when sanitizing secret names
        self.sensitive_keywords = {
            "password", "token", "key", "secret", "credential", "auth",
            "private", "certificate", "access", "api"
        }

    async def list_github_secrets(self, repository_name: str) -> List[str]:
        """
        List GitHub secrets for a repository.

        Args:
            repository_name: The name of the GitHub repository

        Returns:
            List of secret names

        Raises:
            SecretError: If listing secrets fails
        """
        # Note: This would be implemented using GitHub API
        # For now, we'll throw an error as this requires GitHub API integration
        raise SecretError(
            message="Direct GitHub secret listing is not implemented. "
            "Please provide secrets explicitly for migration."
        )

    async def get_github_secret(self, repository_name: str, secret_name: str) -> Secret:
        """
        Get a GitHub secret.

        Args:
            repository_name: The name of the GitHub repository
            secret_name: The name of the secret

        Returns:
            The secret

        Raises:
            SecretError: If getting the secret fails
            ResourceNotFoundError: If the secret doesn't exist
        """
        # Note: This would be implemented using GitHub API
        # For now, we'll throw an error as this requires GitHub API integration
        raise SecretError(
            message="Direct GitHub secret access is not implemented. "
            "Please provide secrets explicitly for migration."
        )

    async def create_gcp_secret(self, project_id: str, secret: Secret) -> Secret:
        """
        Create a GCP Secret Manager secret.

        Args:
            project_id: The GCP project ID
            secret: The secret to create

        Returns:
            The created secret with updated metadata

        Raises:
            SecretError: If creating the secret fails
            ValidationError: If the secret is invalid
        """
        # Validate secret
        if not secret.name:
            raise ValidationError(message="Secret name is required")
        if secret.value is None:
            raise ValidationError(message="Secret value is required")

        # Additional validation for secret name format
        if not self._is_valid_secret_name(secret.name):
            raise ValidationError(
                message=f"Invalid secret name format: {secret.name}. "
                "Secret names must only contain letters, numbers, dashes, and underscores."
            )

        try:
            # Store the secret
            secret_id = self._sanitize_secret_name(secret.name)
            version_name = self.gcp_service.store_secret(secret_id, secret.value)

            # Update secret metadata
            secret.target = "gcp"
            secret.target_project = project_id
            secret.migrated = True
            secret.migrated_at = datetime.now()

            # Extract version from the version name
            # Format: projects/{project}/secrets/{secret}/versions/{version}
            if version_name:
                version = version_name.split("/")[-1]
                if secret.versions is None:
                    secret.versions = [version]
                else:
                    secret.versions.append(version)

            logger.info(f"Created GCP secret: {secret_id}")
            return secret
        except Exception as e:
            error_message = f"Failed to create GCP secret '{secret.name}': {str(e)}"
            logger.error(error_message, exc_info=True)
            raise SecretError(
                message=error_message,
                cause=e
            )

    async def migrate_secret(
        self, repository_name: str, secret_name: str, project_id: str
    ) -> Secret:
        """
        Migrate a secret from GitHub to GCP Secret Manager.

        Args:
            repository_name: The name of the GitHub repository
            secret_name: The name of the secret
            project_id: The GCP project ID

        Returns:
            The migrated secret

        Raises:
            SecretError: If migrating the secret fails
        """
        try:
            # Get GitHub secret
            # Since direct GitHub API access is not implemented,
            # this would throw a SecretError
            try:
                secret = await self.get_github_secret(repository_name, secret_name)
            except SecretError as e:
                # Instead of failing, create a placeholder secret
                # In a real implementation, this would come from GitHub
                logger.warning(
                    f"Direct GitHub secret access not available. "
                    f"Please provide the value for {secret_name} manually."
                )
                return Secret(
                    name=secret_name,
                    source="github",
                    source_repository=repository_name,
                    migrated=False
                )

            # Create GCP secret
            secret = await self.create_gcp_secret(project_id, secret)

            return secret
        except Exception as e:
            raise SecretError(
                message=f"Failed to migrate secret {secret_name}: {str(e)}",
                cause=e
            )

    async def batch_migrate_secrets(
        self, github_secrets: Dict[str, str], project_id: str,
        add_prefix: bool = True
    ) -> List[Secret]:
        """
        Migrate multiple GitHub secrets to GCP Secret Manager in a batch.

        Args:
            github_secrets: Dictionary of secret names and values
            project_id: The GCP project ID
            add_prefix: Whether to add a prefix to the secret names

        Returns:
            List of migrated secrets

        Raises:
            SecretError: If migrating secrets fails
        """
        migrated_secrets = []

        for secret_name, secret_value in github_secrets.items():
            try:
                # Prepare secret
                gcp_secret_name = f"{self.github_secret_prefix}{secret_name}" if add_prefix else secret_name
                secret = Secret(
                    name=gcp_secret_name,
                    value=secret_value,
                    source="github",
                    target="gcp",
                    target_project=project_id
                )

                # Create GCP secret
                migrated_secret = await self.create_gcp_secret(project_id, secret)
                migrated_secrets.append(migrated_secret)

                logger.info(f"Migrated secret: {secret_name} -> {gcp_secret_name}")
            except Exception as e:
                logger.error(f"Failed to migrate secret {secret_name}: {e}")

        return migrated_secrets

    async def validate_secret_migration(
        self, migrated_secrets: List[Secret], project_id: str
    ) -> Dict[str, Any]:
        """
        Validate that secrets were correctly migrated to GCP.

        Args:
            migrated_secrets: List of secrets that were migrated
            project_id: The GCP project ID

        Returns:
            Dictionary with validation results

        Raises:
            SecretError: If validation fails
        """
        results = {
            "total": len(migrated_secrets),
            "success": 0,
            "failed": 0,
            "failures": []
        }

        for secret in migrated_secrets:
            try:
                # Get secret value from GCP
                gcp_value = self.gcp_service.access_secret(secret.name)

                # Compare with original value if available
                if secret.value and gcp_value != secret.value:
                    results["failed"] += 1
                    results["failures"].append({
                        "name": secret.name,
                        "reason": "Value mismatch"
                    })
                else:
                    results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "name": secret.name,
                    "reason": str(e)
                })

        return results

    def _sanitize_secret_name(self, name: str) -> str:
        """
        Sanitize a secret name to ensure it follows GCP Secret Manager naming rules.

        Args:
            name: Original secret name

        Returns:
            Sanitized secret name
        """
        # Replace invalid characters with underscores
        sanitized = ""
        for char in name:
            if char.isalnum() or char == '_' or char == '-':
                sanitized += char
            else:
                sanitized += '_'

        # Ensure name starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
            sanitized = f"s_{sanitized}"

        # Ensure name is not empty
        if not sanitized:
            sanitized = "secret"

        return sanitized

    def organize_secrets_by_sensitivity(
        self, secrets: List[Secret]
    ) -> Dict[str, List[Secret]]:
        """
        Organize secrets by sensitivity level based on their names.

        Args:
            secrets: List of secrets

        Returns:
            Dictionary mapping sensitivity level to list of secrets
        """
        organized = {
            "high": [],
            "medium": [],
            "low": []
        }

        for secret in secrets:
            name_lower = secret.name.lower()

            # Check for high sensitivity keywords
            if any(keyword in name_lower for keyword in self.sensitive_keywords):
                organized["high"].append(secret)
            # Placeholder logic for medium sensitivity
            elif len(secret.value or "") > 20:
                organized["medium"].append(secret)
            else:
                organized["low"].append(secret)

        return organized

    def _is_valid_secret_name(self, name: str) -> bool:
        """
        Check if a secret name follows GCP Secret Manager naming rules.

        Args:
            name: Secret name to validate

        Returns:
            True if the name is valid, False otherwise
        """
        if not name:
            return False

        # Secret names must consist of only lowercase letters, numbers, dashes, and underscores
        for char in name:
            if not (char.isalnum() or char == '_' or char == '-'):
                return False

        # Secret names must start with a letter or underscore
        if not (name[0].isalpha() or name[0] == '_'):
            return False

        return True
