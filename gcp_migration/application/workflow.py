"""
Migration workflow orchestration.

This module provides workflow abstractions for orchestrating migration tasks
and managing their execution, tracking, and reporting.
"""

import asyncio
import datetime
import functools
import logging
import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from types import TracebackType
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

from pydantic import BaseModel, Field

from ..domain.exceptions_fixed import MigrationError, MigrationExecutionError, ValidationError
from ..domain.models import (
    MigrationContext, MigrationPlan, MigrationResource, MigrationResult, 
    MigrationStatus, ValidationResult
)

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T')
R = TypeVar('R')


class StepStatus(Enum):
    """Status of a workflow step."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel, Generic[T]):
    """
    Result of a workflow step execution.
    
    This model captures the result of executing a workflow step,
    including success/failure information and the output value.
    """
    
    step_id: str
    step_name: str
    status: StepStatus
    output: Optional[T] = None
    error: Optional[Dict[str, Any]] = None
    start_time: datetime.datetime = Field(default_factory=datetime.datetime.now)
    end_time: Optional[datetime.datetime] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """Check if the step was successful."""
        return self.status == StepStatus.COMPLETED
    
    @property
    def is_failure(self) -> bool:
        """Check if the step failed."""
        return self.status == StepStatus.FAILED


class WorkflowStep(ABC, Generic[T, R]):
    """
    Base class for workflow steps.
    
    This class defines the interface for workflow steps, which are the
    building blocks of migration workflows.
    """
    
    def __init__(
        self,
        step_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        retry_delay: float = 1.0,
        optional: bool = False,
        skip_condition: Optional[Callable[[T], bool]] = None
    ):
        """
        Initialize a workflow step.
        
        Args:
            step_id: Unique identifier for the step
            name: Display name for the step
            description: Description of what the step does
            dependencies: List of step IDs that must complete before this step
            timeout: Maximum time in seconds for the step to complete
            retry_count: Number of times to retry on failure
            retry_delay: Delay in seconds between retries
            optional: Whether this step is optional
            skip_condition: Function that returns True if the step should be skipped
        """
        self.step_id = step_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.description = description or f"Execute step {self.name}"
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.optional = optional
        self.skip_condition = skip_condition
    
    @abstractmethod
    async def execute(self, context: T) -> R:
        """
        Execute the step.
        
        This method must be implemented by subclasses to define the
        actual work performed by the step.
        
        Args:
            context: Input context for the step
            
        Returns:
            Output of the step
        """
        pass
    
    async def should_skip(self, context: T) -> bool:
        """
        Check if the step should be skipped.
        
        Args:
            context: Input context for the step
            
        Returns:
            True if the step should be skipped, False otherwise
        """
        if self.skip_condition:
            return self.skip_condition(context)
        return False
    
    async def validate(self, context: T) -> ValidationResult:
        """
        Validate the step inputs.
        
        Args:
            context: Input context to validate
            
        Returns:
            Validation result
        """
        # Default validation always passes
        return ValidationResult(
            valid=True,
            checks=[{"name": f"{self.name}_input_validation", "result": True}]
        )
    
    def __str__(self) -> str:
        """Get string representation of the step."""
        return f"{self.name} ({self.step_id})"


class CompositeStep(WorkflowStep[T, Dict[str, Any]]):
    """
    A step that consists of multiple sub-steps.
    
    This class allows for composing multiple steps into a single logical step,
    which can be useful for grouping related operations.
    """
    
    def __init__(
        self,
        steps: List[WorkflowStep],
        parallel: bool = False,
        fail_fast: bool = True,
        **kwargs
    ):
        """
        Initialize a composite step.
        
        Args:
            steps: List of sub-steps to execute
            parallel: Whether to execute steps in parallel
            fail_fast: Whether to stop on first failure
            **kwargs: Additional arguments for WorkflowStep
        """
        super().__init__(**kwargs)
        self.steps = steps
        self.parallel = parallel
        self.fail_fast = fail_fast
    
    async def execute(self, context: T) -> Dict[str, Any]:
        """
        Execute all sub-steps.
        
        Args:
            context: Input context for the steps
            
        Returns:
            Dictionary of step outputs keyed by step ID
            
        Raises:
            MigrationExecutionError: If a required step fails
        """
        results: Dict[str, Any] = {}
        
        if self.parallel:
            # Execute steps in parallel
            tasks = []
            for step in self.steps:
                if await step.should_skip(context):
                    logger.info(f"Skipping step {step.name} ({step.step_id})")
                    continue
                    
                task = asyncio.create_task(step.execute(context))
                tasks.append((step, task))
            
            # Wait for all tasks to complete
            for step, task in tasks:
                try:
                    result = await task
                    results[step.step_id] = result
                except Exception as e:
                    if self.fail_fast and not step.optional:
                        # Cancel all remaining tasks
                        for _, t in tasks:
                            if not t.done():
                                t.cancel()
                        
                        # Re-raise the exception
                        raise MigrationExecutionError(
                            f"Step {step.name} ({step.step_id}) failed: {e}",
                            cause=e,
                            details={"step_id": step.step_id, "step_name": step.name}
                        )
                    else:
                        logger.error(f"Step {step.name} ({step.step_id}) failed: {e}")
                        results[step.step_id] = None
        else:
            # Execute steps sequentially
            for step in self.steps:
                if await step.should_skip(context):
                    logger.info(f"Skipping step {step.name} ({step.step_id})")
                    continue
                    
                try:
                    result = await step.execute(context)
                    results[step.step_id] = result
                except Exception as e:
                    if self.fail_fast and not step.optional:
                        # Re-raise the exception
                        raise MigrationExecutionError(
                            f"Step {step.name} ({step.step_id}) failed: {e}",
                            cause=e,
                            details={"step_id": step.step_id, "step_name": step.name}
                        )
                    else:
                        logger.error(f"Step {step.name} ({step.step_id}) failed: {e}")
                        results[step.step_id] = None
        
        return results


class FunctionalStep(WorkflowStep[T, R]):
    """
    A step that executes a function.
    
    This class allows for creating steps from functions, which can be
    useful for simple operations or adapting existing functions.
    """
    
    def __init__(
        self,
        func: Callable[[T], R],
        **kwargs
    ):
        """
        Initialize a functional step.
        
        Args:
            func: Function to execute
            **kwargs: Additional arguments for WorkflowStep
        """
        super().__init__(**kwargs)
        self.func = func
    
    async def execute(self, context: T) -> R:
        """
        Execute the function.
        
        Args:
            context: Input context for the function
            
        Returns:
            Output of the function
        """
        # Check if the function is asynchronous
        if asyncio.iscoroutinefunction(self.func):
            # Execute asynchronously
            return await self.func(context)
        else:
            # Execute in a thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.func, context)


class Workflow(Generic[T, R]):
    """
    A workflow that executes multiple steps.
    
    This class manages the execution of a sequence of steps, handling
    dependencies, validation, and error handling.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        steps: Optional[List[WorkflowStep]] = None,
    ):
        """
        Initialize a workflow.
        
        Args:
            name: Name of the workflow
            description: Description of the workflow
            steps: List of steps to execute
        """
        self.name = name
        self.description = description or f"Workflow {name}"
        self.steps = steps or []
        self.step_map = {step.step_id: step for step in self.steps}
        
        # Results of step executions
        self.results: Dict[str, StepResult] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the workflow.
        
        Args:
            step: Step to add
        """
        self.steps.append(step)
        self.step_map[step.step_id] = step
    
    def remove_step(self, step_id: str) -> bool:
        """
        Remove a step from the workflow.
        
        Args:
            step_id: ID of the step to remove
            
        Returns:
            True if the step was removed, False if not found
        """
        if step_id in self.step_map:
            step = self.step_map[step_id]
            self.steps.remove(step)
            del self.step_map[step_id]
            return True
        return False
    
    async def execute(self, context: T) -> R:
        """
        Execute the workflow.
        
        This method executes all steps in the workflow, respecting dependencies
        and handling errors.
        
        Args:
            context: Input context for the workflow
            
        Returns:
            Output of the workflow
            
        Raises:
            MigrationExecutionError: If a required step fails
        """
        # Reset results
        self.results = {}
        
        # Build dependency graph
        dependent_steps: Dict[str, Set[str]] = {}
        ready_steps: Set[str] = set()
        
        for step in self.steps:
            # Check if this step has dependencies
            if not step.dependencies:
                ready_steps.add(step.step_id)
            else:
                # Check each dependency
                for dep_id in step.dependencies:
                    if dep_id not in self.step_map:
                        raise ValidationError(
                            f"Step {step.name} ({step.step_id}) has unknown dependency: {dep_id}"
                        )
                    
                    # Add this step as dependent on its dependency
                    if dep_id not in dependent_steps:
                        dependent_steps[dep_id] = set()
                    dependent_steps[dep_id].add(step.step_id)
        
        # Execute steps in dependency order
        remaining_steps = set(self.step_map.keys())
        final_result = None
        
        while remaining_steps and ready_steps:
            # Get next ready step
            step_id = next(iter(ready_steps))
            ready_steps.remove(step_id)
            
            # Execute the step
            step = self.step_map[step_id]
            
            # Skip if condition is met
            should_skip = await step.should_skip(context)
            if should_skip:
                logger.info(f"Skipping step {step.name} ({step.step_id})")
                
                # Record result
                result = StepResult(
                    step_id=step.step_id,
                    step_name=step.name,
                    status=StepStatus.SKIPPED,
                    start_time=datetime.datetime.now(),
                    end_time=datetime.datetime.now(),
                    duration_seconds=0.0
                )
                async with self._lock:
                    self.results[step_id] = result
                
                # Update remaining steps
                remaining_steps.remove(step_id)
                
                # Update ready steps
                if step_id in dependent_steps:
                    for dep_step_id in dependent_steps[step_id]:
                        # Check if all dependencies of this step are complete
                        if all(
                            dep_id not in remaining_steps
                            for dep_id in self.step_map[dep_step_id].dependencies
                        ):
                            ready_steps.add(dep_step_id)
                
                continue
            
            # Execute the step with retries
            start_time = datetime.datetime.now()
            retry = 0
            success = False
            step_output = None
            step_error = None
            
            while retry <= step.retry_count:
                try:
                    if retry > 0:
                        logger.info(f"Retrying step {step.name} (attempt {retry}/{step.retry_count})")
                        await asyncio.sleep(step.retry_delay)
                    
                    # Execute the step with timeout if specified
                    if step.timeout:
                        step_output = await asyncio.wait_for(
                            step.execute(context),
                            timeout=step.timeout
                        )
                    else:
                        step_output = await step.execute(context)
                    
                    # Step completed successfully
                    success = True
                    break
                    
                except asyncio.TimeoutError:
                    # Step timed out
                    step_error = {
                        "type": "TimeoutError",
                        "message": f"Step timed out after {step.timeout} seconds"
                    }
                    logger.error(f"Step {step.name} timed out")
                    
                except Exception as e:
                    # Step failed
                    step_error = {
                        "type": e.__class__.__name__,
                        "message": str(e),
                        "traceback": traceback.format_exc()
                    }
                    logger.error(f"Step {step.name} failed: {e}")
                
                retry += 1
            
            # Record the result
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = StepResult(
                step_id=step.step_id,
                step_name=step.name,
                status=StepStatus.COMPLETED if success else StepStatus.FAILED,
                output=step_output,
                error=step_error,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration
            )
            
            async with self._lock:
                self.results[step_id] = result
            
            # Check if the step failed
            if not success and not step.optional:
                # Fail the workflow if a required step failed
                raise MigrationExecutionError(
                    f"Step {step.name} ({step.step_id}) failed",
                    details={
                        "step_id": step.step_id,
                        "step_name": step.name,
                        "error": step_error
                    }
                )
            
            # Save the result of the last step as the workflow result
            if not remaining_steps:
                final_result = step_output
            
            # Update remaining steps
            remaining_steps.remove(step_id)
            
            # Update ready steps
            if step_id in dependent_steps:
                for dep_step_id in dependent_steps[step_id]:
                    # Check if all dependencies of this step are complete
                    if all(
                        dep_id not in remaining_steps
                        for dep_id in self.step_map[dep_step_id].dependencies
                    ):
                        ready_steps.add(dep_step_id)
        
        # Check if all steps were executed
        if remaining_steps:
            # Circular dependency or missing dependency
            raise MigrationExecutionError(
                f"Workflow could not complete: remaining steps {remaining_steps}"
            )
        
        return final_result
    
    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """
        Get the result of a step.
        
        Args:
            step_id: ID of the step
            
        Returns:
            Result of the step or None if not found
        """
        return self.results.get(step_id)
    
    async def validate(self, context: T) -> ValidationResult:
        """
        Validate the workflow.
        
        Args:
            context: Input context to validate
            
        Returns:
            Validation result
        """
        checks = []
        errors = []
        warnings = []
        
        # Check for circular dependencies
        try:
            # Build dependency graph
            graph = {}
            for step in self.steps:
                graph[step.step_id] = step.dependencies
            
            # Check for cycles
            visited = set()
            temp = set()
            
            def is_cyclic(node, path=None):
                if path is None:
                    path = []
                
                if node in temp:
                    return True, path + [node]
                
                if node in visited:
                    return False, []
                
                temp.add(node)
                path.append(node)
                
                for neighbor in graph.get(node, []):
                    has_cycle, cycle_path = is_cyclic(neighbor, path[:])
                    if has_cycle:
                        return True, cycle_path
                
                temp.remove(node)
                visited.add(node)
                return False, []
            
            for step_id in graph:
                if step_id not in visited:
                    has_cycle, cycle_path = is_cyclic(step_id)
                    if has_cycle:
                        errors.append({
                            "type": "CircularDependency",
                            "message": f"Circular dependency detected: {' -> '.join(cycle_path)}"
                        })
                        checks.append({
                            "name": "circular_dependency",
                            "result": False,
                            "details": {"cycle": cycle_path}
                        })
                    else:
                        checks.append({
                            "name": "circular_dependency",
                            "result": True
                        })
            
            # Validate each step
            for step in self.steps:
                try:
                    step_result = await step.validate(context)
                    checks.extend(step_result.checks)
                    errors.extend(step_result.errors)
                    warnings.extend(step_result.warnings)
                except Exception as e:
                    errors.append({
                        "type": "StepValidationError",
                        "message": f"Step {step.name} ({step.step_id}) validation failed: {e}"
                    })
                    checks.append({
                        "name": f"{step.name}_validation",
                        "result": False,
                        "details": {"error": str(e)}
                    })
            
            # Check for unknown dependencies
            all_step_ids = set(self.step_map.keys())
            for step in self.steps:
                for dep_id in step.dependencies:
                    if dep_id not in all_step_ids:
                        errors.append({
                            "type": "UnknownDependency",
                            "message": f"Step {step.name} ({step.step_id}) has unknown dependency: {dep_id}"
                        })
                        checks.append({
                            "name": f"{step.name}_dependencies",
                            "result": False,
                            "details": {"unknown_dependency": dep_id}
                        })
        
        except Exception as e:
            errors.append({
                "type": "ValidationError",
                "message": f"Workflow validation failed: {e}"
            })
            checks.append({
                "name": "workflow_validation",
                "result": False,
                "details": {"error": str(e)}
            })
        
        # Final validation result
        return ValidationResult(
            valid=len(errors) == 0,
            checks=checks,
            errors=errors,
            warnings=warnings
        )


class MigrationWorkflow(Workflow[MigrationContext, MigrationResult]):
    """
    Workflow for executing a migration.
    
    This class specializes the generic workflow for migration operations,
    providing additional features specific to migration.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        steps: Optional[List[WorkflowStep]] = None,
        on_failure: Optional[Callable[[MigrationContext, Exception], None]] = None
    ):
        """
        Initialize a migration workflow.
        
        Args:
            name: Name of the workflow
            description: Description of the workflow
            steps: List of steps to execute
            on_failure: Callback to execute on workflow failure
        """
        super().__init__(name, description, steps)
        self.on_failure = on_failure
    
    async def execute_migration(
        self,
        context: MigrationContext
    ) -> MigrationResult:
        """
        Execute the migration workflow.
        
        This method executes all steps in the workflow, updates the
        migration context with the results, and returns a migration result.
        
        Args:
            context: Migration context
            
        Returns:
            Migration result
            
        Raises:
            MigrationExecutionError: If the migration fails
        """
        # Update context status
        context.status = MigrationStatus.IN_PROGRESS
        context.start_time = datetime.datetime.now()
        
        # Execute the workflow
        success = True
        errors = []
        try:
            # Execute all steps
            await super().execute(context)
            
        except Exception as e:
            success = False
            error_details = {
                "type": e.__class__.__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            errors.append(error_details)
            
            # Call failure callback if provided
            if self.on_failure:
                try:
                    self.on_failure(context, e)
                except Exception as callback_error:
                    logger.error(f"Error in failure callback: {callback_error}")
            
            # Update context status
            context.status = MigrationStatus.FAILED
        else:
            # Update context status
            context.status = MigrationStatus.COMPLETED
        
        # Update context end time
        context.end_time = datetime.datetime.now()
        
        # Create the migration result
        metrics = self._collect_metrics()
        return MigrationResult(
            plan_id=getattr(context, "plan_id", str(uuid.uuid4())),
            context=context,
            success=success,
            errors=errors,
            warnings=[],
            metrics=metrics,
            start_time=context.start_time,
            end_time=context.end_time
        )
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from the workflow execution.
        
        Returns:
            Dictionary of metrics
        """
        metrics = {
            "total_steps": len(self.steps),
            "completed_steps": sum(1 for r in self.results.values() if r.status == StepStatus.COMPLETED),
            "failed_steps": sum(1 for r in self.results.values() if r.status == StepStatus.FAILED),
            "skipped_steps": sum(1 for r in self.results.values() if r.status == StepStatus.SKIPPED),
            "step_durations": {
                step_id: result.duration_seconds
                for step_id, result in self.results.items()
                if result.duration_seconds is not None
            },
            "total_duration": sum(
                result.duration_seconds or 0
                for result in self.results.values()
            )
        }
        
        return metrics


# Common migration steps that can be reused across different migrations

class ValidateMigrationPlan(WorkflowStep[MigrationContext, ValidationResult]):
    """Step to validate a migration plan."""
    
    async def execute(self, context: MigrationContext) -> ValidationResult:
        """
        Validate the migration plan.
        
        Args:
            context: Migration context
            
        Returns:
            Validation result
        """
        # Check for required fields
        checks = []
        errors = []
        
        # Check source and destination
        if not context.source:
            errors.append({
                "type": "ValidationError",
                "message": "Migration source is required"
            })
        else:
            checks.append({
                "name": "source_validation",
                "result": True
            })
        
        if not context.destination:
            errors.append({
                "type": "ValidationError",
                "message": "Migration destination is required"
            })
        else:
            checks.append({
                "name": "destination_validation",
                "result": True
            })
        
        # Check resources
        if not context.resources:
            errors.append({
                "type": "ValidationError",
                "message": "No resources to migrate"
            })
        else:
            checks.append({
                "name": "resources_validation",
                "result": True
            })
        
        # Return the validation result
        return ValidationResult(
            valid=len(errors) == 0,
            checks=checks,
            errors=errors
        )


class UpdateResourceStatus(WorkflowStep[Tuple[MigrationContext, str, MigrationStatus], None]):
    """Step to update the status of a resource."""
    
    async def execute(self, context: Tuple[MigrationContext, str, MigrationStatus]) -> None:
        """
        Update resource status.
        
        Args:
            context: Tuple of (migration context, resource ID, new status)
            
        Returns:
            None
        """
        migration_context, resource_id, status = context
        
        # Find the resource and update its status
        for resource in migration_context.resources:
            if resource.id == resource_id:
                resource.status = status
                break
        else:
            # Resource not found
            raise ValueError(f"Resource not found: {resource_id}")


class ResourceMigrationStep(WorkflowStep[MigrationContext, MigrationResource]):
    """Base class for resource migration steps."""
    
    def __init__(
        self,
        resource_id: str,
        **kwargs
    ):
        """
        Initialize a resource migration step.
        
        Args:
            resource_id: ID of the resource to migrate
            **kwargs: Additional arguments for WorkflowStep
        """
        super().__init__(**kwargs)
        self.resource_id = resource_id
    
    async def execute(self, context: MigrationContext) -> MigrationResource:
        """
        Migrate the resource.
        
        Args:
            context: Migration context
            
        Returns:
            The migrated resource
            
        Raises:
            ValueError: If the resource is not found
        """
        # Find the resource
        resource = context.resource_by_id(self.resource_id)
        if not resource:
            raise ValueError(f"Resource not found: {self.resource_id}")
        
        # Update resource status
        resource.status = MigrationStatus.IN_PROGRESS
        
        try:
            # Migrate the resource
            await self._migrate_resource(context, resource)
            
            # Update resource status
            resource.status = MigrationStatus.COMPLETED
            
        except Exception as e:
            # Update resource status
            resource.status = MigrationStatus.FAILED
            
            # Re-raise the exception
            raise MigrationExecutionError(
                f"Resource migration failed: {e}",
                cause=e,
                details={"resource_id": resource.id, "resource_name": resource.name}
            )
        
        return resource
    
    @abstractmethod
    async def _migrate_resource(
        self,
        context: MigrationContext,
        resource: MigrationResource
    ) -> None:
        """
        Migrate a specific resource.
        
        This method must be implemented by subclasses to define how
        a specific resource type is migrated.
        
        Args:
            context: Migration context
            resource: Resource to migrate
        """
        pass


import traceback  # Import at the top of the file