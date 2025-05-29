"""
Resilience module for the AgentOrchestrator.

This package provides components for implementing the circuit breaker pattern,
Cloud Monitoring integration, and fallback mechanisms to ensure robust agent operations.
"""

from core.orchestrator.src.resilience.circuit_breaker import CircuitBreaker, get_circuit_breaker
from core.orchestrator.src.resilience.incident_reporter import IncidentReporter, get_incident_reporter
from core.orchestrator.src.resilience.monitoring import GCPMonitoringClient, get_monitoring_client
from core.orchestrator.src.resilience.tasks import (
    TaskQueueManager,
    VertexAiFallbackHandler,
    get_fallback_handler,
    get_task_queue_manager,
)

__all__ = [
    "CircuitBreaker",
    "get_circuit_breaker",
    "GCPMonitoringClient",
    "get_monitoring_client",
    "TaskQueueManager",
    "VertexAiFallbackHandler",
    "get_task_queue_manager",
    "get_fallback_handler",
    "IncidentReporter",
    "get_incident_reporter",
]
