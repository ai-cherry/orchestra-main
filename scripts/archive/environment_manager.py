#!/usr/bin/env python3
"""
Environment Manager for AI Orchestra

This script provides comprehensive environment management for the AI Orchestra project:
1. Clear visual indicators of the current environment
2. Proper environment switching with validation
3. Workspace optimization for better performance
4. Repository size monitoring and management

Usage:
  python environment_manager.py status
  python environment_manager.py switch [dev|staging|prod]
  python environment_manager.py optimize-workspace
  python environment_manager.py repo-size
  python environment_manager.py cleanup [--dry-run]
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Environment-specific colors
    DEV = "\033[102m\033[30m"  # Green background with black text
    STAGING = "\033[103m\033[30m"  # Yellow background with black text
    PROD = "\033[101m\033[97m"  # Red background with white text
    UNKNOWN = "\033[100m\033[97m"  # Grey background with white text

    @staticmethod
    def is_supported() -> bool:
        """Check if the terminal supports ANSI color codes."""
        return bool(
            sys.platform != "win32"
            or os.environ.get("TERM")
            or os.environ.get("WT_SESSION")  # Windows Terminal
        )


class EnvironmentManager:
    """Manages environment settings for AI Orchestra."""

    ENVIRONMENTS = ["dev", "staging", "prod"]
    ENV_FILES = {
        "dev": ".env.development",
        "staging": ".env.staging",
        "prod": ".env.production",
    }
    VSCODE_SETTINGS_PATH = ".vscode/settings.json"

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the environment manager.

        Args:
            base_dir: The base directory of the project
        """
        self.base_dir = base_dir or Path(os.path.dirname(os.path.abspath(__file__)))
        self.env_indicators = {
            ".dev_mode": "dev",
            ".staging_mode": "staging",
            ".prod_mode": "prod",
        }

    def get_current_environment(self) -> str:
        """
        Determine the current environment.

        Returns:
            The current environment (dev, staging, prod, or unknown)
        """
        # Check environment indicator files
        for indicator, env in self.env_indicators.items():
            if (self.base_dir / indicator).exists():
                return env

        # Check environment variables
        env_var = os.environ.get("AI_ORCHESTRA_ENV")
        if env_var:
            return env_var

        # Check .env files for active status
        for env, env_file in self.ENV_FILES.items():
            env_path = self.base_dir / env_file
            if env_path.exists() and self._is_env_file_active(env_path):
                return env

        # Default to unknown for safety
        return "unknown"

    def _is_env_file_active(self, env_path: Path) -> bool:
        """
        Check if an .env file is the active one.

        Args:
            env_path: Path to the .env file

        Returns:
            True if the file is active, False otherwise
        """
        # Look for "ACTIVE=true" in the file
        if not env_path.exists():
            return False

        with open(env_path, "r") as f:
            for line in f:
                if line.strip() == "ACTIVE=true":
                    return True
        return False

    def switch_environment(self, target_env: str) -> bool:
        """
        Switch to the specified environment.

        Args:
            target_env: The environment to switch to

        Returns:
            True if successful, False otherwise
        """
        if target_env not in self.ENVIRONMENTS:
            print(f"Error: Unknown environment '{target_env}'")
            print(f"Available environments: {', '.join(self.ENVIRONMENTS)}")
            return False

        # Remove all indicator files
        for indicator in self.env_indicators.keys():
            indicator_path = self.base_dir / indicator
            if indicator_path.exists():
                indicator_path.unlink()

        # Create the new indicator file
        for indicator, env in self.env_indicators.items():
            if env == target_env:
                indicator_path = self.base_dir / indicator
                indicator_path.touch()
                break

        # Update .env files
        for env, env_file in self.ENV_FILES.items():
            env_path = self.base_dir / env_file
            if env_path.exists():
                self._update_env_file_status(env_path, env == target_env)

        # Create environment file if it doesn't exist
        target_env_path = self.base_dir / self.ENV_FILES.get(
            target_env, f".env.{target_env}"
        )
        if not target_env_path.exists():
            with open(target_env_path, "w") as f:
                f.write(f"# {target_env.upper()} Environment Configuration\n")
                f.write("ACTIVE=true\n")
                f.write(f"AI_ORCHESTRA_ENV={target_env}\n")

        # Update VS Code env indicators
        self._update_vscode_env_indicators(target_env)

        print(f"Successfully switched to {target_env} environment")
        return True

    def _update_env_file_status(self, env_path: Path, active: bool) -> None:
        """
        Update the ACTIVE status in an .env file.

        Args:
            env_path: Path to the .env file
            active: Whether the file should be active
        """
        if not env_path.exists():
            return

        lines = []
        active_line_exists = False

        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("ACTIVE="):
                    lines.append(f"ACTIVE={'true' if active else 'false'}\n")
                    active_line_exists = True
                else:
                    lines.append(line)

        if not active_line_exists:
            lines.append(f"ACTIVE={'true' if active else 'false'}\n")

        with open(env_path, "w") as f:
            f.writelines(lines)

    def _update_vscode_env_indicators(self, current_env: str) -> None:
        """
        Update VS Code settings to indicate current environment.

        Args:
            current_env: Current environment
        """
        settings_path = self.base_dir / self.VSCODE_SETTINGS_PATH
        if not settings_path.exists():
            return

        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)

            # Set window title to include environment
            settings["window.title"] = (
                f"AI Orchestra [${{activeEditorShort}}] - {current_env.upper()}"
            )

            # Set color customizations based on environment
            if "workbench.colorCustomizations" not in settings:
                settings["workbench.colorCustomizations"] = {}

            color_customizations = settings["workbench.colorCustomizations"]

            # Reset all environment-specific colors
            for key in list(color_customizations.keys()):
                if any(env in key for env in ["[Dev]", "[Staging]", "[Prod]"]):
                    del color_customizations[key]

            # Apply color for current environment
            if current_env == "dev":
                color_customizations["[Dev]"] = {
                    "activityBar.background": "#215732",
                    "titleBar.activeBackground": "#215732",
                    "titleBar.activeForeground": "#ffffff",
                }
            elif current_env == "staging":
                color_customizations["[Staging]"] = {
                    "activityBar.background": "#7d6307",
                    "titleBar.activeBackground": "#7d6307",
                    "titleBar.activeForeground": "#ffffff",
                }
            elif current_env == "prod":
                color_customizations["[Prod]"] = {
                    "activityBar.background": "#7f1d1d",
                    "titleBar.activeBackground": "#7f1d1d",
                    "titleBar.activeForeground": "#ffffff",
                }

            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=2)

        except Exception as e:
            print(f"Error updating VS Code settings: {str(e)}")

    def display_status(self) -> None:
        """Display the current environment status."""
        current_env = self.get_current_environment()

        # Display environment banner
        self._print_environment_banner(current_env)

        # Display environment files
        print("\nEnvironment Files:")
        for env, env_file in self.ENV_FILES.items():
            env_path = self.base_dir / env_file
            if env_path.exists():
                active = self._is_env_file_active(env_path)
                status = "ACTIVE" if active else "inactive"
                print(f"  {env_file}: {status}")
            else:
                print(f"  {env_file}: not found")

        # Display environment variables
        print("\nEnvironment Variables:")
        for name in ["AI_ORCHESTRA_ENV", "NODE_ENV", "PYTHON_ENV"]:
            value = os.environ.get(name, "not set")
            print(f"  {name}: {value}")

        # Display active Python environment
        print("\nPython Environment:")
        try:
            venv_path = os.environ.get("VIRTUAL_ENV")
            if venv_path:
                print(f"  Virtual env: {venv_path}")
            else:
                print("  Virtual env: not activated")

            python_version = platform.python_version()
            print(f"  Python version: {python_version}")

            pip_path = shutil.which("pip") or "pip"
            result = subprocess.run(
                [pip_path, "list"], capture_output=True, text=True, check=False
            )
            pkg_count = (
                len(result.stdout.strip().split("\n")) - 2
            )  # Subtract header rows
            print(f"  Installed packages: {pkg_count}")
        except Exception as e:
            print(f"  Error getting Python info: {str(e)}")

    def _print_environment_banner(self, env: str) -> None:
        """
        Print a prominent environment banner.

        Args:
            env: The current environment
        """
        if not Colors.is_supported():
            print("=" * 80)
            print(f"CURRENT ENVIRONMENT: {env.upper()}")
            print("=" * 80)
            return

        color = getattr(Colors, env.upper(), Colors.UNKNOWN)
        width = 80

        print("\n" + "=" * width)
        print(f"{color}{' ' * width}{Colors.RESET}")

        env_text = f"CURRENT ENVIRONMENT: {env.upper()}"
        padding = (width - len(env_text)) // 2
        print(
            f"{color}{' ' * padding}{env_text}{' ' * (width - padding - len(env_text))}{Colors.RESET}"
        )

        print(f"{color}{' ' * width}{Colors.RESET}")
        print("=" * width + "\n")

    def optimize_workspace(self) -> None:
        """Optimize VS Code workspace settings for better performance."""
        settings_path = self.base_dir / self.VSCODE_SETTINGS_PATH

        if not settings_path.exists():
            settings_path.parent.mkdir(exist_ok=True)
            settings = {}
        else:
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {settings_path}")
                return

        # Enhanced exclusions to improve performance
        if "files.exclude" not in settings:
            settings["files.exclude"] = {}

        files_exclude = settings["files.exclude"]

        additional_excludes = {
            "**/__pycache__": True,
            "**/.pytest_cache": True,
            "**/*.pyc": True,
            "**/.mypy_cache": True,
            "**/.ruff_cache": True,
            "**/.coverage": True,
            "**/.DS_Store": True,
            "**/node_modules": True,
            "**/dist": True,
            "**/build": True,
            ".venv": True,
            "google-cloud-sdk/**": True,
            "google-cloud-sdk.staging/**": True,
            "**/*.egg-info": True,
            "**/*.log": True,
            "**/__snapshots__": True,
            "**/.git": True,
        }

        for key, value in additional_excludes.items():
            if key not in files_exclude:
                files_exclude[key] = value

        # Enhanced search excludes
        if "search.exclude" not in settings:
            settings["search.exclude"] = {}

        search_exclude = settings["search.exclude"]

        additional_search_excludes = {
            "**/node_modules": True,
            "**/.venv": True,
            "**/build": True,
            "**/dist": True,
            "google-cloud-sdk/**": True,
            "**/generated/**": True,
            "**/coverage/**": True,
            "**/tmp/**": True,
            "**/logs/**": True,
        }

        for key, value in additional_search_excludes.items():
            if key not in search_exclude:
                search_exclude[key] = value

        # Add workspace performance settings
        performance_settings = {
            "files.watcherExclude": {
                "**/.git/objects/**": True,
                "**/.git/subtree-cache/**": True,
                "**/node_modules/**": True,
                "**/.hg/store/**": True,
                "**/dist/**": True,
                "**/build/**": True,
                "**/.venv/**": True,
                "google-cloud-sdk/**": True,
            },
            "search.searchOnType": False,  # Disable search-as-you-type for performance
            "search.searchOnTypeDebouncePeriod": 300,  # Increase debounce period
            "files.autoSave": "afterDelay",  # Enable autosave
            "files.autoSaveDelay": 1000,  # 1-second delay
            "editor.formatOnSaveMode": "modificationsIfAvailable",  # Only format modified content
            "files.useExperimentalFileWatcher": True,  # Use experimental file watcher for better performance
            "workbench.editor.enablePreview": True,  # Use preview to reduce memory usage
            "workbench.editor.limit.enabled": True,  # Enable editor limit
            "workbench.editor.limit.value": 10,  # Maximum number of open editors
            "workbench.editor.limit.perEditorGroup": True,  # Apply limit per editor group
        }

        for key, value in performance_settings.items():
            if key not in settings:
                settings[key] = value

        # Add environment comment
        settings_comment = "\n// VS Code settings for AI Orchestra project\n  // Optimized for performance on large repositories\n"

        # Write the updated settings
        with open(settings_path, "w") as f:
            settings_str = json.dumps(settings, indent=2)
            settings_str = "{\n" + settings_comment + settings_str[1:]
            f.write(settings_str)

        print(
            "Successfully optimized VS Code workspace settings for better performance"
        )

    def analyze_repository_size(self) -> Dict[str, Any]:
        """
        Analyze repository size and find large files/directories.

        Returns:
            Dictionary with analysis results
        """
        print("Analyzing repository size...")

        # Get total repository size
        total_size = 0
        file_count = 0
        largest_files = []
        largest_dirs = {}

        excluded_dirs = {
            ".git",
            "node_modules",
            ".venv",
            "google-cloud-sdk",
            "google-cloud-sdk.staging",
        }

        # Walk the repository
        for root, dirs, files in os.walk(self.base_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            # Calculate directory size
            dir_size = 0
            dir_path = Path(root)
            relative_path = dir_path.relative_to(self.base_dir)

            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                dir_size += file_size
                total_size += file_size
                file_count += 1

                # Track largest files (> 1MB)
                if file_size > 1024 * 1024:
                    largest_files.append(
                        {
                            "path": str(Path(file_path).relative_to(self.base_dir)),
                            "size": file_size,
                            "size_human": self._format_size(file_size),
                        }
                    )

            # Track directory sizes
            if dir_size > 5 * 1024 * 1024:  # 5MB
                largest_dirs[str(relative_path)] = {
                    "size": dir_size,
                    "size_human": self._format_size(dir_size),
                }

        # Sort largest files and limit to top 20
        largest_files.sort(key=lambda x: x["size"], reverse=True)
        largest_files = largest_files[:20]

        # Convert largest dirs to sorted list
        largest_dirs_list = [
            {"path": path, "size": info["size"], "size_human": info["size_human"]}
            for path, info in largest_dirs.items()
        ]
        largest_dirs_list.sort(key=lambda x: x["size"], reverse=True)
        largest_dirs_list = largest_dirs_list[:20]

        # Generate human-readable report
        print("\nRepository Size Analysis:")
        print(f"Total size: {self._format_size(total_size)}")
        print(f"Total files: {file_count}")

        print("\nLargest Directories:")
        for dir_info in largest_dirs_list:
            print(f"  {dir_info['path']}: {dir_info['size_human']}")

        print("\nLargest Files:")
        for file_info in largest_files:
            print(f"  {file_info['path']}: {file_info['size_human']}")

        # GitHub size warning
        github_warning = False
        if total_size > 1 * 1024 * 1024 * 1024:  # 1GB
            github_warning = True
            print(
                "\n⚠️  WARNING: Repository size exceeds 1GB, which may cause issues with GitHub."
            )
            print(
                "   Consider using Git LFS for large files or implementing a clean-up strategy."
            )
        elif total_size > 500 * 1024 * 1024:  # 500MB
            github_warning = True
            print(
                "\n⚠️  WARNING: Repository size is approaching GitHub's recommended maximum (500MB)."
            )
            print("   Consider implementing a clean-up strategy soon.")

        return {
            "total_size": total_size,
            "total_size_human": self._format_size(total_size),
            "file_count": file_count,
            "largest_files": largest_files,
            "largest_dirs": largest_dirs_list,
            "github_warning": github_warning,
        }

    def cleanup_repository(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up the repository to reduce size.

        Args:
            dry_run: If True, only show what would be deleted without actually deleting

        Returns:
            Dictionary with cleanup results
        """
        print(f"{'Analyzing' if dry_run else 'Performing'} repository cleanup...")

        # Targets for cleanup
        cleanup_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/.pytest_cache",
            "**/.mypy_cache",
            "**/.ruff_cache",
            "**/node_modules",
            "**/dist",
            "**/build",
            "**/*.egg-info",
            "**/.DS_Store",
            "**/*.log",
            "**/tmp",
            "**/.coverage",
            "**/coverage",
            "**/htmlcov",
        ]

        # Potential large files by extension
        large_file_extensions = [
            ".zip",
            ".tar.gz",
            ".tgz",
            ".tar",
            ".rar",
            ".jar",
            ".war",
            ".ear",
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".iso",
            ".dmg",
            ".exe",
            ".pdf",
            ".psd",
            ".ai",
            ".h5",
            ".hdf5",
            ".pkl",
            ".model",
        ]

        deleted_files = []
        deleted_dirs = []
        large_files = []
        cleaned_size = 0

        # Find and delete cleanup targets
        for pattern in cleanup_patterns:
            for path in Path(self.base_dir).glob(pattern):
                rel_path = path.relative_to(self.base_dir)

                if path.is_file():
                    size = path.stat().st_size
                    cleaned_size += size
                    deleted_files.append(
                        {
                            "path": str(rel_path),
                            "size": size,
                            "size_human": self._format_size(size),
                        }
                    )

                    if not dry_run:
                        path.unlink()

                elif path.is_dir():
                    size = self._get_dir_size(path)
                    cleaned_size += size
                    deleted_dirs.append(
                        {
                            "path": str(rel_path),
                            "size": size,
                            "size_human": self._format_size(size),
                        }
                    )

                    if not dry_run:
                        shutil.rmtree(path)

        # Find large files
        for ext in large_file_extensions:
            for path in Path(self.base_dir).glob(f"**/*{ext}"):
                if path.is_file() and path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                    rel_path = path.relative_to(self.base_dir)
                    size = path.stat().st_size

                    large_files.append(
                        {
                            "path": str(rel_path),
                            "size": size,
                            "size_human": self._format_size(size),
                        }
                    )

        # Sort results
        deleted_files.sort(key=lambda x: x["size"], reverse=True)
        deleted_dirs.sort(key=lambda x: x["size"], reverse=True)
        large_files.sort(key=lambda x: x["size"], reverse=True)

        # Print results
        action = "Would clean" if dry_run else "Cleaned"
        print(f"\n{action} up: {self._format_size(cleaned_size)}")

        print(f"\n{action} remove {len(deleted_dirs)} directories:")
        for dir_info in deleted_dirs[:10]:  # Show top 10
            print(f"  {dir_info['path']}: {dir_info['size_human']}")

        if len(deleted_dirs) > 10:
            print(f"  ... and {len(deleted_dirs) - 10} more")

        print(f"\n{action} remove {len(deleted_files)} files:")
        for file_info in deleted_files[:10]:  # Show top 10
            print(f"  {file_info['path']}: {file_info['size_human']}")

        if len(deleted_files) > 10:
            print(f"  ... and {len(deleted_files) - 10} more")

        if large_files:
            print("\nPotential large files to consider for Git LFS:")
            for file_info in large_files[:10]:  # Show top 10
                print(f"  {file_info['path']}: {file_info['size_human']}")

            if len(large_files) > 10:
                print(f"  ... and {len(large_files) - 10} more")

        if dry_run:
            print("\nThis was a dry run. To actually perform the cleanup, run:")
            print("  python environment_manager.py cleanup --no-dry-run")

        return {
            "cleaned_size": cleaned_size,
            "cleaned_size_human": self._format_size(cleaned_size),
            "deleted_files": deleted_files,
            "deleted_dirs": deleted_dirs,
            "large_files": large_files,
        }

    def _get_dir_size(self, path: Path) -> int:
        """
        Calculate directory size recursively.

        Args:
            path: Directory path

        Returns:
            Directory size in bytes
        """
        total_size = 0
        for item in path.glob("**/*"):
            if item.is_file():
                total_size += item.stat().st_size
        return int(total_size)

    def _format_size(self, size: int) -> str:
        """
        Format size in human-readable form.

        Args:
            size: Size in bytes

        Returns:
            Human-readable size string
        """
        size_float = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_float < 1024.0:
                return f"{size_float:.2f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.2f} PB"


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="AI Orchestra Environment Manager")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Status command
    subparsers.add_parser("status", help="Show environment status")

    # Switch command
    switch_parser = subparsers.add_parser("switch", help="Switch environment")
    switch_parser.add_argument(
        "environment",
        choices=["dev", "staging", "prod"],
        help="Environment to switch to",
    )

    # Optimize workspace command
    subparsers.add_parser(
        "optimize-workspace", help="Optimize VS Code workspace settings"
    )

    # Repository size command
    subparsers.add_parser("repo-size", help="Analyze repository size")

    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        "cleanup", help="Clean up repository to reduce size"
    )
    cleanup_parser.add_argument(
        "--no-dry-run",
        action="store_true",
        help="Actually perform deletion (default is dry run)",
    )

    args = parser.parse_args()

    env_manager = EnvironmentManager()

    if args.command == "status":
        env_manager.display_status()

    elif args.command == "switch":
        env_manager.switch_environment(args.environment)
        env_manager.display_status()

    elif args.command == "optimize-workspace":
        env_manager.optimize_workspace()

    elif args.command == "repo-size":
        env_manager.analyze_repository_size()

    elif args.command == "cleanup":
        env_manager.cleanup_repository(dry_run=not args.no_dry_run)

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
