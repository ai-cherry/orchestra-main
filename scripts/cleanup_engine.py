#!/usr/bin/env python3
# cleaned_reference - Intelligent file cleanup with safety checks for Project Symphony

import json
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sys
import re
from typing import Dict, List, Tuple, Any, Optional
from typing_extensions import Optional

# --- Configuration ---
# Critical directories (relative to project root) that should largely be ignored
CRITICAL_DIRS = {
    ".git", "venv", ".venv", "node_modules", "dist", "build", 
    "requirements/frozen", "docs/official_releases", "data/production_seeds",
    # Add core application directories if they should not contain auto-deletable files
    "core", "shared", "services", "scripts" # These are less about deletion, more about not flagging their contents as "junk" by default
}

# Patterns for files/directories that should always be protected (basename matching)
PROTECTED_PATTERNS = [
    re.compile(r"deploy_.*\.sh"),
    re.compile(r"migration_.*\.py"),
    re.compile(r"Pulumi\.(yaml|.*\.yaml)"),
    re.compile(r"README\.md", re.IGNORECASE),
    re.compile(r"\.gitignore"),
    re.compile(r"pyproject\.toml"),
    re.compile(r"requirements.*\.txt"),
    re.compile(r"Makefile"),
    re.compile(r"\.versions\.(yaml|lock)"),
    re.compile(r"package(-lock)?\.json"),
    re.compile(r"tsconfig\.json"),
    re.compile(r"vite\.config\.(ts|js)"),
    # Add project critical file patterns
]

# File extensions often associated with temporary/generated files
POTENTIALLY_OBSOLETE_EXTENSIONS = {
    ".tmp", ".bak", ".log", ".output", ".err", ".swp", ".swo", 
    ".DS_Store", ".pyc", ".pyo", ".pyd", "__pycache__",
    ".orig", ".rej", ".backup", ".old", ".save"
}

# Name patterns often associated with temporary/generated files
POTENTIALLY_OBSOLETE_NAME_PATTERNS = [
    re.compile(r"^tmp_.*"),
    re.compile(r"^temp_.*"),
    re.compile(r".*_temp$"),
    re.compile(r"^ai_generated_.*"),
    re.compile(r"^debug_.*"),
    re.compile(r"^test_output_.*"),
    re.compile(r"^draft_v[0-9]+_.*"),
    re.compile(r".*_backup_[0-9]{8}.*"), # e.g. file_backup_20230101.zip
    re.compile(r".*\.backup\.[0-9]+$"),
    re.compile(r"^\.#.*"),  # Emacs temp files
    re.compile(r".*~$"),    # Editor backup files
]

LOG_FILE = Path("cleanup_actions.log")
CLEANUP_REGISTRY_FILE = Path(".cleanup_registry.json") # For explicit lifecycle management

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

class IntelligentCleanup:
    def __init__(self, inventory_file_path: str, project_root_path: str, dry_run: bool = True):
        self.project_root = Path(project_root_path).resolve()
        self.inventory_path = Path(inventory_file_path).resolve()
        self.inventory: List[Dict[str, Any]] = self._load_json(self.inventory_path)
        self.cleanup_registry: Dict[str, Any] = self._load_json(
            self.project_root / CLEANUP_REGISTRY_FILE, default={}
        )
        self.dry_run = dry_run
        self.automation_scripts: set[str] = self._find_scheduled_scripts()

        if not self.inventory:
            logging.warning(f"Inventory file {inventory_file_path} is empty or not found.")
            sys.exit(1)

    def _load_json(self, file_path: Path, default: Optional[Any] = None) -> Any:
        try:

            pass
            with file_path.open('r') as f:
                return json.load(f)
        except Exception:

            pass
            if default is not None:
                return default
            logging.error(f"File not found: {file_path}")
            sys.exit(1)
        except Exception:

            pass
            logging.error(f"Invalid JSON in file: {file_path}")
            if default is not None:
                return default
            sys.exit(1)

    def _find_scheduled_scripts(self) -> set[str]:
        """Rudimentary check for scheduled scripts (crontab for current user). More robust checks needed for system-wide."""
                    command_part = " ".join(parts[5:])
                    # Try to find scripts within the project root
                    # This requires script paths in cron to be absolute or identifiable
                    for item in re.split(r'\s+|;|&', command_part):
                        if item.startswith(str(self.project_root)) and Path(item).is_file():
                            scheduled.add(str(Path(item).resolve()))
        except Exception:

            pass
            logging.warning("Crontab not found or no entries for current user. Scheduled script check may be incomplete.")
        
        # Check for systemd timers
        try:

            pass
            systemctl_output = subprocess.check_output(
                ['systemctl', 'list-timers', '--all', '--no-pager'], 
                stderr=subprocess.DEVNULL, 
                text=True
            )
            # Parse systemd timer output for project-related services
            for line in systemctl_output.splitlines():
                if str(self.project_root) in line:
                    # Extract service name and try to find associated script
                    parts = line.split()
                    if len(parts) >= 5:
                        service_name = parts[4].replace('.timer', '.service')
                        # This is simplified - would need to parse service files properly
                        logging.debug(f"Found potential systemd service: {service_name}")
        except Exception:

            pass
            logging.debug("systemctl not available or no timers found.")
        
        return scheduled

    def is_safe_to_remove(self, file_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Determine if file is safe to remove based on multiple criteria. Returns (is_safe, reason)."""
            return False, "File is outside project root"

        # 1. Critical Directory Check
        if any(crit_dir in file_path.parts for crit_dir in CRITICAL_DIRS):
            # More nuanced: allow some cleanup in "scripts" if file is clearly temp
            if "scripts" in file_path.parts and any(p.match(file_path.name) for p in POTENTIALLY_OBSOLETE_NAME_PATTERNS):
                pass # Allow script files to be evaluated further
            else:
                return False, f"In critical directory '{relative_path_str}'"

        # 2. Protected Pattern Check
        if any(pattern.search(file_path.name) for pattern in PROTECTED_PATTERNS):
            return False, f"Matches protected pattern '{file_path.name}'"

        # 3. Scheduled Script Check
        if str(file_path) in self.automation_scripts:
            return False, f"Is a scheduled automation script '{relative_path_str}'"

        # 4. Explicit Expiration (from inventory or .cleanup_registry.json)
        expiration_str = file_info.get('expiration', 'none')
        if expiration_str == 'none' and str(file_path) in self.cleanup_registry:
            expiration_str = self.cleanup_registry[str(file_path)].get('expires')
        
        if expiration_str and expiration_str != 'none':
            try:

                pass
                # Attempt to parse various common date formats
                exp_date = datetime.fromisoformat(expiration_str.replace('Z', '+00:00'))
                if exp_date.tzinfo is None: # Assume UTC if no timezone
                    exp_date = exp_date.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) < exp_date:
                    return False, f"Not yet expired (expires {expiration_str})"
            except Exception:

                pass
                logging.warning(f"Could not parse expiration date '{expiration_str}' for {file_path}")
                # If unparsable, treat as non-expiring for safety unless other flags apply

        # 5. Git Tracking & Age & References (for untracked files or non-critical tracked files)
        is_git_tracked = file_info.get('git_tracked', False)
        modified_time = datetime.fromtimestamp(int(file_info.get('modified_epoch', 0)), timezone.utc)
        age_days = (datetime.now(timezone.utc) - modified_time).days
        references = int(file_info.get('references', 0))

        # Rule: Old, untracked, unreferenced files are strong candidates
        if not is_git_tracked and age_days > 90 and references == 0:
             if any(p.match(file_path.name) for p in POTENTIALLY_OBSOLETE_NAME_PATTERNS) or \
                file_path.suffix in POTENTIALLY_OBSOLETE_EXTENSIONS:
                return True, f"Old ({age_days}d), untracked, 0 refs, name/ext matches temp pattern"

        # Rule: Untracked files with temp patterns/extensions, older than 7 days
        if not is_git_tracked and age_days > 7 and \
           (any(p.match(file_path.name) for p in POTENTIALLY_OBSOLETE_NAME_PATTERNS) or \
            file_path.suffix in POTENTIALLY_OBSOLETE_EXTENSIONS):
            return True, f"Untracked, {age_days}d old, name/ext matches temp pattern"
        
        # Rule: Tracked files that look like temporary output, very old, and few refs
        # Be more careful with tracked files
        if is_git_tracked and age_days > 180 and references <= 1 and \
           (any(p.match(file_path.name) for p in POTENTIALLY_OBSOLETE_NAME_PATTERNS) or \
            file_path.suffix in POTENTIALLY_OBSOLETE_EXTENSIONS):
             # Ensure it's not a core script file unless it really looks like an old artifact
            if "scripts/" in relative_path_str and not any(p.match(file_path.name) for p in POTENTIALLY_OBSOLETE_NAME_PATTERNS):
                 return False, f"Tracked script, needs manual review despite age/refs: {relative_path_str}"
            return True, f"Tracked, very old ({age_days}d), low refs ({references}), looks like temp/output"

        # Rule: Files in .cleanup_registry that are past expiration
        if str(file_path) in self.cleanup_registry:
            entry = self.cleanup_registry[str(file_path)]
            if entry.get('expires'):
                try:

                    pass
                    exp_dt = datetime.fromisoformat(entry['expires'].replace('Z', '+00:00'))
                    if exp_dt.tzinfo is None: 
                        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) > exp_dt:
                        return True, f"Registered for cleanup and past expiration ({entry['expires']})"
                except Exception:

                    pass
                    pass # Already logged

        return False, "No specific cleanup rule matched"

    def interactive_cleanup(self):
        """Interactive cleanup with user confirmation."""
            logging.info("No files flagged for cleanup based on current rules.")
            return

        logging.info(f"Found {len(candidates_for_review)} files for potential cleanup review:")
        
        deleted_count = 0
        kept_count = 0

        for file_info, reason in candidates_for_review:
            path = Path(file_info['path'])
            size_kb = int(file_info.get('size', 0)) / 1024
            mod_date = datetime.fromtimestamp(
                int(file_info.get('modified_epoch', 0)), 
                timezone.utc
            ).strftime('%Y-%m-%d %H:%M:%S %Z')
            
            print("-" * 50)
            print(f"📁 File: {path.relative_to(self.project_root)}")
            print(f"   Reason: {reason}")
            print(f"   Size: {size_kb:.2f} KB, Modified: {mod_date}")
            print(f"   Type: {file_info.get('type', 'N/A')}, Git Tracked: {file_info.get('git_tracked', False)}")
            print(f"   References (approx): {file_info.get('references', 0)}")
            
            if self.dry_run:
                print("   Action: Would be prompted for deletion (Dry Run Mode)")
                continue

            while True:
                choice = input("   Action [d(elete)/k(eep)/v(iew)/s(kip this session)]? ").lower()
                if choice == 'd':
                    self._perform_delete(file_info)
                    deleted_count += 1
                    break
                elif choice == 'k':
                    logging.info(f"Kept file: {path}")
                    kept_count += 1
                    break
                elif choice == 'v':
                    self._view_file(path)
                elif choice == 's':
                    logging.info("Skipping further interactive review in this session.")
                    print(f"\nSummary: Deleted {deleted_count} files, Kept (reviewed) {kept_count} files in this session.")
                    return # Exit interactive loop
                else:
                    print("Invalid choice. Please use d/k/v/s.")
        
        print(f"\nCleanup Review Complete. Deleted: {deleted_count}, Kept (reviewed): {kept_count}")

    def non_interactive_cleanup(self, max_deletions: int = 50):
        """Non-interactive cleanup for automation."""
            logging.info("No files flagged for cleanup based on current rules.")
            return
        
        # Sort by safety score (could be enhanced with more sophisticated scoring)
        # For now, prioritize untracked files and older files
        def safety_score(item):
            file_info, _ = item
            score = 0
            if not file_info.get('git_tracked', False):
                score += 10
            age_days = (datetime.now(timezone.utc) - 
                       datetime.fromtimestamp(int(file_info.get('modified_epoch', 0)), timezone.utc)).days
            score += min(age_days / 10, 20)  # Cap age contribution at 20
            return score
        
        candidates_for_review.sort(key=safety_score, reverse=True)
        
        # Limit deletions
        to_delete = candidates_for_review[:max_deletions]
        
        logging.info(f"Found {len(candidates_for_review)} cleanup candidates. Processing {len(to_delete)} files.")
        
        deleted_count = 0
        for file_info, reason in to_delete:
            path = Path(file_info['path'])
            try:

                pass
                logging.info(f"Deleting: {path.relative_to(self.project_root)} - {reason}")
                self._perform_delete(file_info)
                deleted_count += 1
            except Exception:

                pass
                logging.error(f"Failed to delete {path}: {e}")
        
        logging.info(f"Non-interactive cleanup complete. Deleted {deleted_count} files.")

    def _view_file(self, file_path: Path):
        try:

            pass
            content = file_path.read_text(errors='ignore')
            print("\n--- File Content (first 500 chars) ---")
            print(content[:500])
            if len(content) > 500:
                print("... (file truncated)")
            print("--- End File Content ---\n")
        except Exception:

            pass
            print(f"Error viewing file {file_path}: {e}")

    def _perform_delete(self, file_info: Dict[str, Any]):
        path = Path(file_info['path'])
        log_message = f"File: {path.relative_to(self.project_root)}, Size: {file_info.get('size',0)}, Git: {file_info.get('git_tracked')}"
        
        if self.dry_run:
            logging.info(f"[DRY RUN] Would delete: {log_message}")
            return

        try:


            pass
            if file_info.get('git_tracked', False):
                # For git-tracked files, prefer `git rm`
                subprocess.run(['git', 'rm', str(path)], check=True, cwd=self.project_root)
                logging.info(f"Git removed: {log_message}")
            else:
                path.unlink() # Deletes the file
                logging.info(f"Deleted: {log_message}")
            
            # Remove from cleanup_registry if it was there
            if str(path) in self.cleanup_registry:
                del self.cleanup_registry[str(path)]
                self._save_json(self.project_root / CLEANUP_REGISTRY_FILE, self.cleanup_registry)

        except Exception:


            pass
            logging.error(f"Error deleting {path}: {e}")
    
    def _save_json(self, file_path: Path, data: Any):
        try:

            pass
            with file_path.open('w') as f:
                json.dump(data, f, indent=2)
        except Exception:

            pass
            logging.error(f"Error saving JSON to {file_path}: {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate a cleanup report without interactive mode."""
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_files_analyzed": len(self.inventory),
            "cleanup_candidates": len(candidates_for_review),
            "candidates": []
        }
        
        for file_info, reason in candidates_for_review:
            path = Path(file_info['path'])
            report["candidates"].append({
                "path": str(path.relative_to(self.project_root)),
                "reason": reason,
                "size": file_info.get('size', 0),
                "type": file_info.get('type', 'unknown'),
                "git_tracked": file_info.get('git_tracked', False),
                "references": file_info.get('references', 0),
                "modified": datetime.fromtimestamp(
                    int(file_info.get('modified_epoch', 0)), 
                    timezone.utc
                ).isoformat()
            })
        
        return report

def transient_file(lifetime_hours: int = 72):
    """
    """
        registry_path = Path(".cleanup_registry.json")
        current_registry = {}
        if registry_path.exists():
            with registry_path.open('r') as f:
                try:

                    pass
                    current_registry = json.load(f)
                except Exception:

                    pass
                    pass # ignore if malformed, will overwrite
        
        current_registry[str(filepath.resolve())] = {
            "expires": expiration_dt.isoformat(),
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        with registry_path.open('w') as f:
            json.dump(current_registry, f, indent=2)
        logging.info(f"Registered {filepath} for cleanup, expires {expiration_dt.isoformat()}")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Assuming the decorated function returns a Path object or string path to the created file
            file_path_result = func(*args, **kwargs)
            
            if file_path_result:
                p_result = Path(file_path_result)
                if p_result.exists(): # Ensure file was actually created
                    expiration_datetime = datetime.now(timezone.utc) + timedelta(hours=lifetime_hours)
                    register_for_cleanup(p_result, expiration_datetime)
                else:
                    logging.warning(f"Transient file decorator: function {func.__name__} returned path {p_result} but file does not exist.")
            return file_path_result
        return wrapper
    return decorator

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent file cleanup for Project Symphony")
    parser.add_argument("inventory_file", help="Path to the inventory JSON file")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup (default is dry run)")
    parser.add_argument("--report-only", action="store_true", help="Generate report only, no interactive mode")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    parser.add_argument("--ruleset", help="Specific ruleset to use (future feature)")
    parser.add_argument("--max-deletions", type=int, default=50, help="Maximum files to delete in non-interactive mode")
    
    args = parser.parse_args()
    
    # Infer project root from inventory file path (assuming inventory is in project root)
    proj_root = str(Path(args.inventory_file).resolve().parent)
    
    engine = IntelligentCleanup(
        inventory_file_path=args.inventory_file, 
        project_root_path=proj_root, 
        dry_run=not args.execute
    )
    
    if args.report_only:
        report = engine.generate_report()
        print(json.dumps(report, indent=2))
    elif args.non_interactive:
        engine.non_interactive_cleanup(max_deletions=args.max_deletions)
    else:
        engine.interactive_cleanup()
        logging.info(f"Cleanup {'DRY RUN ' if not args.execute else ''}session complete. Log: {LOG_FILE.resolve()}")