"""
Type definitions for WIF implementation.

This module provides type definitions and data models for the WIF implementation.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from pydantic import BaseModel, Field


class ImplementationPhase(Enum):
    """Implementation phases for the WIF implementation plan."""
    VULNERABILITIES = "vulnerabilities"
    MIGRATION = "migration"
    CICD = "cicd"
    TRAINING = "training"


class TaskStatus(Enum):
    """Task status for the WIF implementation plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task:
    """
    Task in the implementation plan.
    
    This class represents a task in the implementation plan.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        phase: ImplementationPhase,
        status: TaskStatus = TaskStatus.PENDING,
        dependencies: Optional[List[str]] = None,
        notes: str = "",
    ):
        """
        Initialize the task.
        
        Args:
            name: The name of the task
            description: The description of the task
            phase: The phase of the task
            status: The status of the task
            dependencies: The dependencies of the task
            notes: Additional notes about the task
        """
        self.name = name
        self.description = description
        self.phase = phase
        self.status = status
        self.dependencies = dependencies or []
        self.notes = notes
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def start(self) -> None:
        """Start the task."""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = datetime.now()
    
    def complete(self) -> None:
        """Complete the task."""
        self.status = TaskStatus.COMPLETED
        self.end_time = datetime.now()
    
    def fail(self, reason: str) -> None:
        """
        Fail the task.
        
        Args:
            reason: The reason for the failure
        """
        self.status = TaskStatus.FAILED
        self.end_time = datetime.now()
        self.notes = f"{self.notes}\nFailed: {reason}"
    
    def skip(self, reason: str) -> None:
        """
        Skip the task.
        
        Args:
            reason: The reason for skipping
        """
        self.status = TaskStatus.SKIPPED
        self.end_time = datetime.now()
        self.notes = f"{self.notes}\nSkipped: {reason}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.
        
        Returns:
            A dictionary representation of the task
        """
        return {
            "name": self.name,
            "description": self.description,
            "phase": self.phase.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "notes": self.notes,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class ImplementationPlan:
    """
    Implementation plan for the WIF implementation.
    
    This class represents the implementation plan for the WIF implementation.
    """
    
    def __init__(self):
        """Initialize the implementation plan."""
        self.tasks: Dict[str, Task] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.current_phase: Optional[ImplementationPhase] = None
    
    def add_task(self, task: Task) -> None:
        """
        Add a task to the implementation plan.
        
        Args:
            task: The task to add
        """
        self.tasks[task.name] = task
    
    def get_task_by_name(self, name: str) -> Optional[Task]:
        """
        Get a task by name.
        
        Args:
            name: The name of the task to get
            
        Returns:
            The task, or None if not found
        """
        return self.tasks.get(name)
    
    def get_tasks_by_phase(self, phase: ImplementationPhase) -> List[Task]:
        """
        Get tasks by phase.
        
        Args:
            phase: The phase to get tasks for
            
        Returns:
            A list of tasks for the phase
        """
        return [task for task in self.tasks.values() if task.phase == phase]
    
    def start(self) -> None:
        """Start the implementation plan."""
        self.start_time = datetime.now()
    
    def complete(self) -> None:
        """Complete the implementation plan."""
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the implementation plan to a dictionary.
        
        Returns:
            A dictionary representation of the implementation plan
        """
        return {
            "tasks": {name: task.to_dict() for name, task in self.tasks.items()},
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_phase": self.current_phase.value if self.current_phase else None,
        }


class Vulnerability:
    """
    Vulnerability in the implementation plan.
    
    This class represents a vulnerability in the implementation plan.
    """
    
    def __init__(
        self,
        id: str,
        package: str,
        severity: str,
        description: str,
        current_version: str,
        fixed_version: Optional[str] = None,
        is_direct: bool = True,
        is_fixed: bool = False,
        fix_command: Optional[str] = None,
        notes: str = "",
    ):
        """
        Initialize the vulnerability.
        
        Args:
            id: The ID of the vulnerability
            package: The package with the vulnerability
            severity: The severity of the vulnerability
            description: The description of the vulnerability
            current_version: The current version of the package
            fixed_version: The fixed version of the package
            is_direct: Whether the package is a direct dependency
            is_fixed: Whether the vulnerability is fixed
            fix_command: The command to fix the vulnerability
            notes: Additional notes about the vulnerability
        """
        self.id = id
        self.package = package
        self.severity = severity
        self.description = description
        self.current_version = current_version
        self.fixed_version = fixed_version
        self.is_direct = is_direct
        self.is_fixed = is_fixed
        self.fix_command = fix_command
        self.notes = notes
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the vulnerability to a dictionary.
        
        Returns:
            A dictionary representation of the vulnerability
        """
        return {
            "id": self.id,
            "package": self.package,
            "severity": self.severity,
            "description": self.description,
            "current_version": self.current_version,
            "fixed_version": self.fixed_version,
            "is_direct": self.is_direct,
            "is_fixed": self.is_fixed,
            "fix_command": self.fix_command,
            "notes": self.notes,
        }


class VulnerabilityModel(BaseModel):
    """Pydantic model for vulnerability."""
    
    id: str = Field(..., description="The ID of the vulnerability")
    package: str = Field(..., description="The package with the vulnerability")
    severity: str = Field(..., description="The severity of the vulnerability")
    description: str = Field(..., description="The description of the vulnerability")
    current_version: str = Field(..., description="The current version of the package")
    fixed_version: Optional[str] = Field(None, description="The fixed version of the package")
    is_direct: bool = Field(True, description="Whether the package is a direct dependency")
    is_fixed: bool = Field(False, description="Whether the vulnerability is fixed")
    fix_command: Optional[str] = Field(None, description="The command to fix the vulnerability")
    notes: str = Field("", description="Additional notes about the vulnerability")


class TaskModel(BaseModel):
    """Pydantic model for task."""
    
    name: str = Field(..., description="The name of the task")
    description: str = Field(..., description="The description of the task")
    phase: str = Field(..., description="The phase of the task")
    status: str = Field("pending", description="The status of the task")
    dependencies: List[str] = Field(default_factory=list, description="The dependencies of the task")
    notes: str = Field("", description="Additional notes about the task")
    start_time: Optional[str] = Field(None, description="The start time of the task")
    end_time: Optional[str] = Field(None, description="The end time of the task")


class ImplementationPlanModel(BaseModel):
    """Pydantic model for implementation plan."""
    
    tasks: Dict[str, TaskModel] = Field(default_factory=dict, description="The tasks in the implementation plan")
    start_time: Optional[str] = Field(None, description="The start time of the implementation plan")
    end_time: Optional[str] = Field(None, description="The end time of the implementation plan")
    current_phase: Optional[str] = Field(None, description="The current phase of the implementation plan")