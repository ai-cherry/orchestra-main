"""
"""
    """States for a workflow"""
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowTransition(BaseModel):
    """Transition between workflow states"""
    """Definition of a workflow"""
    """Instance of a running workflow"""
    """Engine for executing workflows"""
        """Initialize the workflow engine."""
        logger.info("WorkflowEngine initialized")

    def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """
        """
        logger.info(f"Workflow registered: {workflow.name} ({workflow.workflow_id})")
        return workflow.workflow_id

    def register_condition(self, name: str, condition: Callable[[Dict[str, Any]], bool]):
        """
        """

    def register_action(self, name: str, action: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]):
        """
        """

    async def create_instance(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """
        """
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

            pass
            await self._event_bus.publish_async(
                "workflow_instance_created",
                {
                    "instance_id": instance.instance_id,
                    "workflow_id": workflow_id,
                    "initial_state": workflow.initial_state,
                },
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish workflow_instance_created event: {e}")

        return instance.instance_id

    async def start_instance(self, instance_id: str) -> WorkflowState:
        """
        """
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
        """
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

            pass
            await self._event_bus.publish_async(
                "workflow_state_changed",
                {
                    "instance_id": instance_id,
                    "from_state": old_state,
                    "to_state": to_state,
                    "workflow_id": instance.workflow_id,
                },
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish workflow_state_changed event: {e}")

        return True

    async def _process_instance(self, instance_id: str) -> WorkflowState:
        """
        """
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

                    pass
                    # Execute the action
                    result = await action_func(instance.context)

                    # Update context with action result
                    instance.context.update(result)
                except Exception:

                    pass
                    # Record error and transition to FAILED state
                    instance.context["error"] = str(e)
                    await self._transition_state(instance_id, instance.current_state, WorkflowState.FAILED)

                    # Publish error event
                    try:

                        pass
                        await self._event_bus.publish_async(
                            "workflow_action_failed",
                            {
                                "instance_id": instance_id,
                                "action": transition.action_name,
                                "error": str(e),
                            },
                        )
                    except Exception:

                        pass
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
        """
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
        """
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
        """
        """
        """
        """Start background processing of workflow instances."""
        logger.info("Workflow processing started")

    async def stop_processing(self):
        """Stop background processing of workflow instances."""
        logger.info("Workflow processing stopped")

    async def _process_workflows(self):
        """Background task to process workflow instances."""
                logger.error(f"Error processing workflows: {e}")
                await asyncio.sleep(5.0)  # Longer sleep on error

# Singleton instance
_workflow_engine = None

def get_workflow_engine() -> WorkflowEngine:
    """
    """