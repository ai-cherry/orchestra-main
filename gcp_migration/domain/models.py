"""
Domain models for GCP migration toolkit.

This module defines the core data structures used throughout the migration toolkit,
including representations of GCP resources, migration state, and configuration.
"""

from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, validator


class MigrationType(Enum):
    """Types of migrations supported by the toolkit."""

    GITHUB_TO_GCP = auto()
    LOCAL_TO_GCP = auto()
    GCP_TO_GCP = auto()
    OTHER = auto()


class ResourceType(Enum):
    """Types of resources that can be migrated."""

    SECRET = auto()
    REPOSITORY = auto()
    FILE = auto()
    CONFIGURATION = auto()
    SERVICE_ACCOUNT = auto()
    WORKSTATION = auto()
    CONTAINER_IMAGE = auto()
    FUNCTION = auto()
    SERVICE = auto()
    OTHER = auto()


class MigrationStatus(Enum):
    """Status of a migration operation."""

    NOT_STARTED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    PARTIALLY_COMPLETED = auto()
    ROLLED_BACK = auto()


class Secret(BaseModel):
    """
    Represents a secret managed by Secret Manager.

    This model encapsulates a secret value along with its metadata,
    which can be used for migration between environments.
    """

    id: str
    name: str
    value: Optional[str] = None
    version: Optional[str] = "latest"
    labels: Dict[str, str] = Field(default_factory=dict)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""

        frozen = True  # Make the secret immutable for security


class StorageItem(BaseModel):
    """
    Represents an item in Cloud Storage.

    This model encapsulates information about a storage object,
    such as its location, size, and metadata.
    """

    bucket: str
    name: str
    path: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    md5_hash: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_full_path(self) -> str:
        """
        Get the full GCS path to this item.

        Returns:
            Full GCS path in the format "gs://{bucket}/{name}"
        """
        return f"gs://{self.bucket}/{self.name}"

    @validator("path", pre=True, always=True)
    def set_path_from_name(cls, v, values):
        """Set the path if not provided based on the name."""
        if v is None and "name" in values:
            return values["name"]
        return v


class MigrationResource(BaseModel):
    """
    Represents a resource being migrated.

    This model provides a unified representation of any resource
    that can be migrated between environments.
    """

    id: str
    name: str
    type: ResourceType
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    status: MigrationStatus = MigrationStatus.NOT_STARTED
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    @property
    def is_completed(self) -> bool:
        """Check if the resource migration is completed."""
        return self.status == MigrationStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the resource migration failed."""
        return self.status == MigrationStatus.FAILED


class MigrationContext(BaseModel):
    """
    Context for a migration operation.

    This model provides context and configuration for migrations,
    including source and destination information, credentials, and options.
    """

    migration_id: str
    migration_type: MigrationType
    source: Dict[str, Any]
    destination: Dict[str, Any]
    resources: List[MigrationResource] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)
    status: MigrationStatus = MigrationStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True

    @property
    def duration(self) -> Optional[float]:
        """
        Calculate the duration of the migration in seconds.

        Returns:
            Duration in seconds or None if not completed
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def resource_by_id(self, resource_id: str) -> Optional[MigrationResource]:
        """
        Find a resource by its ID.

        Args:
            resource_id: ID of the resource to find

        Returns:
            The resource or None if not found
        """
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        return None


class GithubConfig(BaseModel):
    """
    Configuration for GitHub as a migration source.

    This model provides configuration for accessing GitHub repositories
    and resources for migration to GCP.
    """

    organization: Optional[str] = None
    repository: str
    branch: str = "main"
    access_token: Optional[str] = None
    use_oauth: bool = False
    clone_depth: int = 1
    include_lfs: bool = False
    include_submodules: bool = False
    ssh_key_path: Optional[str] = None

    @validator("repository")
    def validate_repository(cls, v):
        """Validate the repository name."""
        if "/" in v and not cls.organization:
            # Extract organization from the repository name (org/repo format)
            return v.split("/")[-1]
        return v


class GCPConfig(BaseModel):
    """
    Configuration for Google Cloud Platform.

    This model provides configuration for accessing GCP resources
    as either a migration source or destination.
    """

    project_id: str
    location: str = "us-central1"
    credentials_path: Optional[str] = None
    use_application_default: bool = True
    workstation_cluster: Optional[str] = None
    workstation_config: Optional[str] = None
    storage_bucket: Optional[str] = None
    network: Optional[str] = None
    subnet: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)

    @property
    def has_explicit_credentials(self) -> bool:
        """Check if explicit credentials are provided."""
        return self.credentials_path is not None and not self.use_application_default


class MigrationPlan(BaseModel):
    """
    Plan for a migration operation.

    This model defines a plan for migrating resources from
    one environment to another, including validation steps.
    """

    plan_id: str
    description: Optional[str] = None
    context: MigrationContext
    validation_steps: List[str] = Field(default_factory=list)
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    rollback_steps: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def resource_count(self) -> int:
        """Get the number of resources in the migration plan."""
        return len(self.context.resources)


class MigrationResult(BaseModel):
    """
    Result of a migration operation.

    This model captures the result of executing a migration plan,
    including success/failure information and metrics.
    """

    plan_id: str
    context: MigrationContext
    success: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    start_time: datetime
    end_time: datetime

    @property
    def duration_seconds(self) -> float:
        """Get the duration of the migration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def error_count(self) -> int:
        """Get the number of errors encountered during migration."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get the number of warnings encountered during migration."""
        return len(self.warnings)

    @property
    def succeeded_resources(self) -> List[MigrationResource]:
        """Get the list of successfully migrated resources."""
        return [r for r in self.context.resources if r.is_completed]

    @property
    def failed_resources(self) -> List[MigrationResource]:
        """Get the list of resources that failed to migrate."""
        return [r for r in self.context.resources if r.is_failed]


class ValidationResult(BaseModel):
    """
    Result of a validation operation.

    This model captures the result of validating a migration plan
    or checking prerequisites for migration.
    """

    valid: bool
    checks: List[Dict[str, Any]]
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Get the number of validation errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get the number of validation warnings."""
        return len(self.warnings)

    @property
    def success_count(self) -> int:
        """Get the number of successful validation checks."""
        return sum(1 for check in self.checks if check.get("result") is True)
