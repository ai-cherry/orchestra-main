"""
Workflow Engine for executing workflow definitions.

This module implements the core execution engine that processes workflow definitions,
manages their lifecycle, and handles error recovery.
"""

from typing import Dict, List, Optional, Any, Union, Type, Callable, Awaitable
import asyncio
import uuid
from datetime import datetime
import json
import logging
from .models import (
    WorkflowDefinition, 
    WorkflowInstance, 
    WorkflowStep, 
    StepExecution,
    WorkflowStatus,
    StepStatus,
    ErrorHandler,
    ErrorAction
)

logger = logging.getLogger(__name__)


class WorkflowStorageManager:
    """Manages persistence of workflow definitions and instances."""
    
    def __init__(self, storage_dir: str = "./workflow_storage"):
        """Initialize the storage manager."""
        self.storage_dir = storage_dir
        self.definitions: Dict[str, WorkflowDefinition] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        
        # In a real implementation, this would initialize database connections
        # or file storage. For this implementation, we'll use in-memory storage.
    
    async def save_definition(self, definition: WorkflowDefinition) -> bool:
        """Save a workflow definition."""
        self.definitions[definition.id] = definition
        return True
    
    async def get_definition(self, definition_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        return self.definitions.get(definition_id)
    
    async def list_definitions(self) -> List[WorkflowDefinition]:
        """List all workflow definitions."""
        return list(self.definitions.values())
    
    async def save_instance(self, instance: WorkflowInstance) -> bool:
        """Save a workflow instance."""
        self.instances[instance.id] = instance
        return True
    
    async def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by ID."""
        return self.instances.get(instance_id)
    
    async def list_instances(
        self, 
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowInstance]:
        """List workflow instances with optional filtering."""
        instances = list(self.instances.values())
        
        if workflow_id:
            instances = [i for i in instances if i.workflow_id == workflow_id]
        
        if status:
            instances = [i for i in instances if i.status == status]
        
        return instances
    
    async def update_instance_status(
        self, 
        instance_id: str, 
        status: WorkflowStatus,
        error: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the status of a workflow instance."""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        instance.status = status
        
        if status == WorkflowStatus.COMPLETED or status == WorkflowStatus.FAILED:
            instance.end_time = datetime.now().isoformat()
        
        if error:
            instance.error = error
        
        return True
    
    async def update_step_execution(
        self,
        instance_id: str,
        step_id: str,
        status: StepStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the execution status of a workflow step."""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        if step_id not in instance.step_executions:
            return False
        
        step_execution = instance.step_executions[step_id]
        step_execution.status = status
        
        if status == StepStatus.COMPLETED or status == StepStatus.FAILED:
            step_execution.end_time = datetime.now().isoformat()
        
        if output_data:
            step_execution.output_data = output_data
        
        if error:
            step_execution.error = error
        
        return True


class EventBus:
    """Simple event bus for workflow notifications."""
    
    def __init__(self):
        """Initialize the event bus."""
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
    
    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Publish an event to all subscribers."""
        if event_type not in self.subscribers:
            return
        
        for subscriber in self.subscribers[event_type]:
            try:
                await subscriber(event_data)
            except Exception as e:
                logger.error(f"Error in event subscriber: {e}")
    
    def subscribe(
        self, 
        event_type: str, 
        callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(
        self, 
        event_type: str, 
        callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> bool:
        """Unsubscribe from an event type."""
        if event_type not in self.subscribers:
            return False
        
        if callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            return True
        
        return False


class StepExecutor:
    """Base class for executing workflow steps."""
    
    async def execute(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any],
        workflow_instance: WorkflowInstance
    ) -> Dict[str, Any]:
        """Execute a workflow step."""
        raise NotImplementedError("Subclasses must implement execute method")


class WorkflowEngine:
    """Executes workflow definitions and manages their lifecycle."""
    
    def __init__(
        self,
        storage_manager: WorkflowStorageManager,
        event_bus: EventBus,
        step_executors: Dict[str, StepExecutor] = None
    ):
        """Initialize the workflow engine."""
        self.storage_manager = storage_manager
        self.event_bus = event_bus
        self.step_executors = step_executors or {}
        self.active_workflows: Dict[str, asyncio.Task] = {}
    
    def register_step_executor(self, step_type: str, executor: StepExecutor) -> None:
        """Register a step executor for a specific step type."""
        self.step_executors[step_type] = executor
    
    async def start_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Start a workflow execution."""
        # Get the workflow definition
        definition = await self.storage_manager.get_definition(workflow_id)
        if not definition:
            raise ValueError(f"Workflow definition not found: {workflow_id}")
        
        # Create a new workflow instance
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            input_data=input_data or {},
            variables=definition.variables.copy(),
            created_by=created_by
        )
        
        # Initialize step executions
        for step in definition.steps:
            instance.step_executions[step.id] = StepExecution(step_id=step.id)
        
        # Save the instance
        await self.storage_manager.save_instance(instance)
        
        # Start the workflow execution in a separate task
        task = asyncio.create_task(self._execute_workflow(instance.id, context or {}))
        self.active_workflows[instance.id] = task
        
        # Publish workflow started event
        await self.event_bus.publish("workflow_started", {
            "instance_id": instance.id,
            "workflow_id": workflow_id,
            "created_by": created_by
        })
        
        return instance.id
    
    async def _execute_workflow(self, instance_id: str, context: Dict[str, Any]) -> None:
        """Execute a workflow instance."""
        instance = await self.storage_manager.get_instance(instance_id)
        if not instance:
            logger.error(f"Workflow instance not found: {instance_id}")
            return
        
        # Update instance status to running
        instance.status = WorkflowStatus.RUNNING
        instance.start_time = datetime.now().isoformat()
        await self.storage_manager.save_instance(instance)
        
        # Get the workflow definition
        definition = await self.storage_manager.get_definition(instance.workflow_id)
        if not definition:
            logger.error(f"Workflow definition not found: {instance.workflow_id}")
            await self._fail_workflow(instance_id, {"error": "Workflow definition not found"})
            return
        
        try:
            # Build execution plan (topological sort of steps)
            execution_plan = self._build_execution_plan(definition.steps)
            
            # Execute steps according to the plan
            for step_batch in execution_plan:
                # Execute steps in this batch in parallel
                tasks = []
                for step_id in step_batch:
                    step = next((s for s in definition.steps if s.id == step_id), None)
                    if not step:
                        continue
                    
                    # Update current step
                    instance.current_step_id = step_id
                    await self.storage_manager.save_instance(instance)
                    
                    # Execute the step
                    task = asyncio.create_task(self._execute_step(instance_id, step, context))
                    tasks.append(task)
                
                # Wait for all steps in this batch to complete
                await asyncio.gather(*tasks)
                
                # Check if workflow was cancelled or failed
                instance = await self.storage_manager.get_instance(instance_id)
                if instance.status in [WorkflowStatus.CANCELLED, WorkflowStatus.FAILED]:
                    return
            
            # All steps completed successfully
            output_data = self._collect_output_data(instance)
            instance.output_data = output_data
            instance.status = WorkflowStatus.COMPLETED
            instance.end_time = datetime.now().isoformat()
            await self.storage_manager.save_instance(instance)
            
            # Publish workflow completed event
            await self.event_bus.publish("workflow_completed", {
                "instance_id": instance_id,
                "workflow_id": instance.workflow_id,
                "output_data": output_data
            })
            
        except Exception as e:
            logger.exception(f"Error executing workflow {instance_id}: {e}")
            await self._fail_workflow(instance_id, {
                "error": str(e),
                "traceback": logging.traceback.format_exc()
            })
    
    async def _execute_step(
        self, 
        instance_id: str, 
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> None:
        """Execute a single workflow step."""
        instance = await self.storage_manager.get_instance(instance_id)
        if not instance:
            return
        
        step_execution = instance.step_executions.get(step.id)
        if not step_execution:
            return
        
        # Check if all dependencies are satisfied
        for dep_id in step.depends_on:
            dep_execution = instance.step_executions.get(dep_id)
            if not dep_execution or dep_execution.status != StepStatus.COMPLETED:
                # Skip this step if dependencies are not met
                step_execution.status = StepStatus.SKIPPED
                await self.storage_manager.update_step_execution(
                    instance_id, step.id, StepStatus.SKIPPED
                )
                return
        
        # Prepare input data for the step
        input_data = self._prepare_step_input(step, instance)
        step_execution.input_data = input_data
        
        # Update step status to running
        step_execution.status = StepStatus.RUNNING
        step_execution.start_time = datetime.now().isoformat()
        await self.storage_manager.update_step_execution(
            instance_id, step.id, StepStatus.RUNNING
        )
        
        # Get the appropriate executor for this step type
        executor = self.step_executors.get(step.type)
        if not executor:
            await self.storage_manager.update_step_execution(
                instance_id, 
                step.id, 
                StepStatus.FAILED,
                error={"error": f"No executor found for step type: {step.type}"}
            )
            return
        
        # Execute the step with retry logic
        max_retries = step.retry_config.get("max_retries", 0)
        retry_delay = step.retry_config.get("retry_delay", 1)
        
        for attempt in range(max_retries + 1):
            try:
                # Execute the step
                output_data = await executor.execute(step, input_data, instance)
                
                # Update step status to completed
                step_execution.output_data = output_data
                step_execution.status = StepStatus.COMPLETED
                await self.storage_manager.update_step_execution(
                    instance_id, 
                    step.id, 
                    StepStatus.COMPLETED,
                    output_data=output_data
                )
                
                # Publish step completed event
                await self.event_bus.publish("step_completed", {
                    "instance_id": instance_id,
                    "workflow_id": instance.workflow_id,
                    "step_id": step.id,
                    "output_data": output_data
                })
                
                return
                
            except Exception as e:
                logger.error(f"Error executing step {step.id}: {e}")
                error_data = {
                    "error": str(e),
                    "attempt": attempt + 1,
                    "max_retries": max_retries
                }
                
                # Check if we should retry
                if attempt < max_retries:
                    step_execution.retry_count += 1
                    step_execution.logs.append({
                        "level": "error",
                        "message": f"Step failed, retrying ({attempt + 1}/{max_retries}): {e}",
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Wait before retrying
                    await asyncio.sleep(retry_delay)
                    continue
                
                # Max retries exceeded, handle the error
                step_execution.status = StepStatus.FAILED
                step_execution.error = error_data
                await self.storage_manager.update_step_execution(
                    instance_id, 
                    step.id, 
                    StepStatus.FAILED,
                    error=error_data
                )
                
                # Try to handle the error
                handled = await self._handle_step_error(instance_id, step, e)
                if not handled:
                    # If error wasn't handled, fail the workflow
                    await self._fail_workflow(instance_id, {
                        "error": f"Step {step.id} failed: {e}",
                        "step_id": step.id
                    })
                
                # Publish step failed event
                await self.event_bus.publish("step_failed", {
                    "instance_id": instance_id,
                    "workflow_id": instance.workflow_id,
                    "step_id": step.id,
                    "error": error_data,
                    "handled": handled
                })
    
    async def _handle_step_error(
        self, 
        instance_id: str, 
        step: WorkflowStep,
        error: Exception
    ) -> bool:
        """Handle an error that occurred during step execution."""
        # Get error handlers for this step
        error_handlers = step.error_handlers
        
        # If no specific handlers, get workflow-level handlers
        if not error_handlers:
            instance = await self.storage_manager.get_instance(instance_id)
            if not instance:
                return False
            
            definition = await self.storage_manager.get_definition(instance.workflow_id)
            if not definition:
                return False
            
            error_handlers = definition.error_handlers
        
        # Find a handler for this error type
        error_type = type(error).__name__
        handler = next(
            (h for h in error_handlers if h.error_type == error_type or h.error_type == "*"),
            None
        )
        
        if not handler:
            return False
        
        # Handle the error based on the action
        if handler.action == ErrorAction.SKIP:
            # Skip this step and continue
            return True
            
        elif handler.action == ErrorAction.NOTIFY:
            # Notify about the error but don't fail the workflow
            notification = handler.parameters.get("notification", {})
            await self.event_bus.publish("workflow_notification", {
                "instance_id": instance_id,
                "step_id": step.id,
                "notification_type": "error",
                "message": f"Error in step {step.id}: {error}",
                "notification": notification
            })
            return True
            
        elif handler.action == ErrorAction.ALTERNATE_PATH:
            # Take an alternate path in the workflow
            # This would require modifying the execution plan
            # Not implemented in this version
            return False
            
        # For other actions (RETRY is handled in _execute_step, FAIL is the default)
        return False
    
    async def _fail_workflow(self, instance_id: str, error: Dict[str, Any]) -> None:
        """Mark a workflow as failed."""
        await self.storage_manager.update_instance_status(
            instance_id, 
            WorkflowStatus.FAILED,
            error=error
        )
        
        # Publish workflow failed event
        instance = await self.storage_manager.get_instance(instance_id)
        if instance:
            await self.event_bus.publish("workflow_failed", {
                "instance_id": instance_id,
                "workflow_id": instance.workflow_id,
                "error": error
            })
    
    async def pause_workflow(self, instance_id: str) -> bool:
        """Pause a running workflow."""
        instance = await self.storage_manager.get_instance(instance_id)
        if not instance or instance.status != WorkflowStatus.RUNNING:
            return False
        
        # Update instance status
        await self.storage_manager.update_instance_status(instance_id, WorkflowStatus.PAUSED)
        
        # Publish workflow paused event
        await self.event_bus.publish("workflow_paused", {
            "instance_id": instance_id,
            "workflow_id": instance.workflow_id
        })
        
        return True
    
    async def resume_workflow(self, instance_id: str) -> bool:
        """Resume a paused workflow."""
        instance = await self.storage_manager.get_instance(instance_id)
        if not instance or instance.status != WorkflowStatus.PAUSED:
            return False
        
        # Update instance status
        await self.storage_manager.update_instance_status(instance_id, WorkflowStatus.RUNNING)
        
        # Restart the workflow execution
        context = {}  # In a real implementation, we would restore the context
        task = asyncio.create_task(self._execute_workflow(instance_id, context))
        self.active_workflows[instance_id] = task
        
        # Publish workflow resumed event
        await self.event_bus.publish("workflow_resumed", {
            "instance_id": instance_id,
            "workflow_id": instance.workflow_id
        })
        
        return True
    
    async def cancel_workflow(self, instance_id: str) -> bool:
        """Cancel a workflow execution."""
        instance = await self.storage_manager.get_instance(instance_id)
        if not instance or instance.status not in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            return False
        
        # Cancel the running task if it exists
        if instance_id in self.active_workflows:
            task = self.active_workflows[instance_id]
            if not task.done():
                task.cancel()
            
            del self.active_workflows[instance_id]
        
        # Update instance status
        await self.storage_manager.update_instance_status(instance_id, WorkflowStatus.CANCELLED)
        
        # Publish workflow cancelled event
        await self.event_bus.publish("workflow_cancelled", {
            "instance_id": instance_id,
            "workflow_id": instance.workflow_id
        })
        
        return True
    
    def _build_execution_plan(self, steps: List[WorkflowStep]) -> List[List[str]]:
        """Build an execution plan for the workflow steps."""
        # This is a simple topological sort implementation
        # In a real system, this would be more sophisticated
        
        # Create a dependency graph
        graph = {}
        for step in steps:
            graph[step.id] = set(step.depends_on)
        
        # Find steps with no dependencies
        def get_ready_steps():
            return [step_id for step_id, deps in graph.items() if not deps]
        
        # Build the execution plan
        execution_plan = []
        while graph:
            ready_steps = get_ready_steps()
            if not ready_steps:
                # Circular dependency detected
                raise ValueError("Circular dependency detected in workflow steps")
            
            execution_plan.append(ready_steps)
            
            # Remove completed steps from the graph
            for step_id in ready_steps:
                del graph[step_id]
            
            # Remove completed steps from dependencies
            for deps in graph.values():
                deps.difference_update(ready_steps)
        
        return execution_plan
    
    def _prepare_step_input(self, step: WorkflowStep, instance: WorkflowInstance) -> Dict[str, Any]:
        """Prepare input data for a workflow step."""
        input_data = {
            "workflow": {
                "id": instance.workflow_id,
                "instance_id": instance.id,
                "variables": instance.variables
            },
            "step": {
                "id": step.id,
                "type": step.type,
                "parameters": step.parameters
            },
            "input": instance.input_data
        }
        
        # Add output from completed steps
        input_data["steps"] = {}
        for step_id, step_execution in instance.step_executions.items():
            if step_execution.status == StepStatus.COMPLETED:
                input_data["steps"][step_id] = {
                    "output": step_execution.output_data
                }
        
        return input_data
    
    def _collect_output_data(self, instance: WorkflowInstance) -> Dict[str, Any]:
        """Collect output data from all completed steps."""
        output_data = {}
        
        for step_id, step_execution in instance.step_executions.items():
            if step_execution.status == StepStatus.COMPLETED:
                output_data[step_id] = step_execution.output_data
        
        return output_data
