"""
Domain interfaces for the GCP Migration toolkit.

This module defines the abstract interfaces and protocols that other components
of the system must implement. Following the Dependency Inversion Principle,
high-level modules depend on these abstractions rather than concrete implementations.
"""

import abc
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from gcp_migration.domain.models import (
    BenchmarkResult,
    ComputeResource,
    MigrationOperation,
    MigrationPlan,
    NetworkConfig,
    RepositoryInfo,
    Secret,
    WorkstationConfig,
)


@runtime_checkable
class IRepository(Protocol):
    """Base repository interface for data access."""
    
    async def get(self, id: str) -> Any:
        """
        Retrieve an entity by its ID.
        
        Args:
            id: The entity identifier
            
        Returns:
            The retrieved entity
            
        Raises:
            ResourceNotFoundError: If the entity doesn't exist
        """
        ...
    
    async def list(self) -> List[Any]:
        """
        List all entities.
        
        Returns:
            List of all entities
        """
        ...
    
    async def create(self, entity: Any) -> Any:
        """
        Create a new entity.
        
        Args:
            entity: The entity to create
            
        Returns:
            The created entity with any server-generated fields populated
            
        Raises:
            ValidationError: If the entity is invalid
        """
        ...
    
    async def update(self, entity: Any) -> Any:
        """
        Update an existing entity.
        
        Args:
            entity: The entity to update
            
        Returns:
            The updated entity
            
        Raises:
            ResourceNotFoundError: If the entity doesn't exist
            ValidationError: If the entity is invalid
        """
        ...
    
    async def delete(self, id: str) -> None:
        """
        Delete an entity by its ID.
        
        Args:
            id: The entity identifier
            
        Raises:
            ResourceNotFoundError: If the entity doesn't exist
        """
        ...


class IMigrationPlanRepository(IRepository, abc.ABC):
    """Repository for migration plans."""
    
    @abc.abstractmethod
    async def get_by_name(self, name: str) -> MigrationPlan:
        """
        Retrieve a migration plan by its name.
        
        Args:
            name: The name of the migration plan
            
        Returns:
            The migration plan
            
        Raises:
            ResourceNotFoundError: If the plan doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def update_operation(self, plan_id: str, operation: MigrationOperation) -> MigrationOperation:
        """
        Update an operation within a migration plan.
        
        Args:
            plan_id: The ID of the migration plan
            operation: The operation to update
            
        Returns:
            The updated operation
            
        Raises:
            ResourceNotFoundError: If the plan or operation doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def get_active_plans(self) -> List[MigrationPlan]:
        """
        Get all active migration plans (not completed or failed).
        
        Returns:
            List of active migration plans
        """
        pass
    
    @abc.abstractmethod
    async def save_benchmark(self, plan_id: str, benchmark: BenchmarkResult) -> None:
        """
        Save benchmark results for a migration plan.
        
        Args:
            plan_id: The ID of the migration plan
            benchmark: The benchmark results to save
            
        Raises:
            ResourceNotFoundError: If the plan doesn't exist
        """
        pass


class IBenchmarkService(abc.ABC):
    """Service for benchmarking environments."""
    
    @abc.abstractmethod
    async def benchmark_github_codespaces(self) -> BenchmarkResult:
        """
        Benchmark the GitHub Codespaces environment.
        
        Returns:
            The benchmark results for GitHub Codespaces
            
        Raises:
            BenchmarkError: If benchmarking fails
        """
        pass
    
    @abc.abstractmethod
    async def benchmark_gcp_workstation(self, workstation_name: str) -> BenchmarkResult:
        """
        Benchmark a GCP Workstation environment.
        
        Args:
            workstation_name: The name of the GCP Workstation
            
        Returns:
            The benchmark results for the GCP Workstation
            
        Raises:
            BenchmarkError: If benchmarking fails
            ResourceNotFoundError: If the workstation doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def compare_environments(
        self, github_benchmark: BenchmarkResult, gcp_benchmark: BenchmarkResult
    ) -> Dict[str, float]:
        """
        Compare benchmark results between GitHub Codespaces and GCP Workstations.
        
        Args:
            github_benchmark: Benchmark results for GitHub Codespaces
            gcp_benchmark: Benchmark results for GCP Workstations
            
        Returns:
            Dictionary mapping metric names to improvement ratios
        """
        pass


class ITerraformService(abc.ABC):
    """Service for deploying infrastructure with Terraform."""
    
    @abc.abstractmethod
    async def generate_terraform_config(
        self,
        project_id: str,
        network_config: NetworkConfig,
        workstation_configs: List[WorkstationConfig],
    ) -> Dict[str, Any]:
        """
        Generate Terraform configuration for GCP Workstations.
        
        Args:
            project_id: The GCP project ID
            network_config: Network configuration
            workstation_configs: List of workstation configurations
            
        Returns:
            Dictionary containing generated Terraform configuration files
            
        Raises:
            ValidationError: If the configuration is invalid
        """
        pass
    
    @abc.abstractmethod
    async def apply_terraform(
        self, 
        config_path: str, 
        variables: Dict[str, Any], 
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Apply Terraform configuration.
        
        Args:
            config_path: Path to the Terraform configuration directory
            variables: Variables to pass to Terraform
            auto_approve: Whether to automatically approve changes
            
        Returns:
            Dictionary containing Terraform outputs
            
        Raises:
            TerraformError: If Terraform fails
        """
        pass
    
    @abc.abstractmethod
    async def destroy_terraform(
        self, 
        config_path: str, 
        variables: Dict[str, Any], 
        auto_approve: bool = False
    ) -> None:
        """
        Destroy Terraform-managed infrastructure.
        
        Args:
            config_path: Path to the Terraform configuration directory
            variables: Variables to pass to Terraform
            auto_approve: Whether to automatically approve destruction
            
        Raises:
            TerraformError: If Terraform fails
        """
        pass


class ISecretService(abc.ABC):
    """Service for managing secrets."""
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    async def create_gcp_secret(self, project_id: str, secret: Secret) -> Secret:
        """
        Create a GCP Secret Manager secret.
        
        Args:
            project_id: The GCP project ID
            secret: The secret to create
            
        Returns:
            The created secret
            
        Raises:
            SecretError: If creating the secret fails
        """
        pass
    
    @abc.abstractmethod
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
        pass


class IDockerService(abc.ABC):
    """Service for building and managing Docker images."""
    
    @abc.abstractmethod
    async def build_image(
        self, dockerfile_path: str, tag: str, build_args: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build a Docker image.
        
        Args:
            dockerfile_path: Path to the Dockerfile
            tag: Tag for the image
            build_args: Build arguments
            
        Returns:
            The image ID
            
        Raises:
            DockerError: If building the image fails
        """
        pass
    
    @abc.abstractmethod
    async def push_image(self, tag: str, registry: str) -> str:
        """
        Push a Docker image to a registry.
        
        Args:
            tag: Tag of the image to push
            registry: Registry URL
            
        Returns:
            The full image reference
            
        Raises:
            DockerError: If pushing the image fails
        """
        pass
    
    @abc.abstractmethod
    async def generate_dockerfile(
        self, 
        base_image: str, 
        packages: List[str], 
        env_vars: Dict[str, str],
        startup_script: str,
    ) -> str:
        """
        Generate a Dockerfile.
        
        Args:
            base_image: Base image to use
            packages: Packages to install
            env_vars: Environment variables to set
            startup_script: Content of the startup script
            
        Returns:
            The generated Dockerfile content
        """
        pass


class IGitHubService(abc.ABC):
    """Service for interacting with GitHub."""
    
    @abc.abstractmethod
    async def get_repository_info(self, repository_name: str) -> RepositoryInfo:
        """
        Get information about a GitHub repository.
        
        Args:
            repository_name: The name of the GitHub repository
            
        Returns:
            Information about the repository
            
        Raises:
            ResourceNotFoundError: If the repository doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def get_codespace_config(self, repository_name: str) -> Dict[str, Any]:
        """
        Get the GitHub Codespaces configuration for a repository.
        
        Args:
            repository_name: The name of the GitHub repository
            
        Returns:
            The Codespaces configuration
            
        Raises:
            ResourceNotFoundError: If the repository or configuration doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def get_extensions(self, repository_name: str) -> List[str]:
        """
        Get VS Code extensions from GitHub Codespaces configuration.
        
        Args:
            repository_name: The name of the GitHub repository
            
        Returns:
            List of extension IDs
            
        Raises:
            ResourceNotFoundError: If the repository or configuration doesn't exist
        """
        pass


class IGCPService(abc.ABC):
    """Service for interacting with Google Cloud Platform."""
    
    @abc.abstractmethod
    async def get_workstation_info(self, project_id: str, workstation_name: str) -> Dict[str, Any]:
        """
        Get information about a GCP Workstation.
        
        Args:
            project_id: The GCP project ID
            workstation_name: The name of the GCP Workstation
            
        Returns:
            Information about the workstation
            
        Raises:
            ResourceNotFoundError: If the workstation doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def create_workstation(
        self, project_id: str, config: WorkstationConfig
    ) -> Dict[str, Any]:
        """
        Create a GCP Workstation.
        
        Args:
            project_id: The GCP project ID
            config: The workstation configuration
            
        Returns:
            Information about the created workstation
            
        Raises:
            ValidationError: If the configuration is invalid
            InfrastructureError: If creating the workstation fails
        """
        pass
    
    @abc.abstractmethod
    async def delete_workstation(self, project_id: str, workstation_name: str) -> None:
        """
        Delete a GCP Workstation.
        
        Args:
            project_id: The GCP project ID
            workstation_name: The name of the GCP Workstation
            
        Raises:
            ResourceNotFoundError: If the workstation doesn't exist
            InfrastructureError: If deleting the workstation fails
        """
        pass
    
    @abc.abstractmethod
    async def start_workstation(self, project_id: str, workstation_name: str) -> Dict[str, Any]:
        """
        Start a GCP Workstation.
        
        Args:
            project_id: The GCP project ID
            workstation_name: The name of the GCP Workstation
            
        Returns:
            Information about the started workstation
            
        Raises:
            ResourceNotFoundError: If the workstation doesn't exist
            InfrastructureError: If starting the workstation fails
        """
        pass
    
    @abc.abstractmethod
    async def stop_workstation(self, project_id: str, workstation_name: str) -> None:
        """
        Stop a GCP Workstation.
        
        Args:
            project_id: The GCP project ID
            workstation_name: The name of the GCP Workstation
            
        Raises:
            ResourceNotFoundError: If the workstation doesn't exist
            InfrastructureError: If stopping the workstation fails
        """
        pass


class IMigrationService(abc.ABC):
    """Orchestrates the migration process."""
    
    @abc.abstractmethod
    async def create_migration_plan(
        self,
        name: str,
        repository_names: List[str],
        project_id: str,
        compute_resources: List[ComputeResource],
    ) -> MigrationPlan:
        """
        Create a new migration plan.
        
        Args:
            name: The name of the migration plan
            repository_names: Names of GitHub repositories to migrate
            project_id: The GCP project ID
            compute_resources: List of compute resources for workstations
            
        Returns:
            The created migration plan
            
        Raises:
            ValidationError: If the parameters are invalid
        """
        pass
    
    @abc.abstractmethod
    async def execute_migration_plan(self, plan_id: str) -> MigrationPlan:
        """
        Execute a migration plan.
        
        Args:
            plan_id: The ID of the migration plan
            
        Returns:
            The updated migration plan with operation results
            
        Raises:
            ResourceNotFoundError: If the plan doesn't exist
            MigrationError: If migration fails
        """
        pass
    
    @abc.abstractmethod
    async def get_migration_status(self, plan_id: str) -> Dict[str, Any]:
        """
        Get the status of a migration plan.
        
        Args:
            plan_id: The ID of the migration plan
            
        Returns:
            Dictionary with status information
            
        Raises:
            ResourceNotFoundError: If the plan doesn't exist
        """
        pass
    
    @abc.abstractmethod
    async def rollback_migration(self, plan_id: str) -> MigrationPlan:
        """
        Rollback a migration plan.
        
        Args:
            plan_id: The ID of the migration plan
            
        Returns:
            The updated migration plan after rollback
            
        Raises:
            ResourceNotFoundError: If the plan doesn't exist
            MigrationError: If rollback fails
        """
        pass


class IValidationService(abc.ABC):
    """Service for validating migrations."""
    
    @abc.abstractmethod
    async def validate_workstation(
        self, project_id: str, workstation_name: str
    ) -> Dict[str, Any]:
        """
        Validate a GCP Workstation.
        
        Args:
            project_id: The GCP project ID
            workstation_name: The name of the GCP Workstation
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ResourceNotFoundError: If the workstation doesn't exist
            ValidationError: If validation fails
        """
        pass
    
    @abc.abstractmethod
    async def validate_terraform_config(self, config_path: str) -> Dict[str, Any]:
        """
        Validate Terraform configuration.
        
        Args:
            config_path: Path to the Terraform configuration directory
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    @abc.abstractmethod
    async def validate_docker_image(self, image_tag: str) -> Dict[str, Any]:
        """
        Validate a Docker image.
        
        Args:
            image_tag: Tag of the image to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    @abc.abstractmethod
    async def validate_migration_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Validate a migration plan.
        
        Args:
            plan_id: The ID of the migration plan
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ResourceNotFoundError: If the plan doesn't exist
            ValidationError: If validation fails
        """
        pass