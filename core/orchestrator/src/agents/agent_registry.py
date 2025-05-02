"""
Agent Registry for AI Orchestration System.

This module provides a registry for agent implementations, allowing dynamic
selection of agents based on context, with circuit breaker pattern for resilience.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Callable, Type
import random
import time
from datetime import datetime

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.resilience.circuit_breaker import get_circuit_breaker
from core.orchestrator.src.resilience.tasks import get_fallback_handler
from core.orchestrator.src.resilience.incident_reporter import get_incident_reporter

# Configure logging
logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for agent implementations.

    This class maintains a registry of agent implementations and provides
    mechanisms for selecting appropriate agents based on context.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, Agent] = {}
        self._agent_types: Dict[str, Type[Agent]] = {}
        self._default_agent_type = "simple_text"
        self._environment = os.environ.get("DEPLOYMENT_ENVIRONMENT", "development")

        logger.info(f"AgentRegistry initialized for environment: {self._environment}")

    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent instance.

        Args:
            agent: Agent instance to register
        """
        agent_type = agent.agent_type
        self._agents[agent_type] = agent
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
            logger.warning(
                f"Unknown agent type '{agent_type}' cannot be set as default"
            )

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

        # Return existing instance if available
        if agent_type in self._agents:
            return self._agents[agent_type]

        # Create new instance if type is registered
        if agent_type in self._agent_types:
            agent = self._agent_types[agent_type]()
            self._agents[agent_type] = agent
            return agent

        # Raise error if not found
        raise KeyError(f"Agent type '{agent_type}' not registered")

    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        Select the most appropriate agent for a context with circuit breaker protection.

        This method examines the context and selects the agent best suited
        for handling it. If multiple agents are suitable, one is chosen
        based on heuristics. The selected agent is wrapped with circuit breaker
        protection to handle failures gracefully.

        Args:
            context: Agent context

        Returns:
            Selected agent instance with circuit breaker protection

        Raises:
            RuntimeError: If no agents are registered
        """
        if not self._agents and not self._agent_types:
            raise RuntimeError("No agents registered")

        # ENHANCE: Implement more sophisticated selection logic based on context

        # Select the appropriate agent
        try:
            selected_agent = self.get_agent(self._default_agent_type)
            agent_id = f"{selected_agent.agent_type}"
        except KeyError:
            # Fall back to any registered agent if default not available
            if self._agents:
                agent_type = next(iter(self._agents))
                logger.warning(f"Default agent not available, using {agent_type}")
                selected_agent = self._agents[agent_type]
                agent_id = f"{agent_type}"
            # Fall back to creating first registered type
            elif self._agent_types:
                agent_type = next(iter(self._agent_types))
                logger.warning(f"No agent instances available, creating {agent_type}")
                selected_agent = self._agent_types[agent_type]()
                self._agents[agent_type] = selected_agent
                agent_id = f"{agent_type}"
            else:
                raise RuntimeError("No agent types registered")

        # Create a resilient agent wrapper with circuit breaker protection
        return ResilienceAgentWrapper(selected_agent, agent_id)

    def get_environment(self) -> str:
        """
        Get the current deployment environment.
        
        Returns:
            The current deployment environment (e.g., 'development', 'staging', 'production')
        """
        return self._environment
        
    def get_agent_status(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the status of agents including circuit state.
        
        Args:
            agent_id: Optional specific agent ID to get status for
            
        Returns:
            Dictionary with agent status information
        """
        result = {
            "environment": self._environment,
            "default_agent_type": self._default_agent_type,
            "registered_agents": list(self._agents.keys()),
            "registered_agent_types": list(self._agent_types.keys()),
        }
        
        # Add circuit breaker status if available
        try:
            circuit_breaker = get_circuit_breaker()
            
            if agent_id:
                # Get status for specific agent
                if agent_id in self._agents:
                    agent_status = circuit_breaker.get_agent_status(agent_id)
                    result["circuit_status"] = agent_status
                else:
                    result["circuit_status"] = {"error": f"Agent {agent_id} not found"}
            else:
                # Get status for all agents
                circuit_status = {}
                for agent_id in self._agents.keys():
                    circuit_status[agent_id] = circuit_breaker.get_agent_status(agent_id)
                result["circuit_status"] = circuit_status
        except Exception as e:
            logger.error(f"Failed to get circuit breaker status: {str(e)}")
            result["circuit_status"] = {"error": str(e)}
            
        return result


class ResilienceAgentWrapper(Agent):
    """
    Wrapper for agents that adds circuit breaker protection.
    
    This wrapper implements the Agent interface and adds circuit breaker
    protection to the wrapped agent, with fallback to vertex-agent when
    the circuit is open.
    """
    
    def __init__(self, agent: Agent, agent_id: str):
        """
        Initialize the wrapper.
        
        Args:
            agent: The agent to wrap
            agent_id: ID for the agent in the circuit breaker
        """
        self.agent = agent
        self.agent_id = agent_id
        self.circuit_breaker = get_circuit_breaker()
        self.incident_reporter = get_incident_reporter()
        
        # Initialize metrics client for the circuit breaker if not already set
        from core.orchestrator.src.resilience.monitoring import get_monitoring_client
        self.circuit_breaker.set_metrics_client(get_monitoring_client())
        
        logger.info(f"Created resilience wrapper for agent {agent_id}")
    
    @property
    def agent_type(self) -> str:
        """Get the agent type."""
        return self.agent.agent_type
    
    @property
    def name(self) -> str:
        """Get the agent name."""
        return f"resilient:{self.agent.name}" if hasattr(self.agent, 'name') else f"resilient:{self.agent_id}"
    
    async def process(self, user_input: str) -> str:
        """
        Process user input with circuit breaker protection.
        
        Args:
            user_input: User input to process
            
        Returns:
            Response from agent or fallback
        """
        # Create the primary operation (calls the wrapped agent)
        async def primary_operation():
            start_time = time.monotonic()
            try:
                return await self.agent.process(user_input)
            except Exception as e:
                # Create incident report for the failure
                try:
                    self.incident_reporter.report_incident(
                        agent_id=self.agent_id,
                        incident_type="agent_failure",
                        details={
                            "error": str(e),
                            "user_input": user_input[:100] + "..." if len(user_input) > 100 else user_input,
                            "execution_time_ms": int((time.monotonic() - start_time) * 1000)
                        }
                    )
                except Exception as log_err:
                    logger.warning(f"Failed to report incident: {str(log_err)}")
                
                # Re-raise to let circuit breaker handle it
                raise
        
        # Create the fallback operation (uses vertex-agent)
        async def fallback_operation():
            # Get the fallback handler
            try:
                fallback_handler = get_fallback_handler()
                
                # Report fallback activation
                self.incident_reporter.report_fallback_activation(
                    agent_id=self.agent_id,
                    user_input=user_input,
                    fallback_agent_id="vertex-agent"
                )
                
                return await fallback_handler.process(user_input)
            except Exception as e:
                logger.error(f"Fallback operation failed: {str(e)}")
                
                # Last resort - return a graceful error message
                return (
                    "I'm having trouble processing your request at the moment. "
                    "Our systems are experiencing some issues, but the team has been notified. "
                    "Please try again later or contact support if this persists."
                )
        
        # Execute with circuit breaker protection
        try:
            return await self.circuit_breaker.execute(
                agent_id=self.agent_id,
                operation=primary_operation,
                fallback_operation=fallback_operation
            )
        except Exception as e:
            logger.error(f"Circuit breaker execution failed: {str(e)}")
            
            # Last resort fallback
            try:
                return await fallback_operation()
            except Exception:
                return (
                    "I apologize, but I'm unable to process your request at this time. "
                    "We're experiencing technical difficulties, and our team has been notified. "
                    "Please try again later."
                )

# Global agent registry instance
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    This function provides a simple dependency injection mechanism
    for accessing the agent registry throughout the application.

    Returns:
        The global AgentRegistry instance
    """
    global _agent_registry

    if _agent_registry is None:
        _agent_registry = AgentRegistry()

    return _agent_registry


def register_default_agents():
    """
    Register default agents in the registry.

    This function registers the standard agent implementations that
    should be available by default.
    """
    from core.orchestrator.src.agents.agent_base import Agent
    from core.orchestrator.src.agents.persona_agent import PersonaAwareAgent
    from core.orchestrator.src.agents.llm_agent import LLMAgent

    registry = get_agent_registry()

    # Register agent types
    registry.register_agent_type("simple_text", PersonaAwareAgent)
    registry.register_agent_type("llm_agent", LLMAgent)
    
    # Try to register PhidataAgentWrapper if available
    try:
        from packages.agents.src.phidata_agent import PhidataAgentWrapper, PHIDATA_AVAILABLE
        
        if PHIDATA_AVAILABLE:
            registry.register_agent_type("phidata", PhidataAgentWrapper)
            logger.info("Registered PhidataAgentWrapper type")
        else:
            logger.warning("Phidata dependencies available but PHIDATA_AVAILABLE flag is False")
            
    except ImportError as e:
        logger.warning(f"PhidataAgentWrapper not available - skipping registration: {str(e)}")

    # Create and register default instances
    registry.register_agent(PersonaAwareAgent())
    registry.register_agent(LLMAgent())
    
    # Try to create and register a PhidataAgentWrapper instance if available
    try:
        from packages.agents.src.phidata_agent import PhidataAgentWrapper, PHIDATA_AVAILABLE
        
        if PHIDATA_AVAILABLE:
            # Get settings to determine memory configuration
            from core.orchestrator.src.config.config import get_settings
            settings = get_settings()
            
            # Configure based on environment 
            environment = os.environ.get("DEPLOYMENT_ENVIRONMENT", "development")
            
            # This would normally use proper initialization with dependencies
            phidata_agent_config = {
                "name": f"PhidataAgent-{environment}",
                "markdown": True,
                "show_tool_calls": True,
                # Set lower temperature for production
                "temperature": 0.5 if environment == "production" else 0.7
            }

            # Get memory manager if available through dependency injection
            memory_manager = None
            llm_client = None
            tool_registry = None
            
            try:
                from core.orchestrator.src.services.memory_service import get_memory_manager
                memory_manager = get_memory_manager()
                logger.info("Successfully loaded memory manager for PhidataAgentWrapper")
            except (ImportError, Exception) as memory_err:
                logger.warning(f"Failed to load memory manager for PhidataAgentWrapper: {memory_err}")
                
            registry.register_agent(PhidataAgentWrapper(
                agent_config=phidata_agent_config,
                memory_manager=memory_manager,
                llm_client=llm_client,
                tool_registry=tool_registry
            ))
            logger.info(f"Registered PhidataAgentWrapper instance for environment: {environment}")
    except (ImportError, Exception) as e:
        logger.warning(f"Failed to register PhidataAgentWrapper instance: {e}")

    # Set default agent type
    from core.orchestrator.src.config.config import get_settings

    settings = get_settings()
    default_agent_type = getattr(settings, "DEFAULT_AGENT_TYPE", "simple_text")
    registry.set_default_agent_type(default_agent_type)

    logger.info("Registered default agents")
