"""
Base workflow abstractions for Orchestra AI.

This module provides interfaces for defining and executing workflows
with support for parallel execution, dependencies, and error handling.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from core.services.events.event_bus import Event, get_event_bus

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Task execution priority."""

    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """Definition of a workflow task."""

    id: str
    name: str
    handler: Callable
    dependencies: Set[str] = field(default_factory=set)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)


@dataclass
class WorkflowContext:
    """Context passed through workflow execution."""

    workflow_id: UUID
    inputs: Dict[str, Any]
    outputs: Dict[str, Any] = field(default_factory=dict)
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_task_output(self, task_id: str) -> Any:
        """Get output from a completed task."""
        result = self.task_results.get(task_id)
        if result and result.status == TaskStatus.COMPLETED:
            return result.output
        return None

    def set_output(self, key: str, value: Any) -> None:
        """Set a workflow output value."""
        self.outputs[key] = value


class Task(ABC):
    """Abstract base class for workflow tasks."""

    @abstractmethod
    async def execute(self, context: WorkflowContext) -> Any:
        """Execute the task with given context."""
        pass

    @abstractmethod
    def validate_inputs(self, context: WorkflowContext) -> bool:
        """Validate task inputs from context."""
        pass


class Workflow:
    """Workflow definition and execution logic."""

    def __init__(self, name: str, description: str = ""):
        self.id = uuid4()
        self.name = name
        self.description = description
        self.tasks: Dict[str, TaskDefinition] = {}
        self._event_bus = get_event_bus()

    def add_task(
        self,
        task_id: str,
        name: str,
        handler: Callable,
        dependencies: Optional[List[str]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: Optional[int] = None,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a task to the workflow."""
        task_def = TaskDefinition(
            id=task_id,
            name=name,
            handler=handler,
            dependencies=set(dependencies or []),
            priority=priority,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            metadata=metadata or {},
        )

        # Validate dependencies exist
        for dep_id in task_def.dependencies:
            if dep_id not in self.tasks:
                raise ValueError(f"Dependency '{dep_id}' not found in workflow")

        self.tasks[task_id] = task_def

    def get_execution_order(self) -> List[List[str]]:
        """Get tasks organized by execution levels (parallel groups)."""
        levels = []
        completed = set()

        while len(completed) < len(self.tasks):
            level = []

            for task_id, task in self.tasks.items():
                if task_id in completed:
                    continue

                # Check if all dependencies are completed
                if task.dependencies.issubset(completed):
                    level.append(task_id)

            if not level:
                # Circular dependency detected
                remaining = set(self.tasks.keys()) - completed
                raise ValueError(f"Circular dependency detected in tasks: {remaining}")

            levels.append(level)
            completed.update(level)

        return levels

    async def execute(self, inputs: Dict[str, Any]) -> WorkflowContext:
        """Execute the workflow with given inputs."""
        context = WorkflowContext(workflow_id=self.id, inputs=inputs)

        # Emit workflow started event
        await self._event_bus.publish(
            Event(
                type="workflow.started",
                data={
                    "workflow_id": str(self.id),
                    "workflow_name": self.name,
                    "inputs": inputs,
                },
            )
        )

        try:
            # Get execution order
            execution_levels = self.get_execution_order()

            # Execute tasks level by level
            for level in execution_levels:
                # Sort tasks in level by priority
                sorted_tasks = sorted(level, key=lambda tid: self.tasks[tid].priority.value, reverse=True)

                # Execute tasks in parallel within each level
                await self._execute_level(sorted_tasks, context)

            # Emit workflow completed event
            await self._event_bus.publish(
                Event(
                    type="workflow.completed",
                    data={
                        "workflow_id": str(self.id),
                        "workflow_name": self.name,
                        "outputs": context.outputs,
                    },
                )
            )

        except Exception as e:
            # Emit workflow failed event
            await self._event_bus.publish(
                Event(
                    type="workflow.failed",
                    data={
                        "workflow_id": str(self.id),
                        "workflow_name": self.name,
                        "error": str(e),
                    },
                )
            )
            raise

        return context

    async def _execute_level(self, task_ids: List[str], context: WorkflowContext) -> None:
        """Execute tasks in parallel."""
        tasks = []

        for task_id in task_ids:
            task_def = self.tasks[task_id]
            task_coro = self._execute_task(task_def, context)
            tasks.append(task_coro)

        # Execute all tasks in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_task(self, task_def: TaskDefinition, context: WorkflowContext) -> None:
        """Execute a single task with retry logic."""
        attempts = 0
        max_attempts = task_def.retry_count + 1

        while attempts < max_attempts:
            try:
                # Create task result
                result = TaskResult(
                    task_id=task_def.id,
                    status=TaskStatus.RUNNING,
                    started_at=datetime.utcnow(),
                )

                # Emit task started event
                await self._event_bus.publish(
                    Event(
                        type="task.started",
                        data={
                            "workflow_id": str(context.workflow_id),
                            "task_id": task_def.id,
                            "task_name": task_def.name,
                            "attempt": attempts + 1,
                        },
                    )
                )

                # Execute with timeout if specified
                if task_def.timeout_seconds:
                    output = await asyncio.wait_for(task_def.handler(context), timeout=task_def.timeout_seconds)
                else:
                    output = await task_def.handler(context)

                # Update result
                result.status = TaskStatus.COMPLETED
                result.output = output
                result.completed_at = datetime.utcnow()

                # Store result in context
                context.task_results[task_def.id] = result

                # Emit task completed event
                await self._event_bus.publish(
                    Event(
                        type="task.completed",
                        data={
                            "workflow_id": str(context.workflow_id),
                            "task_id": task_def.id,
                            "task_name": task_def.name,
                            "output": output,
                        },
                    )
                )

                return

            except asyncio.TimeoutError:
                error_msg = f"Task '{task_def.name}' timed out after {task_def.timeout_seconds}s"
                logger.error(error_msg)

                result.status = TaskStatus.FAILED
                result.error = error_msg
                result.completed_at = datetime.utcnow()

                attempts += 1

                if attempts >= max_attempts:
                    context.task_results[task_def.id] = result
                    await self._emit_task_failed(task_def, context, error_msg)
                    raise

            except Exception as e:
                error_msg = f"Task '{task_def.name}' failed: {str(e)}"
                logger.error(error_msg, exc_info=True)

                result.status = TaskStatus.FAILED
                result.error = error_msg
                result.completed_at = datetime.utcnow()

                attempts += 1

                if attempts >= max_attempts:
                    context.task_results[task_def.id] = result
                    await self._emit_task_failed(task_def, context, error_msg)
                    raise

                # Wait before retry
                await asyncio.sleep(2**attempts)  # Exponential backoff

    async def _emit_task_failed(self, task_def: TaskDefinition, context: WorkflowContext, error: str) -> None:
        """Emit task failed event."""
        await self._event_bus.publish(
            Event(
                type="task.failed",
                data={
                    "workflow_id": str(context.workflow_id),
                    "task_id": task_def.id,
                    "task_name": task_def.name,
                    "error": error,
                },
            )
        )


class WorkflowEngine:
    """Engine for managing and executing workflows."""

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._running_workflows: Dict[UUID, WorkflowContext] = {}
        self._event_bus = get_event_bus()

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow with the engine."""
        self._workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get a registered workflow by name."""
        return self._workflows.get(name)

    def list_workflows(self) -> List[str]:
        """List all registered workflow names."""
        return list(self._workflows.keys())

    async def execute_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> WorkflowContext:
        """Execute a workflow by name."""
        workflow = self._workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found")

        # Execute workflow
        context = await workflow.execute(inputs)

        # Track running workflow
        self._running_workflows[context.workflow_id] = context

        return context

    def get_workflow_status(self, workflow_id: UUID) -> Optional[WorkflowContext]:
        """Get the status of a running workflow."""
        return self._running_workflows.get(workflow_id)

    async def cancel_workflow(self, workflow_id: UUID) -> bool:
        """Cancel a running workflow."""
        context = self._running_workflows.get(workflow_id)
        if not context:
            return False

        # Emit cancellation event
        await self._event_bus.publish(Event(type="workflow.cancelled", data={"workflow_id": str(workflow_id)}))

        # Remove from running workflows
        del self._running_workflows[workflow_id]

        return True


# Global workflow engine instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance."""
    global _workflow_engine

    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()

    return _workflow_engine
