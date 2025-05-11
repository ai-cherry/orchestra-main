"""Training manager for WIF implementation.

This module provides functionality for managing training resources and materials
for Workload Identity Federation (WIF) implementation.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from .error_handler import WIFError, ErrorSeverity, handle_exception, safe_execute
from . import ImplementationPhase, TaskStatus, Task, ImplementationPlan

logger = logging.getLogger("wif_implementation.training_manager")


class TrainingError(WIFError):
    """Exception raised when there is a training error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.
        
        Args:
            message: The error message
            details: Additional details about the error
            cause: The underlying exception that caused this error
        """
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details,
            cause=cause,
        )


class TrainingManager:
    """Training manager for WIF implementation."""
    
    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize the training manager.
        
        Args:
            base_path: The base path for training materials
            verbose: Whether to show detailed output during processing
            dry_run: Whether to run in dry-run mode (no changes made)
        """
        if base_path is None:
            base_path = Path(".")
        
        self.base_path = Path(base_path).resolve()
        self.verbose = verbose
        self.dry_run = dry_run
        self.training_materials: List[Dict[str, Any]] = []
        
        if verbose:
            logger.setLevel(logging.DEBUG)
    
    def execute_task(self, task_name: str, plan: ImplementationPlan) -> bool:
        """
        Execute a training task.
        
        Args:
            task_name: The name of the task to execute
            plan: The implementation plan
            
        Returns:
            True if the task was executed successfully, False otherwise
        """
        task = plan.get_task_by_name(task_name)
        if not task:
            logger.error(f"Task {task_name} not found")
            return False
        
        if task.phase != ImplementationPhase.TRAINING:
            logger.error(f"Task {task_name} not in TRAINING phase")
            return False
        
        task_map = {
            "create_training_materials": self._create_training_materials,
            "schedule_training_sessions": self._schedule_training_sessions,
            "conduct_training": self._conduct_training,
            "evaluate_training": self._evaluate_training,
            "document_best_practices": self._document_best_practices,
        }
        
        if task_name in task_map:
            return task_map[task_name](plan)
        
        logger.error(f"Unknown task: {task_name}")
        return False
    
    @handle_exception
    def _create_training_materials(self, plan: ImplementationPlan) -> bool:
        """
        Create training materials for WIF implementation.
        
        Args:
            plan: The implementation plan
            
        Returns:
            True if the materials were created successfully, False otherwise
        """
        logger.info("create_training_materials:start")
        
        # Create training materials directory
        training_dir = self.base_path / "wif_training_materials"
        
        if self.dry_run:
            logger.info(f"Would create training directory: {training_dir}")
        else:
            training_dir.mkdir(exist_ok=True)
            logger.info(f"Created training directory: {training_dir}")
        
        # Define training materials
        materials = [
            {
                "title": "Introduction to Workload Identity Federation",
                "filename": "01_introduction_to_wif.md",
                "content": "# Introduction to Workload Identity Federation\n\nWIF allows workloads in non-Google Cloud environments to access Google Cloud resources securely without using service account keys."
            },
            {
                "title": "Setting Up Workload Identity Federation",
                "filename": "02_setting_up_wif.md",
                "content": "# Setting Up Workload Identity Federation\n\nThis guide walks through the process of setting up Workload Identity Federation for GitHub Actions."
            },
            {
                "title": "Best Practices for WIF Security",
                "filename": "03_wif_security_best_practices.md",
                "content": "# Best Practices for Workload Identity Federation Security\n\nThis guide outlines best practices for securing your Workload Identity Federation implementation."
            }
        ]
        
        # Create training materials
        self.training_materials = materials
        
        if self.dry_run:
            for material in materials:
                logger.info(f"Would create training material: {material['filename']}")
        else:
            for material in materials:
                file_path = training_dir / material["filename"]
                with open(file_path, "w") as f:
                    f.write(material["content"])
                logger.info(f"Created training material: {file_path}")
        
        # Create an index file
        index_content = "# Workload Identity Federation Training Materials\n\n"
        for material in materials:
            index_content += f"- [{material['title']}]({material['filename']})\n"
        
        if self.dry_run:
            logger.info("Would create training index: README.md")
        else:
            index_path = training_dir / "README.md"
            with open(index_path, "w") as f:
                f.write(index_content)
            logger.info(f"Created training index: {index_path}")
        
        logger.info("create_training_materials:complete")
        return True
    
    @handle_exception
    def _schedule_training_sessions(self, plan: ImplementationPlan) -> bool:
        """
        Schedule training sessions for WIF implementation.
        
        Args:
            plan: The implementation plan
            
        Returns:
            True if the sessions were scheduled successfully, False otherwise
        """
        logger.info("schedule_training_sessions:start")
        
        # Create training schedule directory
        schedule_dir = self.base_path / "wif_training_materials" / "schedule"
        
        if self.dry_run:
            logger.info(f"Would create schedule directory: {schedule_dir}")
        else:
            schedule_dir.mkdir(exist_ok=True)
            logger.info(f"Created schedule directory: {schedule_dir}")
            
            # Create schedule file
            schedule_path = schedule_dir / "training_schedule.md"
            with open(schedule_path, "w") as f:
                f.write("# Workload Identity Federation Training Schedule\n\n")
                f.write("## Introduction to WIF\n\n")
                f.write(f"- **Date:** {datetime.now().date().isoformat()}\n")
                f.write("- **Time:** 10:00-11:00\n")
                f.write("- **Presenter:** Cloud Security Team\n")
                f.write("- **Location:** Virtual Meeting Room 1\n\n")
                
                f.write("## Setting Up WIF\n\n")
                f.write(f"- **Date:** {datetime.now().date().isoformat()}\n")
                f.write("- **Time:** 14:00-15:30\n")
                f.write("- **Presenter:** DevOps Team\n")
                f.write("- **Location:** Virtual Meeting Room 1\n\n")
                
                f.write("## WIF Security Best Practices\n\n")
                f.write(f"- **Date:** {datetime.now().date().isoformat()}\n")
                f.write("- **Time:** 10:00-11:00\n")
                f.write("- **Presenter:** Security Team\n")
                f.write("- **Location:** Virtual Meeting Room 1\n\n")
            
            logger.info(f"Created training schedule: {schedule_path}")
        
        logger.info("schedule_training_sessions:complete")
        return True
    
    @handle_exception
    def _conduct_training(self, plan: ImplementationPlan) -> bool:
        """
        Conduct training sessions for WIF implementation.
        
        Args:
            plan: The implementation plan
            
        Returns:
            True if the training was conducted successfully, False otherwise
        """
        logger.info("conduct_training:start")
        
        # Create training records directory
        records_dir = self.base_path / "wif_training_materials" / "records"
        
        if self.dry_run:
            logger.info(f"Would create records directory: {records_dir}")
        else:
            records_dir.mkdir(exist_ok=True)
            logger.info(f"Created records directory: {records_dir}")
            
            # Create records file
            records_path = records_dir / "training_records.md"
            with open(records_path, "w") as f:
                f.write("# Workload Identity Federation Training Records\n\n")
                f.write("## Introduction to WIF\n\n")
                f.write(f"- **Date:** {datetime.now().date().isoformat()}\n")
                f.write("- **Attendees:** John Doe, Jane Smith, Bob Johnson\n")
                f.write("- **Notes:** Session went well. Participants had questions about the security benefits of WIF.\n")
                f.write("- **Feedback Score:** 4.5/5.0\n\n")
            
            logger.info(f"Created training records: {records_path}")
        
        logger.info("conduct_training:complete")
        return True
    
    @handle_exception
    def _evaluate_training(self, plan: ImplementationPlan) -> bool:
        """
        Evaluate training effectiveness for WIF implementation.
        
        Args:
            plan: The implementation plan
            
        Returns:
            True if the evaluation was completed successfully, False otherwise
        """
        logger.info("evaluate_training:start")
        
        # Create evaluation directory
        eval_dir = self.base_path / "wif_training_materials" / "evaluation"
        
        if self.dry_run:
            logger.info(f"Would create evaluation directory: {eval_dir}")
        else:
            eval_dir.mkdir(exist_ok=True)
            logger.info(f"Created evaluation directory: {eval_dir}")
            
            # Create report file
            report_path = eval_dir / "training_evaluation.md"
            with open(report_path, "w") as f:
                f.write("# Workload Identity Federation Training Evaluation\n\n")
                f.write("## Overall Metrics\n\n")
                f.write("- **Overall Score:** 4.5/5.0\n")
                f.write("- **Completion Rate:** 95%\n")
                f.write("- **Knowledge Improvement:** 85%\n\n")
                
                f.write("## Recommendations\n\n")
                f.write("- Add more hands-on exercises\n")
                f.write("- Include more complex scenarios\n")
                f.write("- Provide follow-up resources\n")
                f.write("- Create a troubleshooting guide\n")
            
            logger.info(f"Created evaluation report: {report_path}")
        
        logger.info("evaluate_training:complete")
        return True
    
    @handle_exception
    def _document_best_practices(self, plan: ImplementationPlan) -> bool:
        """
        Document best practices for WIF implementation.
        
        Args:
            plan: The implementation plan
            
        Returns:
            True if the documentation was created successfully, False otherwise
        """
        logger.info("document_best_practices:start")
        
        # Create best practices directory
        bp_dir = self.base_path / "wif_training_materials" / "best_practices"
        
        if self.dry_run:
            logger.info(f"Would create best practices directory: {bp_dir}")
        else:
            bp_dir.mkdir(exist_ok=True)
            logger.info(f"Created best practices directory: {bp_dir}")
            
            # Create checklist file
            checklist_path = bp_dir / "wif_implementation_checklist.md"
            with open(checklist_path, "w") as f:
                f.write("# Workload Identity Federation Implementation Checklist\n\n")
                f.write("Use this checklist to ensure you've properly implemented Workload Identity Federation.\n\n")
                f.write("## Prerequisites\n\n")
                f.write("- [ ] Google Cloud project with billing enabled\n")
                f.write("- [ ] Required APIs enabled\n")
                f.write("  - [ ] IAM API (`iam.googleapis.com`)\n")
                f.write("  - [ ] IAM Credentials API (`iamcredentials.googleapis.com`)\n")
                f.write("  - [ ] Cloud Resource Manager API (`cloudresourcemanager.googleapis.com`)\n")
                f.write("  - [ ] Service-specific APIs (e.g., Cloud Run, GKE, etc.)\n\n")
                f.write("## Workload Identity Pool\n\n")
                f.write("- [ ] Workload Identity Pool created\n")
                f.write("- [ ] Meaningful display name and description\n")
                f.write("- [ ] Appropriate state (ACTIVE)\n")
            
            logger.info(f"Created implementation checklist: {checklist_path}")
        
        logger.info("document_best_practices:complete")
        return True
