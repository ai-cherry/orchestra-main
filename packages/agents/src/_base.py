"""
Orchestra Agent Abstract Base Class

This module defines the OrchestraAgentBase abstract base class that all agent wrappers
must inherit from. It provides a standardized interface for different agent frameworks
to integrate with the Orchestra orchestration system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from packages.shared.src.llm_client.portkey_client import PortkeyClient

# Updated imports for other modules - using correct paths based on project structure
from packages.shared.src.memory.memory_manager import MemoryManager

# Updated imports to use the current module paths
from packages.shared.src.models.domain_models import AgentResponse as AgentOutput, UserRequest as AgentInput
from packages.shared.src.storage.base import ToolRegistry

logger = logging.getLogger(__name__)


class OrchestraAgentBase(ABC):
    """
    Abstract Base Class for all agent wrappers in the Orchestra system.

    All agent framework integrations must implement this interface to ensure
    standardized interaction with the core orchestration system.
    """

    agent_type: str = "base"  # Class variable to identify the type

    def __init__(
        self,
        agent_config: Dict[str, Any],
        memory_manager: MemoryManager,
        llm_client: PortkeyClient,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize the agent wrapper with required dependencies.

        Args:
            agent_config: Agent-specific configuration dict from the registry
            memory_manager: Orchestra's centralized memory management system
            llm_client: Configured LLM provider (usually via Portkey)
            tool_registry: Access to registered system tools
        """
        self.agent_config = agent_config
        self.memory = memory_manager
        self.llm = llm_client
        self.tools = tool_registry

        # Basic agent identification
        self.name = self.agent_config.get("name", self.__class__.__name__)
        self.id = self.agent_config.get("id", self.name.lower())

        logger.info(f"Initializing agent wrapper: {self.name} (ID: {self.id})")

    @abstractmethod
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent's main functionality with standardized input/output.

        This method must be implemented by all concrete agent wrappers and is
        responsible for:
        1. Translating Orchestra's AgentInput into the framework-specific format
        2. Loading relevant history/context from memory
        3. Calling the framework-specific agent execution method
        4. Persisting the interaction in memory
        5. Translating the framework's output to Orchestra's AgentOutput format

        Args:
            input_data: Standardized input containing prompt, user ID, session ID, etc.

        Returns:
            Standardized agent output with content and metadata
        """

    async def health_check(self) -> bool:
        """
        Check if the agent wrapper and its underlying framework are available.

        Returns:
            True if the agent is operational, False otherwise
        """
        return True
