"""
Example usage of the AI Orchestra agent system.

This module demonstrates how to set up and use the different agent types
with the new memory and tool systems.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from core.orchestrator.src.agents.agent_base import AgentContext, AgentResponse
from core.orchestrator.src.agents.memory.layered_memory import (
    LayeredMemoryManager,
    MemoryLayer,
)
from core.orchestrator.src.agents.observable_agent import (
    ObservableAgent,
)
from core.orchestrator.src.agents.stateful_agent import (
    ConversationalAgent,
    StatefulAgent,
)
from core.orchestrator.src.agents.teams.coordinator import AgentTeam, TeamCoordinator
from core.orchestrator.src.agents.tools.base import Tool, ToolUsingAgent
from core.orchestrator.src.config.models import MemoryType, PersonaConfig, TeamMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalculatorTool(Tool):
    """Example tool that performs basic calculations."""

    def __init__(self):
        """Initialize the calculator tool."""
        super().__init__(name="calculator", description="Perform basic arithmetic calculations")

    async def execute(self, expression: str) -> float:
        """
        Execute the calculator tool.

        Args:
            expression: The arithmetic expression to evaluate

        Returns:
            The result of the calculation

        Raises:
            ValueError: If the expression is invalid
        """
        try:
            # Simple and safe eval for basic arithmetic
            # In a real implementation, use a proper expression parser
            allowed_chars = set("0123456789+-*/() .")
            if not all(c in allowed_chars for c in expression):
                raise ValueError(f"Invalid characters in expression: {expression}")

            # Evaluate the expression
            result = eval(expression)

            return float(result)
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")


class WeatherTool(Tool):
    """Example tool that provides weather information."""

    def __init__(self):
        """Initialize the weather tool."""
        super().__init__(name="weather", description="Get weather information for a location")

    async def execute(self, location: str) -> Dict[str, Any]:
        """
        Execute the weather tool.

        Args:
            location: The location to get weather for

        Returns:
            Weather information

        Raises:
            ValueError: If the location is invalid
        """
        # In a real implementation, this would call a weather API
        # For this example, we'll return mock data

        if not location:
            raise ValueError("Location is required")

        # Mock weather data
        return {
            "location": location,
            "temperature": 72,
            "condition": "sunny",
            "humidity": 45,
            "wind_speed": 5,
        }


class ExampleToolUsingAgent(ToolUsingAgent, StatefulAgent):
    """Example agent that uses tools."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the example tool-using agent.

        Args:
            config: Optional configuration for the agent
        """
        StatefulAgent.__init__(self, config)
        ToolUsingAgent.__init__(self, tools=[CalculatorTool(), WeatherTool()])

    async def process_with_state(self, context: AgentContext) -> tuple[AgentResponse, Any]:
        """
        Process user input with tools and state.

        Args:
            context: The context for this interaction

        Returns:
            A tuple of (response, state)
        """
        # Get state
        state = self.get_state(context)

        # Increment step counter
        state.increment_step()

        # Remember user message
        await self.remember(
            context=context,
            text=context.user_input,
            metadata={"source": "user", "step": state.current_step},
        )

        # Check for calculator request
        if "calculate" in context.user_input.lower():
            # Extract expression
            expression = context.user_input.lower().replace("calculate", "").strip()

            try:
                # Use calculator tool
                result = await self.use_tool("calculator", expression=expression)

                # Create response
                response_text = f"The result of {expression} is {result}"

                # Add tool result to state
                state.add_tool_result("calculator", result)

            except ValueError as e:
                response_text = f"Error: {str(e)}"

        # Check for weather request
        elif "weather" in context.user_input.lower():
            # Extract location
            location = context.user_input.lower().replace("weather", "").strip()

            try:
                # Use weather tool
                weather_data = await self.use_tool("weather", location=location)

                # Create response
                response_text = (
                    f"Weather for {weather_data['location']}: "
                    f"{weather_data['temperature']}°F, {weather_data['condition']}, "
                    f"{weather_data['humidity']}% humidity, "
                    f"wind {weather_data['wind_speed']} mph"
                )

                # Add tool result to state
                state.add_tool_result("weather", weather_data)

            except ValueError as e:
                response_text = f"Error: {str(e)}"

        # Default response
        else:
            response_text = "I'm a tool-using agent. You can ask me to:\n- calculate [expression]\n- weather [location]"

        # Create response
        response = AgentResponse(
            text=response_text,
            confidence=0.9,
            metadata={
                "state": state.dict(),
                "step": state.current_step,
                "available_tools": self.get_tool_descriptions(),
            },
        )

        # Remember agent response
        await self.remember(
            context=context,
            text=response.text,
            metadata={"source": "agent", "step": state.current_step},
        )

        return response, state


class ExampleObservableAgent(ObservableAgent):
    """Example agent with observability features."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the example observable agent.

        Args:
            config: Optional configuration for the agent
        """
        super().__init__(config)

        # Register error handlers
        self.register_error_handler(
            "ValueError",
            self._handle_value_error,
            "Handles value errors with a friendly message",
        )

        self.register_error_handler(
            "Exception",
            self._handle_generic_error,
            "Generic error handler for all other exceptions",
        )

    async def _handle_value_error(self, context: AgentContext, error: Exception) -> AgentResponse:
        """
        Handle value errors.

        Args:
            context: The context for this interaction
            error: The error that occurred

        Returns:
            A response for the user
        """
        return AgentResponse(
            text=f"I couldn't understand your input: {str(error)}",
            confidence=0.5,
            metadata={"error": str(error), "error_type": "ValueError", "handled": True},
        )

    async def _handle_generic_error(self, context: AgentContext, error: Exception) -> AgentResponse:
        """
        Handle generic errors.

        Args:
            context: The context for this interaction
            error: The error that occurred

        Returns:
            A response for the user
        """
        return AgentResponse(
            text="I encountered an unexpected error. Please try again.",
            confidence=0.3,
            metadata={
                "error": str(error),
                "error_type": type(error).__name__,
                "handled": True,
            },
        )

    async def _process_impl(self, context: AgentContext) -> AgentResponse:
        """
        Process user input with error handling.

        Args:
            context: The context for this interaction

        Returns:
            The agent's response
        """
        # Record custom metrics
        self._record_metric("input_length", len(context.user_input))
        self._record_metric("user_id", context.user_id)

        # Simulate processing
        if "error" in context.user_input.lower():
            # Simulate an error for testing
            raise ValueError("Simulated error for testing")

        # Normal processing
        return AgentResponse(
            text=f"I processed your input: {context.user_input}",
            confidence=0.9,
            metadata={"metrics": self.get_metrics()},
        )


async def setup_memory_manager() -> LayeredMemoryManager:
    """
    Set up the memory manager with different layers.

    Returns:
        Configured memory manager
    """
    # Create memory layers
    layers = [
        MemoryLayer(
            name="short_term",
            store_type=MemoryType.IN_MEMORY,  # Use in-memory for example
            priority=3,  # Highest priority
            config={},
        ),
        MemoryLayer(
            name="long_term",
            store_type=MemoryType.IN_MEMORY,  # Use in-memory for example
            priority=2,
            config={},
        ),
    ]

    # Create memory manager
    memory_manager = LayeredMemoryManager(layers)

    # Initialize memory manager
    await memory_manager.initialize()

    return memory_manager


async def setup_agent_team() -> AgentTeam:
    """
    Set up an agent team with different agent types.

    Returns:
        Configured agent team
    """
    # Create agents
    tool_agent = ExampleToolUsingAgent()
    observable_agent = ExampleObservableAgent()
    conversational_agent = ConversationalAgent()

    # Create coordinator
    coordinator = TeamCoordinator()

    # Create team
    team = AgentTeam(
        coordinator=coordinator,
        agents={
            "tool_agent": tool_agent,
            "observable_agent": observable_agent,
            "conversational_agent": conversational_agent,
        },
        team_mode=TeamMode.COLLABORATE,
        team_name="example_team",
    )

    return team


async def run_example() -> None:
    """Run the example."""
    # Set up memory manager
    memory_manager = await setup_memory_manager()

    # Set up agent team
    team = await setup_agent_team()

    # Create persona
    persona = PersonaConfig(
        name="Helper",
        background="I'm a helpful assistant.",
        interaction_style="friendly",
        traits={"helpful": 90, "creative": 70, "technical": 80},
    )

    # Create context
    context = AgentContext(
        user_input="Tell me about the weather in New York",
        user_id="example_user",
        persona=persona,
        session_id="example_session",
        interaction_id="example_interaction",
    )

    # Process with team
    response = await team.process(context)

    # Print response
    logger.info(f"Team response: {response.text}")

    # Clean up
    await memory_manager.close()


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_example())
