"""AI Collaboration Models Package"""

from .enums import AIAgentType, TaskStatus, MetricType, EventType
from .entities import AIAgent, AITask, AIMetric, CollaborationEvent
from .value_objects import TaskPayload, MetricValue, AgentCapabilities
from .dto import (
    AIStatusDTO,
    TaskCreateDTO,
    TaskUpdateDTO,
    MetricDTO,
    CollaborationEventDTO,
)

__all__ = [
    # Enums
    "AIAgentType",
    "TaskStatus",
    "MetricType",
    "EventType",
    # Entities
    "AIAgent",
    "AITask",
    "AIMetric",
    "CollaborationEvent",
    # Value Objects
    "TaskPayload",
    "MetricValue",
    "AgentCapabilities",
    # DTOs
    "AIStatusDTO",
    "TaskCreateDTO",
    "TaskUpdateDTO",
    "MetricDTO",
    "CollaborationEventDTO",
]