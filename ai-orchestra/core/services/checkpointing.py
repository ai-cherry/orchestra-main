"""
State checkpointing system for AI Orchestra.

This module provides a system for checkpointing agent state,
allowing for recovery from failures and debugging.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

from ai_orchestra.core.interfaces.memory import MemoryProvider


class StateCheckpointManager:
    """Manager for agent state checkpoints."""

    def __init__(
        self,
        memory_provider: MemoryProvider,
        checkpoint_ttl: int = 86400,  # 24 hours
    ):
        """
        Initialize the checkpoint manager.

        Args:
            memory_provider: The memory provider to use
            checkpoint_ttl: TTL for checkpoints in seconds
        """
        self.memory_provider = memory_provider
        self.checkpoint_ttl = checkpoint_ttl

    def _get_checkpoint_key(self, agent_id: str, checkpoint_id: str) -> str:
        """Get the key for a checkpoint."""
        return f"checkpoint:{agent_id}:{checkpoint_id}"

    def _get_checkpoint_list_key(self, agent_id: str) -> str:
        """Get the key for the checkpoint list."""
        return f"checkpoint_list:{agent_id}"

    async def create_checkpoint(
        self,
        agent_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a checkpoint of agent state.

        Args:
            agent_id: The agent ID
            state: The agent state to checkpoint
            metadata: Optional metadata about the checkpoint

        Returns:
            The checkpoint ID
        """
        # Generate a unique checkpoint ID
        checkpoint_id = str(uuid.uuid4())

        # Create checkpoint data
        checkpoint_data = {
            "agent_id": agent_id,
            "checkpoint_id": checkpoint_id,
            "state": state,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }

        # Store the checkpoint
        checkpoint_key = self._get_checkpoint_key(agent_id, checkpoint_id)
        await self.memory_provider.store(
            key=checkpoint_key,
            value=checkpoint_data,
            ttl=self.checkpoint_ttl,
        )

        # Update the checkpoint list
        checkpoint_list_key = self._get_checkpoint_list_key(agent_id)
        checkpoint_list = await self.memory_provider.retrieve(checkpoint_list_key) or []

        # Add new checkpoint to list
        checkpoint_list.append(
            {
                "checkpoint_id": checkpoint_id,
                "timestamp": checkpoint_data["timestamp"],
                "metadata": metadata or {},
            }
        )

        # Keep only the latest 10 checkpoints in the list
        checkpoint_list = sorted(
            checkpoint_list,
            key=lambda x: x["timestamp"],
            reverse=True,
        )[:10]

        # Update the checkpoint list
        await self.memory_provider.store(
            key=checkpoint_list_key,
            value=checkpoint_list,
            ttl=self.checkpoint_ttl,
        )

        return checkpoint_id

    async def restore_checkpoint(
        self,
        agent_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Restore agent state from checkpoint.

        Args:
            agent_id: The agent ID
            checkpoint_id: The checkpoint ID, or None for latest

        Returns:
            The agent state, or None if not found
        """
        # If no checkpoint ID provided, get the latest
        if checkpoint_id is None:
            checkpoint_list_key = self._get_checkpoint_list_key(agent_id)
            checkpoint_list = (
                await self.memory_provider.retrieve(checkpoint_list_key) or []
            )

            if not checkpoint_list:
                return None

            # Get the latest checkpoint
            checkpoint_id = checkpoint_list[0]["checkpoint_id"]

        # Get the checkpoint
        checkpoint_key = self._get_checkpoint_key(agent_id, checkpoint_id)
        checkpoint_data = await self.memory_provider.retrieve(checkpoint_key)

        if not checkpoint_data:
            return None

        return checkpoint_data["state"]

    async def list_checkpoints(
        self,
        agent_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List checkpoints for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            List of checkpoint information
        """
        checkpoint_list_key = self._get_checkpoint_list_key(agent_id)
        return await self.memory_provider.retrieve(checkpoint_list_key) or []

    async def delete_checkpoint(
        self,
        agent_id: str,
        checkpoint_id: str,
    ) -> bool:
        """
        Delete a checkpoint.

        Args:
            agent_id: The agent ID
            checkpoint_id: The checkpoint ID

        Returns:
            True if the checkpoint was deleted, False otherwise
        """
        # Delete the checkpoint
        checkpoint_key = self._get_checkpoint_key(agent_id, checkpoint_id)
        result = await self.memory_provider.delete(checkpoint_key)

        # Update the checkpoint list
        checkpoint_list_key = self._get_checkpoint_list_key(agent_id)
        checkpoint_list = await self.memory_provider.retrieve(checkpoint_list_key) or []

        # Remove the checkpoint from the list
        checkpoint_list = [
            c for c in checkpoint_list if c["checkpoint_id"] != checkpoint_id
        ]

        # Update the checkpoint list
        await self.memory_provider.store(
            key=checkpoint_list_key,
            value=checkpoint_list,
            ttl=self.checkpoint_ttl,
        )

        return result
