#!/usr/bin/env python3
"""
"""
    """Base exception for all MCP server errors."""
        code: str = "MCP_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        """
        """
        """
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }

# Memory Store Exceptions
class MemoryError(MCPError):
    """Base exception for memory store errors."""
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
        code: str = "TOOL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class ToolNotEnabledError(ToolError):
    """Exception raised when a tool is not enabled."""
        super().__init__(f"Tool not enabled: {tool}", "TOOL_NOT_ENABLED", {"tool": tool})

class ToolExecutionError(ToolError):
    """Exception raised when a tool execution fails."""
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
        super().__init__(f"Tool not implemented: {tool}", "TOOL_NOT_IMPLEMENTED", {"tool": tool})

# Workflow Manager Exceptions
class WorkflowError(MCPError):
    """Base exception for workflow manager errors."""
        code: str = "WORKFLOW_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class WorkflowNotFoundError(WorkflowError):
    """Exception raised when a workflow is not found."""
            f"Workflow not found: {workflow_id}",
            "WORKFLOW_NOT_FOUND",
            {"workflow_id": workflow_id},
        )

class WorkflowExecutionError(WorkflowError):
    """Exception raised when a workflow execution fails."""
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
            f"Workflow has no steps: {workflow_id}",
            "WORKFLOW_NO_STEPS",
            {"workflow_id": workflow_id},
        )

class WorkflowNoToolsError(WorkflowError):
    """Exception raised when no tools are available for a workflow."""
            f"No tools available for workflow: {workflow_id}",
            "WORKFLOW_NO_TOOLS",
            {"workflow_id": workflow_id},
        )

# Configuration Exceptions
class ConfigError(MCPError):
    """Base exception for configuration errors."""
        code: str = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class ConfigFileError(ConfigError):
    """Exception raised when a configuration file cannot be loaded."""
            "path": path,
        }
        if reason:
            details["reason"] = reason

        super().__init__(f"Failed to load configuration file: {path}", "CONFIG_FILE_ERROR", details)

class ConfigValidationError(ConfigError):
    """Exception raised when a configuration is invalid."""
            "Configuration validation failed",
            "CONFIG_VALIDATION_ERROR",
            {"errors": errors},
        )

# Server Exceptions
class ServerError(MCPError):
    """Base exception for server errors."""
        code: str = "SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class ServerStartupError(ServerError):
    """Exception raised when the server fails to start."""
            details["reason"] = reason

        super().__init__("Failed to start server", "SERVER_STARTUP_ERROR", details)

class ServerShutdownError(ServerError):
    """Exception raised when the server fails to shut down."""
            details["reason"] = reason

        super().__init__("Failed to shut down server", "SERVER_SHUTDOWN_ERROR", details)

# Authentication Exceptions
class AuthError(MCPError):
    """Base exception for authentication errors."""
        code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, code, details)

class AuthTokenError(AuthError):
    """Exception raised when an authentication token is invalid."""
            details["reason"] = reason

        super().__init__("Invalid authentication token", "AUTH_TOKEN_ERROR", details)

class AuthPermissionError(AuthError):
    """Exception raised when a user does not have permission to access a resource."""
            f"Permission denied: {action} on {resource}",
            "AUTH_PERMISSION_ERROR",
            {
                "resource": resource,
                "action": action,
            },
        )
