"""
Phidata Agent Integration for Orchestra

This module provides integration with Phidata's agent framework.
"""

import logging

from packages.shared.src.models.domain_models import AgentResponse as AgentOutput, UserRequest as AgentInput

from ._base import OrchestraAgentBase

logger = logging.getLogger(__name__)

class PhidataAgentWrapper(OrchestraAgentBase):
    """
    Wrapper for integrating Phidata-based agents with Orchestra.

    This wrapper adapts Phidata's agent framework to work with the
    Orchestra orchestration system.
    """

    agent_type = "phidata"

    def __init__(self, **kwargs):
        """
        Initialize the Phidata agent wrapper.

        Args:
            agent_config: Configuration for the Phidata agent
            memory_manager: Orchestra's memory management system
            llm_client: LLM client for the agent
            tool_registry: Tool registry for the agent
        """
        super().__init__(**kwargs)

        # Initialize Phidata agent
        self.phidata_agent = None
        self._initialize_phidata_agent()

    def _initialize_phidata_agent(self):
        """
        Initialize the Phidata agent based on configuration.

        This creates a new Phidata agent instance using the
        configuration provided and the dependencies from Orchestra.
        """
        try:
            # Get the agent class from the configuration
            agent_class_name = self.agent_config.get("phidata_agent_class")
            if not agent_class_name:
                raise ValueError("phidata_agent_class not defined in agent config")

            # Dynamically import the agent class
            components = agent_class_name.split(".")
            module_name = ".".join(components[:-1])
            class_name = components[-1]
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)

            # Create an instance of the agent class, passing the agent config
            self.phidata_agent = agent_class(agent_config=self.agent_config)

            logger.info(f"Initialized Phidata agent: {agent_class_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Phidata agent: {str(e)}")

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the Phidata agent with the given input, including short-term memory.

        Args:
            input_data: The user input to process

        Returns:
            AgentOutput containing the agent's response
        """
        try:
            # 1. Retrieve recent messages from short-term memory
            from core.orchestrator.src.main import short_term_memory

            recent_messages = short_term_memory

            # 2. Include recent messages in the context passed to the Phidata agent
            context = {
                "user_input": input_data.content,
                "recent_messages": recent_messages,
            }

            # 3. Call the Phidata agent's processing method
            logger.info(f"Processing input with Phidata agent: {self.name}")
            agent_response = await self.phidata_agent.process(context)

            # 4. Translate the results back to Orchestra's format
            return AgentOutput(
                response_id="phidata-response",  # Replace with actual response ID if available
                request_id=input_data.request_id,
                agent_id=self.id,
                content=str(agent_response),  # Ensure the content is a string
                status="completed",
            )

        except Exception as e:
            logger.error(f"Error running Phidata agent: {str(e)}")
            return AgentOutput(
                response_id="error-response",
                request_id=input_data.request_id,
                agent_id=self.id,
                content=f"Error executing Phidata agent: {str(e)}",
                status="error",
            )
