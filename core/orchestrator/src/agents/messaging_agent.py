"""
Messaging-Enabled Agent Implementation.

This module provides an example agent that uses the messaging system
for communication with other agents.
"""

import logging
from typing import Any, Dict, Optional

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.agents.message_handler_mixin import MessageHandlerMixin
from core.orchestrator.src.protocols.agent_protocol import (
    AgentQuery,
    AgentResponse as ProtocolResponse,
    MessageType,
    create_protocol_message,
)
from core.orchestrator.src.services.message_queue import AgentMessage, get_message_queue

# Configure logging
logger = logging.getLogger(__name__)


class MessagingAgent(Agent, MessageHandlerMixin):
    """
    Agent that communicates with other agents via the messaging system.

    This agent demonstrates how to use the messaging system for
    inter-agent communication.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a messaging-enabled agent.

        Args:
            config: Optional configuration for the agent
        """
        Agent.__init__(self, config)
        MessageHandlerMixin.__init__(self)

        # Register message handlers
        self.register_message_handler(MessageType.QUERY, self._handle_query)
        self.register_message_handler(MessageType.STATUS, self._handle_status)

    async def initialize_async(self) -> None:
        """Initialize the agent asynchronously."""
        # Start message processing
        await self.start_message_processing()
        logger.info(f"MessagingAgent initialized: {self.config.get('agent_id')}")

    async def close_async(self) -> None:
        """Close the agent and release resources."""
        # Stop message processing
        await self.stop_message_processing()
        logger.info(f"MessagingAgent closed: {self.config.get('agent_id')}")

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input and generate a response.

        This method demonstrates how to use the messaging system to
        collaborate with other agents.

        Args:
            context: The context for this interaction

        Returns:
            The agent's response
        """
        # Example: Query another agent if needed
        if "delegate" in context.user_input.lower():
            # Get the delegate agent ID from config
            delegate_id = self.config.get("delegate_agent_id")

            if delegate_id:
                # Query the delegate agent
                delegate_response = await self.query_agent(
                    recipient_id=delegate_id,
                    query=context.user_input,
                    context={"original_context": context.dict()},
                )

                if delegate_response:
                    # Use the delegate's response
                    return AgentResponse(
                        text=f"Delegate says: {delegate_response.response}",
                        confidence=delegate_response.confidence * 0.9,
                        metadata={"delegated": True, "delegate_id": delegate_id},
                    )

        # Default processing
        return AgentResponse(
            text=f"I received your message: '{context.user_input}'",
            confidence=0.8,
            metadata={"agent_type": "MessagingAgent"},
        )

    async def query_agent(
        self, recipient_id: str, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[ProtocolResponse]:
        """
        Query another agent and wait for a response.

        Args:
            recipient_id: The recipient agent ID
            query: The query text
            context: Optional context information

        Returns:
            The agent's response or None if timeout
        """
        # Get agent ID from config or generate one
        sender_id = self.config.get("agent_id", f"{self.__class__.__name__}_{id(self)}")

        # Create query content
        query_content = AgentQuery(query=query, context=context or {})

        # Create protocol message
        message_dict = create_protocol_message(sender=sender_id, recipient=recipient_id, content=query_content)

        # Convert to AgentMessage
        message = AgentMessage(**message_dict)

        # Send and wait for response
        message_queue = get_message_queue()
        response = await message_queue.request_response(message, timeout=30.0)

        if response and response.message_type == MessageType.RESPONSE:
            return ProtocolResponse(**response.content)

        return None

    async def _handle_query(self, message: AgentMessage) -> None:
        """
        Handle a query message from another agent.

        Args:
            message: The query message
        """
        try:
            # Parse the query
            query_data = AgentQuery(**message.content)

            # Generate a response (simplified for example)
            response_text = f"Response to: {query_data.query}"

            # Create response content
            response_content = ProtocolResponse(response=response_text, confidence=0.9)

            # Create protocol message
            response_dict = create_protocol_message(
                sender=self.config.get("agent_id", f"{self.__class__.__name__}_{id(self)}"),
                recipient=message.sender_id,
                content=response_content,
                correlation_id=message.message_id,
                conversation_id=message.conversation_id,
            )

            # Send response
            response_message = AgentMessage(**response_dict)
            message_queue = get_message_queue()
            await message_queue.send_message(response_message)

        except Exception as e:
            logger.error(f"Error handling query: {e}")

    async def _handle_status(self, message: AgentMessage) -> None:
        """
        Handle a status message from another agent.

        Args:
            message: The status message
        """
        # Log the status update
        logger.info(f"Received status from {message.sender_id}: {message.content}")

    def can_handle(self, context: AgentContext) -> float:
        """
        Determine if this agent can handle the given context.

        Args:
            context: The context for this interaction

        Returns:
            A score between 0 and 1
        """
        # This agent can handle any context, but with moderate confidence
        return 0.7
