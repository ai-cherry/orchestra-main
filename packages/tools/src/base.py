"""
Tool Registry and Base Tool Definitions for Orchestra

This module provides the base Tool class that all tools must inherit from,
as well as the ToolRegistry which manages tool registration and instantiation.
It is designed to be compatible with Phidata's tool system while providing
Orchestra-specific functionality.
"""

import logging
import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable, Union

logger = logging.getLogger(__name__)


class OrchestraTool(ABC):
    """
    Abstract base class for all tools in the Orchestra system.

    All tool implementations must inherit from this class to ensure
    compatibility with the Orchestra tool registry and agent systems.
    This class is designed to be compatible with Phidata's Tool class
    while providing Orchestra-specific functionality.
    """

    # Phidata-compatible class attributes
    name: str = ""
    description: str = ""

    def __init__(self, **kwargs):
        """
        Initialize the tool with optional configuration parameters.

        Args:
            **kwargs: Configuration parameters for the tool
        """
        # Set any configuration parameters as instance attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

        # If name wasn't provided in kwargs, use the class attribute
        if not hasattr(self, "name") or not self.name:
            self.name = self.__class__.name

        # If description wasn't provided in kwargs, use the class attribute
        if not hasattr(self, "description") or not self.description:
            self.description = self.__class__.description

        logger.debug(f"Initialized tool: {self.name}")

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool's main functionality.

        This method must be implemented by all concrete tool classes and is
        responsible for performing the tool's primary function.

        Args:
            **kwargs: Arguments specific to the tool implementation

        Returns:
            Dictionary containing the tool's output and any relevant metadata
        """
        pass

    def to_phidata_tool(self) -> Any:
        """
        Convert this Orchestra tool to a Phidata-compatible tool.

        This method creates a Phidata Tool instance that wraps this
        Orchestra tool, allowing it to be used with Phidata agents.

        Returns:
            A Phidata-compatible Tool instance
        """
        try:
            # Import the Phidata Tool class
            from phi.tools import Tool as PhidataTool

            # Create a wrapper function that calls this tool's run method
            def tool_function(**kwargs):
                return self.run(**kwargs)

            # Return a Phidata Tool that wraps our function
            phidata_tool = PhidataTool(
                name=self.name,
                description=self.description,
                function=tool_function,
            )

            return phidata_tool

        except ImportError:
            logger.warning("Phidata not installed, cannot convert to Phidata tool")
            return None
        except Exception as e:
            logger.error(f"Error converting to Phidata tool: {e}")
            return None

    @classmethod
    def get_phidata_decorator(cls) -> Optional[Callable]:
        """
        Get the Phidata tool decorator for directly defining Phidata-compatible tools.

        This class method returns the @tool decorator from Phidata if it's available,
        allowing tools to be defined with Phidata's native decorator syntax.

        Returns:
            The Phidata tool decorator, or None if Phidata is not installed
        """
        try:
            from phi.tools import tool

            return tool
        except ImportError:
            return None


class ToolRegistry:
    """
    Registry for tools in the Orchestra system.

    This class is responsible for:
    1. Maintaining a mapping from tool types to their implementing classes
    2. Instantiating tools with the appropriate configuration
    3. Providing tools in the format needed by different agent frameworks
    """

    def __init__(self):
        """Initialize the tool registry."""
        # Dictionary mapping tool types to their implementing classes
        self._tool_classes: Dict[str, Type[OrchestraTool]] = {}

        # Dictionary of instantiated tool instances
        self._tool_instances: Dict[str, OrchestraTool] = {}

        logger.info("Tool registry initialized")

    def register_tool_class(
        self, tool_type: str, tool_class: Type[OrchestraTool]
    ) -> None:
        """
        Register a tool class for a specific tool type.

        Args:
            tool_type: The identifier for this tool type in configuration
            tool_class: The class implementing the tool
        """
        if tool_type in self._tool_classes:
            logger.warning(f"Overwriting existing tool class for type: {tool_type}")

        self._tool_classes[tool_type] = tool_class
        logger.info(f"Registered tool class for type: {tool_type}")

    def create_tool(
        self, tool_id: str, tool_config: Dict[str, Any]
    ) -> Optional[OrchestraTool]:
        """
        Create a tool instance based on configuration.

        Args:
            tool_id: Unique identifier for this tool instance
            tool_config: Configuration dictionary for the tool

        Returns:
            Instantiated tool, or None if creation failed
        """
        tool_type = tool_config.get("type")
        if not tool_type:
            logger.error(f"No tool_type specified in config for tool: {tool_id}")
            return None

        # Check if tool type is registered directly
        if tool_type in self._tool_classes:
            tool_class = self._tool_classes[tool_type]
        else:
            # Try to import the tool class dynamically
            try:
                module_path, class_name = tool_type.rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)

                # Ensure it's a subclass of OrchestraTool
                if not issubclass(tool_class, OrchestraTool):
                    logger.error(
                        f"Class {tool_type} is not a subclass of OrchestraTool"
                    )
                    return None

                # Register the tool class for future use
                self.register_tool_class(tool_type, tool_class)

            except (ImportError, AttributeError, ValueError) as e:
                logger.error(f"Failed to import tool class: {tool_type}: {e}")
                return None

        try:
            # Extract tool parameters from config
            tool_params = tool_config.get("params", {})

            # Create the tool instance
            tool = tool_class(**tool_params)

            # Store the instance
            self._tool_instances[tool_id] = tool

            logger.info(f"Successfully created tool: {tool_id} of type: {tool_type}")
            return tool

        except Exception as e:
            logger.error(
                f"Failed to create tool: {tool_id} of type: {tool_type}: {e}",
                exc_info=True,
            )
            return None

    def get_tool(self, tool_id: str) -> Optional[OrchestraTool]:
        """
        Get a tool instance by its ID.

        Args:
            tool_id: The unique identifier for the tool

        Returns:
            The tool instance, or None if not found
        """
        return self._tool_instances.get(tool_id)

    def get_all_tools(self) -> Dict[str, OrchestraTool]:
        """
        Get all registered tool instances.

        Returns:
            Dictionary mapping tool IDs to tool instances
        """
        return dict(self._tool_instances)

    def get_available_tool_types(self) -> Dict[str, str]:
        """
        Get a dictionary of available tool types and their descriptions.

        Returns:
            Dictionary mapping tool type names to their descriptions
        """
        result = {}
        for tool_type, tool_class in self._tool_classes.items():
            doc = tool_class.__doc__ or ""
            # Extract the first line of the docstring as a short description
            description = (
                doc.strip().split("\n")[0] if doc else f"Tool type: {tool_type}"
            )
            result[tool_type] = description

        return result

    def load_tool_class_from_path(self, tool_type: str, class_path: str) -> bool:
        """
        Dynamically load and register a tool class from a module path.

        Args:
            tool_type: The identifier to register for this tool
            class_path: Full import path to the class, e.g., "mypackage.module.MyClass"

        Returns:
            True if successfully loaded and registered, False otherwise
        """
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)

            # Ensure it's a subclass of OrchestraTool
            if not issubclass(tool_class, OrchestraTool):
                logger.error(f"Class {class_path} is not a subclass of OrchestraTool")
                return False

            # Register the tool
            self.register_tool_class(tool_type, tool_class)
            return True

        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to load tool class from path: {class_path}: {e}")
            return False

    def get_phidata_tools(self) -> List[Any]:
        """
        Get all tools in a format compatible with Phidata.

        This method converts all registered tools to Phidata-compatible
        tools that can be passed directly to Phidata agents.

        Returns:
            List of Phidata-compatible tools
        """
        phidata_tools = []

        for tool_id, tool in self._tool_instances.items():
            phidata_tool = tool.to_phidata_tool()
            if phidata_tool:
                phidata_tools.append(phidata_tool)

        return phidata_tools


# Create a singleton instance
tool_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.

    Returns:
        The global ToolRegistry instance
    """
    return tool_registry
