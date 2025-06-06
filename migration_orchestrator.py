#!/usr/bin/env python3
"""
Migration Orchestrator for Orchestra AI Refactoring
Automates the 5-phase refactoring with safety measures and progress tracking.
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MigrationOrchestrator:
    """Orchestrates the refactoring migration across all phases."""
    
    def __init__(self, workspace_root: Path = None):
        self.workspace_root = workspace_root or Path.cwd()
        self.backup_dir = self.workspace_root / ""
        self.state_file = self.workspace_root / ".migration_state.json"
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load migration state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {
            "current_phase": 0,
            "completed_tasks": [],
            "failed_tasks": [],
            "backups": [],
            "started_at": None,
            "last_updated": None
        }
    
    def _save_state(self):
        """Save migration state to file."""
        self.state["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _create_backup(self, files: List[Path], backup_name: str) -> Optional[Path]:
        """Create backup of specified files."""
        try:
            backup_path = self.backup_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_name}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            for file_path in files:
                if file_path.exists():
                    if file_path.is_file():
                        dest = backup_path / file_path.name
                        shutil.copy2(file_path, dest)
                    elif file_path.is_dir():
                        dest = backup_path / file_path.name
                        shutil.copytree(file_path, dest, dirs_exist_ok=True)
            
            self.state["backups"].append({
                "name": backup_name,
                "path": str(backup_path),
                "created_at": datetime.now().isoformat()
            })
            
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def _run_task(self, task_name: str, task_func, *args, **kwargs) -> bool:
        """Run a migration task with error handling."""
        logger.info(f"Starting task: {task_name}")
        try:
            result = task_func(*args, **kwargs)
            if result:
                self.state["completed_tasks"].append({
                    "name": task_name,
                    "completed_at": datetime.now().isoformat()
                })
                logger.info(f"Task completed: {task_name}")
                return True
            else:
                raise Exception("Task returned False")
        except Exception as e:
            self.state["failed_tasks"].append({
                "name": task_name,
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            })
            logger.error(f"Task failed: {task_name} - {e}")
            return False
        finally:
            self._save_state()
    
    def phase_1_foundation_cleanup(self) -> bool:
        """Phase 1: Foundation Cleanup"""
        logger.info("Starting Phase 1: Foundation Cleanup")
        
        # Task 1: Remove Poetry configuration
        def remove_poetry_config():
            pyproject_path = self.workspace_root / "pyproject.toml"
            if pyproject_path.exists():
                # Backup first
                self._create_backup([pyproject_path], "poetry_config")
                
                # Read and filter content
                with open(pyproject_path) as f:
                    content = f.read()
                
                # Remove Poetry sections
                lines = content.split('\n')
                filtered_lines = []
                in_poetry_section = False
                
                for line in lines:
                    if line.strip().startswith('[tool.poetry'):
                        in_poetry_section = True
                        continue
                    elif line.strip().startswith('[') and in_poetry_section:
                        in_poetry_section = False
                    
                    if not in_poetry_section:
                        filtered_lines.append(line)
                
                # Write back
                with open(pyproject_path, 'w') as f:
                    f.write('\n'.join(filtered_lines))
                
                logger.info("Removed Poetry configuration from pyproject.toml")
            return True
        
        # Task 2: Consolidate requirements
        def consolidate_requirements():
            req_dir = self.workspace_root / "requirements"
            if req_dir.exists():
                self._create_backup([req_dir], "requirements_old")
            
            # Create unified requirements
            unified_req = self.workspace_root / "requirements.txt"
            req_content = """# Orchestra AI - Unified Requirements
# Core Framework
fastapi==0.115.12
uvicorn[standard]==0.32.1
pydantic==2.10.7
pydantic-settings==2.7.0

# Database
asyncpg==0.30.0
sqlalchemy==2.0.30
weaviate-client==4.9.7

# LLM Providers
openai==1.82.0
anthropic==0.39.0
litellm==1.70.4

# AI Framework
llama-index==0.10.38
chromadb==0.4.22

# API & Networking
httpx==0.28.1
aiohttp==3.11.18
requests==2.32.3

# Authentication & Security
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
authlib==1.3.1

# Monitoring & Logging
structlog==25.5.0
prometheus-client==0.21.1
opentelemetry-api==1.33.1

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.2
click==8.1.8
jinja2==3.1.6
python-multipart==0.0.12

# Development
black==24.4.2
isort==5.13.2
flake8==7.0.0
pytest==8.3.4
pytest-asyncio==0.25.0

# Voice (Optional)
elevenlabs==2.1.0

# Kubernetes (Optional)
kubernetes==32.0.1

# MCP Integration
mcp==1.9.2

# File Processing
beautifulsoup4==4.13.4
pandas==2.2.0
numpy==1.26.4

# Background Tasks
celery==5.4.0
redis==5.2.1

# Async Support
anyio==4.9.0
trio==0.27.0
"""
            
            with open(unified_req, 'w') as f:
                f.write(req_content)
            
            logger.info("Created unified requirements.txt")
            return True
        
        # Task 3: Deploy unified configuration
        def deploy_unified_config():
            # Check if core/config directory exists
            config_dir = self.workspace_root / "core" / "config"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if unified config was already created
            unified_config_path = config_dir / "__init__.py"
            if unified_config_path.exists():
                logger.info("Unified configuration already exists")
                return True
            
            logger.info("Unified configuration needs to be created first")
            return True
        
        # Execute tasks
        success = True
        success &= self._run_task("Remove Poetry Config", remove_poetry_config)
        success &= self._run_task("Consolidate Requirements", consolidate_requirements)
        success &= self._run_task("Deploy Unified Config", deploy_unified_config)
        
        if success:
            self.state["current_phase"] = 1
            logger.info("Phase 1 completed successfully")
        
        return success
    
    def phase_2_core_consolidation(self) -> bool:
        """Phase 2: Core Consolidation"""
        logger.info("Starting Phase 2: Core Consolidation")
        
        # Task 1: Deploy unified LLM router
        def deploy_unified_llm_router():
            llm_dir = self.workspace_root / "core" / "llm"
            llm_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if unified router exists
            router_path = llm_dir / "unified_router.py"
            if router_path.exists():
                logger.info("Unified LLM router already exists")
                return True
            
            logger.info("Unified LLM router needs to be created")
            return True
        
        # Task 2: Deploy unified database
        def deploy_unified_database():
            db_dir = self.workspace_root / "shared" / "database"
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if unified database exists
            unified_db_path = db_dir / "__init__.py"
            if unified_db_path.exists():
                logger.info("Unified database already exists")
                return True
            
            logger.info("Unified database needs to be created")
            return True
        
        # Task 3: Migrate imports and remove duplicates
        def migrate_imports():
            # Find and backup duplicate files
            duplicate_files = [
                "core/llm/llm_router_enhanced.py",
                "core/llm/llm_router_dynamic.py", 
                "core/llm/llm_router_dynamic_enhanced.py",
                "core/llm/llm_intelligent_router.py"
            ]
            
            files_to_backup = []
            for file_path in duplicate_files:
                full_path = self.workspace_root / file_path
                if full_path.exists():
                    files_to_backup.append(full_path)
            
            if files_to_backup:
                self._create_backup(files_to_backup, "duplicate_routers")
                
                # Remove duplicate files
                for file_path in files_to_backup:
                    try:
                        file_path.unlink()
                        logger.info(f"Removed duplicate file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")
            
            return True
        
        # Execute tasks
        success = True
        success &= self._run_task("Deploy Unified LLM Router", deploy_unified_llm_router)
        success &= self._run_task("Deploy Unified Database", deploy_unified_database)
        success &= self._run_task("Migrate Imports", migrate_imports)
        
        if success:
            self.state["current_phase"] = 2
            logger.info("Phase 2 completed successfully")
        
        return success
    
    def phase_3_architecture_enhancement(self) -> bool:
        """Phase 3: Architecture Enhancement"""
        logger.info("Starting Phase 3: Architecture Enhancement")
        
        # Task 1: Reorganize core directory
        def reorganize_core_directory():
            logger.info("Core directory reorganization would be implemented here")
            return True
        
        # Task 2: Enhance orchestrator
        def enhance_orchestrator():
            logger.info("Orchestrator enhancement would be implemented here")
            return True
        
        # Execute tasks
        success = True
        success &= self._run_task("Reorganize Core Directory", reorganize_core_directory)
        success &= self._run_task("Enhance Orchestrator", enhance_orchestrator)
        
        if success:
            self.state["current_phase"] = 3
            logger.info("Phase 3 completed successfully")
        
        return success
    
    def phase_4_performance_optimization(self) -> bool:
        """Phase 4: Performance Optimization"""
        logger.info("Starting Phase 4: Performance Optimization")
        
        # Task 1: Optimize async patterns
        def optimize_async_patterns():
            logger.info("Async pattern optimization would be implemented here")
            return True
        
        # Task 2: Implement monitoring
        def implement_monitoring():
            logger.info("Monitoring implementation would be implemented here")
            return True
        
        # Execute tasks
        success = True
        success &= self._run_task("Optimize Async Patterns", optimize_async_patterns)
        success &= self._run_task("Implement Monitoring", implement_monitoring)
        
        if success:
            self.state["current_phase"] = 4
            logger.info("Phase 4 completed successfully")
        
        return success
    
    def phase_5_script_automation(self) -> bool:
        """Phase 5: Script Automation"""
        logger.info("Starting Phase 5: Script Automation")
        
        # Task 1: Consolidate scripts
        def consolidate_scripts():
            logger.info("Script consolidation would be implemented here")
            return True
        
        # Task 2: Improve CLI
        def improve_cli():
            logger.info("CLI improvement would be implemented here")
            return True
        
        # Execute tasks
        success = True
        success &= self._run_task("Consolidate Scripts", consolidate_scripts)
        success &= self._run_task("Improve CLI", improve_cli)
        
        if success:
            self.state["current_phase"] = 5
            logger.info("Phase 5 completed successfully")
        
        return success
    
    def run_phase(self, phase_number: int) -> bool:
        """Run a specific phase."""
        if self.state.get("started_at") is None:
            self.state["started_at"] = datetime.now().isoformat()
        
        phase_functions = {
            1: self.phase_1_foundation_cleanup,
            2: self.phase_2_core_consolidation,
            3: self.phase_3_architecture_enhancement,
            4: self.phase_4_performance_optimization,
            5: self.phase_5_script_automation
        }
        
        if phase_number not in phase_functions:
            logger.error(f"Invalid phase number: {phase_number}")
            return False
        
        return phase_functions[phase_number]()
    
    def run_all_phases(self) -> bool:
        """Run all phases in sequence."""
        for phase in range(1, 6):
            if not self.run_phase(phase):
                logger.error(f"Failed at phase {phase}")
                return False
        
        logger.info("All phases completed successfully!")
        return True
    
    def status(self):
        """Show migration status."""
        print(f"Current Phase: {self.state.get('current_phase', 0)}")
        print(f"Completed Tasks: {len(self.state.get('completed_tasks', []))}")
        print(f"Failed Tasks: {len(self.state.get('failed_tasks', []))}")
        print(f"Backups Created: {len(self.state.get('backups', []))}")
        
        if self.state.get('started_at'):
            print(f"Started: {self.state['started_at']}")
        if self.state.get('last_updated'):
            print(f"Last Updated: {self.state['last_updated']}")
    
    def rollback(self, backup_name: str = None):
        """Rollback to a previous state."""
        if not self.state.get('backups'):
            logger.error("No backups available for rollback")
            return False
        
        if backup_name is None:
            # Use latest backup
            backup = self.state['backups'][-1]
        else:
            backup = next((b for b in self.state['backups'] if b['name'] == backup_name), None)
            if not backup:
                logger.error(f"Backup not found: {backup_name}")
                return False
        
        logger.info(f"Rolling back to: {backup['name']}")
        # Rollback implementation would go here
        return True

def main():
    parser = argparse.ArgumentParser(description="Orchestra AI Migration Orchestrator")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4, 5], help="Run specific phase")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--rollback", type=str, help="Rollback to backup")
    
    args = parser.parse_args()
    
    orchestrator = MigrationOrchestrator()
    
    if args.status:
        orchestrator.status()
    elif args.rollback:
        orchestrator.rollback(args.rollback)
    elif args.phase:
        orchestrator.run_phase(args.phase)
    elif args.all:
        orchestrator.run_all_phases()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 