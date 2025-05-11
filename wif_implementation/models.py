"""
Core data models for the WIF implementation plan.

This module defines the data models used throughout the WIF implementation plan,
including phases, tasks, and vulnerabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Any


class ImplementationPhase(Enum):
    """Phases of the WIF implementation plan."""
    VULNERABILITIES = "vulnerabilities"
    MIGRATION = "migration"
    CICD = "cicd"
    TRAINING = "training"
    ALL = "all"


class TaskStatus(Enum):
    """Status of a task in the implementation plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Vulnerability:
    """Representation of a security vulnerability."""
    id: str
    package: str
    severity: str
    description: str
    current_version: str
    fixed_version: Optional[str] = None
    is_direct: bool = True
    is_fixed: bool = False
    fix_command: Optional[str] = None
    notes: str = ""


@dataclass
class Task:
    """A task in the implementation plan."""
    name: str
    description: str
    phase: ImplementationPhase
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    subtasks: List["Task"] = field(default_factory=list)
    notes: str = ""

    def start(self) -> None:
        """Mark the task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete(self) -> None:
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.end_time = datetime.now()

    def fail(self, reason: str) -> None:
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
        self.end_time = datetime.now()
        self.notes = reason

    def skip(self, reason: str) -> None:
        """Mark the task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.end_time = datetime.now()
        self.notes = reason

    def add_subtask(self, subtask: "Task") -> None:
        """Add a subtask to this task."""
        self.subtasks.append(subtask)

    def get_duration(self) -> Optional[float]:
        """Get the duration of the task in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class ImplementationPlan:
    """The overall WIF implementation plan."""
    tasks: Dict[str, Task] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_phase: Optional[ImplementationPhase] = None

    def add_task(self, task: Task) -> None:
        """Add a task to the implementation plan."""
        self.tasks[task.name] = task

    def get_tasks_by_phase(self, phase: ImplementationPhase) -> List[Task]:
        """Get all tasks for a specific phase."""
        return [task for task in self.tasks.values() if task.phase == phase]

    def get_task_by_name(self, name: str) -> Optional[Task]:
        """Get a task by its name."""
        return self.tasks.get(name)

    def start(self) -> None:
        """Start the implementation plan."""
        self.start_time = datetime.now()

    def complete(self) -> None:
        """Complete the implementation plan."""
        self.end_time = datetime.now()