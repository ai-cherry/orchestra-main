#!/usr/bin/env python3
"""
Migration script for AI Orchestra System

This script facilitates migration to the AI Orchestra System by:
1. Analyzing existing resources, files, and configuration
2. Creating a migration plan for moving to the centralized system
3. Executing the migration according to the plan
4. Validating the migration was successful

Usage:
    python -m orchestra_system.migrate [options]

Options:
    --analyze       Analyze existing environment (default)
    --plan          Create migration plan
    --execute       Execute migration plan
    --validate      Validate migration
    --report        Generate migration report
    --rollback      Rollback migration if issues are found
    --all           Run complete migration process
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestra-migrate")

# Add parent directory to path to import orchestra_system
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

# Import orchestra_system components
try:
    from orchestra_system.api import get_api, initialize_system
    from orchestra_system.resource_registry import get_registry
    from orchestra_system.config_manager import get_manager
    from orchestra_system.conflict_resolver import get_resolver
except ImportError as e:
    logger.error(f"Failed to import orchestra_system: {e}")
    logger.error("Make sure the package is installed or in your PYTHONPATH")
    sys.exit(1)


class MigrationAnalysis:
    """Analysis of the environment for migration."""
    
    def __init__(self):
        """Initialize the analysis."""
        self.api = get_api()
        self.registry = get_registry()
        self.config_manager = get_manager()
        self.conflict_resolver = get_resolver()
        
        # Analysis results
        self.resources = []
        self.config_entries = {}
        self.conflicts = []
        self.existing_files = []
        self.migration_items = []
        self.timestamp = datetime.now().isoformat()
    
    async def analyze(self) -> Dict[str, Any]:
        """Analyze the environment.
        
        Returns:
            Analysis results
        """
        logger.info("Analyzing environment for migration...")
        
        # Discover resources
        self.resources = await self.api.discover_resources()
        logger.info(f"Found {len(self.resources)} resources")
        
        # Discover configuration
        self.config_entries = self.api.get_all_configuration()
        logger.info(f"Found {len(self.config_entries)} configuration entries")
        
        # Detect conflicts
        self.conflicts = self.api.detect_conflicts()
        logger.info(f"Found {len(self.conflicts)} conflicts")
        
        # Find existing integration files
        self.existing_files = self._find_existing_files()
        logger.info(f"Found {len(self.existing_files)} existing integration files")
        
        # Identify migration items
        self.migration_items = self._identify_migration_items()
        logger.info(f"Identified {len(self.migration_items)} items to migrate")
        
        # Generate analysis report
        report = {
            "timestamp": self.timestamp,
            "resources_count": len(self.resources),
            "config_count": len(self.config_entries),
            "conflicts_count": len(self.conflicts),
            "existing_files_count": len(self.existing_files),
            "migration_items_count": len(self.migration_items),
            "resources": self.resources,
            "config_entries": self.config_entries,
            "conflicts": self.conflicts,
            "existing_files": self.existing_files,
            "migration_items": self.migration_items
        }
        
        return report
    
    def _find_existing_files(self) -> List[Dict[str, Any]]:
        """Find existing integration files.
        
        Returns:
            List of existing files
        """
        existing_files = []
        
        # Look for configuration files
        config_patterns = [
            ".env",
            "config.json",
            "config.yaml",
            "config.yml",
            "settings.json",
            "terraform/variables.tf"
        ]
        
        # Look for tool registries
        tool_registry_patterns = [
            "gcp_migration/tool_registry.py",
            "tool_registry.py",
            "*tool_registry*.py"
        ]
        
        # Look for MCP clients
        mcp_client_patterns = [
            "gcp_migration/mcp_client*.py",
            "mcp_client*.py"
        ]
        
        # Function to find files matching patterns
        def find_files(patterns):
            found_files = []
            for pattern in patterns:
                # Handle exact matches
                if "*" not in pattern:
                    if os.path.exists(pattern):
                        found_files.append({
                            "path": pattern,
                            "size": os.path.getsize(pattern),
                            "modified": datetime.fromtimestamp(os.path.getmtime(pattern)).isoformat()
                        })
                else:
                    # Handle wildcard patterns
                    import glob
                    for path in glob.glob(pattern):
                        if os.path.isfile(path):
                            found_files.append({
                                "path": path,
                                "size": os.path.getsize(path),
                                "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                            })
            return found_files
        
        # Find all matching files
        existing_files.extend(find_files(config_patterns))
        existing_files.extend(find_files(tool_registry_patterns))
        existing_files.extend(find_files(mcp_client_patterns))
        
        return existing_files
    
    def _identify_migration_items(self) -> List[Dict[str, Any]]:
        """Identify items to migrate.
        
        Returns:
            List of migration items
        """
        migration_items = []
        
        # Function to add migration item
        def add_item(item_type, source, destination=None, description=None, priority="medium"):
            migration_items.append({
                "type": item_type,
                "source": source,
                "destination": destination,
                "description": description or f"Migrate {item_type} from {source}",
                "priority": priority
            })
        
        # Migrate configuration files
        for file in self.existing_files:
            path = file["path"]
            if path.endswith((".json", ".yaml", ".yml", ".env")):
                add_item(
                    "configuration",
                    path,
                    None,
                    f"Import configuration from {path}",
                    "high"
                )
            elif "tool_registry" in path:
                add_item(
                    "tool_registry",
                    path,
                    None,
                    f"Migrate tool registry from {path}",
                    "high"
                )
            elif "mcp_client" in path:
                add_item(
                    "mcp_client",
                    path,
                    None,
                    f"Migrate MCP client integration from {path}",
                    "medium"
                )
        
        # Add system initialization
        add_item(
            "system_initialization",
            None,
            None,
            "Initialize the Orchestra System",
            "critical"
        )
        
        # Add resource discovery
        add_item(
            "resource_discovery",
            None,
            None,
            "Discover all available resources",
            "high"
        )
        
        return migration_items


class MigrationPlanner:
    """Planner for migration to Orchestra System."""
    
    def __init__(self, analysis: Optional[MigrationAnalysis] = None):
        """Initialize the planner.
        
        Args:
            analysis: Optional analysis to use
        """
        self.api = get_api()
        self.analysis = analysis or MigrationAnalysis()
        
        # Plan details
        self.steps = []
        self.backup_paths = []
        self.created_files = []
        self.timestamp = datetime.now().isoformat()
    
    async def create_plan(self, analysis_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a migration plan.
        
        Args:
            analysis_report: Optional analysis report to use
            
        Returns:
            Migration plan
        """
        logger.info("Creating migration plan...")
        
        # Run analysis if not provided
        if not analysis_report:
            analysis_report = await self.analysis.analyze()
        
        # Extract migration items
        migration_items = analysis_report.get("migration_items", [])
        
        # Create steps
        self._create_initialization_steps()
        self._create_backup_steps()
        self._create_migration_steps(migration_items)
        self._create_validation_steps()
        
        # Generate plan
        plan = {
            "timestamp": self.timestamp,
            "steps": self.steps,
            "backup_paths": self.backup_paths,
            "analysis": analysis_report
        }
        
        logger.info(f"Created migration plan with {len(self.steps)} steps")
        
        return plan
    
    def _create_initialization_steps(self):
        """Create steps for system initialization."""
        self.steps.append({
            "id": "init_system",
            "name": "Initialize Orchestra System",
            "description": "Initialize the system components",
            "command": "python -m orchestra_system.setup --init",
            "priority": "critical",
            "dependencies": []
        })
    
    def _create_backup_steps(self):
        """Create steps for backing up existing files."""
        # Create backup directory
        backup_dir = f"orchestra_migration_backup_{int(time.time())}"
        self.backup_paths.append(backup_dir)
        
        self.steps.append({
            "id": "create_backup_dir",
            "name": "Create backup directory",
            "description": f"Create directory for backups: {backup_dir}",
            "command": f"mkdir -p {backup_dir}",
            "priority": "critical",
            "dependencies": []
        })
        
        # Add backup steps for existing files
        if hasattr(self.analysis, "existing_files"):
            for i, file in enumerate(self.analysis.existing_files):
                path = file["path"]
                backup_path = f"{backup_dir}/{Path(path).name}"
                
                self.steps.append({
                    "id": f"backup_file_{i}",
                    "name": f"Backup {path}",
                    "description": f"Copy {path} to {backup_path}",
                    "command": f"cp {path} {backup_path}",
                    "priority": "high",
                    "dependencies": ["create_backup_dir"]
                })
    
    def _create_migration_steps(self, migration_items: List[Dict[str, Any]]):
        """Create steps for migrating items.
        
        Args:
            migration_items: Items to migrate
        """
        for i, item in enumerate(migration_items):
            item_type = item["type"]
            source = item["source"]
            description = item["description"]
            priority = item["priority"]
            
            if item_type == "configuration" and source:
                # Import configuration
                self.steps.append({
                    "id": f"migrate_config_{i}",
                    "name": f"Import configuration from {source}",
                    "description": description,
                    "command": f"python -m orchestra_system.setup --config --output migration_config_{i}.json",
                    "priority": priority,
                    "dependencies": ["init_system"]
                })
            
            elif item_type == "tool_registry" and source:
                # Migrate tool registry
                self.steps.append({
                    "id": f"migrate_tool_registry_{i}",
                    "name": f"Migrate tool registry from {source}",
                    "description": description,
                    "command": "python -m orchestra_system.setup --discover --output migration_tools_{i}.json",
                    "priority": priority,
                    "dependencies": ["init_system"]
                })
            
            elif item_type == "mcp_client" and source:
                # Migrate MCP client
                self.steps.append({
                    "id": f"migrate_mcp_client_{i}",
                    "name": f"Migrate MCP client from {source}",
                    "description": description,
                    "command": "python -m orchestra_system.setup --integration --output migration_mcp_{i}.json",
                    "priority": priority,
                    "dependencies": ["init_system"]
                })
            
            elif item_type == "system_initialization":
                # Already handled in _create_initialization_steps
                pass
            
            elif item_type == "resource_discovery":
                # Discover resources
                self.steps.append({
                    "id": f"discover_resources_{i}",
                    "name": "Discover resources",
                    "description": description,
                    "command": "python -m orchestra_system.setup --discover --output migration_resources.json",
                    "priority": priority,
                    "dependencies": ["init_system"]
                })
    
    def _create_validation_steps(self):
        """Create steps for validating the migration."""
        self.steps.append({
            "id": "validate_migration",
            "name": "Validate migration",
            "description": "Validate the migration was successful",
            "command": "python -m orchestra_system.migrate --validate --output migration_validation.json",
            "priority": "high",
            "dependencies": [s["id"] for s in self.steps if s["id"] != "validate_migration"]
        })
        
        self.steps.append({
            "id": "generate_report",
            "name": "Generate migration report",
            "description": "Generate a comprehensive migration report",
            "command": "python -m orchestra_system.migrate --report --output migration_report.json",
            "priority": "medium",
            "dependencies": ["validate_migration"]
        })


class MigrationExecutor:
    """Executor for migration to Orchestra System."""
    
    def __init__(self, plan: Optional[Dict[str, Any]] = None):
        """Initialize the executor.
        
        Args:
            plan: Optional migration plan to use
        """
        self.api = get_api()
        self.plan = plan
        
        # Execution state
        self.executed_steps = []
        self.failed_steps = []
        self.timestamp = datetime.now().isoformat()
    
    async def execute_plan(self, plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a migration plan.
        
        Args:
            plan: Optional migration plan to use
            
        Returns:
            Execution results
        """
        logger.info("Executing migration plan...")
        
        # Use provided plan or existing one
        plan = plan or self.plan
        if not plan:
            logger.error("No migration plan provided")
            raise ValueError("No migration plan provided")
        
        steps = plan.get("steps", [])
        
        # Sort steps by dependencies
        sorted_steps = self._sort_steps_by_dependencies(steps)
        
        # Execute steps
        for step in sorted_steps:
            step_id = step["id"]
            name = step["name"]
            command = step["command"]
            
            logger.info(f"Executing step {step_id}: {name}")
            
            try:
                # Execute command
                import subprocess
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                # Check result
                if result.returncode == 0:
                    logger.info(f"Step {step_id} completed successfully")
                    self.executed_steps.append({
                        "id": step_id,
                        "name": name,
                        "success": True,
                        "output": result.stdout,
                        "executed_at": datetime.now().isoformat()
                    })
                else:
                    logger.error(f"Step {step_id} failed: {result.stderr}")
                    self.failed_steps.append({
                        "id": step_id,
                        "name": name,
                        "success": False,
                        "error": result.stderr,
                        "executed_at": datetime.now().isoformat()
                    })
            
            except Exception as e:
                logger.error(f"Step {step_id} failed with exception: {e}")
                self.failed_steps.append({
                    "id": step_id,
                    "name": name,
                    "success": False,
                    "error": str(e),
                    "executed_at": datetime.now().isoformat()
                })
        
        # Generate execution report
        execution_report = {
            "timestamp": self.timestamp,
            "executed_steps": self.executed_steps,
            "failed_steps": self.failed_steps,
            "success": len(self.failed_steps) == 0,
            "plan": plan
        }
        
        logger.info(f"Migration execution completed with "
                   f"{len(self.executed_steps)} successful steps and "
                   f"{len(self.failed_steps)} failed steps")
        
        return execution_report
    
    def _sort_steps_by_dependencies(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort steps by dependencies.
        
        Args:
            steps: Steps to sort
            
        Returns:
            Sorted steps
        """
        # Create dependency graph
        graph = {}
        for step in steps:
            step_id = step["id"]
            dependencies = step.get("dependencies", [])
            graph[step_id] = dependencies
        
        # Perform topological sort
        visited = set()
        temp = set()
        result = []
        
        def visit(node):
            if node in temp:
                raise ValueError(f"Circular dependency detected for step {node}")
            if node in visited:
                return
            
            temp.add(node)
            
            # Visit dependencies
            for dependency in graph.get(node, []):
                visit(dependency)
            
            temp.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visit all nodes
        for step_id in graph:
            if step_id not in visited:
                visit(step_id)
        
        # Map step IDs back to steps
        step_map = {step["id"]: step for step in steps}
        return [step_map[step_id] for step_id in result]
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate the migration.
        
        Returns:
            Validation results
        """
        logger.info("Validating migration...")
        
        # Initialize system
        state = await self.api.initialize_system()
        
        # Check resources
        resources = await self.api.get_resources()
        resource_count = len(resources)
        
        # Check configuration
        config = self.api.get_all_configuration()
        config_count = len(config)
        
        # Check for conflicts
        conflicts = self.api.get_conflicts()
        conflict_count = len(conflicts)
        
        # Get system context
        context = await self.api.get_context()
        
        # Generate validation report
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "system_state": state,
            "resource_count": resource_count,
            "config_count": config_count,
            "conflict_count": conflict_count,
            "context": context,
            "success": resource_count > 0 and conflict_count == 0,
            "issues": []
        }
        
        # Check for issues
        if resource_count == 0:
            validation_report["issues"].append("No resources found")
        
        if conflict_count > 0:
            validation_report["issues"].append(f"Found {conflict_count} conflicts")
        
        logger.info(f"Validation completed with "
                   f"{resource_count} resources, "
                   f"{config_count} configurations, and "
                   f"{conflict_count} conflicts")
        
        return validation_report
    
    async def rollback_migration(self, backup_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Rollback the migration.
        
        Args:
            backup_paths: Optional backup paths to use
            
        Returns:
            Rollback results
        """
        logger.info("Rolling back migration...")
        
        # Use backup paths from plan
        if not backup_paths and self.plan:
            backup_paths = self.plan.get("backup_paths", [])
        
        if not backup_paths:
            logger.error("No backup paths provided for rollback")
            return {"success": False, "error": "No backup paths provided"}
        
        restored_files = []
        failed_files = []
        
        # Restore files from backup
        for backup_path in backup_paths:
            if not os.path.exists(backup_path):
                logger.error(f"Backup path not found: {backup_path}")
                continue
            
            if os.path.isdir(backup_path):
                # Restore files from backup directory
                for root, _, files in os.walk(backup_path):
                    for file in files:
                        src = os.path.join(root, file)
                        dest = os.path.join(os.path.basename(backup_path), file)
                        
                        try:
                            shutil.copy(src, dest)
                            restored_files.append(dest)
                            logger.info(f"Restored {dest} from backup")
                        except Exception as e:
                            logger.error(f"Failed to restore {dest}: {e}")
                            failed_files.append({"path": dest, "error": str(e)})
            else:
                # Single file backup
                try:
                    dest = os.path.basename(backup_path)
                    shutil.copy(backup_path, dest)
                    restored_files.append(dest)
                    logger.info(f"Restored {dest} from backup")
                except Exception as e:
                    logger.error(f"Failed to restore {dest}: {e}")
                    failed_files.append({"path": dest, "error": str(e)})
        
        # Generate rollback report
        rollback_report = {
            "timestamp": datetime.now().isoformat(),
            "restored_files": restored_files,
            "failed_files": failed_files,
            "success": len(restored_files) > 0 and len(failed_files) == 0
        }
        
        logger.info(f"Rollback completed with "
                   f"{len(restored_files)} restored files and "
                   f"{len(failed_files)} failed files")
        
        return rollback_report
    
    async def generate_report(
        self,
        execution_report: Optional[Dict[str, Any]] = None,
        validation_report: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive migration report.
        
        Args:
            execution_report: Optional execution report to use
            validation_report: Optional validation report to use
            
        Returns:
            Migration report
        """
        logger.info("Generating migration report...")
        
        # Validate migration if not provided
        if not validation_report:
            validation_report = await self.validate_migration()
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "execution": execution_report,
            "validation": validation_report,
            "system_state": validation_report.get("system_state", {}),
            "success": validation_report.get("success", False),
            "issues": validation_report.get("issues", []),
            "resources": {
                "count": validation_report.get("resource_count", 0),
                "details": await self.api.get_resources()
            },
            "configuration": {
                "count": validation_report.get("config_count", 0),
                "details": self.api.get_all_configuration()
            },
            "conflicts": {
                "count": validation_report.get("conflict_count", 0),
                "details": self.api.get_conflicts()
            }
        }
        
        logger.info("Migration report generated successfully")
        
        return report


async def run_analysis() -> Dict[str, Any]:
    """Run migration analysis.
    
    Returns:
        Analysis report
    """
    analysis = MigrationAnalysis()
    return await analysis.analyze()


async def create_plan(analysis_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create migration plan.
    
    Args:
        analysis_report: Optional analysis report to use
        
    Returns:
        Migration plan
    """
    planner = MigrationPlanner()
    return await planner.create_plan(analysis_report)


async def execute_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute migration plan.
    
    Args:
        plan: Migration plan to execute
        
    Returns:
        Execution report
    """
    executor = MigrationExecutor(plan)
    return await executor.execute_plan()


async def validate_migration() -> Dict[str, Any]:
    """Validate migration.
    
    Returns:
        Validation report
    """
    executor = MigrationExecutor()
    return await executor.validate_migration()


async def rollback_migration(backup_paths: List[str]) -> Dict[str, Any]:
    """Rollback migration.
    
    Args:
        backup_paths: Backup paths to use
        
    Returns:
        Rollback report
    """
    executor = MigrationExecutor()
    return await executor.rollback_migration(backup_paths)


async def generate_report(
    execution_report: Optional[Dict[str, Any]] = None,
    validation_report: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Generate migration report.
    
    Args:
        execution_report: Optional execution report to use
        validation_report: Optional validation report to use
        
    Returns:
        Migration report
    """
    executor = MigrationExecutor()
    return await executor.generate_report(execution_report, validation_report)


async def run_complete_migration() -> Dict[str, Any]:
    """Run complete migration process.
    
    Returns:
        Migration report
    """
    logger.info("Starting complete migration process...")
    
    # Analyze environment
    analysis_report = await run_analysis()
    
    # Create plan
    plan = await create_plan(analysis_report)
    
    # Execute plan
    execution_report = await execute_plan(plan)
    
    # Validate migration
    validation_report = await validate_migration()
    
    # Generate report
    report = await generate_report(execution_report, validation_report)
    
    logger.info("Complete migration process finished")
    
    return report


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Orchestra System Migration")
    parser.add_argument("--analyze", action="store_true", help="Analyze environment")
    parser.add_argument("--plan", action="store_true", help="Create migration plan")
    parser.add_argument("--execute", action="store_true", help="Execute migration plan")
    parser.add_argument("--validate", action="store_true", help="Validate migration")
    parser.add_argument("--report", action="store_true", help="Generate migration report")
    parser.add_argument("--rollback", action="store_true", help="Rollback migration")
    parser.add_argument("--all", action="store_true", help="Run complete migration process")
    parser.add_argument("--backup-paths", nargs="+", help="Backup paths for rollback")
    parser.add_argument("--plan-file", help="Migration plan file")
    parser.add_argument("--execution-file", help="Execution report file")
    parser.add_argument("--validation-file", help="Validation report file")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    # If no arguments provided, default to analyze
    if not any([args.analyze, args.plan, args.execute, args.validate, 
                args.report, args.rollback, args.all]):
        args.analyze = True
    
    # If --all is specified, run complete migration
    if args.all:
        report = await run_complete_migration()
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Migration report saved to {args.output}")
        
        sys.exit(0)
    
    # Run individual steps
    result = None
    
    if args.analyze:
        result = await run_analysis()
    
    if args.plan:
        analysis_report = None
        if result and "resources_count" in result:
            analysis_report = result
        
        result = await create_plan(analysis_report)
    
    if args.execute:
        plan = None
        if args.plan_file:
            with open(args.plan_file, "r") as f:
                plan = json.load(f)
        elif result and "steps" in result:
            plan = result
        
        if not plan:
            logger.error("No migration plan provided")
            sys.exit(1)
        
        result = await execute_plan(plan)
    
    if args.validate:
        result = await validate_migration()
    
    if args.rollback:
        backup_paths = args.backup_paths
        if not backup_paths and args.plan_file:
            with open(args.plan_file, "r") as f:
                plan = json.load(f)
                backup_paths = plan.get("backup_paths", [])
        
        if not backup_paths:
            logger.error("No backup paths provided for rollback")
            sys.exit(1)
        
        result = await rollback_migration(backup_paths)
    
    if args.report:
        execution_report = None
        validation_report = None
        
        if args.execution_file:
            with open(args.execution_file, "r") as f:
                execution_report = json.load(f)
        
        if args.validation_file:
            with open(args.validation_file, "r") as f:
                validation_report = json.load(f)
        
        result = await generate_report(execution_report, validation_report)
    
    # Save result if output file specified
    if result and args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())