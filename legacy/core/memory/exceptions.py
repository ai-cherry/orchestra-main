"""
"""
    """
    """
        error_code: str = "MEMORY_ERROR",
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
        
    def __str__(self) -> str:
        """Format the except Exception:
     pass
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
            
        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")
            
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
            "error": self.error_code,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None
        }

class MemoryNotFoundError(MemoryException):
    """Raised when a requested memory item is not found."""
        context = {"key": key}
        if tier:
            context["tier"] = tier
            
        super().__init__(
            message=f"Memory item not found: {key}",
            error_code="MEMORY_NOT_FOUND",
            context=context,
            cause=cause
        )

class MemoryStorageError(MemoryException):
    """Raised when a storage operation fails."""
            "operation": operation,
            "storage_backend": storage_backend,
            "reason": reason
        }
        if key:
            context["key"] = key
            
        super().__init__(
            message=f"Storage operation '{operation}' failed on {storage_backend}: {reason}",
            error_code="MEMORY_STORAGE_ERROR",
            context=context,
            cause=cause
        )

class MemoryTierError(MemoryException):
    """Raised when tier operations fail."""
        reason: str = "",
        cause: Optional[Exception] = None
    ):
        context = {"operation": operation}
        if from_tier:
            context["from_tier"] = from_tier
        if to_tier:
            context["to_tier"] = to_tier
            
        message = f"Tier operation '{operation}' failed"
        if from_tier and to_tier:
            message += f" (migration from {from_tier} to {to_tier})"
        if reason:
            message += f": {reason}"
            
        super().__init__(
            message=message,
            error_code="MEMORY_TIER_ERROR",
            context=context,
            cause=cause
        )

class MemoryOptimizationError(MemoryException):
    """Raised when optimization operations fail."""
            "optimization_type": optimization_type,
            "reason": reason
        }
        if items_affected is not None:
            context["items_affected"] = items_affected
            
        super().__init__(
            message=f"Optimization '{optimization_type}' failed: {reason}",
            error_code="MEMORY_OPTIMIZATION_ERROR",
            context=context,
            cause=cause
        )

class MemoryConnectionError(MemoryException):
    """Raised when connection to a storage backend fails."""
            "backend": backend,
            "host": host,
            "port": port
        }
        
        super().__init__(
            message=f"Failed to connect to {backend} at {host}:{port}: {reason}",
            error_code="MEMORY_CONNECTION_ERROR",
            context=context,
            cause=cause
        )

class MemorySerializationError(MemoryException):
    """Raised when serialization/deserialization fails."""
            "operation": operation,
            "key": key,
            "value_type": value_type
        }
        
        super().__init__(
            message=f"Failed to {operation} value of type {value_type} for key {key}: {reason}",
            error_code="MEMORY_SERIALIZATION_ERROR",
            context=context,
            cause=cause
        )

class MemoryCapacityError(MemoryException):
    """Raised when memory capacity is exceeded."""
            "tier": tier,
            "current_size": current_size,
            "max_size": max_size,
            "requested_size": requested_size,
            "available_size": max_size - current_size
        }
        
        super().__init__(
            message=f"Memory capacity exceeded in {tier}: current={current_size}, max={max_size}, requested={requested_size}",
            error_code="MEMORY_CAPACITY_ERROR",
            context=context,
            cause=cause
        )

class MemoryTimeoutError(MemoryException):
    """Raised when a memory operation times out."""
            "operation": operation,
            "timeout_seconds": timeout_seconds
        }
        if key:
            context["key"] = key
            
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_seconds}s",
            error_code="MEMORY_TIMEOUT_ERROR",
            context=context,
            cause=cause
        )

class MemoryValidationError(MemoryException):
    """Raised when validation fails."""
            "validation_type": validation_type,
            "field": field,
            "value": str(value)[:100],  # Truncate long values
            "constraint": constraint
        }
        
        super().__init__(
            message=f"Validation failed for {field}: {constraint}",
            error_code="MEMORY_VALIDATION_ERROR",
            context=context,
            cause=cause
        )

class MemoryConfigurationError(MemoryException):
    """Raised when configuration is invalid."""
            "config_section": config_section,
            "parameter": parameter,
            "value": str(value),
            "reason": reason
        }
        
        super().__init__(
            message=f"Invalid configuration in {config_section}.{parameter}: {reason}",
            error_code="MEMORY_CONFIGURATION_ERROR",
            context=context,
            cause=cause
        )

class MemoryLockError(MemoryException):
    """Raised when distributed locking fails."""
            "lock_key": lock_key,
            "operation": operation
        }
        if holder:
            context["current_holder"] = holder
        if timeout:
            context["timeout"] = timeout
            
        message = f"Failed to acquire lock for {lock_key} during {operation}"
        if holder:
            message += f" (held by {holder})"
            
        super().__init__(
            message=message,
            error_code="MEMORY_LOCK_ERROR",
            context=context,
            cause=cause
        )

# Exception handler utility
class MemoryExceptionHandler:
    """
    """
        """Convert storage-specific exceptions to MemoryStorageError."""
            "ConnectionError": "Connection failed",
            "TimeoutError": "Operation timed out",
            "AuthenticationError": "Authentication failed",
            "PermissionError": "Permission denied",
        }
        
        error_type = type(original_error).__name__
        reason = error_mappings.get(error_type, str(original_error))
        
        return MemoryStorageError(
            operation=operation,
            storage_backend=backend,
            reason=reason,
            key=key,
            cause=original_error
        )
    
    @staticmethod
    def is_retryable(error: MemoryException) -> bool:
        """Determine if an error is retryable."""
            "MEMORY_TIMEOUT_ERROR",
            "MEMORY_CONNECTION_ERROR",
            "MEMORY_LOCK_ERROR",
        }
        
        # Check if it's a storage error with retryable cause
        if isinstance(error, MemoryStorageError):
            retryable_reasons = {"Connection failed", "Operation timed out"}
            return error.context.get("reason", "") in retryable_reasons
            
        return error.error_code in retryable_codes
    
    @staticmethod
    def get_retry_delay(error: MemoryException, attempt: int) -> float:
        """Calculate retry delay based on error type and attempt number."""
            "MEMORY_TIMEOUT_ERROR": 1.0,
            "MEMORY_CONNECTION_ERROR": 2.0,
            "MEMORY_LOCK_ERROR": 0.5,
        }
        
        base_delay = base_delays.get(error.error_code, 1.0)
        # Exponential backoff with jitter
        import random
        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
        
        # Cap at 30 seconds
        return min(delay, 30.0)