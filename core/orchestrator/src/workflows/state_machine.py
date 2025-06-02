"""
Workflow State Machine for AI Orchestration System.

This module provides a state machine implementation for managing complex
workflows involving multiple agents and steps.
"""

import asyncio
import logging
import time
import uuid
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

# Handle both pydantic v1 and v2
try:
    from pydantic.v1 import BaseModel, Field  # For pydantic v2
except ImportError:
    from pydantic import BaseModel, Field  # For pydantic v1

from core.orchestrator.src.services.event_bus import get_event_bus

# Configure logging
logger = logging.getLogger(__name__)

class WorkflowState(str, Enum):
    """States for a workflow"""

    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowTransition(BaseModel):
    """Transition between workflow states"""

    from_state: WorkflowState
    to_state: WorkflowState
    condition_name: Optional[str] = None
    action_name: Optional[str] = None

class WorkflowDefinition(BaseModel):
    """Definition of a workflow"""

    workflow_id: str
    name: str
    description: Optional[str] = None
    initial_state: WorkflowState = WorkflowState.CREATED
    states: List[WorkflowState]
    transitions: List[WorkflowTransition]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowInstance(BaseModel):
    """Instance of a running workflow"""

    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    current_state: WorkflowState
    context: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowEngine:
    """Engine for executing workflows"""

    def __init__(self):
        """Initialize the workflow engine."""
        self._event_bus = get_event_bus()
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._instances: Dict[str, WorkflowInstance] = {}
        self._conditions: Dict[str, Callable[[Dict[str, Any]], bool]] = {}
        self._actions: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}
        self._active_instances: Set[str] = set()
        self._processing_task = None
        logger.info("WorkflowEngine initialized")

    def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """
        Register a workflow definition.

        Args:
            workflow: The workflow definition

        Returns:
            The workflow ID
        """
        self._workflows[workflow.workflow_id] = workflow
        logger.info(f"Workflow registered: {workflow.name} ({workflow.workflow_id})")
        return workflow.workflow_id

    def register_condition(self, name: str, condition: Callable[[Dict[str, Any]], bool]):
        """
        Register a condition function.

        Args:
            name: The condition name
            condition: Function that evaluates a condition
        """
        self._conditions[name] = condition
        logger.debug(f"Condition registered: {name}")

    def register_action(self, name: str, action: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """
        Register an action function.

        Args:
            name: The action name
            action: Async function that performs an action
        """
        self._actions[name] = action
        logger.debug(f"Action registered: {name}")

    async def create_instance(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """
        Create a new instance of a workflow.

        Args:
            workflow_id: The workflow definition ID
            context: Initial context for the workflow

        Returns:
            The instance ID

        Raises:
            ValueError: If the workflow ID is unknown
        """
        if workflow_id not in self._workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")

        workflow = self._workflows[workflow_id]

        instance = WorkflowInstance(
            workflow_id=workflow_id,
            current_state=workflow.initial_state,
            context=context or {},
        )

        self._instances[instance.instance_id] = instance

        # Publish event
        try:
            await self._event_bus.publish_async(
                "workflow_instance_created",
                {
                    "instance_id": instance.instance_id,
                    "workflow_id": workflow_id,
                    "initial_state": workflow.initial_state,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish workflow_instance_created event: {e}")

        return instance.instance_id

    async def start_instance(self, instance_id: str) -> WorkflowState:
        """
        Start a workflow instance.

        Args:
            instance_id: The instance ID

        Returns:
            The new state of the instance

        Raises:
            ValueError: If the instance ID is unknown
        """
        if instance_id not in self._instances:
            raise ValueError(f"Unknown workflow instance: {instance_id}")

        instance = self._instances[instance_id]

        # Add to active instances
        self._active_instances.add(instance_id)

        # Transition to RUNNING state if in CREATED state
        if instance.current_state == WorkflowState.CREATED:
            await self._transition_state(instance_id, WorkflowState.CREATED, WorkflowState.RUNNING)

        # Start processing the instance
        return await self._process_instance(instance_id)

    async def _transition_state(self, instance_id: str, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        """
        Transition an instance from one state to another.

        Args:
            instance_id: The instance ID
            from_state: The expected current state
            to_state: The new state

        Returns:
            True if the transition was successful
        """
        instance = self._instances[instance_id]

        # Check current state
        if instance.current_state != from_state:
            logger.warning(
                f"Cannot transition instance {instance_id} from {from_state} to {to_state}: "
                f"current state is {instance.current_state}"
            )
            return False

        # Update state
        old_state = instance.current_state
        instance.current_state = to_state
        instance.updated_at = time.time()

        # Update completed_at if terminal state
        if to_state in [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        ]:
            instance.completed_at = time.time()

        # Add to history
        instance.history.append({"from_state": old_state, "to_state": to_state, "timestamp": time.time()})

        # Publish event
        try:
            await self._event_bus.publish_async(
                "workflow_state_changed",
                {
                    "instance_id": instance_id,
                    "from_state": old_state,
                    "to_state": to_state,
                    "workflow_id": instance.workflow_id,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish workflow_state_changed event: {e}")

        return True

    async def _process_instance(self, instance_id: str) -> WorkflowState:
        """
        Process a workflow instance.

        Args:
            instance_id: The instance ID

        Returns:
            The final state of the instance
        """
        instance = self._instances[instance_id]
        workflow = self._workflows[instance.workflow_id]

        # Find valid transitions from current state
        valid_transitions = [t for t in workflow.transitions if t.from_state == instance.current_state]

        # Try each transition
        for transition in valid_transitions:
            # Check condition if specified
            if transition.condition_name:
                if transition.condition_name not in self._conditions:
                    logger.warning(f"Unknown condition: {transition.condition_name}")
                    continue

                condition_func = self._conditions[transition.condition_name]
                if not condition_func(instance.context):
                    # Condition not met
                    continue

            # Execute action if specified
            if transition.action_name:
                if transition.action_name not in self._actions:
                    logger.warning(f"Unknown action: {transition.action_name}")
                    continue

                action_func = self._actions[transition.action_name]
                try:
                    # Execute the action
                    result = await action_func(instance.context)

                    # Update context with action result
                    instance.context.update(result)
                except Exception as e:
                    # Record error and transition to FAILED state
                    instance.context["error"] = str(e)
                    await self._transition_state(instance_id, instance.current_state, WorkflowState.FAILED)

                    # Publish error event
                    try:
                        await self._event_bus.publish_async(
                            "workflow_action_failed",
                            {
                                "instance_id": instance_id,
                                "action": transition.action_name,
                                "error": str(e),
                            },
                        )
                    except Exception as event_error:
                        logger.warning(f"Failed to publish workflow_action_failed event: {event_error}")

                    return WorkflowState.FAILED

            # Perform the transition
            success = await self._transition_state(instance_id, instance.current_state, transition.to_state)

            if success:
                # If transitioned to a non-terminal state, continue processing
                if transition.to_state not in [
                    WorkflowState.COMPLETED,
                    WorkflowState.FAILED,
                    WorkflowState.CANCELLED,
                    WorkflowState.WAITING,
                ]:
                    return await self._process_instance(instance_id)

                # If waiting, add to active instances but don't process further
                if transition.to_state == WorkflowState.WAITING:
                    self._active_instances.add(instance_id)
                else:
                    # Terminal state, remove from active instances
                    self._active_instances.discard(instance_id)

                return transition.to_state

        # No valid transition found
        return instance.current_state

    async def resume_instance(self, instance_id: str) -> WorkflowState:
        """
        Resume a waiting workflow instance.

        Args:
            instance_id: The instance ID

        Returns:
            The new state of the instance

        Raises:
            ValueError: If the instance ID is unknown or not in WAITING state
        """
        if instance_id not in self._instances:
            raise ValueError(f"Unknown workflow instance: {instance_id}")

        instance = self._instances[instance_id]

        if instance.current_state != WorkflowState.WAITING:
            raise ValueError(f"Cannot resume instance {instance_id}: not in WAITING state")

        # Transition to RUNNING state
        await self._transition_state(instance_id, WorkflowState.WAITING, WorkflowState.RUNNING)

        # Process the instance
        return await self._process_instance(instance_id)

    async def cancel_instance(self, instance_id: str) -> bool:
        """
        Cancel a workflow instance.

        Args:
            instance_id: The instance ID

        Returns:
            True if the instance was cancelled

        Raises:
            ValueError: If the instance ID is unknown
        """
        if instance_id not in self._instances:
            raise ValueError(f"Unknown workflow instance: {instance_id}")

        instance = self._instances[instance_id]

        # Only cancel if not already in a terminal state
        if instance.current_state in [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        ]:
            return False

        # Transition to CANCELLED state
        success = await self._transition_state(instance_id, instance.current_state, WorkflowState.CANCELLED)

        if success:
            # Remove from active instances
            self._active_instances.discard(instance_id)

        return success

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """
        Get a workflow instance.

        Args:
            instance_id: The instance ID

        Returns:
            The workflow instance or None if not found
        """
        return self._instances.get(instance_id)

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        Get a workflow definition.

        Args:
            workflow_id: The workflow ID

        Returns:
            The workflow definition or None if not found
        """
        return self._workflows.get(workflow_id)

    async def start_processing(self):
        """Start background processing of workflow instances."""
        if self._processing_task is not None:
            return

        self._processing_task = asyncio.create_task(self._process_workflows())
        logger.info("Workflow processing started")

    async def stop_processing(self):
        """Stop background processing of workflow instances."""
        if self._processing_task is None:
            return

        self._processing_task.cancel()
        try:
            await self._processing_task
        except asyncio.CancelledError:
            pass
        self._processing_task = None
        logger.info("Workflow processing stopped")

    async def _process_workflows(self):
        """Background task to process workflow instances."""
        while True:
            try:
                # Process each active instance
                active_instances = list(self._active_instances)
                for instance_id in active_instances:
                    if instance_id in self._instances:
                        instance = self._instances[instance_id]

                        # Only process RUNNING instances
                        if instance.current_state == WorkflowState.RUNNING:
                            await self._process_instance(instance_id)

                # Sleep before next cycle
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing workflows: {e}")
                await asyncio.sleep(5.0)  # Longer sleep on error

# Singleton instance
_workflow_engine = None

def get_workflow_engine() -> WorkflowEngine:
    """
    Get the global workflow engine instance.

    Returns:
        The global WorkflowEngine instance
    """
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = WorkflowEngine()
    return _workflow_engine
