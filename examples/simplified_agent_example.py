#!/usr/bin/env python3
"""
Example usage of the Simplified Agent Registry.

This script demonstrates how to use the simplified agent registry
for agent management and selection without security overhead.
"""

import logging
import sys
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("simplified-agent-example")

from core.orchestrator.src.agents.agent_base import AgentContext

# Import the simplified agent registry
from core.orchestrator.src.agents.simplified_agent_registry import (
    AgentCapability,
    get_simplified_agent_registry,
    register_default_agents,
)

class SimpleAgent:
    """A simple agent implementation for demonstration purposes."""

    def __init__(self, agent_type: str, capabilities: list = None):
        """Initialize the simple agent."""
        self.agent_type = agent_type
        self.capabilities = capabilities or [AgentCapability.GENERAL]
        logger.info(f"Created SimpleAgent with type: {agent_type}")

    async def process(self, user_input: str) -> str:
        """Process user input and return a response."""
        return f"SimpleAgent ({self.agent_type}) processed: {user_input}"

class CodeAgent:
    """A simple code-focused agent implementation."""

    def __init__(self):
        """Initialize the code agent."""
        self.agent_type = "code_agent"
        self.capabilities = [AgentCapability.CODE_GENERATION]
        logger.info("Created CodeAgent")

    async def process(self, user_input: str) -> str:
        """Process user input and return code."""
        return f"```python\n# Generated code for: {user_input}\ndef example():\n    print('Hello, world!')\n```"

def create_context(user_input: str, metadata: Dict[str, Any] = None) -> AgentContext:
    """Create a simple agent context for testing."""
    return AgentContext(
        user_input=user_input,
        metadata=metadata or {},
        conversation_id="test-conversation",
        message_id="test-message",
    )

async def run_example():
    """Run the simplified agent registry example."""
    logger.info("Starting simplified agent registry example")

    # Get the registry and register default agents
    registry = get_simplified_agent_registry()
    register_default_agents()

    # Register our custom agents
    simple_agent = SimpleAgent("simple_agent", [AgentCapability.TEXT_GENERATION])
    registry.register_agent(simple_agent)

    code_agent = CodeAgent()
    registry.register_agent(code_agent)

    # Print registry status
    status = registry.get_agent_status()
    logger.info(f"Registry status: {status}")

    # Test agent selection with different contexts
    test_cases = [
        ("Hello, how are you?", {}),
        ("Write a function to calculate fibonacci numbers", {}),
        ("Can you summarize this article?", {}),
        ("Tell me a story", {}),
        ("What is the capital of France?", {}),
        ("Hello", {"agent_type": "simple_agent"}),  # Explicitly request an agent
    ]

    for user_input, metadata in test_cases:
        context = create_context(user_input, metadata)
        logger.info(f"\nProcessing: '{user_input}'")

        # Select an agent for this context
        agent = registry.select_agent_for_context(context)
        logger.info(f"Selected agent: {agent.agent_type}")

        # Process the input
        response = await agent.process(user_input)
        logger.info(f"Response: {response}")

if __name__ == "__main__":
    import asyncio

    asyncio.run(run_example())
