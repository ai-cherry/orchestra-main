"""
Migration service for orchestrating migration operations.

This module provides the main service for executing migrations, handling
configuration, and providing a high-level API for the migration toolkit.
"""

import asyncio
import datetime
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from ..domain.exceptions_fixed import (
    ConfigurationError, MigrationError, MigrationExecutionError, 
    ValidationError
)
from ..domain.models import (
    GCPConfig, GithubConfig, MigrationContext, MigrationPlan, 
    MigrationResource, MigrationResult, MigrationStatus,
    MigrationType, ResourceType, ValidationResult
)
from ..infrastructure.gcp_service import (
    SecretManagerService, StorageService, FirestoreService
)
from .workflow import (
    MigrationWorkflow, ResourceMigrationStep, StepStatus, ValidationResult,
    ValidateMigrationPlan, WorkflowStep
)

# Configure logging
logger = logging.getLogger(__name__)


class MigrationOptions(BaseModel):
    """
    Options for configuring a migration operation.
    
    This model defines the configuration options for a migration,
    such as validation, dry run, and parallellism.
    """
    
    validate_only: bool = False
    dry_run: bool = False
    skip_validation: bool = False
    parallel_resources: bool = True
    max_concurrent_resources: int = 5
    timeout_seconds: Optional[int] = None
    rollback_on_failure: bool = True
    extra_options: Dict[str, Any] = {}


class MigrationService:
    """
    Service for executing migrations.
    
    This class provides methods for planning, validating, and executing
    migrations between different environments.
    """
    
    def __init__(
        self,
        default_project_id: Optional[str] = None,
        default_location: str = "us-central1",
        default_credentials_path: Optional[str] = None,
        use_application_default: bool = True
    ):
        """
        Initialize the migration service.
        
        Args:
            default_project_id: Default GCP project ID
            default_location: Default GCP location
            default_credentials_path: Default path to GCP credentials
            use_application_default: Whether to use application default credentials
        """
        self.default_project_id = default_project_id
        self.default_location = default_location
        self.default_credentials_path = default_credentials_path
        self.use_application_default = use_application_default
        
        # Service clients
        self._secret_manager: Optional[SecretManagerService] = None
        self._storage: Optional[StorageService] = None
        self._firestore: Optional[FirestoreService] = None
        
        # Migration workflows
        self._workflows: Dict[str, MigrationWorkflow] = {}
    
    async def initialize(self) -> None:
        """
        Initialize the migration service.
        
        This method initializes service clients and other resources
        needed by the migration service.
        
        Raises:
            ConfigurationError: If required configuration is missing
        """
        if not self.default_project_id:
            # Try to get project ID from environment
            self.default_project_id = os.environ.get('GCP_PROJECT')
            
            if not self.default_project_id:
                raise ConfigurationError(
                    "No project ID provided and GCP_PROJECT environment variable not set"
                )
        
        # Initialize service clients
        self._secret_manager = SecretManagerService(
            project_id=self.default_project_id,
            credentials_path=self.default_credentials_path,
            use_application_default=self.use_application_default,
            location=self.default_location
        )
        await self._secret_manager.initialize()
        
        self._storage = StorageService(
            project_id=self.default_project_id,
            credentials_path=self.default_credentials_path,
            use_application_default=self.use_application_default,
            location=self.default_location
        )
        await self._storage.initialize()
        
        self._firestore = FirestoreService(
            project_id=self.default_project_id,
            credentials_path=self.default_credentials_path,
            use_application_default=self.use_application_default,
            location=self.default_location
        )
        await self._firestore.initialize()
        
        logger.info(f"Migration service initialized for project {self.default_project_id}")
    
    async def close(self) -> None:
        """
        Close the migration service and release resources.
        """
        if self._secret_manager:
            await self._secret_manager.close()
            self._secret_manager = None
            
        if self._storage:
            await self._storage.close()
            self._storage = None
            
        if self._firestore:
            await self._firestore.close()
            self._firestore = None
            
        logger.info("Migration service closed")
    
    async def create_github_to_gcp_plan(
        self,
        github_config: GithubConfig,
        gcp_config: Optional[GCPConfig] = None,
        resources: Optional[List[MigrationResource]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> MigrationPlan:
        """
        Create a migration plan from GitHub to GCP.
        
        This method creates a plan for migrating resources from
        GitHub to Google Cloud Platform.
        
        Args:
            github_config: GitHub configuration
            gcp_config: GCP configuration (optional)
            resources: List of resources to migrate (optional)
            options: Additional options for the migration
            
        Returns:
            Migration plan
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        # Use default project if none provided
        if gcp_config is None:
            if not self.default_project_id:
                raise ConfigurationError(
                    "No GCP project ID provided and no default project ID set"
                )
            
            gcp_config = GCPConfig(
                project_id=self.default_project_id,
                location=self.default_location,
                credentials_path=self.default_credentials_path,
                use_application_default=self.use_application_default
            )
        
        # Create default resources if none provided
        if resources is None:
            resources = []
        
        # Create migration context
        context = MigrationContext(
            migration_id=str(uuid.uuid4()),
            migration_type=MigrationType.GITHUB_TO_GCP,
            source={
                "type": "github",
                "config": github_config.dict()
            },
            destination={
                "type": "gcp",
                "config": gcp_config.dict()
            },
            resources=resources,
            options=options or {}
        )
        
        # Create the plan steps
        validation_steps = [
            "validate_github_credentials",
            "validate_gcp_credentials",
            "validate_resources"
        ]
        
        execution_steps = [
            {
                "id": "github_auth",
                "name": "Authenticate with GitHub",
                "description": "Authenticate with GitHub using provided credentials"
            },
            {
                "id": "gcp_auth",
                "name": "Authenticate with GCP",
                "description": "Authenticate with Google Cloud Platform"
            },
            {
                "id": "clone_repository",
                "name": "Clone GitHub Repository",
                "description": f"Clone the repository {github_config.repository}"
            },
            {
                "id": "migrate_resources",
                "name": "Migrate Resources",
                "description": "Migrate resources from GitHub to GCP"
            },
            {
                "id": "validate_migration",
                "name": "Validate Migration",
                "description": "Validate migrated resources"
            }
        ]
        
        rollback_steps = [
            {
                "id": "delete_migrated_resources",
                "name": "Delete Migrated Resources",
                "description": "Delete resources migrated to GCP"
            },
            {
                "id": "cleanup_temp_files",
                "name": "Clean Up Temporary Files",
                "description": "Clean up temporary files created during migration"
            }
        ]
        
        # Create the plan
        plan = MigrationPlan(
            plan_id=str(uuid.uuid4()),
            description=f"Migration from GitHub repository {github_config.repository} to GCP project {gcp_config.project_id}",
            context=context,
            validation_steps=validation_steps,
            execution_steps=execution_steps,
            rollback_steps=rollback_steps
        )
        
        return plan
    
    async def create_workflow_for_plan(
        self,
        plan: MigrationPlan,
        options: Optional[MigrationOptions] = None
    ) -> MigrationWorkflow:
        """
        Create a workflow for executing a migration plan.
        
        This method creates a workflow that defines the steps for executing
        a migration plan, based on the plan's execution steps.
        
        Args:
            plan: Migration plan to execute
            options: Options for the workflow execution
            
        Returns:
            Migration workflow
            
        Raises:
            ConfigurationError: If plan is invalid
        """
        options = options or MigrationOptions()
        
        # Create workflow steps based on migration type
        steps: List[WorkflowStep] = []
        
        # Add validation step
        steps.append(ValidateMigrationPlan(
            step_id="validate_plan",
            name="Validate Migration Plan",
            description="Validate the migration plan before execution"
        ))
        
        # Create steps based on migration type
        if plan.context.migration_type == MigrationType.GITHUB_TO_GCP:
            # Add GitHub to GCP migration steps
            steps.extend(await self._create_github_to_gcp_steps(plan, options))
        else:
            raise ConfigurationError(
                f"Unsupported migration type: {plan.context.migration_type}"
            )
        
        # Create the workflow
        workflow_id = f"migration-{plan.plan_id}"
        workflow = MigrationWorkflow(
            name=f"Migration Workflow {plan.plan_id}",
            description=plan.description,
            steps=steps
        )
        
        # Store the workflow
        self._workflows[workflow_id] = workflow
        
        return workflow
    
    async def _create_github_to_gcp_steps(
        self,
        plan: MigrationPlan,
        options: MigrationOptions
    ) -> List[WorkflowStep]:
        """
        Create steps for a GitHub to GCP migration.
        
        Args:
            plan: Migration plan
            options: Migration options
            
        Returns:
            List of workflow steps
        """
        steps: List[WorkflowStep] = []
        
        # Get configuration
        github_config = GithubConfig(**plan.context.source["config"])
        gcp_config = GCPConfig(**plan.context.destination["config"])
        
        # Add GitHub authentication step
        steps.append(GitHubAuthenticationStep(
            step_id="github_auth",
            name="GitHub Authentication",
            description="Authenticate with GitHub"
        ))
        
        # Add GCP authentication step
        steps.append(GCPAuthenticationStep(
            step_id="gcp_auth",
            name="GCP Authentication",
            description="Authenticate with Google Cloud Platform"
        ))
        
        # Add repository cloning step
        steps.append(CloneRepositoryStep(
            step_id="clone_repo",
            name="Clone Repository",
            description=f"Clone repository {github_config.repository}",
            repository=github_config.repository,
            branch=github_config.branch
        ))
        
        # Add resource migration steps for each resource
        for resource in plan.context.resources:
            steps.append(self._create_resource_migration_step(resource))
        
        # Add validation step
        steps.append(ValidateMigratedResourcesStep(
            step_id="validate_resources",
            name="Validate Migrated Resources",
            description="Validate that resources were migrated successfully"
        ))
        
        # Add cleanup step
        steps.append(CleanupStep(
            step_id="cleanup",
            name="Cleanup",
            description="Clean up temporary resources",
            optional=True
        ))
        
        return steps
    
    def _create_resource_migration_step(self, resource: MigrationResource) -> ResourceMigrationStep:
        """
        Create a step for migrating a specific resource.
        
        Args:
            resource: Resource to migrate
            
        Returns:
            Resource migration step
            
        Raises:
            ConfigurationError: If resource type is unsupported
        """
        # Create step based on resource type
        if resource.type == ResourceType.SECRET:
            return SecretMigrationStep(
                resource_id=resource.id,
                step_id=f"migrate_secret_{resource.id}",
                name=f"Migrate Secret {resource.name}",
                description=f"Migrate secret {resource.name} to Secret Manager"
            )
        elif resource.type == ResourceType.FILE:
            return FileMigrationStep(
                resource_id=resource.id,
                step_id=f"migrate_file_{resource.id}",
                name=f"Migrate File {resource.name}",
                description=f"Migrate file {resource.name} to Cloud Storage"
            )
        elif resource.type == ResourceType.CONFIGURATION:
            return ConfigMigrationStep(
                resource_id=resource.id,
                step_id=f"migrate_config_{resource.id}",
                name=f"Migrate Configuration {resource.name}",
                description=f"Migrate configuration {resource.name}"
            )
        else:
            raise ConfigurationError(
                f"Unsupported resource type: {resource.type}"
            )
    
    async def validate_plan(self, plan: MigrationPlan) -> ValidationResult:
        """
        Validate a migration plan.
        
        Args:
            plan: Migration plan to validate
            
        Returns:
            Validation result
        """
        # Create a workflow for the plan
        workflow = await self.create_workflow_for_plan(plan)
        
        # Validate the workflow
        return await workflow.validate(plan.context)
    
    async def execute_plan(
        self,
        plan: MigrationPlan,
        options: Optional[MigrationOptions] = None
    ) -> MigrationResult:
        """
        Execute a migration plan.
        
        Args:
            plan: Migration plan to execute
            options: Options for plan execution
            
        Returns:
            Migration result
            
        Raises:
            MigrationExecutionError: If the migration fails
            ValidationError: If the plan validation fails
        """
        options = options or MigrationOptions()
        
        # Check if service is initialized
        if self._secret_manager is None:
            await self.initialize()
        
        # Validate the plan if not skipped
        if not options.skip_validation:
            validation_result = await self.validate_plan(plan)
            
            if not validation_result.valid:
                raise ValidationError(
                    f"Migration plan validation failed: {validation_result.errors}",
                    details={"errors": validation_result.errors}
                )
            
            if options.validate_only:
                # Return empty result for validate-only
                return MigrationResult(
                    plan_id=plan.plan_id,
                    context=plan.context,
                    success=True,
                    start_time=datetime.datetime.now(),
                    end_time=datetime.datetime.now()
                )
        
        # Create a workflow for the plan
        workflow = await self.create_workflow_for_plan(plan, options)
        
        # Execute the workflow
        if options.dry_run:
            # Don't actually execute the workflow
            logger.info(f"Dry run of migration plan {plan.plan_id}")
            
            # Return dummy result
            return MigrationResult(
                plan_id=plan.plan_id,
                context=plan.context,
                success=True,
                metrics={"dry_run": True},
                start_time=datetime.datetime.now(),
                end_time=datetime.datetime.now()
            )
        else:
            # Execute the workflow
            return await workflow.execute_migration(plan.context)
    
    async def get_migration_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the status of a migration workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Status information for the workflow
            
        Raises:
            ValueError: If the workflow is not found
        """
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        workflow = self._workflows[workflow_id]
        
        # Collect status information
        completed_steps = 0
        failed_steps = 0
        in_progress_steps = 0
        
        for step_id, result in workflow.results.items():
            if result.status == StepStatus.COMPLETED:
                completed_steps += 1
            elif result.status == StepStatus.FAILED:
                failed_steps += 1
            elif result.status == StepStatus.IN_PROGRESS:
                in_progress_steps += 1
        
        # Calculate progress
        total_steps = len(workflow.steps)
        progress = round(completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": "failed" if failed_steps > 0 else "completed" if completed_steps == total_steps else "in_progress",
            "progress": progress,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "in_progress_steps": in_progress_steps,
            "total_steps": total_steps
        }


# Resource migration step implementations

class GitHubAuthenticationStep(WorkflowStep[MigrationContext, Dict[str, Any]]):
    """Step for authenticating with GitHub."""
    
    async def execute(self, context: MigrationContext) -> Dict[str, Any]:
        """
        Authenticate with GitHub.
        
        Args:
            context: Migration context
            
        Returns:
            Authentication result with token information
        """
        # Get GitHub configuration
        github_config = GithubConfig(**context.source["config"])
        
        # Authenticate with GitHub
        # In a real implementation, this would use GitHub API or git commands
        logger.info(f"Authenticating with GitHub for {github_config.repository}")
        
        # Simulate authentication
        await asyncio.sleep(1)
        
        return {
            "authenticated": True,
            "repository": github_config.repository,
            "token_type": "oauth" if github_config.use_oauth else "personal"
        }


class GCPAuthenticationStep(WorkflowStep[MigrationContext, Dict[str, Any]]):
    """Step for authenticating with GCP."""
    
    async def execute(self, context: MigrationContext) -> Dict[str, Any]:
        """
        Authenticate with GCP.
        
        Args:
            context: Migration context
            
        Returns:
            Authentication result with project information
        """
        # Get GCP configuration
        gcp_config = GCPConfig(**context.destination["config"])
        
        # Authenticate with GCP
        # In a real implementation, this would use GCP API
        logger.info(f"Authenticating with GCP for project {gcp_config.project_id}")
        
        # Simulate authentication
        await asyncio.sleep(1)
        
        return {
            "authenticated": True,
            "project_id": gcp_config.project_id,
            "authenticated_with": "application_default" if gcp_config.use_application_default else "service_account"
        }


class CloneRepositoryStep(WorkflowStep[MigrationContext, str]):
    """Step for cloning a GitHub repository."""
    
    def __init__(
        self,
        repository: str,
        branch: str = "main",
        target_dir: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize clone repository step.
        
        Args:
            repository: Repository name (owner/repo)
            branch: Branch to clone
            target_dir: Target directory for the clone
            **kwargs: Additional arguments for WorkflowStep
        """
        super().__init__(**kwargs)
        self.repository = repository
        self.branch = branch
        self.target_dir = target_dir or f"/tmp/migration/{repository.replace('/', '_')}"
    
    async def execute(self, context: MigrationContext) -> str:
        """
        Clone the repository.
        
        Args:
            context: Migration context
            
        Returns:
            Path to the cloned repository
        """
        # Get GitHub configuration
        github_config = GithubConfig(**context.source["config"])
        
        # Clone the repository
        # In a real implementation, this would use git commands
        logger.info(f"Cloning repository {self.repository} branch {self.branch}")
        
        # Create the target directory
        os.makedirs(self.target_dir, exist_ok=True)
        
        # Simulate cloning
        await asyncio.sleep(2)
        
        # Update context with repository path
        context.options["repository_path"] = self.target_dir
        
        return self.target_dir


class SecretMigrationStep(ResourceMigrationStep):
    """Step for migrating a secret to GCP Secret Manager."""
    
    async def _migrate_resource(self, context: MigrationContext, resource: MigrationResource) -> None:
        """
        Migrate a secret to Secret Manager.
        
        Args:
            context: Migration context
            resource: Resource to migrate
        """
        # Get GCP configuration
        gcp_config = GCPConfig(**context.destination["config"])
        
        # In a real implementation, this would extract the secret from GitHub
        secret_value = f"dummy-secret-value-{resource.id}"
        
        # Migrate the secret to Secret Manager
        logger.info(f"Migrating secret {resource.name} to Secret Manager")
        
        # Simulate migration
        await asyncio.sleep(1)
        
        # Update resource metadata
        resource.metadata["secret_manager_path"] = f"projects/{gcp_config.project_id}/secrets/{resource.name}"


class FileMigrationStep(ResourceMigrationStep):
    """Step for migrating a file to GCP Cloud Storage."""
    
    async def _migrate_resource(self, context: MigrationContext, resource: MigrationResource) -> None:
        """
        Migrate a file to Cloud Storage.
        
        Args:
            context: Migration context
            resource: Resource to migrate
        """
        # Get GCP configuration and repository path
        gcp_config = GCPConfig(**context.destination["config"])
        repo_path = context.options.get("repository_path", "")
        
        # Get source and destination paths
        source_path = os.path.join(repo_path, resource.source_path or "")
        destination_bucket = gcp_config.storage_bucket or f"{gcp_config.project_id}-migration"
        
        # In a real implementation, this would upload the file to Cloud Storage
        logger.info(f"Migrating file {resource.name} to Cloud Storage bucket {destination_bucket}")
        
        # Simulate migration
        await asyncio.sleep(1)
        
        # Update resource metadata
        resource.metadata["storage_path"] = f"gs://{destination_bucket}/{resource.name}"
        resource.destination_path = f"gs://{destination_bucket}/{resource.name}"


class ConfigMigrationStep(ResourceMigrationStep):
    """Step for migrating a configuration to GCP."""
    
    async def _migrate_resource(self, context: MigrationContext, resource: MigrationResource) -> None:
        """
        Migrate a configuration.
        
        Args:
            context: Migration context
            resource: Resource to migrate
        """
        # Get GCP configuration
        gcp_config = GCPConfig(**context.destination["config"])
        
        # In a real implementation, this would migrate the configuration
        logger.info(f"Migrating configuration {resource.name}")
        
        # Simulate migration
        await asyncio.sleep(1)
        
        # Update resource metadata
        resource.metadata["config_path"] = f"projects/{gcp_config.project_id}/configs/{resource.name}"


class ValidateMigratedResourcesStep(WorkflowStep[MigrationContext, ValidationResult]):
    """Step for validating migrated resources."""
    
    async def execute(self, context: MigrationContext) -> ValidationResult:
        """
        Validate migrated resources.
        
        Args:
            context: Migration context
            
        Returns:
            Validation result
        """
        checks = []
        errors = []
        
        # Validate each resource
        for resource in context.resources:
            if resource.status == MigrationStatus.COMPLETED:
                checks.append({
                    "name": f"resource_{resource.id}",
                    "result": True,
                    "details": {"resource_name": resource.name}
                })
            elif resource.status == MigrationStatus.FAILED:
                errors.append({
                    "type": "ResourceMigrationFailed",
                    "message": f"Resource {resource.name} failed to migrate",
                    "details": {"resource_id": resource.id}
                })
                checks.append({
                    "name": f"resource_{resource.id}",
                    "result": False,
                    "details": {"resource_name": resource.name}
                })
        
        # Return validation result
        return ValidationResult(
            valid=len(errors) == 0,
            checks=checks,
            errors=errors
        )


class CleanupStep(WorkflowStep[MigrationContext, None]):
    """Step for cleaning up temporary resources."""
    
    async def execute(self, context: MigrationContext) -> None:
        """
        Clean up temporary resources.
        
        Args:
            context: Migration context
        """
        # Clean up temporary files
        repo_path = context.options.get("repository_path", "")
        if repo_path and os.path.exists(repo_path):
            logger.info(f"Cleaning up repository path: {repo_path}")
            # In a real implementation, this would delete the directory
            # os.rmdir(repo_path)
        
        # Clean up other temporary resources
        logger.info("Cleaning up temporary resources")