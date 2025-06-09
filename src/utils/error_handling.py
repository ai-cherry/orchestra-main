from enum import Enum
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Classification of error severity."""
    CRITICAL = "critical"  # System cannot continue
    ERROR = "error"        # Operation failed but system can continue
    WARNING = "warning"    # Operation succeeded with issues
    INFO = "info"          # Informational only

class ErrorHandler:
    """Centralized error handling with specific exception types."""
    @staticmethod
    def handle_exception(
        e: Exception,
        context: Dict[str, Any] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recovery_action: Optional[Callable] = None
    ) -> Dict[str, Any]:
        context = context or {}
        logger.error(f"[{severity.value.upper()}] Exception: {str(e)} | Context: {context}")
        if severity == ErrorSeverity.CRITICAL:
            # Optionally trigger alerts or system shutdown
            logger.critical(f"Critical error occurred: {str(e)}")
        if recovery_action:
            try:
                return recovery_action()
            except Exception as recovery_e:
                logger.error(f"Recovery action failed: {str(recovery_e)}")
        return {
            "status": "error",
            "severity": severity.value,
            "message": str(e),
            "context": context
        } 