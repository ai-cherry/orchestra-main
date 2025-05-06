"""
Custom exceptions for the AI Orchestration System.

This module defines custom exceptions for different types of failures in the orchestration
system, allowing for more precise error handling and easier troubleshooting.
"""

from typing import Optional, Any, Dict


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(message)


class ConfigurationError(OrchestratorError):
    """Raised when there's a configuration issue."""
    pass


class DependencyError(OrchestratorError):
    """Raised when a required dependency is missing or unavailable."""
    pass


class MemoryError(OrchestratorError):
    """Base exception for memory system errors."""
    pass


class MemoryConnectionError(MemoryError):
    """Raised when a connection to a memory storage system fails."""
    pass


class MemoryOperationError(MemoryError):
    """Raised when a memory operation fails."""
    pass


class MemoryItemNotFoundError(MemoryError):
    """Raised when a memory item is not found."""
    pass


class AgentError(OrchestratorError):
    """Base exception for agent-related errors."""
    pass


class AgentNotFoundError(AgentError):
    """Raised when a requested agent is not found."""
    pass


class AgentExecutionError(AgentError):
    """Raised when an agent execution fails."""
    
    def __init__(
        self, 
        message: str, 
        agent_id: str, 
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.details = details or {}
        super().__init__(message, original_error)


class ResilienceError(OrchestratorError):
    """Base exception for resilience system errors."""
    pass


class CircuitBreakerOpenError(ResilienceError):
    """Raised when a circuit breaker is open."""
    
    def __init__(
        self, 
        message: str, 
        agent_id: str, 
        next_retry_time: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        self.agent_id = agent_id
        self.next_retry_time = next_retry_time
        super().__init__(message, original_error)


class FallbackError(ResilienceError):
    """Raised when a fallback operation fails."""
    pass


class LLMError(OrchestratorError):
    """Base exception for LLM-related errors."""
    pass


class LLMProviderError(LLMError):
    """Raised when an LLM provider operation fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when an LLM provider enforces rate limiting."""
    pass


class APIError(OrchestratorError):
    """Base exception for API-related errors."""
    pass


class ValidationError(APIError):
    """Raised when API request validation fails."""
    pass


class ServiceUnavailableError(APIError):
    """Raised when a required service is unavailable."""
    pass
