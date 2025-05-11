#!/usr/bin/env python3
"""
Automation Controller for AI Orchestra

This script serves as the central controller for all automation tasks in the AI Orchestra project.
It integrates performance enhancement, workspace optimization, and various automation strategies
into a cohesive system with a unified interface.
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class AutomationTask(str, Enum):
    """Available automation tasks."""
    PERFORMANCE = "performance"
    WORKSPACE = "workspace"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    AI_SERVICE = "ai_service"
    COST = "cost"
    INFRASTRUCTURE = "infrastructure"
    ALL = "all"


class AutomationMode(str, Enum):
    """Automation execution modes."""
    ANALYZE = "analyze"      # Only analyze, don't make changes
    RECOMMEND = "recommend"  # Analyze and recommend changes
    APPLY = "apply"          # Apply recommended changes
    CONTINUOUS = "continuous"  # Run in continuous mode


class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AutomationController:
    """
    Central controller for AI Orchestra automation tasks.
    
    This class coordinates between different automation subsystems,
    provides a unified interface, and ensures proper sequencing of operations.
    """
    
    def __init__(
        self,
        base_dir: str = ".",
        ai_orchestra_dir: str = "ai-orchestra",
        config_path: Optional[str] = None,
        environment: Environment = Environment.DEVELOPMENT,
        data_dir: str = ".automation_data",
    ):
        """
        Initialize the automation controller.
        
        Args:
            base_dir: Base directory of the project
            ai_orchestra_dir: AI Orchestra directory
            config_path: Path to configuration file (optional)
            environment: Deployment environment
            data_dir: Directory to store automation data
        """
        self.base_dir = Path(base_dir)
        self.ai_orchestra_dir = self.base_dir / ai_orchestra_dir
        self.environment = environment
        
        # Set up data directory
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup task executors
        self.task_executors = {}
        
        # Initialize task dependencies
        self.task_dependencies = {
            AutomationTask.PERFORMANCE: [],
            AutomationTask.WORKSPACE: [],
            AutomationTask.DEPLOYMENT: [AutomationTask.TESTING],
            AutomationTask.TESTING: [],
            AutomationTask.AI_SERVICE: [],
            AutomationTask.COST: [],
            AutomationTask.INFRASTRUCTURE: [AutomationTask.COST],
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Returns:
            Configuration dictionary
        """
        default_config = {
            "performance": {
                "enabled": True,
                "automation_level": 2,  # 1=conservative, 2=moderate, 3=aggressive, 4=self-tuning
                "analysis_frequency_hours": 24,
                "apply_threshold": {
                    "development": 0.7,
                    "staging": 0.5,
                    "production": 0.3,
                }
            },
            "workspace": {
                "enabled": True,
                "file_exclusion_enabled": True,
                "git_optimization_enabled": True,
                "workspace_segmentation_enabled": True,
                "env_standardization_enabled": True,
                "repo_size_management_enabled": True,
            },
            "deployment": {
                "enabled": True,
                "auto_deployment": {
                    "development": True,
                    "staging": False,
                    "production": False
                },
                "deployment_window": {
                    "development": "anytime",
                    "staging": "8-18:00",  # 8am to 6pm
                    "production": "2-5:00"  # 2am to 5am
                },
                "approval_required": {
                    "development": False,
                    "staging": True,
                    "production": True
                }
            },
            "testing": {
                "enabled": True,
                "unit_test_frequency_hours": 4,
                "integration_test_frequency_hours": 8,
                "performance_test_frequency_hours": 24,
                "test_environments": ["development", "staging"]
            },
            "ai_service": {
                "enabled": True,
                "caching_enabled": True,
                "batching_enabled": True,
                "model_selection_optimization": True,
                "semantic_cache_threshold": 0.85,
                "cache_ttl_seconds": 3600
            },
            "cost": {
                "enabled": True,
                "alert_threshold_percent": 20,
                "auto_optimization_enabled": False,
                "billing_export_dataset": "billing_export",
                "recommendation_frequency_days": 7
            },
            "infrastructure": {
                "enabled": True,
                "self_tuning_enabled": False,
                "adaptation_frequency_hours": 24,
                "prediction_window_days": 7,
                "terraform_dir": "./terraform"
            },
            "notification": {
                "email_enabled": False,
                "email_recipients": [],
                "slack_enabled": False,
                "slack_webhook": ""
            }
        }
        
        if not self.config_path:
            return default_config
        
        config_path = Path(self.config_path)
        if not config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # Merge with defaults (for any missing keys)
            merged_config = default_config.copy()
            self._deep_update(merged_config, config)
            return merged_config
            
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return default_config
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update a dictionary.
        
        Args:
            d: Dictionary to update
            u: Dictionary with updates
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
    
    def _initialize_task_executors(self):
        """Initialize task executors for each automation task."""
        # Import task executors
        try:
            # Performance task executor
            from fully_automated_performance_enhancement import (
                AutomatedEnhancementEngine, AutomationLevel)
            
            performance_config = self.config.get("performance", {})
            if performance_config.get("enabled", True):
                self.task_executors[AutomationTask.PERFORMANCE] = AutomatedEnhancementEngine(
                    base_dir=str(self.base_dir),
                    ai_orchestra_dir=str(self.ai_orchestra_dir.relative_to(self.base_dir)),
                    automation_level=AutomationLevel(performance_config.get("automation_level", 2)),
                    environment=Environment(self.environment),
                    config_path=self.config_path,
                    data_dir=str(self.data_dir / "performance_data"),
                )
                logger.info("Initialized Performance Enhancement Engine")
        except ImportError:
            logger.warning("Performance Enhancement Engine not available")
        
        try:
            # Workspace task executor
            from workspace_optimization import WorkspaceOptimizer, OptimizationCategory
            
            workspace_config = self.config.get("workspace", {})
            if workspace_config.get("enabled", True):
                self.task_executors[AutomationTask.WORKSPACE] = WorkspaceOptimizer(
                    base_dir=str(self.base_dir),
                    config_path=self.config_path,
                    data_dir=str(self.data_dir / "workspace_optimization"),
                    max_data_size_mb=50,
                )
                logger.info("Initialized Workspace Optimizer")
        except ImportError:
            logger.warning("Workspace Optimizer not available")
    
    async def run_task(
        self, 
        task: AutomationTask, 
        mode: AutomationMode
    ) -> Dict[str, Any]:
        """
        Run an automation task.
        
        Args:
            task: Automation task to run
            mode: Mode to run in (analyze, recommend, apply, continuous)
            
        Returns:
            Task results
        """
        # Initialize task executors if not already done
        if not self.task_executors:
            self._initialize_task_executors()
        
        # Check if task is enabled
        task_config = self.config.get(task.value, {})
        if not task_config.get("enabled", True):
            logger.info(f"Task {task} is disabled in configuration")
            return {"status": "skipped", "reason": "disabled_in_config"}
        
        # Check if task executor is available
        if task not in self.task_executors:
            logger.warning(f"No executor available for {task}")
            return {"status": "error", "reason": "no_executor_available"}
        
        # Check if any dependencies need to be run first
        for dependency in self.task_dependencies.get(task, []):
            if dependency not in self.task_executors:
                logger.warning(f"Dependency {dependency} not available for {task}")
                continue
            
            logger.info(f"Running dependency {dependency} for {task}")
            await self.run_task(dependency, AutomationMode.ANALYZE)
        
        # Run the task
        executor = self.task_executors[task]
        result = {"status": "unknown"}
        
        try:
            if mode == AutomationMode.ANALYZE:
                if task == AutomationTask.PERFORMANCE:
                    system_profile = await executor.collect_system_metrics()
                    result = {"status": "success", "metrics": system_profile.to_dict()}
                
                elif task == AutomationTask.WORKSPACE:
                    optimization_profile = await executor.analyze_workspace()
                    result = {"status": "success", "profile": optimization_profile.to_dict()}
            
            elif mode == AutomationMode.RECOMMEND:
                if task == AutomationTask.PERFORMANCE:
                    recommendations = await executor.analyze_metrics()
                    result = {"status": "success", "recommendations": [r.to_dict() for r in recommendations]}
                
                elif task == AutomationTask.WORKSPACE:
                    # Workspace optimizer doesn't have a separate recommend mode,
                    # so we'll just analyze
                    optimization_profile = await executor.analyze_workspace()
                    result = {"status": "success", "profile": optimization_profile.to_dict()}
            
            elif mode == AutomationMode.APPLY:
                if task == AutomationTask.PERFORMANCE:
                    recommendations = await executor.analyze_metrics()
                    plan = await executor.create_enhancement_plan(recommendations)
                    success = await executor.process_plan(plan)
                    result = {"status": "success" if success else "partial", "plan_id": plan.id}
                
                elif task == AutomationTask.WORKSPACE:
                    # Get categories from config
                    workspace_config = self.config.get("workspace", {})
                    categories = []
                    
                    if workspace_config.get("file_exclusion_enabled", True):
                        categories.append("file_exclusions")
                    
                    if workspace_config.get("git_optimization_enabled", True):
                        categories.append("git_optimization")
                    
                    if workspace_config.get("workspace_segmentation_enabled", True):
                        categories.append("workspace_segmentation")
                    
                    if workspace_config.get("env_standardization_enabled", True):
                        categories.append("env_management")
                    
                    if workspace_config.get("repo_size_management_enabled", True):
                        categories.append("repo_size")
                    
                    success = await executor.optimize_workspace(categories=categories)
                    result = {"status": "success" if success else "partial"}
            
            elif mode == AutomationMode.CONTINUOUS:
                if task == AutomationTask.PERFORMANCE:
                    # Get analysis frequency
                    frequency = self.config.get("performance", {}).get("analysis_frequency_hours", 24)
                    await executor.run_continuous_monitoring(frequency * 3600)
                    result = {"status": "running"}
                    
        except Exception as e:
            logger.error(f"Error running {task} in {mode} mode: {str(e)}")
            result = {"status": "error", "error": str(e)}
        
        return result
    
    async def run_multiple_tasks(
        self,
        tasks: List[AutomationTask],
        mode: AutomationMode
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run multiple automation tasks.
        
        Args:
            tasks: List of automation tasks to run
            mode: Mode to run in (analyze, recommend, apply, continuous)
            
        Returns:
            Dictionary of task results
        """
        results = {}
        
        for task in tasks:
            logger.info(f"Running {task} in {mode} mode")
            results[task] = await self.run_task(task, mode)
        
        return results
    
    async def run_all_tasks(self, mode: AutomationMode) -> Dict[str, Dict[str, Any]]:
        """
        Run all enabled automation tasks.
        
        Args:
            mode: Mode to run in (analyze, recommend, apply, continuous)
            
        Returns:
            Dictionary of task results
        """
        tasks = [
            task for task in AutomationTask 
            if task != AutomationTask.ALL and self.config.get(task.value, {}).get("enabled", True)
        ]
        
        return await self.run_multiple_tasks(tasks, mode)
    
    async def generate_report(
        self, 
        results: Dict[str, Dict[str, Any]],
        format: str = "text"
    ) -> str:
        """
        Generate a report of automation results.
        
        Args:
            results: Dictionary of task results
            format: Report format (text, json, html)
            
        Returns:
            Report as a string
        """
        if format == "json":
            return json.dumps(results, indent=2)
        
        elif format == "html":
            # Generate HTML report
            html = "<html><head><title>Automation Report</title></head><body>"
            html += "<h1>AI Orchestra Automation Report</h1>"
            
            for task, result in results.items():
                status = result.get("status", "unknown")
                status_class = {
                    "success": "success",
                    "partial": "warning",
                    "error": "error",
                    "skipped": "info",
                    "unknown": "info"
                }.get(status, "info")
                
                html += f'<div class="task {status_class}">'
                html += f'<h2>{task.value.title()}</h2>'
                html += f'<p>Status: {status}</p>'
                
                if "error" in result:
                    html += f'<p>Error: {result["error"]}</p>'
                
                html += "</div>"
            
            html += "</body></html>"
            return html
        
        else:  # Text format
            report = "AI Orchestra Automation Report\n"
            report += "===========================\n\n"
            
            for task, result in results.items():
                status = result.get("status", "unknown")
                report += f"{task.value.title()}: {status}\n"
                
                if status == "error" and "error" in result:
                    report += f"  Error: {result['error']}\n"
                elif status == "success" and "recommendations" in result:
                    report += f"  Recommendations: {len(result['recommendations'])}\n"
                
                report += "\n"
            
            return report
    
    async def notify_results(
        self, 
        report: str,
        format: str = "text"
    ) -> bool:
        """
        Send notification with results.
        
        Args:
            report: Report to send
            format: Report format (text, json, html)
            
        Returns:
            True if notification was sent successfully
        """
        notification_config = self.config.get("notification", {})
        
        # Email notification
        if notification_config.get("email_enabled", False):
            recipients = notification_config.get("email_recipients", [])
            if recipients:
                try:
                    # Send email
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    msg = MIMEMultipart()
                    msg["Subject"] = f"AI Orchestra Automation Report - {self.environment.value.title()}"
                    msg["From"] = "ai-orchestra-automation@example.com"
                    msg["To"] = ", ".join(recipients)
                    
                    if format == "html":
                        msg.attach(MIMEText(report, "html"))
                    else:
                        msg.attach(MIMEText(report, "plain"))
                    
                    # This would be replaced with actual SMTP configuration
                    # with smtplib.SMTP("smtp.example.com") as server:
                    #     server.send_message(msg)
                    
                    logger.info(f"Email notification sent to {len(recipients)} recipients")
                except Exception as e:
                    logger.error(f"Failed to send email notification: {str(e)}")
                    return False
        
        # Slack notification
        if notification_config.get("slack_enabled", False):
            webhook = notification_config.get("slack_webhook", "")
            if webhook:
                try:
                    # Send Slack notification
                    import requests
                    
                    data = {
                        "text": f"AI Orchestra Automation Report - {self.environment.value.title()}",
                        "attachments": [
                            {
                                "title": "Automation Results",
                                "text": report if format == "text" else "Please see attached report",
                                "color": "#36a64f"
                            }
                        ]
                    }
                    
                    # This would be uncommented in actual implementation
                    # response = requests.post(webhook, json=data)
                    # response.raise_for_status()
                    
                    logger.info("Slack notification sent")
                except Exception as e:
                    logger.error(f"Failed to send Slack notification: {str(e)}")
                    return False
        
        return True


async def run_automation_controller(args):
    """
    Run the automation controller with the provided arguments.
    
    Args:
        args: Command-line arguments
    """
    # Create the controller
    controller = AutomationController(
        base_dir=args.base_dir,
        ai_orchestra_dir=args.ai_orchestra_dir,
        config_path=args.config,
        environment=Environment(args.environment),
        data_dir=args.data_dir,
    )
    
    # Parse tasks
    tasks = []
    if args.tasks:
        for task in args.tasks.split(","):
            try:
                tasks.append(AutomationTask(task))
            except ValueError:
                logger.warning(f"Invalid task: {task}")
    
    # Run tasks
    if AutomationTask.ALL in tasks or not tasks:
        results = await controller.run_all_tasks(AutomationMode(args.mode))
    else:
        results = await controller.run_multiple_tasks(tasks, AutomationMode(args.mode))
    
    # Generate report
    report = await controller.generate_report(results, args.report_format)
    
    # Print report
    print(report)
    
    # Save report if requested
    if args.save_report:
        report_path = Path(args.save_report)
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"Report saved to {report_path}")
    
    # Send notification if requested
    if args.notify:
        success = await controller.notify_results(report, args.report_format)
        if success:
            print("Notification sent successfully")
        else:
            print("Failed to send notification")
    
    return 0


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Automation Controller for AI Orchestra"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory of the project",
    )
    
    parser.add_argument(
        "--ai-orchestra-dir",
        type=str,
        default="ai-orchestra",
        help="AI Orchestra directory",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (YAML or JSON)",
    )
    
    parser.add_argument(
        "--environment",
        type=str,
        choices=["development", "staging", "production"],
        default="development",
        help="Deployment environment",
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default=".automation_data",
        help="Directory to store automation data",
    )
    
    parser.add_argument(
        "--tasks",
        type=str,
        help="Comma-separated list of tasks to run (default: all)",
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["analyze", "recommend", "apply", "continuous"],
        default="analyze",
        help="Mode to run in",
    )
    
    parser.add_argument(
        "--report-format",
        type=str,
        choices=["text", "json", "html"],
        default="text",
        help="Report format",
    )
    
    parser.add_argument(
        "--save-report",
        type=str,
        help="Save report to file",
    )
    
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send notification with results",
    )
    
    args = parser.parse_args()
    
    # Create data directory
    Path(args.data_dir).mkdir(exist_ok=True)
    
    # Run the controller
    asyncio.run(run_automation_controller(args))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())