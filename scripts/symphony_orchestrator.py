import asyncio
#!/usr/bin/env python3
"""
"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskResult:
    """Result of a task execution"""
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
    """Main coordination engine for all automated tasks"""
    def __init__(self, config_path: str = "config/conductor_config.json"):
        self.config_path = Path(config_path)
        self.project_root = Path(__file__).parent.parent
        self.tasks: Dict[str, Task] = {}
        self.results: List[TaskResult] = []
        self.running = False
        self.scheduler_thread = None
        self.state_file = Path("conductor_state.json")
        
        # Ensure directories exist
        (self.project_root / "logs").mkdir(exist_ok=True)
        (self.project_root / "status").mkdir(exist_ok=True)
        
        # Load configuration
        self._load_config()
        self._load_state()
        
    def _load_config(self):
        """Load conductor configuration"""
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
                    "",
                    "schedule": "30 2 * * *",  # Daily at 2:30 AM
                    "dependencies": ["inventory_scan"],
                    "timeout": 1800,
                    "enabled": True
                },
                {
                    "name": "cleanup_execution",
                    "",
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
        """Load conductor state from disk"""
                logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save conductor state to disk"""
            logger.error(f"Failed to save state: {e}")
    
    def _can_run_task(self, task: Task) -> bool:
        """Check if a task can run based on dependencies"""
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

                pass
                # Change to project root for execution
                process = await asyncio.create_subprocess_shell(
                    task.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.project_root
                )
                
                # Wait for completion with timeout
                try:

                    pass
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
                        
                except Exception:

                        
                    pass
                    process.terminate()
                    await process.wait()
                    raise Exception(f"Task timed out after {task.timeout} seconds")
                    
            except Exception:

                    
                pass
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
            logger.error(f"Failed to send notification: {e}")
    
    def _schedule_tasks(self):
        """Schedule all tasks based on their cron expressions"""
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
                
            except Exception:

                
                pass
                logger.error(f"Failed to schedule task {task.name}: {e}")
    
    def _scheduler_loop(self):
        """Background thread for running scheduled tasks"""
        """Start the conductor"""
        logger.info("Starting Symphony conductor...")
        
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
        
        logger.info("Symphony conductor started successfully")
        
        # Write PID file for service management
        pid_file = Path("conductor.pid")
        pid_file.write_text(str(os.getpid()))
    
    def stop(self):
        """Stop the conductor"""
        logger.info("Stopping Symphony conductor...")
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self._save_state()
        
        # Remove PID file
        pid_file = Path("conductor.pid")
        if pid_file.exists():
            pid_file.unlink()
        
        logger.info("Symphony conductor stopped")
    
    def status(self) -> Dict[str, Any]:
        """Get current conductor status"""
        """Run a specific task manually"""
            logger.error(f"Unknown task: {task_name}")
            return None
        
        return asyncio.run(self._run_task(task))

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if hasattr(signal_handler, 'conductor'):
        signal_handler.conductor.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Symphony conductor - Unified Automation System")
    parser.add_argument('command', choices=['start', 'stop', 'status', 'run'], 
                       help='Command to execute')
    parser.add_argument('--task', help='Task name for manual run')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--config', default='config/conductor_config.json',
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    if args.command == 'stop':
        # Stop running conductor
        pid_file = Path("conductor.pid")
        if pid_file.exists():
            pid = int(pid_file.read_text())
            try:

                pass
                os.kill(pid, signal.SIGTERM)
                print("conductor stopped")
            except Exception:

                pass
                print("conductor not running")
                pid_file.unlink()
        else:
            print("conductor not running")
        return
    
    conductor = Symphonyconductor(args.config)
    
    if args.command == 'status':
        # Show status
        status = conductor.status()
        print(json.dumps(status, indent=2))
        
    elif args.command == 'run':
        # Run specific task
        if not args.task:
            print("Error: --task required for run command")
            sys.exit(1)
        
        result = conductor.run_task_manually(args.task)
        if result:
            print(f"Task {result.task_name}: {result.status.value}")
            if result.output:
                print(f"Output:\n{result.output}")
            if result.error:
                print(f"Error:\n{result.error}")
    
    elif args.command == 'start':
        # Start conductor
        signal_handler.conductor = conductor
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        if args.daemon:
            # Fork to background
            import daemon
            with daemon.DaemonContext():
                conductor.start()
                # Keep running
                while conductor.running:
                    await asyncio.sleep(1)
        else:
            conductor.start()
            print("Symphony conductor is running. Press Ctrl+C to stop.")
            try:

                pass
                while True:
                    await asyncio.sleep(1)
            except Exception:

                pass
                conductor.stop()

if __name__ == "__main__":
    main()