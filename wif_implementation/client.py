"""
WIF Client for AI Orchestra.

This module provides a client for interacting with the WIF implementation.
It serves as the main entry point for WIF operations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .error_handler import WIFError, ErrorSeverity, handle_exception
from .config import WIFConfig
from . import ImplementationPhase, TaskStatus, Task, ImplementationPlan

logger = logging.getLogger("wif_implementation.client")


class WIFClient:
    """
    Client for interacting with the WIF implementation.
    
    This class provides a high-level interface for working with the
    WIF implementation components. It serves as the main entry point
    for WIF operations and manages the execution of tasks in the
    implementation plan.
    """
    
    def __init__(
        self,
        config: Optional[WIFConfig] = None,
        base_path: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize the WIF client.
        
        Args:
            config: The WIF configuration
            base_path: The base path for the WIF implementation
            verbose: Whether to enable verbose logging
            dry_run: Whether to run in dry-run mode
        """
        self.config = config or WIFConfig()
        self.base_path = Path(base_path) if base_path else Path(".")
        self.verbose = verbose
        self.dry_run = dry_run
        
        # Initialize managers
        # Import here to avoid circular imports
        from .managers.vulnerability_manager import VulnerabilityManager
        from .managers.cicd_manager import CICDManager
        from .managers.migration_manager import MigrationManager
        
        self.vulnerability_manager = VulnerabilityManager(
            base_path=self.base_path,
            verbose=self.verbose,
            dry_run=self.dry_run,
        )
        
        self.cicd_manager = CICDManager(
            base_path=self.base_path,
            verbose=self.verbose,
            dry_run=self.dry_run,
        )
        
        self.migration_manager = MigrationManager(
            base_path=self.base_path,
            verbose=self.verbose,
            dry_run=self.dry_run,
        )
        
        # Create implementation plan
        self.plan = ImplementationPlan()
        self._initialize_plan()
        
        if self.verbose:
            logger.setLevel(logging.DEBUG)
    
    def _initialize_plan(self) -> None:
        """Initialize the implementation plan with tasks."""
        # Vulnerability tasks
        self.plan.add_task(Task(
            name="inventory_vulnerabilities",
            description="Inventory vulnerabilities in the project",
            phase=ImplementationPhase.VULNERABILITIES,
        ))
        
        self.plan.add_task(Task(
            name="prioritize_vulnerabilities",
            description="Prioritize vulnerabilities by severity and impact",
            phase=ImplementationPhase.VULNERABILITIES,
            dependencies=["inventory_vulnerabilities"],
        ))
        
        self.plan.add_task(Task(
            name="update_direct_dependencies",
            description="Update direct dependencies with vulnerabilities",
            phase=ImplementationPhase.VULNERABILITIES,
            dependencies=["prioritize_vulnerabilities"],
        ))
        
        self.plan.add_task(Task(
            name="address_transitive_dependencies",
            description="Address transitive dependencies with vulnerabilities",
            phase=ImplementationPhase.VULNERABILITIES,
            dependencies=["update_direct_dependencies"],
        ))
        
        # CICD tasks
        self.plan.add_task(Task(
            name="identify_pipelines",
            description="Identify CI/CD pipelines in the project",
            phase=ImplementationPhase.CICD,
        ))
        
        self.plan.add_task(Task(
            name="analyze_auth_methods",
            description="Analyze authentication methods used in pipelines",
            phase=ImplementationPhase.CICD,
            dependencies=["identify_pipelines"],
        ))
        
        self.plan.add_task(Task(
            name="create_templates",
            description="Create templates for WIF-enabled pipelines",
            phase=ImplementationPhase.CICD,
            dependencies=["analyze_auth_methods"],
        ))
        
        self.plan.add_task(Task(
            name="update_pipelines",
            description="Update pipelines to use WIF",
            phase=ImplementationPhase.CICD,
            dependencies=["create_templates"],
        ))
        
        # Migration tasks
        self.plan.add_task(Task(
            name="prepare_migration",
            description="Prepare for migration to Workload Identity Federation",
            phase=ImplementationPhase.MIGRATION,
        ))
        
        self.plan.add_task(Task(
            name="create_wif_pool",
            description="Create Workload Identity Federation pool",
            phase=ImplementationPhase.MIGRATION,
            dependencies=["prepare_migration"],
        ))
        
        self.plan.add_task(Task(
            name="create_service_account",
            description="Create service account for WIF",
            phase=ImplementationPhase.MIGRATION,
            dependencies=["create_wif_pool"],
        ))
        
        self.plan.add_task(Task(
            name="configure_github_secrets",
            description="Configure GitHub secrets for WIF",
            phase=ImplementationPhase.MIGRATION,
            dependencies=["create_service_account"],
        ))
    
    @handle_exception(logger=logger)
    def execute_task(self, task_name: str) -> bool:
        """
        Execute a task in the implementation plan.
        
        Args:
            task_name: The name of the task to execute
            
        Returns:
            True if the task was executed successfully, False otherwise
        """
        task = self.plan.get_task_by_name(task_name)
        if not task:
            logger.error(f"Task not found: {task_name}")
            return False
        
        # Check dependencies
        for dependency in task.dependencies:
            dependency_task = self.plan.get_task_by_name(dependency)
            if not dependency_task or dependency_task.status != TaskStatus.COMPLETED:
                logger.error(f"Dependency not satisfied: {dependency}")
                return False
        
        # Start the task
        task.start()
        logger.info(f"Executing task: {task_name}")
        
        # Execute the task based on its phase
        success = False
        try:
            if task.phase == ImplementationPhase.VULNERABILITIES:
                success = self.vulnerability_manager.execute_task(task_name, self.plan)
            elif task.phase == ImplementationPhase.CICD:
                success = self.cicd_manager.execute_task(task_name, self.plan)
            elif task.phase == ImplementationPhase.MIGRATION:
                success = self.migration_manager.execute_task(task_name, self.plan)
            else:
                logger.error(f"Unsupported phase: {task.phase}")
                task.fail(f"Unsupported phase: {task.phase}")
                return False
            
            if success:
                task.complete()
                logger.info(f"Task completed successfully: {task_name}")
            else:
                task.fail("Task execution failed")
                logger.error(f"Task execution failed: {task_name}")
            
            return success
        except Exception as e:
            task.fail(str(e))
            logger.exception(f"Error executing task: {task_name}")
            return False
    
    def get_plan_status(self) -> Dict[str, Any]:
        """
        Get the status of the implementation plan.
        
        Returns:
            A dictionary with the plan status
        """
        tasks_by_phase = {}
        for phase in ImplementationPhase:
            tasks = self.plan.get_tasks_by_phase(phase)
            tasks_by_phase[phase.value] = {
                "total": len(tasks),
                "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
                "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
                "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
                "skipped": sum(1 for t in tasks if t.status == TaskStatus.SKIPPED),
            }
        
        return {
            "phases": tasks_by_phase,
            "total_tasks": len(self.plan.tasks),
            "completed_tasks": sum(1 for t in self.plan.tasks.values() if t.status == TaskStatus.COMPLETED),
            "start_time": self.plan.start_time.isoformat() if self.plan.start_time else None,
            "end_time": self.plan.end_time.isoformat() if self.plan.end_time else None,
        }
    
    def start_plan(self) -> None:
        """Start the implementation plan."""
        self.plan.start()
        logger.info("Implementation plan started")
    
    def complete_plan(self) -> None:
        """Complete the implementation plan."""
        self.plan.complete()
        logger.info("Implementation plan completed")
    
    def get_vulnerabilities(self) -> List[Any]:
        """
        Get the vulnerabilities found in the project.
        
        Returns:
            A list of vulnerabilities
        """
        return self.vulnerability_manager.vulnerabilities
    
    def get_pipelines(self) -> List[Dict[str, Any]]:
        """
        Get the CI/CD pipelines found in the project.
        
        Returns:
            A list of pipelines
        """
        return self.cicd_manager.pipelines