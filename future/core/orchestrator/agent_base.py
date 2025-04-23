"""
Base classes for agent implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from shared.models.base_models import AgentData


class Agent(ABC):
    """
    Abstract base class for all agents in the system.
    """
    
    def __init__(self, agent_id: str, name: str, description: Optional[str] = None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Optional description of the agent's purpose
        """
        self.id = agent_id
        self.name = name
        self.description = description
        self._is_initialized = False
    
    @abstractmethod
    async def process(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """
        Process input and generate a response.
        
        Args:
            input_text: The input text to process
            context: Optional context information
            
        Returns:
            The agent's response
        """
        pass
    
    async def initialize(self) -> None:
        """
        Initialize the agent. This is called once before the agent is used.
        Override this method to perform any setup needed.
        """
        self._is_initialized = True
    
    def to_data(self) -> AgentData:
        """
        Convert this agent to a data model for serialization.
        
        Returns:
            An AgentData instance representing this agent
        """
        return AgentData(
            id=self.id,
            name=self.name,
            description=self.description,
            capabilities=[],  # Override this in subclasses
            config={}  # Override this in subclasses
        )