#!/usr/bin/env python3
"""
AI Orchestra Environment Synchronization

This module provides bidirectional synchronization between GitHub Codespaces
and GCP Cloud Workstations, ensuring consistent development environments during
the migration process.

Key features:
- VS Code settings and extensions synchronization
- Git repository state synchronization
- Environment variable propagation
- Development container configuration alignment
- Credential and authentication synchronization

Usage:
    python environment_sync.py --mode=bidirectional
    python environment_sync.py --mode=codespaces-to-gcp
    python environment_sync.py --mode=gcp-to-codespaces
    python environment_sync.py --mode=status
"""

import argparse
import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("environment_sync.log"),
    ],
)
logger = logging.getLogger("environment_sync")


class SyncMode(Enum):
    """Synchronization mode for environment sync."""
    BIDIRECTIONAL = "bidirectional"
    CODESPACES_TO_GCP = "codespaces-to-gcp"
    GCP_TO_CODESPACES = "gcp-to-codespaces"
    STATUS = "status"


class SyncDirection(Enum):
    """Direction of synchronization for a specific operation."""
    TO_GCP = "to-gcp"
    TO_CODESPACES = "to-codespaces"


class EnvironmentType(Enum):
    """Type of environment being used."""
    CODESPACES = "codespaces"
    GCP_WORKSTATION = "gcp-workstation"
    UNKNOWN = "unknown"


class SyncItem:
    """Base class for items to be synchronized."""
    
    def __init__(
        self,
        name: str,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
    ):
        """Initialize the sync item.
        
        Args:
            name: Name of the item
            source_path: Source path of the item
            target_path: Target path of the item
            direction: Direction of synchronization
        """
        self.name = name
        self.source_path = source_path
        self.target_path = target_path
        self.direction = direction
        self.last_sync_time: Optional[datetime] = None
        self.status = "pending"
        self.error: Optional[str] = None
    
    def __str__(self) -> str:
        return (
            f"{self.name} ({self.direction.value}): {self.source_path} -> {self.target_path} "
            f"[{self.status}]"
        )
    
    async def sync(self) -> bool:
        """Synchronize the item.
        
        Returns:
            True if synchronization was successful, False otherwise
        """
        try:
            await self._do_sync()
            self.last_sync_time = datetime.now()
            self.status = "success"
            return True
        except Exception as e:
            logger.error(f"Error synchronizing {self.name}: {str(e)}")
            self.status = "error"
            self.error = str(e)
            return False
    
    async def _do_sync(self) -> None:
        """Perform the actual synchronization.
        
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _do_sync()")


class FileSyncItem(SyncItem):
    """Item for synchronizing individual files."""
    
    def __init__(
        self,
        name: str,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
        binary: bool = False,
    ):
        """Initialize the file sync item.
        
        Args:
            name: Name of the item
            source_path: Source path of the file
            target_path: Target path of the file
            direction: Direction of synchronization
            binary: Whether the file is binary
        """
        super().__init__(name, source_path, target_path, direction)
        self.binary = binary
    
    async def _do_sync(self) -> None:
        """Perform file synchronization."""
        # Check if source file exists
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source file not found: {self.source_path}")
        
        # Ensure target directory exists
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        logger.info(f"Copying {self.source_path} to {self.target_path}")
        
        # Use shutil for actual file copy
        try:
            shutil.copy2(self.source_path, self.target_path)
        except Exception as e:
            logger.error(f"Error copying file: {str(e)}")
            raise
        
        # Verify file was copied correctly
        if not self.target_path.exists():
            raise RuntimeError(f"File copy failed: {self.target_path} does not exist")
        
        if not self.binary:
            # For text files, verify content
            with open(self.source_path, "r") as sf, open(self.target_path, "r") as tf:
                source_content = sf.read()
                target_content = tf.read()
                
                if source_content != target_content:
                    raise RuntimeError(
                        f"File content verification failed for {self.name}"
                    )


class DirectorySyncItem(SyncItem):
    """Item for synchronizing directories."""
    
    def __init__(
        self,
        name: str,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """Initialize the directory sync item.
        
        Args:
            name: Name of the item
            source_path: Source path of the directory
            target_path: Target path of the directory
            direction: Direction of synchronization
            exclude_patterns: Patterns to exclude from synchronization
        """
        super().__init__(name, source_path, target_path, direction)
        self.exclude_patterns = exclude_patterns or []
        self._compiled_exclude_patterns = [
            re.compile(pattern) for pattern in self.exclude_patterns
        ]
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded based on exclude patterns.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        path_str = str(path)
        return any(pattern.search(path_str) for pattern in self._compiled_exclude_patterns)
    
    async def _do_sync(self) -> None:
        """Perform directory synchronization."""
        # Check if source directory exists
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_path}")
        
        # Ensure target directory exists
        self.target_path.mkdir(parents=True, exist_ok=True)
        
        # Walk the source directory
        for root, dirs, files in os.walk(self.source_path):
            # Convert to Path objects
            root_path = Path(root)
            rel_path = root_path.relative_to(self.source_path)
            target_root = self.target_path / rel_path
            
            # Create target directories if they don't exist
            target_root.mkdir(parents=True, exist_ok=True)
            
            # Filter directories based on exclude patterns
            dirs[:] = [d for d in dirs if not self._should_exclude(rel_path / d)]
            
            # Synchronize files
            for file in files:
                source_file = root_path / file
                target_file = target_root / file
                
                # Skip excluded files
                if self._should_exclude(rel_path / file):
                    logger.debug(f"Skipping excluded file: {rel_path / file}")
                    continue
                
                # Determine if the file is binary
                try:
                    with open(source_file, "r") as f:
                        f.read(1024)
                    is_binary = False
                except UnicodeDecodeError:
                    is_binary = True
                
                # Create a file sync item and synchronize it
                file_sync_item = FileSyncItem(
                    name=f"File: {rel_path / file}",
                    source_path=source_file,
                    target_path=target_file,
                    direction=self.direction,
                    binary=is_binary,
                )
                
                await file_sync_item.sync()


class JsonSyncItem(SyncItem):
    """Item for synchronizing JSON files with merge capability."""
    
    def __init__(
        self,
        name: str,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
        merge_strategy: str = "deep",
    ):
        """Initialize the JSON sync item.
        
        Args:
            name: Name of the item
            source_path: Source path of the JSON file
            target_path: Target path of the JSON file
            direction: Direction of synchronization
            merge_strategy: Strategy for merging JSON (deep, shallow, replace)
        """
        super().__init__(name, source_path, target_path, direction)
        self.merge_strategy = merge_strategy
    
    def _deep_merge(self, source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a deep merge of two dictionaries.
        
        Args:
            source: Source dictionary
            target: Target dictionary
            
        Returns:
            Merged dictionary
        """
        result = target.copy()
        
        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                result[key] = self._deep_merge(value, result[key])
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Merge lists by appending unique items
                result[key] = list(set(result[key] + value))
            else:
                # Otherwise, replace the value
                result[key] = value
        
        return result
    
    async def _do_sync(self) -> None:
        """Perform JSON file synchronization with merge."""
        # Check if source file exists
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source file not found: {self.source_path}")
        
        # Ensure target directory exists
        self.target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load source JSON
        with open(self.source_path, "r") as f:
            source_data = json.load(f)
        
        # Check if target exists
        if self.target_path.exists():
            # Load target JSON
            with open(self.target_path, "r") as f:
                target_data = json.load(f)
            
            # Merge according to strategy
            if self.merge_strategy == "deep":
                merged_data = self._deep_merge(source_data, target_data)
            elif self.merge_strategy == "shallow":
                # Shallow merge just updates top-level keys
                merged_data = target_data.copy()
                merged_data.update(source_data)
            else:  # replace
                merged_data = source_data
        else:
            # Target doesn't exist, just use source data
            merged_data = source_data
        
        # Write merged JSON to target
        with open(self.target_path, "w") as f:
            json.dump(merged_data, f, indent=2)


class GitSyncItem(SyncItem):
    """Item for synchronizing Git repositories."""
    
    def __init__(
        self,
        name: str,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
        branch: str = "main",
    ):
        """Initialize the Git sync item.
        
        Args:
            name: Name of the item
            source_path: Source path of the Git repository
            target_path: Target path of the Git repository
            direction: Direction of synchronization
            branch: Branch to synchronize
        """
        super().__init__(name, source_path, target_path, direction)
        self.branch = branch
    
    async def _run_git_command(self, args: List[str], cwd: Path) -> str:
        """Run a Git command.
        
        Args:
            args: Command arguments
            cwd: Working directory
            
        Returns:
            Command output
        """
        cmd = ["git"] + args
        logger.debug(f"Running git command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise RuntimeError(f"Git command failed: {e.stderr}")
    
    async def _do_sync(self) -> None:
        """Perform Git repository synchronization."""
        # Check if source repository exists
        if not (self.source_path / ".git").exists():
            raise FileNotFoundError(f"Source git repository not found: {self.source_path}")
        
        # Check if target repository exists
        if not (self.target_path / ".git").exists():
            # Initialize target repository
            self.target_path.mkdir(parents=True, exist_ok=True)
            await self._run_git_command(["init"], self.target_path)
            
            # Add source as remote
            remote_name = "source"
            await self._run_git_command(
                ["remote", "add", remote_name, str(self.source_path.absolute())],
                self.target_path,
            )
        else:
            # Update source remote
            remote_name = "source"
            try:
                await self._run_git_command(
                    ["remote", "remove", remote_name],
                    self.target_path,
                )
            except Exception:
                # Remote might not exist yet
                pass
            
            await self._run_git_command(
                ["remote", "add", remote_name, str(self.source_path.absolute())],
                self.target_path,
            )
        
        # Fetch from source
        await self._run_git_command(
            ["fetch", remote_name],
            self.target_path,
        )
        
        # Merge changes
        try:
            await self._run_git_command(
                ["merge", f"{remote_name}/{self.branch}", "--allow-unrelated-histories"],
                self.target_path,
            )
        except Exception as e:
            logger.warning(f"Merge failed, attempting with strategy: {str(e)}")
            
            # Try with a specific merge strategy
            try:
                await self._run_git_command(
                    [
                        "merge",
                        f"{remote_name}/{self.branch}",
                        "--allow-unrelated-histories",
                        "-X", "theirs",
                    ],
                    self.target_path,
                )
            except Exception as e2:
                logger.error(f"Merge failed with strategy: {str(e2)}")
                
                # Abort the merge
                try:
                    await self._run_git_command(
                        ["merge", "--abort"],
                        self.target_path,
                    )
                except Exception:
                    pass
                
                raise RuntimeError(f"Git merge failed: {str(e2)}")


class VSCodeSettingsSyncItem(JsonSyncItem):
    """Item for synchronizing VS Code settings."""
    
    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
    ):
        """Initialize the VS Code settings sync item.
        
        Args:
            source_path: Source path of the settings file
            target_path: Target path of the settings file
            direction: Direction of synchronization
        """
        super().__init__(
            name="VS Code Settings",
            source_path=source_path,
            target_path=target_path,
            direction=direction,
            merge_strategy="deep",
        )


class EnvironmentVariableSyncItem(SyncItem):
    """Item for synchronizing environment variables."""
    
    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        direction: SyncDirection,
        exclude_vars: Optional[List[str]] = None,
    ):
        """Initialize the environment variables sync item.
        
        Args:
            source_path: Source path of the environment file
            target_path: Target path of the environment file
            direction: Direction of synchronization
            exclude_vars: Variables to exclude from synchronization
        """
        super().__init__(
            name="Environment Variables",
            source_path=source_path,
            target_path=target_path,
            direction=direction,
        )
        self.exclude_vars = exclude_vars or []
    
    def _parse_env_file(self, path: Path) -> Dict[str, str]:
        """Parse an environment file.
        
        Args:
            path: Path to the environment file
            
        Returns:
            Dictionary of environment variables
        """
        if not path.exists():
            return {}
        
        env_vars = {}
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Parse key-value pair
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
        
        return env_vars
    
    def _write_env_file(self, path: Path, env_vars: Dict[str, str]) -> None:
        """Write environment variables to a file.
        
        Args:
            path: Path to the environment file
            env_vars: Dictionary of environment variables
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            for key, value in sorted(env_vars.items()):
                if key in self.exclude_vars:
                    continue
                
                # Add quotes if value contains spaces
                if " " in value or "\t" in value or "\n" in value:
                    value = f'"{value}"'
                
                f.write(f"{key}={value}\n")
    
    async def _do_sync(self) -> None:
        """Perform environment variables synchronization."""
        # Parse source environment file
        source_env = self._parse_env_file(self.source_path)
        
        # Parse target environment file if it exists
        target_env = self._parse_env_file(self.target_path) if self.target_path.exists() else {}
        
        # Merge environment variables
        merged_env = {**target_env, **source_env}
        
        # Write merged environment variables to target
        self._write_env_file(self.target_path, merged_env)


class EnvironmentSynchronizer:
    """Synchronizer for development environments."""
    
    def __init__(
        self,
        codespaces_dir: Path,
        gcp_dir: Path,
        mode: SyncMode = SyncMode.BIDIRECTIONAL,
    ):
        """Initialize the environment synchronizer.
        
        Args:
            codespaces_dir: GitHub Codespaces directory
            gcp_dir: GCP Cloud Workstation directory
            mode: Synchronization mode
        """
        self.codespaces_dir = codespaces_dir
        self.gcp_dir = gcp_dir
        self.mode = mode
        self.sync_items: List[SyncItem] = []
        self.current_environment = self._detect_environment()
        
        logger.info(f"Initialized environment synchronizer in {mode.value} mode")
        logger.info(f"Codespaces directory: {codespaces_dir}")
        logger.info(f"GCP directory: {gcp_dir}")
        logger.info(f"Current environment: {self.current_environment.value}")
    
    def _detect_environment(self) -> EnvironmentType:
        """Detect the current environment.
        
        Returns:
            Environment type
        """
        # Check for CODESPACES environment variable (set in GitHub Codespaces)
        if os.environ.get("CODESPACES", "").lower() == "true":
            return EnvironmentType.CODESPACES
        
        # Check for CLOUD_WORKSTATIONS_ENVIRONMENT variable (set in GCP Cloud Workstations)
        if "CLOUD_WORKSTATIONS_ENVIRONMENT" in os.environ:
            return EnvironmentType.GCP_WORKSTATION
        
        # Try to detect based on paths and files
        # 1. Check for .codespaces file or folder
        if (self.codespaces_dir / ".codespaces").exists():
            return EnvironmentType.CODESPACES
        
        # 2. Check for gcp workstation specific files
        if (self.gcp_dir / ".gcp-workstation").exists():
            return EnvironmentType.GCP_WORKSTATION
        
        return EnvironmentType.UNKNOWN
    
    def add_sync_item(self, item: SyncItem) -> None:
        """Add a sync item.
        
        Args:
            item: Sync item to add
        """
        self.sync_items.append(item)
    
    def create_default_sync_items(self) -> None:
        """Create default sync items based on common patterns."""
        # VS Code settings
        if self.mode in [SyncMode.BIDIRECTIONAL, SyncMode.CODESPACES_TO_GCP]:
            self.add_sync_item(
                VSCodeSettingsSyncItem(
                    source_path=self.codespaces_dir / ".vscode" / "settings.json",
                    target_path=self.gcp_dir / ".vscode" / "settings.json",
                    direction=SyncDirection.TO_GCP,
                )
            )
        
        if self.mode in [SyncMode.BIDIRECTIONAL, SyncMode.GCP_TO_CODESPACES]:
            self.add_sync_item(
                VSCodeSettingsSyncItem(
                    source_path=self.gcp_dir / ".vscode" / "settings.json",
                    target_path=self.codespaces_dir / ".vscode" / "settings.json",
                    direction=SyncDirection.TO_CODESPACES,
                )
            )
        
        # Environment variables
        if self.mode in [SyncMode.BIDIRECTIONAL, SyncMode.CODESPACES_TO_GCP]:
            self.add_sync_item(
                EnvironmentVariableSyncItem(
                    source_path=self.codespaces_dir / ".env",
                    target_path=self.gcp_dir / ".env",
                    direction=SyncDirection.TO_GCP,
                    exclude_vars=["GITHUB_TOKEN", "CODESPACES", "CODESPACE_NAME"],
                )
            )
        
        if self.mode in [SyncMode.BIDIRECTIONAL, SyncMode.GCP_TO_CODESPACES]:
            self.add_sync_item(
                EnvironmentVariableSyncItem(
                    source_path=self.gcp_dir / ".env",
                    target_path=self.codespaces_dir / ".env",
                    direction=SyncDirection.TO_CODESPACES,
                    exclude_vars=["CLOUD_WORKSTATIONS_ENVIRONMENT", "GOOGLE_APPLICATION_CREDENTIALS"],
                )
            )
        
        # Git repository sync if we're in a different directory structure
        if str(self.codespaces_dir) != str(self.gcp_dir):
            if self.mode in [SyncMode.BIDIRECTIONAL, SyncMode.CODESPACES_TO_GCP]:
                self.add_sync_item(
                    GitSyncItem(
                        name="Repository (Codespaces to GCP)",
                        source_path=self.codespaces_dir,
                        target_path=self.gcp_dir,
                        direction=SyncDirection.TO_GCP,
                    )
                )
            
            if self.mode in [SyncMode.BIDIRECTIONAL, SyncMode.GCP_TO_CODESPACES]:
                self.add_sync_item(
                    GitSyncItem(
                        name="Repository (GCP to Codespaces)",
                        source_path=self.gcp_dir,
                        target_path=self.codespaces_dir,
                        direction=SyncDirection.TO_CODESPACES,
                    )
                )
    
    async def synchronize(self) -> Dict[str, Any]:
        """Synchronize all items.
        
        Returns:
            Synchronization results
        """
        results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode.value,
            "current_environment": self.current_environment.value,
            "items": [],
        }
        
        success_count = 0
        error_count = 0
        
        for item in self.sync_items:
            # Skip items that don't match the current mode
            if (
                self.mode == SyncMode.CODESPACES_TO_GCP 
                and item.direction != SyncDirection.TO_GCP
            ):
                continue
            
            if (
                self.mode == SyncMode.GCP_TO_CODESPACES 
                and item.direction != SyncDirection.TO_CODESPACES
            ):
                continue
            
            # Synchronize the item
            start_time = time.time()
            success = await item.sync()
            end_time = time.time()
            
            # Update counters
            if success:
                success_count += 1
            else:
                error_count += 1
            
            # Add to results
            results["items"].append({
                "name": item.name,
                "direction": item.direction.value,
                "status": item.status,
                "duration_seconds": end_time - start_time,
                "error": item.error,
            })
        
        # Add summary
        results["summary"] = {
            "total": len(self.sync_items),
            "success": success_count,
            "error": error_count,
        }
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get synchronization status.
        
        Returns:
            Synchronization status
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode.value,
            "current_environment": self.current_environment.value,
            "items": [
                {
                    "name": item.name,
                    "direction": item.direction.value,
                    "status": item.status,
                    "last_sync_time": item.last_sync_time.isoformat() if item.last_sync_time else None,
                    "error": item.error,
                }
                for item in self.sync_items
            ],
        }
    
    def save_status(self, path: Path) -> None:
        """Save synchronization status to a file.
        
        Args:
            path: Path to save status to
        """
        status = self.get_status()
        
        with open(path, "w") as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Saved sync status to {path}")


async def run_synchronizer(args: argparse.Namespace) -> int:
    """Run the environment synchronizer.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    # Create the synchronizer
    synchronizer = EnvironmentSynchronizer(
        codespaces_dir=Path(args.codespaces_dir),
        gcp_dir=Path(args.gcp_dir),
        mode=SyncMode(args.mode),
    )
    
    # Create default sync items
    synchronizer.create_default_sync_items()
    
    # If status mode, just print status
    if args.mode == SyncMode.STATUS.value:
        status = synchronizer.get_status()
        print(json.dumps(status, indent=2))
        return 0
    
    # Otherwise, run synchronization
    results = await synchronizer.synchronize()
    
    # Save status
    if args.status_file:
        synchronizer.save_status(Path(args.status_file))
    
    # Print summary
    print("Synchronization Results:")
    print(f"Total: {results['summary']['total']}")
    print(f"Success: {results['summary']['success']}")
    print(f"Error: {results['summary']['error']}")
    
    # Print errors
    errors = [item for item in results["items"] if item["status"] == "error"]
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error['name']}: {error['error']}")
    
    return 0 if results["summary"]["error"] == 0 else 1


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing.
    
    Returns:
        Argument parser
    """
    parser = argparse.ArgumentParser(
        description="Synchronize development environments between GitHub Codespaces and GCP Cloud Workstations"
    )
    
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in SyncMode],
        default=SyncMode.BIDIRECTIONAL.value,
        help="Synchronization mode"
    )
    
    parser.add_argument(
        "--codespaces-dir",
        type=str,
        default=os.getcwd(),
        help="GitHub Codespaces directory"
    )
    
    parser.add_argument(
        "--gcp-dir",
        type=str,
        default=os.getcwd(),
        help="GCP Cloud Workstation directory"
    )
    
    parser.add_argument(
        "--status-file",
        type=str,
        help="Path to save synchronization status"
    )
    
    return parser


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    parser = setup_argparse()
    args = parser.parse_args()
    
    try:
        return asyncio.run(run_synchronizer(args))
    except KeyboardInterrupt:
        logger.info("Synchronization interrupted by user")
        return 1
    except Exception as e:
        logger.exception(f"Error running synchronizer: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())