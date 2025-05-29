"""
LangChain Agent Integration for Orchestra

This module provides integration with LangChain's agent framework,
enabling modular, plug-and-play use of LangChain agents within the Orchestra system.
"""

import asyncio
import logging

from packages.shared.src.models.domain_models import AgentResponse as AgentOutput, UserRequest as AgentInput

from ._base import OrchestraAgentBase

logger = logging.getLogger(__name__)


class LangChainAgentWrapper(OrchestraAgentBase):
    """
    Wrapper for integrating LangChain-based agents with Orchestra.

    This wrapper adapts LangChain's agent framework to work with the
    Orchestra orchestration system, supporting modular agent execution.
    """

    agent_type = "langchain"

    def __init__(self, **kwargs):
        """
        Initialize the LangChain agent wrapper.

        Args:
            agent_config: Configuration for the LangChain agent
            memory_manager: Orchestra's memory management system
            llm_client: LLM client for the agent
            tool_registry: Tool registry for the agent
        """
        super().__init__(**kwargs)

        # Initialize LangChain agent
        self.langchain_agent = None
        self._initialize_langchain_agent()

    def _initialize_langchain_agent(self):
        """
        Initialize the LangChain agent based on configuration.

        Dynamically imports and instantiates the LangChain agent class
        specified in the agent configuration.
        """
        try:
            agent_class_name = self.agent_config.get("langchain_agent_class")
            if not agent_class_name:
                raise ValueError("langchain_agent_class not defined in agent config")

            # Dynamically import the agent class
            components = agent_class_name.split(".")
            module_name = ".".join(components[:-1])
            class_name = components[-1]
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)

            # Create an instance of the agent class, passing the agent config
            self.langchain_agent = agent_class(agent_config=self.agent_config)

            logger.info(f"Initialized LangChain agent: {agent_class_name}")

        except Exception as e:
            logger.error(f"Failed to initialize LangChain agent: {str(e)}")

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the LangChain agent with the given input, including short-term memory.

        Args:
            input_data: The user input to process

        Returns:
            AgentOutput containing the agent's response
        """
        try:
            # 1. Retrieve recent messages from short-term memory (if available)
            # NOTE: Replace with actual memory retrieval logic as needed
            try:
                from core.orchestrator.src.main import short_term_memory

                recent_messages = short_term_memory
            except ImportError:
                recent_messages = []

            # 2. Prepare context for the LangChain agent
            context = {
                "user_input": input_data.content,
                "recent_messages": recent_messages,
            }

            # 3. Call the LangChain agent's processing method
            logger.info(f"Processing input with LangChain agent: {self.name}")
            # Assume the LangChain agent exposes an async 'process' method
            if hasattr(self.langchain_agent, "process") and asyncio.iscoroutinefunction(self.langchain_agent.process):
                agent_response = await self.langchain_agent.process(context)
            elif hasattr(self.langchain_agent, "process"):
                # Fallback to sync method if async not available
                agent_response = self.langchain_agent.process(context)
            else:
                raise AttributeError("LangChain agent does not have a 'process' method")

            # 4. Translate the results back to Orchestra's format
            return AgentOutput(
                response_id="langchain-response",  # Replace with actual response ID if available
                request_id=input_data.request_id,
                agent_id=self.id,
                content=str(agent_response),  # Ensure the content is a string
                status="completed",
            )

        except Exception as e:
            logger.error(f"Error running LangChain agent: {str(e)}")
            return AgentOutput(
                response_id="error-response",
                request_id=input_data.request_id,
                agent_id=self.id,
                content=f"Error executing LangChain agent: {str(e)}",
                status="error",
            )

    async def health_check(self) -> bool:
        """
        Check if the LangChain agent wrapper and its underlying framework are available.

        Returns:
            True if the agent is operational, False otherwise
        """
        # Optionally, implement a more robust health check for LangChain
        return self.langchain_agent is not None
