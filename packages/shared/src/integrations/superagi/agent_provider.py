"""
SuperAGI Agent Provider for Orchestra.

This module provides integration between Orchestra and SuperAGI's cloud agent
management platform, enabling advanced agent lifecycle management and tooling.
"""

import logging
import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Union, Callable

from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.memory.base_memory_manager import MemoryManager

# Configure logging
logger = logging.getLogger(__name__)


class SuperAGIAgentProvider:
    """
    Integration adapter for SuperAGI's cloud agent management platform.

    This adapter:
    1. Implements Orchestra's agent provider interface
    2. Connects to SuperAGI for agent lifecycle management
    3. Maps Orchestra's tool registry to SuperAGI's tool format
    4. Enables advanced agent monitoring and resource optimization
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        memory_manager: Optional[MemoryManager] = None,
    ):
        """
        Initialize the SuperAGI Agent Provider.

        Args:
            config: Configuration options for the provider
            memory_manager: Orchestra's memory manager for context
        """
        self.config = config or {}
        self.memory_manager = memory_manager
        self.superagi_client = None
        self.agents = {}  # Map of agent_id -> SuperAGI agent
        self._initialized = False
        logger.info("SuperAGIAgentProvider initialized with config")

    async def initialize(self) -> bool:
        """Initialize connection to SuperAGI cloud."""
        try:
            # Import SuperAGI client library (assumed to be installed)
            try:
                from superagi_client import SuperAGIClient
                from superagi_client.models import AgentConfig, ToolConfig

                self.SuperAGIClient = SuperAGIClient
                self.AgentConfig = AgentConfig
                self.ToolConfig = ToolConfig
            except ImportError:
                logger.warning(
                    "SuperAGI client library not available. Install with: pip install superagi-client"
                )
                return False

            # Initialize SuperAGI client
            api_key = self.config.get("api_key") or os.environ.get("SUPERAGI_API_KEY")
            if not api_key:
                logger.warning("SuperAGI API key not provided")
                return False

            self.superagi_client = self.SuperAGIClient(
                api_key=api_key,
                api_url=self.config.get("api_url", "https://api.superagi.com/v1"),
                organization_id=self.config.get("organization_id"),
            )

            # Test connection
            await self.superagi_client.test_connection()

            self._initialized = True
            logger.info("Connected to SuperAGI cloud platform")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SuperAGI agent provider: {e}")
            return False

    async def create_agent(
        self, agent_config: Dict[str, Any], tools: List[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new agent using SuperAGI's platform.

        Args:
            agent_config: Agent configuration
            tools: List of tools to provide to the agent

        Returns:
            ID of the created agent
        """
        if not self._initialized:
            logger.warning("SuperAGIAgentProvider not initialized")
            return None

        try:
            # Map Orchestra agent config to SuperAGI format
            superagi_config = self._map_to_superagi_config(agent_config)

            # Process tools if provided
            superagi_tools = []
            if tools:
                for tool in tools:
                    superagi_tool = self._map_tool_to_superagi(tool)
                    if superagi_tool:
                        superagi_tools.append(superagi_tool)

            # Create agent in SuperAGI
            agent_id = await self.superagi_client.create_agent(
                config=superagi_config, tools=superagi_tools
            )

            # Store reference to the agent
            self.agents[agent_id] = {
                "id": agent_id,
                "config": agent_config,
                "status": "created",
            }

            logger.info(f"Created agent {agent_id} in SuperAGI")
            return agent_id
        except Exception as e:
            logger.error(f"Failed to create SuperAGI agent: {e}")
            return None

    async def run_agent(self, agent_id: str, input_data: Any = None) -> Dict[str, Any]:
        """
        Run an agent with optional input data.

        Args:
            agent_id: ID of the agent to run
            input_data: Optional input data for the agent

        Returns:
            Result from the agent run
        """
        if not self._initialized:
            logger.warning("SuperAGIAgentProvider not initialized")
            return {"error": "Not initialized"}

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return {"error": f"Agent {agent_id} not found"}

            # Run the agent in SuperAGI
            run_id = await self.superagi_client.run_agent(
                agent_id=agent_id, input=input_data
            )

            # Wait for agent to complete
            result = await self._wait_for_agent_completion(agent_id, run_id)

            # Update agent status
            self.agents[agent_id]["status"] = "available"

            return result
        except Exception as e:
            logger.error(f"Failed to run SuperAGI agent: {e}")
            return {"error": str(e)}

    async def get_agent_status(self, agent_id: str) -> str:
        """
        Get the current status of an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Current status of the agent
        """
        if not self._initialized:
            logger.warning("SuperAGIAgentProvider not initialized")
            return "unknown"

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return "not_found"

            # Get latest status from SuperAGI
            status = await self.superagi_client.get_agent_status(agent_id)

            # Update local status
            self.agents[agent_id]["status"] = status

            return status
        except Exception as e:
            logger.error(f"Failed to get SuperAGI agent status: {e}")
            return "error"

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent from SuperAGI.

        Args:
            agent_id: ID of the agent to delete

        Returns:
            Whether the agent was successfully deleted
        """
        if not self._initialized:
            logger.warning("SuperAGIAgentProvider not initialized")
            return False

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            # Delete agent in SuperAGI
            success = await self.superagi_client.delete_agent(agent_id)

            if success:
                # Remove from local tracking
                del self.agents[agent_id]
                logger.info(f"Deleted agent {agent_id} from SuperAGI")

            return success
        except Exception as e:
            logger.error(f"Failed to delete SuperAGI agent: {e}")
            return False

    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents managed by this provider.

        Returns:
            List of agent information dictionaries
        """
        if not self._initialized:
            logger.warning("SuperAGIAgentProvider not initialized")
            return []

        try:
            # Get latest agent data from SuperAGI
            agents_data = await self.superagi_client.list_agents()

            # Update local tracking
            for agent in agents_data:
                agent_id = agent["id"]
                if agent_id in self.agents:
                    self.agents[agent_id]["status"] = agent["status"]
                else:
                    self.agents[agent_id] = {
                        "id": agent_id,
                        "config": agent.get("config", {}),
                        "status": agent["status"],
                    }

            return list(self.agents.values())
        except Exception as e:
            logger.error(f"Failed to list SuperAGI agents: {e}")
            return []

    async def _wait_for_agent_completion(
        self, agent_id: str, run_id: str, timeout: int = 600, check_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for an agent run to complete.

        Args:
            agent_id: ID of the agent
            run_id: ID of the run to wait for
            timeout: Maximum time to wait in seconds
            check_interval: How often to check status in seconds

        Returns:
            Result from the agent run
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check if timeout reached
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning(f"Timeout waiting for agent {agent_id} run {run_id}")
                return {"error": "timeout", "partial_result": None}

            # Check run status
            status = await self.superagi_client.get_run_status(run_id)

            if status in ["completed", "succeeded"]:
                # Get the run result
                result = await self.superagi_client.get_run_result(run_id)
                return result
            elif status in ["failed", "error"]:
                logger.error(f"Agent run failed: {run_id}")
                return {"error": "agent_failed", "status": status}

            # Wait before checking again
            await asyncio.sleep(check_interval)

    def _map_to_superagi_config(self, agent_config: Dict[str, Any]) -> Any:
        """
        Map Orchestra agent config to SuperAGI format.

        Args:
            agent_config: Orchestra's agent configuration

        Returns:
            SuperAGI agent configuration
        """
        # Extract fields needed for SuperAGI
        name = agent_config.get("name", "Orchestra Agent")
        description = agent_config.get("description", "")
        goal = agent_config.get(
            "goal", agent_config.get("instructions", ["Assist the user"])
        )

        # If goal is a list, join with newlines
        if isinstance(goal, list):
            goal = "\n".join(goal)

        # Create SuperAGI AgentConfig
        return self.AgentConfig(
            name=name,
            description=description,
            goal=goal,
            instruction=agent_config.get("detailed_instructions", ""),
            constraints=agent_config.get("constraints", []),
            exit_criteria=agent_config.get("exit_criteria", ["Goal is achieved"]),
            agent_type=agent_config.get("agent_type", "advanced"),
            agent_workflow=agent_config.get("workflow", "default"),
            LTM_enabled=agent_config.get("long_term_memory", True),
            max_iterations=agent_config.get("max_iterations", 25),
            scheduled=agent_config.get("scheduled", False),
        )

    def _map_tool_to_superagi(self, tool: Dict[str, Any]) -> Optional[Any]:
        """
        Map Orchestra tool to SuperAGI format.

        Args:
            tool: Orchestra tool definition

        Returns:
            SuperAGI tool configuration or None if mapping failed
        """
        try:
            # Extract tool information
            name = tool.get("name")
            description = tool.get("description", "")

            if not name:
                logger.warning("Tool missing required 'name' field")
                return None

            # Map parameters
            parameters = []
            for param in tool.get("parameters", []):
                parameters.append(
                    {
                        "name": param.get("name", ""),
                        "type": param.get("type", "string"),
                        "description": param.get("description", ""),
                        "required": param.get("required", False),
                    }
                )

            # Create SuperAGI ToolConfig
            return self.ToolConfig(
                name=name, description=description, parameters=parameters
            )
        except Exception as e:
            logger.error(f"Error mapping tool to SuperAGI format: {e}")
            return None
