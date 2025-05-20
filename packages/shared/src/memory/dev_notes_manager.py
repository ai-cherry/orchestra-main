"""
Development Notes Manager for AI Orchestration System.

This module provides a specialized manager for development notes,
enabling structured storage and retrieval of technical context,
architecture decisions, and implementation details.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

from packages.shared.src.memory.memory_manager import MemoryManager, MemoryHealth
from packages.shared.src.models.base_models import AgentData
from packages.shared.src.models.metadata_schemas import (
    DevNoteMetadata,
    DevNoteType,
    MetadataValidationError,
    add_standard_metadata_fields,
    validate_dev_note_metadata,
)
from packages.shared.src.storage.config import (
    AGENT_DATA_COLLECTION,
    DEV_NOTES_COLLECTION,
    StorageConfig,
)

# Configure logging
logger = logging.getLogger(__name__)


class DevNoteContent:
    """Helper class for creating structured development note content."""

    @staticmethod
    def create_implementation_note(
        overview: str,
        implementation_details: str,
        affected_files: List[str],
        testing_status: str,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an implementation note content structure.

        Args:
            overview: Brief overview of the implementation
            implementation_details: Detailed explanation of the implementation
            affected_files: List of affected files
            testing_status: Testing status (e.g., "not_tested", "unit_tests_passed")
            additional_info: Any additional information

        Returns:
            Structured content dictionary
        """
        content = {
            "overview": overview,
            "implementation_details": implementation_details,
            "affected_files": affected_files,
            "testing_status": testing_status,
        }

        if additional_info:
            content.update(additional_info)

        return content

    @staticmethod
    def create_architecture_note(
        decision: str,
        context: str,
        alternatives: List[str],
        consequences: str,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an architecture decision note content structure.

        Args:
            decision: The architectural decision
            context: Context in which the decision was made
            alternatives: Alternative options considered
            consequences: Consequences of the decision
            additional_info: Any additional information

        Returns:
            Structured content dictionary
        """
        content = {
            "decision": decision,
            "context": context,
            "alternatives": alternatives,
            "consequences": consequences,
        }

        if additional_info:
            content.update(additional_info)

        return content

    @staticmethod
    def create_issue_note(
        issue_description: str,
        reproduction_steps: List[str],
        impact: str,
        proposed_solution: Optional[str] = None,
        additional_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an issue note content structure.

        Args:
            issue_description: Description of the issue
            reproduction_steps: Steps to reproduce the issue
            impact: Impact of the issue
            proposed_solution: Optional proposed solution
            additional_info: Any additional information

        Returns:
            Structured content dictionary
        """
        content = {
            "issue_description": issue_description,
            "reproduction_steps": reproduction_steps,
            "impact": impact,
        }

        if proposed_solution:
            content["proposed_solution"] = proposed_solution

        if additional_info:
            content.update(additional_info)

        return content


class DevNotesManager:
    """
    Manager for development notes and technical documentation.

    This class provides methods for storing and retrieving development notes,
    such as implementation details, architectural decisions, and issues.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        config: Optional[StorageConfig] = None,
        agent_id: str = "dev_system",
    ):
        """
        Initialize the development notes manager.

        Args:
            memory_manager: Underlying memory manager for storage
            config: Optional storage configuration
            agent_id: Agent ID to use for notes
        """
        self.memory_manager = memory_manager
        self.config = config or StorageConfig()
        self.agent_id = agent_id

    async def initialize(self) -> None:
        """Initialize the development notes manager."""
        await self.memory_manager.initialize()
        logger.info("Development notes manager initialized")

    async def close(self) -> None:
        """Close the development notes manager."""
        # No need to close the memory manager as it might be used elsewhere
        pass

    async def add_note(
        self,
        component: str,
        note_type: Union[str, DevNoteType],
        content: Union[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        expiration: Optional[Union[datetime, timedelta]] = None,
    ) -> str:
        """
        Add a development note.

        Args:
            component: System component being documented
            note_type: Type of note
            content: Note content
            metadata: Additional metadata
            expiration: Optional expiration time

        Returns:
            ID of the created note

        Raises:
            MetadataValidationError: If metadata validation fails
        """
        # Prepare metadata
        meta = metadata or {}
        meta["component"] = component
        meta["note_type"] = (
            note_type.value if isinstance(note_type, DevNoteType) else note_type
        )

        # Add expiration if provided
        if expiration:
            if isinstance(expiration, timedelta):
                meta["expiration"] = datetime.utcnow() + expiration
            else:
                meta["expiration"] = expiration

        # Validate metadata
        try:
            validated_metadata = validate_dev_note_metadata(meta)
            validated_metadata = add_standard_metadata_fields(validated_metadata)
        except MetadataValidationError as e:
            logger.error(f"Failed to validate development note metadata: {e}")
            raise

        # Convert content to string if needed
        content_str = json.dumps(content) if isinstance(content, dict) else content

        # Create AgentData for storage
        data = AgentData(
            agent_id=self.agent_id,
            data_type="dev_note",
            content=content_str,
            metadata=validated_metadata,
        )

        # Store the note
        note_id = await self.memory_manager.add_raw_agent_data(data)
        logger.info(f"Added development note {note_id} for component {component}")

        return note_id

    async def add_implementation_note(
        self,
        component: str,
        overview: str,
        implementation_details: str,
        affected_files: List[str],
        testing_status: str,
        metadata: Optional[Dict[str, Any]] = None,
        additional_content: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an implementation note.

        Args:
            component: System component being documented
            overview: Brief overview of the implementation
            implementation_details: Detailed explanation of the implementation
            affected_files: List of affected files
            testing_status: Testing status
            metadata: Additional metadata
            additional_content: Any additional content fields

        Returns:
            ID of the created note
        """
        content = DevNoteContent.create_implementation_note(
            overview=overview,
            implementation_details=implementation_details,
            affected_files=affected_files,
            testing_status=testing_status,
            additional_info=additional_content,
        )

        return await self.add_note(
            component=component,
            note_type=DevNoteType.IMPLEMENTATION,
            content=content,
            metadata=metadata,
        )

    async def add_architecture_note(
        self,
        component: str,
        decision: str,
        context: str,
        alternatives: List[str],
        consequences: str,
        metadata: Optional[Dict[str, Any]] = None,
        additional_content: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an architecture decision note.

        Args:
            component: System component being documented
            decision: The architectural decision
            context: Context in which the decision was made
            alternatives: Alternative options considered
            consequences: Consequences of the decision
            metadata: Additional metadata
            additional_content: Any additional content fields

        Returns:
            ID of the created note
        """
        content = DevNoteContent.create_architecture_note(
            decision=decision,
            context=context,
            alternatives=alternatives,
            consequences=consequences,
            additional_info=additional_content,
        )

        return await self.add_note(
            component=component,
            note_type=DevNoteType.ARCHITECTURE,
            content=content,
            metadata=metadata,
        )

    async def add_issue_note(
        self,
        component: str,
        issue_description: str,
        reproduction_steps: List[str],
        impact: str,
        proposed_solution: Optional[str] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
        additional_content: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an issue note.

        Args:
            component: System component being documented
            issue_description: Description of the issue
            reproduction_steps: Steps to reproduce the issue
            impact: Impact of the issue
            proposed_solution: Optional proposed solution
            priority: Issue priority
            metadata: Additional metadata
            additional_content: Any additional content fields

        Returns:
            ID of the created note
        """
        content = DevNoteContent.create_issue_note(
            issue_description=issue_description,
            reproduction_steps=reproduction_steps,
            impact=impact,
            proposed_solution=proposed_solution,
            additional_info=additional_content,
        )

        # Set priority in metadata
        meta = metadata or {}
        meta["priority"] = priority

        return await self.add_note(
            component=component,
            note_type=DevNoteType.ISSUE,
            content=content,
            metadata=meta,
        )

    async def get_component_notes(
        self,
        component: str,
        note_type: Optional[Union[str, DevNoteType]] = None,
        limit: int = 20,
    ) -> List[AgentData]:
        """
        Get development notes for a specific component.

        Args:
            component: Component to get notes for
            note_type: Optional note type to filter by
            limit: Maximum number of notes to return

        Returns:
            List of development notes
        """
        # Prepare filters
        filters = {"metadata.component": component, "data_type": "dev_note"}

        # Add note type filter if provided
        if note_type:
            type_value = (
                note_type.value if isinstance(note_type, DevNoteType) else note_type
            )
            filters["metadata.note_type"] = type_value

        # TODO: This is a simplified implementation that assumes add_raw_agent_data
        # stores data in a way that can be efficiently queried. In a real implementation,
        # we would need a more sophisticated query mechanism.

        # For now, we'll fetch all agent data and filter manually
        all_data = []
        async for data in self._query_agent_data(filters):
            all_data.append(data)
            if len(all_data) >= limit:
                break

        return all_data

    async def _query_agent_data(self, filters: Dict[str, Any]) -> List[AgentData]:
        """
        Query agent data based on filters.

        This is a placeholder implementation that would need to be replaced
        with actual query logic based on the memory manager's capabilities.

        Args:
            filters: Filters to apply

        Returns:
            List of matching agent data
        """
        # This is just a placeholder. In a real implementation, we would use
        # the memory manager's query capabilities to efficiently find matching data.
        # Since the current MemoryManager interface doesn't provide a direct way to
        # query agent data by metadata, we're using this as a generator to simulate
        # an async query.

        # This could be implemented by extending the MemoryManager interface or
        # by using a different storage backend that provides better query capabilities.

        # For now, yield an empty list to avoid errors
        yield []

    async def health_check(self) -> MemoryHealth:
        """Check the health of the development notes manager."""
        # Simply delegate to the underlying memory manager
        return await self.memory_manager.health_check()
