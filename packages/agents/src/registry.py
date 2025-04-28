"""
Agent Registry for Orchestra

This module provides functionality to discover, register, and instantiate agent wrappers
based on configuration. It serves as a central registry for all agent wrapper types
available in the Orchestra system.
"""

import logging
import importlib
from typing import Dict, Type, Any, Optional

# Import the base class
from packages.agents.src._base import OrchestraAgentBase

# Import wrapper implementations
# Use team_wrapper import for Phidata since it enhances the original wrapper
from packages.agents.src.phidata.team_wrapper import PhidataTeamAgentWrapper

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Registry for agent wrappers in the Orchestra system.
    
    This class is responsible for:
    1. Maintaining a mapping from configuration names to wrapper classes
    2. Instantiating wrappers with the appropriate configuration and dependencies
    3. Providing discovery mechanisms for available wrapper types
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        # Dictionary mapping wrapper types to their implementing classes
        self._wrapper_classes: Dict[str, Type[OrchestraAgentBase]] = {}
        
        # Register built-in wrapper types
        self._register_builtin_wrappers()
    
    def _register_builtin_wrappers(self) -> None:
        """Register the built-in wrapper implementations."""
        # Register the enhanced Phidata wrapper with team support
        self.register_wrapper_class("phidata", PhidataTeamAgentWrapper)
        
        # Add other built-in wrappers as they are implemented
        # Example: self.register_wrapper_class("arno", ArnoAgentWrapper)
        # Example: self.register_wrapper_class("adk", ADKAgentWrapper)
    
    def register_wrapper_class(self, wrapper_type: str, wrapper_class: Type[OrchestraAgentBase]) -> None:
        """
        Register a wrapper class for a specific wrapper type.
        
        Args:
            wrapper_type: The identifier for this wrapper type in configuration
            wrapper_class: The class implementing the wrapper
        """
        if wrapper_type in self._wrapper_classes:
            logger.warning(f"Overwriting existing wrapper class for type: {wrapper_type}")
        
        self._wrapper_classes[wrapper_type] = wrapper_class
        logger.info(f"Registered wrapper class for type: {wrapper_type}")
    
    def create_agent(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        memory_manager: Any,
        llm_client: Any,
        tool_registry: Any
    ) -> Optional[OrchestraAgentBase]:
        """
        Create an agent instance based on configuration.
        
        Args:
            agent_id: Unique identifier for this agent instance
            agent_config: Configuration dictionary for the agent
            memory_manager: Memory manager instance to inject
            llm_client: LLM client instance to inject
            tool_registry: Tool registry instance to inject
            
        Returns:
            Instantiated agent wrapper, or None if creation failed
        """
        wrapper_type = agent_config.get("wrapper_type")
        if not wrapper_type:
            logger.error(f"No wrapper_type specified in config for agent: {agent_id}")
            return None
        
        if wrapper_type not in self._wrapper_classes:
            logger.error(f"Unknown wrapper_type: {wrapper_type} for agent: {agent_id}")
            return None
        
        try:
            # Get the wrapper class
            wrapper_class = self._wrapper_classes[wrapper_type]
            
            # Ensure agent_id is in the config
            config = dict(agent_config)
            config["id"] = agent_id
            
            # Create the wrapper instance
            agent = wrapper_class(
                agent_config=config,
                memory_manager=memory_manager,
                llm_client=llm_client,
                tool_registry=tool_registry
            )
            
            logger.info(f"Successfully created agent: {agent_id} with wrapper: {wrapper_type}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent: {agent_id} with wrapper: {wrapper_type}: {e}", exc_info=True)
            return None
    
    def get_available_wrapper_types(self) -> Dict[str, str]:
        """
        Get a dictionary of available wrapper types and their descriptions.
        
        Returns:
            Dictionary mapping wrapper type names to their descriptions
        """
        result = {}
        for wrapper_type, wrapper_class in self._wrapper_classes.items():
            doc = wrapper_class.__doc__ or ""
            # Extract the first line of the docstring as a short description
            description = doc.strip().split("\n")[0] if doc else f"Wrapper type: {wrapper_type}"
            result[wrapper_type] = description
        
        return result
    
    def load_wrapper_class_from_path(self, wrapper_type: str, class_path: str) -> bool:
        """
        Dynamically load and register a wrapper class from a module path.
        
        Args:
            wrapper_type: The identifier to register for this wrapper
            class_path: Full import path to the class, e.g., "mypackage.module.MyClass"
            
        Returns:
            True if successfully loaded and registered, False otherwise
        """
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            wrapper_class = getattr(module, class_name)
            
            # Ensure it's a subclass of OrchestraAgentBase
            if not issubclass(wrapper_class, OrchestraAgentBase):
                logger.error(f"Class {class_path} is not a subclass of OrchestraAgentBase")
                return False
            
            # Register the wrapper
            self.register_wrapper_class(wrapper_type, wrapper_class)
            return True
            
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to load wrapper class from path: {class_path}: {e}")
            return False

# Create a singleton instance
agent_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Returns:
        The global AgentRegistry instance
    """
    return agent_registry
