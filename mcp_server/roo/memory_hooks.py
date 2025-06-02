"""
Memory integration hooks for Roo.

This module provides integration points between Roo modes and the MCP
working memory system, enabling efficient memory access patterns and
context preservation across mode transitions.
"""

import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .modes import get_mode
from .transitions import ModeTransitionManager

logger = logging.getLogger(__name__)

class OperationStatus(str, Enum):
    """Status of a boomerang operation."""

    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class OperationContext(BaseModel):
    """Context for a boomerang operation."""

    operation_id: str = Field(..., description="Unique identifier for this operation")
    initial_mode: str = Field(..., description="Slug of the initial mode")
    target_modes: List[str] = Field(..., description="List of mode slugs to transition through")
    current_mode_index: int = Field(default=0, description="Index of the current mode in target_modes")
    return_mode: str = Field(..., description="Slug of the mode to return to after completion")
    operation_data: Dict[str, Any] = Field(default_factory=dict, description="Data for the operation")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from each mode")
    status: OperationStatus = Field(default=OperationStatus.STARTED, description="Status of the operation")
    created_at: float = Field(
        default_factory=time.time,
        description="Timestamp when this operation was created",
    )
    updated_at: float = Field(
        default_factory=time.time,
        description="Timestamp when this operation was last updated",
    )
    memory_keys: List[str] = Field(
        default_factory=list,
        description="Keys of memory entries related to this operation",
    )

    def add_memory_key(self, key: str) -> None:
        """Add a memory key to track during the operation."""
        if key not in self.memory_keys:
            self.memory_keys.append(key)

    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a result from a mode."""
        self.results.append(result)
        self.updated_at = time.time()

    def update_status(self, status: OperationStatus) -> None:
        """Update the status of the operation."""
        self.status = status
        self.updated_at = time.time()

class BoomerangOperation:
    """
    Implements the boomerang pattern for complex operations that require
    multiple mode transitions with preserved context.

    The boomerang pattern allows an operation to transition through multiple
    modes and then return to the original mode, preserving context throughout
    the entire process.
    """

    def __init__(self, memory_manager, transition_manager: ModeTransitionManager):
        """
        Initialize the boomerang operation.

        Args:
            memory_manager: The memory manager to use for storing operation context
            transition_manager: The transition manager to use for mode transitions
        """
        self.memory_manager = memory_manager
        self.transition_manager = transition_manager
        self.active_operations: Dict[str, OperationContext] = {}

    async def start_operation(
        self,
        initial_mode: str,
        target_modes: List[str],
        operation_data: Dict[str, Any],
        return_mode: str,
    ) -> Optional[str]:
        """
        Start a complex operation that will transition through multiple modes
        and return to the original mode.

        Args:
            initial_mode: Slug of the initial mode
            target_modes: List of mode slugs to transition through
            operation_data: Data for the operation
            return_mode: Slug of the mode to return to after completion

        Returns:
            The operation ID if successful, None otherwise
        """
        # Validate modes
        if not get_mode(initial_mode) or not get_mode(return_mode):
            logger.error(f"Invalid mode: initial={initial_mode}, return={return_mode}")
            return None

        for mode_slug in target_modes:
            if not get_mode(mode_slug):
                logger.error(f"Invalid target mode: {mode_slug}")
                return None

        # Create operation ID
        operation_id = str(uuid.uuid4())

        # Create operation context
        context = OperationContext(
            operation_id=operation_id,
            initial_mode=initial_mode,
            target_modes=target_modes,
            return_mode=return_mode,
            operation_data=operation_data,
        )

        # Store in memory
        memory_key = f"boomerang:{operation_id}"
        try:
            await self.memory_manager.store(
                memory_key,
                context.dict(),
                "roo_boomerang",
                ttl_seconds=86400,  # 24 hour TTL for long operations
            )

            context.add_memory_key(memory_key)
            self.active_operations[operation_id] = context

            logger.info(f"Started boomerang operation {operation_id}")

            # Prepare first transition if there are target modes
            if target_modes:
                context.update_status(OperationStatus.IN_PROGRESS)
                first_target = target_modes[0]

                # Store updated context
                await self.memory_manager.store(memory_key, context.dict(), "roo_boomerang", ttl_seconds=86400)

                # Prepare transition
                await self.transition_manager.prepare_transition(
                    initial_mode,
                    first_target,
                    operation_id,
                    {
                        "memory_key": memory_key,
                        "step": 0,
                        "operation_type": "boomerang",
                        "operation_data": operation_data,
                    },
                )

            return operation_id
        except Exception as e:
            logger.error(f"Failed to start boomerang operation: {e}")
            return None

    async def advance_operation(self, operation_id: str, result: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Advance the operation to the next mode or complete it.

        Args:
            operation_id: ID of the operation to advance
            result: Result from the current mode

        Returns:
            The next transition details or None if complete or failed
        """
        # Retrieve operation context
        if operation_id in self.active_operations:
            context = self.active_operations[operation_id]
        else:
            # Try to retrieve from memory
            memory_key = f"boomerang:{operation_id}"
            try:
                stored_context = await self.memory_manager.retrieve(memory_key)
                if not stored_context:
                    logger.error(f"Operation not found: {operation_id}")
                    return None

                context = OperationContext(**stored_context)
                self.active_operations[operation_id] = context
            except Exception as e:
                logger.error(f"Failed to retrieve operation {operation_id}: {e}")
                return None

        # Add result from current step
        if result:
            context.add_result(result)

        # Update current mode index
        current_index = context.current_mode_index
        next_index = current_index + 1

        # Check if we've gone through all target modes
        if next_index >= len(context.target_modes):
            # Operation complete, return to original mode
            context.update_status(OperationStatus.COMPLETED)

            # Store updated context
            memory_key = f"boomerang:{operation_id}"
            try:
                await self.memory_manager.store(memory_key, context.dict(), "roo_boomerang", ttl_seconds=86400)

                # Store results separately for easier retrieval
                results_key = f"boomerang_results:{operation_id}"
                await self.memory_manager.store(
                    results_key,
                    {"results": context.results},
                    "roo_boomerang",
                    ttl_seconds=86400,
                )
                context.add_memory_key(results_key)

                # Prepare transition back to return mode
                current_mode = context.target_modes[current_index]
                transition_context = await self.transition_manager.prepare_transition(
                    current_mode,
                    context.return_mode,
                    operation_id,
                    {
                        "memory_key": memory_key,
                        "step": "final",
                        "complete": True,
                        "operation_type": "boomerang",
                        "results": context.results,
                    },
                )

                if not transition_context:
                    logger.error(f"Failed to prepare final transition for operation {operation_id}")
                    return None

                # Clean up
                if operation_id in self.active_operations:
                    del self.active_operations[operation_id]

                return {
                    "operation_id": operation_id,
                    "next_mode": context.return_mode,
                    "is_final": True,
                    "transition_id": transition_context.id,
                    "context": context.dict(),
                }
            except Exception as e:
                logger.error(f"Failed to complete operation {operation_id}: {e}")
                return None
        else:
            # Move to next mode
            context.current_mode_index = next_index

            # Store updated context
            memory_key = f"boomerang:{operation_id}"
            try:
                await self.memory_manager.store(memory_key, context.dict(), "roo_boomerang", ttl_seconds=86400)

                # Prepare transition to next mode
                current_mode = context.target_modes[current_index]
                next_mode = context.target_modes[next_index]

                # Include results from previous steps
                transition_data = {
                    "memory_key": memory_key,
                    "step": next_index,
                    "operation_type": "boomerang",
                    "previous_results": context.results,
                    "operation_data": context.operation_data,
                }

                transition_context = await self.transition_manager.prepare_transition(
                    current_mode, next_mode, operation_id, transition_data
                )

                if not transition_context:
                    logger.error(f"Failed to prepare transition for operation {operation_id}")
                    return None

                return {
                    "operation_id": operation_id,
                    "next_mode": next_mode,
                    "is_final": False,
                    "transition_id": transition_context.id,
                    "context": context.dict(),
                }
            except Exception as e:
                logger.error(f"Failed to advance operation {operation_id}: {e}")
                return None

    async def get_operation(self, operation_id: str) -> Optional[OperationContext]:
        """
        Get an operation by its ID.

        Args:
            operation_id: ID of the operation to retrieve

        Returns:
            The operation context if found, None otherwise
        """
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]

        # Try to retrieve from memory
        memory_key = f"boomerang:{operation_id}"
        try:
            stored_context = await self.memory_manager.retrieve(memory_key)
            if not stored_context:
                return None

            return OperationContext(**stored_context)
        except Exception as e:
            logger.error(f"Failed to retrieve operation {operation_id}: {e}")
            return None

    async def get_operation_results(self, operation_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the results of an operation.

        Args:
            operation_id: ID of the operation

        Returns:
            The operation results if found, None otherwise
        """
        # Try to retrieve from dedicated results key first
        results_key = f"boomerang_results:{operation_id}"
        try:
            stored_results = await self.memory_manager.retrieve(results_key)
            if stored_results and "results" in stored_results:
                return stored_results["results"]
        except Exception:
            pass

        # Fall back to retrieving from operation context
        operation = await self.get_operation(operation_id)
        if operation:
            return operation.results

        return None

class RooMemoryCategory(str, Enum):
    """Categories of memory entries related to Roo operations."""

    MODE_CONTEXT = "mode_context"
    TRANSITION = "transition"
    OPERATION = "operation"
    CODE_CHANGE = "code_change"
    ANALYSIS = "analysis"
    USER_PREFERENCE = "user_preference"

class RooMemoryManager:
    """
    Specialized memory manager for Roo operations that integrates
    with the MCP memory system.

    This class provides a higher-level interface for storing and retrieving
    Roo-specific memory entries, with specialized methods for different
    types of memory entries.
    """

    def __init__(self, base_memory_manager):
        """
        Initialize the Roo memory manager.

        Args:
            base_memory_manager: The base memory manager to use for storage
        """
        self.memory_manager = base_memory_manager

    async def store_mode_context(
        self, mode_slug: str, context_data: Dict[str, Any], ttl_seconds: int = 3600
    ) -> Optional[str]:
        """
        Store context data for a specific mode.

        Args:
            mode_slug: Slug of the mode
            context_data: Context data to store
            ttl_seconds: Time-to-live in seconds

        Returns:
            The memory key if successful, None otherwise
        """
        key = f"roo:mode:{mode_slug}:{int(time.time())}"

        metadata = {
            "category": RooMemoryCategory.MODE_CONTEXT.value,
            "mode": mode_slug,
            "timestamp": time.time(),
        }

        try:
            success = await self.memory_manager.store(
                key,
                {"content": context_data, "metadata": metadata},
                "roo_memory_manager",
                ttl_seconds,
            )
            return key if success else None
        except Exception as e:
            logger.error(f"Failed to store mode context: {e}")
            return None

    async def retrieve_mode_contexts(self, mode_slug: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent context data for a specific mode.

        Args:
            mode_slug: Slug of the mode
            limit: Maximum number of contexts to retrieve

        Returns:
            List of context data dictionaries
        """
        try:
            # This would use the search functionality of the base memory manager
            results = await self.memory_manager.search(f"roo:mode:{mode_slug}:", limit)
            return [r.get("content", {}) for r in results if isinstance(r, dict) and "content" in r]
        except Exception as e:
            logger.error(f"Failed to retrieve mode contexts: {e}")
            return []

    async def store_code_change(
        self,
        file_path: str,
        change_type: str,
        content: Dict[str, Any],
        mode_slug: str,
        ttl_seconds: int = 86400,
    ) -> Optional[str]:
        """
        Store information about a code change.

        Args:
            file_path: Path of the file that was changed
            change_type: Type of change (e.g., "create", "update", "delete")
            content: Content of the change
            mode_slug: Slug of the mode that made the change
            ttl_seconds: Time-to-live in seconds

        Returns:
            The memory key if successful, None otherwise
        """
        key = f"roo:code_change:{file_path}:{int(time.time())}"

        metadata = {
            "category": RooMemoryCategory.CODE_CHANGE.value,
            "file_path": file_path,
            "change_type": change_type,
            "mode": mode_slug,
            "timestamp": time.time(),
        }

        try:
            success = await self.memory_manager.store(
                key,
                {"content": content, "metadata": metadata},
                "roo_memory_manager",
                ttl_seconds,
            )
            return key if success else None
        except Exception as e:
            logger.error(f"Failed to store code change: {e}")
            return None

    async def get_recent_changes_for_file(self, file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent changes for a specific file.

        Args:
            file_path: Path of the file
            limit: Maximum number of changes to retrieve

        Returns:
            List of change dictionaries
        """
        try:
            results = await self.memory_manager.search(f"roo:code_change:{file_path}:", limit)
            return [
                {"content": r.get("content", {}), "metadata": r.get("metadata", {})}
                for r in results
                if isinstance(r, dict) and "content" in r and "metadata" in r
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve file changes: {e}")
            return []

    async def store_analysis(
        self,
        analysis_type: str,
        content: Dict[str, Any],
        mode_slug: str,
        ttl_seconds: int = 86400,
    ) -> Optional[str]:
        """
        Store an analysis result.

        Args:
            analysis_type: Type of analysis
            content: Content of the analysis
            mode_slug: Slug of the mode that performed the analysis
            ttl_seconds: Time-to-live in seconds

        Returns:
            The memory key if successful, None otherwise
        """
        key = f"roo:analysis:{analysis_type}:{int(time.time())}"

        metadata = {
            "category": RooMemoryCategory.ANALYSIS.value,
            "analysis_type": analysis_type,
            "mode": mode_slug,
            "timestamp": time.time(),
        }

        try:
            success = await self.memory_manager.store(
                key,
                {"content": content, "metadata": metadata},
                "roo_memory_manager",
                ttl_seconds,
            )
            return key if success else None
        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")
            return None

    async def get_recent_analyses(self, analysis_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent analyses.

        Args:
            analysis_type: Type of analysis to filter by (optional)
            limit: Maximum number of analyses to retrieve

        Returns:
            List of analysis dictionaries
        """
        search_key = f"roo:analysis:{analysis_type or ''}:"
        try:
            results = await self.memory_manager.search(search_key, limit)
            return [
                {"content": r.get("content", {}), "metadata": r.get("metadata", {})}
                for r in results
                if isinstance(r, dict) and "content" in r and "metadata" in r
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve analyses: {e}")
            return []

    async def store_user_preference(
        self, preference_type: str, value: Any, ttl_seconds: int = 2592000  # 30 days
    ) -> Optional[str]:
        """
        Store a user preference.

        Args:
            preference_type: Type of preference
            value: Value of the preference
            ttl_seconds: Time-to-live in seconds

        Returns:
            The memory key if successful, None otherwise
        """
        key = f"roo:user_preference:{preference_type}"

        metadata = {
            "category": RooMemoryCategory.USER_PREFERENCE.value,
            "preference_type": preference_type,
            "timestamp": time.time(),
        }

        try:
            success = await self.memory_manager.store(
                key,
                {"content": {"value": value}, "metadata": metadata},
                "roo_memory_manager",
                ttl_seconds,
            )
            return key if success else None
        except Exception as e:
            logger.error(f"Failed to store user preference: {e}")
            return None

    async def get_user_preference(self, preference_type: str, default_value: Any = None) -> Any:
        """
        Get a user preference.

        Args:
            preference_type: Type of preference
            default_value: Default value to return if preference not found

        Returns:
            The preference value if found, default_value otherwise
        """
        key = f"roo:user_preference:{preference_type}"
        try:
            result = await self.memory_manager.retrieve(key)
            if result and isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, dict) and "value" in content:
                    return content["value"]
        except Exception as e:
            logger.error(f"Failed to retrieve user preference: {e}")

        return default_value
