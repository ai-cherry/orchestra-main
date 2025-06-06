#!/usr/bin/env python3
"""
Value Objects for AI Collaboration Service
Immutable objects that represent domain concepts without identity
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import json


@dataclass(frozen=True)
class TaskPayload:
    """
    Immutable value object representing task data
    """
    task_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate payload structure"""
        if not isinstance(self.task_data, dict):
            raise ValueError("task_data must be a dictionary")
        if not isinstance(self.context, dict):
            raise ValueError("context must be a dictionary")
        if not isinstance(self.constraints, dict):
            raise ValueError("constraints must be a dictionary")
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "task_data": self.task_data,
            "context": self.context,
            "constraints": self.constraints,
            "result": self.result
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskPayload':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(
            task_data=data.get("task_data", {}),
            context=data.get("context", {}),
            constraints=data.get("constraints", {}),
            result=data.get("result")
        )
    
    def with_result(self, result: Dict[str, Any]) -> 'TaskPayload':
        """Create new payload with result"""
        return TaskPayload(
            task_data=self.task_data,
            context=self.context,
            constraints=self.constraints,
            result=result
        )
    
    def get_timeout(self) -> int:
        """Get timeout from constraints"""
        return self.constraints.get("timeout_seconds", 300)
    
    def get_max_retries(self) -> int:
        """Get max retries from constraints"""
        return self.constraints.get("max_retries", 3)
    
    def requires_collaboration(self) -> bool:
        """Check if task requires collaboration"""
        return self.constraints.get("requires_collaboration", False)


@dataclass(frozen=True)
class MetricValue:
    """
    Immutable value object representing a metric measurement
    """
    value: float
    unit: str = ""
    confidence: float = 1.0  # 0-1 confidence score
    
    def __post_init__(self):
        """Validate metric value"""
        if not isinstance(self.value, (int, float)):
            raise ValueError("value must be numeric")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
    
    def is_valid(self) -> bool:
        """Check if metric value is valid"""
        return (
            isinstance(self.value, (int, float))
            and not (self.value != self.value)  # Check for NaN
            and self.confidence > 0
        )
    
    def is_anomalous(self, threshold: float) -> bool:
        """Check if value exceeds threshold"""
        return abs(self.value) > threshold
    
    def with_confidence(self, confidence: float) -> 'MetricValue':
        """Create new value with different confidence"""
        return MetricValue(
            value=self.value,
            unit=self.unit,
            confidence=confidence
        )
    
    def __str__(self) -> str:
        """String representation"""
        if self.unit:
            return f"{self.value} {self.unit}"
        return str(self.value)


@dataclass(frozen=True)
class AgentCapabilities:
    """
    Immutable value object representing AI agent capabilities
    """
    supported_tasks: Set[str] = field(default_factory=set)
    max_concurrent_tasks: int = 5
    supported_languages: Set[str] = field(default_factory=lambda: {"en"})
    features: Dict[str, bool] = field(default_factory=dict)
    performance_profile: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate capabilities"""
        if self.max_concurrent_tasks < 1:
            raise ValueError("max_concurrent_tasks must be at least 1")
        
        # Convert lists to sets for immutability
        if isinstance(self.supported_tasks, list):
            object.__setattr__(self, 'supported_tasks', set(self.supported_tasks))
        if isinstance(self.supported_languages, list):
            object.__setattr__(self, 'supported_languages', set(self.supported_languages))
    
    def supports_task_type(self, task_type: str) -> bool:
        """Check if agent supports a task type"""
        return task_type in self.supported_tasks or "*" in self.supported_tasks
    
    def supports_language(self, language: str) -> bool:
        """Check if agent supports a language"""
        return language in self.supported_languages or "*" in self.supported_languages
    
    def has_feature(self, feature: str) -> bool:
        """Check if agent has a feature"""
        return self.features.get(feature, False)
    
    def get_performance_score(self, metric: str) -> float:
        """Get performance score for a metric"""
        return self.performance_profile.get(metric, 0.5)  # Default to neutral
    
    def with_task_type(self, task_type: str) -> 'AgentCapabilities':
        """Create new capabilities with additional task type"""
        new_tasks = self.supported_tasks | {task_type}
        return AgentCapabilities(
            supported_tasks=new_tasks,
            max_concurrent_tasks=self.max_concurrent_tasks,
            supported_languages=self.supported_languages,
            features=self.features,
            performance_profile=self.performance_profile
        )
    
    def with_feature(self, feature: str, enabled: bool = True) -> 'AgentCapabilities':
        """Create new capabilities with feature toggle"""
        new_features = dict(self.features)
        new_features[feature] = enabled
        return AgentCapabilities(
            supported_tasks=self.supported_tasks,
            max_concurrent_tasks=self.max_concurrent_tasks,
            supported_languages=self.supported_languages,
            features=new_features,
            performance_profile=self.performance_profile
        )
    
    @classmethod
    def default_for_agent_type(cls, agent_type: str) -> 'AgentCapabilities':
        """Create default capabilities for an agent type"""
        defaults = {
            "manus": cls(
                supported_tasks={"deployment", "infrastructure", "monitoring", "ci_cd"},
                max_concurrent_tasks=10,
                features={
                    "auto_rollback": True,
                    "blue_green_deployment": True,
                    "health_checks": True,
                    "metrics_collection": True
                },
                performance_profile={
                    "deployment_speed": 0.9,
                    "reliability": 0.95,
                    "resource_efficiency": 0.8
                }
            ),
            "cursor": cls(
                supported_tasks={"development", "code_generation", "refactoring", "testing"},
                max_concurrent_tasks=5,
                features={
                    "syntax_highlighting": True,
                    "auto_completion": True,
                    "code_analysis": True,
                    "test_generation": True
                },
                performance_profile={
                    "code_quality": 0.85,
                    "development_speed": 0.9,
                    "test_coverage": 0.8
                }
            ),
            "claude": cls(
                supported_tasks={"architecture", "design", "documentation", "planning", "analysis"},
                max_concurrent_tasks=3,
                features={
                    "diagram_generation": True,
                    "pattern_recognition": True,
                    "best_practices": True,
                    "security_analysis": True
                },
                performance_profile={
                    "design_quality": 0.95,
                    "comprehensiveness": 0.9,
                    "clarity": 0.85
                }
            ),
            "gpt4": cls(
                supported_tasks={"*"},  # Can handle any task
                max_concurrent_tasks=8,
                features={
                    "multi_modal": True,
                    "context_understanding": True,
                    "creative_solutions": True,
                    "optimization": True
                },
                performance_profile={
                    "versatility": 0.95,
                    "accuracy": 0.9,
                    "creativity": 0.85
                }
            )
        }
        
        return defaults.get(agent_type, cls(supported_tasks={"general"}))


@dataclass(frozen=True)
class TimeWindow:
    """
    Immutable value object representing a time window
    """
    start: datetime
    end: datetime
    
    def __post_init__(self):
        """Validate time window"""
        if self.start >= self.end:
            raise ValueError("start must be before end")
    
    def duration_seconds(self) -> float:
        """Get duration in seconds"""
        return (self.end - self.start).total_seconds()
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within window"""
        return self.start <= timestamp <= self.end
    
    def overlaps(self, other: 'TimeWindow') -> bool:
        """Check if windows overlap"""
        return not (self.end < other.start or other.end < self.start)
    
    def merge(self, other: 'TimeWindow') -> 'TimeWindow':
        """Merge two overlapping windows"""
        if not self.overlaps(other):
            raise ValueError("Windows do not overlap")
        return TimeWindow(
            start=min(self.start, other.start),
            end=max(self.end, other.end)
        )


@dataclass(frozen=True)
class ResourceRequirements:
    """
    Immutable value object representing resource requirements
    """
    cpu_cores: float = 1.0
    memory_mb: int = 512
    gpu_required: bool = False
    network_bandwidth_mbps: float = 10.0
    storage_gb: float = 1.0
    
    def __post_init__(self):
        """Validate requirements"""
        if self.cpu_cores <= 0:
            raise ValueError("cpu_cores must be positive")
        if self.memory_mb <= 0:
            raise ValueError("memory_mb must be positive")
        if self.network_bandwidth_mbps < 0:
            raise ValueError("network_bandwidth_mbps cannot be negative")
        if self.storage_gb < 0:
            raise ValueError("storage_gb cannot be negative")
    
    def can_fit_in(self, available: 'ResourceRequirements') -> bool:
        """Check if requirements can fit in available resources"""
        return (
            self.cpu_cores <= available.cpu_cores
            and self.memory_mb <= available.memory_mb
            and (not self.gpu_required or available.gpu_required)
            and self.network_bandwidth_mbps <= available.network_bandwidth_mbps
            and self.storage_gb <= available.storage_gb
        )
    
    def scale(self, factor: float) -> 'ResourceRequirements':
        """Scale requirements by a factor"""
        if factor <= 0:
            raise ValueError("factor must be positive")
        return ResourceRequirements(
            cpu_cores=self.cpu_cores * factor,
            memory_mb=int(self.memory_mb * factor),
            gpu_required=self.gpu_required,
            network_bandwidth_mbps=self.network_bandwidth_mbps * factor,
            storage_gb=self.storage_gb * factor
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "gpu_required": self.gpu_required,
            "network_bandwidth_mbps": self.network_bandwidth_mbps,
            "storage_gb": self.storage_gb
        }