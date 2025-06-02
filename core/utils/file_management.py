#!/usr/bin/env python3
"""File management utilities with lifecycle support for Project Symphony."""

import json
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Callable, Optional, Union, Any
import atexit
import weakref

logger = logging.getLogger(__name__)

# Global registry for cleanup tracking
CLEANUP_REGISTRY_FILE = Path(".cleanup_registry.json")
_cleanup_registry_cache: Optional[dict] = None
_registered_files: weakref.WeakSet = weakref.WeakSet()

def _load_cleanup_registry() -> dict:
    """Load the cleanup registry from disk."""
    global _cleanup_registry_cache
    
    if _cleanup_registry_cache is not None:
        return _cleanup_registry_cache
    
    if CLEANUP_REGISTRY_FILE.exists():
        try:
            with CLEANUP_REGISTRY_FILE.open('r') as f:
                _cleanup_registry_cache = json.load(f)
                return _cleanup_registry_cache
        except json.JSONDecodeError:
            logger.warning(f"Corrupted cleanup registry at {CLEANUP_REGISTRY_FILE}, starting fresh")
    
    _cleanup_registry_cache = {}
    return _cleanup_registry_cache

def _save_cleanup_registry(registry: dict) -> None:
    """Save the cleanup registry to disk."""
    global _cleanup_registry_cache
    _cleanup_registry_cache = registry
    
    try:
        with CLEANUP_REGISTRY_FILE.open('w') as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save cleanup registry: {e}")

def register_for_cleanup(
    filepath: Path, 
    expiration_dt: datetime,
    metadata: Optional[dict] = None
) -> None:
    """Register a file for future cleanup.
    
    Args:
        filepath: Path to the file to register
        expiration_dt: When the file should be cleaned up
        metadata: Optional metadata about the file
    """
    registry = _load_cleanup_registry()
    
    registry[str(filepath.resolve())] = {
        "expires": expiration_dt.isoformat(),
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    
    _save_cleanup_registry(registry)
    _registered_files.add(filepath)
    logger.info(f"Registered {filepath} for cleanup, expires {expiration_dt.isoformat()}")

def unregister_from_cleanup(filepath: Path) -> None:
    """Remove a file from the cleanup registry.
    
    Args:
        filepath: Path to the file to unregister
    """
    registry = _load_cleanup_registry()
    
    filepath_str = str(filepath.resolve())
    if filepath_str in registry:
        del registry[filepath_str]
        _save_cleanup_registry(registry)
        logger.info(f"Unregistered {filepath} from cleanup")

def cleanup_expired_files(dry_run: bool = True) -> list[Path]:
    """Clean up files that have passed their expiration.
    
    Args:
        dry_run: If True, only report what would be deleted
        
    Returns:
        List of paths that were (or would be) deleted
    """
    registry = _load_cleanup_registry()
    now = datetime.now(timezone.utc)
    expired_files = []
    
    for filepath_str, info in list(registry.items()):
        try:
            expiration = datetime.fromisoformat(info['expires'].replace('Z', '+00:00'))
            if expiration.tzinfo is None:
                expiration = expiration.replace(tzinfo=timezone.utc)
            
            if now > expiration:
                filepath = Path(filepath_str)
                expired_files.append(filepath)
                
                if not dry_run:
                    try:
                        if filepath.exists():
                            filepath.unlink()
                            logger.info(f"Deleted expired file: {filepath}")
                        del registry[filepath_str]
                    except Exception as e:
                        logger.error(f"Failed to delete {filepath}: {e}")
                else:
                    logger.info(f"Would delete expired file: {filepath}")
        
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid registry entry for {filepath_str}: {e}")
    
    if not dry_run and expired_files:
        _save_cleanup_registry(registry)
    
    return expired_files

def transient_file(
    lifetime_hours: int = 72,
    cleanup_on_exit: bool = False,
    metadata: Optional[dict] = None
) -> Callable:
    """Decorator for functions that create temporary files with managed lifecycle.
    
    The decorated function should return a Path object pointing to the created file.
    The file will be registered for cleanup after the specified lifetime.
    
    Args:
        lifetime_hours: How long the file should exist before cleanup (default: 72 hours)
        cleanup_on_exit: If True, attempt cleanup when program exits
        metadata: Optional metadata to store with the file registration
        
    Example:
        @transient_file(lifetime_hours=24)
        def create_report(data: dict) -> Path:
            report_path = Path(f"reports/temp_report_{uuid4()}.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(data))
            return report_path
    """
    def decorator(func: Callable[..., Union[Path, str]]) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Union[Path, str]:
            # Call the original function
            result = func(*args, **kwargs)
            
            if result is None:
                logger.warning(f"Function {func.__name__} returned None, no file to register")
                return result
            
            # Convert string paths to Path objects
            file_path = Path(result) if isinstance(result, str) else result
            
            # Verify the file exists
            if not file_path.exists():
                logger.warning(
                    f"Function {func.__name__} returned path {file_path} but file does not exist"
                )
                return result
            
            # Calculate expiration time
            expiration = datetime.now(timezone.utc) + timedelta(hours=lifetime_hours)
            
            # Add function metadata
            enhanced_metadata = {
                "creator_function": func.__name__,
                "creator_module": func.__module__,
                **(metadata or {})
            }
            
            # Register for cleanup
            register_for_cleanup(file_path, expiration, enhanced_metadata)
            
            # Optional: Register cleanup on program exit
            if cleanup_on_exit:
                def cleanup_on_exit_handler():
                    try:
                        if file_path.exists():
                            file_path.unlink()
                            logger.info(f"Cleaned up {file_path} on exit")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {file_path} on exit: {e}")
                
                atexit.register(cleanup_on_exit_handler)
            
            return result
        
        return wrapper
    return decorator

def managed_temp_directory(
    prefix: str = "tmp_",
    lifetime_hours: int = 24,
    base_dir: Optional[Path] = None
) -> Path:
    """Create a temporary directory with lifecycle management.
    
    Args:
        prefix: Prefix for the directory name
        lifetime_hours: How long before the directory should be cleaned up
        base_dir: Base directory to create temp dir in (default: current dir)
        
    Returns:
        Path to the created directory
    """
    import tempfile
    
    base_dir = base_dir or Path.cwd()
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=base_dir))
    
    # Register the directory for cleanup
    expiration = datetime.now(timezone.utc) + timedelta(hours=lifetime_hours)
    register_for_cleanup(temp_dir, expiration, {"type": "directory"})
    
    logger.info(f"Created managed temp directory: {temp_dir}")
    return temp_dir

class ManagedFile:
    """Context manager for files with automatic lifecycle management.
    
    Example:
        with ManagedFile('output.txt', lifetime_hours=12) as f:
            f.write('Hello, world!')
    """
    
    def __init__(
        self, 
        filepath: Union[str, Path], 
        mode: str = 'w',
        lifetime_hours: int = 72,
        **kwargs
    ):
        self.filepath = Path(filepath)
        self.mode = mode
        self.lifetime_hours = lifetime_hours
        self.kwargs = kwargs
        self.file_handle = None
    
    def __enter__(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.file_handle = open(self.filepath, self.mode, **self.kwargs)
        
        # Register for cleanup
        expiration = datetime.now(timezone.utc) + timedelta(hours=self.lifetime_hours)
        register_for_cleanup(self.filepath, expiration)
        
        return self.file_handle
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            self.file_handle.close()

# Cleanup task for cron/automation
def cleanup_expired_files_task() -> int:
    """Task to clean up expired files. Suitable for cron scheduling.
    
    Returns:
        0 on success, 1 on failure
    """
    try:
        logger.info("Starting cleanup of expired files")
        expired = cleanup_expired_files(dry_run=False)
        logger.info(f"Cleaned up {len(expired)} expired files")
        return 0
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    # If run directly, perform cleanup
    import sys
    sys.exit(cleanup_expired_files_task())