#!/usr/bin/env python3
"""
Workspace Optimization Tool for AI Orchestra

This tool implements repository and workspace optimization strategies to improve
development experience, reduce load times, and manage repository size according
to the comprehensive DevOps strategy.
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import asyncio
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union, TypedDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- Configuration Constants ---
# Top-level config keys
CONFIG_WORKSPACE_SEGMENTATION = "workspace_segmentation"
CONFIG_FILE_EXCLUSIONS = "file_exclusions"
CONFIG_GIT_OPTIMIZATION = "git_optimization"
CONFIG_RESOURCE_MANAGEMENT = "resource_management"
CONFIG_ENV_MANAGEMENT = "env_management"
CONFIG_REPO_SIZE_MANAGEMENT = "repo_size_management"

# Common sub-keys
CONFIG_KEY_ENABLED = "enabled"
CONFIG_KEY_SEGMENTS = "segments"
CONFIG_KEY_CUSTOM_PATTERNS = "custom_patterns"
CONFIG_KEY_USE_ENHANCED_PATTERNS = "use_enhanced_patterns"
CONFIG_KEY_USE_SEARCH_EXCLUSIONS = "use_search_exclusions"
CONFIG_KEY_USE_SPARSE_CHECKOUT = "use_sparse_checkout"
CONFIG_KEY_USE_GIT_ATTRIBUTES = "use_git_attributes"
CONFIG_KEY_USE_SHALLOW_CLONES = "use_shallow_clones"
CONFIG_KEY_CUSTOM_GIT_ATTRIBUTES = "custom_git_attributes"
CONFIG_KEY_EXTENSIONS = "extensions"
CONFIG_KEY_RECOMMENDED = "recommended"
CONFIG_KEY_UNWANTED = "unwanted"
CONFIG_KEY_STANDARDIZE_ENV_FILES = "standardize_env_files"
CONFIG_KEY_ENV_FILE_SCHEMA = "env_file_schema"
CONFIG_KEY_REQUIRED_VARIABLES = "required_variables"
CONFIG_KEY_OPTIONAL_VARIABLES = "optional_variables"
CONFIG_KEY_LFS_THRESHOLD_KB = "lfs_threshold_kb"
# Add more as identified

# --- End Configuration Constants ---


class OptimizationCategory(str, Enum):
    """Categories of workspace optimizations."""

    WORKSPACE_SEGMENTATION = "workspace_segmentation"
    FILE_EXCLUSIONS = "file_exclusions"
    GIT_OPTIMIZATION = "git_optimization"
    RESOURCE_MANAGEMENT = "resource_management"
    ENV_MANAGEMENT = "env_management"
    VIRTUALIZATION = "virtualization"
    REPO_SIZE = "repo_size"
    ALL = "all"


class WorkspaceSegment(str, Enum):
    """Workspace segments for targeted optimization."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"
    TOOLS = "tools"
    ALL = "all"


# TypedDicts for structured statistics
class FileExtensionStats(TypedDict):
    count: int
    total_size_bytes: int


class BinaryFileStats(TypedDict):
    count: int
    total_size_bytes: int
    extensions: List[str]


class LargestFileEntry(TypedDict):
    path: str
    size_bytes: int


class FileAnalysisStats(TypedDict):
    total_count: int
    total_size_bytes: int
    by_extension: Dict[str, FileExtensionStats]
    largest_files: List[LargestFileEntry]
    binary_files: BinaryFileStats


class LargestDirectoryEntry(TypedDict):
    path: str
    size_bytes: int


class DirectoryAnalysisStats(TypedDict):
    total_count: int
    deepest_nesting: int
    deepest_path: str
    largest_directories: List[LargestDirectoryEntry]


class EnvFileInfo(TypedDict):
    path: str
    size: int
    line_count: int
    var_count: int


class OptimizationProfile:
    """Profile containing workspace optimization data and metrics."""

    def __init__(
        self,
        file_stats: FileAnalysisStats,
        directory_stats: DirectoryAnalysisStats,
        exclusion_patterns: List[str],
        git_stats: Dict[str, Any],
        env_files: List[EnvFileInfo],
    ):
        """
        Initialize the optimization profile.

        Args:
            file_stats: Statistics about files (counts, sizes, etc.)
            directory_stats: Statistics about directories
            exclusion_patterns: Current exclusion patterns
            git_stats: Git repository statistics
            env_files: Environment file information
        """
        self.file_stats = file_stats
        self.directory_stats = directory_stats
        self.exclusion_patterns = exclusion_patterns
        self.git_stats = git_stats
        self.env_files = env_files

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "file_stats": self.file_stats,
            "directory_stats": self.directory_stats,
            "exclusion_patterns": self.exclusion_patterns,
            "git_stats": self.git_stats,
            "env_files": self.env_files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationProfile":
        """Create profile from dictionary."""
        return cls(
            file_stats=data.get(
                "file_stats",
                FileAnalysisStats(
                    total_count=0,
                    total_size_bytes=0,
                    by_extension={},
                    largest_files=[],
                    binary_files=BinaryFileStats(
                        count=0, total_size_bytes=0, extensions=[]
                    ),
                ),
            ),
            directory_stats=data.get(
                "directory_stats",
                DirectoryAnalysisStats(
                    total_count=0,
                    deepest_nesting=0,
                    deepest_path=".",
                    largest_directories=[],
                ),
            ),
            exclusion_patterns=data.get("exclusion_patterns", []),
            git_stats=data.get("git_stats", {}),
            env_files=data.get("env_files", []),
        )


class ConfigLoader:
    """Handles loading and merging of workspace optimization configurations."""

    def __init__(self, config_path_str: Optional[str], base_dir: Path):
        self.config_path_str = config_path_str
        self.base_dir = base_dir
        self._yaml_available = False
        self.yaml_module = None
        try:
            import yaml  # type: ignore

            self._yaml_available = True
            self.yaml_module = yaml
            logger.debug("PyYAML is available for YAML config file parsing.")
        except ImportError:
            logger.info(
                "PyYAML not installed. YAML config files (.yaml, .yml) will not be supported. "
                "To enable YAML support, please install PyYAML (e.g., 'pip install PyYAML')."
            )

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Returns the default configuration dictionary using defined constants."""
        return {
            CONFIG_WORKSPACE_SEGMENTATION: {
                CONFIG_KEY_ENABLED: True,
                CONFIG_KEY_SEGMENTS: {
                    "frontend": ["apps/", "llm-chat/", "admin-interface/"],
                    "backend": ["ai-orchestra/", "core/", "packages/", "services/"],
                    "infrastructure": ["terraform/", "infra/", "terraform-modules/"],
                    "documentation": ["docs/"],
                    "tools": ["scripts/", "tools/"],
                },
            },
            CONFIG_FILE_EXCLUSIONS: {
                CONFIG_KEY_USE_ENHANCED_PATTERNS: True,
                CONFIG_KEY_USE_SEARCH_EXCLUSIONS: True,
                CONFIG_KEY_CUSTOM_PATTERNS: [],
            },
            CONFIG_GIT_OPTIMIZATION: {
                CONFIG_KEY_USE_SPARSE_CHECKOUT: True,
                CONFIG_KEY_USE_GIT_ATTRIBUTES: True,
                CONFIG_KEY_USE_SHALLOW_CLONES: True,
                CONFIG_KEY_CUSTOM_GIT_ATTRIBUTES: [],
            },
            CONFIG_RESOURCE_MANAGEMENT: {
                "workspace_trust": True,  # Example: Not all keys might be constants yet
                "language_server_memory_limit": 4096,
                CONFIG_KEY_EXTENSIONS: {
                    CONFIG_KEY_RECOMMENDED: [
                        "ms-python.python",
                        "ms-python.vscode-pylance",
                        "ms-azuretools.vscode-docker",
                        "hashicorp.terraform",
                        "redhat.vscode-yaml",
                        "streetsidesoftware.code-spell-checker",
                    ],
                    CONFIG_KEY_UNWANTED: [],
                },
            },
            CONFIG_ENV_MANAGEMENT: {
                CONFIG_KEY_STANDARDIZE_ENV_FILES: True,
                CONFIG_KEY_ENV_FILE_SCHEMA: {
                    CONFIG_KEY_REQUIRED_VARIABLES: [
                        "ENVIRONMENT",
                        "GCP_PROJECT_ID",
                        "GCP_REGION",
                    ],
                    CONFIG_KEY_OPTIONAL_VARIABLES: [
                        "DEBUG",
                        "LOG_LEVEL",
                        "API_PORT",
                    ],
                },
                "visual_indicators": {  # Example: Nested keys not yet constants
                    "terminal_prefix": True,
                    "vscode_color_customization": True,
                },
            },
            CONFIG_REPO_SIZE_MANAGEMENT: {
                "max_repo_size_mb": 1000,
                CONFIG_KEY_LFS_THRESHOLD_KB: 500,
                "retention_policies": {
                    "log_files_days": 7,
                    "temp_files_days": 1,
                    "build_artifacts_days": 30,
                },
                "external_storage": {
                    "large_binaries": "GCS",
                    "build_artifacts": "Artifact Registry",
                    "historical_data": "BigQuery",
                },
            },
        }

    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update a dictionary.

        Args:
            d: Dictionary to update.
            u: Dictionary with updates.

        Returns:
            Updated dictionary.
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        Returns:
            Configuration dictionary.
        """
        default_config = self.get_default_config()

        if not self.config_path_str:
            logger.info("No config path provided, using default configuration.")
            return default_config

        config_file_path = Path(self.config_path_str)
        if not config_file_path.is_absolute():
            config_file_path = self.base_dir / config_file_path
        config_file_path = config_file_path.resolve()

        if not config_file_path.exists():
            logger.warning(
                f"Config file {config_file_path} not found, using default configuration."
            )
            return default_config

        if not config_file_path.is_file():
            logger.warning(
                f"Config path {config_file_path} is not a file. Using default configuration."
            )
            return default_config

        try:
            with open(config_file_path, "r", encoding="utf-8") as f:  # Added encoding
                content = f.read()
                if not content.strip():
                    logger.warning(
                        f"Config file {config_file_path} is empty. Using default configuration."
                    )
                    return default_config
                f.seek(0)  # Reset cursor for parsing

                if config_file_path.suffix.lower() in [".yaml", ".yml"]:
                    if not self._yaml_available or self.yaml_module is None:
                        logger.error(
                            f"Cannot load YAML config file {config_file_path} because PyYAML is not available. "
                            "Please install 'PyYAML' or use a JSON config file. Falling back to defaults."
                        )
                        return default_config
                    try:
                        loaded_config_data = self.yaml_module.safe_load(f)
                    except (
                        self.yaml_module.YAMLError
                    ) as yaml_err:  # Specific YAML error
                        logger.error(
                            f"Failed to parse YAML from {config_file_path}: {str(yaml_err)}. "
                            "Falling back to default configuration."
                        )
                        return default_config
                elif config_file_path.suffix.lower() == ".json":
                    try:
                        loaded_config_data = json.load(f)
                    except json.JSONDecodeError as json_err:  # Specific JSON error
                        logger.error(
                            f"Failed to decode JSON from {config_file_path}: {str(json_err)}. "
                            "Ensure the JSON is valid. Falling back to default configuration."
                        )
                        return default_config
                else:
                    logger.warning(
                        f"Unsupported config file extension: {config_file_path.suffix}. "
                        "Please use .json, .yaml, or .yml. Falling back to defaults."
                    )
                    return default_config

            if not isinstance(loaded_config_data, dict):
                logger.error(
                    f"Configuration file {config_file_path} did not load as a dictionary (loaded type: {type(loaded_config_data)}). "
                    "Falling back to defaults."
                )
                return default_config

            merged_config = default_config.copy()
            self._deep_update(merged_config, loaded_config_data)
            logger.info(f"Loaded configuration from {config_file_path}")
            return merged_config

        except IOError as io_err:  # For issues with open(), read(), etc.
            logger.error(
                f"IOError when trying to read config file {config_file_path}: {str(io_err)}. "
                "Falling back to default configuration."
            )
            return default_config
        except (
            Exception
        ) as e:  # Catch-all for other unexpected errors during the loading logic
            logger.error(
                f"An unexpected error occurred while loading config from {config_file_path}: {str(e)}. "
                "Falling back to default configuration."
            )
            return default_config


class FileSystemAnalyzer:
    """Analyzes file system components like files and directories."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.default_skip_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        }

    def discover_env_files(self) -> List[EnvFileInfo]:
        """
        Discover environment files in the repository.
        Returns:
            List of environment file information using EnvFileInfo TypedDict.
        """
        env_files_data: List[EnvFileInfo] = []
        patterns = [".env", ".env.*", "*.env", "env.*"]

        for pattern in patterns:
            for file_path in self.base_dir.glob(pattern):
                if file_path.is_file():
                    rel_path_str = "<unknown>"
                    try:
                        rel_path = file_path.relative_to(self.base_dir)
                        rel_path_str = str(rel_path)
                        line_count = 0
                        var_count = 0
                        file_size = file_path.stat().st_size

                        with open(file_path, "r", encoding="utf-8") as f:
                            for line in f:
                                line_count += 1
                                if re.match(r"^\s*[A-Za-z0-9_]+=", line):
                                    var_count += 1

                        env_files_data.append(
                            {
                                "path": rel_path_str,
                                "size": file_size,
                                "line_count": line_count,
                                "var_count": var_count,
                            }
                        )
                    except (FileNotFoundError, PermissionError) as fs_err:
                        logger.warning(
                            f"Skipping env file {file_path} due to file system error: {str(fs_err)}"
                        )
                    except ValueError:  # from relative_to
                        logger.warning(
                            f"Skipping env file {file_path} not under base directory {self.base_dir}"
                        )
                    except IOError as io_err:
                        logger.warning(
                            f"IOError reading env file {file_path}: {str(io_err)}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Unexpected error processing env file {file_path}: {str(e)}"
                        )
        return env_files_data

    def _do_analyze_files_sync(
        self, skip_dirs_override: Optional[Set[str]] = None
    ) -> FileAnalysisStats:
        """Synchronous core logic for analyzing files."""
        stats: FileAnalysisStats = {
            "total_count": 0,
            "total_size_bytes": 0,
            "by_extension": {},
            "largest_files": [],
            "binary_files": {"count": 0, "total_size_bytes": 0, "extensions": []},
        }
        skip_dirs = self.default_skip_dirs.copy()
        if skip_dirs_override:
            skip_dirs.update(skip_dirs_override)
        largest_files_tracking: List[Tuple[str, int]] = []
        binary_file_extensions_set: Set[str] = set()

        for root_str, dirs, files in os.walk(
            self.base_dir,
            topdown=True,
            onerror=lambda err: logger.warning(
                f"Error walking directory {err.filename}: {err.strerror}"
            ),
        ):
            root_path = Path(root_str)
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            for file_name in files:
                if file_name.startswith("."):
                    continue
                file_path = root_path / file_name
                try:
                    # Ensure file still exists before trying to get relative path or stat
                    if not file_path.exists() or not file_path.is_file():
                        # logger.debug(f"File {file_path} no longer exists or is not a file. Skipping.")
                        continue
                    rel_path_str = str(file_path.relative_to(self.base_dir))
                    size = file_path.stat().st_size
                    stats["total_count"] += 1
                    stats["total_size_bytes"] += size
                    ext = file_path.suffix.lower()
                    if ext:
                        if ext not in stats["by_extension"]:
                            stats["by_extension"][ext] = {
                                "count": 0,
                                "total_size_bytes": 0,
                            }
                        stats["by_extension"][ext]["count"] += 1
                        stats["by_extension"][ext]["total_size_bytes"] += size
                    is_binary = False
                    try:
                        with open(file_path, "r", encoding="utf-8") as f_text:
                            f_text.read(1024)
                    except UnicodeDecodeError:
                        is_binary = True
                    except IOError:
                        is_binary = True  # Could be permission or other read issue for text mode
                    except Exception:
                        is_binary = True  # Broad catch for other read issues
                    if is_binary:
                        stats["binary_files"]["count"] += 1
                        stats["binary_files"]["total_size_bytes"] += size
                        if ext:
                            binary_file_extensions_set.add(ext)
                    if (
                        not largest_files_tracking
                        or size > largest_files_tracking[-1][1]
                        or len(largest_files_tracking) < 10
                    ):
                        largest_files_tracking.append((rel_path_str, size))
                        largest_files_tracking.sort(key=lambda x: x[1], reverse=True)
                        if len(largest_files_tracking) > 10:
                            largest_files_tracking.pop()
                except (FileNotFoundError, PermissionError) as fs_err:
                    # Debug for less noise
                    logger.debug(
                        f"Skipping file {file_path} during analysis: {str(fs_err)}"
                    )
                except ValueError:
                    logger.warning(
                        f"Skipping file {file_path} not under base dir {self.base_dir}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Unexpected error analyzing file {file_path}: {str(e)}"
                    )
        stats["binary_files"]["extensions"] = sorted(list(binary_file_extensions_set))
        stats["largest_files"] = [
            {"path": p, "size_bytes": s} for p, s in largest_files_tracking
        ]
        return stats

    async def analyze_files(
        self, skip_dirs_override: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze files in the workspace.

        Args:
            skip_dirs_override: Optional set of directory names to skip in addition to defaults.

        Returns:
            Dictionary with file statistics
        """
        stats = self._do_analyze_files_sync(skip_dirs_override)
        return stats

    def _do_analyze_directories_sync(
        self, skip_dirs_override: Optional[Set[str]] = None
    ) -> DirectoryAnalysisStats:
        """Synchronous core logic for analyzing directories."""
        stats: DirectoryAnalysisStats = {
            "total_count": 0,
            "deepest_nesting": 0,
            "deepest_path": "",
            "largest_directories": [],
        }
        skip_dirs = self.default_skip_dirs.copy()
        if skip_dirs_override:
            skip_dirs.update(skip_dirs_override)
        dir_sizes: Dict[str, int] = {}
        max_depth = 0
        deepest_path_candidate = "."

        for root_str, dirs, _ in os.walk(
            self.base_dir,
            topdown=True,
            onerror=lambda err: logger.warning(
                f"Error walking directory {err.filename}: {err.strerror}"
            ),
        ):
            root_path = Path(root_str)
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            try:
                rel_path_str = str(root_path.relative_to(self.base_dir))
            except ValueError:
                continue
            stats["total_count"] += 1
            current_depth = (
                len(rel_path_str.split(os.sep))
                if rel_path_str != "."
                else (1 if str(self.base_dir) == str(root_path) else 0)
            )
            if current_depth > max_depth:
                max_depth = current_depth
                deepest_path_candidate = rel_path_str
            current_dir_size = 0
            try:
                for item in root_path.iterdir():
                    if item.is_file():
                        try:
                            # Ensure item still exists before stat-ing
                            if item.exists():
                                current_dir_size += item.stat().st_size
                        except (FileNotFoundError, PermissionError) as item_err:
                            logger.debug(
                                f"Skipping item {item} in dir {root_path} for size calc: {item_err}"
                            )
                        except Exception as e_stat:  # Catch other potential stat errors
                            logger.debug(
                                f"Error stating item {item} in dir {root_path}: {e_stat}"
                            )
            except (FileNotFoundError, PermissionError) as fs_err:
                logger.warning(
                    f"Cannot iterate directory {root_path} for size calc: {str(fs_err)}"
                )
                continue
            except Exception as e_iter:  # Catch other potential iterdir errors
                logger.warning(
                    f"Error iterating directory {root_path} for size calc: {str(e_iter)}"
                )
                continue
            dir_sizes[rel_path_str] = current_dir_size
        stats["deepest_nesting"] = max_depth
        stats["deepest_path"] = (
            deepest_path_candidate
            if deepest_path_candidate
            else str(self.base_dir.name)
        )
        largest_dirs_sorted = sorted(
            dir_sizes.items(), key=lambda item: item[1], reverse=True
        )[:10]
        stats["largest_directories"] = [
            {"path": p, "size_bytes": s} for p, s in largest_dirs_sorted
        ]
        return stats

    async def analyze_directories(
        self, skip_dirs_override: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze directories in the workspace.

        Args:
            skip_dirs_override: Optional set of directory names to skip in addition to defaults.

        Returns:
            Dictionary with directory statistics
        """
        stats = self._do_analyze_directories_sync(skip_dirs_override)
        return stats


class GitOptimizerHelper:
    """Handles Git-specific analysis and optimization tasks."""

    def __init__(self, base_dir: Path, config: Dict[str, Any]):
        self.base_dir = base_dir
        self.git_dir = self.base_dir / ".git"
        self.config = config
        self.git_attributes_defaults = [
            "*.png binary",
            "*.jpg binary",
            "*.jpeg binary",
            "*.gif binary",
            "*.ico binary",
            "*.mov binary",
            "*.mp4 binary",
            "*.mp3 binary",
            "*.flv binary",
            "*.fla binary",
            "*.swf binary",
            "*.gz binary",
            "*.zip binary",
            "*.7z binary",
            "*.ttf binary",
            "*.eot binary",
            "*.woff binary",
            "*.woff2 binary",
            "*.pyc binary",
            "*.pdf binary",
            "*.ez binary",
            "*.bz2 binary",
            "*.swp binary",
            "*.webp binary",
            "*.jar binary",
            "*.jks binary",
            "*.tar binary",
            "*.tgz binary",
            "*.war binary",
        ]

    async def analyze_git_repo(self) -> Dict[str, Any]:
        """
        Analyze Git repository.
        Returns:
            Dictionary with Git statistics.
        """
        stats: Dict[str, Any] = {
            "is_git_repo": False,
            "repo_size_bytes": 0,
            "objects_count": 0,
            "largest_objects": [],
            "error_messages": [],
        }

        if not self.git_dir.exists() or not self.git_dir.is_dir():
            msg = f"No Git repository found at {self.git_dir}. Skipping Git analysis."
            logger.info(msg)
            stats["error_messages"].append(msg)
            return stats

        # Check if git command is available early
        try:
            git_version_proc = await asyncio.create_subprocess_exec(
                "git",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr_git_version = await git_version_proc.communicate()
            if git_version_proc.returncode != 0:
                err_msg = f"Git command seems unavailable or failing: {stderr_git_version.decode().strip() if stderr_git_version else 'Unknown error'}"
                logger.error(err_msg)
                stats["error_messages"].append(err_msg)
                return stats  # Cannot proceed if git is not working
        except FileNotFoundError:
            err_msg = (
                "Git command not found. Please ensure Git is installed and in PATH."
            )
            logger.error(err_msg)
            stats["error_messages"].append(err_msg)
            return stats
        except Exception as e_git_check:  # Catch other startup errors
            err_msg = f"Unexpected error checking Git availability: {str(e_git_check)}"
            logger.error(err_msg)
            stats["error_messages"].append(err_msg)
            return stats

        stats["is_git_repo"] = True

        try:
            objects_dir = self.git_dir / "objects"
            if objects_dir.exists() and objects_dir.is_dir():
                # This can be very slow for large repos, consider alternatives or making it optional
                # For now, wrapping in a to_thread call as it's blocking I/O
                try:
                    total_size = await asyncio.to_thread(
                        sum,
                        (
                            f.stat().st_size
                            for f in objects_dir.rglob("*")
                            if f.is_file()
                        ),
                    )
                    stats["repo_size_bytes"] = total_size
                except Exception as e_size_calc:
                    err_msg = f"Could not calculate .git/objects size: {e_size_calc}"
                    logger.warning(err_msg)
                    stats["error_messages"].append(err_msg)
            else:
                logger.warning(f"Git objects directory not found at {objects_dir}")
                stats["error_messages"].append(
                    f"Git objects directory not found at {objects_dir}"
                )

            count_proc = await asyncio.create_subprocess_exec(
                "git",
                "count-objects",
                "-v",
                cwd=self.base_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_count, stderr_count = await count_proc.communicate()
            if count_proc.returncode == 0 and stdout_count:
                for line in stdout_count.decode().splitlines():
                    if line.startswith("count:"):
                        try:
                            stats["objects_count"] = int(line.split(":")[1].strip())
                            break
                        except (IndexError, ValueError) as e:
                            err_msg = (
                                f"Could not parse objects_count from line '{line}': {e}"
                            )
                            logger.warning(err_msg)
                            stats["error_messages"].append(err_msg)
            elif stderr_count or count_proc.returncode != 0:
                err_msg = f"Error running 'git count-objects': {stderr_count.decode().strip() if stderr_count else 'Return code: ' + str(count_proc.returncode)}"
                logger.warning(err_msg)
                stats["error_messages"].append(err_msg)

            rev_list_proc = await asyncio.create_subprocess_exec(
                "git",
                "rev-list",
                "--objects",
                "--all",
                cwd=self.base_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_rev_list, stderr_rev_list = await rev_list_proc.communicate()
            if rev_list_proc.returncode == 0 and stdout_rev_list:
                object_hashes = [
                    line.strip().split()[0]
                    for line in stdout_rev_list.decode().splitlines()
                    if line.strip()
                ]
                if object_hashes:
                    batch_check_input = "\n".join(object_hashes)
                    cat_file_proc = await asyncio.create_subprocess_exec(
                        # objectsize:disk for actual size
                        "git",
                        "cat-file",
                        "--batch-check=%(objectname) %(objecttype) %(objectsize:disk)",
                        cwd=self.base_dir,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout_cat_file, stderr_cat_file = await cat_file_proc.communicate(
                        input=batch_check_input.encode()
                    )
                    if cat_file_proc.returncode == 0 and stdout_cat_file:
                        object_details = []
                        for line in stdout_cat_file.decode().splitlines():
                            parts = line.strip().split()
                            if len(parts) == 3 and parts[1] == "blob":
                                try:
                                    object_details.append(
                                        {"hash": parts[0], "size_bytes": int(parts[2])}
                                    )
                                except ValueError:
                                    logger.warning(
                                        f"Could not parse object size from: {line}"
                                    )
                        object_details.sort(key=lambda x: x["size_bytes"], reverse=True)
                        stats["largest_objects"] = object_details[:10]
                    elif stderr_cat_file or cat_file_proc.returncode != 0:
                        err_msg = f"Error running 'git cat-file --batch-check': {stderr_cat_file.decode().strip() if stderr_cat_file else 'Return code: ' + str(cat_file_proc.returncode)}"
                        logger.warning(err_msg)
                        stats["error_messages"].append(err_msg)
            elif stderr_rev_list or rev_list_proc.returncode != 0:
                err_msg = f"Error running 'git rev-list --objects --all': {stderr_rev_list.decode().strip() if stderr_rev_list else 'Return code: ' + str(rev_list_proc.returncode)}"
                logger.warning(err_msg)
                stats["error_messages"].append(err_msg)
        except Exception as e:
            err_msg = f"Unexpected error during Git repository analysis: {str(e)}"
            logger.error(err_msg)
            stats["error_messages"].append(err_msg)
        return stats

    async def implement_git_attributes(self) -> bool:
        """Writes or updates the .gitattributes file."""
        if not self.git_dir.exists():
            logger.warning(
                "Not a Git repository (or .git directory missing), skipping .gitattributes generation."
            )
            return False

        attributes_path = self.base_dir / ".gitattributes"
        # Use constants for config access
        git_optimization_config = self.config.get(CONFIG_GIT_OPTIMIZATION, {})
        custom_attributes = git_optimization_config.get(
            CONFIG_KEY_CUSTOM_GIT_ATTRIBUTES, []
        )
        all_attributes = self.git_attributes_defaults + custom_attributes

        try:
            with open(attributes_path, "w", encoding="utf-8") as f:
                f.write("# Auto-generated by WorkspaceOptimizer for AI Orchestra\n")
                f.write("# Managed by GitOptimizerHelper\n\n")
                for attribute_line in all_attributes:
                    f.write(f"{attribute_line}\n")
            logger.info(
                f"Successfully wrote/updated .gitattributes file: {attributes_path}"
            )
            return True
        except IOError as e_io:
            logger.error(
                f"IOError writing .gitattributes file {attributes_path}: {str(e_io)}"
            )
            return False
        except Exception as e_general:
            logger.error(
                f"Unexpected error writing .gitattributes file {attributes_path}: {str(e_general)}"
            )
            return False

    async def configure_git_lfs(self) -> bool:
        # ... (existing content of configure_git_lfs) ...
        # Inside configure_git_lfs, if you were to use the LFS threshold from config:
        # lfs_management_config = self.config.get(CONFIG_REPO_SIZE_MANAGEMENT, {})
        # lfs_threshold_kb = lfs_management_config.get(CONFIG_KEY_LFS_THRESHOLD_KB, 500)
        # logger.info(f"LFS threshold from config: {lfs_threshold_kb}KB (currently used for logging, not direct LFS command filtering here)")
        # ... (rest of configure_git_lfs method body)
        pass
