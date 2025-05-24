"""
Agent Communication Service for AI Orchestra.

This module provides a service for agent communication using PubSub.
It handles message routing, event distribution, and task coordination.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union, Set

from core.orchestrator.src.services.pubsub_client import get_pubsub_client
from core.orchestrator.src.config.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class AgentCommunicationService:
    """Service for agent communication using PubSub."""

    def __init__(self):
        """Initialize the agent communication service."""
        self.pubsub_client = get_pubsub_client()
        self.environment = settings.ENVIRONMENT or "dev"
        self.agent_id = None
        self.conversation_id = None
        self.subscriptions: Set[str] = set()
        self.event_handlers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self.task_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}

    async def initialize(self, agent_id: str, conversation_id: Optional[str] = None) -> None:
        """
        Initialize the communication service.

        Args:
            agent_id: The ID of this agent
            conversation_id: Optional conversation ID
        """
        self.agent_id = agent_id
        self.conversation_id = conversation_id

        # Create topics if they don't exist
        self.pubsub_client.create_topic("agent-events")
        self.pubsub_client.create_topic("agent-tasks")
        self.pubsub_client.create_topic("agent-results")

        # Create agent-specific subscription for events
        agent_filter = f'attributes.recipient_id = "{agent_id}" OR attributes.recipient_id = "all"'
        if conversation_id:
            agent_filter += f' AND attributes.conversation_id = "{conversation_id}"'

        self.pubsub_client.create_subscription(f"agent-events-{agent_id}", "agent-events", filter_expr=agent_filter)

        # Create agent-specific subscription for tasks
        task_filter = f'attributes.agent_id = "{agent_id}"'
        if conversation_id:
            task_filter += f' AND attributes.conversation_id = "{conversation_id}"'

        self.pubsub_client.create_subscription(f"agent-tasks-{agent_id}", "agent-tasks", filter_expr=task_filter)

        # Start listening for events
        await self.start_event_listener()

        # Start listening for tasks
        await self.start_task_listener()

        logger.info(f"Agent communication initialized for agent {agent_id}")

    async def start_event_listener(self) -> None:
        """Start listening for events."""
        subscription_name = f"agent-events-{self.agent_id}"

        # Define the callback for events
        async def event_callback(data: Dict[str, Any], attributes: Dict[str, str]) -> None:
            event_type = attributes.get("event_type")
            if not event_type:
                logger.warning(f"Received event without event_type: {attributes}")
                return

            # Call registered handlers for this event type
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(data)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event_type}: {e}")

        # Start the subscription
        asyncio.create_task(self.pubsub_client.subscribe_async(subscription_name, event_callback))
        self.subscriptions.add(subscription_name)

        logger.info(f"Started event listener for agent {self.agent_id}")

    async def start_task_listener(self) -> None:
        """Start listening for tasks."""
        subscription_name = f"agent-tasks-{self.agent_id}"

        # Define the callback for tasks
        async def task_callback(data: Dict[str, Any], attributes: Dict[str, str]) -> None:
            task_type = attributes.get("task_type")
            if not task_type:
                logger.warning(f"Received task without task_type: {attributes}")
                return

            # Call registered handler for this task type
            if task_type in self.task_handlers:
                try:
                    # Process the task
                    result = await self.task_handlers[task_type](data)

                    # Publish the result
                    await self.publish_task_result(
                        task_id=attributes.get("task_id", str(uuid.uuid4())),
                        result=result,
                        task_type=task_type,
                    )
                except Exception as e:
                    logger.error(f"Error in task handler for {task_type}: {e}")

                    # Publish error result
                    await self.publish_task_result(
                        task_id=attributes.get("task_id", str(uuid.uuid4())),
                        result={"error": str(e)},
                        task_type=task_type,
                        success=False,
                    )

        # Start the subscription
        asyncio.create_task(self.pubsub_client.subscribe_async(subscription_name, task_callback))
        self.subscriptions.add(subscription_name)

        logger.info(f"Started task listener for agent {self.agent_id}")

    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """
        Register a handler for a specific event type.

        Args:
            event_type: The type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def register_task_handler(
        self,
        task_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ) -> None:
        """
        Register a handler for a specific task type.

        Args:
            task_type: The type of task to handle
            handler: Async function to handle the task
        """
        self.task_handlers[task_type] = handler

    async def publish_event(self, event_type: str, data: Dict[str, Any], recipient_id: str = "all") -> str:
        """
        Publish an event.

        Args:
            event_type: The type of event
            data: The event data
            recipient_id: The recipient agent ID or "all"

        Returns:
            The published message ID
        """
        attributes = {
            "event_type": event_type,
            "sender_id": self.agent_id,
            "recipient_id": recipient_id,
            "timestamp": str(int(time.time())),
        }

        if self.conversation_id:
            attributes["conversation_id"] = self.conversation_id

        return await self.pubsub_client.publish_message_async(
            "agent-events",
            data,
            ordering_key=self.conversation_id,
            attributes=attributes,
        )

    async def publish_task(
        self,
        task_type: str,
        data: Dict[str, Any],
        agent_id: str,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Publish a task.

        Args:
            task_type: The type of task
            data: The task data
            agent_id: The agent ID to assign the task to
            task_id: Optional task ID

        Returns:
            The published message ID
        """
        task_id = task_id or str(uuid.uuid4())

        attributes = {
            "task_type": task_type,
            "task_id": task_id,
            "sender_id": self.agent_id,
            "agent_id": agent_id,
            "timestamp": str(int(time.time())),
        }

        if self.conversation_id:
            attributes["conversation_id"] = self.conversation_id

        return await self.pubsub_client.publish_message_async(
            "agent-tasks", data, ordering_key=task_id, attributes=attributes
        )

    async def publish_task_result(
        self, task_id: str, result: Dict[str, Any], task_type: str, success: bool = True
    ) -> str:
        """
        Publish a task result.

        Args:
            task_id: The task ID
            result: The task result
            task_type: The type of task
            success: Whether the task was successful

        Returns:
            The published message ID
        """
        attributes = {
            "task_id": task_id,
            "task_type": task_type,
            "agent_id": self.agent_id,
            "success": str(success).lower(),
            "timestamp": str(int(time.time())),
        }

        if self.conversation_id:
            attributes["conversation_id"] = self.conversation_id

        return await self.pubsub_client.publish_message_async(
            "agent-results", result, ordering_key=task_id, attributes=attributes
        )

    async def close(self) -> None:
        """Close the communication service."""
        # Stop all subscriptions
        for subscription_name in self.subscriptions:
            self.pubsub_client.stop_subscription(subscription_name)

        self.subscriptions.clear()
        logger.info(f"Agent communication closed for agent {self.agent_id}")


# Singleton instance
_agent_communication = None


async def get_agent_communication(
    agent_id: Optional[str] = None, conversation_id: Optional[str] = None
) -> AgentCommunicationService:
    """
    Get the global agent communication service instance.

    Args:
        agent_id: Optional agent ID to initialize with
        conversation_id: Optional conversation ID

    Returns:
        The global AgentCommunicationService instance
    """
    global _agent_communication
    if _agent_communication is None:
        _agent_communication = AgentCommunicationService()

    if agent_id and not _agent_communication.agent_id:
        await _agent_communication.initialize(agent_id, conversation_id)

    return _agent_communication
