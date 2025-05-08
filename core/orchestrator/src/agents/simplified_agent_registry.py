"""
Simplified Agent Registry for AI Orchestration System.

This module provides a streamlined registry for managing AI agents with minimal
security overhead and simplified implementation for better performance.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional, Type, Any

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse

# Configure logging
logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """
    Basic capabilities that agents can provide.
    
    These capabilities are used for simple agent selection based on context.
    """
    
    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    GENERAL = "general"  # For basic agents that don't have specialized capabilities


class SimplifiedAgentRegistry:
    """
    Simplified registry for managing and selecting AI agents.
    
    This registry provides basic agent management and selection without
    the overhead of circuit breakers, complex lifecycle management, or
    extensive security checks.
    """
    
    def __init__(self):
        """Initialize the simplified agent registry."""
        self._agents: Dict[str, Agent] = {}
        self._agent_types: Dict[str, Type[Agent]] = {}
        self._capabilities: Dict[str, List[AgentCapability]] = {}
        self._default_agent_type = None
        logger.info("SimplifiedAgentRegistry initialized")
    
    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent instance.
        
        Args:
            agent: Agent instance to register
        """
        agent_type = agent.agent_type
        self._agents[agent_type] = agent
        
        # Store capabilities if available
        if hasattr(agent, "capabilities"):
            self._capabilities[agent_type] = agent.capabilities
        else:
            # Default to general capability
            self._capabilities[agent_type] = [AgentCapability.GENERAL]
        
        # Set as default if first agent
        if self._default_agent_type is None:
            self._default_agent_type = agent_type
            
        logger.info(f"Registered agent: {agent_type}")
    
    def register_agent_type(self, agent_type: str, agent_class: Type[Agent]) -> None:
        """
        Register an agent type.
        
        Args:
            agent_type: Type identifier
            agent_class: Agent class
        """
        self._agent_types[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")
    
    def set_default_agent_type(self, agent_type: str) -> None:
        """
        Set the default agent type.
        
        Args:
            agent_type: Default agent type
        """
        if agent_type in self._agent_types or agent_type in self._agents:
            self._default_agent_type = agent_type
            logger.info(f"Set default agent type: {agent_type}")
        else:
            logger.warning(f"Unknown agent type '{agent_type}' cannot be set as default")
    
    def get_agent(self, agent_type: Optional[str] = None) -> Agent:
        """
        Get an agent instance by type.
        
        Args:
            agent_type: Type of agent to get, or None for default
            
        Returns:
            Agent instance
            
        Raises:
            KeyError: If the agent type is not registered
        """
        # Use default if not specified
        if agent_type is None:
            agent_type = self._default_agent_type
            if agent_type is None:
                raise KeyError("No default agent type set")
        
        # Return existing instance if available
        if agent_type in self._agents:
            return self._agents[agent_type]
        
        # Create new instance if type is registered
        if agent_type in self._agent_types:
            agent = self._agent_types[agent_type]()
            self._agents[agent_type] = agent
            
            # Store capabilities if available
            if hasattr(agent, "capabilities"):
                self._capabilities[agent_type] = agent.capabilities
            else:
                # Default to general capability
                self._capabilities[agent_type] = [AgentCapability.GENERAL]
                
            return agent
        
        # Raise error if not found
        raise KeyError(f"Agent type '{agent_type}' not registered")
    
    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context.
        
        This is a simplified selection that checks for keywords in the input
        and matches them to agent capabilities.
        
        Args:
            context: Agent context
            
        Returns:
            Selected agent instance
            
        Raises:
            RuntimeError: If no agents are registered
        """
        if not self._agents and not self._agent_types:
            raise RuntimeError("No agents registered")
        
        # Check if a specific agent is requested
        requested_agent = context.metadata.get("agent_type")
        if requested_agent:
            try:
                return self.get_agent(requested_agent)
            except KeyError:
                logger.warning(f"Requested agent '{requested_agent}' not found, using selection logic")
        
        # Simple keyword-based selection
        user_input = context.user_input.lower()
        
        # Check for code generation
        if any(kw in user_input for kw in ["code", "function", "class", "programming"]):
            for agent_type, capabilities in self._capabilities.items():
                if AgentCapability.CODE_GENERATION in capabilities:
                    logger.info(f"Selected agent {agent_type} for code generation")
                    return self.get_agent(agent_type)
        
        # Check for question answering
        if "?" in user_input or any(kw in user_input for kw in ["what", "how", "why", "when", "where"]):
            for agent_type, capabilities in self._capabilities.items():
                if AgentCapability.QUESTION_ANSWERING in capabilities:
                    logger.info(f"Selected agent {agent_type} for question answering")
                    return self.get_agent(agent_type)
        
        # Check for summarization
        if any(kw in user_input for kw in ["summarize", "summary", "summarization"]):
            for agent_type, capabilities in self._capabilities.items():
                if AgentCapability.SUMMARIZATION in capabilities:
                    logger.info(f"Selected agent {agent_type} for summarization")
                    return self.get_agent(agent_type)
        
        # Default to text generation or general capability
        for agent_type, capabilities in self._capabilities.items():
            if AgentCapability.TEXT_GENERATION in capabilities:
                logger.info(f"Selected agent {agent_type} for text generation")
                return self.get_agent(agent_type)
        
        # Fall back to default agent
        logger.info(f"Using default agent: {self._default_agent_type}")
        return self.get_agent(self._default_agent_type)
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get basic status information about registered agents.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "registered_agents": list(self._agents.keys()),
            "registered_agent_types": list(self._agent_types.keys()),
            "default_agent_type": self._default_agent_type,
            "agent_count": len(self._agents),
        }


# Global agent registry instance
_simplified_agent_registry = None


def get_simplified_agent_registry() -> SimplifiedAgentRegistry:
    """
    Get the global simplified agent registry instance.
    
    Returns:
        The global SimplifiedAgentRegistry instance
    """
    global _simplified_agent_registry
    
    if _simplified_agent_registry is None:
        _simplified_agent_registry = SimplifiedAgentRegistry()
    
    return _simplified_agent_registry


def register_default_agents():
    """
    Register default agents in the simplified registry.
    
    This function registers the standard agent implementations that
    should be available by default.
    """
    from core.orchestrator.src.agents.persona_agent import PersonaAwareAgent
    from core.orchestrator.src.agents.llm_agent import LLMAgent
    
    registry = get_simplified_agent_registry()
    
    # Register agent types
    registry.register_agent_type("simple_text", PersonaAwareAgent)
    registry.register_agent_type("llm_agent", LLMAgent)
    
    # Create and register default instances
    persona_agent = PersonaAwareAgent()
    # Set capabilities if the class supports it
    if hasattr(persona_agent, "capabilities"):
        persona_agent.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.GENERAL
        ]
    registry.register_agent(persona_agent)
    
    llm_agent = LLMAgent()
    # Set capabilities if the class supports it
    if hasattr(llm_agent, "capabilities"):
        llm_agent.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.QUESTION_ANSWERING,
            AgentCapability.CODE_GENERATION
        ]
    registry.register_agent(llm_agent)
    
    # Try to register PhidataAgentWrapper if available
    try:
        from packages.agents.src.phidata_agent import PhidataAgentWrapper
        
        phidata_agent = PhidataAgentWrapper()
        # Set capabilities if the class supports it
        if hasattr(phidata_agent, "capabilities"):
            phidata_agent.capabilities = [
                AgentCapability.TEXT_GENERATION,
                AgentCapability.QUESTION_ANSWERING,
                AgentCapability.SUMMARIZATION
            ]
        registry.register_agent(phidata_agent)
        logger.info("Registered PhidataAgentWrapper instance")
    except ImportError:
        logger.info("PhidataAgentWrapper not available - skipping registration")
    
    # Set default agent type
    registry.set_default_agent_type("llm_agent")
    
    logger.info("Registered default agents in simplified registry")