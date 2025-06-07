#!/usr/bin/env python3
"""File management utilities with lifecycle support for Project Symphony."""
CLEANUP_REGISTRY_FILE = Path(".cleanup_registry.json")
_cleanup_registry_cache: Optional[dict] = None
_registered_files: weakref.WeakSet = weakref.WeakSet()

def _load_cleanup_registry() -> dict:
    """Load the cleanup registry from disk."""
            logger.warning(f"Corrupted cleanup registry at {CLEANUP_REGISTRY_FILE}, starting fresh")
    
    _cleanup_registry_cache = {}
    return _cleanup_registry_cache

def _save_cleanup_registry(registry: dict) -> None:
    """Save the cleanup registry to disk."""
        logger.error(f"Failed to save cleanup registry: {e}")

def register_for_cleanup(
    filepath: Path, 
    expiration_dt: datetime,
    metadata: Optional[dict] = None
) -> None:
    """
    """
        "expires": expiration_dt.isoformat(),
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    
    _save_cleanup_registry(registry)
    _registered_files.add(filepath)
    logger.info(f"Registered {filepath} for cleanup, expires {expiration_dt.isoformat()}")

def unregister_from_cleanup(filepath: Path) -> None:
    """
    """
        logger.info(f"Unregistered {filepath} from cleanup")

def cleanup_expired_files(dry_run: bool = True) -> list[Path]:
    """
    """
                            logger.info(f"Deleted expired file: {filepath}")
                        del registry[filepath_str]
                    except Exception:

                        pass
                        logger.error(f"Failed to delete {filepath}: {e}")
                else:
                    logger.info(f"Would delete expired file: {filepath}")
        
        except Exception:

        
            pass
            logger.warning(f"Invalid registry entry for {filepath_str}: {e}")
    
    if not dry_run and expired_files:
        _save_cleanup_registry(registry)
    
    return expired_files

def transient_file(
    lifetime_hours: int = 72,
    cleanup_on_exit: bool = False,
    metadata: Optional[dict] = None
) -> Callable:
    """
            report_path = Path(f"reports/temp_report_{uuid4()}.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(data))
            return report_path
    """
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

                        pass
                        if file_path.exists():
                            file_path.unlink()
                            logger.info(f"Cleaned up {file_path} on exit")
                    except Exception:

                        pass
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
    """
    """
    register_for_cleanup(temp_dir, expiration, {"type": "directory"})
    
    logger.info(f"Created managed temp directory: {temp_dir}")
    return temp_dir

class ManagedFile:
    """
    """
    """
    """
        logger.info("Starting cleanup of expired files")
        expired = cleanup_expired_files(dry_run=False)
        logger.info(f"Cleaned up {len(expired)} expired files")
        return 0
    except Exception:

        pass
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    # If run directly, perform cleanup
    import sys
    sys.exit(cleanup_expired_files_task())