"""
Tool Integration Framework for AI Orchestration System.

This module provides a standardized framework for defining and using tools
with agents, enabling consistent tool registration, discovery, and execution.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, get_type_hints

from pydantic import BaseModel, Field, create_model

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for tool return types
T = TypeVar("T")


class ToolParameter(BaseModel):
    """
    Metadata about a tool parameter.

    This class captures information about a parameter that a tool accepts,
    including its name, type, description, and whether it's required.
    """

    name: str
    type_hint: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolMetadata(BaseModel):
    """
    Metadata about a tool.

    This class captures information about a tool, including its name,
    description, parameters, and return type.
    """

    name: str
    description: str
    parameters: List[ToolParameter]
    return_type: str
    requires_async: bool = True
    categories: List[str] = Field(default_factory=list)


class Tool(ABC):
    """
    Base class for tools that agents can use.

    This abstract class defines the interface that all tools must implement,
    providing a consistent way for agents to discover and use tools.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize a tool.

        Args:
            name: The name of the tool
            description: A description of what the tool does
        """
        self.name = name
        self.description = description
        self._metadata = None

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            The result of the tool execution

        Raises:
            ValueError: If required parameters are missing or invalid
        """

    def get_metadata(self) -> ToolMetadata:
        """
        Get metadata about this tool.

        This method uses introspection to determine the tool's parameters
        and return type, making it easier for agents to use the tool correctly.

        Returns:
            Metadata about the tool
        """
        if self._metadata is None:
            # Get the execute method's signature
            sig = inspect.signature(self.execute)

            # Get type hints for the execute method
            type_hints = get_type_hints(self.execute)
            return_type = type_hints.get("return", Any).__name__

            # Extract parameter information
            parameters = []
            for name, param in sig.parameters.items():
                if name == "self":
                    continue

                param_type = type_hints.get(name, Any).__name__
                required = param.default == inspect.Parameter.empty
                default = None if required else param.default

                # Try to get parameter description from docstring
                param_desc = f"Parameter {name}"

                parameters.append(
                    ToolParameter(
                        name=name,
                        type_hint=param_type,
                        description=param_desc,
                        required=required,
                        default=default,
                    )
                )

            self._metadata = ToolMetadata(
                name=self.name,
                description=self.description,
                parameters=parameters,
                return_type=return_type,
                requires_async=inspect.iscoroutinefunction(self.execute),
            )

        return self._metadata

    def create_input_model(self) -> Type[BaseModel]:
        """
        Create a Pydantic model for validating tool inputs.

        This method dynamically creates a Pydantic model based on the
        tool's parameters, making it easy to validate inputs before execution.

        Returns:
            A Pydantic model class for validating inputs
        """
        metadata = self.get_metadata()
        fields = {}

        for param in metadata.parameters:
            field_info = Field(
                default=None if not param.required else ...,
                description=param.description,
            )
            fields[param.name] = (
                Optional[Any] if not param.required else Any,
                field_info,
            )

        model_name = f"{self.name.title()}Input"
        return create_model(model_name, **fields)


class ToolRegistry:
    """
    Registry for tools that agents can use.

    This class provides a central registry for tools, making it easy for
    agents to discover and use available tools.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, Set[str]] = {}

    def register_tool(self, tool: Tool, categories: Optional[List[str]] = None) -> None:
        """
        Register a tool with the registry.

        Args:
            tool: The tool to register
            categories: Optional categories to associate with the tool

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered")

        self._tools[tool.name] = tool

        # Register categories
        if categories:
            for category in categories:
                if category not in self._categories:
                    self._categories[category] = set()
                self._categories[category].add(tool.name)

        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool:
        """
        Get a tool by name.

        Args:
            name: The name of the tool to get

        Returns:
            The requested tool

        Raises:
            ValueError: If no tool with the given name is registered
        """
        if name not in self._tools:
            raise ValueError(f"No tool with name '{name}' is registered")

        return self._tools[name]

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        Get all tools in a specific category.

        Args:
            category: The category to get tools for

        Returns:
            A list of tools in the specified category
        """
        if category not in self._categories:
            return []

        return [self._tools[name] for name in self._categories[category]]

    def get_all_tools(self) -> List[Tool]:
        """
        Get all registered tools.

        Returns:
            A list of all registered tools
        """
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """
        Get the names of all registered tools.

        Returns:
            A list of all registered tool names
        """
        return list(self._tools.keys())


class ToolUsingAgent:
    """
    Mixin for agents that can use tools.

    This class provides functionality for agents to use tools, including
    tool discovery, execution, and result handling.
    """

    def __init__(self, tools: Optional[List[Tool]] = None):
        """
        Initialize a tool-using agent.

        Args:
            tools: Optional list of tools this agent can use
        """
        self.tools = tools or []
        self._tool_map = {tool.name: tool for tool in self.tools}

    def add_tool(self, tool: Tool) -> None:
        """
        Add a tool to this agent.

        Args:
            tool: The tool to add

        Raises:
            ValueError: If a tool with the same name is already added
        """
        if tool.name in self._tool_map:
            raise ValueError(f"Tool with name '{tool.name}' is already added")

        self.tools.append(tool)
        self._tool_map[tool.name] = tool

    def remove_tool(self, tool_name: str) -> None:
        """
        Remove a tool from this agent.

        Args:
            tool_name: The name of the tool to remove

        Raises:
            ValueError: If no tool with the given name is added
        """
        if tool_name not in self._tool_map:
            raise ValueError(f"No tool with name '{tool_name}' is added")

        tool = self._tool_map[tool_name]
        self.tools.remove(tool)
        del self._tool_map[tool_name]

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if this agent has a specific tool.

        Args:
            tool_name: The name of the tool to check for

        Returns:
            True if the agent has the tool, False otherwise
        """
        return tool_name in self._tool_map

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        Get descriptions of all tools this agent can use.

        Returns:
            A list of tool descriptions
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": [p.dict() for p in tool.get_metadata().parameters],
            }
            for tool in self.tools
        ]

    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Use a specific tool by name.

        Args:
            tool_name: The name of the tool to use
            **kwargs: Tool-specific parameters

        Returns:
            The result of the tool execution

        Raises:
            ValueError: If no tool with the given name is available
        """
        if tool_name not in self._tool_map:
            raise ValueError(f"Tool {tool_name} not found")

        tool = self._tool_map[tool_name]

        # Create and validate input model
        input_model = tool.create_input_model()
        validated_inputs = input_model(**kwargs).dict()

        # Execute the tool
        logger.debug(f"Executing tool: {tool_name} with params: {validated_inputs}")
        result = await tool.execute(**validated_inputs)
        logger.debug(f"Tool {tool_name} returned: {result}")

        return result


# Global tool registry
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry.

    Returns:
        The global tool registry
    """
    return _global_registry
