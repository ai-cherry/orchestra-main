"""
AutoGen Team Adapter for Orchestra.

This module provides integration between Orchestra and AutoGen's multi-agent
conversation protocols, enabling structured dialogues and agent specialization.
"""

import logging
import asyncio
import json
import os
from typing import Dict, List, Any, Optional, Union, Callable, Type

from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.memory.base_memory_manager import MemoryManager

# Configure logging
logger = logging.getLogger(__name__)


class AutoGenTeamAdapter:
    """
    Adapter for AutoGen's multi-agent conversation protocols.

    This adapter:
    1. Extends PhidataAgentWrapper with AutoGen's GroupChat capabilities
    2. Implements structured multi-agent conversation protocols
    3. Enables advanced agent communication patterns and reasoning
    """

    def __init__(
        self,
        agent_config: Dict[str, Any],
        memory_manager: Optional[MemoryManager] = None,
        llm_client: Any = None,
        tool_registry: Any = None,
    ):
        """
        Initialize the AutoGen Team Adapter.

        Args:
            agent_config: Agent configuration dictionary
            memory_manager: Orchestra's memory manager
            llm_client: LLM client for agent interactions
            tool_registry: Registry of available tools
        """
        self.agent_config = agent_config
        self.memory_manager = memory_manager
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.autogen_agents = []
        self.group_chat = None
        self.chat_manager = None
        self._initialized = False
        self._is_team = True
        logger.info("AutoGenTeamAdapter initialized with config")

    async def initialize(self) -> bool:
        """Initialize the AutoGen integration."""
        try:
            # Import AutoGen modules
            try:
                import autogen
                from autogen import (
                    Agent,
                    ConversableAgent,
                    AssistantAgent,
                    UserProxyAgent,
                    GroupChat,
                    GroupChatManager,
                )

                self.autogen = autogen
                self.Agent = Agent
                self.ConversableAgent = ConversableAgent
                self.AssistantAgent = AssistantAgent
                self.UserProxyAgent = UserProxyAgent
                self.GroupChat = GroupChat
                self.GroupChatManager = GroupChatManager
            except ImportError:
                logger.warning(
                    "AutoGen library not available. Install with: pip install pyautogen"
                )
                return False

            # Initialize team configuration
            self.team_config = self.agent_config.get("autogen_team", {})
            if not self.team_config:
                logger.error("No AutoGen team configuration found")
                return False

            # Create AutoGen agents
            await self._create_autogen_agents()

            # Set up GroupChat with all agents
            self._setup_group_chat()

            self._initialized = True
            logger.info("AutoGenTeamAdapter initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AutoGenTeamAdapter: {e}")
            return False

    async def run(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Run the AutoGen team conversation.

        Args:
            prompt: The input prompt/query
            **kwargs: Additional arguments

        Returns:
            Result from the conversation
        """
        if not self._initialized:
            logger.warning("AutoGenTeamAdapter not initialized")
            return {"error": "Not initialized"}

        try:
            # Initialize chat history if provided
            memory_id = kwargs.get("memory_id")
            session_id = kwargs.get("session_id")
            user_id = kwargs.get("user_id", "default_user")

            # Set up conversation context
            context = {
                "prompt": prompt,
                "memory_id": memory_id,
                "session_id": session_id,
                "user_id": user_id,
            }

            # Run the group chat
            result = await self._run_group_chat(prompt, context)

            # Process and return the result
            return self._process_result(result)
        except Exception as e:
            logger.error(f"Error running AutoGen team: {e}")
            return {"error": str(e)}

    async def _create_autogen_agents(self) -> None:
        """Create AutoGen agents from configuration."""
        # Get agent definitions from config
        agent_configs = self.team_config.get("agents", [])
        if not agent_configs:
            raise ValueError("No agent configurations found in team_config.agents")

        for idx, agent_config in enumerate(agent_configs):
            # Get agent type and name
            agent_type = agent_config.get("type", "assistant")
            name = agent_config.get("name", f"Agent_{idx}")

            # Create appropriate agent type
            if agent_type == "assistant":
                agent = await self._create_assistant_agent(agent_config)
            elif agent_type == "user_proxy":
                agent = await self._create_user_proxy_agent(agent_config)
            else:
                logger.warning(
                    f"Unknown agent type: {agent_type}, creating default assistant agent"
                )
                agent = await self._create_assistant_agent(agent_config)

            if agent:
                self.autogen_agents.append(agent)
                logger.info(f"Created AutoGen agent: {name} of type {agent_type}")

        if not self.autogen_agents:
            raise ValueError("Failed to create any AutoGen agents")

    async def _create_assistant_agent(self, agent_config: Dict[str, Any]) -> Any:
        """Create an AutoGen AssistantAgent."""
        name = agent_config.get("name", "Assistant")
        system_message = agent_config.get("system_message", "")

        # Get LLM configuration
        llm_config = self._get_llm_config(agent_config)

        # Create the agent
        return self.AssistantAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER",
        )

    async def _create_user_proxy_agent(self, agent_config: Dict[str, Any]) -> Any:
        """Create an AutoGen UserProxyAgent."""
        name = agent_config.get("name", "UserProxy")
        system_message = agent_config.get("system_message", "")

        # Process tools if provided
        tools = []
        for tool_config in agent_config.get("tools", []):
            tool_func = await self._create_tool_function(tool_config)
            if tool_func:
                tools.append(tool_func)

        # Create the agent
        return self.UserProxyAgent(
            name=name,
            system_message=system_message,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            function_map={t.__name__: t for t in tools},
        )

    async def _create_tool_function(
        self, tool_config: Dict[str, Any]
    ) -> Optional[Callable]:
        """Create a tool function from configuration."""
        try:
            tool_name = tool_config.get("name")
            tool_description = tool_config.get("description", "")

            if not tool_name:
                logger.warning("Tool missing required 'name' field")
                return None

            # Check if tool is in registry
            if self.tool_registry and hasattr(self.tool_registry, "get_tool"):
                registry_tool = self.tool_registry.get_tool(tool_name)
                if registry_tool:
                    # Adapt registry tool to AutoGen function signature
                    async def registry_tool_adapter(*args, **kwargs):
                        return await registry_tool.execute(*args, **kwargs)

                    # Set proper name and docstring
                    registry_tool_adapter.__name__ = tool_name
                    registry_tool_adapter.__doc__ = tool_description

                    return registry_tool_adapter

            # If custom code is provided
            if "code" in tool_config:
                code = tool_config["code"]
                # WARNING: eval is generally unsafe, this is for demonstration
                # In production, use a safer mechanism to create functions
                namespace = {}
                exec(code, namespace)
                if tool_name in namespace:
                    return namespace[tool_name]

            logger.warning(f"Could not create tool function for {tool_name}")
            return None
        except Exception as e:
            logger.error(f"Error creating tool function: {e}")
            return None

    def _setup_group_chat(self) -> None:
        """Set up the GroupChat with all agents."""
        # Get GroupChat configuration
        max_rounds = self.team_config.get("max_rounds", 10)
        speaker_selection_method = self.team_config.get("speaker_selection", "auto")

        # Create the GroupChat
        self.group_chat = self.GroupChat(
            agents=self.autogen_agents,
            messages=[],
            max_round=max_rounds,
            speaker_selection_method=speaker_selection_method,
        )

        # Create the GroupChatManager if specified
        if self.team_config.get("use_manager", True):
            llm_config = self._get_llm_config(
                self.team_config.get("manager_config", {})
            )

            self.chat_manager = self.GroupChatManager(
                groupchat=self.group_chat, llm_config=llm_config
            )

    async def _run_group_chat(
        self, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the GroupChat with the prompt."""
        # Determine which agent should initiate the chat
        initiator = self.autogen_agents[0]  # Default to first agent

        # Check if a specific initiator is configured
        initiator_name = self.team_config.get("initiator")
        if initiator_name:
            for agent in self.autogen_agents:
                if agent.name == initiator_name:
                    initiator = agent
                    break

        # Start the chat
        start_time = asyncio.get_event_loop().time()

        try:
            if self.chat_manager:
                # Use the manager to coordinate the conversation
                result = await asyncio.to_thread(
                    self.chat_manager.run, message=prompt, sender=initiator
                )
            else:
                # Direct group chat without manager
                result = await asyncio.to_thread(
                    self.group_chat.run, message=prompt, sender=initiator
                )

            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"GroupChat completed in {elapsed:.2f} seconds")

            # Create a structured result
            return {
                "content": result,
                "messages": self.group_chat.messages,
                "elapsed_seconds": elapsed,
                "success": True,
            }
        except Exception as e:
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.error(f"Error in GroupChat: {e}")

            return {
                "content": str(e),
                "messages": self.group_chat.messages
                if hasattr(self.group_chat, "messages")
                else [],
                "elapsed_seconds": elapsed,
                "success": False,
                "error": str(e),
            }

    def _process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process the GroupChat result into a standardized format."""
        # Extract and format messages for storage
        messages = []
        for msg in result.get("messages", []):
            if isinstance(msg, dict):
                messages.append(msg)
            else:
                # Convert to dictionary if not already
                try:
                    messages.append(
                        {
                            "role": getattr(msg, "role", "unknown"),
                            "content": getattr(msg, "content", str(msg)),
                            "sender": getattr(msg, "sender", "unknown"),
                            "timestamp": getattr(msg, "timestamp", None),
                        }
                    )
                except:
                    # Fallback if conversion fails
                    messages.append({"content": str(msg)})

        # Construct final response
        response = {
            "result": result.get("content", ""),
            "messages": messages,
            "success": result.get("success", False),
            "elapsed_seconds": result.get("elapsed_seconds", 0),
        }

        # Add error if present
        if "error" in result:
            response["error"] = result["error"]

        return response

    def _get_llm_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get LLM configuration for AutoGen agents."""
        # If specific LLM config is provided, use it
        if "llm_config" in config:
            return config["llm_config"]

        # Otherwise construct default config
        model = config.get("model", "gpt-4o")

        # Basic config for demonstration
        llm_config = {
            "config_list": [
                {"model": model, "api_key": os.environ.get("OPENAI_API_KEY", "")}
            ],
            "temperature": config.get("temperature", 0.2),
            "timeout": config.get("timeout", 120),
            "cache_seed": config.get("cache_seed", 42),
        }

        return llm_config
