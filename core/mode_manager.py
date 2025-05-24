#!/usr/bin/env python3
"""
Mode Manager for AI Orchestra

This module provides a comprehensive mode management system for AI Orchestra,
enabling the use of different AI models for specific tasks and managing workflows
that transition between modes. It supports:

1. Loading configurations from YAML
2. Switching between modes with context preservation
3. Running predefined workflow sequences
4. Suggesting next modes based on current state
5. Enforcing file access permissions

The system optimizes model usage by assigning:
- Gemini 2.5 Pro: architect, orchestrator, and reviewer modes
- GPT-4.1: code and debug modes
- Claude 3.7: strategy, ask, and creative modes
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = PROJECT_ROOT / "config"
MODE_CONFIG_PATH = CONFIG_DIR / "mode_definitions.yaml"
WORKFLOW_STATE_PATH = CONFIG_DIR / "workflow_state.yaml"


class FileAccessError(Exception):
    """Exception raised when a mode attempts to access a restricted file."""


class WorkflowError(Exception):
    """Exception raised for workflow-related errors."""


@dataclass
class Mode:
    """
    Represents an operation mode with specific AI model and capabilities.

    Each mode represents a specialized role with access to specific file patterns
    and a designated AI model optimized for its tasks.
    """

    slug: str
    name: str
    model: str
    description: str
    write_access: bool = False
    file_patterns: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    token_limit: int = 32000
    suggested_transitions: List[str] = field(default_factory=list)

    def can_write_file(self, file_path: str) -> bool:
        """
        Check if this mode can write to the specified file path.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the mode has write access to this file, False otherwise
        """
        if not self.write_access:
            return False

        # If no specific patterns are defined but write_access is True,
        # allow all files
        if not self.file_patterns:
            return True

        # Check if the file matches any of the allowed patterns
        for pattern in self.file_patterns:
            if re.match(pattern, file_path):
                return True

        return False


@dataclass
class WorkflowStep:
    """
    A single step in a workflow sequence.

    Each step specifies a mode to use and a task to perform.
    """

    mode: str
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False


@dataclass
class Workflow:
    """
    A sequence of mode transitions for a specific development task.

    Workflows define predefined sequences of mode transitions for common
    development tasks like feature development, bug fixes, etc.
    """

    slug: str
    name: str
    description: str
    steps: List[WorkflowStep]
    current_step: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    global_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def completed(self) -> bool:
        """Check if all steps in the workflow are completed."""
        return self.current_step >= len(self.steps) or all(step.completed for step in self.steps)


class ModeManager:
    """
    Manages modes, workflows, and transitions between modes.

    This class is responsible for:
    1. Loading mode and workflow configurations
    2. Switching between modes
    3. Managing workflow execution
    4. Suggesting next modes based on current context
    5. Validating file access permissions
    """

    _instance: ClassVar[Optional["ModeManager"]] = None

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the mode manager.

        Args:
            config_path: Path to the configuration file (optional)
        """
        self.modes: Dict[str, Mode] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.current_mode: Optional[Mode] = None
        self.current_workflow: Optional[Workflow] = None
        self.history: List[str] = []
        self.context: Dict[str, Any] = {}

        # Load configuration
        config_path = config_path or MODE_CONFIG_PATH
        self.load_configuration(config_path)

    def load_configuration(self, config_path: Union[str, Path]) -> bool:
        """
        Load mode and workflow configuration from YAML file.

        Args:
            config_path: Path to the configuration file

        Returns:
            True if configuration was successfully loaded, False otherwise
        """
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Clear existing configuration
            self.modes = {}
            self.workflows = {}

            # Load modes
            for slug, mode_config in config.get("modes", {}).items():
                self.modes[slug] = Mode(
                    slug=slug,
                    name=mode_config.get("name", slug),
                    model=mode_config.get("model", "default"),
                    description=mode_config.get("description", ""),
                    write_access=mode_config.get("write_access", False),
                    file_patterns=mode_config.get("file_patterns", []),
                    capabilities=mode_config.get("capabilities", []),
                    token_limit=mode_config.get("token_limit", 32000),
                    suggested_transitions=mode_config.get("suggested_transitions", []),
                )

            # Load workflows
            for slug, workflow_config in config.get("workflows", {}).items():
                steps = []
                for step_config in workflow_config.get("steps", []):
                    steps.append(
                        WorkflowStep(
                            mode=step_config.get("mode", ""),
                            task=step_config.get("task", ""),
                        )
                    )

                self.workflows[slug] = Workflow(
                    slug=slug,
                    name=workflow_config.get("name", slug),
                    description=workflow_config.get("description", ""),
                    steps=steps,
                )

            logger.info(f"Loaded {len(self.modes)} modes and {len(self.workflows)} workflows")
            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def switch_mode(self, mode_slug: str) -> Tuple[bool, str]:
        """
        Switch to a different mode.

        Args:
            mode_slug: Slug of the mode to switch to

        Returns:
            Tuple of (success, message)
        """
        if mode_slug not in self.modes:
            return False, f"Mode '{mode_slug}' not found"

        # Save current mode to history
        if self.current_mode:
            self.history.append(self.current_mode.slug)

        # Set new mode
        self.current_mode = self.modes[mode_slug]
        logger.info(f"Switched to mode: {self.current_mode.name}")

        return True, f"Switched to {self.current_mode.name} mode"

    def can_write_file(self, file_path: str) -> bool:
        """
        Check if the current mode can write to the specified file path.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the current mode has write access to this file, False otherwise
        """
        if not self.current_mode:
            return False

        return self.current_mode.can_write_file(file_path)

    def validate_file_access(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if the current mode can write to the specified file path.

        Args:
            file_path: Path to the file to check

        Returns:
            Tuple of (success, message)
        """
        if not self.current_mode:
            return False, "No active mode selected"

        if not self.current_mode.write_access:
            return False, f"Mode '{self.current_mode.slug}' does not have write access"

        if not self.can_write_file(file_path):
            allowed_patterns = self.current_mode.file_patterns
            patterns_str = ", ".join(f"'{p}'" for p in allowed_patterns)
            return False, (
                f"Mode '{self.current_mode.slug}' cannot write to '{file_path}'. " f"Allowed patterns: {patterns_str}"
            )

        return True, "File access allowed"

    def start_workflow(self, workflow_slug: str) -> Tuple[bool, str]:
        """
        Start a workflow sequence.

        Args:
            workflow_slug: Slug of the workflow to start

        Returns:
            Tuple of (success, message)
        """
        if workflow_slug not in self.workflows:
            return False, f"Workflow '{workflow_slug}' not found"

        # Initialize workflow
        self.current_workflow = self.workflows[workflow_slug]
        self.current_workflow.start_time = datetime.now()
        self.current_workflow.current_step = 0
        self.current_workflow.global_context = {}

        # Reset step completion status
        for step in self.current_workflow.steps:
            step.completed = False
            step.context = {}

        # Switch to the first mode
        if self.current_workflow.steps:
            first_step = self.current_workflow.steps[0]
            success, message = self.switch_mode(first_step.mode)
            if not success:
                return False, f"Failed to start workflow: {message}"

        logger.info(f"Started workflow: {self.current_workflow.name}")
        return True, f"Started workflow: {self.current_workflow.name}"

    def advance_workflow(self) -> Tuple[bool, str]:
        """
        Advance to the next step in the current workflow.

        Returns:
            Tuple of (success, message)
        """
        if not self.current_workflow:
            return False, "No active workflow"

        # Mark current step as completed
        if 0 <= self.current_workflow.current_step < len(self.current_workflow.steps):
            self.current_workflow.steps[self.current_workflow.current_step].completed = True

        # Advance to next step
        self.current_workflow.current_step += 1

        # Check if workflow is completed
        if self.current_workflow.current_step >= len(self.current_workflow.steps):
            self.current_workflow.end_time = datetime.now()
            return True, f"Workflow '{self.current_workflow.name}' completed"

        # Switch to the next mode
        next_step = self.current_workflow.steps[self.current_workflow.current_step]
        success, message = self.switch_mode(next_step.mode)
        if not success:
            return False, f"Failed to advance workflow: {message}"

        logger.info(f"Advanced to step {self.current_workflow.current_step + 1}: {next_step.task}")
        return (
            True,
            f"Advanced to step {self.current_workflow.current_step + 1}: {next_step.task}",
        )

    def suggest_next_modes(self, limit: int = 3) -> List[Dict[str, str]]:
        """
        Suggest next modes based on current context and configuration.

        Args:
            limit: Maximum number of suggestions to return

        Returns:
            List of suggested modes with reasons
        """
        suggestions = []

        if not self.current_mode:
            # No current mode, suggest popular starting modes
            starter_modes = ["code", "ask", "strategy"]
            for slug in starter_modes:
                if slug in self.modes:
                    mode = self.modes[slug]
                    suggestions.append(
                        {
                            "slug": slug,
                            "name": mode.name,
                            "reason": f"Good starting point for {mode.description.lower()}",
                        }
                    )
        else:
            # Suggest transitions from current mode
            for transition in self.current_mode.suggested_transitions:
                # Parse mode and reason
                parts = transition.split(" (", 1)
                slug = parts[0].strip()
                reason = parts[1][:-1] if len(parts) > 1 else "Suggested transition"

                if slug in self.modes:
                    mode = self.modes[slug]
                    suggestions.append({"slug": slug, "name": mode.name, "reason": reason})

            # Add recently used modes
            for slug in reversed(self.history[-5:]):
                if (
                    slug in self.modes
                    and slug != self.current_mode.slug
                    and not any(s["slug"] == slug for s in suggestions)
                ):
                    mode = self.modes[slug]
                    suggestions.append({"slug": slug, "name": mode.name, "reason": "Recently used"})

        # Limit suggestions
        return suggestions[:limit]

    def get_model_for_current_mode(self) -> str:
        """
        Get the AI model assigned to the current mode.

        Returns:
            Model identifier for the current mode
        """
        if not self.current_mode:
            return "default"

        return self.current_mode.model

    def save_workflow_state(self) -> bool:
        """
        Save current workflow state to a file.

        Returns:
            True if state was successfully saved, False otherwise
        """
        if not self.current_workflow:
            return False

        try:
            # Convert workflow to serializable dict
            state = {
                "workflow": self.current_workflow.slug,
                "current_step": self.current_workflow.current_step,
                "start_time": (
                    self.current_workflow.start_time.isoformat() if self.current_workflow.start_time else None
                ),
                "end_time": self.current_workflow.end_time.isoformat() if self.current_workflow.end_time else None,
                "global_context": self.current_workflow.global_context,
                "steps": [],
            }

            for step in self.current_workflow.steps:
                step_dict = {
                    "mode": step.mode,
                    "task": step.task,
                    "context": step.context,
                    "completed": step.completed,
                }
                state["steps"].append(step_dict)

            # Save state to file
            os.makedirs(os.path.dirname(WORKFLOW_STATE_PATH), exist_ok=True)
            with open(WORKFLOW_STATE_PATH, "w") as f:
                yaml.dump(state, f)

            logger.info(f"Saved workflow state to {WORKFLOW_STATE_PATH}")
            return True

        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False

    def load_workflow_state(self) -> bool:
        """
        Load workflow state from file.

        Returns:
            True if state was successfully loaded, False otherwise
        """
        if not os.path.exists(WORKFLOW_STATE_PATH):
            return False

        try:
            with open(WORKFLOW_STATE_PATH, "r") as f:
                state = yaml.safe_load(f)

            workflow_slug = state.get("workflow")
            if workflow_slug not in self.workflows:
                logger.error(f"Workflow '{workflow_slug}' not found")
                return False

            # Load workflow
            self.current_workflow = self.workflows[workflow_slug]
            self.current_workflow.current_step = state.get("current_step", 0)
            self.current_workflow.global_context = state.get("global_context", {})

            # Parse dates
            if state.get("start_time"):
                self.current_workflow.start_time = datetime.fromisoformat(state["start_time"])
            if state.get("end_time"):
                self.current_workflow.end_time = datetime.fromisoformat(state["end_time"])

            # Load steps
            for i, step_dict in enumerate(state.get("steps", [])):
                if i < len(self.current_workflow.steps):
                    self.current_workflow.steps[i].context = step_dict.get("context", {})
                    self.current_workflow.steps[i].completed = step_dict.get("completed", False)

            # Switch to current mode
            if 0 <= self.current_workflow.current_step < len(self.current_workflow.steps):
                current_step = self.current_workflow.steps[self.current_workflow.current_step]
                self.switch_mode(current_step.mode)

            logger.info(f"Loaded workflow state from {WORKFLOW_STATE_PATH}")
            return True

        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return False


# Singleton instance
_instance = None


def get_mode_manager() -> ModeManager:
    """Get singleton instance of ModeManager."""
    global _instance
    if _instance is None:
        _instance = ModeManager()
    return _instance


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Mode Manager CLI")
    parser.add_argument("--switch", help="Switch to mode")
    parser.add_argument("--workflow", help="Start workflow")
    parser.add_argument("--suggest", action="store_true", help="Get mode suggestions")
    parser.add_argument("--check-file", help="Check if current mode can write to file")

    args = parser.parse_args()

    manager = get_mode_manager()

    if args.switch:
        success, message = manager.switch_mode(args.switch)
        print(message)

    elif args.workflow:
        success, message = manager.start_workflow(args.workflow)
        print(message)

    elif args.suggest:
        suggestions = manager.suggest_next_modes()
        print("Suggested next modes:")
        for i, suggestion in enumerate(suggestions):
            print(f"{i+1}. {suggestion['name']} ({suggestion['slug']}): {suggestion['reason']}")

    elif args.check_file:
        success, message = manager.validate_file_access(args.check_file)
        print(message)

    else:
        if manager.current_mode:
            print(f"Current mode: {manager.current_mode.name} ({manager.current_mode.slug})")
            print(f"Model: {manager.current_mode.model}")
            if manager.current_mode.write_access:
                print("Write access: Yes")
                if manager.current_mode.file_patterns:
                    print(f"File patterns: {', '.join(manager.current_mode.file_patterns)}")
            else:
                print("Write access: No")
        else:
            print("No active mode")
