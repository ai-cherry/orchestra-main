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
from typing import Dict, List, Optional, Set, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


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


class OptimizationProfile:
    """Profile containing workspace optimization data and metrics."""
    
    def __init__(
        self,
        file_stats: Dict[str, Any],
        directory_stats: Dict[str, Any],
        exclusion_patterns: List[str],
        git_stats: Dict[str, Any],
        env_files: List[Dict[str, Any]],
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
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationProfile':
        """Create profile from dictionary."""
        return cls(
            file_stats=data.get("file_stats", {}),
            directory_stats=data.get("directory_stats", {}),
            exclusion_patterns=data.get("exclusion_patterns", []),
            git_stats=data.get("git_stats", {}),
            env_files=data.get("env_files", []),
        )


class WorkspaceOptimizer:
    """
    Workspace optimizer implementing repository and IDE optimization strategies.
    """
    
    def __init__(
        self,
        base_dir: str = ".",
        config_path: Optional[str] = None,
        data_dir: str = ".workspace_optimization",
        max_data_size_mb: int = 50,
    ):
        """
        Initialize the workspace optimizer.
        
        Args:
            base_dir: Base directory of the project
            config_path: Path to configuration file (optional)
            data_dir: Directory to store optimization data
            max_data_size_mb: Maximum size for optimization data in MB
        """
        self.base_dir = Path(base_dir)
        self.config_path = config_path
        
        # Set up data directory with size management
        self.data_dir = self.base_dir / data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.max_data_size_mb = max_data_size_mb
        
        # Load configuration
        self.config = self._load_config()
        
        # Environment configuration
        self.env_files = self._discover_env_files()
        
        # Default VSCode exclusion patterns
        self.default_exclusions = [
            "**/__pycache__",
            "**/.pytest_cache",
            "**/*.pyc",
            ".mypy_cache",
            ".ruff_cache",
            "**/.DS_Store",
            "**/node_modules",
            "google-cloud-sdk/**",
            "google-cloud-sdk.staging/**",
        ]
        
        # Enhanced exclusion patterns
        self.enhanced_exclusions = self.default_exclusions + [
            "**/.venv",
            "**/venv",
            "**/.ipynb_checkpoints",
            "**/dist",
            "**/build",
            "**/.coverage",
            "**/htmlcov",
            "**/*.egg-info",
            "**/*.egg",
            "**/*.so",
            "**/*.dll",
            "**/*.pyd",
            "**/Thumbs.db",
            "**/*.log",
            "**/logs",
            "**/*.bak",
            "**/*.swp",
            "**/*.tmp",
            "**/temp",
            ".git/**",
        ]
        
        # Segment-specific exclusions
        self.segment_exclusions = {
            WorkspaceSegment.FRONTEND: [
                "**/node_modules",
                "**/.cache",
                "**/coverage",
                "**/dist",
                "**/build",
                "**/.npm",
                "**/.yarn",
            ],
            WorkspaceSegment.BACKEND: [
                "**/__pycache__",
                "**/*.pyc",
                "**/*.pyo",
                "**/.pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "**/.coverage",
                "**/htmlcov",
                "**/*.egg-info",
            ],
            WorkspaceSegment.INFRASTRUCTURE: [
                "**/.terraform",
                "**/.terraform.lock.hcl",
                "**/terraform.tfstate*",
                "**/terraform.tfvars",
                "**/terraform.tfplan",
                "**/.terragrunt-cache",
            ],
            WorkspaceSegment.DOCUMENTATION: [
                "**/_build",
                "**/.doctrees",
                "**/*.aux",
                "**/*.bbl",
                "**/*.bcf",
                "**/*.blg",
                "**/*.run.xml",
                "**/*.synctex.gz",
                "**/*.toc",
            ],
            WorkspaceSegment.TOOLS: [
                "**/node_modules",
                "**/__pycache__",
                "**/*.pyc",
                "**/dist",
                "**/build",
            ],
        }
        
        # Search exclusions (separate from file exclusions)
        self.search_exclusions = self.enhanced_exclusions + [
            "**/*.min.js",
            "**/*.min.css",
            "**/*.map",
            "**/*.bundle.js",
            "**/*.bundle.css",
            "**/vendor/**",
            "**/third_party/**",
            "**/generated/**",
            "**/translations/**",
            "**/*.pb.go",
            "**/*.pb.*.go",
            "**/*.generated.*",
        ]
        
        # Git optimization settings
        self.git_attributes = [
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
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Returns:
            Configuration dictionary
        """
        default_config = {
            "workspace_segmentation": {
                "enabled": True,
                "segments": {
                    "frontend": ["apps/", "llm-chat/", "admin-interface/"],
                    "backend": ["ai-orchestra/", "core/", "packages/", "services/"],
                    "infrastructure": ["terraform/", "infra/", "terraform-modules/"],
                    "documentation": ["docs/"],
                    "tools": ["scripts/", "tools/"],
                },
            },
            "file_exclusions": {
                "use_enhanced_patterns": True,
                "use_search_exclusions": True,
                "custom_patterns": [],
            },
            "git_optimization": {
                "use_sparse_checkout": True,
                "use_git_attributes": True,
                "use_shallow_clones": True,
                "custom_git_attributes": [],
            },
            "resource_management": {
                "workspace_trust": True,
                "language_server_memory_limit": 4096,
                "extensions": {
                    "recommended": [
                        "ms-python.python",
                        "ms-python.vscode-pylance",
                        "ms-azuretools.vscode-docker",
                        "hashicorp.terraform",
                        "redhat.vscode-yaml",
                        "streetsidesoftware.code-spell-checker",
                    ],
                    "unwanted": [],
                },
            },
            "env_management": {
                "standardize_env_files": True,
                "env_file_schema": {
                    "required_variables": [
                        "ENVIRONMENT",
                        "GCP_PROJECT_ID",
                        "GCP_REGION",
                    ],
                    "optional_variables": [
                        "DEBUG",
                        "LOG_LEVEL",
                        "API_PORT",
                    ],
                },
                "visual_indicators": {
                    "terminal_prefix": True,
                    "vscode_color_customization": True,
                },
            },
            "repo_size_management": {
                "max_repo_size_mb": 1000,
                "lfs_threshold_kb": 500,
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
        
        if not self.config_path:
            return default_config
        
        config_path = Path(self.config_path)
        if not config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # Merge with defaults (for any missing keys)
            merged_config = default_config.copy()
            self._deep_update(merged_config, config)
            return merged_config
            
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return default_config
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update a dictionary.
        
        Args:
            d: Dictionary to update
            u: Dictionary with updates
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
    
    def _discover_env_files(self) -> List[Dict[str, Any]]:
        """
        Discover environment files in the repository.
        
        Returns:
            List of environment file information
        """
        env_files = []
        
        # Common env file patterns
        patterns = [
            ".env",
            ".env.*",
            "*.env",
            "env.*",
        ]
        
        # Find all env files
        for pattern in patterns:
            for file_path in self.base_dir.glob(pattern):
                if file_path.is_file():
                    # Get relative path
                    rel_path = file_path.relative_to(self.base_dir)
                    
                    # Count lines and variables
                    line_count = 0
                    var_count = 0
                    
                    try:
                        with open(file_path, 'r') as f:
                            for line in f:
                                line_count += 1
                                if re.match(r'^\s*[A-Za-z0-9_]+=', line):
                                    var_count += 1
                    except Exception as e:
                        logger.warning(f"Error reading {rel_path}: {str(e)}")
                    
                    env_files.append({
                        "path": str(rel_path),
                        "size": file_path.stat().st_size,
                        "line_count": line_count,
                        "var_count": var_count,
                    })
        
        return env_files
    
    async def analyze_workspace(self) -> OptimizationProfile:
        """
        Analyze the workspace and collect optimization metrics.
        
        Returns:
            Optimization profile with workspace metrics
        """
        # Collect file statistics
        file_stats = await self._analyze_files()
        
        # Collect directory statistics
        directory_stats = await self._analyze_directories()
        
        # Collect current exclusion patterns
        exclusion_patterns = await self._collect_current_exclusions()
        
        # Collect Git statistics
        git_stats = await self._analyze_git_repo()
        
        # Create optimization profile
        profile = OptimizationProfile(
            file_stats=file_stats,
            directory_stats=directory_stats,
            exclusion_patterns=exclusion_patterns,
            git_stats=git_stats,
            env_files=self.env_files,
        )
        
        # Save profile with size management
        await self._save_optimization_profile(profile)
        
        return profile
    
    async def _analyze_files(self) -> Dict[str, Any]:
        """
        Analyze files in the workspace.
        
        Returns:
            Dictionary with file statistics
        """
        stats = {
            "total_count": 0,
            "total_size_bytes": 0,
            "by_extension": {},
            "largest_files": [],
            "binary_files": {
                "count": 0,
                "total_size_bytes": 0,
                "extensions": set(),
            },
        }
        
        # Skip hidden directories
        skip_dirs = {".git", ".venv", "node_modules", "__pycache__"}
        
        # Collect stats
        largest_files = []
        
        for root, dirs, files in os.walk(self.base_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            
            for file in files:
                file_path = Path(root) / file
                
                # Get relative path
                try:
                    rel_path = file_path.relative_to(self.base_dir)
                except ValueError:
                    continue
                
                # Skip hidden files
                if file.startswith("."):
                    continue
                
                try:
                    # Get file size
                    size = file_path.stat().st_size
                    
                    # Update statistics
                    stats["total_count"] += 1
                    stats["total_size_bytes"] += size
                    
                    # Update extension stats
                    ext = file_path.suffix.lower()
                    if ext:
                        if ext not in stats["by_extension"]:
                            stats["by_extension"][ext] = {
                                "count": 0,
                                "total_size_bytes": 0,
                            }
                        stats["by_extension"][ext]["count"] += 1
                        stats["by_extension"][ext]["total_size_bytes"] += size
                    
                    # Check if binary file
                    is_binary = False
                    try:
                        with open(file_path, 'r') as f:
                            f.read(1024)
                    except UnicodeDecodeError:
                        is_binary = True
                    
                    if is_binary:
                        stats["binary_files"]["count"] += 1
                        stats["binary_files"]["total_size_bytes"] += size
                        stats["binary_files"]["extensions"].add(ext)
                    
                    # Track largest files
                    largest_files.append((str(rel_path), size))
                    largest_files.sort(key=lambda x: x[1], reverse=True)
                    largest_files = largest_files[:10]
                    
                except Exception as e:
                    logger.warning(f"Error analyzing {rel_path}: {str(e)}")
        
        # Convert set to list for JSON serialization
        stats["binary_files"]["extensions"] = list(stats["binary_files"]["extensions"])
        
        # Add largest files to stats
        stats["largest_files"] = [
            {"path": path, "size_bytes": size}
            for path, size in largest_files
        ]
        
        return stats
    
    async def _analyze_directories(self) -> Dict[str, Any]:
        """
        Analyze directories in the workspace.
        
        Returns:
            Dictionary with directory statistics
        """
        stats = {
            "total_count": 0,
            "deepest_nesting": 0,
            "largest_directories": [],
        }
        
        # Skip hidden directories
        skip_dirs = {".git", ".venv", "node_modules", "__pycache__"}
        
        # Collect directory sizes
        dir_sizes = {}
        deepest_path = ""
        max_depth = 0
        
        for root, dirs, files in os.walk(self.base_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            
            # Get relative path
            try:
                rel_path = Path(root).relative_to(self.base_dir)
            except ValueError:
                continue
            
            # Update directory count
            stats["total_count"] += 1
            
            # Calculate directory depth
            depth = len(str(rel_path).split(os.sep))
            if depth > max_depth:
                max_depth = depth
                deepest_path = str(rel_path)
            
            # Calculate directory size
            dir_size = sum(
                file.stat().st_size
                for file in Path(root).iterdir()
                if file.is_file()
            )
            
            dir_sizes[str(rel_path)] = dir_size
        
        # Update deepest nesting
        stats["deepest_nesting"] = max_depth
        stats["deepest_path"] = deepest_path
        
        # Add largest directories to stats
        largest_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:10]
        stats["largest_directories"] = [
            {"path": path, "size_bytes": size}
            for path, size in largest_dirs
        ]
        
        return stats
    
    async def _collect_current_exclusions(self) -> List[str]:
        """
        Collect current exclusion patterns from VSCode settings.
        
        Returns:
            List of current exclusion patterns
        """
        vscode_settings_path = self.base_dir / ".vscode" / "settings.json"
        
        if not vscode_settings_path.exists():
            return []
        
        try:
            with open(vscode_settings_path, 'r') as f:
                settings = json.load(f)
            
            # Get file exclusions
            file_excludes = settings.get("files.exclude", {})
            return [pattern for pattern in file_excludes.keys()]
            
        except Exception as e:
            logger.warning(f"Error reading VSCode settings: {str(e)}")
            return []
    
    async def _analyze_git_repo(self) -> Dict[str, Any]:
        """
        Analyze Git repository.
        
        Returns:
            Dictionary with Git statistics
        """
        stats = {
            "is_git_repo": False,
            "repo_size_bytes": 0,
            "objects_count": 0,
            "largest_objects": [],
        }
        
        git_dir = self.base_dir / ".git"
        
        if not git_dir.exists():
            return stats
        
        stats["is_git_repo"] = True
        
        try:
            # Get repository size
            objects_dir = git_dir / "objects"
            repo_size = sum(
                f.stat().st_size
                for f in objects_dir.glob("**/*")
                if f.is_file()
            )
            stats["repo_size_bytes"] = repo_size
            
            # Count objects
            result = subprocess.run(
                ["git", "count-objects", "-v"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            
            for line in result.stdout.splitlines():
                if line.startswith("count:"):
                    stats["objects_count"] = int(line.split(":")[1].strip())
            
            # Find large objects
            try:
                result = subprocess.run(
                    ["git", "rev-list", "--objects", "--all"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                
                objects = []
                for line in result.stdout.splitlines():
                    parts = line.strip().split()
                    if len(parts) > 1:
                        objects.append(parts[1])
                
                if objects:
                    # Get object sizes
                    result = subprocess.run(
                        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
                        cwd=self.base_dir,
                        input="\n".join(objects),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    
                    object_sizes = []
                    for line in result.stdout.splitlines():
                        parts = line.strip().split()
                        if len(parts) == 3 and parts[1] == "blob":
                            object_sizes.append((parts[0], int(parts[2])))
                    
                    # Sort by size
                    object_sizes.sort(key=lambda x: x[1], reverse=True)
                    
                    # Get largest objects
                    largest_objects = []
                    for obj_hash, size in object_sizes[:10]:
                        # Get file path
                        result = subprocess.run(
                            ["git", "log", "--all", "--format=%H", f"--ancestry-path={obj_hash}"],
                            cwd=self.base_dir,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        
                        if result.stdout.strip():
                            commit = result.stdout.splitlines()[0].strip()
                            
                            result = subprocess.run(
                                ["git", "ls-tree", "-r", commit],
                                cwd=self.base_dir,
                                capture_output=True,
                                text=True,
                                check=False,
                            )
                            
                            for line in result.stdout.splitlines():
                                if obj_hash in line:
                                    parts = line.strip().split()
                                    if len(parts) >= 4:
                                        path = " ".join(parts[3:])
                                        largest_objects.append({
                                            "hash": obj_hash,
                                            "path": path,
                                            "size_bytes": size,
                                        })
                                        break
                    
                    stats["largest_objects"] = largest_objects
            except Exception as e:
                logger.warning(f"Error finding large Git objects: {str(e)}")
            
        except Exception as e:
            logger.warning(f"Error analyzing Git repository: {str(e)}")
        
        return stats
    
    async def _save_optimization_profile(self, profile: OptimizationProfile) -> None:
        """
        Save optimization profile with size management.
        
        Args:
            profile: Optimization profile to save
        """
        # Check total data directory size
        total_size = sum(
            f.stat().st_size
            for f in self.data_dir.glob("*.json")
            if f.is_file()
        )
        
        # Convert MB to bytes
        max_size_bytes = self.max_data_size_mb * 1024 * 1024
        
        # If approaching size limit, archive old files
        if total_size > max_size_bytes * 0.9:
            await self._archive_old_profiles()
        
        # Create a timestamped filename
        filename = f"profile_{int(time.time())}.json"
        filepath = self.data_dir / filename
        
        # Save as JSON
        with open(filepath, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
        
        logger.info(f"Saved optimization profile to {filepath}")
    
    async def _archive_old_profiles(self) -> None:
        """Archive old optimization profiles to maintain data directory size."""
        logger.info("Archiving old optimization profiles")
        
        # Get all profile files
        profile_files = list(self.data_dir.glob("profile_*.json"))
        
        # Sort by creation time (oldest first)
        profile_files.sort(key=lambda x: x.stat().st_ctime)
        
        # Keep only the 5 most recent files
        files_to_archive = profile_files[:-5] if len(profile_files) > 5 else []
        
        if not files_to_archive:
            return
        
        # Create archive directory
        archive_dir = self.data_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Move files to archive
        for file in files_to_archive:
            try:
                shutil.move(str(file), str(archive_dir / file.name))
                logger.debug(f"Archived {file.name}")
            except Exception as e:
                logger.warning(f"Error archiving {file.name}: {str(e)}")
    
    async def implement_workspace_segmentation(self) -> bool:
        """
        Implement workspace segmentation.
        
        Returns:
            True if successful
        """
        logger.info("Implementing workspace segmentation")
        
        # Check if workspace segmentation is enabled
        if not self.config.get("workspace_segmentation", {}).get("enabled", False):
            logger.info("Workspace segmentation is disabled in config")
            return False
        
        # Create .vscode directory if it doesn't exist
        vscode_dir = self.base_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # Create workspace configuration file
        workspace_config = {
            "folders": [],
            "settings": {},
        }
        
        # Add each segment as a folder
        segments = self.config.get("workspace_segmentation", {}).get("segments", {})
        
        for segment_name, segment_paths in segments.items():
            # Verify that at least one path exists
            valid_paths = [
                path for path in segment_paths
                if (self.base_dir / path).exists()
            ]
            
            if valid_paths:
                workspace_config["folders"].append({
                    "name": segment_name,
                    "path": valid_paths[0],  # Use the first valid path
                })
        
        # Add settings
        workspace_config["settings"] = {
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {
                "source.organizeImports": True,
                "source.fixAll": True,
            },
            "python.linting.enabled": True,
            "python.linting.pylintEnabled": False,
            "python.linting.flake8Enabled": True,
            "python.formatting.provider": "black",
        }
        
        # Save workspace configuration
        workspace_path = self.base_dir / "ai-orchestra.code-workspace"
        
        try:
            with open(workspace_path, 'w') as f:
                json.dump(workspace_config, f, indent=2)
            
            logger.info(f"Created workspace configuration: {workspace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create workspace configuration: {str(e)}")
            return False
    
    async def implement_file_exclusions(self) -> bool:
        """
        Implement enhanced file exclusions.
        
        Returns:
            True if successful
        """
        logger.info("Implementing file exclusions")
        
        # Check if enhanced exclusions are enabled
        if not self.config.get("file_exclusions", {}).get("use_enhanced_patterns", False):
            logger.info("Enhanced file exclusions are disabled in config")
            return False
        
        # Create .vscode directory if it doesn't exist
        vscode_dir = self.base_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # Load existing settings
        settings_path = vscode_dir / "settings.json"
        settings = {}
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
            except Exception as e:
                logger.warning(f"Error reading settings: {str(e)}")
        
        # Update file exclusions
        files_exclude = {}
        
        # Add all enhanced exclusions
        for pattern in self.enhanced_exclusions:
            files_exclude[pattern] = True
        
        # Add custom patterns from config
        custom_patterns = self.config.get("file_exclusions", {}).get("custom_patterns", [])
        for pattern in custom_patterns:
            files_exclude[pattern] = True
        
        # Update settings
        settings["files.exclude"] = files_exclude
        
        # Add search exclusions if enabled
        if self.config.get("file_exclusions", {}).get("use_search_exclusions", False):
            search_exclude = {}
            
            for pattern in self.search_exclusions:
                search_exclude[pattern] = True
            
            settings["search.exclude"] = search_exclude
        
        # Save settings
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"Updated VSCode settings: {settings_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update VSCode settings: {str(e)}")
            return False
    
    async def implement_git_optimization(self) -> bool:
        """
        Implement Git optimization.
        
        Returns:
            True if successful
        """
        logger.info("Implementing Git optimization")
        
        # Check if Git optimization is enabled
        git_config = self.config.get("git_optimization", {})
        if not any(git_config.get(k, False) for k in [
            "use_sparse_checkout",
            "use_git_attributes",
            "use_shallow_clones",
        ]):
            logger.info("Git optimization is disabled in config")
            return False
        
        # Check if this is a Git repository
        git_dir = self.base_dir / ".git"
        if not git_dir.exists():
            logger.warning("Not a Git repository, skipping Git optimization")
            return False
        
        success = True
        
        # Implement Git attributes
        if git_config.get("use_git_attributes", False):
            attributes_path = self.base_dir / ".gitattributes"
            
            try:
                # Create or update .gitattributes
                with open(attributes_path, 'w') as f:
                    # Add standard attributes
                    for attribute in self.git_attributes:
                        f.write(f"{attribute}\n")
                    
                    # Add custom attributes
                    custom_attributes = git_config.get("custom_git_attributes", [])
                    for attribute in custom_attributes:
                        f.write(f"{attribute}\n")
                
                logger.info(f"Updated Git attributes: {attributes_path}")
                
            except Exception as e:
                logger.error(f"Failed to update Git attributes: {str(e)}")
                success = False
        
        # Set Git config for optimization
        try:
            # Configure Git LFS if available
            result = subprocess.run(
                ["git", "lfs", "version"],
                cwd=self.base_dir,
                capture_output=True,
                check=False,
            )
            
            if result.returncode == 0:
                # Git LFS is available, configure it
                logger.info("Configuring Git LFS")
                
                # Set up Git LFS
                subprocess.run(
                    ["git", "lfs", "install"],
                    cwd=self.base_dir,
                    check=False,
                )
                
                # Track large files with LFS
                lfs_threshold_kb = self.config.get("repo_size_management", {}).get("lfs_threshold_kb", 500)
                
                # Add common binary file patterns
                for pattern in [
                    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.pdf", "*.zip", "*.gz",
                    "*.jar", "*.war", "*.mp4", "*.mp3", "*.mov", "*.avi",
                ]:
                    subprocess.run(
                        ["git", "lfs", "track", pattern],
                        cwd=self.base_dir,
                        check=False,
                    )
                
                logger.info(f"Configured Git LFS for files larger than {lfs_threshold_kb}KB")
        
        except Exception as e:
            logger.error(f"Failed to configure Git: {str(e)}")
            success = False
        
        return success
    
    async def standardize_env_files(self) -> bool:
        """
        Standardize environment files.
        
        Returns:
            True if successful
        """
        logger.info("Standardizing environment files")
        
        # Check if environment standardization is enabled
        if not self.config.get("env_management", {}).get("standardize_env_files", False):
            logger.info("Environment file standardization is disabled in config")
            return False
        
        # Get environment schema
        env_schema = self.config.get("env_management", {}).get("env_file_schema", {})
        required_vars = env_schema.get("required_variables", [])
        optional_vars = env_schema.get("optional_variables", [])
        
        # Check for existing environment files
        env_files = [Path(file["path"]) for file in self.env_files]
        
        # Create standardized template
        template_path = self.base_dir / ".env.template"
        
        try:
            with open(template_path, 'w') as f:
                f.write("# AI Orchestra Environment Configuration\n")
                f.write("# Generated template for standardized environment variables\n\n")
                
                f.write("# Required Variables\n")
                for var in required_vars:
                    f.write(f"{var}=\n")
                
                f.write("\n# Optional Variables\n")
                for var in optional_vars:
                    f.write(f"# {var}=\n")
            
            logger.info(f"Created environment template: {template_path}")
            
            # Create environment-specific templates if they don't exist
            for env_name in ["development", "staging", "production"]:
                env_path = self.base_dir / f".env.{env_name}"
                
                if not env_path.exists():
                    with open(env_path, 'w') as f:
                        f.write(f"# AI Orchestra {env_name.capitalize()} Environment\n")
                        f.write("# Generated from template\n\n")
                        
                        f.write("# Required Variables\n")
                        f.write(f"ENVIRONMENT={env_name}\n")
                        
                        for var in required_vars:
                            if var != "ENVIRONMENT":
                                f.write(f"{var}=\n")
                        
                        f.write("\n# Optional Variables\n")
                        for var in optional_vars:
                            f.write(f"# {var}=\n")
                    
                    logger.info(f"Created environment file: {env_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to standardize environment files: {str(e)}")
            return False
    
    async def implement_virtualization_config(self) -> bool:
        """
        Implement virtualization configuration.
        
        Returns:
            True if successful
        """
        logger.info("Implementing virtualization configuration")
        
        # Create or update Poetry configuration
        pyproject_path = self.base_dir / "pyproject.toml"
        
        if not pyproject_path.exists():
            logger.warning("pyproject.toml not found, skipping virtualization config")
            return False
        
        # Create or update .vscode settings for Python
        vscode_dir = self.base_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        settings_path = vscode_dir / "settings.json"
        settings = {}
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
            except Exception as e:
                logger.warning(f"Error reading settings: {str(e)}")
        
        # Update Python settings
        # Update Python settings
        settings.update({
            "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
            "python.terminal.activateEnvironment": True,
            "python.linting.enabled": True,
            "python.linting.flake8Enabled": True,
            "python.formatting.provider": "black",
            "python.formatting.blackPath": "${workspaceFolder}/.venv/bin/black",
            "python.linting.flake8Path": "${workspaceFolder}/.venv/bin/flake8",
            "python.linting.mypyPath": "${workspaceFolder}/.venv/bin/mypy",
        })
        # Save settings
        try:
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"Updated VSCode Python settings: {settings_path}")
            
            # Create or update Docker Compose configuration
            docker_compose_path = self.base_dir / "docker-compose.yml"
            
            if not docker_compose_path.exists():
                # Create basic Docker Compose config
                docker_compose = {
                    "version": "3",
                    "services": {
                        "api": {
                            "build": {
                                "context": ".",
                                "dockerfile": "Dockerfile",
                            },
                            "volumes": [
                                ".:/app",
                            ],
                            "ports": [
                                "8000:8000",
                            ],
                            "environment": [
                                "ENVIRONMENT=development",
                            ],
                        },
                    },
                }
                
                import yaml
                with open(docker_compose_path, 'w') as f:
                    yaml.dump(docker_compose, f, default_flow_style=False)
                
                logger.info(f"Created Docker Compose config: {docker_compose_path}")
            
            # Create virtualization setup script
            setup_script_path = self.base_dir / "setup_venv.sh"
            
            with open(setup_script_path, 'w') as f:
                f.write("#!/bin/bash\n\n")
                f.write("# Setup Python virtual environment for AI Orchestra\n\n")
                
                f.write("# Ensure python 3.11+ is available\n")
                f.write('if ! command -v python3.11 &> /dev/null; then\n')
                f.write('    echo "Python 3.11+ is required but not found"\n')
                f.write('    echo "Please install Python 3.11+ and try again"\n')
                f.write('    exit 1\n')
                f.write('fi\n\n')
                
                f.write("# Create virtual environment if it doesn't exist\n")
                f.write('if [ ! -d ".venv" ]; then\n')
                f.write('    echo "Creating virtual environment..."\n')
                f.write('    python3.11 -m venv .venv\n')
                f.write('fi\n\n')
                
                f.write("# Activate virtual environment\n")
                f.write('source .venv/bin/activate\n\n')
                
                f.write("# Install dependencies with Poetry\n")
                f.write('if ! command -v poetry &> /dev/null; then\n')
                f.write('    echo "Installing Poetry..."\n')
                f.write('    pip install poetry\n')
                f.write('fi\n\n')
                
                f.write("# Install project dependencies\n")
                f.write('echo "Installing project dependencies..."\n')
                f.write('poetry install\n\n')
                
                f.write("# Install pre-commit hooks\n")
                f.write('if ! command -v pre-commit &> /dev/null; then\n')
                f.write('    echo "Installing pre-commit..."\n')
                f.write('    pip install pre-commit\n')
                f.write('fi\n\n')
                
                f.write('pre-commit install\n\n')
                
                f.write('echo "Virtual environment setup complete!"\n')
                f.write('echo "Run source .venv/bin/activate to activate the environment"\n')
            
            # Make script executable
            setup_script_path.chmod(setup_script_path.stat().st_mode | 0o755)
            
            logger.info(f"Created virtualization setup script: {setup_script_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to implement virtualization config: {str(e)}")
            return False
    
    async def implement_repository_size_management(self) -> bool:
        """
        Implement repository size management.
        
        Returns:
            True if successful
        """
        logger.info("Implementing repository size management")
        
        # Create or update .gitignore
        gitignore_path = self.base_dir / ".gitignore"
        
        try:
            # Read existing .gitignore
            gitignore_lines = []
            if gitignore_path.exists():
                with open(gitignore_path, 'r') as f:
                    gitignore_lines = [line.strip() for line in f.readlines()]
            
            # Add size management entries
            size_management_entries = [
                "# Repository Size Management",
                ".workspace_optimization/",
                ".performance_data/",
                "**/*.log",
                "**/*.tmp",
                "temp/",
                "tmp/",
                "**/__pycache__/",
                "**/*.pyc",
                "**/*.pyo",
                "**/*.pyd",
                "**/.pytest_cache/",
                "**/.coverage",
                "**/htmlcov/",
                "**/.mypy_cache/",
                "**/.ruff_cache/",
                "**/*.egg-info/",
                "**/*.egg",
                "**/dist/",
                "**/build/",
                "**/.ipynb_checkpoints/",
                "**/node_modules/",
                "**/logs/",
            ]
            
            # Add entries if they don't exist
            for entry in size_management_entries:
                if entry not in gitignore_lines:
                    gitignore_lines.append(entry)
            
            # Write updated .gitignore
            with open(gitignore_path, 'w') as f:
                f.write("\n".join(gitignore_lines))
                f.write("\n")
            
            logger.info(f"Updated .gitignore for size management: {gitignore_path}")
            
            # Create repository cleanup script
            cleanup_script_path = self.base_dir / "cleanup_repo.sh"
            
            with open(cleanup_script_path, 'w') as f:
                f.write("#!/bin/bash\n\n")
                f.write("# Repository cleanup script for AI Orchestra\n\n")
                
                f.write("echo 'Cleaning up repository...\n\n")
                
                f.write("# Remove temporary files\n")
                f.write('find . -name "*.tmp" -delete\n')
                f.write('find . -name "*.log" -mtime +7 -delete\n')
                f.write('find . -path "*/temp/*" -delete\n')
                f.write('find . -path "*/tmp/*" -delete\n\n')
                
                f.write("# Clean Python cache files\n")
                f.write('find . -name "__pycache__" -type d -exec rm -rf {} +\n')
                f.write('find . -name "*.pyc" -delete\n')
                f.write('find . -name "*.pyo" -delete\n')
                f.write('find . -name ".pytest_cache" -type d -exec rm -rf {} +\n')
                f.write('find . -name ".coverage" -delete\n')
                f.write('find . -name "htmlcov" -type d -exec rm -rf {} +\n')
                f.write('find . -name ".mypy_cache" -type d -exec rm -rf {} +\n')
                f.write('find . -name ".ruff_cache" -type d -exec rm -rf {} +\n\n')
                
                f.write("# Clean build artifacts\n")
                f.write('find . -name "dist" -type d -exec rm -rf {} +\n')
                f.write('find . -name "build" -type d -exec rm -rf {} +\n')
                f.write('find . -name "*.egg-info" -type d -exec rm -rf {} +\n')
                f.write('find . -name "*.egg" -delete\n\n')
                
                f.write("# Git maintenance\n")
                f.write('git gc --aggressive --prune=now\n\n')
                
                f.write('echo "Repository cleanup complete!"\n')
                f.write('echo "Repository size: $(du -sh . | cut -f1)"\n')
            
            # Make script executable
            cleanup_script_path.chmod(cleanup_script_path.stat().st_mode | 0o755)
            
            logger.info(f"Created repository cleanup script: {cleanup_script_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to implement repository size management: {str(e)}")
            return False
    
    async def optimize_workspace(
        self,
        categories: Optional[List[OptimizationCategory]] = None,
        segments: Optional[List[WorkspaceSegment]] = None,
    ) -> bool:
        """
        Optimize workspace based on selected categories and segments.
        
        Args:
            categories: Categories to optimize
            segments: Workspace segments to optimize
            
        Returns:
            True if optimization was successful
        """
        # Default to all categories
        if not categories:
            categories = [OptimizationCategory.ALL]
        
        # Default to all segments
        if not segments:
            segments = [WorkspaceSegment.ALL]
        
        # Expand ALL category
        if OptimizationCategory.ALL in categories:
            categories = [
                cat for cat in OptimizationCategory
                if cat != OptimizationCategory.ALL
            ]
        
        # Expand ALL segment
        if WorkspaceSegment.ALL in segments:
            segments = [
                seg for seg in WorkspaceSegment
                if seg != WorkspaceSegment.ALL
            ]
        
        # Track success
        success = True
        
        # Analyze workspace
        await self.analyze_workspace()
        
        # Implement optimizations by category
        for category in categories:
            if category == OptimizationCategory.WORKSPACE_SEGMENTATION:
                if not await self.implement_workspace_segmentation():
                    success = False
            
            elif category == OptimizationCategory.FILE_EXCLUSIONS:
                if not await self.implement_file_exclusions():
                    success = False
            
            elif category == OptimizationCategory.GIT_OPTIMIZATION:
                if not await self.implement_git_optimization():
                    success = False
            
            elif category == OptimizationCategory.ENV_MANAGEMENT:
                if not await self.standardize_env_files():
                    success = False
            
            elif category == OptimizationCategory.VIRTUALIZATION:
                if not await self.implement_virtualization_config():
                    success = False
            
            elif category == OptimizationCategory.REPO_SIZE:
                if not await self.implement_repository_size_management():
                    success = False
        
        return success


async def run_optimizer(args):
    """Run the workspace optimizer."""
    # Create the optimizer
    optimizer = WorkspaceOptimizer(
        base_dir=args.base_dir,
        config_path=args.config,
        data_dir=args.data_dir,
        max_data_size_mb=args.max_data_size,
    )
    
    # Parse categories
    categories = []
    if args.categories:
        for category in args.categories.split(","):
            try:
                categories.append(OptimizationCategory(category))
            except ValueError:
                logger.warning(f"Invalid category: {category}")
    
    # Parse segments
    segments = []
    if args.segments:
        for segment in args.segments.split(","):
            try:
                segments.append(WorkspaceSegment(segment))
            except ValueError:
                logger.warning(f"Invalid segment: {segment}")
    
    if args.analyze_only:
        # Analyze workspace
        profile = await optimizer.analyze_workspace()
        
        # Print analysis results
        print("\n===== Workspace Analysis Results =====\n")
        
        print(f"Total Files: {profile.file_stats.get('total_count', 0)}")
        print(f"Total Size: {profile.file_stats.get('total_size_bytes', 0) / (1024 * 1024):.2f} MB")
        
        print("\nLargest Files:")
        for file in profile.file_stats.get("largest_files", [])[:5]:
            print(f"- {file.get('path')}: {file.get('size_bytes', 0) / 1024:.2f} KB")
        
        print("\nBinary Files:")
        binary_files = profile.file_stats.get("binary_files", {})
        print(f"- Count: {binary_files.get('count', 0)}")
        print(f"- Size: {binary_files.get('total_size_bytes', 0) / (1024 * 1024):.2f} MB")
        
        print("\nDeepest Directory:")
        print(f"- {profile.directory_stats.get('deepest_path', '')}")
        print(f"- Depth: {profile.directory_stats.get('deepest_nesting', 0)}")
        
        print("\nGit Repository:")
        git_stats = profile.git_stats
        if git_stats.get("is_git_repo", False):
            print(f"- Size: {git_stats.get('repo_size_bytes', 0) / (1024 * 1024):.2f} MB")
            print(f"- Objects: {git_stats.get('objects_count', 0)}")
        else:
            print("- Not a Git repository")
        
        print("\nEnvironment Files:")
        for env_file in profile.env_files:
            print(f"- {env_file.get('path')}: {env_file.get('var_count', 0)} variables")
        
        print("\n===== End of Analysis =====\n")
    else:
        # Optimize workspace
        success = await optimizer.optimize_workspace(
            categories=categories,
            segments=segments,
        )
        
        if success:
            print("\nWorkspace optimization completed successfully!")
        else:
            print("\nWorkspace optimization completed with some errors.")
            print("Check the log for details.")


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Workspace Optimization Tool for AI Orchestra"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory of the project",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (YAML or JSON)",
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default=".workspace_optimization",
        help="Directory to store optimization data",
    )
    
    parser.add_argument(
        "--max-data-size",
        type=int,
        default=50,
        help="Maximum size for optimization data in MB",
    )
    
    parser.add_argument(
        "--categories",
        type=str,
        help="Comma-separated list of optimization categories",
    )
    
    parser.add_argument(
        "--segments",
        type=str,
        help="Comma-separated list of workspace segments",
    )
    
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze workspace without making changes",
    )
    
    args = parser.parse_args()
    
    # Run the optimizer
    asyncio.run(run_optimizer(args))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())