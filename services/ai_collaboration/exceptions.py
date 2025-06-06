#!/usr/bin/env python3
"""
Custom exceptions for AI Collaboration Service
Following clean error handling patterns with meaningful error messages
"""

from typing import Optional, Dict, Any, List


class AICollaborationError(Exception):
    """Base exception for AI Collaboration Service"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ServiceError(AICollaborationError):
    """General service error"""
    pass


class ConfigurationError(AICollaborationError):
    """Configuration related errors"""
    pass


class InitializationError(AICollaborationError):
    """Service initialization errors"""
    pass


# Entity-related exceptions

class EntityNotFoundError(AICollaborationError):
    """Entity not found in database"""
    
    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(
            f"{entity_type} with ID {entity_id} not found",
            error_code="ENTITY_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": str(entity_id)}
        )


class AgentNotFoundError(EntityNotFoundError):
    """AI Agent not found"""
    
    def __init__(self, agent_id: int):
        super().__init__("Agent", agent_id)


class TaskNotFoundError(EntityNotFoundError):
    """Task not found"""
    
    def __init__(self, task_id: Any):
        super().__init__("Task", task_id)


# State-related exceptions

class InvalidStateError(AICollaborationError):
    """Invalid state for operation"""
    pass


class InvalidStateTransitionError(InvalidStateError):
    """Invalid state transition attempted"""
    
    def __init__(self, from_state: str, to_state: str, entity_type: str = "Entity"):
        super().__init__(
            f"Invalid {entity_type} state transition from {from_state} to {to_state}",
            error_code="INVALID_STATE_TRANSITION",
            details={
                "from_state": from_state,
                "to_state": to_state,
                "entity_type": entity_type
            }
        )


class AgentNotAvailableError(InvalidStateError):
    """Agent is not available for tasks"""
    
    def __init__(self, agent_id: int, reason: str = "Agent is offline or at capacity"):
        super().__init__(
            f"Agent {agent_id} is not available: {reason}",
            error_code="AGENT_NOT_AVAILABLE",
            details={"agent_id": agent_id, "reason": reason}
        )


# Validation exceptions

class ValidationError(AICollaborationError):
    """Data validation error"""
    
    def __init__(self, field: str, value: Any, constraint: str):
        super().__init__(
            f"Validation failed for field '{field}': {constraint}",
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": str(value),
                "constraint": constraint
            }
        )


class InvalidTaskTypeError(ValidationError):
    """Invalid task type provided"""
    
    def __init__(self, task_type: str, supported_types: List[str]):
        super().__init__(
            "task_type",
            task_type,
            f"Must be one of: {', '.join(supported_types)}"
        )
        self.details["supported_types"] = supported_types


# Connection exceptions

class ConnectionError(AICollaborationError):
    """Connection related errors"""
    pass


class WebSocketConnectionError(ConnectionError):
    """WebSocket connection error"""
    
    def __init__(self, url: str, reason: str):
        super().__init__(
            f"Failed to connect to WebSocket at {url}: {reason}",
            error_code="WEBSOCKET_CONNECTION_ERROR",
            details={"url": url, "reason": reason}
        )


class DatabaseConnectionError(ConnectionError):
    """Database connection error"""
    
    def __init__(self, reason: str):
        super().__init__(
            f"Database connection failed: {reason}",
            error_code="DATABASE_CONNECTION_ERROR",
            details={"reason": reason}
        )


class CacheConnectionError(ConnectionError):
    """Cache connection error"""
    
    def __init__(self, reason: str):
        super().__init__(
            f"Cache connection failed: {reason}",
            error_code="CACHE_CONNECTION_ERROR",
            details={"reason": reason}
        )


# Operation exceptions

class OperationError(AICollaborationError):
    """Operation execution error"""
    pass


class TaskRoutingError(OperationError):
    """Error routing task to agent"""
    
    def __init__(self, task_type: str, reason: str):
        super().__init__(
            f"Failed to route task of type '{task_type}': {reason}",
            error_code="TASK_ROUTING_ERROR",
            details={"task_type": task_type, "reason": reason}
        )


class MetricsCollectionError(OperationError):
    """Error collecting metrics"""
    
    def __init__(self, metric_type: str, reason: str):
        super().__init__(
            f"Failed to collect metric '{metric_type}': {reason}",
            error_code="METRICS_COLLECTION_ERROR",
            details={"metric_type": metric_type, "reason": reason}
        )


class CircuitBreakerOpenError(OperationError):
    """Circuit breaker is open"""
    
    def __init__(self, service: str, failure_count: int):
        super().__init__(
            f"Circuit breaker for {service} is open after {failure_count} failures",
            error_code="CIRCUIT_BREAKER_OPEN",
            details={"service": service, "failure_count": failure_count}
        )


# Resource exceptions

class ResourceError(AICollaborationError):
    """Resource related errors"""
    pass


class ResourceExhaustedError(ResourceError):
    """Resource exhausted error"""
    
    def __init__(self, resource: str, limit: Any):
        super().__init__(
            f"Resource '{resource}' exhausted. Limit: {limit}",
            error_code="RESOURCE_EXHAUSTED",
            details={"resource": resource, "limit": str(limit)}
        )


class QuotaExceededError(ResourceError):
    """Quota exceeded error"""
    
    def __init__(self, quota_type: str, current: int, limit: int):
        super().__init__(
            f"Quota exceeded for '{quota_type}': {current}/{limit}",
            error_code="QUOTA_EXCEEDED",
            details={
                "quota_type": quota_type,
                "current": current,
                "limit": limit
            }
        )


# Timeout exceptions

class TimeoutError(AICollaborationError):
    """Operation timeout error"""
    
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            f"Operation '{operation}' timed out after {timeout_seconds} seconds",
            error_code="TIMEOUT",
            details={
                "operation": operation,
                "timeout_seconds": timeout_seconds
            }
        )


class TaskTimeoutError(TimeoutError):
    """Task execution timeout"""
    
    def __init__(self, task_id: str, timeout_seconds: int):
        super().__init__(f"Task {task_id}", timeout_seconds)
        self.details["task_id"] = task_id


# Security exceptions

class SecurityError(AICollaborationError):
    """Security related errors"""
    pass


class AuthenticationError(SecurityError):
    """Authentication failed"""
    
    def __init__(self, reason: str = "Invalid credentials"):
        super().__init__(
            f"Authentication failed: {reason}",
            error_code="AUTHENTICATION_ERROR",
            details={"reason": reason}
        )


class AuthorizationError(SecurityError):
    """Authorization failed"""
    
    def __init__(self, action: str, resource: str):
        super().__init__(
            f"Not authorized to {action} on {resource}",
            error_code="AUTHORIZATION_ERROR",
            details={"action": action, "resource": resource}
        )


# Data exceptions

class DataError(AICollaborationError):
    """Data related errors"""
    pass


class DataIntegrityError(DataError):
    """Data integrity violation"""
    
    def __init__(self, entity: str, reason: str):
        super().__init__(
            f"Data integrity error for {entity}: {reason}",
            error_code="DATA_INTEGRITY_ERROR",
            details={"entity": entity, "reason": reason}
        )


class SerializationError(DataError):
    """Data serialization error"""
    
    def __init__(self, data_type: str, reason: str):
        super().__init__(
            f"Failed to serialize {data_type}: {reason}",
            error_code="SERIALIZATION_ERROR",
            details={"data_type": data_type, "reason": reason}
        )


# External service exceptions

class ExternalServiceError(AICollaborationError):
    """External service error"""
    
    def __init__(self, service: str, reason: str):
        super().__init__(
            f"External service '{service}' error: {reason}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "reason": reason}
        )


class VectorStoreError(ExternalServiceError):
    """Vector store operation error"""
    
    def __init__(self, operation: str, reason: str):
        super().__init__("VectorStore", f"{operation} failed: {reason}")
        self.details["operation"] = operation


# Retry exceptions

class RetryableError(AICollaborationError):
    """Base class for retryable errors"""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after"] = retry_after


class TemporaryError(RetryableError):
    """Temporary error that should be retried"""
    pass


class RateLimitError(RetryableError):
    """Rate limit exceeded"""
    
    def __init__(self, limit: int, window: str, retry_after: int):
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window}",
            retry_after=retry_after,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "limit": limit,
                "window": window
            }
        )


# Additional specific exceptions for AI Collaboration

class ResourceNotFoundError(AICollaborationError):
    """Resource not found error"""
    pass


class ResourceConflictError(AICollaborationError):
    """Resource conflict error"""
    pass


class ServiceUnavailableError(AICollaborationError):
    """Service temporarily unavailable"""
    pass


class MetricsError(AICollaborationError):
    """Metrics collection or processing error"""
    pass


class RoutingError(AICollaborationError):
    """Task routing error"""
    pass


# Factory function for creating exceptions from error codes

def create_exception(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> AICollaborationError:
    """
    Factory function to create appropriate exception from error code
    
    Args:
        error_code: Error code string
        message: Error message
        details: Optional error details
        
    Returns:
        Appropriate exception instance
    """
    error_map = {
        "ENTITY_NOT_FOUND": EntityNotFoundError,
        "INVALID_STATE_TRANSITION": InvalidStateTransitionError,
        "VALIDATION_ERROR": ValidationError,
        "CONNECTION_ERROR": ConnectionError,
        "TIMEOUT": TimeoutError,
        "AUTHENTICATION_ERROR": AuthenticationError,
        "AUTHORIZATION_ERROR": AuthorizationError,
        "RATE_LIMIT_EXCEEDED": RateLimitError,
        "CIRCUIT_BREAKER_OPEN": CircuitBreakerOpenError,
    }
    
    exception_class = error_map.get(error_code, AICollaborationError)
    
    # Handle special cases that need specific parameters
    if error_code == "ENTITY_NOT_FOUND" and details:
        return EntityNotFoundError(
            details.get("entity_type", "Entity"),
            details.get("entity_id", "unknown")
        )
    elif error_code == "RATE_LIMIT_EXCEEDED" and details:
        return RateLimitError(
            details.get("limit", 0),
            details.get("window", "unknown"),
            details.get("retry_after", 60)
        )
    
    # Default case
    return exception_class(message, error_code=error_code, details=details)