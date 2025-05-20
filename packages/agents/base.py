"""
Base Agent implementation for AI Orchestration System.

This module provides the BaseAgent class that all concrete agents should inherit from.
It defines the common interface and functionality for agents in the system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the AI Orchestration System.

    Provides common functionality and defines the interface that all
    concrete agent implementations must follow.
    """

    def __init__(self, config: Dict[str, Any] = None, persona: Dict[str, Any] = None):
        """
        Initialize a new agent.

        Args:
            config: Agent-specific configuration.
            persona: Optional persona configuration for the agent.
        """
        self.config = config or {}
        self.persona = persona or {}
        self.name = self.config.get("name", self.__class__.__name__)
        self.id = self.config.get("id", self.name.lower())
        logger.info(f"Initializing agent: {self.name} (ID: {self.id})")

    def setup_tools(self, tools: List[str]) -> None:
        """
        Set up tools for the agent to use.

        Args:
            tools: List of tool names to set up.
        """
        logger.info(f"Agent {self.name}: Setting up tools: {tools}")

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.

        Args:
            context: The context for the agent run, containing input parameters.

        Returns:
            Dictionary containing the agent's output.
        """
        pass

    def process_feedback(self, feedback: Dict[str, Any]) -> None:
        """
        Process feedback about the agent's performance.

        Args:
            feedback: Feedback data for the agent to process.
        """
        logger.info(f"Agent {self.name}: Received feedback: {feedback}")

    def shutdown(self) -> None:
        """
        Perform any necessary cleanup when shutting down the agent.
        """
        logger.info(f"Agent {self.name}: Shutting down")
