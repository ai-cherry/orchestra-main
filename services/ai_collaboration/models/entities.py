#!/usr/bin/env python3
"""
Domain Entities for AI Collaboration Service
Following Domain-Driven Design principles with rich domain models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from .enums import AIAgentType, TaskStatus, MetricType, EventType
from .value_objects import TaskPayload, MetricValue, AgentCapabilities


@dataclass
class AIAgent:
    """
    AI Agent entity representing an AI system in the collaboration network
    This is an aggregate root in DDD terms
    """
    id: int
    agent_type: AIAgentType
    agent_name: str
    capabilities: AgentCapabilities
    status: str = "inactive"
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Runtime state (not persisted)
    _active_tasks: List['AITask'] = field(default_factory=list, init=False, repr=False)
    _performance_metrics: Dict[MetricType, float] = field(default_factory=dict, init=False, repr=False)
    
    def __post_init__(self):
        """Validate agent after initialization"""
        if not self.agent_name:
            raise ValueError("Agent name cannot be empty")
        if self.agent_type not in AIAgentType:
            raise ValueError(f"Invalid agent type: {self.agent_type}")
    
    def is_available(self) -> bool:
        """Check if agent is available for new tasks"""
        if self.status != "active":
            return False
        if self.last_heartbeat:
            time_since_heartbeat = (datetime.utcnow() - self.last_heartbeat).total_seconds()
            if time_since_heartbeat > 60:  # 1 minute timeout
                return False
        return True
    
    def can_handle_task(self, task_type: str) -> bool:
        """Check if agent can handle a specific task type"""
        return self.capabilities.supports_task_type(task_type)
    
    def get_current_load(self) -> int:
        """Get current number of active tasks"""
        return len([task for task in self._active_tasks if task.is_active()])
    
    def assign_task(self, task: 'AITask') -> None:
        """Assign a task to this agent"""
        if not self.is_available():
            raise RuntimeError(f"Agent {self.agent_name} is not available")
        if not self.can_handle_task(task.task_type):
            raise ValueError(f"Agent {self.agent_name} cannot handle task type {task.task_type}")
        
        self._active_tasks.append(task)
        task.assign_to_agent(self.id)
    
    def update_heartbeat(self) -> None:
        """Update the last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_performance_metric(self, metric_type: MetricType, value: float) -> None:
        """Update a performance metric for this agent"""
        self._performance_metrics[metric_type] = value
    
    def get_performance_score(self) -> float:
        """Calculate overall performance score (0-100)"""
        if not self._performance_metrics:
            return 50.0  # Default neutral score
        
        # Weighted scoring based on different metrics
        weights = {
            MetricType.RESPONSE_TIME: -0.3,  # Lower is better
            MetricType.TASK_DURATION: -0.2,  # Lower is better
            MetricType.ERROR_RATE: -0.3,     # Lower is better
            MetricType.THROUGHPUT: 0.2,      # Higher is better
        }
        
        score = 50.0  # Base score
        for metric_type, weight in weights.items():
            if metric_type in self._performance_metrics:
                # Normalize metric value (this is simplified, real implementation would use proper normalization)
                metric_value = self._performance_metrics[metric_type]
                score += weight * metric_value
        
        return max(0.0, min(100.0, score))


@dataclass
class AITask:
    """
    AI Task entity representing a unit of work for AI agents
    """
    id: int
    task_id: UUID = field(default_factory=uuid4)
    agent_id: Optional[int] = None
    task_type: str = ""
    payload: TaskPayload = field(default_factory=TaskPayload)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5  # 1-10, higher is more important
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300  # 5 minutes default
    
    def __post_init__(self):
        """Validate task after initialization"""
        if not self.task_type:
            raise ValueError("Task type cannot be empty")
        if not 1 <= self.priority <= 10:
            raise ValueError("Priority must be between 1 and 10")
    
    def is_active(self) -> bool:
        """Check if task is in an active state"""
        return self.status.is_active()
    
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state"""
        return self.status.is_terminal()
    
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (
            self.status == TaskStatus.FAILED
            and self.retry_count < self.max_retries
        )
    
    def assign_to_agent(self, agent_id: int) -> None:
        """Assign task to an agent"""
        if self.status != TaskStatus.PENDING and self.status != TaskStatus.QUEUED:
            raise ValueError(f"Cannot assign task in status {self.status}")
        
        self.agent_id = agent_id
        self.transition_to(TaskStatus.ASSIGNED)
    
    def start(self) -> None:
        """Mark task as started"""
        if self.status != TaskStatus.ASSIGNED:
            raise ValueError(f"Cannot start task in status {self.status}")
        
        self.started_at = datetime.utcnow()
        self.transition_to(TaskStatus.IN_PROGRESS)
    
    def complete(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as completed"""
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete task in status {self.status}")
        
        self.completed_at = datetime.utcnow()
        if result:
            self.payload.result = result
        self.transition_to(TaskStatus.COMPLETED)
    
    def fail(self, error: Dict[str, Any]) -> None:
        """Mark task as failed"""
        if not self.status.is_active():
            raise ValueError(f"Cannot fail task in status {self.status}")
        
        self.error_details = error
        self.transition_to(TaskStatus.FAILED)
    
    def retry(self) -> None:
        """Retry a failed task"""
        if not self.can_retry():
            raise ValueError("Task cannot be retried")
        
        self.retry_count += 1
        self.error_details = None
        self.started_at = None
        self.completed_at = None
        self.transition_to(TaskStatus.RETRYING)
    
    def cancel(self, reason: str = "") -> None:
        """Cancel the task"""
        if self.is_terminal():
            raise ValueError(f"Cannot cancel task in terminal status {self.status}")
        
        if reason:
            self.error_details = {"cancellation_reason": reason}
        self.transition_to(TaskStatus.CANCELLED)
    
    def transition_to(self, new_status: TaskStatus) -> None:
        """Transition to a new status with validation"""
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        
        self.status = new_status
    
    def get_duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_timed_out(self) -> bool:
        """Check if task has timed out"""
        if self.started_at and self.status == TaskStatus.IN_PROGRESS:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
            return elapsed > self.timeout_seconds
        return False


@dataclass
class AIMetric:
    """
    AI Metric entity for performance tracking
    """
    id: int
    agent_id: int
    metric_type: MetricType
    value: MetricValue
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate metric after initialization"""
        if self.agent_id <= 0:
            raise ValueError("Invalid agent ID")
        if self.metric_type not in MetricType:
            raise ValueError(f"Invalid metric type: {self.metric_type}")
        if not self.value.is_valid():
            raise ValueError("Invalid metric value")
    
    def is_anomalous(self, threshold: float) -> bool:
        """Check if metric value is anomalous based on threshold"""
        return self.value.is_anomalous(threshold)
    
    def get_formatted_value(self) -> str:
        """Get formatted value with unit"""
        unit = self.metric_type.get_unit()
        return f"{self.value.value} {unit}".strip()


@dataclass
class CollaborationEvent:
    """
    Collaboration Event entity for tracking AI interactions
    """
    id: int
    event_type: EventType
    source_agent_id: Optional[int] = None
    target_agent_id: Optional[int] = None
    task_id: Optional[UUID] = None
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate event after initialization"""
        if self.event_type not in EventType:
            raise ValueError(f"Invalid event type: {self.event_type}")
        
        # Validate required fields based on event type
        if self.event_type in EventType.task_events():
            if not self.task_id:
                raise ValueError(f"Task ID required for event type {self.event_type}")
        
        if self.event_type in EventType.collaboration_events():
            if not self.source_agent_id or not self.target_agent_id:
                raise ValueError(f"Source and target agents required for event type {self.event_type}")
    
    def get_severity(self) -> str:
        """Get event severity level"""
        return self.event_type.get_severity()
    
    def is_error(self) -> bool:
        """Check if this is an error event"""
        return self.get_severity() == "error"
    
    def is_warning(self) -> bool:
        """Check if this is a warning event"""
        return self.get_severity() == "warning"
    
    def to_log_entry(self) -> str:
        """Convert event to log entry format"""
        parts = [
            f"[{self.timestamp.isoformat()}]",
            f"[{self.get_severity().upper()}]",
            f"Event: {self.event_type.value}",
        ]
        
        if self.source_agent_id:
            parts.append(f"Source: Agent#{self.source_agent_id}")
        if self.target_agent_id:
            parts.append(f"Target: Agent#{self.target_agent_id}")
        if self.task_id:
            parts.append(f"Task: {self.task_id}")
        
        if self.event_data:
            parts.append(f"Data: {self.event_data}")
        
        return " | ".join(parts)