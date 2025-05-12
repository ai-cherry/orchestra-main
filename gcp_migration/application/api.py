"""
API module for the GCP migration toolkit.

This module provides a FastAPI interface for the migration toolkit,
allowing for programmatic execution of migrations via HTTP.
"""

import asyncio
import logging
import os
import uuid
from typing import Dict, List, Optional, Union, Any

from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..domain.exceptions_fixed import MigrationError, ValidationError
from ..domain.models import (
    GCPConfig, GithubConfig, MigrationContext, MigrationPlan, 
    MigrationResult, MigrationStatus, MigrationType,
    ResourceType, MigrationResource
)
from .migration_service import MigrationService, MigrationOptions

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GCP Migration Toolkit API",
    description="API for executing migrations to Google Cloud Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for migration results
# In a real implementation, this would be stored in a database
migration_results: Dict[str, MigrationResult] = {}
migration_tasks: Dict[str, asyncio.Task] = {}


# Request and response models

class MigrationResourceRequest(BaseModel):
    """Request model for a migration resource."""
    
    id: str
    name: str
    type: str
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)


class GitHubToGCPRequest(BaseModel):
    """Request model for GitHub to GCP migration."""
    
    # Github config
    github_repository: str
    github_branch: str = "main"
    github_access_token: Optional[str] = None
    github_use_oauth: bool = False
    
    # GCP config
    gcp_project_id: str
    gcp_location: str = "us-central1"
    gcp_credentials_path: Optional[str] = None
    gcp_use_application_default: bool = True
    gcp_storage_bucket: Optional[str] = None
    
    # Resources
    resources: List[MigrationResourceRequest] = Field(default_factory=list)
    
    # Options
    validate_only: bool = False
    dry_run: bool = False
    skip_validation: bool = False
    parallel_resources: bool = True


class MigrationResponse(BaseModel):
    """Response model for a migration operation."""
    
    migration_id: str
    status: str
    plan_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class MigrationStatusResponse(BaseModel):
    """Response model for migration status."""
    
    migration_id: str
    status: str
    progress: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    resources_total: int = 0
    resources_completed: int = 0
    resources_failed: int = 0


class ValidationResponse(BaseModel):
    """Response model for validation results."""
    
    valid: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    details: Optional[Dict[str, Any]] = None


# Dependency for migration service
async def get_migration_service() -> MigrationService:
    """
    Get an initialized migration service.
    
    Returns:
        Initialized migration service
    """
    # Get project ID from environment if not provided
    project_id = os.environ.get("GCP_PROJECT")
    
    # Create and initialize the service
    service = MigrationService(
        default_project_id=project_id,
        default_location=os.environ.get("GCP_LOCATION", "us-central1"),
        default_credentials_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        use_application_default=True
    )
    
    try:
        await service.initialize()
        return service
    except Exception as e:
        logger.error(f"Failed to initialize migration service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize migration service: {e}"
        )


# Exception handlers
@app.exception_handler(MigrationError)
async def migration_error_handler(request, exc):
    """Handle migration errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_type": exc.__class__.__name__,
            "details": exc.details if hasattr(exc, "details") else None
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_type": "ValidationError",
            "details": exc.details if hasattr(exc, "details") else None
        }
    )


# API routes

@app.get("/", tags=["Status"])
async def root():
    """Get API status."""
    return {"status": "ok", "service": "GCP Migration Toolkit API"}


@app.post("/migrations/github-to-gcp", response_model=MigrationResponse, tags=["Migrations"])
async def create_github_to_gcp_migration(
    request: GitHubToGCPRequest,
    background_tasks: BackgroundTasks,
    migration_service: MigrationService = Depends(get_migration_service)
):
    """
    Create and execute a migration from GitHub to GCP.
    
    Args:
        request: Migration request
        background_tasks: Background task manager
        migration_service: Migration service
        
    Returns:
        Migration response with ID and status
    """
    try:
        # Create GitHub config
        github_config = GithubConfig(
            repository=request.github_repository,
            branch=request.github_branch,
            access_token=request.github_access_token,
            use_oauth=request.github_use_oauth
        )
        
        # Create GCP config
        gcp_config = GCPConfig(
            project_id=request.gcp_project_id,
            location=request.gcp_location,
            credentials_path=request.gcp_credentials_path,
            use_application_default=request.gcp_use_application_default,
            storage_bucket=request.gcp_storage_bucket
        )
        
        # Convert resources
        resources = []
        for resource_req in request.resources:
            resources.append(MigrationResource(
                id=resource_req.id,
                name=resource_req.name,
                type=ResourceType[resource_req.type.upper()],
                source_path=resource_req.source_path,
                destination_path=resource_req.destination_path,
                metadata=resource_req.metadata,
                dependencies=resource_req.dependencies
            ))
        
        # Create migration plan
        plan = await migration_service.create_github_to_gcp_plan(
            github_config=github_config,
            gcp_config=gcp_config,
            resources=resources
        )
        
        # Create migration options
        options = MigrationOptions(
            validate_only=request.validate_only,
            dry_run=request.dry_run,
            skip_validation=request.skip_validation,
            parallel_resources=request.parallel_resources
        )
        
        # Create migration ID
        migration_id = str(uuid.uuid4())
        
        # Define the task function
        async def execute_migration_task():
            try:
                # Execute the plan
                result = await migration_service.execute_plan(plan, options)
                
                # Store the result
                migration_results[migration_id] = result
                
                logger.info(f"Migration {migration_id} completed with status: {result.success}")
            except Exception as e:
                logger.error(f"Migration {migration_id} failed: {e}")
                # Store error information
                migration_results[migration_id] = {
                    "error": str(e),
                    "error_type": e.__class__.__name__
                }
        
        # Add the task to background tasks if not validate_only
        if not request.validate_only:
            background_tasks.add_task(execute_migration_task)
            
            return MigrationResponse(
                migration_id=migration_id,
                plan_id=plan.plan_id,
                status="pending",
                message="Migration started in the background"
            )
        else:
            # For validate_only, return immediately
            return MigrationResponse(
                migration_id=migration_id,
                plan_id=plan.plan_id,
                status="validated",
                message="Migration plan validated successfully"
            )
    
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        if isinstance(e, MigrationError):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create migration: {e}"
            )


@app.get("/migrations/{migration_id}", response_model=MigrationStatusResponse, tags=["Migrations"])
async def get_migration_status(
    migration_id: str,
    migration_service: MigrationService = Depends(get_migration_service)
):
    """
    Get status information for a migration.
    
    Args:
        migration_id: ID of the migration
        migration_service: Migration service
        
    Returns:
        Migration status information
    """
    # Check if migration exists
    if migration_id not in migration_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration {migration_id} not found"
        )
    
    result = migration_results[migration_id]
    
    # Check if result is an error
    if isinstance(result, dict) and "error" in result:
        return MigrationStatusResponse(
            migration_id=migration_id,
            status="failed",
            progress=0,
            resources_total=0,
            resources_completed=0,
            resources_failed=0
        )
    
    # Extract status information
    if isinstance(result, MigrationResult):
        # Calculate resource counts
        resources_total = len(result.context.resources)
        resources_completed = len(result.succeeded_resources)
        resources_failed = len(result.failed_resources)
        
        # Calculate progress
        progress = round((resources_completed / resources_total * 100) 
                         if resources_total > 0 else 0)
        
        return MigrationStatusResponse(
            migration_id=migration_id,
            status="completed" if result.success else "failed",
            progress=progress,
            started_at=result.start_time.isoformat() if result.start_time else None,
            completed_at=result.end_time.isoformat() if result.end_time else None,
            resources_total=resources_total,
            resources_completed=resources_completed,
            resources_failed=resources_failed
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid migration result for {migration_id}"
        )


@app.post("/validate/github-to-gcp", response_model=ValidationResponse, tags=["Validation"])
async def validate_github_to_gcp_migration(
    request: GitHubToGCPRequest,
    migration_service: MigrationService = Depends(get_migration_service)
):
    """
    Validate a migration from GitHub to GCP.
    
    Args:
        request: Migration request
        migration_service: Migration service
        
    Returns:
        Validation result
    """
    try:
        # Create GitHub config
        github_config = GithubConfig(
            repository=request.github_repository,
            branch=request.github_branch,
            access_token=request.github_access_token,
            use_oauth=request.github_use_oauth
        )
        
        # Create GCP config
        gcp_config = GCPConfig(
            project_id=request.gcp_project_id,
            location=request.gcp_location,
            credentials_path=request.gcp_credentials_path,
            use_application_default=request.gcp_use_application_default,
            storage_bucket=request.gcp_storage_bucket
        )
        
        # Convert resources
        resources = []
        for resource_req in request.resources:
            resources.append(MigrationResource(
                id=resource_req.id,
                name=resource_req.name,
                type=ResourceType[resource_req.type.upper()],
                source_path=resource_req.source_path,
                destination_path=resource_req.destination_path,
                metadata=resource_req.metadata,
                dependencies=resource_req.dependencies
            ))
        
        # Create migration plan
        plan = await migration_service.create_github_to_gcp_plan(
            github_config=github_config,
            gcp_config=gcp_config,
            resources=resources
        )
        
        # Validate the plan
        validation_result = await migration_service.validate_plan(plan)
        
        return ValidationResponse(
            valid=validation_result.valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            details={
                "checks": validation_result.checks,
                "plan_id": plan.plan_id
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to validate migration: {e}")
        if isinstance(e, MigrationError):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate migration: {e}"
            )


@app.get("/migrations", response_model=List[MigrationStatusResponse], tags=["Migrations"])
async def list_migrations(
    status: Optional[str] = Query(None, description="Filter by status: pending, completed, failed"),
    limit: int = Query(100, description="Maximum number of migrations to return")
):
    """
    List migrations with optional filters.
    
    Args:
        status: Optional status filter
        limit: Maximum number of migrations to return
        
    Returns:
        List of migration status information
    """
    results = []
    
    # Filter by status if provided
    for migration_id, result in migration_results.items():
        # Check if result is an error
        if isinstance(result, dict) and "error" in result:
            if status is None or status == "failed":
                results.append(
                    MigrationStatusResponse(
                        migration_id=migration_id,
                        status="failed",
                        progress=0,
                        resources_total=0,
                        resources_completed=0,
                        resources_failed=0
                    )
                )
        elif isinstance(result, MigrationResult):
            result_status = "completed" if result.success else "failed"
            
            if status is None or status == result_status:
                # Calculate resource counts
                resources_total = len(result.context.resources)
                resources_completed = len(result.succeeded_resources)
                resources_failed = len(result.failed_resources)
                
                # Calculate progress
                progress = round((resources_completed / resources_total * 100) 
                               if resources_total > 0 else 0)
                
                results.append(
                    MigrationStatusResponse(
                        migration_id=migration_id,
                        status=result_status,
                        progress=progress,
                        started_at=result.start_time.isoformat() if result.start_time else None,
                        completed_at=result.end_time.isoformat() if result.end_time else None,
                        resources_total=resources_total,
                        resources_completed=resources_completed,
                        resources_failed=resources_failed
                    )
                )
    
    # Sort by started_at (most recent first)
    results.sort(key=lambda x: x.started_at or "", reverse=True)
    
    # Apply limit
    return results[:limit]


@app.delete("/migrations/{migration_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Migrations"])
async def delete_migration(migration_id: str):
    """
    Delete a migration and its results.
    
    Args:
        migration_id: ID of the migration to delete
    """
    # Check if migration exists
    if migration_id not in migration_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration {migration_id} not found"
        )
    
    # Cancel any running task
    if migration_id in migration_tasks and not migration_tasks[migration_id].done():
        migration_tasks[migration_id].cancel()
        
    # Remove from results
    del migration_results[migration_id]
    
    # Remove from tasks if present
    if migration_id in migration_tasks:
        del migration_tasks[migration_id]
    
    return None