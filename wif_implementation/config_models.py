"""
Configuration models for Workload Identity Federation implementation.

This module defines Pydantic models for type-safe configuration
of the WIF implementation.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Callable, Any

from pydantic import BaseModel, Field, validator


class AuthMethod(str, Enum):
    """Authentication methods for GCP."""

    WIF = "workload_identity_federation"
    SERVICE_ACCOUNT_KEY = "service_account_key"
    DEFAULT_SA = "default_service_account"
    UNKNOWN = "unknown"


class GCPProjectConfig(BaseModel):
    """GCP project configuration."""

    project_id: str = Field(..., description="GCP project ID")
    project_number: Optional[str] = Field(None, description="GCP project number")
    region: str = Field("us-central1", description="Default GCP region")

    @validator("project_id")
    def validate_project_id(cls, v: str) -> str:
        """Validate project ID format."""
        if not v or not v.strip():
            raise ValueError("Project ID cannot be empty")
        return v


class WorkloadIdentityConfig(BaseModel):
    """Workload Identity Federation configuration."""

    pool_id: str = Field("github-pool", description="WIF pool ID")
    provider_id: str = Field("github-provider", description="WIF provider ID")
    service_account_id: str = Field(
        "github-actions-sa", description="Service account ID for WIF"
    )
    attribute_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "google.subject": "assertion.sub",
            "attribute.actor": "assertion.actor",
            "attribute.repository": "assertion.repository",
        },
        description="Attribute mapping for the WIF provider",
    )

    def get_provider_resource_name(self, project_config: "GCPProjectConfig") -> str:
        """
        Get the full resource name for the Workload Identity Provider.

        Args:
            project_config: GCP project configuration

        Returns:
            Full resource name for the Workload Identity Provider
        """
        project_id = project_config.project_number or project_config.project_id
        return (
            f"projects/{project_id}/locations/global/workloadIdentityPools/"
            f"{self.pool_id}/providers/{self.provider_id}"
        )

    def get_service_account_email(self, project_config: "GCPProjectConfig") -> str:
        """
        Get the service account email.

        Args:
            project_config: GCP project configuration

        Returns:
            Service account email
        """
        return f"{self.service_account_id}@{project_config.project_id}.iam.gserviceaccount.com"


class RepositoryConfig(BaseModel):
    """GitHub repository configuration."""

    owner: str = Field(
        ..., description="GitHub repository owner (user or organization)"
    )
    name: str = Field(..., description="GitHub repository name")

    @property
    def full_name(self) -> str:
        """Get the full repository name (owner/name)."""
        return f"{self.owner}/{self.name}"


class GitHubConfig(BaseModel):
    """GitHub configuration."""

    repositories: List[RepositoryConfig] = Field(
        default_factory=list, description="GitHub repositories"
    )
    token: Optional[str] = Field(None, description="GitHub token for API access")

    def repository_conditions(self) -> str:
        """
        Generate the attribute.repository condition for WIF provider.

        Returns:
            Attribute condition string for repository matching
        """
        if not self.repositories:
            return "assertion.repository.startsWith('REPO_OWNER/')"

        conditions = [
            f"assertion.repository=='{repo.full_name}'" for repo in self.repositories
        ]
        return " || ".join(conditions)


# Factory functions for default model instances
def create_default_workload_identity() -> WorkloadIdentityConfig:
    """Create a default WorkloadIdentityConfig instance."""
    # All parameters have defaults in the class definition
    # but we need to provide them explicitly to avoid linter errors
    return WorkloadIdentityConfig(
        pool_id="github-pool",
        provider_id="github-provider",
        service_account_id="github-actions-sa",
    )


def create_default_github_config() -> GitHubConfig:
    """Create a default GitHubConfig instance."""
    # repositories defaults to an empty list
    # token defaults to None
    return GitHubConfig(
        repositories=[],
        token=None,
    )


class WIFImplementationConfig(BaseModel):
    """Main configuration for WIF implementation."""

    gcp: GCPProjectConfig
    workload_identity: WorkloadIdentityConfig = Field(
        default_factory=create_default_workload_identity,
        description="WIF configuration",
    )
    github: GitHubConfig = Field(
        default_factory=create_default_github_config, description="GitHub configuration"
    )
    template_dir: Optional[Path] = Field(
        None, description="Directory containing templates"
    )
    output_dir: Path = Field(
        default_factory=lambda: Path("wif_output"),
        description="Directory for output files",
    )
    debug: bool = Field(False, description="Enable debug mode")
