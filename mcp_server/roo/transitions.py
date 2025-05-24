"""
Mode transition logic for Roo.

This module provides the logic for transitioning between Roo modes,
preserving context and ensuring smooth handoffs between different
capabilities.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

from .modes import RooMode, get_mode

logger = logging.getLogger(__name__)


class TransitionContext(BaseModel):
    """Context information preserved during mode transitions."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this transition",
    )
    source_mode: str = Field(..., description="Slug of the source mode")
    target_mode: str = Field(..., description="Slug of the target mode")
    operation_id: str = Field(..., description="ID of the operation this transition is part of")
    timestamp: float = Field(
        default_factory=time.time,
        description="Timestamp when this transition was created",
    )
    memory_keys: List[str] = Field(
        default_factory=list,
        description="Keys of memory entries related to this transition",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for this transition")
    completed: bool = Field(default=False, description="Whether this transition has been completed")

    def add_memory_key(self, key: str) -> None:
        """Add a memory key to track during transition."""
        if key not in self.memory_keys:
            self.memory_keys.append(key)

    def mark_completed(self) -> None:
        """Mark this transition as completed."""
        self.completed = True
        self.metadata["completed_at"] = time.time()


class ModeTransitionManager:
    """
    Manages transitions between Roo modes with context preservation.

    This class handles the logic for transitioning between different Roo modes,
    ensuring that context is preserved and that transitions are valid according
    to the mode definitions.
    """

    def __init__(self, memory_manager):
        """
        Initialize the mode transition manager.

        Args:
            memory_manager: The memory manager to use for storing transition context
        """
        self.memory_manager = memory_manager
        self.active_transitions: Dict[str, TransitionContext] = {}

    async def prepare_transition(
        self,
        source_mode: str,
        target_mode: str,
        operation_id: str,
        context_data: Dict[str, Any] = None,
    ) -> Optional[TransitionContext]:
        """
        Prepare for a mode transition by preserving context.

        Args:
            source_mode: Slug of the source mode
            target_mode: Slug of the target mode
            operation_id: ID of the operation this transition is part of
            context_data: Additional context data to preserve

        Returns:
            The transition context if successful, None otherwise
        """
        source = get_mode(source_mode)
        target = get_mode(target_mode)

        if not source or not target:
            logger.error(f"Invalid mode: source={source_mode}, target={target_mode}")
            return None

        if target_mode not in source.can_transition_to:
            logger.error(f"Invalid transition: {source_mode} -> {target_mode}")
            return None

        # Create transition context
        context = TransitionContext(
            source_mode=source_mode,
            target_mode=target_mode,
            operation_id=operation_id,
            metadata=context_data or {},
        )

        # Store in memory for retrieval
        memory_key = f"transition:{context.id}"
        try:
            await self.memory_manager.store(
                memory_key,
                context.dict(),
                "roo_transition_manager",
                ttl_seconds=3600,  # 1 hour TTL
            )

            context.add_memory_key(memory_key)
            self.active_transitions[context.id] = context

            logger.info(f"Prepared transition {context.id}: {source_mode} -> {target_mode}")
            return context
        except Exception as e:
            logger.error(f"Failed to prepare transition: {e}")
            return None

    async def complete_transition(
        self, transition_id: str, result_data: Dict[str, Any] = None
    ) -> Optional[TransitionContext]:
        """
        Complete a mode transition and update context with results.

        Args:
            transition_id: ID of the transition to complete
            result_data: Results of the operation in the target mode

        Returns:
            The updated transition context if successful, None otherwise
        """
        if transition_id in self.active_transitions:
            context = self.active_transitions[transition_id]
        else:
            # Try to retrieve from memory
            memory_key = f"transition:{transition_id}"
            try:
                stored_context = await self.memory_manager.retrieve(memory_key)
                if not stored_context:
                    logger.error(f"Transition not found: {transition_id}")
                    return None

                context = TransitionContext(**stored_context)
            except Exception as e:
                logger.error(f"Failed to retrieve transition {transition_id}: {e}")
                return None

        # Update context with results
        if result_data:
            context.metadata.update(result_data)

        # Mark as completed
        context.mark_completed()

        # Store updated context
        memory_key = f"transition_result:{transition_id}"
        try:
            await self.memory_manager.store(
                memory_key,
                context.dict(),
                "roo_transition_manager",
                ttl_seconds=3600,  # 1 hour TTL
            )

            context.add_memory_key(memory_key)

            # Update original transition record
            original_key = f"transition:{transition_id}"
            await self.memory_manager.store(
                original_key,
                context.dict(),
                "roo_transition_manager",
                ttl_seconds=3600,  # 1 hour TTL
            )

            logger.info(f"Completed transition {transition_id}")

            # Clean up
            if transition_id in self.active_transitions:
                del self.active_transitions[transition_id]

            return context
        except Exception as e:
            logger.error(f"Failed to complete transition {transition_id}: {e}")
            return None

    async def get_transition(self, transition_id: str) -> Optional[TransitionContext]:
        """
        Get a transition by its ID.

        Args:
            transition_id: ID of the transition to retrieve

        Returns:
            The transition context if found, None otherwise
        """
        if transition_id in self.active_transitions:
            return self.active_transitions[transition_id]

        # Try to retrieve from memory
        memory_key = f"transition:{transition_id}"
        try:
            stored_context = await self.memory_manager.retrieve(memory_key)
            if not stored_context:
                return None

            return TransitionContext(**stored_context)
        except Exception as e:
            logger.error(f"Failed to retrieve transition {transition_id}: {e}")
            return None

    async def get_active_transitions(self) -> List[TransitionContext]:
        """
        Get all active transitions.

        Returns:
            List of active transition contexts
        """
        return list(self.active_transitions.values())

    async def get_transitions_for_operation(self, operation_id: str) -> List[TransitionContext]:
        """
        Get all transitions for a specific operation.

        Args:
            operation_id: ID of the operation

        Returns:
            List of transition contexts for the operation
        """
        # First check active transitions
        transitions = [t for t in self.active_transitions.values() if t.operation_id == operation_id]

        # Then search in memory
        try:
            # This would ideally use a more efficient query mechanism
            # For now, we'll just use a simple search
            results = await self.memory_manager.search(f"transition:.*:{operation_id}", limit=100)
            for result in results:
                if isinstance(result, dict) and "content" in result:
                    try:
                        transition = TransitionContext(**result["content"])
                        if transition.id not in [t.id for t in transitions]:
                            transitions.append(transition)
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Failed to search for transitions: {e}")

        return transitions
