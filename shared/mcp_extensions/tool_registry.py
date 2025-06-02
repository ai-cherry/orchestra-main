"""
Tool Registry for MCP Extensions

This module provides a registry for tools that can be used by MCP clients.
It handles registration, discovery, and access control for tools.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Callable, Union

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for MCP tools with access control.

    This class manages tool registration and enforces access control
    based on environment and user roles.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._access_control = {
            "environments": {
                "production": {
                    "restricted_tools": ["system_admin", "data_deletion"],
                    "allowed_tools": ["search", "query", "chat"],
                },
                "staging": {
                    "restricted_tools": ["system_admin"],
                    "allowed_tools": ["search", "query", "chat", "data_deletion"],
                },
                "development": {"allow_all": True},
                "local_development": {"allow_all": True},
                "ci": {"allow_all": True},
            },
            "roles": {
                "admin": {"allow_all": True},
                "developer": {"allowed_tools": ["search", "query", "chat", "data_deletion", "debug"]},
                "user": {"allowed_tools": ["search", "query", "chat"]},
            },
        }

    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        parameters: Dict[str, Any] = None,
        required_role: str = "user",
    ) -> None:
        """
        Register a new tool with the registry.

        Args:
            name: Unique identifier for the tool
            handler: Function that implements the tool
            description: Human-readable description of the tool
            parameters: Dictionary describing the parameters the tool accepts
            required_role: Minimum role required to use this tool
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered. Overwriting.")

        self._tools[name] = {
            "handler": handler,
            "description": description,
            "parameters": parameters or {},
            "required_role": required_role,
        }

        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tool by name.

        Args:
            name: Name of the tool to retrieve

        Returns:
            Tool configuration dictionary or None if not found
        """
        return self._tools.get(name)

    def list_tools(self, environment: str = "production", role: str = "user") -> List[Dict[str, Any]]:
        """
        List all tools available for the given environment and role.

        Args:
            environment: Current execution environment
            role: User role

        Returns:
            List of available tools with their metadata
        """
        available_tools = []

        for name, tool in self._tools.items():
            if self._is_tool_allowed(name, tool, environment, role):
                # Create a copy without the handler for serialization
                tool_info = {k: v for k, v in tool.items() if k != "handler"}
                tool_info["name"] = name
                available_tools.append(tool_info)

        return available_tools

    def _is_tool_allowed(self, name: str, tool: Dict[str, Any], environment: str, role: str) -> bool:
        """
        Check if a tool is allowed for the given environment and role.

        Args:
            name: Tool name
            tool: Tool configuration
            environment: Current execution environment
            role: User role

        Returns:
            True if the tool is allowed, False otherwise
        """
        # Check role-based access
        role_config = self._access_control["roles"].get(role, {})
        if role_config.get("allow_all", False):
            return True

        allowed_tools = role_config.get("allowed_tools", [])
        if name in allowed_tools:
            # Tool is explicitly allowed for this role
            return True

        # Check environment-based access
        env_config = self._access_control["environments"].get(environment, {})
        if env_config.get("allow_all", False):
            return True

        restricted_tools = env_config.get("restricted_tools", [])
        if name in restricted_tools:
            # Tool is explicitly restricted in this environment
            return False

        allowed_tools = env_config.get("allowed_tools", [])
        if allowed_tools and name in allowed_tools:
            # Tool is explicitly allowed in this environment
            return True

        # Default to restricted
        return False

    def execute_tool(
        self, name: str, params: Dict[str, Any], environment: str = "production", role: str = "user"
    ) -> Any:
        """
        Execute a tool with the given parameters.

        Args:
            name: Name of the tool to execute
            params: Parameters to pass to the tool
            environment: Current execution environment
            role: User role

        Returns:
            Result of the tool execution

        Raises:
            ValueError: If the tool is not found or not allowed
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        if not self._is_tool_allowed(name, tool, environment, role):
            raise ValueError(f"Tool '{name}' is not allowed in {environment} for role {role}")

        handler = tool["handler"]
        return handler(**params)


# Singleton instance for global access
default_registry = ToolRegistry()


def register_tool(
    name: str, handler: Callable, description: str = "", parameters: Dict[str, Any] = None, required_role: str = "user"
) -> None:
    """
    Register a tool with the default registry.

    Args:
        name: Unique identifier for the tool
        handler: Function that implements the tool
        description: Human-readable description of the tool
        parameters: Dictionary describing the parameters the tool accepts
        required_role: Minimum role required to use this tool
    """
    default_registry.register_tool(
        name=name, handler=handler, description=description, parameters=parameters, required_role=required_role
    )


def get_tool(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a tool from the default registry.

    Args:
        name: Name of the tool to retrieve

    Returns:
        Tool configuration dictionary or None if not found
    """
    return default_registry.get_tool(name)


def list_tools(environment: str = "production", role: str = "user") -> List[Dict[str, Any]]:
    """
    List all tools available in the default registry.

    Args:
        environment: Current execution environment
        role: User role

    Returns:
        List of available tools with their metadata
    """
    return default_registry.list_tools(environment, role)


def execute_tool(name: str, params: Dict[str, Any], environment: str = "production", role: str = "user") -> Any:
    """
    Execute a tool from the default registry.

    Args:
        name: Name of the tool to execute
        params: Parameters to pass to the tool
        environment: Current execution environment
        role: User role

    Returns:
        Result of the tool execution
    """
    return default_registry.execute_tool(name, params, environment, role)
