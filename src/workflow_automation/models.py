"""
Core data models for the Workflow Automation system.

This module defines the fundamental data structures used throughout the workflow automation system,
including workflow definitions, steps, triggers, and error handlers.
"""

from typing import Dict, List, Optional, Any, Union, Type
from enum import Enum, auto
from dataclasses import dataclass, field
import uuid
from datetime import datetime


class WorkflowStatus(str, Enum):
    """Status of a workflow instance."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Status of a workflow step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ErrorAction(str, Enum):
    """Action to take when an error occurs."""
    RETRY = "retry"
    SKIP = "skip"
    FAIL = "fail"
    ALTERNATE_PATH = "alternate_path"
    NOTIFY = "notify"


@dataclass
class WorkflowTrigger:
    """Defines how a workflow can be triggered."""
    
    type: str  # "api", "persona_request", "event", etc.
    configuration: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    enabled: bool = True


@dataclass
class ErrorHandler:
    """Handles errors that occur during workflow execution."""
    
    error_type: str
    action: ErrorAction
    parameters: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    
    id: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_config: Dict[str, Any] = field(default_factory=dict)
    error_handlers: List[ErrorHandler] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Represents a complete workflow definition."""
    
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    error_handlers: List[ErrorHandler] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: Optional[str] = None


@dataclass
class StepExecution:
    """Records the execution of a workflow step."""
    
    step_id: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    logs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowInstance:
    """Represents a running instance of a workflow."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    current_step_id: Optional[str] = None
    step_executions: Dict[str, StepExecution] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "current_step_id": self.current_step_id,
            "step_executions": {
                step_id: {
                    "status": step.status,
                    "start_time": step.start_time,
                    "end_time": step.end_time,
                    "input_data": step.input_data,
                    "output_data": step.output_data,
                    "error": step.error,
                    "retry_count": step.retry_count
                } for step_id, step in self.step_executions.items()
            },
            "variables": self.variables,
            "error": self.error,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowInstance':
        """Create an instance from a dictionary."""
        instance = cls(
            id=data.get("id", str(uuid.uuid4())),
            workflow_id=data.get("workflow_id", ""),
            status=data.get("status", WorkflowStatus.PENDING),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data", {}),
            current_step_id=data.get("current_step_id"),
            variables=data.get("variables", {}),
            error=data.get("error"),
            created_by=data.get("created_by")
        )
        
        # Reconstruct step executions
        step_executions = {}
        for step_id, step_data in data.get("step_executions", {}).items():
            step_executions[step_id] = StepExecution(
                step_id=step_id,
                status=step_data.get("status", StepStatus.PENDING),
                start_time=step_data.get("start_time"),
                end_time=step_data.get("end_time"),
                input_data=step_data.get("input_data", {}),
                output_data=step_data.get("output_data", {}),
                error=step_data.get("error"),
                retry_count=step_data.get("retry_count", 0),
                logs=step_data.get("logs", [])
            )
        
        instance.step_executions = step_executions
        return instance
