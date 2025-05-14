#!/usr/bin/env python3
"""
Synchronization System

This module provides a clean implementation of the synchronization system
for the GCP migration. It handles bidirectional synchronization between
GitHub Codespaces and GCP Cloud Workstations with clear abstractions
and efficient file handling.
"""

import abc
import asyncio
import concurrent.futures
import contextlib
import enum
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, 
    Tuple, TypeVar, Union, cast
)

# Import worker pool for parallel operations
try:
    from .worker_pool import WorkerPool, worker_pool_context, TaskPriority
except ImportError:
    # For standalone usage
    import sys
    sys.path.append(str(Path(__file__).parent))
    from worker_pool import WorkerPool, worker_pool_context, TaskPriority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("sync_system")


class EnvironmentType(enum.Enum):
    """Type of development environment."""
    CODESPACES = "codespaces"
    GCP_WORKSTATION = "gcp_workstation"
    UNKNOWN = "unknown"


class SyncDirection(enum.Enum):
    """Direction of synchronization."""
    CODESPACES_TO_GCP = "codespaces_to_gcp"
    GCP_TO_CODESPACES = "gcp_to_codespaces"
    BIDIRECTIONAL = "bidirectional"


class SyncItemType(enum.Enum):
    """Type of synchronization item."""
    FILE = "file"
    DIRECTORY = "directory"
    GIT_REPO = "git_repo"
    JSON_FILE = "json_file"
    VSCODE_SETTINGS = "vscode_settings"
    ENVIRONMENT_VARIABLE = "environment_variable"


class ConflictResolutionStrategy(enum.Enum):
    """Strategy for resolving synchronization conflicts."""
    SOURCE_WINS = "source_wins"  # Source overwrites target
    TARGET_WINS = "target_wins"  # Target is preserved
    MERGE = "merge"  # Attempt to merge changes
    MANUAL = "manual"  # Require manual intervention
    SKIP = "skip"  # Skip conflicting item


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    item_path: str
    item_type: SyncItemType
    direction: SyncDirection
    message: Optional[str] = None
    error: Optional[Exception] = None
    changes_made: bool = False
    conflicts_resolved: int = 0
    bytes_transferred: int = 0


@dataclass
class SyncConfig:
    """Configuration for synchronization."""
    source_dir: Path
    target_dir: Path
    direction: SyncDirection
    conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.SOURCE_WINS
    exclude_patterns: List[str] = field(default_factory=list)
    max_workers: int = 8
    dry_run: bool = False
    verbose: bool = False
    include_hidden: bool = False
    backup: bool = True
    backup_dir: Optional[Path] = None


class SyncItem(abc.ABC):
    """Base class for synchronization items."""
    
    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        config: SyncConfig,
    ):
        """Initialize the synchronization item.
        
        Args:
            source_path: Source path
            target_path: Target path
            config: Synchronization configuration
        """
        self.source_path = source_path
        self.target_path = target_path
        self.config = config
        self.type = self._get_type()
    
    @abc.abstractmethod
    def _get_type(self) -> SyncItemType:
        """Get the type of synchronization item."""
        pass
    
    @abc.abstractmethod
    def needs_sync(self) -> bool:
        """Check if synchronization is needed."""
        pass
    
    @abc.abstractmethod
    def synchronize(self) -> SyncResult:
        """Perform synchronization and return the result."""
        pass
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded based on exclusion patterns."""
        path_str = str(path)
        for pattern in self.config.exclude_patterns:
            if re.search(pattern, path_str):
                return True
        
        # Exclude hidden files and directories unless explicitly included
        if not self.config.include_hidden and path.name.startswith("."):
            return True
        
        return False
    
    def _create_backup(self, path: Path) -> Optional[Path]:
        """Create a backup of a file or directory.
        
        Args:
            path: Path to back up
            
        Returns:
            Path to backup or None if backup was not created
        """
        if not self.config.backup or not path.exists():
            return None
        
        # Determine backup directory
        backup_dir = self.config.backup_dir
        if backup_dir is None:
            backup_dir = path.parent / ".sync_backups"
        
        # Create backup directory if it doesn't exist
        backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Create unique backup name with timestamp
        timestamp = time.strftime("%Y%m%d%H%M%S")
        backup_name = f"{path.name}.{timestamp}.bak"
        backup_path = backup_dir / backup_name
        
        # Create backup
        if path.is_file():
            shutil.copy2(path, backup_path)
        elif path.is_dir():
            shutil.copytree(path, backup_path)
        
        logger.debug(f"Created backup of {path} at {backup_path}")
        return backup_path
    
    def _is_binary_file(self, path: Path) -> bool:
        """Check if a file is binary.
        
        Args:
            path: Path to check
            
        Returns:
            True if the file is binary, False otherwise
        """
        if not path.is_file():
            return False
        
        # Check file extension first
        binary_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.pdf',
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
            '.exe', '.dll', '.so', '.dylib', '.jar', '.war', '.ear',
            '.pyc', '.pyo', '.pyd', '.obj', '.o',
        }
        
        if path.suffix.lower() in binary_extensions:
            return True
        
        # Check file content
        try:
            chunk_size = 1024
            with open(path, 'rb') as file:
                chunk = file.read(chunk_size)
                # Binary files often contain null bytes
                if b'\0' in chunk:
                    return True
                
                # Try to decode as text
                try:
                    chunk.decode('utf-8')
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception as e:
            logger.warning(f"Error checking if {path} is binary: {str(e)}")
            # Assume binary if we can't determine
            return True


class FileSyncItem(SyncItem):
    """Synchronization item for a file."""
    
    def _get_type(self) -> SyncItemType:
        return SyncItemType.FILE
    
    def needs_sync(self) -> bool:
        """Check if the file needs synchronization."""
        # Skip if source doesn't exist
        if not self.source_path.exists():
            return False
        
        # Skip if excluded
        if self._should_exclude(self.source_path):
            return False
        
        # If target doesn't exist, sync is needed
        if not self.target_path.exists():
            return True
        
        # Both exist, check if they differ
        return self._files_differ(self.source_path, self.target_path)
    
    def _files_differ(self, file1: Path, file2: Path) -> bool:
        """Check if two files have different content.
        
        Args:
            file1: First file
            file2: Second file
            
        Returns:
            True if files differ, False otherwise
        """
        # Check file size first (quick check)
        if file1.stat().st_size != file2.stat().st_size:
            return True
        
        # Check modification time if within 2 seconds (fast check for unchanged files)
        # This helps avoid content comparison for files that haven't changed
        mtime1 = file1.stat().st_mtime
        mtime2 = file2.stat().st_mtime
        if abs(mtime1 - mtime2) < 2 and file1.stat().st_size == file2.stat().st_size:
            return False
        
        # Compare file content
        try:
            # For binary files, use hash comparison
            if self._is_binary_file(file1) or self._is_binary_file(file2):
                return self._files_differ_binary(file1, file2)
            
            # For text files, compare line by line
            return self._files_differ_text(file1, file2)
        except Exception as e:
            logger.warning(f"Error comparing {file1} and {file2}: {str(e)}")
            # Assume different if we can't determine
            return True
    
    def _files_differ_binary(self, file1: Path, file2: Path) -> bool:
        """Compare binary files using hashing.
        
        Args:
            file1: First file
            file2: Second file
            
        Returns:
            True if files differ, False otherwise
        """
        # Use MD5 for speed (not for security)
        return self._get_file_hash(file1) != self._get_file_hash(file2)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate the MD5 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash as hexadecimal string
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _files_differ_text(self, file1: Path, file2: Path) -> bool:
        """Compare text files line by line.
        
        Args:
            file1: First file
            file2: Second file
            
        Returns:
            True if files differ, False otherwise
        """
        with open(file1, 'r', encoding='utf-8', errors='replace') as f1, \
             open(file2, 'r', encoding='utf-8', errors='replace') as f2:
            for line1, line2 in zip(f1, f2):
                if line1 != line2:
                    return True
            
            # Check if one file has more lines than the other
            if next(f1, None) is not None or next(f2, None) is not None:
                return True
        
        return False
    
    def synchronize(self) -> SyncResult:
        """Synchronize the file from source to target."""
        # Skip if we don't need to sync
        if not self.needs_sync():
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="File is already in sync",
                changes_made=False,
            )
        
        # Skip if in dry run mode
        if self.config.dry_run:
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Would synchronize file (dry run)",
                changes_made=False,
            )
        
        try:
            # Create backup if target exists
            if self.target_path.exists():
                self._create_backup(self.target_path)
            
            # Ensure target directory exists
            self.target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(self.source_path, self.target_path)
            
            # Calculate bytes transferred
            bytes_transferred = self.source_path.stat().st_size
            
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"File synchronized successfully ({bytes_transferred} bytes)",
                changes_made=True,
                bytes_transferred=bytes_transferred,
            )
        
        except Exception as e:
            logger.exception(f"Error synchronizing file {self.source_path} to {self.target_path}")
            return SyncResult(
                success=False,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"Error synchronizing file: {str(e)}",
                error=e,
                changes_made=False,
            )


class DirectorySyncItem(SyncItem):
    """Synchronization item for a directory."""
    
    def _get_type(self) -> SyncItemType:
        return SyncItemType.DIRECTORY
    
    def needs_sync(self) -> bool:
        """Check if the directory needs synchronization.
        
        For directories, we always return True and let the 
        synchronize method handle the details.
        """
        # Skip if source doesn't exist
        if not self.source_path.exists():
            return False
        
        # Skip if excluded
        if self._should_exclude(self.source_path):
            return False
        
        return True
    
    def _list_directory_files(self, directory: Path) -> Set[Path]:
        """List all files in a directory recursively.
        
        Args:
            directory: Directory to list
            
        Returns:
            Set of relative paths
        """
        files = set()
        
        if not directory.exists():
            return files
        
        for item in directory.glob("**/*"):
            if item.is_file() and not self._should_exclude(item):
                # Get path relative to the directory
                relative_path = item.relative_to(directory)
                files.add(relative_path)
        
        return files
    
    def synchronize(self) -> SyncResult:
        """Synchronize the directory from source to target."""
        if not self.source_path.exists():
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Source directory does not exist",
                changes_made=False,
            )
        
        if self._should_exclude(self.source_path):
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Directory is excluded",
                changes_made=False,
            )
        
        try:
            # Ensure target directory exists
            if not self.target_path.exists():
                if self.config.dry_run:
                    logger.info(f"Would create directory: {self.target_path}")
                else:
                    self.target_path.mkdir(parents=True, exist_ok=True)
            
            # List all files in source and target
            source_files = self._list_directory_files(self.source_path)
            target_files = self._list_directory_files(self.target_path)
            
            # Determine files to sync
            files_to_add = {f for f in source_files if f not in target_files}
            files_to_update = {f for f in source_files if f in target_files}
            files_to_remove = {f for f in target_files if f not in source_files}
            
            if self.config.verbose:
                logger.info(f"Directory sync {self.source_path} -> {self.target_path}:")
                logger.info(f"  - Files to add: {len(files_to_add)}")
                logger.info(f"  - Files to update: {len(files_to_update)}")
                logger.info(f"  - Files to remove: {len(files_to_remove)}")
            
            # If dry run, return
            if self.config.dry_run:
                return SyncResult(
                    success=True,
                    item_path=str(self.source_path),
                    item_type=self.type,
                    direction=self.config.direction,
                    message=f"Would synchronize directory ({len(files_to_add)} to add, {len(files_to_update)} to update, {len(files_to_remove)} to remove)",
                    changes_made=False,
                )
            
            total_changes = 0
            conflicts_resolved = 0
            bytes_transferred = 0
            
            # Use the worker pool to sync files in parallel
            with worker_pool_context(num_workers=self.config.max_workers) as pool:
                # Add new files
                add_results = {}
                for file in files_to_add:
                    source_file = self.source_path / file
                    target_file = self.target_path / file
                    
                    item = FileSyncItem(source_file, target_file, self.config)
                    task_id = pool.submit(item.synchronize)
                    add_results[file] = task_id
                
                # Update existing files
                update_results = {}
                for file in files_to_update:
                    source_file = self.source_path / file
                    target_file = self.target_path / file
                    
                    item = FileSyncItem(source_file, target_file, self.config)
                    # Only sync if needed
                    if item.needs_sync():
                        task_id = pool.submit(item.synchronize)
                        update_results[file] = task_id
                
                # Process add results
                for file, task_id in add_results.items():
                    result = pool.wait_for(task_id)
                    if result.success and result.value.changes_made:
                        total_changes += 1
                        bytes_transferred += result.value.bytes_transferred
                        conflicts_resolved += result.value.conflicts_resolved
                
                # Process update results
                for file, task_id in update_results.items():
                    result = pool.wait_for(task_id)
                    if result.success and result.value.changes_made:
                        total_changes += 1
                        bytes_transferred += result.value.bytes_transferred
                        conflicts_resolved += result.value.conflicts_resolved
                
                # Remove files if appropriate
                if self.config.conflict_strategy != ConflictResolutionStrategy.TARGET_WINS:
                    for file in files_to_remove:
                        target_file = self.target_path / file
                        if target_file.exists():
                            self._create_backup(target_file)
                            target_file.unlink()
                            total_changes += 1
            
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"Directory synchronized successfully ({total_changes} changes, {bytes_transferred} bytes transferred)",
                changes_made=total_changes > 0,
                conflicts_resolved=conflicts_resolved,
                bytes_transferred=bytes_transferred,
            )
        
        except Exception as e:
            logger.exception(f"Error synchronizing directory {self.source_path} to {self.target_path}")
            return SyncResult(
                success=False,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"Error synchronizing directory: {str(e)}",
                error=e,
                changes_made=False,
            )


class JsonSyncItem(SyncItem):
    """Synchronization item for a JSON file with merge capabilities."""
    
    def _get_type(self) -> SyncItemType:
        return SyncItemType.JSON_FILE
    
    def needs_sync(self) -> bool:
        """Check if the JSON file needs synchronization."""
        # Skip if source doesn't exist
        if not self.source_path.exists():
            return False
        
        # Skip if excluded
        if self._should_exclude(self.source_path):
            return False
        
        # If target doesn't exist, sync is needed
        if not self.target_path.exists():
            return True
        
        # Both exist, check if they differ
        try:
            source_data = self._load_json(self.source_path)
            target_data = self._load_json(self.target_path)
            
            # Check if data differs
            return source_data != target_data
        except Exception as e:
            logger.warning(f"Error comparing JSON files {self.source_path} and {self.target_path}: {str(e)}")
            # Assume different if we can't determine
            return True
    
    def _load_json(self, path: Path) -> Any:
        """Load JSON data from a file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If the file is not valid JSON
        """
        if not path.exists():
            return {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f"Invalid JSON file {path}: {str(e)}")
    
    def _save_json(self, path: Path, data: Any) -> None:
        """Save JSON data to a file.
        
        Args:
            path: Path to JSON file
            data: JSON data to save
            
        Raises:
            ValueError: If the data cannot be serialized to JSON
        """
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write data with pretty formatting
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)
        except Exception as e:
            raise ValueError(f"Error saving JSON file {path}: {str(e)}")
    
    def _deep_merge(self, source: Any, target: Any) -> Any:
        """Deep merge two JSON objects.
        
        Args:
            source: Source object
            target: Target object
            
        Returns:
            Merged object
            
        The merge strategy is:
        - For dictionaries, merge recursively
        - For lists, preserve both source and target values
        - For other types, source wins
        """
        if isinstance(source, dict) and isinstance(target, dict):
            # Merge dictionaries recursively
            result = target.copy()
            for key, value in source.items():
                if key in result:
                    result[key] = self._deep_merge(value, result[key])
                else:
                    result[key] = value
            return result
        
        elif isinstance(source, list) and isinstance(target, list):
            # For lists, preserve all values from both sides
            # Use dictionary for deduplication
            result_dict = {}
            
            # Add target items first
            for item in target:
                if isinstance(item, (dict, list)):
                    # Skip complex objects from target, they'll be handled by source
                    continue
                elif isinstance(item, (str, int, float, bool, type(None))):
                    # For primitive values, use the value as the key for deduplication
                    key = str(item)
                    result_dict[key] = item
                else:
                    # Skip unsupported types
                    continue
            
            # Add source items last (overwriting duplicates)
            for item in source:
                if isinstance(item, (dict, list)):
                    # For complex objects, convert to string for deduplication
                    key = json.dumps(item, sort_keys=True)
                    result_dict[key] = item
                elif isinstance(item, (str, int, float, bool, type(None))):
                    key = str(item)
                    result_dict[key] = item
                else:
                    # Skip unsupported types
                    continue
            
            # Convert back to list
            return list(result_dict.values())
        
        else:
            # For other types, source wins
            return source
    
    def synchronize(self) -> SyncResult:
        """Synchronize the JSON file with merge capability."""
        # Skip if we don't need to sync
        if not self.needs_sync():
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="JSON file is already in sync",
                changes_made=False,
            )
        
        # If dry run, return
        if self.config.dry_run:
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Would synchronize JSON file (dry run)",
                changes_made=False,
            )
        
        try:
            # Load source and target data
            source_data = self._load_json(self.source_path)
            
            # If target doesn't exist, just copy source data
            if not self.target_path.exists():
                self._save_json(self.target_path, source_data)
                
                # Calculate bytes transferred
                bytes_transferred = self.source_path.stat().st_size
                
                return SyncResult(
                    success=True,
                    item_path=str(self.source_path),
                    item_type=self.type,
                    direction=self.config.direction,
                    message=f"JSON file created ({bytes_transferred} bytes)",
                    changes_made=True,
                    bytes_transferred=bytes_transferred,
                )
            
            # Load target data
            target_data = self._load_json(self.target_path)
            
            # Create backup
            self._create_backup(self.target_path)
            
            # Apply appropriate strategy
            conflicts_resolved = 0
            result_data = None
            
            if self.config.conflict_strategy == ConflictResolutionStrategy.SOURCE_WINS:
                # Source overwrites target
                result_data = source_data
            
            elif self.config.conflict_strategy == ConflictResolutionStrategy.TARGET_WINS:
                # Target is preserved
                result_data = target_data
            
            elif self.config.conflict_strategy == ConflictResolutionStrategy.MERGE:
                # Merge source and target
                result_data = self._deep_merge(source_data, target_data)
                
                # Count conflicts resolved (approximate by counting merged items)
                if isinstance(source_data, dict) and isinstance(target_data, dict):
                    # Count keys in both source and target
                    common_keys = set(source_data.keys()) & set(target_data.keys())
                    for key in common_keys:
                        if source_data[key] != target_data[key]:
                            conflicts_resolved += 1
            
            else:
                # Skip or manual strategy, do nothing
                return SyncResult(
                    success=True,
                    item_path=str(self.source_path),
                    item_type=self.type,
                    direction=self.config.direction,
                    message=f"JSON file synchronization skipped due to conflict strategy {self.config.conflict_strategy.value}",
                    changes_made=False,
                )
            
            # Save result data
            if result_data is not None:
                self._save_json(self.target_path, result_data)
            
            # Calculate bytes transferred (approximate)
            source_size = self.source_path.stat().st_size
            target_size = self.target_path.stat().st_size
            bytes_transferred = max(source_size, target_size)
            
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"JSON file synchronized successfully ({conflicts_resolved} conflicts resolved)",
                changes_made=True,
                conflicts_resolved=conflicts_resolved,
                bytes_transferred=bytes_transferred,
            )
        
        except Exception as e:
            logger.exception(f"Error synchronizing JSON file {self.source_path} to {self.target_path}")
            return SyncResult(
                success=False,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"Error synchronizing JSON file: {str(e)}",
                error=e,
                changes_made=False,
            )


class GitSyncItem(SyncItem):
    """Synchronization item for a Git repository."""
    
    def _get_type(self) -> SyncItemType:
        return SyncItemType.GIT_REPO
    
    def needs_sync(self) -> bool:
        """Check if the Git repository needs synchronization."""
        # Skip if source doesn't exist
        if not self.source_path.exists():
            return False
        
        # Skip if excluded
        if self._should_exclude(self.source_path):
            return False
        
        # Check if source is a Git repository
        if not self._is_git_repo(self.source_path):
            return False
        
        # If target doesn't exist, sync is needed
        if not self.target_path.exists():
            return True
        
        # Check if target is a Git repository
        if not self._is_git_repo(self.target_path):
            return True
        
        # Check if repositories are in sync
        return not self._repos_in_sync(self.source_path, self.target_path)
    
    def _is_git_repo(self, path: Path) -> bool:
        """Check if a directory is a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if the directory is a Git repository, False otherwise
        """
        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    def _get_git_ref(self, repo_path: Path, ref: str = "HEAD") -> str:
        """Get the Git reference hash.
        
        Args:
            repo_path: Path to Git repository
            ref: Reference to get (default: HEAD)
            
        Returns:
            Git reference hash or empty string if error
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "rev-parse", ref],
                capture_output=True,
                text=True,
                check=True,
            )
            
            return result.stdout.strip()
        except subprocess.SubprocessError:
            return ""
    
    def _get_git_status(self, repo_path: Path) -> Tuple[bool, str]:
        """Get the Git repository status.
        
        Args:
            repo_path: Path to Git repository
            
        Returns:
            Tuple of (is_clean, status_output)
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            
            return (len(result.stdout.strip()) == 0, result.stdout)
        except subprocess.SubprocessError:
            return (False, "Error getting git status")
    
    def _repos_in_sync(self, repo1: Path, repo2: Path) -> bool:
        """Check if two Git repositories are in sync.
        
        Args:
            repo1: Path to first repository
            repo2: Path to second repository
            
        Returns:
            True if repositories are in sync, False otherwise
        """
        ref1 = self._get_git_ref(repo1)
        ref2 = self._get_git_ref(repo2)
        
        if not ref1 or not ref2:
            return False
        
        return ref1 == ref2
    
    def synchronize(self) -> SyncResult:
        """Synchronize the Git repository."""
        # Skip if we don't need to sync
        if not self.needs_sync():
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Git repository is already in sync",
                changes_made=False,
            )
        
        # If dry run, return
        if self.config.dry_run:
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Would synchronize Git repository (dry run)",
                changes_made=False,
            )
        
        try:
            # Check if source is a Git repository
            if not self._is_git_repo(self.source_path):
                return SyncResult(
                    success=False,
                    item_path=str(self.source_path),
                    item_type=self.type,
                    direction=self.config.direction,
                    message="Source is not a Git repository",
                    changes_made=False,
                )
            
            # Check if target is a Git repository
            if not self.target_path.exists():
                # Clone repository
                subprocess.run(
                    ["git", "clone", str(self.source_path), str(self.target_path)],
                    check=True,
                )
                
                return SyncResult(
                    success=True,
                    item_path=str(self.source_path),
                    item_type=self.type,
                    direction=self.config.direction,
                    message="Git repository cloned",
                    changes_made=True,
                )
            
            # Check if target is a Git repository
            if not self._is_git_repo(self.target_path):
                # Target exists but is not a Git repository
                return SyncResult(
                    success=False,
                    item_path=str(self.source_path),
                    item_type=self.type,
                    direction=self.config.direction,
                    message="Target exists but is not a Git repository",
                    changes_made=False,
                )
            
            # Check if there are uncommitted changes in the target
            target_clean, target_status = self._get_git_status(self.target_path)
            
            if not target_clean:
                if self.config.conflict_strategy == ConflictResolutionStrategy.SOURCE_WINS:
                    # Force reset target to match source
                    subprocess.run(
                        ["git", "-C", str(self.target_path), "reset", "--hard"],
                        check=True,
                    )
                    
                    subprocess.run(
                        ["git", "-C", str(self.target_path), "clean", "-fd"],
                        check=True,
                    )
                else:
                    # Cannot sync due to uncommitted changes
                    return SyncResult(
                        success=False,
                        item_path=str(self.source_path),
                        item_type=self.type,
                        direction=self.config.direction,
                        message="Target has uncommitted changes",
                        changes_made=False,
                    )
            
            # Get remote URL and name
            source_remote_url = self.source_path.absolute().as_uri()
            
            # Update target to match source
            # First, add source as remote if not already present
            subprocess.run(
                ["git", "-C", str(self.target_path), "remote", "add", "source", source_remote_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            
            # Fetch from source
            subprocess.run(
                ["git", "-C", str(self.target_path), "fetch", "source"],
                check=True,
            )
            
            # Get the current branch
            result = subprocess.run(
                ["git", "-C", str(self.target_path), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            
            current_branch = result.stdout.strip()
            
            # Reset to source/branch
            subprocess.run(
                ["git", "-C", str(self.target_path), "reset", "--hard", f"source/{current_branch}"],
                check=True,
            )
            
            return SyncResult(
                success=True,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message="Git repository synchronized",
                changes_made=True,
            )
        
        except Exception as e:
            logger.exception(f"Error synchronizing Git repository {self.source_path} to {self.target_path}")
            return SyncResult(
                success=False,
                item_path=str(self.source_path),
                item_type=self.type,
                direction=self.config.direction,
                message=f"Error synchronizing Git repository: {str(e)}",
                error=e,
                changes_made=False,
            )


class SyncManager:
    """Manager for synchronization operations."""
    
    def __init__(self, config: SyncConfig):
        """Initialize the synchronization manager.
        
        Args:
            config: Synchronization configuration
        """
        self.config = config
        self.results: List[SyncResult] = []
    
    def sync_path(self, source_path: Path, target_path: Path) -> SyncResult:
        """Synchronize a path (file or directory).
        
        Args:
            source_path: Source path
            target_path: Target path
            
        Returns:
            Synchronization result
        """
        # Skip if source doesn't exist
        if not source_path.exists():
            result = SyncResult(
                success=True,
                item_path=str(source_path),
                item_type=SyncItemType.FILE if source_path.is_file() else SyncItemType.DIRECTORY,
                direction=self.config.direction,
                message="Source does not exist",
                changes_made=False,
            )
            self.results.append(result)
            return result
        
        # Create appropriate sync item
        item: SyncItem
        
        if source_path.is_file():
            # Check if it's a JSON file
            if source_path.suffix.lower() == ".json":
                item = JsonSyncItem(source_path, target_path, self.config)
            else:
                item = FileSyncItem(source_path, target_path, self.config)
        
        elif self._is_git_repo(source_path):
            item = GitSyncItem(source_path, target_path, self.config)
        
        else:
            item = DirectorySyncItem(source_path, target_path, self.config)
        
        # Synchronize and record result
        result = item.synchronize()
        self.results.append(result)
        return result
    
    def _is_git_repo(self, path: Path) -> bool:
        """Check if a directory is a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if the directory is a Git repository, False otherwise
        """
        git_dir = path / ".git"
        return git_dir.exists() and git_dir.is_dir()
    
    @staticmethod
    def get_environment_type() -> EnvironmentType:
        """Detect the current environment type.
        
        Returns:
            Environment type
        """
        return _detect_environment()


def _detect_environment() -> EnvironmentType:
    """Detect the current environment type.
    
    Returns:
        Environment type
    """
    # Check environment variables
    if os.environ.get("CODESPACES", "").lower() == "true":
        return EnvironmentType.CODESPACES
    
    if os.environ.get("CLOUD_WORKSTATIONS_ENVIRONMENT", ""):
        return EnvironmentType.GCP_WORKSTATION
    
    # Check for marker files
    if Path("/.codespaces").exists():
        return EnvironmentType.CODESPACES
    
    if Path("/.gcp-workstation").exists():
        return EnvironmentType.GCP_WORKSTATION
    
    # Check for specific directories and files
    codespaces_paths = [
        Path("/home/codespace"),
        Path("/workspaces"),
    ]
    
    gcp_paths = [
        Path("/google"),
        Path("/gcp-workstations"),
    ]
    
    for path in codespaces_paths:
        if path.exists():
            return EnvironmentType.CODESPACES
    
    for path in gcp_paths:
        if path.exists():
            return EnvironmentType.GCP_WORKSTATION
    
    # Fallback
    return EnvironmentType.UNKNOWN


def synchronize_environments(
    source_dir: Union[str, Path],
    target_dir: Union[str, Path],
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
    exclude_patterns: List[str] = None,
    conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MERGE,
    max_workers: int = 8,
    dry_run: bool = False,
    verbose: bool = False,
) -> List[SyncResult]:
    """Synchronize environments.
    
    Args:
        source_dir: Source directory
        target_dir: Target directory
        direction: Synchronization direction
        exclude_patterns: Patterns to exclude
        conflict_strategy: Conflict resolution strategy
        max_workers: Maximum number of worker threads
        dry_run: Whether to perform a dry run
        verbose: Whether to enable verbose logging
        
    Returns:
        List of synchronization results
    """
    # Set default exclude patterns
    if exclude_patterns is None:
        exclude_patterns = [
            r"\.git$",
            r"\.github$",
            r"__pycache__$",
            r"\.pyc$",
            r"\.pyo$",
            r"\.pyd$",
            r"\.pytest_cache$",
            r"\.venv$",
            r"venv$",
            r"\.env$",
            r"\.idea$",
            r"\.vscode$",
            r"\.DS_Store$",
            r"\.sass-cache$",
            r"\.tox$",
            r"\.coverage$",
            r"\.coverage\.",
            r"htmlcov$",
            r"\.hypothesis$",
        ]
    
    # Convert to Path objects
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)
    
    # Create configuration
    config = SyncConfig(
        source_dir=source_dir,
        target_dir=target_dir,
        direction=direction,
        conflict_strategy=conflict_strategy,
        exclude_patterns=exclude_patterns,
        max_workers=max_workers,
        dry_run=dry_run,
        verbose=verbose,
    )
    
    # Create sync manager
    manager = SyncManager(config)
    
    # Synchronize
    manager.sync_path(source_dir, target_dir)
    
    return manager.results


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Environment Synchronization")
    parser.add_argument("--source", required=True, help="Source directory")
    parser.add_argument("--target", required=True, help="Target directory")
    parser.add_argument(
        "--direction",
        choices=["to-gcp", "to-codespaces", "bidirectional"],
        default="bidirectional",
        help="Synchronization direction",
    )
    parser.add_argument(
        "--conflict-strategy",
        choices=["source-wins", "target-wins", "merge", "manual", "skip"],
        default="merge",
        help="Conflict resolution strategy",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum number of worker threads",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Map direction
    direction_map = {
        "to-gcp": SyncDirection.CODESPACES_TO_GCP,
        "to-codespaces": SyncDirection.GCP_TO_CODESPACES,
        "bidirectional": SyncDirection.BIDIRECTIONAL,
    }
    
    # Map conflict strategy
    strategy_map = {
        "source-wins": ConflictResolutionStrategy.SOURCE_WINS,
        "target-wins": ConflictResolutionStrategy.TARGET_WINS,
        "merge": ConflictResolutionStrategy.MERGE,
        "manual": ConflictResolutionStrategy.MANUAL,
        "skip": ConflictResolutionStrategy.SKIP,
    }
    
    # Run synchronization
    results = synchronize_environments(
        source_dir=args.source,
        target_dir=args.target,
        direction=direction_map[args.direction],
        conflict_strategy=strategy_map[args.conflict_strategy],
        max_workers=args.max_workers,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    
    # Print summary
    success_count = sum(1 for r in results if r.success)
    failure_count = len(results) - success_count
    changes_count = sum(1 for r in results if r.changes_made)
    
    print(f"Synchronization complete:")
    print(f"  - Total items: {len(results)}")
    print(f"  - Successful: {success_count}")
    print(f"  - Failed: {failure_count}")
    print(f"  - Changes made: {changes_count}")
    
    if failure_count > 0:
        print("\nFailures:")
        for result in results:
            if not result.success:
                print(f"  - {result.item_path}: {result.message}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())