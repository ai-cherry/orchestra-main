#!/usr/bin/env python3
"""
Symphony Orchestrator - Unified Automated System for AI Optimization Framework

This is the main orchestration service that manages all cleanup, maintenance,
and optimization tasks automatically without manual intervention.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/symphony_orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Task status enum
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskResult:
    """Result of a task execution"""
    task_name: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: str = ""
    error: str = ""
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.end_time:
            return self.end_time - self.start_time
        return None

@dataclass
class Task:
    """Definition of an automated task"""
    name: str
    command: str
    schedule: str  # cron-like or interval
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 3600  # seconds
    retry_count: int = 3
    retry_delay: int = 300  # seconds
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
class SymphonyOrchestrator:
    """Main orchestration engine for all automated tasks"""
    
    def __init__(self, config_path: str = "config/orchestrator_config.json"):
        self.config_path = Path(config_path)
        self.project_root = Path(__file__).parent.parent
        self.tasks: Dict[str, Task] = {}
        self.results: List[TaskResult] = []
        self.running = False
        self.scheduler_thread = None
        self.state_file = Path("orchestrator_state.json")
        
        # Ensure directories exist
        (self.project_root / "logs").mkdir(exist_ok=True)
        (self.project_root / "status").mkdir(exist_ok=True)
        
        # Load configuration
        self._load_config()
        self._load_state()
        
    def _load_config(self):
        """Load orchestrator configuration"""
        # Default configuration if file doesn't exist
        default_config = {
            "tasks": [
                {
                    "name": "inventory_scan",
                    "command": "./scripts/comprehensive_inventory.sh",
                    "schedule": "0 2 * * *",  # Daily at 2 AM
                    "dependencies": [],
                    "timeout": 1800,
                    "enabled": True
                },
                {
                    "name": "cleanup_analysis",
                    "command": "python scripts/cleanup_engine.py cleanup_inventory.json --report-only",
                    "schedule": "30 2 * * *",  # Daily at 2:30 AM
                    "dependencies": ["inventory_scan"],
                    "timeout": 1800,
                    "enabled": True
                },
                {
                    "name": "cleanup_execution",
                    "command": "python scripts/cleanup_engine.py cleanup_inventory.json --execute --non-interactive",
                    "schedule": "0 3 * * 0",  # Weekly on Sunday at 3 AM
                    "dependencies": ["cleanup_analysis"],
                    "timeout": 3600,
                    "enabled": True,
                    "retry_count": 1
                },
                {
                    "name": "health_check",
                    "command": "./scripts/quick_health_check.sh",
                    "schedule": "*/30 * * * *",  # Every 30 minutes
                    "dependencies": [],
                    "timeout": 300,
                    "enabled": True
                },
                {
                    "name": "automation_health",
                    "command": "python scripts/automation_manager.py health",
                    "schedule": "0 * * * *",  # Every hour
                    "dependencies": [],
                    "timeout": 300,
                    "enabled": True
                },
                {
                    "name": "expired_files_cleanup",
                    "command": "python -m core.utils.file_management",
                    "schedule": "0 4 * * *",  # Daily at 4 AM
                    "dependencies": [],
                    "timeout": 1800,
                    "enabled": True
                },
                {
                    "name": "git_maintenance",
                    "command": "git gc --aggressive --prune=now",
                    "schedule": "0 5 1 * *",  # Monthly on 1st at 5 AM
                    "dependencies": [],
                    "timeout": 3600,
                    "enabled": True
                }
            ],
            "settings": {
                "max_concurrent_tasks": 3,
                "task_history_retention_days": 30,
                "notification_webhook": None,
                "enable_notifications": False
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        else:
            # Create default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            config = default_config
            logger.info(f"Created default configuration at {self.config_path}")
        
        # Parse tasks
        for task_config in config.get('tasks', []):
            task = Task(**task_config)
            self.tasks[task.name] = task
        
        self.settings = config.get('settings', {})
        
    def _load_state(self):
        """Load orchestrator state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                # Restore last run times
                for task_name, task_state in state.get('tasks', {}).items():
                    if task_name in self.tasks:
                        last_run = task_state.get('last_run')
                        if last_run:
                            self.tasks[task_name].last_run = datetime.fromisoformat(last_run)
                
                # Restore results history
                for result_data in state.get('results', [])[-100:]:  # Keep last 100
                    result = TaskResult(
                        task_name=result_data['task_name'],
                        status=TaskStatus(result_data['status']),
                        start_time=datetime.fromisoformat(result_data['start_time']),
                        end_time=datetime.fromisoformat(result_data['end_time']) if result_data.get('end_time') else None,
                        output=result_data.get('output', ''),
                        error=result_data.get('error', '')
                    )
                    self.results.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save orchestrator state to disk"""
        state = {
            'tasks': {
                name: {
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                }
                for name, task in self.tasks.items()
            },
            'results': [
                {
                    'task_name': r.task_name,
                    'status': r.status.value,
                    'start_time': r.start_time.isoformat(),
                    'end_time': r.end_time.isoformat() if r.end_time else None,
                    'output': r.output[-1000:],  # Keep last 1000 chars
                    'error': r.error[-1000:]
                }
                for r in self.results[-100:]  # Keep last 100 results
            ],
            'last_save': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _can_run_task(self, task: Task) -> bool:
        """Check if a task can run based on dependencies"""
        for dep in task.dependencies:
            # Check if dependency has run successfully today
            dep_task = self.tasks.get(dep)
            if not dep_task:
                logger.warning(f"Unknown dependency {dep} for task {task.name}")
                return False
            
            if not dep_task.last_run:
                return False
            
            # Check if dependency ran successfully in the last 24 hours
            recent_results = [r for r in self.results 
                            if r.task_name == dep and 
                            r.start_time > datetime.now(timezone.utc) - timedelta(days=1)]
            
            if not recent_results or recent_results[-1].status != TaskStatus.SUCCESS:
                return False
        
        return True
    
    async def _run_task(self, task: Task) -> TaskResult:
        """Execute a single task"""
        logger.info(f"Starting task: {task.name}")
        
        result = TaskResult(
            task_name=task.name,
            status=TaskStatus.RUNNING,
            start_time=datetime.now(timezone.utc)
        )
        
        # Check dependencies
        if not self._can_run_task(task):
            result.status = TaskStatus.SKIPPED
            result.error = "Dependencies not met"
            result.end_time = datetime.now(timezone.utc)
            logger.info(f"Skipped task {task.name}: dependencies not met")
            return result
        
        # Execute command
        retry_count = 0
        while retry_count <= task.retry_count:
            try:
                # Change to project root for execution
                process = await asyncio.create_subprocess_shell(
                    task.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_root
                )
                
                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=task.timeout
                    )
                    
                    result.output = stdout.decode('utf-8', errors='replace')
                    result.error = stderr.decode('utf-8', errors='replace')
                    
                    if process.returncode == 0:
                        result.status = TaskStatus.SUCCESS
                        task.last_run = datetime.now(timezone.utc)
                        logger.info(f"Task {task.name} completed successfully")
                        break
                    else:
                        raise Exception(f"Command failed with exit code {process.returncode}")
                        
                except asyncio.TimeoutError:
                    process.terminate()
                    await process.wait()
                    raise Exception(f"Task timed out after {task.timeout} seconds")
                    
            except Exception as e:
                logger.error(f"Task {task.name} failed (attempt {retry_count + 1}): {e}")
                result.error = str(e)
                result.status = TaskStatus.FAILED
                
                retry_count += 1
                if retry_count <= task.retry_count:
                    logger.info(f"Retrying task {task.name} in {task.retry_delay} seconds...")
                    await asyncio.sleep(task.retry_delay)
        
        result.end_time = datetime.now(timezone.utc)
        
        # Save result
        self.results.append(result)
        self._save_state()
        
        # Send notification if enabled
        if self.settings.get('enable_notifications') and result.status == TaskStatus.FAILED:
            self._send_notification(result)
        
        return result
    
    def _send_notification(self, result: TaskResult):
        """Send notification for task result"""
        webhook_url = self.settings.get('notification_webhook')
        if not webhook_url:
            return
        
        try:
            import requests
            payload = {
                'task': result.task_name,
                'status': result.status.value,
                'duration': str(result.duration) if result.duration else None,
                'error': result.error[:500] if result.error else None
            }
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def _schedule_tasks(self):
        """Schedule all tasks based on their cron expressions"""
        import croniter
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            try:
                # Parse cron expression
                cron = croniter.croniter(task.schedule, datetime.now())
                task.next_run = cron.get_next(datetime)
                
                # Schedule with python schedule library for simplicity
                if task.schedule.startswith("*/"):
                    # Interval schedule
                    minutes = int(task.schedule.split()[0].replace("*/", ""))
                    schedule.every(minutes).minutes.do(
                        lambda t=task: asyncio.run(self._run_task(t))
                    )
                elif task.schedule == "0 * * * *":
                    # Hourly
                    schedule.every().hour.at(":00").do(
                        lambda t=task: asyncio.run(self._run_task(t))
                    )
                else:
                    # For complex cron, check every minute
                    def check_and_run(t=task):
                        now = datetime.now()
                        cron = croniter.croniter(t.schedule, now - timedelta(minutes=1))
                        next_run = cron.get_next(datetime)
                        if next_run <= now:
                            asyncio.run(self._run_task(t))
                    
                    schedule.every().minute.do(check_and_run)
                
                logger.info(f"Scheduled task {task.name} with schedule {task.schedule}")
                
            except Exception as e:
                logger.error(f"Failed to schedule task {task.name}: {e}")
    
    def _scheduler_loop(self):
        """Background thread for running scheduled tasks"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def start(self):
        """Start the orchestrator"""
        logger.info("Starting Symphony Orchestrator...")
        
        self.running = True
        
        # Schedule all tasks
        self._schedule_tasks()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # Run initial health check
        health_task = self.tasks.get('health_check')
        if health_task:
            asyncio.run(self._run_task(health_task))
        
        logger.info("Symphony Orchestrator started successfully")
        
        # Write PID file for service management
        pid_file = Path("orchestrator.pid")
        pid_file.write_text(str(os.getpid()))
    
    def stop(self):
        """Stop the orchestrator"""
        logger.info("Stopping Symphony Orchestrator...")
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self._save_state()
        
        # Remove PID file
        pid_file = Path("orchestrator.pid")
        if pid_file.exists():
            pid_file.unlink()
        
        logger.info("Symphony Orchestrator stopped")
    
    def status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            'running': self.running,
            'tasks': {
                name: {
                    'enabled': task.enabled,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'schedule': task.schedule
                }
                for name, task in self.tasks.items()
            },
            'recent_results': [
                {
                    'task': r.task_name,
                    'status': r.status.value,
                    'time': r.start_time.isoformat(),
                    'duration': str(r.duration) if r.duration else None
                }
                for r in self.results[-20:]
            ]
        }
    
    def run_task_manually(self, task_name: str) -> Optional[TaskResult]:
        """Run a specific task manually"""
        task = self.tasks.get(task_name)
        if not task:
            logger.error(f"Unknown task: {task_name}")
            return None
        
        return asyncio.run(self._run_task(task))

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if hasattr(signal_handler, 'orchestrator'):
        signal_handler.orchestrator.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Symphony Orchestrator - Unified Automation System")
    parser.add_argument('command', choices=['start', 'stop', 'status', 'run'], 
                       help='Command to execute')
    parser.add_argument('--task', help='Task name for manual run')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--config', default='config/orchestrator_config.json',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    if args.command == 'stop':
        # Stop running orchestrator
        pid_file = Path("orchestrator.pid")
        if pid_file.exists():
            pid = int(pid_file.read_text())
            try:
                os.kill(pid, signal.SIGTERM)
                print("Orchestrator stopped")
            except ProcessLookupError:
                print("Orchestrator not running")
                pid_file.unlink()
        else:
            print("Orchestrator not running")
        return
    
    orchestrator = SymphonyOrchestrator(args.config)
    
    if args.command == 'status':
        # Show status
        status = orchestrator.status()
        print(json.dumps(status, indent=2))
        
    elif args.command == 'run':
        # Run specific task
        if not args.task:
            print("Error: --task required for run command")
            sys.exit(1)
        
        result = orchestrator.run_task_manually(args.task)
        if result:
            print(f"Task {result.task_name}: {result.status.value}")
            if result.output:
                print(f"Output:\n{result.output}")
            if result.error:
                print(f"Error:\n{result.error}")
    
    elif args.command == 'start':
        # Start orchestrator
        signal_handler.orchestrator = orchestrator
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        if args.daemon:
            # Fork to background
            import daemon
            with daemon.DaemonContext():
                orchestrator.start()
                # Keep running
                while orchestrator.running:
                    time.sleep(1)
        else:
            orchestrator.start()
            print("Symphony Orchestrator is running. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                orchestrator.stop()

if __name__ == "__main__":
    main()