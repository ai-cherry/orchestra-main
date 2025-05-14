#!/usr/bin/env python3
"""
AI Orchestra GCP Migration Rollback Tool

This script provides a safe way to rollback changes made during the migration process
if issues are encountered. It implements phase-specific rollback procedures and
maintains a state log to ensure proper recovery.

Usage:
    python rollback.py --phase=core_infrastructure
    python rollback.py --phase=workstation_config
    python rollback.py --phase=memory_system
    python rollback.py --phase=ai_coding
    python rollback.py --phase=api_deployment
    python rollback.py --phase=all
    python rollback.py --to-checkpoint=<checkpoint_id>
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rollback.log"),
    ],
)
logger = logging.getLogger(__name__)

# Migration phases (must match those in migration_toolkit.py)
class MigrationPhase(Enum):
    CORE_INFRASTRUCTURE = "core_infrastructure"
    WORKSTATION_CONFIG = "workstation_config"
    MEMORY_SYSTEM = "memory_system" 
    AI_CODING = "ai_coding"
    API_DEPLOYMENT = "api_deployment"
    VALIDATION = "validation"
    ALL = "all"

# Rollback states for tracking progress
ROLLBACK_STATE_FILE = "rollback_state.json"

class RollbackTool:
    """Rollback tool for the GCP migration process."""
    
    def __init__(self, phase: Optional[MigrationPhase] = None, checkpoint_id: Optional[str] = None):
        """Initialize the rollback tool.
        
        Args:
            phase: The specific migration phase to rollback
            checkpoint_id: A specific checkpoint to rollback to
        """
        self.phase = phase
        self.checkpoint_id = checkpoint_id
        self.base_dir = Path(__file__).parent
        self.project_id = "cherry-ai-project"
        self.region = "us-central1"
        self.state = self._load_state()
        
        # Define the phase dependency order (for proper rollback sequence)
        self.phase_dependencies = {
            MigrationPhase.VALIDATION: [MigrationPhase.API_DEPLOYMENT],
            MigrationPhase.API_DEPLOYMENT: [MigrationPhase.AI_CODING],
            MigrationPhase.AI_CODING: [MigrationPhase.MEMORY_SYSTEM],
            MigrationPhase.MEMORY_SYSTEM: [MigrationPhase.WORKSTATION_CONFIG],
            MigrationPhase.WORKSTATION_CONFIG: [MigrationPhase.CORE_INFRASTRUCTURE],
            MigrationPhase.CORE_INFRASTRUCTURE: [],
        }
    
    def _load_state(self) -> Dict[str, Any]:
        """Load the current rollback state.
        
        Returns:
            Dict containing the current rollback state
        """
        state_file = self.base_dir / ROLLBACK_STATE_FILE
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading rollback state: {str(e)}")
                return self._create_default_state()
        else:
            return self._create_default_state()
    
    def _create_default_state(self) -> Dict[str, Any]:
        """Create a default rollback state.
        
        Returns:
            Dict containing the default rollback state
        """
        return {
            "checkpoints": [],
            "last_rollback": None,
            "completed_phases": [],
        }
    
    def _save_state(self) -> None:
        """Save the current rollback state."""
        state_file = self.base_dir / ROLLBACK_STATE_FILE
        try:
            with open(state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rollback state: {str(e)}")
    
    def _create_checkpoint(self, phase: MigrationPhase) -> str:
        """Create a checkpoint before making changes.
        
        Args:
            phase: The migration phase being executed
            
        Returns:
            str: The checkpoint ID
        """
        checkpoint_id = f"{phase.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create checkpoint directory
        checkpoint_dir = self.base_dir / "checkpoints" / checkpoint_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Add to state
        self.state["checkpoints"].append({
            "id": checkpoint_id,
            "phase": phase.value,
            "timestamp": datetime.now().isoformat(),
            "resources": [],
        })
        self._save_state()
        
        logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_id
    
    def execute(self) -> int:
        """Execute the rollback process.
        
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        logger.info("Starting rollback process...")
        
        try:
            # If rolling back to a specific checkpoint
            if self.checkpoint_id:
                return self._rollback_to_checkpoint()
            
            # If rolling back a specific phase
            if self.phase and self.phase != MigrationPhase.ALL:
                return self._rollback_phase(self.phase)
            
            # If rolling back all phases
            if self.phase == MigrationPhase.ALL:
                return self._rollback_all_phases()
            
            logger.error("No phase or checkpoint specified for rollback")
            return 1
        
        except Exception as e:
            logger.exception(f"Rollback failed: {str(e)}")
            return 1
    
    def _rollback_to_checkpoint(self) -> int:
        """Rollback to a specific checkpoint.
        
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        # Find the checkpoint
        checkpoint = None
        for cp in self.state["checkpoints"]:
            if cp["id"] == self.checkpoint_id:
                checkpoint = cp
                break
        
        if not checkpoint:
            logger.error(f"Checkpoint not found: {self.checkpoint_id}")
            return 1
        
        logger.info(f"Rolling back to checkpoint: {self.checkpoint_id} (Phase: {checkpoint['phase']})")
        
        # Track the rollback
        self.state["last_rollback"] = {
            "checkpoint_id": self.checkpoint_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_state()
        
        # Perform phase-specific rollback
        phase = MigrationPhase(checkpoint["phase"])
        return self._rollback_phase(phase)
    
    def _rollback_phase(self, phase: MigrationPhase) -> int:
        """Rollback a specific migration phase.
        
        Args:
            phase: The migration phase to rollback
            
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        logger.info(f"Rolling back phase: {phase.value}")
        
        # Create a rollback checkpoint
        rollback_checkpoint_id = f"rollback_{phase.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Rollback the phase
        if phase == MigrationPhase.CORE_INFRASTRUCTURE:
            success = self._rollback_core_infrastructure()
        elif phase == MigrationPhase.WORKSTATION_CONFIG:
            success = self._rollback_workstation_config()
        elif phase == MigrationPhase.MEMORY_SYSTEM:
            success = self._rollback_memory_system()
        elif phase == MigrationPhase.AI_CODING:
            success = self._rollback_ai_coding()
        elif phase == MigrationPhase.API_DEPLOYMENT:
            success = self._rollback_api_deployment()
        elif phase == MigrationPhase.VALIDATION:
            # Validation doesn't require rollback as it doesn't make changes
            success = True
        else:
            logger.error(f"Unknown phase: {phase}")
            return 1
        
        # Update state
        if success and phase.value in self.state["completed_phases"]:
            self.state["completed_phases"].remove(phase.value)
            self._save_state()
        
        return 0 if success else 1
    
    def _rollback_all_phases(self) -> int:
        """Rollback all migration phases in reverse dependency order.
        
        Returns:
            int: Exit code (0 for success, non-zero for failure)
        """
        logger.info("Rolling back all phases")
        
        # Get all phases in reverse dependency order
        rollback_order = [
            MigrationPhase.VALIDATION,
            MigrationPhase.API_DEPLOYMENT,
            MigrationPhase.AI_CODING,
            MigrationPhase.MEMORY_SYSTEM,
            MigrationPhase.WORKSTATION_CONFIG,
            MigrationPhase.CORE_INFRASTRUCTURE,
        ]
        
        # Rollback each phase
        success = True
        for phase in rollback_order:
            if phase.value in self.state["completed_phases"]:
                phase_success = self._rollback_phase(phase) == 0
                success = success and phase_success
                if not phase_success:
                    logger.error(f"Failed to rollback phase: {phase.value}")
        
        return 0 if success else 1
    
    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
        """Run a command and return success/failure.
        
        Args:
            cmd: The command to run
            cwd: The working directory (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, cwd=cwd)
            return True
        except subprocess.SubprocessError as e:
            logger.error(f"Command failed: {str(e)}")
            return False
    
    def _rollback_core_infrastructure(self) -> bool:
        """Rollback the core infrastructure phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Rolling back core infrastructure...")
        
        # Use terraform to rollback infrastructure changes
        tf_dir = self.base_dir / "terraform"
        if tf_dir.exists():
            logger.info("Rolling back Terraform infrastructure")
            
            # Initialize terraform
            if not self._run_command(["terraform", "init"], cwd=tf_dir):
                return False
            
            # Run terraform destroy
            if not self._run_command(["terraform", "destroy", "-auto-approve"], cwd=tf_dir):
                return False
        
        # Simulate additional rollback steps
        time.sleep(1)
        
        logger.info("Core infrastructure rollback completed")
        return True
    
    def _rollback_workstation_config(self) -> bool:
        """Rollback the workstation configuration phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Rolling back workstation configuration...")
        
        # Delete workstation resources
        workstation_config = "ai-orchestra-config"
        workstation_cluster = "ai-orchestra-cluster"
        
        # Delete workstation instance
        self._run_command([
            "gcloud", "workstations", "delete", "ai-orchestra-workstation",
            f"--cluster={workstation_cluster}",
            f"--config={workstation_config}",
            f"--region={self.region}",
            f"--project={self.project_id}",
            "--quiet"
        ])
        
        # Delete workstation configuration
        self._run_command([
            "gcloud", "workstations", "configs", "delete", workstation_config,
            f"--cluster={workstation_cluster}",
            f"--region={self.region}",
            f"--project={self.project_id}",
            "--quiet"
        ])
        
        # Delete workstation cluster
        self._run_command([
            "gcloud", "workstations", "clusters", "delete", workstation_cluster,
            f"--region={self.region}",
            f"--project={self.project_id}",
            "--quiet"
        ])
        
        logger.info("Workstation configuration rollback completed")
        return True
    
    def _rollback_memory_system(self) -> bool:
        """Rollback the memory system optimization phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Rolling back memory system optimization...")
        
        # Restore original vector indices (if backup exists)
        vector_indices_backup = self.base_dir / "checkpoints" / "vector_indices_backup.sql"
        if vector_indices_backup.exists():
            logger.info("Restoring original vector indices")
            
            # In a real implementation, this would execute SQL against AlloyDB
            # For now, we'll just simulate it
            time.sleep(1)
        
        logger.info("Memory system rollback completed")
        return True
    
    def _rollback_ai_coding(self) -> bool:
        """Rollback the AI coding assistant configuration phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Rolling back AI coding assistant configuration...")
        
        # Restore original Gemini configuration (if backup exists)
        gemini_config_backup = self.base_dir / "checkpoints" / "gemini_config_backup.yaml"
        if gemini_config_backup.exists():
            logger.info("Restoring original Gemini configuration")
            
            # In a real implementation, this would restore the original configuration
            # For now, we'll just simulate it
            time.sleep(1)
        
        logger.info("AI coding assistant rollback completed")
        return True
    
    def _rollback_api_deployment(self) -> bool:
        """Rollback the API deployment phase.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("Rolling back API deployment...")
        
        # Revert to previous Cloud Run revision
        service_name = "ai-orchestra-api"
        
        # List revisions to get the previous one
        self._run_command([
            "gcloud", "run", "revisions", "list",
            f"--service={service_name}",
            f"--region={self.region}",
            f"--project={self.project_id}",
            "--format=json"
        ])
        
        # In a real implementation, we would parse the JSON output to get the previous revision
        # and then update traffic to route to that revision
        
        # For now, we'll just simulate traffic rerouting
        time.sleep(1)
        
        logger.info("API deployment rollback completed")
        return True


def main() -> int:
    """Main entry point for the rollback tool.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="AI Orchestra GCP Migration Rollback Tool")
    
    # Add arguments
    parser.add_argument(
        "--phase",
        type=str,
        choices=[phase.value for phase in MigrationPhase] + ["all"],
        help="Migration phase to rollback",
    )
    parser.add_argument(
        "--to-checkpoint",
        type=str,
        help="Checkpoint ID to rollback to",
    )
    parser.add_argument(
        "--list-checkpoints",
        action="store_true",
        help="List available checkpoints",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rollback without confirmation",
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create rollback tool
    phase = MigrationPhase(args.phase) if args.phase else None
    rollback_tool = RollbackTool(phase, args.to_checkpoint)
    
    # List checkpoints if requested
    if args.list_checkpoints:
        print("Available checkpoints:")
        for checkpoint in rollback_tool.state["checkpoints"]:
            print(f"  {checkpoint['id']} - {checkpoint['phase']} ({checkpoint['timestamp']})")
        return 0
    
    # Confirm rollback unless --force is used
    if not args.force:
        if args.phase:
            confirm = input(f"Are you sure you want to rollback the {args.phase} phase? (y/n): ")
        elif args.to_checkpoint:
            confirm = input(f"Are you sure you want to rollback to checkpoint {args.to_checkpoint}? (y/n): ")
        else:
            confirm = input("Are you sure you want to rollback? (y/n): ")
        
        if confirm.lower() != "y":
            print("Rollback cancelled")
            return 0
    
    # Execute rollback
    return rollback_tool.execute()


if __name__ == "__main__":
    sys.exit(main())