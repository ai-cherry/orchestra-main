"""
Registry for managing agents in the orchestration system.
"""
import logging
from typing import Dict, List, Optional, Type

from packages.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing agents in the system.
    Allows registering, retrieving, and managing agent instances.
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls) -> 'AgentRegistry':
        """
        Get or create the singleton instance of the registry.
        
        Returns:
            The registry instance
        """
        if cls._instance is None:
            cls._instance = AgentRegistry()
        return cls._instance
    
    def __init__(self):
        """Initialize an empty agent registry."""
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent instance.
        
        Args:
            agent: The agent to register
        """
        if agent.id in self.agents:
            logger.warning(f"Replacing existing agent with ID: {agent.id}")
        
        self.agents[agent.id] = agent
        logger.info(f"Registered agent: {agent.name} (ID: {agent.id})")
    
    def register_agent_class(self, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """
        Register an agent class for later instantiation.
        
        Args:
            agent_type: A string identifier for the agent type
            agent_class: The agent class to register
        """
        self.agent_classes[agent_type] = agent_class
        logger.info(f"Registered agent class: {agent_class.__name__} as {agent_type}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            The agent instance, or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            A list of all agent instances
        """
        return list(self.agents.values())
    
    def create_agent(self, agent_type: str, agent_id: str, name: str, description: Optional[str] = None) -> Optional[BaseAgent]:
        """
        Create and register a new agent of the specified type.
        
        Args:
            agent_type: The type of agent to create
            agent_id: The ID for the new agent
            name: The name for the new agent
            description: Optional description
            
        Returns:
            The created agent, or None if the type is not registered
        """
        if agent_type not in self.agent_classes:
            logger.error(f"Unknown agent type: {agent_type}")
            return None
        
        agent_class = self.agent_classes[agent_type]
        
        # Create config for BaseAgent initialization
        config = {
            "id": agent_id,
            "name": name,
            "description": description
        }
        
        agent = agent_class(config=config)
        self.register_agent(agent)
        return agent


# Convenience functions to access the registry
def get_registry() -> AgentRegistry:
    """Get the agent registry instance."""
    return AgentRegistry.get_instance()

def register_agent(agent: BaseAgent) -> None:
    """Register an agent with the global registry."""
    get_registry().register_agent(agent)

def register_agent_class(agent_type: str, agent_class: Type[BaseAgent]) -> None:
    """Register an agent class with the global registry."""
    get_registry().register_agent_class(agent_type, agent_class)

def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """Get an agent by ID from the global registry."""
    return get_registry().get_agent(agent_id)

def get_all_agents() -> List[BaseAgent]:
    """Get all agents from the global registry."""
    return get_registry().get_all_agents()

def register_default_agents() -> None:
    """Register default agents."""
    from orchestrator.agents.echo_agent import EchoAgent
    
    # Create and register an instance of the EchoAgent
    echo_agent = EchoAgent(
        agent_id="echo-default",
        name="Echo Agent",
        description="A simple agent that echoes back user input"
    )
    register_agent(echo_agent)
    
    # Register the EchoAgent class for later instantiation
    register_agent_class("echo", EchoAgent)
    
    logger.info("Default agents registered")
