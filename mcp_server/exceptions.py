#!/usr/bin/env python3
"""
exceptions.py - Custom Exceptions for MCP Server

This module provides a hierarchy of custom exceptions for the MCP server,
allowing for more specific error handling and better error messages.
"""

from typing import Any, Dict, Optional

class MCPError(Exception):
    """Base exception for all MCP server errors."""

    def __init__(
        self,
        message: str,
        code: str = "MCP_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Error message
            code: Error code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary.

        Returns:
            Dictionary representation of the exception
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }

# Memory Store Exceptions
class MemoryError(MCPError):
    """Base exception for memory store errors."""

    def __init__(
        self,
        message: str,
        code: str = "MEMORY_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class MemoryNotFoundError(MemoryError):
    """Exception raised when a memory item is not found."""

    def __init__(self, key: str, scope: str = "session", tool: Optional[str] = None):
        details = {
            "key": key,
            "scope": scope,
            "tool": tool,
        }
        super().__init__(
            f"Memory item not found: {key} (scope={scope}, tool={tool})",
            "MEMORY_NOT_FOUND",
            details,
        )

class MemoryWriteError(MemoryError):
    """Exception raised when a memory item cannot be written."""

    def __init__(
        self,
        key: str,
        scope: str = "session",
        tool: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {
            "key": key,
            "scope": scope,
            "tool": tool,
        }
        if reason:
            details["reason"] = reason

        super().__init__(
            f"Failed to write memory item: {key} (scope={scope}, tool={tool})",
            "MEMORY_WRITE_ERROR",
            details,
        )

class MemoryDeleteError(MemoryError):
    """Exception raised when a memory item cannot be deleted."""

    def __init__(
        self,
        key: str,
        scope: str = "session",
        tool: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {
            "key": key,
            "scope": scope,
            "tool": tool,
        }
        if reason:
            details["reason"] = reason

        super().__init__(
            f"Failed to delete memory item: {key} (scope={scope}, tool={tool})",
            "MEMORY_DELETE_ERROR",
            details,
        )

class MemorySyncError(MemoryError):
    """Exception raised when a memory item cannot be synced."""

    def __init__(
        self,
        key: str,
        source_tool: str,
        target_tool: str,
        scope: str = "session",
        reason: Optional[str] = None,
    ):
        details = {
            "key": key,
            "scope": scope,
            "source_tool": source_tool,
            "target_tool": target_tool,
        }
        if reason:
            details["reason"] = reason

        super().__init__(
            f"Failed to sync memory item: {key} from {source_tool} to {target_tool} (scope={scope})",
            "MEMORY_SYNC_ERROR",
            details,
        )

# Tool Manager Exceptions
class ToolError(MCPError):
    """Base exception for tool manager errors."""

    def __init__(
        self,
        message: str,
        code: str = "TOOL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class ToolNotEnabledError(ToolError):
    """Exception raised when a tool is not enabled."""

    def __init__(self, tool: str):
        super().__init__(f"Tool not enabled: {tool}", "TOOL_NOT_ENABLED", {"tool": tool})

class ToolExecutionError(ToolError):
    """Exception raised when a tool execution fails."""

    def __init__(self, tool: str, mode: str, reason: Optional[str] = None):
        details = {
            "tool": tool,
            "mode": mode,
        }
        if reason:
            details["reason"] = reason

        super().__init__(
            f"Failed to execute tool: {tool} (mode={mode})",
            "TOOL_EXECUTION_ERROR",
            details,
        )

class ToolNotImplementedError(ToolError):
    """Exception raised when a tool is not implemented."""

    def __init__(self, tool: str):
        super().__init__(f"Tool not implemented: {tool}", "TOOL_NOT_IMPLEMENTED", {"tool": tool})

# Workflow Manager Exceptions
class WorkflowError(MCPError):
    """Base exception for workflow manager errors."""

    def __init__(
        self,
        message: str,
        code: str = "WORKFLOW_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class WorkflowNotFoundError(WorkflowError):
    """Exception raised when a workflow is not found."""

    def __init__(self, workflow_id: str):
        super().__init__(
            f"Workflow not found: {workflow_id}",
            "WORKFLOW_NOT_FOUND",
            {"workflow_id": workflow_id},
        )

class WorkflowExecutionError(WorkflowError):
    """Exception raised when a workflow execution fails."""

    def __init__(self, workflow_id: str, step: Optional[int] = None, reason: Optional[str] = None):
        details = {
            "workflow_id": workflow_id,
        }
        if step is not None:
            details["step"] = step
        if reason:
            details["reason"] = reason

        message = f"Failed to execute workflow: {workflow_id}"
        if step is not None:
            message += f" (step {step})"

        super().__init__(message, "WORKFLOW_EXECUTION_ERROR", details)

class WorkflowStepTypeError(WorkflowError):
    """Exception raised when a workflow step has an invalid type."""

    def __init__(self, workflow_id: str, step: int, step_type: str):
        super().__init__(
            f"Invalid step type in workflow: {workflow_id} (step {step}, type={step_type})",
            "WORKFLOW_STEP_TYPE_ERROR",
            {
                "workflow_id": workflow_id,
                "step": step,
                "step_type": step_type,
            },
        )

class WorkflowNoStepsError(WorkflowError):
    """Exception raised when a workflow has no steps."""

    def __init__(self, workflow_id: str):
        super().__init__(
            f"Workflow has no steps: {workflow_id}",
            "WORKFLOW_NO_STEPS",
            {"workflow_id": workflow_id},
        )

class WorkflowNoToolsError(WorkflowError):
    """Exception raised when no tools are available for a workflow."""

    def __init__(self, workflow_id: str):
        super().__init__(
            f"No tools available for workflow: {workflow_id}",
            "WORKFLOW_NO_TOOLS",
            {"workflow_id": workflow_id},
        )

# Configuration Exceptions
class ConfigError(MCPError):
    """Base exception for configuration errors."""

    def __init__(
        self,
        message: str,
        code: str = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class ConfigFileError(ConfigError):
    """Exception raised when a configuration file cannot be loaded."""

    def __init__(self, path: str, reason: Optional[str] = None):
        details = {
            "path": path,
        }
        if reason:
            details["reason"] = reason

        super().__init__(f"Failed to load configuration file: {path}", "CONFIG_FILE_ERROR", details)

class ConfigValidationError(ConfigError):
    """Exception raised when a configuration is invalid."""

    def __init__(self, errors: Dict[str, str]):
        super().__init__(
            "Configuration validation failed",
            "CONFIG_VALIDATION_ERROR",
            {"errors": errors},
        )

# Server Exceptions
class ServerError(MCPError):
    """Base exception for server errors."""

    def __init__(
        self,
        message: str,
        code: str = "SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class ServerStartupError(ServerError):
    """Exception raised when the server fails to start."""

    def __init__(self, reason: Optional[str] = None):
        details = {}
        if reason:
            details["reason"] = reason

        super().__init__("Failed to start server", "SERVER_STARTUP_ERROR", details)

class ServerShutdownError(ServerError):
    """Exception raised when the server fails to shut down."""

    def __init__(self, reason: Optional[str] = None):
        details = {}
        if reason:
            details["reason"] = reason

        super().__init__("Failed to shut down server", "SERVER_SHUTDOWN_ERROR", details)

# Authentication Exceptions
class AuthError(MCPError):
    """Base exception for authentication errors."""

    def __init__(
        self,
        message: str,
        code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class AuthTokenError(AuthError):
    """Exception raised when an authentication token is invalid."""

    def __init__(self, reason: Optional[str] = None):
        details = {}
        if reason:
            details["reason"] = reason

        super().__init__("Invalid authentication token", "AUTH_TOKEN_ERROR", details)

class AuthPermissionError(AuthError):
    """Exception raised when a user does not have permission to access a resource."""

    def __init__(self, resource: str, action: str):
        super().__init__(
            f"Permission denied: {action} on {resource}",
            "AUTH_PERMISSION_ERROR",
            {
                "resource": resource,
                "action": action,
            },
        )
