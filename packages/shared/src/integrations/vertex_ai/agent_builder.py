"""
Vertex AI Agent Builder Integration for Orchestra.

This module provides integration between Orchestra and Google's Vertex AI Agent Builder
platform, enabling enterprise-grade agent management, analytics, and deployment.
"""

import logging
import os
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class VertexAIAgentBuilder:
    """
    Integration with Google's Vertex AI Agent Builder.

    This integration:
    1. Provides enterprise-grade agent deployment capabilities
    2. Enables analytics and monitoring for agent performance
    3. Implements A/B testing for agent optimization
    4. Connects to Google's compliance and security features
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Vertex AI Agent Builder integration.

        Args:
            config: Configuration options for the integration
        """
        self.config = config or {}
        self.vertex_client = None
        self.project_id = self.config.get("project_id")
        self.region = self.config.get("region", "us-central1")
        self.agents = {}  # Map of agent_id -> Vertex agent
        self._initialized = False
        logger.info("VertexAIAgentBuilder initialized with config")

    async def initialize(self) -> bool:
        """Initialize connection to Vertex AI."""
        try:
            # Import Vertex AI client libraries
            try:
                from google.cloud import aiplatform
                from google.cloud.aiplatform.preview.language_models import (
                    ChatModel,
                    CodeChatModel,
                    GroundingSource,
                    TextGenerationModel,
                )
                from vertexai.language_models import ChatMessage
                from vertexai.preview.generative_models import (
                    Content,
                    GenerationConfig,
                    GenerativeModel,
                    Part,
                )

                self.aiplatform = aiplatform
                self.ChatModel = ChatModel
                self.TextGenerationModel = TextGenerationModel
                self.GroundingSource = GroundingSource
                self.CodeChatModel = CodeChatModel
                self.GenerativeModel = GenerativeModel
                self.Content = Content
                self.Part = Part
                self.GenerationConfig = GenerationConfig
                self.ChatMessage = ChatMessage
            except ImportError:
                logger.warning("Vertex AI libraries not available. Install with: pip install google-cloud-aiplatform")
                return False

            # Initialize Vertex AI client
            if not self.project_id:
                logger.warning("Project ID not provided")

                # Try to get from environment
                self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
                if not self.project_id:
                    logger.error("No project ID available")
                    return False

            # Initialize Vertex AI SDK
            self.aiplatform.init(project=self.project_id, location=self.region)

            # Import Agent builder libraries
            try:
                from vertexai.agents import (
                    Agent,
                    ExecutionConfig,
                    FunctionDeclaration,
                    Parameter,
                    Tool,
                )

                self.Agent = Agent
                self.Tool = Tool
                self.FunctionDeclaration = FunctionDeclaration
                self.Parameter = Parameter
                self.ExecutionConfig = ExecutionConfig

                logger.info("Vertex AI Agent Builder libraries loaded successfully")
            except ImportError:
                logger.warning(
                    "Vertex AI Agent Builder libraries not available. Make sure to use the latest version of the SDK."
                )

            self._initialized = True
            logger.info(f"Connected to Vertex AI project: {self.project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI Agent Builder: {e}")
            return False

    async def create_agent(self, agent_config: Dict[str, Any], tools: List[Dict[str, Any]] = None) -> str:
        """
        Create a new agent using Vertex AI Agent Builder.

        Args:
            agent_config: Agent configuration
            tools: List of tools to provide to the agent

        Returns:
            ID of the created agent
        """
        if not self._initialized:
            logger.warning("VertexAIAgentBuilder not initialized")
            return None

        try:
            # Extract agent details
            display_name = agent_config.get("name", "Orchestra Agent")
            description = agent_config.get("description", "Agent created by Orchestra")

            # Process tools if provided
            agent_tools = []
            if tools:
                for tool_config in tools:
                    vertex_tool = await self._create_vertex_tool(tool_config)
                    if vertex_tool:
                        agent_tools.append(vertex_tool)

            # Create Vertex AI Agent
            vertex_agent = self.Agent.create(
                display_name=display_name,
                description=description,
                tools=agent_tools if agent_tools else None,
            )

            # Store reference to the agent
            agent_id = vertex_agent.name.split("/")[-1]
            self.agents[agent_id] = {
                "id": agent_id,
                "vertex_agent": vertex_agent,
                "config": agent_config,
            }

            logger.info(f"Created Vertex AI Agent: {display_name} (ID: {agent_id})")
            return agent_id
        except Exception as e:
            logger.error(f"Error creating Vertex AI Agent: {e}")
            return None

    async def deploy_agent(self, agent_id: str, deployment_name: str = "production") -> bool:
        """
        Deploy an agent to a Vertex AI endpoint.

        Args:
            agent_id: ID of the agent to deploy
            deployment_name: Name for the deployment

        Returns:
            Whether the deployment was successful
        """
        if not self._initialized:
            logger.warning("VertexAIAgentBuilder not initialized")
            return False

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            # Get the Vertex agent
            agent_info = self.agents[agent_id]
            vertex_agent = agent_info["vertex_agent"]

            # Deploy the agent
            deployment = vertex_agent.deploy(display_name=deployment_name)

            # Update agent info with deployment details
            agent_info["deployment"] = {
                "name": deployment_name,
                "endpoint": deployment.name,
            }

            logger.info(f"Deployed agent {agent_id} to endpoint: {deployment.name}")
            return True
        except Exception as e:
            logger.error(f"Error deploying Vertex AI Agent: {e}")
            return False

    async def run_agent(self, agent_id: str, prompt: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run an agent with a prompt and optional parameters.

        Args:
            agent_id: ID of the agent to run
            prompt: The prompt to send to the agent
            parameters: Optional parameters for the agent

        Returns:
            Agent response
        """
        if not self._initialized:
            logger.warning("VertexAIAgentBuilder not initialized")
            return {"error": "Not initialized"}

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return {"error": f"Agent {agent_id} not found"}

            # Get the Vertex agent
            agent_info = self.agents[agent_id]
            vertex_agent = agent_info["vertex_agent"]

            # Check if agent is deployed
            if "deployment" not in agent_info:
                logger.warning(f"Agent {agent_id} is not deployed")
                # Create a conversation using the agent directly
                conversation = vertex_agent.start_conversation()
            else:
                # Get the deployed agent
                deployment_name = agent_info["deployment"]["endpoint"]
                conversation = self.Agent.get_deployed_agent(deployment_name).start_conversation()

            # Run the agent with the prompt
            response = conversation.send_message(message=prompt, tool_params=parameters)

            # Process the response
            result = {
                "text": response.text,
                "tool_calls": response.tool_calls if hasattr(response, "tool_calls") else [],
            }

            # Add citation information if available
            if hasattr(response, "citations") and response.citations:
                result["citations"] = [
                    {
                        "start_index": citation.start_index,
                        "end_index": citation.end_index,
                        "url": citation.url,
                        "title": citation.title,
                        "license": citation.license,
                    }
                    for citation in response.citations
                ]

            return result
        except Exception as e:
            logger.error(f"Error running Vertex AI Agent: {e}")
            return {"error": str(e)}

    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents in the project.

        Returns:
            List of agent information dictionaries
        """
        if not self._initialized:
            logger.warning("VertexAIAgentBuilder not initialized")
            return []

        try:
            # Get agents from Vertex AI
            vertex_agents = self.Agent.list()

            # Process agents
            agents = []
            for vertex_agent in vertex_agents:
                agent_id = vertex_agent.name.split("/")[-1]

                # Check if we have local info for this agent
                if agent_id in self.agents:
                    agents.append(self.agents[agent_id])
                else:
                    # Create info for newly discovered agent
                    agents.append(
                        {
                            "id": agent_id,
                            "vertex_agent": vertex_agent,
                            "display_name": vertex_agent.display_name,
                            "description": vertex_agent.description,
                        }
                    )

                    # Add to local tracking
                    self.agents[agent_id] = agents[-1]

            return agents
        except Exception as e:
            logger.error(f"Error listing Vertex AI Agents: {e}")
            return []

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent from Vertex AI.

        Args:
            agent_id: ID of the agent to delete

        Returns:
            Whether the deletion was successful
        """
        if not self._initialized:
            logger.warning("VertexAIAgentBuilder not initialized")
            return False

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            # Get the Vertex agent
            agent_info = self.agents[agent_id]
            vertex_agent = agent_info["vertex_agent"]

            # Delete deployments if any
            if "deployment" in agent_info:
                # Undeploy the agent
                deployment_name = agent_info["deployment"]["endpoint"]
                self.Agent.get_deployed_agent(deployment_name).undeploy()
                logger.info(f"Undeployed agent {agent_id} from {deployment_name}")

            # Delete the agent
            vertex_agent.delete()

            # Remove from local tracking
            del self.agents[agent_id]

            logger.info(f"Deleted Vertex AI Agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting Vertex AI Agent: {e}")
            return False

    async def _create_vertex_tool(self, tool_config: Dict[str, Any]) -> Any:
        """Create a Vertex AI tool from configuration."""
        try:
            # Extract tool details
            name = tool_config.get("name")
            description = tool_config.get("description", "")

            if not name:
                logger.warning("Tool missing required 'name' field")
                return None

            # Process parameters
            parameters = []
            for param_config in tool_config.get("parameters", []):
                param_name = param_config.get("name")
                param_type = param_config.get("type", "string")
                param_description = param_config.get("description", "")

                vertex_param = self.Parameter(
                    parameter_id=param_name,
                    type=param_type,
                    description=param_description,
                    required=param_config.get("required", False),
                )
                parameters.append(vertex_param)

            # Define the function declaration
            function_declaration = self.FunctionDeclaration(name=name, description=description, parameters=parameters)

            # Create the tool with function declaration
            tool = self.Tool(function_declarations=[function_declaration])

            return tool
        except Exception as e:
            logger.error(f"Error creating Vertex AI tool: {e}")
            return None

    async def create_conversation(self, agent_id: str) -> Any:
        """
        Create a conversation with a deployed agent.

        Args:
            agent_id: ID of the agent to converse with

        Returns:
            Conversation object or None if creation failed
        """
        if not self._initialized:
            logger.warning("VertexAIAgentBuilder not initialized")
            return None

        try:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return None

            # Get the Vertex agent
            agent_info = self.agents[agent_id]
            vertex_agent = agent_info["vertex_agent"]

            # Check if agent is deployed
            if "deployment" in agent_info:
                # Get the deployed agent
                deployment_name = agent_info["deployment"]["endpoint"]
                conversation = self.Agent.get_deployed_agent(deployment_name).start_conversation()
            else:
                # Create a conversation using the agent directly
                conversation = vertex_agent.start_conversation()

            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation with Vertex AI Agent: {e}")
            return None
