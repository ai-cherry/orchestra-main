#!/usr/bin/env python3
"""
AI Collaboration Service Package
Production-ready implementation following SOLID principles and clean architecture
"""

from typing import TYPE_CHECKING

# Version info
__version__ = "1.0.0"
__author__ = "Cherry AI Team"

# Public API exports
__all__ = [
    "AICollaborationService",
    "CollaborationBridgeAdapter",
    "AIMetricsCollector",
    "AITaskRouter",
    "AICollaborationAPI",
    "AIAgentType",
    "TaskStatus",
    "MetricType",
    "CollaborationEvent",
]

# Lazy imports for better performance
if TYPE_CHECKING:
    from .service import AICollaborationService
    from .adapters.websocket_adapter import CollaborationBridgeAdapter
    from .metrics.collector import AIMetricsCollector
    from .routing.task_router import AITaskRouter
    from .api.endpoints import AICollaborationAPI
    from .models.enums import AIAgentType, TaskStatus, MetricType
    from .models.events import CollaborationEvent
else:
    # Deferred imports
    def __getattr__(name):
        if name == "AICollaborationService":
            from .service import AICollaborationService
            return AICollaborationService
        elif name == "CollaborationBridgeAdapter":
            from .adapters.websocket_adapter import CollaborationBridgeAdapter
            return CollaborationBridgeAdapter
        elif name == "AIMetricsCollector":
            from .metrics.collector import AIMetricsCollector
            return AIMetricsCollector
        elif name == "AITaskRouter":
            from .routing.task_router import AITaskRouter
            return AITaskRouter
        elif name == "AICollaborationAPI":
            from .api.endpoints import AICollaborationAPI
            return AICollaborationAPI
        elif name == "AIAgentType":
            from .models.enums import AIAgentType
            return AIAgentType
        elif name == "TaskStatus":
            from .models.enums import TaskStatus
            return TaskStatus
        elif name == "MetricType":
            from .models.enums import MetricType
            return MetricType
        elif name == "CollaborationEvent":
            from .models.events import CollaborationEvent
            return CollaborationEvent
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")