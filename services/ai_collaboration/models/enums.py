#!/usr/bin/env python3
"""
Enumerations for AI Collaboration Service
Following best practices for type safety and extensibility
"""

from enum import Enum, auto
from typing import List, Set


class AIAgentType(str, Enum):
    """AI Agent types with string values for JSON serialization"""
    MANUS = "manus"
    CURSOR = "cursor"
    CLAUDE = "claude"
    GPT4 = "gpt4"
    CUSTOM = "custom"
    
    @classmethod
    def get_deployment_agents(cls) -> Set['AIAgentType']:
        """Get agents specialized for deployment tasks"""
        return {cls.MANUS}
    
    @classmethod
    def get_development_agents(cls) -> Set['AIAgentType']:
        """Get agents specialized for development tasks"""
        return {cls.CURSOR}
    
    @classmethod
    def get_architecture_agents(cls) -> Set['AIAgentType']:
        """Get agents specialized for architecture tasks"""
        return {cls.CLAUDE}
    
    @classmethod
    def get_analysis_agents(cls) -> Set['AIAgentType']:
        """Get agents specialized for analysis tasks"""
        return {cls.GPT4}
    
    def get_capabilities(self) -> List[str]:
        """Get capabilities for this agent type"""
        capabilities_map = {
            self.MANUS: ["deployment", "infrastructure", "ci_cd", "monitoring"],
            self.CURSOR: ["development", "code_generation", "refactoring", "testing"],
            self.CLAUDE: ["architecture", "design", "documentation", "planning"],
            self.GPT4: ["analysis", "optimization", "research", "general"],
            self.CUSTOM: ["configurable"],
        }
        return capabilities_map.get(self, [])


class TaskStatus(str, Enum):
    """Task status with string values for database storage"""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    
    @classmethod
    def active_statuses(cls) -> Set['TaskStatus']:
        """Get statuses that indicate active tasks"""
        return {cls.PENDING, cls.QUEUED, cls.ASSIGNED, cls.IN_PROGRESS, cls.RETRYING}
    
    @classmethod
    def terminal_statuses(cls) -> Set['TaskStatus']:
        """Get statuses that indicate terminal states"""
        return {cls.COMPLETED, cls.FAILED, cls.CANCELLED}
    
    def is_active(self) -> bool:
        """Check if this status indicates an active task"""
        return self in self.active_statuses()
    
    def is_terminal(self) -> bool:
        """Check if this status indicates a terminal state"""
        return self in self.terminal_statuses()
    
    def can_transition_to(self, new_status: 'TaskStatus') -> bool:
        """Check if transition to new status is valid"""
        valid_transitions = {
            self.PENDING: {self.QUEUED, self.CANCELLED},
            self.QUEUED: {self.ASSIGNED, self.CANCELLED},
            self.ASSIGNED: {self.IN_PROGRESS, self.CANCELLED},
            self.IN_PROGRESS: {self.COMPLETED, self.FAILED, self.CANCELLED},
            self.FAILED: {self.RETRYING, self.CANCELLED},
            self.RETRYING: {self.IN_PROGRESS, self.FAILED, self.CANCELLED},
            self.COMPLETED: set(),
            self.CANCELLED: set(),
        }
        return new_status in valid_transitions.get(self, set())


class MetricType(str, Enum):
    """Metric types for performance monitoring"""
    RESPONSE_TIME = "response_time"
    TASK_DURATION = "task_duration"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    QUEUE_DEPTH = "queue_depth"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    WEBSOCKET_LATENCY = "websocket_latency"
    API_LATENCY = "api_latency"
    CACHE_HIT_RATE = "cache_hit_rate"
    
    @classmethod
    def performance_metrics(cls) -> Set['MetricType']:
        """Get performance-related metrics"""
        return {
            cls.RESPONSE_TIME,
            cls.TASK_DURATION,
            cls.THROUGHPUT,
            cls.WEBSOCKET_LATENCY,
            cls.API_LATENCY,
        }
    
    @classmethod
    def resource_metrics(cls) -> Set['MetricType']:
        """Get resource-related metrics"""
        return {cls.MEMORY_USAGE, cls.CPU_USAGE, cls.QUEUE_DEPTH}
    
    @classmethod
    def quality_metrics(cls) -> Set['MetricType']:
        """Get quality-related metrics"""
        return {cls.ERROR_RATE, cls.CACHE_HIT_RATE}
    
    def get_unit(self) -> str:
        """Get the unit for this metric type"""
        units = {
            self.RESPONSE_TIME: "ms",
            self.TASK_DURATION: "seconds",
            self.ERROR_RATE: "percentage",
            self.THROUGHPUT: "tasks/second",
            self.QUEUE_DEPTH: "count",
            self.MEMORY_USAGE: "MB",
            self.CPU_USAGE: "percentage",
            self.WEBSOCKET_LATENCY: "ms",
            self.API_LATENCY: "ms",
            self.CACHE_HIT_RATE: "percentage",
        }
        return units.get(self, "")
    
    def get_aggregation_method(self) -> str:
        """Get the preferred aggregation method for this metric"""
        aggregations = {
            self.RESPONSE_TIME: "percentile",
            self.TASK_DURATION: "average",
            self.ERROR_RATE: "average",
            self.THROUGHPUT: "sum",
            self.QUEUE_DEPTH: "max",
            self.MEMORY_USAGE: "max",
            self.CPU_USAGE: "average",
            self.WEBSOCKET_LATENCY: "percentile",
            self.API_LATENCY: "percentile",
            self.CACHE_HIT_RATE: "average",
        }
        return aggregations.get(self, "average")


class EventType(str, Enum):
    """Event types for collaboration tracking"""
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_ONLINE = "agent_online"
    AGENT_OFFLINE = "agent_offline"
    COLLABORATION_STARTED = "collaboration_started"
    COLLABORATION_ENDED = "collaboration_ended"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_ALERT = "performance_alert"
    
    @classmethod
    def task_events(cls) -> Set['EventType']:
        """Get task-related events"""
        return {
            cls.TASK_CREATED,
            cls.TASK_ASSIGNED,
            cls.TASK_STARTED,
            cls.TASK_COMPLETED,
            cls.TASK_FAILED,
        }
    
    @classmethod
    def agent_events(cls) -> Set['EventType']:
        """Get agent-related events"""
        return {cls.AGENT_ONLINE, cls.AGENT_OFFLINE}
    
    @classmethod
    def collaboration_events(cls) -> Set['EventType']:
        """Get collaboration-related events"""
        return {
            cls.COLLABORATION_STARTED,
            cls.COLLABORATION_ENDED,
            cls.MESSAGE_SENT,
            cls.MESSAGE_RECEIVED,
        }
    
    @classmethod
    def alert_events(cls) -> Set['EventType']:
        """Get alert-related events"""
        return {cls.ERROR_OCCURRED, cls.PERFORMANCE_ALERT}
    
    def get_severity(self) -> str:
        """Get severity level for this event type"""
        severities = {
            self.TASK_CREATED: "info",
            self.TASK_ASSIGNED: "info",
            self.TASK_STARTED: "info",
            self.TASK_COMPLETED: "info",
            self.TASK_FAILED: "warning",
            self.AGENT_ONLINE: "info",
            self.AGENT_OFFLINE: "warning",
            self.COLLABORATION_STARTED: "info",
            self.COLLABORATION_ENDED: "info",
            self.MESSAGE_SENT: "debug",
            self.MESSAGE_RECEIVED: "debug",
            self.ERROR_OCCURRED: "error",
            self.PERFORMANCE_ALERT: "warning",
        }
        return severities.get(self, "info")