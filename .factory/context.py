"""
Factory AI Context Management Module.

This module provides context management for Factory AI Droid integration,
handling context storage, retrieval, and synchronization across droids.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

import yaml

logger = logging.getLogger(__name__)

@dataclass
class DroidContext:
    """Context information for a specific Factory AI Droid."""

    droid_name: str
    task_id: UUID
    created_at: datetime
    updated_at: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_context_id: Optional[UUID] = None
    child_context_ids: Set[UUID] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary format."""
        return {
            "droid_name": self.droid_name,
            "task_id": str(self.task_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "parent_context_id": str(self.parent_context_id) if self.parent_context_id else None,
            "child_context_ids": [str(cid) for cid in self.child_context_ids],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DroidContext":
        """Create context from dictionary format."""
        return cls(
            droid_name=data["droid_name"],
            task_id=UUID(data["task_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            parent_context_id=UUID(data["parent_context_id"]) if data.get("parent_context_id") else None,
            child_context_ids={UUID(cid) for cid in data.get("child_context_ids", [])},
        )

class FactoryContextManager:
    """Manages context for Factory AI Droid operations."""

    def __init__(self, config_path: Path = Path(".factory/config.yaml")):
        """Initialize the context manager.

        Args:
            config_path: Path to the Factory AI configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.contexts: Dict[UUID, DroidContext] = {}
        self.active_contexts: Dict[str, UUID] = {}  # droid_name -> active context ID

    def _load_config(self) -> Dict[str, Any]:
        """Load Factory AI configuration."""
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def create_context(
        self,
        droid_name: str,
        initial_data: Optional[Dict[str, Any]] = None,
        parent_context_id: Optional[UUID] = None,
    ) -> DroidContext:
        """Create a new context for a droid.

        Args:
            droid_name: Name of the droid (architect, code, debug, etc.)
            initial_data: Initial context data
            parent_context_id: Optional parent context for hierarchical contexts

        Returns:
            Created DroidContext instance
        """
        now = datetime.now(timezone.utc)
        context = DroidContext(
            droid_name=droid_name,
            task_id=uuid4(),
            created_at=now,
            updated_at=now,
            data=initial_data or {},
            parent_context_id=parent_context_id,
        )

        # Update parent-child relationships
        if parent_context_id and parent_context_id in self.contexts:
            parent = self.contexts[parent_context_id]
            parent.child_context_ids.add(context.task_id)

        self.contexts[context.task_id] = context
        self.active_contexts[droid_name] = context.task_id

        logger.info(f"Created context {context.task_id} for {droid_name}")
        return context

    def get_context(self, task_id: UUID) -> Optional[DroidContext]:
        """Retrieve a context by task ID."""
        return self.contexts.get(task_id)

    def get_active_context(self, droid_name: str) -> Optional[DroidContext]:
        """Get the active context for a specific droid."""
        context_id = self.active_contexts.get(droid_name)
        return self.contexts.get(context_id) if context_id else None

    def update_context(
        self,
        task_id: UUID,
        data_updates: Optional[Dict[str, Any]] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an existing context.

        Args:
            task_id: ID of the context to update
            data_updates: Data fields to update
            metadata_updates: Metadata fields to update

        Returns:
            True if update successful, False otherwise
        """
        context = self.contexts.get(task_id)
        if not context:
            logger.warning(f"Context {task_id} not found")
            return False

        if data_updates:
            context.data.update(data_updates)
        if metadata_updates:
            context.metadata.update(metadata_updates)

        context.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updated context {task_id}")
        return True

    def merge_contexts(self, source_ids: List[UUID], target_droid: str) -> DroidContext:
        """Merge multiple contexts into a new context.

        Args:
            source_ids: List of context IDs to merge
            target_droid: Target droid for the merged context

        Returns:
            New merged context
        """
        merged_data = {}
        merged_metadata = {"source_contexts": [str(sid) for sid in source_ids]}

        for source_id in source_ids:
            context = self.contexts.get(source_id)
            if context:
                merged_data.update(context.data)
                merged_metadata[f"from_{context.droid_name}"] = {
                    "task_id": str(context.task_id),
                    "created_at": context.created_at.isoformat(),
                }

        return self.create_context(
            droid_name=target_droid,
            initial_data=merged_data,
        )

    def get_context_chain(self, task_id: UUID) -> List[DroidContext]:
        """Get the full context chain (ancestors and descendants).

        Args:
            task_id: Starting context ID

        Returns:
            List of contexts in the chain
        """
        chain = []
        context = self.contexts.get(task_id)
        if not context:
            return chain

        # Get ancestors
        current = context
        ancestors = []
        while current.parent_context_id:
            parent = self.contexts.get(current.parent_context_id)
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break

        # Build chain: ancestors -> current -> descendants
        chain.extend(reversed(ancestors))
        chain.append(context)

        # Get descendants (BFS)
        to_visit = list(context.child_context_ids)
        while to_visit:
            child_id = to_visit.pop(0)
            child = self.contexts.get(child_id)
            if child:
                chain.append(child)
                to_visit.extend(child.child_context_ids)

        return chain

    def export_context(self, task_id: UUID) -> Optional[str]:
        """Export a context to JSON format.

        Args:
            task_id: Context ID to export

        Returns:
            JSON string or None if context not found
        """
        context = self.contexts.get(task_id)
        if not context:
            return None

        return json.dumps(context.to_dict(), indent=2)

    def import_context(self, json_data: str) -> Optional[DroidContext]:
        """Import a context from JSON format.

        Args:
            json_data: JSON string containing context data

        Returns:
            Imported context or None if import failed
        """
        try:
            data = json.loads(json_data)
            context = DroidContext.from_dict(data)
            self.contexts[context.task_id] = context
            return context
        except Exception as e:
            logger.error(f"Failed to import context: {e}")
            return None

    def cleanup_old_contexts(self, days: int = 7) -> int:
        """Remove contexts older than specified days.

        Args:
            days: Number of days to keep contexts

        Returns:
            Number of contexts removed
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        to_remove = []

        for task_id, context in self.contexts.items():
            if context.updated_at < cutoff:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.contexts[task_id]
            # Remove from active contexts if present
            for droid, active_id in list(self.active_contexts.items()):
                if active_id == task_id:
                    del self.active_contexts[droid]

        logger.info(f"Cleaned up {len(to_remove)} old contexts")
        return len(to_remove)

# Import timedelta for cleanup function
from datetime import timedelta

# Example usage
if __name__ == "__main__":
    # Initialize context manager
    manager = FactoryContextManager()

    # Create context for architect droid
    architect_ctx = manager.create_context(
        "architect",
        initial_data={
            "project_type": "web_application",
            "requirements": ["scalability", "security", "performance"],
        },
    )

    # Create child context for code droid
    code_ctx = manager.create_context(
        "code",
        initial_data={
            "language": "python",
            "framework": "fastapi",
        },
        parent_context_id=architect_ctx.task_id,
    )

    # Update context
    manager.update_context(
        code_ctx.task_id,
        data_updates={"modules_completed": ["auth", "api"]},
    )

    # Get context chain
    chain = manager.get_context_chain(code_ctx.task_id)
    print(f"Context chain length: {len(chain)}")

    # Export context
    exported = manager.export_context(code_ctx.task_id)
    print(f"Exported context: {exported[:100]}...")
