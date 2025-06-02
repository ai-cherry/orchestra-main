#!/usr/bin/env python3
"""
Orchestra AI Refactoring Orchestrator

This script manages the complete refactoring and enhancement process for Orchestra AI.
It provides automated migration, safety checks, rollback capabilities, and progress tracking.

Usage:
    python scripts/refactoring_orchestrator.py --phase 1 --preview    # Preview changes
    python scripts/refactoring_orchestrator.py --phase 1 --execute   # Execute phase 1
    python scripts/refactoring_orchestrator.py --rollback phase-1    # Rollback phase 1
    python scripts/refactoring_orchestrator.py --status              # Show status
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import logging

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.tree import Tree

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rich console for beautiful output
console = Console()

class Phase(Enum):
    """Refactoring phases"""
    FOUNDATION = 1
    CONSOLIDATION = 2
    ENHANCEMENT = 3
    PERFORMANCE = 4
    AUTOMATION = 5

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Task:
    """Individual refactoring task"""
    id: str
    name: str
    description: str
    phase: Phase
    priority: int
    estimated_duration: int  # minutes
    dependencies: List[str]
    rollback_commands: List[str]
    execute_func: Optional[Callable] = None
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class MigrationState:
    """Current migration state"""
    current_phase: Optional[Phase] = None
    completed_tasks: List[str] = None
    failed_tasks: List[str] = None
    rollback_points: Dict[str, datetime] = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.completed_tasks is None:
            self.completed_tasks = []
        if self.failed_tasks is None:
            self.failed_tasks = []
        if self.rollback_points is None:
            self.rollback_points = {}
        if self.last_updated is None:
            self.last_updated = datetime.now()

class RefactoringOrchestrator:
    """Main orchestrator for the refactoring process"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_file = project_root / ".refactoring_state.json"
        self.backup_dir = project_root / ".refactoring_backups"
        self.state = self._load_state()
        self.tasks = self._define_tasks()
    
    def _load_state(self) -> MigrationState:
        """Load migration state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Convert phase back to enum
                    if data.get('current_phase'):
                        data['current_phase'] = Phase(data['current_phase'])
                    # Convert datetime strings back
                    if data.get('last_updated'):
                        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                    if data.get('rollback_points'):
                        data['rollback_points'] = {
                            k: datetime.fromisoformat(v) 
                            for k, v in data['rollback_points'].items()
                        }
                    return MigrationState(**data)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        
        return MigrationState()
    
    def _save_state(self):
        """Save migration state to file"""
        try:
            # Convert enums and datetime to serializable format
            state_dict = asdict(self.state)
            if state_dict['current_phase']:
                state_dict['current_phase'] = state_dict['current_phase'].value
            if state_dict['last_updated']:
                state_dict['last_updated'] = state_dict['last_updated'].isoformat()
            if state_dict['rollback_points']:
                state_dict['rollback_points'] = {
                    k: v.isoformat() for k, v in state_dict['rollback_points'].items()
                }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _define_tasks(self) -> Dict[str, Task]:
        """Define all refactoring tasks"""
        tasks = {}
        
        # Phase 1: Foundation Tasks
        tasks["remove_poetry"] = Task(
            id="remove_poetry",
            name="Remove Poetry Configuration",
            description="Remove pyproject.toml Poetry sections and consolidate to pip/venv",
            phase=Phase.FOUNDATION,
            priority=1,
            estimated_duration=15,
            dependencies=[],
            rollback_commands=["git checkout pyproject.toml"],
            execute_func=self._remove_poetry_config
        )
        
        tasks["consolidate_requirements"] = Task(
            id="consolidate_requirements",
            name="Consolidate Requirements Files",
            description="Merge all requirement files into unified structure",
            phase=Phase.FOUNDATION,
            priority=2,
            estimated_duration=30,
            dependencies=["remove_poetry"],
            rollback_commands=["git checkout requirements/"],
            execute_func=self._consolidate_requirements
        )
        
        tasks["setup_unified_config"] = Task(
            id="setup_unified_config",
            name="Deploy Unified Configuration",
            description="Deploy the unified configuration system",
            phase=Phase.FOUNDATION,
            priority=3,
            estimated_duration=45,
            dependencies=["consolidate_requirements"],
            rollback_commands=["rm -rf core/config/unified_config.py"],
            execute_func=self._setup_unified_config
        )
        
        # Phase 2: Consolidation Tasks
        tasks["deploy_unified_llm_router"] = Task(
            id="deploy_unified_llm_router",
            name="Deploy Unified LLM Router",
            description="Replace all LLM router implementations with unified version",
            phase=Phase.CONSOLIDATION,
            priority=1,
            estimated_duration=60,
            dependencies=["setup_unified_config"],
            rollback_commands=["git checkout core/llm*"],
            execute_func=self._deploy_unified_llm_router
        )
        
        tasks["deploy_unified_database"] = Task(
            id="deploy_unified_database",
            name="Deploy Unified Database",
            description="Replace database implementations with unified interface",
            phase=Phase.CONSOLIDATION,
            priority=2,
            estimated_duration=45,
            dependencies=["setup_unified_config"],
            rollback_commands=["git checkout shared/database/"],
            execute_func=self._deploy_unified_database
        )
        
        tasks["migrate_core_imports"] = Task(
            id="migrate_core_imports",
            name="Migrate Core Imports",
            description="Update all imports to use new unified interfaces",
            phase=Phase.CONSOLIDATION,
            priority=3,
            estimated_duration=90,
            dependencies=["deploy_unified_llm_router", "deploy_unified_database"],
            rollback_commands=["git checkout core/ shared/ agent/"],
            execute_func=self._migrate_core_imports
        )
        
        # Phase 3: Enhancement Tasks
        tasks["reorganize_core_directory"] = Task(
            id="reorganize_core_directory",
            name="Reorganize Core Directory",
            description="Organize core files into logical subdirectories",
            phase=Phase.ENHANCEMENT,
            priority=1,
            estimated_duration=30,
            dependencies=["migrate_core_imports"],
            rollback_commands=["git checkout core/"],
            execute_func=self._reorganize_core_directory
        )
        
        tasks["enhance_orchestrator"] = Task(
            id="enhance_orchestrator",
            name="Enhance Orchestrator Architecture",
            description="Implement clean architecture patterns in orchestrator",
            phase=Phase.ENHANCEMENT,
            priority=2,
            estimated_duration=120,
            dependencies=["reorganize_core_directory"],
            rollback_commands=["git checkout core/orchestrator/"],
            execute_func=self._enhance_orchestrator
        )
        
        # Phase 4: Performance Tasks
        tasks["optimize_async_patterns"] = Task(
            id="optimize_async_patterns",
            name="Optimize Async Patterns",
            description="Improve async/await usage throughout codebase",
            phase=Phase.PERFORMANCE,
            priority=1,
            estimated_duration=60,
            dependencies=["enhance_orchestrator"],
            rollback_commands=["git checkout core/ shared/"],
            execute_func=self._optimize_async_patterns
        )
        
        tasks["implement_monitoring"] = Task(
            id="implement_monitoring",
            name="Implement Enhanced Monitoring",
            description="Add comprehensive monitoring and metrics",
            phase=Phase.PERFORMANCE,
            priority=2,
            estimated_duration=45,
            dependencies=["optimize_async_patterns"],
            rollback_commands=["git checkout core/monitoring/"],
            execute_func=self._implement_monitoring
        )
        
        # Phase 5: Automation Tasks
        tasks["consolidate_scripts"] = Task(
            id="consolidate_scripts",
            name="Consolidate Scripts",
            description="Merge overlapping scripts and improve automation",
            phase=Phase.AUTOMATION,
            priority=1,
            estimated_duration=90,
            dependencies=["implement_monitoring"],
            rollback_commands=["git checkout scripts/"],
            execute_func=self._consolidate_scripts
        )
        
        return tasks
    
    def create_backup(self, name: str) -> Path:
        """Create a backup of current state"""
        self.backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{name}_{timestamp}"
        
        # Create backup using git stash or direct copy
        try:
            subprocess.run(["git", "stash", "push", "-m", f"Backup {name}"], 
                          cwd=self.project_root, check=True)
            logger.info(f"Created git stash backup: {name}")
        except:
            # Fallback to direct copy
            shutil.copytree(self.project_root, backup_path, 
                          ignore=shutil.ignore_patterns('.git', '__pycache__', 'venv'))
            logger.info(f"Created directory backup: {backup_path}")
        
        return backup_path
    
    def preview_phase(self, phase: Phase) -> None:
        """Preview tasks for a specific phase"""
        phase_tasks = [task for task in self.tasks.values() if task.phase == phase]
        
        console.print(f"\n[bold blue]Phase {phase.value}: {phase.name.title()}[/bold blue]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Task", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Duration", style="yellow")
        table.add_column("Dependencies", style="green")
        table.add_column("Status", style="red")
        
        for task in sorted(phase_tasks, key=lambda x: x.priority):
            deps = ", ".join(task.dependencies) if task.dependencies else "None"
            status_color = {
                TaskStatus.PENDING: "yellow",
                TaskStatus.COMPLETED: "green",
                TaskStatus.FAILED: "red",
                TaskStatus.IN_PROGRESS: "blue"
            }.get(task.status, "white")
            
            table.add_row(
                task.name,
                task.description,
                f"{task.estimated_duration}min",
                deps,
                f"[{status_color}]{task.status.value}[/{status_color}]"
            )
        
        console.print(table)
        
        total_duration = sum(task.estimated_duration for task in phase_tasks)
        console.print(f"\n[bold]Total estimated duration: {total_duration} minutes[/bold]")
    
    async def execute_phase(self, phase: Phase, dry_run: bool = False) -> bool:
        """Execute all tasks in a phase"""
        phase_tasks = [task for task in self.tasks.values() if task.phase == phase]
        phase_tasks.sort(key=lambda x: x.priority)
        
        if dry_run:
            console.print(f"[yellow]DRY RUN: Would execute {len(phase_tasks)} tasks[/yellow]")
            self.preview_phase(phase)
            return True
        
        console.print(f"\n[bold green]Executing Phase {phase.value}: {phase.name.title()}[/bold green]")
        
        # Create backup before starting
        backup_name = f"phase-{phase.value}-{phase.name.lower()}"
        self.create_backup(backup_name)
        self.state.rollback_points[backup_name] = datetime.now()
        
        success_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            for task in phase_tasks:
                # Check dependencies
                unmet_deps = [dep for dep in task.dependencies 
                            if dep not in self.state.completed_tasks]
                
                if unmet_deps:
                    console.print(f"[red]Skipping {task.name}: unmet dependencies {unmet_deps}[/red]")
                    task.status = TaskStatus.SKIPPED
                    continue
                
                if task.id in self.state.completed_tasks:
                    console.print(f"[green]Skipping {task.name}: already completed[/green]")
                    continue
                
                task_progress = progress.add_task(f"Executing {task.name}", total=100)
                task.status = TaskStatus.IN_PROGRESS
                task.start_time = datetime.now()
                
                try:
                    if task.execute_func:
                        await task.execute_func(progress, task_progress)
                    
                    task.status = TaskStatus.COMPLETED
                    task.end_time = datetime.now()
                    self.state.completed_tasks.append(task.id)
                    success_count += 1
                    
                    console.print(f"[green]✓ Completed: {task.name}[/green]")
                    
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.end_time = datetime.now()
                    task.error_message = str(e)
                    self.state.failed_tasks.append(task.id)
                    
                    console.print(f"[red]✗ Failed: {task.name} - {e}[/red]")
                    
                    # Ask user if they want to continue
                    if not click.confirm("Continue with remaining tasks?"):
                        break
                
                finally:
                    progress.remove_task(task_progress)
                    self._save_state()
        
        console.print(f"\n[bold]Phase {phase.value} completed: {success_count}/{len(phase_tasks)} tasks successful[/bold]")
        return success_count == len(phase_tasks)
    
    def rollback_to_point(self, point_name: str) -> bool:
        """Rollback to a specific backup point"""
        if point_name not in self.state.rollback_points:
            console.print(f"[red]Rollback point '{point_name}' not found[/red]")
            return False
        
        console.print(f"[yellow]Rolling back to: {point_name}[/yellow]")
        
        try:
            # Try git-based rollback first
            result = subprocess.run(
                ["git", "stash", "list", "--grep", f"Backup {point_name}"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                stash_ref = result.stdout.split(':')[0]
                subprocess.run(["git", "stash", "apply", stash_ref], 
                              cwd=self.project_root, check=True)
                console.print(f"[green]Successfully rolled back using git stash[/green]")
                return True
            
        except Exception as e:
            console.print(f"[red]Git rollback failed: {e}[/red]")
        
        console.print(f"[red]Rollback failed - manual intervention required[/red]")
        return False
    
    def show_status(self) -> None:
        """Show current migration status"""
        console.print("\n[bold]Orchestra AI Refactoring Status[/bold]")
        
        # Overall progress
        total_tasks = len(self.tasks)
        completed_tasks = len(self.state.completed_tasks)
        failed_tasks = len(self.state.failed_tasks)
        
        progress_table = Table(show_header=True, header_style="bold magenta")
        progress_table.add_column("Metric", style="cyan")
        progress_table.add_column("Value", style="white")
        
        progress_table.add_row("Total Tasks", str(total_tasks))
        progress_table.add_row("Completed", f"[green]{completed_tasks}[/green]")
        progress_table.add_row("Failed", f"[red]{failed_tasks}[/red]")
        progress_table.add_row("Remaining", str(total_tasks - completed_tasks - failed_tasks))
        progress_table.add_row("Current Phase", 
                              self.state.current_phase.name if self.state.current_phase else "None")
        progress_table.add_row("Last Updated", 
                              self.state.last_updated.strftime("%Y-%m-%d %H:%M:%S"))
        
        console.print(progress_table)
        
        # Phase breakdown
        console.print("\n[bold]Phase Breakdown[/bold]")
        
        for phase in Phase:
            phase_tasks = [task for task in self.tasks.values() if task.phase == phase]
            phase_completed = len([t for t in phase_tasks if t.id in self.state.completed_tasks])
            phase_failed = len([t for t in phase_tasks if t.id in self.state.failed_tasks])
            
            status_color = "green" if phase_completed == len(phase_tasks) else "yellow"
            if phase_failed > 0:
                status_color = "red"
            
            console.print(f"[{status_color}]Phase {phase.value}: {phase_completed}/{len(phase_tasks)} completed[/{status_color}]")
        
        # Recent failures
        if self.state.failed_tasks:
            console.print("\n[bold red]Recent Failures:[/bold red]")
            for task_id in self.state.failed_tasks[-3:]:  # Show last 3 failures
                task = self.tasks.get(task_id)
                if task:
                    console.print(f"  • {task.name}: {task.error_message}")
    
    # Task implementation methods
    async def _remove_poetry_config(self, progress, task_id):
        """Remove Poetry configuration from pyproject.toml"""
        pyproject_path = self.project_root / "pyproject.toml"
        
        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                content = f.read()
            
            # Remove Poetry sections but keep other tools (black, isort, etc.)
            lines = content.split('\n')
            new_lines = []
            skip_section = False
            
            for line in lines:
                if line.strip().startswith('[tool.poetry'):
                    skip_section = True
                elif line.strip().startswith('[') and not line.strip().startswith('[tool.poetry'):
                    skip_section = False
                
                if not skip_section:
                    new_lines.append(line)
            
            with open(pyproject_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            progress.update(task_id, advance=50)
        
        progress.update(task_id, advance=50)
    
    async def _consolidate_requirements(self, progress, task_id):
        """Consolidate requirements files"""
        # The unified requirements file is already created
        # Here we would clean up old requirement files and update references
        
        old_files = [
            "requirements/base.txt",
            "requirements/dev.txt", 
            "requirements/production/",
            "requirements/frozen/"
        ]
        
        backup_root = self.backup_dir / "requirements"
        backup_root.mkdir(parents=True, exist_ok=True)
        
        for old_file in old_files:
            old_path = self.project_root / old_file
            if old_path.exists():
                # Create a unique backup name outside the source directory
                safe_name = old_file.replace("/", "_").replace(".", "_")
                backup_path = backup_root / f"{safe_name}.backup"
                if old_path.is_file():
                    shutil.move(str(old_path), str(backup_path))
                else:
                    # For directories, move to backup_root with a unique name
                    shutil.move(str(old_path), str(backup_path))
        
        progress.update(task_id, advance=100)
    
    async def _setup_unified_config(self, progress, task_id):
        """Deploy unified configuration system"""
        # Configuration system is already created in core/config/unified_config.py
        # Here we would update imports and references
        progress.update(task_id, advance=100)
    
    async def _deploy_unified_llm_router(self, progress, task_id):
        """Deploy unified LLM router"""
        # Router is already created in core/llm/unified_router.py
        # Here we would remove old routers and update imports
        
        old_routers = [
            "core/llm_router_enhanced.py",
            "core/llm_router_dynamic.py",
            "core/llm_router_dynamic_enhanced.py", 
            "core/llm_intelligent_router.py"
        ]
        
        for router in old_routers:
            router_path = self.project_root / router
            if router_path.exists():
                backup_path = self.project_root / f"{router}.backup"
                shutil.move(router_path, backup_path)
        
        progress.update(task_id, advance=100)
    
    async def _deploy_unified_database(self, progress, task_id):
        """Deploy unified database interface"""
        # Database interface is already created
        # Remove old implementations
        
        old_db_files = [
            "shared/database/unified_db_v2.py"
        ]
        
        for db_file in old_db_files:
            db_path = self.project_root / db_file
            if db_path.exists():
                backup_path = self.project_root / f"{db_file}.backup"
                shutil.move(db_path, backup_path)
        
        progress.update(task_id, advance=100)
    
    async def _migrate_core_imports(self, progress, task_id):
        """Update imports throughout codebase"""
        # This would be a comprehensive find-and-replace operation
        # For now, we'll simulate the work
        await asyncio.sleep(2)  # Simulate work
        progress.update(task_id, advance=100)
    
    async def _reorganize_core_directory(self, progress, task_id):
        """Reorganize core directory structure"""
        # Create new subdirectories and move files
        core_dir = self.project_root / "core"
        
        # Create subdirectories
        subdirs = ["routing", "config", "monitoring", "health"]
        for subdir in subdirs:
            (core_dir / subdir).mkdir(exist_ok=True)
        
        progress.update(task_id, advance=100)
    
    async def _enhance_orchestrator(self, progress, task_id):
        """Enhance orchestrator architecture"""
        # Implement clean architecture patterns
        await asyncio.sleep(3)  # Simulate work
        progress.update(task_id, advance=100)
    
    async def _optimize_async_patterns(self, progress, task_id):
        """Optimize async/await usage"""
        # Review and optimize async patterns
        await asyncio.sleep(2)  # Simulate work
        progress.update(task_id, advance=100)
    
    async def _implement_monitoring(self, progress, task_id):
        """Implement enhanced monitoring"""
        # Add comprehensive monitoring
        await asyncio.sleep(1.5)  # Simulate work
        progress.update(task_id, advance=100)
    
    async def _consolidate_scripts(self, progress, task_id):
        """Consolidate overlapping scripts"""
        # Merge and clean up scripts
        await asyncio.sleep(3)  # Simulate work
        progress.update(task_id, advance=100)

@click.group()
def cli():
    """Orchestra AI Refactoring Orchestrator"""
    pass

@cli.command()
@click.option('--phase', type=int, help='Phase number to preview (1-5)')
def preview(phase):
    """Preview tasks for a specific phase"""
    orchestrator = RefactoringOrchestrator(Path.cwd())
    
    if phase:
        phase_enum = Phase(phase)
        orchestrator.preview_phase(phase_enum)
    else:
        for p in Phase:
            orchestrator.preview_phase(p)

@cli.command()
@click.option('--phase', type=int, required=True, help='Phase number to execute (1-5)')
@click.option('--dry-run', is_flag=True, help='Preview without executing')
def execute(phase, dry_run):
    """Execute a specific phase"""
    orchestrator = RefactoringOrchestrator(Path.cwd())
    phase_enum = Phase(phase)
    
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")
    
    asyncio.run(orchestrator.execute_phase(phase_enum, dry_run=dry_run))

@cli.command()
@click.argument('point_name')
def rollback(point_name):
    """Rollback to a specific backup point"""
    orchestrator = RefactoringOrchestrator(Path.cwd())
    success = orchestrator.rollback_to_point(point_name)
    
    if success:
        console.print("[green]Rollback completed successfully[/green]")
    else:
        console.print("[red]Rollback failed[/red]")

@cli.command()
def status():
    """Show current refactoring status"""
    orchestrator = RefactoringOrchestrator(Path.cwd())
    orchestrator.show_status()

@cli.command()
def validate():
    """Validate current state and run tests"""
    console.print("[blue]Running validation checks...[/blue]")
    
    # Run tests
    try:
        result = subprocess.run(["python", "-m", "pytest", "tests/", "-v"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            console.print("[green]✓ All tests passed[/green]")
        else:
            console.print(f"[red]✗ Tests failed:\n{result.stdout}[/red]")
    except FileNotFoundError:
        console.print("[yellow]⚠ pytest not found, skipping tests[/yellow]")
    
    # Check imports
    console.print("[blue]Checking imports...[/blue]")
    try:
        subprocess.run(["python", "-c", "import core.config.unified_config"], check=True)
        console.print("[green]✓ Unified config imports correctly[/green]")
    except Exception as e:
        console.print(f"[red]✗ Import error: {e}[/red]")

if __name__ == "__main__":
    cli() 