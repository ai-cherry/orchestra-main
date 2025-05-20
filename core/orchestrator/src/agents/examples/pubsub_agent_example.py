"""
Example Agent Using PubSub Communication.

This module demonstrates how to implement an agent that uses the PubSub
communication system for inter-agent messaging and task coordination.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.services.agent_communication import get_agent_communication

# Configure logging
logger = logging.getLogger(__name__)


class PubSubAgent(Agent):
    """Example agent that uses PubSub for communication."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PubSub agent.

        Args:
            config: Optional configuration for the agent
        """
        super().__init__(config)
        self.agent_id = config.get("agent_id", f"pubsub-agent-{uuid.uuid4()}")
        self.communication = None
        self.initialized = False

    async def initialize_async(self) -> None:
        """Initialize the agent asynchronously."""
        # Get the communication service
        self.communication = await get_agent_communication(
            agent_id=self.agent_id, conversation_id=self.config.get("conversation_id")
        )

        # Register event handlers
        self.communication.register_event_handler(
            "agent_message", self._handle_agent_message
        )
        self.communication.register_event_handler(
            "system_notification", self._handle_system_notification
        )

        # Register task handlers
        self.communication.register_task_handler(
            "process_query", self._handle_process_query_task
        )
        self.communication.register_task_handler(
            "generate_content", self._handle_generate_content_task
        )

        self.initialized = True
        logger.info(f"PubSubAgent initialized: {self.agent_id}")

    async def close_async(self) -> None:
        """Close the agent and release resources."""
        if self.communication:
            await self.communication.close()
        logger.info(f"PubSubAgent closed: {self.agent_id}")

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input and generate a response.

        This method demonstrates how to use the communication service
        to collaborate with other agents.

        Args:
            context: The context for this interaction

        Returns:
            The agent's response
        """
        if not self.initialized:
            await self.initialize_async()

        # Example: Check if we should delegate to another agent
        if "delegate" in context.user_input.lower():
            # Get the delegate agent ID from config
            delegate_id = self.config.get("delegate_agent_id")

            if delegate_id:
                # Publish a task for the delegate agent
                task_id = str(uuid.uuid4())
                await self.communication.publish_task(
                    task_type="process_query",
                    data={"query": context.user_input, "context": context.dict()},
                    agent_id=delegate_id,
                    task_id=task_id,
                )

                # In a real implementation, we would wait for the result
                # For this example, we'll just return a placeholder
                return AgentResponse(
                    text=f"Task {task_id} delegated to agent {delegate_id}",
                    confidence=0.8,
                    metadata={
                        "delegated": True,
                        "delegate_id": delegate_id,
                        "task_id": task_id,
                    },
                )

        # Example: Notify other agents about this interaction
        await self.communication.publish_event(
            event_type="agent_message",
            data={
                "message": f"Agent {self.agent_id} is processing: {context.user_input}",
                "context_id": context.context_id,
            },
        )

        # Default processing
        return AgentResponse(
            text=f"I received your message: '{context.user_input}'",
            confidence=0.8,
            metadata={"agent_type": "PubSubAgent"},
        )

    async def _handle_agent_message(self, data: Dict[str, Any]) -> None:
        """
        Handle an agent message event.

        Args:
            data: The event data
        """
        logger.info(f"Received agent message: {data.get('message')}")

    async def _handle_system_notification(self, data: Dict[str, Any]) -> None:
        """
        Handle a system notification event.

        Args:
            data: The event data
        """
        logger.info(f"Received system notification: {data}")

    async def _handle_process_query_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a process query task.

        Args:
            data: The task data

        Returns:
            The task result
        """
        query = data.get("query", "")
        logger.info(f"Processing query: {query}")

        # In a real implementation, we would process the query
        # For this example, we'll just return a simple response
        return {"response": f"Processed query: {query}", "confidence": 0.9}

    async def _handle_generate_content_task(
        self, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a generate content task.

        Args:
            data: The task data

        Returns:
            The task result
        """
        prompt = data.get("prompt", "")
        logger.info(f"Generating content for prompt: {prompt}")

        # In a real implementation, we would generate content
        # For this example, we'll just return a simple response
        return {
            "content": f"Generated content for: {prompt}",
            "metadata": {"tokens": len(prompt.split()), "model": "example-model"},
        }

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


# Example usage
async def main():
    """Example of using the PubSubAgent."""
    # Create an agent
    agent = PubSubAgent(
        {"agent_id": "example-agent-1", "conversation_id": "example-conversation-1"}
    )

    # Initialize the agent
    await agent.initialize_async()

    try:
        # Create a context
        context = AgentContext(
            user_input="Hello, can you help me with a task?",
            context_id="example-context-1",
        )

        # Process the context
        response = await agent.process(context)
        print(f"Response: {response.text}")

        # Example: Send a message to another agent
        other_agent_id = "example-agent-2"
        await agent.communication.publish_event(
            event_type="agent_message",
            data={
                "message": "Hello from example-agent-1!",
                "context_id": "example-context-1",
            },
            recipient_id=other_agent_id,
        )

        # Example: Assign a task to another agent
        await agent.communication.publish_task(
            task_type="generate_content",
            data={"prompt": "Generate a summary of the latest news"},
            agent_id=other_agent_id,
        )

        # Wait a bit to allow messages to be processed
        await asyncio.sleep(2)

    finally:
        # Close the agent
        await agent.close_async()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the example
    asyncio.run(main())
