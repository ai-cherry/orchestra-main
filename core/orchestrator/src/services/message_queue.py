"""
Message Queue Service for AI Orchestration System.

This module provides a reliable message queue for agent communication,
supporting direct messaging, broadcast, and request-response patterns.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

# Handle both pydantic v1 and v2
try:
    from pydantic.v1 import BaseModel, Field  # For pydantic v2
except ImportError:
    from pydantic import BaseModel, Field  # For pydantic v1

from core.orchestrator.src.services.event_bus import get_event_bus

# Configure logging
logger = logging.getLogger(__name__)

class AgentMessage(BaseModel):
    """Standardized message format for agent communication"""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: Optional[str] = None  # None for broadcast
    message_type: str
    content: Dict[str, Any]
    correlation_id: Optional[str] = None  # For tracking related messages
    reply_to: Optional[str] = None  # For request-response patterns
    timestamp: float = Field(default_factory=time.time)
    ttl: Optional[int] = None  # Time-to-live in seconds

class MessageQueue:
    """Message queue for reliable agent communication"""

    def __init__(self):
        """Initialize the message queue."""
        self._event_bus = get_event_bus()
        self._queues: Dict[str, asyncio.Queue] = {}
        self._handlers: Dict[str, List[Callable[[AgentMessage], Awaitable[None]]]] = {}
        logger.info("MessageQueue initialized")

    async def send_message(self, message: AgentMessage) -> str:
        """
        Send a message to an agent or broadcast.

        Args:
            message: The message to send

        Returns:
            The message ID
        """
        if not message.message_id:
            message.message_id = str(uuid.uuid4())

        # Publish to event bus for monitoring/logging
        try:
            await self._event_bus.publish_async("agent_message_sent", {"message": message.dict()})
        except Exception as e:
            logger.warning(f"Failed to publish agent_message_sent event: {e}")

        if message.recipient_id:
            # Direct message to specific agent
            if message.recipient_id not in self._queues:
                self._queues[message.recipient_id] = asyncio.Queue()
            await self._queues[message.recipient_id].put(message)
            logger.debug(f"Message {message.message_id} queued for {message.recipient_id}")
        else:
            # Broadcast to all registered handlers
            broadcast_count = 0
            for agent_id, handler_list in self._handlers.items():
                for handler in handler_list:
                    try:
                        await handler(message)
                        broadcast_count += 1
                    except Exception as e:
                        logger.error(f"Error in broadcast handler for agent {agent_id}: {e}")
                        await self._event_bus.publish_async(
                            "agent_message_error",
                            {"message_id": message.message_id, "error": str(e)},
                        )
            logger.debug(f"Message {message.message_id} broadcast to {broadcast_count} handlers")

        return message.message_id

    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        Receive a message for a specific agent.

        Args:
            agent_id: The ID of the agent receiving messages
            timeout: Optional timeout in seconds

        Returns:
            The received message or None if timeout
        """
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()

        try:
            if timeout:
                message = await asyncio.wait_for(self._queues[agent_id].get(), timeout)
            else:
                message = await self._queues[agent_id].get()

            # Mark as processed
            self._queues[agent_id].task_done()

            # Log receipt
            logger.debug(f"Agent {agent_id} received message {message.message_id}")

            return message
        except asyncio.TimeoutError:
            return None

    def register_handler(self, agent_id: str, handler: Callable[[AgentMessage], Awaitable[None]]):
        """
        Register a message handler for an agent.

        Args:
            agent_id: The ID of the agent
            handler: Async function to handle messages
        """
        if agent_id not in self._handlers:
            self._handlers[agent_id] = []
        self._handlers[agent_id].append(handler)
        logger.debug(f"Handler registered for agent {agent_id}")

    def unregister_handler(self, agent_id: str, handler: Callable[[AgentMessage], Awaitable[None]]) -> bool:
        """
        Unregister a message handler.

        Args:
            agent_id: The ID of the agent
            handler: The handler to remove

        Returns:
            True if handler was found and removed
        """
        if agent_id in self._handlers:
            try:
                self._handlers[agent_id].remove(handler)
                logger.debug(f"Handler unregistered for agent {agent_id}")
                return True
            except ValueError:
                return False
        return False

    async def request_response(self, request: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        Send a request and wait for a response.

        Args:
            request: The request message
            timeout: Timeout in seconds

        Returns:
            The response message or None if timeout
        """
        if not request.sender_id:
            raise ValueError("Sender ID is required for request-response pattern")

        if not request.recipient_id:
            raise ValueError("Recipient ID is required for request-response pattern")

        # Set up for response tracking
        request.reply_to = request.sender_id

        # Create a future to wait for the response
        response_future = asyncio.Future()

        # Define a handler for the response
        async def response_handler(message: AgentMessage):
            if message.correlation_id == request.message_id or message.correlation_id == request.correlation_id:
                response_future.set_result(message)

        # Register temporary handler
        self.register_handler(request.sender_id, response_handler)

        try:
            # Send the request
            await self.send_message(request)

            # Wait for response with timeout
            return await asyncio.wait_for(response_future, timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Request {request.message_id} timed out after {timeout}s")
            return None
        finally:
            # Clean up handler
            self.unregister_handler(request.sender_id, response_handler)

# Singleton instance
_message_queue = None

def get_message_queue() -> MessageQueue:
    """
    Get the global message queue instance.

    Returns:
        The global MessageQueue instance
    """
    global _message_queue
    if _message_queue is None:
        _message_queue = MessageQueue()
    return _message_queue
