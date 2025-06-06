"""
Centralized Error Handling System
Provides consistent error handling, logging, and monitoring across all components
"""

import asyncio
import logging
import traceback
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    PERSONA = "persona"
    MEMORY = "memory"
    VOICE = "voice"
    COORDINATION = "coordination"
    ADMIN = "admin"
    RAG = "rag"
    AGENT = "agent"
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"

@dataclass
class ErrorContext:
    """Context information for errors"""
    function_name: str
    module_name: str
    user_id: Optional[str] = None
    persona_id: Optional[str] = None
    operation_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorRecord:
    """Complete error record for tracking and analysis"""
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    traceback_info: str
    user_message: str
    resolution_steps: List[str] = field(default_factory=list)
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

# ========================================
# STANDARD EXCEPTION HIERARCHY
# ========================================

class StandardError(Exception):
    """Base exception for all application errors"""
    
    def __init__(self, 
                 message: str, 
                 error_code: str = None,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 details: Dict[str, Any] = None,
                 user_message: str = None,
                 resolution_steps: List[str] = None):
        
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.category = category
        self.details = details or {}
        self.user_message = user_message or "An error occurred. Please try again."
        self.resolution_steps = resolution_steps or []
        self.timestamp = datetime.now()
        
        super().__init__(self.message)

class PersonaError(StandardError):
    """Persona-related errors"""
    
    def __init__(self, message: str, persona_id: str = None, **kwargs):
        self.persona_id = persona_id
        super().__init__(
            message, 
            category=ErrorCategory.PERSONA,
            details={"persona_id": persona_id},
            **kwargs
        )

class MemoryError(StandardError):
    """Memory system errors"""
    
    def __init__(self, message: str, memory_key: str = None, layer: str = None, **kwargs):
        self.memory_key = memory_key
        self.layer = layer
        super().__init__(
            message,
            category=ErrorCategory.MEMORY,
            details={"memory_key": memory_key, "layer": layer},
            **kwargs
        )

class VoiceError(StandardError):
    """Voice generation and processing errors"""
    
    def __init__(self, message: str, voice_id: str = None, **kwargs):
        self.voice_id = voice_id
        super().__init__(
            message,
            category=ErrorCategory.VOICE,
            details={"voice_id": voice_id},
            **kwargs
        )

class CoordinationError(StandardError):
    """Cross-domain coordination errors"""
    
    def __init__(self, message: str, coordination_type: str = None, **kwargs):
        self.coordination_type = coordination_type
        super().__init__(
            message,
            category=ErrorCategory.COORDINATION,
            details={"coordination_type": coordination_type},
            **kwargs
        )

class AdminError(StandardError):
    """Admin interface and operations errors"""
    
    def __init__(self, message: str, operation: str = None, admin_user: str = None, **kwargs):
        self.operation = operation
        self.admin_user = admin_user
        super().__init__(
            message,
            category=ErrorCategory.ADMIN,
            details={"operation": operation, "admin_user": admin_user},
            **kwargs
        )

class RAGError(StandardError):
    """RAG system errors"""
    
    def __init__(self, message: str, query: str = None, strategy: str = None, **kwargs):
        self.query = query
        self.strategy = strategy
        super().__init__(
            message,
            category=ErrorCategory.RAG,
            details={"query": query, "strategy": strategy},
            **kwargs
        )

class AgentError(StandardError):
    """Multi-agent system errors"""
    
    def __init__(self, message: str, agent_id: str = None, swarm_id: str = None, **kwargs):
        self.agent_id = agent_id
        self.swarm_id = swarm_id
        super().__init__(
            message,
            category=ErrorCategory.AGENT,
            details={"agent_id": agent_id, "swarm_id": swarm_id},
            **kwargs
        )

class DatabaseError(StandardError):
    """Database operation errors"""
    
    def __init__(self, message: str, query: str = None, table: str = None, **kwargs):
        self.query = query
        self.table = table
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            details={"query": query, "table": table},
            **kwargs
        )

class ValidationError(StandardError):
    """Input validation errors"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        self.field = field
        self.value = value
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details={"field": field, "value": str(value) if value is not None else None},
            **kwargs
        )

# ========================================
# CENTRALIZED ERROR HANDLER
# ========================================

class CentralizedErrorHandler:
    """Centralized error handling and monitoring system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_records: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.error_patterns: Dict[str, List[datetime]] = {}
        self.max_records = 10000  # Keep last 10k errors
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # Alert immediately
            ErrorSeverity.HIGH: 5,      # Alert after 5 in 10 minutes
            ErrorSeverity.MEDIUM: 20,   # Alert after 20 in 30 minutes
            ErrorSeverity.LOW: 100      # Alert after 100 in 1 hour
        }
        self.notification_callbacks: List[Callable] = []
    
    async def handle_error(self, 
                          error: Exception, 
                          context: Optional[ErrorContext] = None) -> ErrorRecord:
        """Handle and log errors consistently"""
        
        # Generate unique error ID
        error_id = f"err_{int(time.time() * 1000)}_{id(error)}"
        
        # Extract error information
        if isinstance(error, StandardError):
            error_type = error.__class__.__name__
            message = error.message
            severity = error.severity
            category = error.category
            user_message = error.user_message
            resolution_steps = error.resolution_steps
        else:
            error_type = type(error).__name__
            message = str(error)
            severity = ErrorSeverity.MEDIUM
            category = ErrorCategory.SYSTEM
            user_message = "An unexpected error occurred. Please try again."
            resolution_steps = ["Check system logs", "Retry the operation", "Contact support if issue persists"]
        
        # Create error context if not provided
        if context is None:
            context = self._extract_context_from_traceback()
        
        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=error_type,
            message=message,
            severity=severity,
            category=category,
            context=context,
            traceback_info=traceback.format_exc(),
            user_message=user_message,
            resolution_steps=resolution_steps
        )
        
        # Store error record
        self.error_records.append(error_record)
        
        # Maintain record limit
        if len(self.error_records) > self.max_records:
            self.error_records = self.error_records[-self.max_records:]
        
        # Update error statistics
        self._update_error_statistics(error_record)
        
        # Log error based on severity
        self._log_error(error_record)
        
        # Check for alert conditions
        await self._check_alert_conditions(error_record)
        
        # Track error patterns
        self._track_error_patterns(error_record)
        
        return error_record
    
    def _extract_context_from_traceback(self) -> ErrorContext:
        """Extract context information from current traceback"""
        
        # Get current frame information
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual error location
            while frame and frame.f_code.co_name in ['handle_error', '_extract_context_from_traceback']:
                frame = frame.f_back
            
            if frame:
                function_name = frame.f_code.co_name
                module_name = frame.f_globals.get('__name__', 'unknown')
                
                # Try to extract additional context from local variables
                local_vars = frame.f_locals
                user_id = local_vars.get('user_id') or local_vars.get('admin_user')
                persona_id = local_vars.get('persona_id')
                operation_id = local_vars.get('operation_id')
                request_id = local_vars.get('request_id')
                
                return ErrorContext(
                    function_name=function_name,
                    module_name=module_name,
                    user_id=user_id,
                    persona_id=persona_id,
                    operation_id=operation_id,
                    request_id=request_id
                )
            else:
                return ErrorContext(
                    function_name="unknown",
                    module_name="unknown"
                )
        finally:
            del frame
    
    def _update_error_statistics(self, error_record: ErrorRecord):
        """Update error statistics and counts"""
        
        # Update error type counts
        error_type = error_record.error_type
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Update category counts
        category_key = f"category_{error_record.category.value}"
        self.error_counts[category_key] = self.error_counts.get(category_key, 0) + 1
        
        # Update severity counts
        severity_key = f"severity_{error_record.severity.value}"
        self.error_counts[severity_key] = self.error_counts.get(severity_key, 0) + 1
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error based on severity level"""
        
        log_message = (
            f"[{error_record.error_id}] {error_record.error_type}: {error_record.message} "
            f"| Context: {error_record.context.function_name} in {error_record.context.module_name}"
        )
        
        extra_data = {
            "error_id": error_record.error_id,
            "error_type": error_record.error_type,
            "severity": error_record.severity.value,
            "category": error_record.category.value,
            "context": error_record.context.__dict__
        }
        
        if error_record.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=extra_data)
        elif error_record.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=extra_data)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=extra_data)
        else:
            self.logger.info(log_message, extra=extra_data)
    
    async def _check_alert_conditions(self, error_record: ErrorRecord):
        """Check if error conditions warrant alerts"""
        
        severity = error_record.severity
        threshold = self.alert_thresholds.get(severity, 0)
        
        if threshold == 0:
            return
        
        # Count recent errors of same severity
        now = datetime.now()
        time_windows = {
            ErrorSeverity.CRITICAL: timedelta(minutes=1),
            ErrorSeverity.HIGH: timedelta(minutes=10),
            ErrorSeverity.MEDIUM: timedelta(minutes=30),
            ErrorSeverity.LOW: timedelta(hours=1)
        }
        
        time_window = time_windows.get(severity, timedelta(minutes=10))
        cutoff_time = now - time_window
        
        recent_errors = [
            record for record in self.error_records
            if record.severity == severity and record.timestamp >= cutoff_time
        ]
        
        if len(recent_errors) >= threshold:
            await self._send_alert(severity, recent_errors)
    
    async def _send_alert(self, severity: ErrorSeverity, recent_errors: List[ErrorRecord]):
        """Send alert for error conditions"""
        
        alert_data = {
            "severity": severity.value,
            "error_count": len(recent_errors),
            "time_window": "recent",
            "errors": [
                {
                    "error_id": record.error_id,
                    "error_type": record.error_type,
                    "message": record.message,
                    "timestamp": record.timestamp.isoformat()
                }
                for record in recent_errors[-5:]  # Last 5 errors
            ]
        }
        
        # Notify all registered callbacks
        for callback in self.notification_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                self.logger.error(f"Error in notification callback: {e}")
    
    def _track_error_patterns(self, error_record: ErrorRecord):
        """Track error patterns for analysis"""
        
        pattern_key = f"{error_record.error_type}_{error_record.category.value}"
        
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = []
        
        self.error_patterns[pattern_key].append(error_record.timestamp)
        
        # Keep only last 100 occurrences per pattern
        if len(self.error_patterns[pattern_key]) > 100:
            self.error_patterns[pattern_key] = self.error_patterns[pattern_key][-100:]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        
        now = datetime.now()
        
        # Calculate time-based statistics
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)
        
        recent_errors = {
            "last_hour": len([r for r in self.error_records if r.timestamp >= last_hour]),
            "last_day": len([r for r in self.error_records if r.timestamp >= last_day]),
            "last_week": len([r for r in self.error_records if r.timestamp >= last_week])
        }
        
        # Calculate severity distribution
        severity_distribution = {}
        for severity in ErrorSeverity:
            severity_distribution[severity.value] = len([
                r for r in self.error_records if r.severity == severity
            ])
        
        # Calculate category distribution
        category_distribution = {}
        for category in ErrorCategory:
            category_distribution[category.value] = len([
                r for r in self.error_records if r.category == category
            ])
        
        # Get top error types
        error_type_counts = {}
        for record in self.error_records:
            error_type_counts[record.error_type] = error_type_counts.get(record.error_type, 0) + 1
        
        top_error_types = sorted(
            error_type_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "total_errors": len(self.error_records),
            "recent_errors": recent_errors,
            "severity_distribution": severity_distribution,
            "category_distribution": category_distribution,
            "top_error_types": top_error_types,
            "error_rate_per_hour": recent_errors["last_hour"],
            "last_updated": now.isoformat()
        }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error records"""
        
        recent_records = self.error_records[-limit:] if self.error_records else []
        
        return [
            {
                "error_id": record.error_id,
                "timestamp": record.timestamp.isoformat(),
                "error_type": record.error_type,
                "message": record.message,
                "severity": record.severity.value,
                "category": record.category.value,
                "context": {
                    "function_name": record.context.function_name,
                    "module_name": record.context.module_name,
                    "user_id": record.context.user_id,
                    "persona_id": record.context.persona_id
                },
                "user_message": record.user_message,
                "resolved": record.resolved
            }
            for record in reversed(recent_records)
        ]
    
    def add_notification_callback(self, callback: Callable):
        """Add notification callback for alerts"""
        self.notification_callbacks.append(callback)
    
    def mark_error_resolved(self, error_id: str, resolution_note: str = None) -> bool:
        """Mark an error as resolved"""
        
        for record in self.error_records:
            if record.error_id == error_id:
                record.resolved = True
                record.resolution_timestamp = datetime.now()
                if resolution_note:
                    record.resolution_steps.append(f"Resolved: {resolution_note}")
                return True
        
        return False

# ========================================
# ERROR HANDLING DECORATORS
# ========================================

def handle_errors(error_type: Type[StandardError] = StandardError, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 user_message: str = None):
    """Decorator for consistent error handling"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except StandardError as e:
                # Re-raise StandardError as-is
                error_record = await error_handler.handle_error(e)
                raise e
            except Exception as e:
                # Convert other exceptions to StandardError
                context = ErrorContext(
                    function_name=func.__name__,
                    module_name=func.__module__
                )
                
                standard_error = error_type(
                    message=f"Error in {func.__name__}: {str(e)}",
                    severity=severity,
                    category=category,
                    user_message=user_message or f"An error occurred in {func.__name__}. Please try again."
                )
                
                error_record = await error_handler.handle_error(standard_error, context)
                raise standard_error
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except StandardError as e:
                # For sync functions, we can't await, so we create a task
                asyncio.create_task(error_handler.handle_error(e))
                raise e
            except Exception as e:
                context = ErrorContext(
                    function_name=func.__name__,
                    module_name=func.__module__
                )
                
                standard_error = error_type(
                    message=f"Error in {func.__name__}: {str(e)}",
                    severity=severity,
                    category=category,
                    user_message=user_message or f"An error occurred in {func.__name__}. Please try again."
                )
                
                asyncio.create_task(error_handler.handle_error(standard_error, context))
                raise standard_error
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def handle_persona_errors(persona_id: str = None):
    """Decorator specifically for persona-related operations"""
    return handle_errors(
        error_type=PersonaError,
        category=ErrorCategory.PERSONA,
        user_message="There was an issue with the AI persona. Please try again."
    )

def handle_memory_errors(memory_key: str = None, layer: str = None):
    """Decorator specifically for memory operations"""
    return handle_errors(
        error_type=MemoryError,
        category=ErrorCategory.MEMORY,
        user_message="There was an issue accessing memory. Please try again."
    )

def handle_voice_errors(voice_id: str = None):
    """Decorator specifically for voice operations"""
    return handle_errors(
        error_type=VoiceError,
        category=ErrorCategory.VOICE,
        user_message="There was an issue with voice generation. Please try again."
    )

def handle_admin_errors(operation: str = None):
    """Decorator specifically for admin operations"""
    return handle_errors(
        error_type=AdminError,
        category=ErrorCategory.ADMIN,
        severity=ErrorSeverity.HIGH,
        user_message="There was an issue with the admin operation. Please check your permissions and try again."
    )

# ========================================
# GLOBAL ERROR HANDLER INSTANCE
# ========================================

# Global centralized error handler
error_handler = CentralizedErrorHandler()

# Export all error handling components
__all__ = [
    "StandardError",
    "PersonaError",
    "MemoryError", 
    "VoiceError",
    "CoordinationError",
    "AdminError",
    "RAGError",
    "AgentError",
    "DatabaseError",
    "ValidationError",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorRecord",
    "CentralizedErrorHandler",
    "handle_errors",
    "handle_persona_errors",
    "handle_memory_errors",
    "handle_voice_errors",
    "handle_admin_errors",
    "error_handler"
]

