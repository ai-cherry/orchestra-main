"""
Base manager for WIF implementation.

This module provides a base manager class for the WIF implementation.
All manager classes should inherit from this base class.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from ..error_handler import handle_exception, WIFError, ErrorSeverity
from ..types import ImplementationPlan, Task


class BaseManager:
    """
    Base manager for WIF implementation.
    
    This class provides common functionality for all manager classes.
    """
    
    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize the base manager.
        
        Args:
            base_path: The base path for the WIF implementation
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode
        """
        self.base_path = Path(base_path) if base_path else Path(".")
        self.verbose = verbose
        self.dry_run = dry_run
        self.logger = logging.getLogger(self.__class__.__module__)
        
        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        
        self.logger.debug(f"Initialized {self.__class__.__name__}")
    
    @handle_exception()
    def execute_task(self, task_name: str, plan: ImplementationPlan) -> bool:
        """
        Execute a task.
        
        This method should be overridden by subclasses to implement
        task execution logic.
        
        Args:
            task_name: The name of the task to execute
            plan: The implementation plan
            
        Returns:
            True if the task was executed successfully, False otherwise
            
        Raises:
            NotImplementedError: If the method is not overridden by a subclass
        """
        raise NotImplementedError("Subclasses must implement execute_task")
    
    def get_task_method_name(self, task_name: str) -> str:
        """
        Get the method name for a task.
        
        This method converts a task name to a method name by replacing
        underscores with camelCase.
        
        Args:
            task_name: The name of the task
            
        Returns:
            The method name for the task
        """
        parts = task_name.split("_")
        return parts[0] + "".join(part.capitalize() for part in parts[1:])
    
    def get_file_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Get the absolute path for a file.
        
        Args:
            relative_path: The relative path to the file
            
        Returns:
            The absolute path to the file
        """
        return self.base_path / relative_path
    
    def file_exists(self, relative_path: Union[str, Path]) -> bool:
        """
        Check if a file exists.
        
        Args:
            relative_path: The relative path to the file
            
        Returns:
            True if the file exists, False otherwise
        """
        return self.get_file_path(relative_path).exists()
    
    def read_file(self, relative_path: Union[str, Path]) -> str:
        """
        Read a file.
        
        Args:
            relative_path: The relative path to the file
            
        Returns:
            The contents of the file
            
        Raises:
            WIFError: If the file does not exist or cannot be read
        """
        file_path = self.get_file_path(relative_path)
        
        if not file_path.exists():
            raise WIFError(
                message=f"File not found: {file_path}",
                severity=ErrorSeverity.ERROR,
                details={"file_path": str(file_path)},
            )
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise WIFError(
                message=f"Error reading file: {file_path}",
                severity=ErrorSeverity.ERROR,
                details={"file_path": str(file_path), "error": str(e)},
                cause=e,
            )
    
    def write_file(self, relative_path: Union[str, Path], content: str) -> None:
        """
        Write a file.
        
        Args:
            relative_path: The relative path to the file
            content: The content to write to the file
            
        Raises:
            WIFError: If the file cannot be written
        """
        file_path = self.get_file_path(relative_path)
        
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would write to file: {file_path}")
            return
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.logger.debug(f"Wrote file: {file_path}")
        except Exception as e:
            raise WIFError(
                message=f"Error writing file: {file_path}",
                severity=ErrorSeverity.ERROR,
                details={"file_path": str(file_path), "error": str(e)},
                cause=e,
            )
    
    def execute_command(self, command: str) -> str:
        """
        Execute a command.
        
        Args:
            command: The command to execute
            
        Returns:
            The output of the command
            
        Raises:
            WIFError: If the command fails
        """
        import subprocess
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would execute command: {command}")
            return "[DRY RUN] Command output"
        
        try:
            self.logger.debug(f"Executing command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=self.base_path,
            )
            
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise WIFError(
                message=f"Command failed: {command}",
                severity=ErrorSeverity.ERROR,
                details={
                    "command": command,
                    "exit_code": e.returncode,
                    "stdout": e.stdout,
                    "stderr": e.stderr,
                },
                cause=e,
            )
        except Exception as e:
            raise WIFError(
                message=f"Error executing command: {command}",
                severity=ErrorSeverity.ERROR,
                details={"command": command, "error": str(e)},
                cause=e,
            )
    
    def log_task_start(self, task_name: str) -> None:
        """
        Log the start of a task.
        
        Args:
            task_name: The name of the task
        """
        self.logger.info(f"Starting task: {task_name}")
    
    def log_task_complete(self, task_name: str) -> None:
        """
        Log the completion of a task.
        
        Args:
            task_name: The name of the task
        """
        self.logger.info(f"Completed task: {task_name}")
    
    def log_task_failed(self, task_name: str, reason: str) -> None:
        """
        Log the failure of a task.
        
        Args:
            task_name: The name of the task
            reason: The reason for the failure
        """
        self.logger.error(f"Task failed: {task_name} - {reason}")