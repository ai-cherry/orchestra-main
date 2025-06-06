#!/usr/bin/env python3
"""
Data Transfer Objects for AI Collaboration Service
Clean API contracts with validation and serialization
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from uuid import UUID
import json

from .enums import AIAgentType, TaskStatus, MetricType, EventType
from .value_objects import AgentCapabilities, TaskPayload, MetricValue


@dataclass
class AIStatusDTO:
    """DTO for AI agent status information"""
    agent_id: int
    agent_type: AIAgentType
    agent_name: str
    status: str
    active_tasks: int
    completed_tasks_hour: int
    avg_response_time: Optional[float]
    error_count: int
    last_heartbeat: Optional[str]  # ISO format string
    performance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "agent_name": self.agent_name,
            "status": self.status,
            "active_tasks": self.active_tasks,
            "completed_tasks_hour": self.completed_tasks_hour,
            "avg_response_time": self.avg_response_time,
            "error_count": self.error_count,
            "last_heartbeat": self.last_heartbeat,
            "performance_score": self.performance_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIStatusDTO':
        """Create from dictionary"""
        return cls(
            agent_id=data["agent_id"],
            agent_type=AIAgentType(data["agent_type"]),
            agent_name=data["agent_name"],
            status=data["status"],
            active_tasks=data["active_tasks"],
            completed_tasks_hour=data["completed_tasks_hour"],
            avg_response_time=data.get("avg_response_time"),
            error_count=data["error_count"],
            last_heartbeat=data.get("last_heartbeat"),
            performance_score=data.get("performance_score", 50.0)
        )
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy"""
        return (
            self.status == "active"
            and self.error_count < 10
            and self.performance_score > 30
        )


@dataclass
class TaskCreateDTO:
    """DTO for creating a new task"""
    task_type: str
    task_data: Dict[str, Any]
    priority: int = 5
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate task creation data"""
        if not self.task_type:
            raise ValueError("task_type is required")
        if not isinstance(self.task_data, dict):
            raise ValueError("task_data must be a dictionary")
        if not 1 <= self.priority <= 10:
            raise ValueError("priority must be between 1 and 10")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskCreateDTO':
        """Create from dictionary"""
        return cls(**data)
    
    def validate(self) -> List[str]:
        """Validate and return list of errors"""
        errors = []
        
        if not self.task_type:
            errors.append("task_type is required")
        
        if not self.task_data:
            errors.append("task_data cannot be empty")
        
        if not 1 <= self.priority <= 10:
            errors.append("priority must be between 1 and 10")
        
        # Validate specific task types
        if self.task_type == "deployment":
            if "target" not in self.task_data:
                errors.append("deployment tasks require 'target' in task_data")
            if "version" not in self.task_data:
                errors.append("deployment tasks require 'version' in task_data")
        
        return errors


@dataclass
class TaskUpdateDTO:
    """DTO for updating task status"""
    task_id: UUID
    status: TaskStatus
    error_details: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": str(self.task_id),
            "status": self.status.value,
            "error_details": self.error_details,
            "result": self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskUpdateDTO':
        """Create from dictionary"""
        return cls(
            task_id=UUID(data["task_id"]),
            status=TaskStatus(data["status"]),
            error_details=data.get("error_details"),
            result=data.get("result")
        )
    
    def is_terminal(self) -> bool:
        """Check if this update represents a terminal state"""
        return self.status.is_terminal()


@dataclass
class MetricDTO:
    """DTO for metric data"""
    agent_id: int
    metric_type: MetricType
    value: float
    timestamp: str  # ISO format
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetricDTO':
        """Create from dictionary"""
        return cls(
            agent_id=data["agent_id"],
            metric_type=MetricType(data["metric_type"]),
            value=data["value"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {})
        )
    
    def get_formatted_value(self) -> str:
        """Get formatted value with unit"""
        unit = self.metric_type.get_unit()
        return f"{self.value} {unit}".strip()


@dataclass
class CollaborationEventDTO:
    """DTO for collaboration events"""
    event_type: EventType
    source_agent_id: Optional[int] = None
    target_agent_id: Optional[int] = None
    task_id: Optional[str] = None  # String representation of UUID
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "task_id": self.task_id,
            "event_data": self.event_data,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollaborationEventDTO':
        """Create from dictionary"""
        return cls(
            event_type=EventType(data["event_type"]),
            source_agent_id=data.get("source_agent_id"),
            target_agent_id=data.get("target_agent_id"),
            task_id=data.get("task_id"),
            event_data=data.get("event_data", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )
    
    def get_severity(self) -> str:
        """Get event severity"""
        return self.event_type.get_severity()


@dataclass
class DashboardSummaryDTO:
    """DTO for dashboard summary data"""
    total_agents: int
    active_agents: int
    total_tasks: int
    active_tasks: int
    completed_tasks_hour: int
    failed_tasks_hour: int
    avg_task_duration: float
    system_health: str  # "healthy", "degraded", "critical"
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_metrics(cls, agents: List[AIStatusDTO], tasks_data: Dict[str, Any]) -> 'DashboardSummaryDTO':
        """Create summary from agent statuses and task data"""
        total_agents = len(agents)
        active_agents = sum(1 for a in agents if a.status == "active")
        
        # Calculate system health
        if active_agents == 0:
            health = "critical"
        elif active_agents < total_agents * 0.5:
            health = "degraded"
        else:
            health = "healthy"
        
        # Generate alerts
        alerts = []
        for agent in agents:
            if not agent.is_healthy():
                alerts.append({
                    "type": "agent_unhealthy",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "reason": "High error rate" if agent.error_count >= 10 else "Low performance"
                })
        
        return cls(
            total_agents=total_agents,
            active_agents=active_agents,
            total_tasks=tasks_data.get("total_tasks", 0),
            active_tasks=tasks_data.get("active_tasks", 0),
            completed_tasks_hour=tasks_data.get("completed_tasks_hour", 0),
            failed_tasks_hour=tasks_data.get("failed_tasks_hour", 0),
            avg_task_duration=tasks_data.get("avg_task_duration", 0.0),
            system_health=health,
            alerts=alerts
        )


@dataclass
class TaskAssignmentDTO:
    """DTO for task assignment result"""
    task_id: str
    assigned_to: str  # Agent type
    agent_id: int
    estimated_duration: float
    confidence: float  # 0-1 confidence in assignment
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class PerformanceReportDTO:
    """DTO for performance reporting"""
    time_period: str  # e.g., "1h", "24h", "7d"
    agent_performance: List[Dict[str, Any]]
    task_metrics: Dict[str, Any]
    collaboration_metrics: Dict[str, Any]
    system_metrics: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def generate_insights(self) -> List[str]:
        """Generate insights from performance data"""
        insights = []
        
        # Analyze agent performance
        if self.agent_performance:
            avg_score = sum(a["performance_score"] for a in self.agent_performance) / len(self.agent_performance)
            if avg_score < 50:
                insights.append("Overall agent performance is below average. Consider scaling resources.")
            
            # Find underperforming agents
            underperformers = [a for a in self.agent_performance if a["performance_score"] < 30]
            if underperformers:
                insights.append(f"{len(underperformers)} agents are underperforming and may need attention.")
        
        # Analyze task metrics
        if self.task_metrics.get("failure_rate", 0) > 0.1:
            insights.append("High task failure rate detected. Review error logs and retry policies.")
        
        if self.task_metrics.get("avg_duration", 0) > 300:
            insights.append("Average task duration exceeds 5 minutes. Consider optimizing task processing.")
        
        # Analyze collaboration
        if self.collaboration_metrics.get("collaboration_count", 0) == 0:
            insights.append("No AI collaboration detected. Consider enabling multi-agent workflows.")
        
        return insights


@dataclass
class WebSocketMessageDTO:
    """DTO for WebSocket messages"""
    message_type: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessageDTO':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessageDTO':
        """Create from dictionary"""
        return cls(
            message_type=data["message_type"],
            payload=data["payload"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            correlation_id=data.get("correlation_id")
        )


# API Request/Response DTOs

@dataclass
class CreateAgentRequest:
    """Request DTO for creating an agent"""
    name: str
    type: AIAgentType
    capabilities: AgentCapabilities
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate request"""
        errors = []
        if not self.name:
            errors.append("Agent name is required")
        if len(self.name) > 100:
            errors.append("Agent name must be less than 100 characters")
        return errors


@dataclass
class CreateAgentResponse:
    """Response DTO for agent creation"""
    id: str
    name: str
    type: AIAgentType
    status: str
    capabilities: AgentCapabilities
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status,
            "capabilities": asdict(self.capabilities),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CreateTaskRequest:
    """Request DTO for creating a task"""
    title: str
    description: str
    agent_type: AIAgentType
    priority: int = 5
    payload: Optional[TaskPayload] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate request"""
        errors = []
        if not self.title:
            errors.append("Task title is required")
        if not self.description:
            errors.append("Task description is required")
        if not 1 <= self.priority <= 10:
            errors.append("Priority must be between 1 and 10")
        return errors


@dataclass
class CreateTaskResponse:
    """Response DTO for task creation"""
    id: str
    title: str
    description: str
    agent_type: AIAgentType
    status: TaskStatus
    priority: int
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class UpdateTaskRequest:
    """Request DTO for updating a task"""
    status: TaskStatus
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskResponse:
    """Response DTO for task details"""
    id: str
    title: str
    description: str
    agent_type: AIAgentType
    status: TaskStatus
    priority: int
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class MetricRequest:
    """Request DTO for recording a metric"""
    agent_id: str
    type: MetricType
    value: MetricValue
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricResponse:
    """Response DTO for metric details"""
    id: str
    agent_id: str
    type: MetricType
    value: MetricValue
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "type": self.type.value,
            "value": asdict(self.value),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CollaborationEventResponse:
    """Response DTO for collaboration event"""
    id: str
    type: EventType
    agent_id: Optional[str]
    task_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }