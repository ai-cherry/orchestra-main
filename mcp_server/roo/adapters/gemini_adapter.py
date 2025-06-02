"""
Gemini adapter for Roo integration with MCP.

This module provides an adapter for integrating Gemini with Roo and MCP,
enabling memory access and mode transitions for Gemini-based agents.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from ..memory_hooks import BoomerangOperation, RooMemoryManager
from ..modes import get_mode
from ..rules import RuleEngine, create_rule_engine
from ..transitions import ModeTransitionManager

logger = logging.getLogger(__name__)

class GeminiRooAdapter:
    """
    Adapter for integrating Gemini with Roo and MCP.

    This class provides methods for handling Gemini requests and responses,
    integrating with the Roo mode system and MCP memory.
    """

    def __init__(
        self,
        memory_manager,
        transition_manager: Optional[ModeTransitionManager] = None,
        rule_engine: Optional[RuleEngine] = None,
    ):
        """
        Initialize the Gemini Roo adapter.

        Args:
            memory_manager: The memory manager to use
            transition_manager: The transition manager to use (optional)
            rule_engine: The rule engine to use (optional)
        """
        self.memory_manager = memory_manager
        self.roo_memory = RooMemoryManager(memory_manager)

        # Create managers if not provided
        if transition_manager is None:
            self.transition_manager = ModeTransitionManager(memory_manager)
        else:
            self.transition_manager = transition_manager

        if rule_engine is None:
            self.rule_engine = create_rule_engine()
        else:
            self.rule_engine = rule_engine

        self.boomerang = BoomerangOperation(memory_manager, self.transition_manager)

    async def prepare_context(self, mode_slug: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare context for a Gemini request based on the current mode.

        Args:
            mode_slug: The slug of the current mode
            request_data: The request data from the client

        Returns:
            Dictionary of context data to include in the request
        """
        mode = get_mode(mode_slug)
        if not mode:
            logger.error(f"Invalid mode: {mode_slug}")
            return {}

        context = {
            "mode": mode.dict(),
            "timestamp": time.time(),
            "request_id": request_data.get("request_id", ""),
        }

        # Check for transition context
        transition_id = request_data.get("transition_id")
        if transition_id:
            transition = await self.transition_manager.get_transition(transition_id)
            if transition:
                context["transition"] = transition.dict()

                # Include operation context if this is part of a boomerang operation
                if transition.metadata.get("operation_type") == "boomerang":
                    operation_id = transition.operation_id
                    operation = await self.boomerang.get_operation(operation_id)
                    if operation:
                        context["operation"] = operation.dict()

        # Include recent mode contexts
        recent_contexts = await self.roo_memory.retrieve_mode_contexts(mode_slug, limit=3)
        if recent_contexts:
            context["recent_contexts"] = recent_contexts

        # Apply rules
        rule_context = {
            "mode_slug": mode_slug,
            "request_type": request_data.get("type", ""),
            "has_transition": transition_id is not None,
        }

        rule_results = self.rule_engine.evaluate(rule_context)
        if rule_results:
            context["rules"] = rule_results

        return context

    async def process_request(self, mode_slug: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Gemini request.

        Args:
            mode_slug: The slug of the current mode
            request_data: The request data from the client

        Returns:
            Dictionary of processed request data
        """
        # Prepare context
        context = await self.prepare_context(mode_slug, request_data)

        # Store mode context
        await self.roo_memory.store_mode_context(mode_slug, {"request": request_data, "context": context})

        # Add context to request
        processed_request = {**request_data, "context": context}

        return processed_request

    async def process_response(
        self,
        mode_slug: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a Gemini response.

        Args:
            mode_slug: The slug of the current mode
            request_data: The original request data
            response_data: The response data from Gemini

        Returns:
            Dictionary of processed response data
        """
        # Check for mode transition request
        if "mode_transition" in response_data:
            transition_request = response_data["mode_transition"]
            target_mode = transition_request.get("target_mode")

            if target_mode and get_mode(target_mode):
                # Prepare transition
                transition = await self.transition_manager.prepare_transition(
                    mode_slug,
                    target_mode,
                    request_data.get("request_id", ""),
                    {
                        "reason": transition_request.get("reason", ""),
                        "context_data": transition_request.get("context_data", {}),
                    },
                )

                if transition:
                    response_data["transition"] = {
                        "id": transition.id,
                        "source_mode": mode_slug,
                        "target_mode": target_mode,
                        "success": True,
                    }
                else:
                    response_data["transition"] = {
                        "source_mode": mode_slug,
                        "target_mode": target_mode,
                        "success": False,
                        "error": "Failed to prepare transition",
                    }

        # Check for boomerang operation completion
        if "complete_operation" in response_data:
            operation_data = response_data["complete_operation"]
            operation_id = operation_data.get("operation_id")

            if operation_id:
                result = await self.boomerang.advance_operation(operation_id, operation_data.get("result", {}))

                if result:
                    response_data["operation_result"] = result

        # Check for code changes
        if "code_changes" in response_data:
            changes = response_data["code_changes"]
            for change in changes:
                file_path = change.get("file_path")
                change_type = change.get("type")

                if file_path and change_type:
                    await self.roo_memory.store_code_change(file_path, change_type, change, mode_slug)

        # Store response in memory
        await self.roo_memory.store_mode_context(mode_slug, {"request": request_data, "response": response_data})

        return response_data

    async def handle_mode_transition(self, transition_id: str, result_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle a completed mode transition.

        Args:
            transition_id: ID of the completed transition
            result_data: Results from the target mode

        Returns:
            Dictionary with transition completion status
        """
        transition = await self.transition_manager.complete_transition(transition_id, result_data)

        if not transition:
            return {"success": False, "error": "Transition not found"}

        return {"success": True, "transition": transition.dict()}

    async def start_boomerang_operation(
        self,
        initial_mode: str,
        target_modes: List[str],
        operation_data: Dict[str, Any],
        return_mode: str,
    ) -> Dict[str, Any]:
        """
        Start a boomerang operation.

        Args:
            initial_mode: Slug of the initial mode
            target_modes: List of mode slugs to transition through
            operation_data: Data for the operation
            return_mode: Slug of the mode to return to after completion

        Returns:
            Dictionary with operation status
        """
        operation_id = await self.boomerang.start_operation(initial_mode, target_modes, operation_data, return_mode)

        if not operation_id:
            return {"success": False, "error": "Failed to start operation"}

        return {"success": True, "operation_id": operation_id}

    async def get_file_history(self, file_path: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the history of changes for a file.

        Args:
            file_path: Path of the file
            limit: Maximum number of changes to retrieve

        Returns:
            List of change dictionaries
        """
        return await self.roo_memory.get_recent_changes_for_file(file_path, limit)
