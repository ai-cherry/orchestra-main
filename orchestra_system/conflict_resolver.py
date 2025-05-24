#!/usr/bin/env python3
"""
Conflict Resolver for AI Orchestra

This module implements an automated conflict detection and resolution system
for the AI Orchestra project. It identifies and resolves conflicts between
resources, configurations, and files across different environments.

Key features:
- Automatic detection of file duplicates and conflicts
- Resource reference inconsistency detection
- Multiple resolution strategies (priority-based, environment-specific, etc.)
- Resolution history tracking
- Integration with MCP memory for persistent conflict state
"""

import asyncio
import difflib
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    TypeVar,
    Generic,
    Callable,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("conflict-resolver")

# Try to import MCP client
try:
    from gcp_migration.mcp_client_enhanced import (
        MCPClient,
        MCPResponse,
        get_client as get_mcp_client,
    )
except ImportError:
    logger.warning("Could not import enhanced MCP client, attempting to import basic client")
    try:
        from gcp_migration.mcp_client import MCPClient, get_client as get_mcp_client
    except ImportError:
        logger.error("Failed to import MCP client. Conflict Resolver will operate in offline mode.")
        MCPClient = object

        def get_mcp_client(*args, **kwargs):
            return None


# Try to import resource registry and config manager
try:
    from orchestra_system.resource_registry import (
        Resource,
        ResourceStatus,
        get_registry,
    )
except ImportError:
    logger.warning("Could not import resource registry, some functionality will be limited")
    Resource = None
    ResourceStatus = None

    def get_registry(*args, **kwargs):
        return None


try:
    from orchestra_system.config_manager import ConfigEntry, ConfigConflict, get_manager
except ImportError:
    logger.warning("Could not import config manager, some functionality will be limited")
    ConfigEntry = None
    ConfigConflict = None

    def get_manager(*args, **kwargs):
        return None


class ConflictType(str, Enum):
    """Types of conflicts that can be detected and resolved."""

    DUPLICATE_FILE = "duplicate_file"  # Multiple files with the same content
    FILE_CONFLICT = "file_conflict"  # Files with conflicting content
    RESOURCE_CONFLICT = "resource_conflict"  # Conflicting resources
    CONFIG_CONFLICT = "config_conflict"  # Conflicting configuration
    REFERENCE_INCONSISTENCY = "ref_inconsistency"  # Inconsistent references
    DEPENDENCY_CONFLICT = "dependency_conflict"  # Conflicting dependencies
    VERSION_CONFLICT = "version_conflict"  # Version conflicts


class ResolutionStrategy(str, Enum):
    """Strategies for resolving conflicts."""

    PRIORITY = "priority"  # Resolve based on priority
    ENVIRONMENT = "environment"  # Resolve based on environment
    TIMESTAMP = "timestamp"  # Resolve based on timestamp (newest wins)
    MERGE = "merge"  # Merge conflicting items
    MANUAL = "manual"  # Manual resolution required
    RENAME = "rename"  # Rename conflicting items
    DELETE_DUPLICATE = "delete_duplicate"  # Delete duplicate items
    KEEP_ALL = "keep_all"  # Keep all conflicting items


class ResolutionStatus(str, Enum):
    """Status of a conflict resolution."""

    PENDING = "pending"  # Resolution is pending
    RESOLVED = "resolved"  # Conflict resolved
    PARTIALLY_RESOLVED = "partial"  # Conflict partially resolved
    FAILED = "failed"  # Resolution failed
    MANUAL_REQUIRED = "manual"  # Manual resolution required


class Conflict:
    """Represents a detected conflict."""

    def __init__(
        self,
        conflict_id: str,
        conflict_type: ConflictType,
        items: List[Dict[str, Any]],
        description: str,
        detected_at: Optional[str] = None,
        environment: Optional[str] = None,
        severity: str = "medium",
    ):
        """Initialize a conflict.

        Args:
            conflict_id: Unique identifier for the conflict
            conflict_type: Type of conflict
            items: List of conflicting items
            description: Description of the conflict
            detected_at: Timestamp when the conflict was detected
            environment: Environment where the conflict was detected
            severity: Severity of the conflict (low, medium, high, critical)
        """
        self.conflict_id = conflict_id
        self.conflict_type = conflict_type
        self.items = items
        self.description = description
        self.detected_at = detected_at or datetime.now().isoformat()
        self.environment = environment or os.environ.get("DEPLOYMENT_ENV", "development")
        self.severity = severity

        # Resolution information
        self.resolution_status = ResolutionStatus.PENDING
        self.resolution_strategy = None
        self.resolved_at = None
        self.resolution_description = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the conflict to a dictionary for serialization."""
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type,
            "items": self.items,
            "description": self.description,
            "detected_at": self.detected_at,
            "environment": self.environment,
            "severity": self.severity,
            "resolution_status": self.resolution_status,
            "resolution_strategy": self.resolution_strategy,
            "resolved_at": self.resolved_at,
            "resolution_description": self.resolution_description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conflict":
        """Create a conflict from a dictionary."""
        conflict = cls(
            conflict_id=data["conflict_id"],
            conflict_type=data["conflict_type"],
            items=data["items"],
            description=data["description"],
            detected_at=data.get("detected_at"),
            environment=data.get("environment"),
            severity=data.get("severity", "medium"),
        )

        # Set resolution information
        conflict.resolution_status = data.get("resolution_status", ResolutionStatus.PENDING)
        conflict.resolution_strategy = data.get("resolution_strategy")
        conflict.resolved_at = data.get("resolved_at")
        conflict.resolution_description = data.get("resolution_description")

        return conflict


class Resolution:
    """Represents a resolution to a conflict."""

    def __init__(
        self,
        conflict_id: str,
        strategy: ResolutionStrategy,
        actions: List[Dict[str, Any]],
        status: ResolutionStatus = ResolutionStatus.PENDING,
        resolved_at: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize a resolution.

        Args:
            conflict_id: ID of the conflict being resolved
            strategy: Resolution strategy
            actions: List of actions to take for resolution
            status: Resolution status
            resolved_at: Timestamp when the resolution was applied
            description: Description of the resolution
        """
        self.conflict_id = conflict_id
        self.strategy = strategy
        self.actions = actions
        self.status = status
        self.resolved_at = resolved_at
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert the resolution to a dictionary for serialization."""
        return {
            "conflict_id": self.conflict_id,
            "strategy": self.strategy,
            "actions": self.actions,
            "status": self.status,
            "resolved_at": self.resolved_at,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resolution":
        """Create a resolution from a dictionary."""
        return cls(
            conflict_id=data["conflict_id"],
            strategy=data["strategy"],
            actions=data["actions"],
            status=data.get("status", ResolutionStatus.PENDING),
            resolved_at=data.get("resolved_at"),
            description=data.get("description"),
        )


class ConflictResolver:
    """Automated conflict detection and resolution system."""

    # MCP memory keys
    CONFLICTS_KEY = "conflicts:registry"
    RESOLUTIONS_KEY = "conflicts:resolutions"
    HISTORY_KEY = "conflicts:history"

    def __init__(self, mcp_client: Optional[MCPClient] = None):
        """Initialize the Conflict Resolver.

        Args:
            mcp_client: An instance of MCPClient for accessing shared memory
        """
        self.mcp_client = mcp_client or get_mcp_client()
        self.conflicts: Dict[str, Conflict] = {}
        self.resolutions: Dict[str, Resolution] = {}
        self.resolution_history: List[Dict[str, Any]] = []

        # Resolution handlers for each conflict type
        self.resolution_handlers = {
            ConflictType.DUPLICATE_FILE: self._resolve_duplicate_file,
            ConflictType.FILE_CONFLICT: self._resolve_file_conflict,
            ConflictType.RESOURCE_CONFLICT: self._resolve_resource_conflict,
            ConflictType.CONFIG_CONFLICT: self._resolve_config_conflict,
            ConflictType.REFERENCE_INCONSISTENCY: self._resolve_reference_inconsistency,
            ConflictType.DEPENDENCY_CONFLICT: self._resolve_dependency_conflict,
            ConflictType.VERSION_CONFLICT: self._resolve_version_conflict,
        }

        # Initialize the resolver
        self._initialize_resolver()

    def _initialize_resolver(self) -> None:
        """Initialize the Conflict Resolver."""
        try:
            if self.mcp_client:
                # Load conflicts from MCP memory
                conflicts_response = self.mcp_client.get(self.CONFLICTS_KEY)
                if conflicts_response and conflicts_response.success and conflicts_response.value:
                    conflicts_data = conflicts_response.value
                    for conflict_id, conflict_data in conflicts_data.items():
                        self.conflicts[conflict_id] = Conflict.from_dict(conflict_data)

                # Load resolutions from MCP memory
                resolutions_response = self.mcp_client.get(self.RESOLUTIONS_KEY)
                if resolutions_response and resolutions_response.success and resolutions_response.value:
                    resolutions_data = resolutions_response.value
                    for conflict_id, resolution_data in resolutions_data.items():
                        self.resolutions[conflict_id] = Resolution.from_dict(resolution_data)

                # Load history from MCP memory
                history_response = self.mcp_client.get(self.HISTORY_KEY)
                if history_response and history_response.success and history_response.value:
                    self.resolution_history = history_response.value

                logger.info(
                    f"Loaded {len(self.conflicts)} conflicts and {len(self.resolutions)} resolutions from MCP memory"
                )
            else:
                logger.warning("No MCP client available. Conflict state will not be persistent.")

        except Exception as e:
            logger.error(f"Failed to initialize Conflict Resolver: {e}")

    def _save_to_mcp(self) -> bool:
        """Save conflicts and resolutions to MCP memory."""
        try:
            if not self.mcp_client:
                return False

            # Save conflicts
            conflicts_data = {conflict_id: conflict.to_dict() for conflict_id, conflict in self.conflicts.items()}
            conflicts_result = self.mcp_client.set(self.CONFLICTS_KEY, conflicts_data)

            # Save resolutions
            resolutions_data = {
                resolution.conflict_id: resolution.to_dict() for resolution in self.resolutions.values()
            }
            resolutions_result = self.mcp_client.set(self.RESOLUTIONS_KEY, resolutions_data)

            # Save history
            history_result = self.mcp_client.set(self.HISTORY_KEY, self.resolution_history)

            if not (
                conflicts_result
                and conflicts_result.success
                and resolutions_result
                and resolutions_result.success
                and history_result
                and history_result.success
            ):
                logger.error("Failed to save to MCP memory")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to save to MCP memory: {e}")
            return False

    def detect_duplicate_files(
        self, directory: Union[str, Path], extensions: Optional[List[str]] = None
    ) -> List[Conflict]:
        """Detect duplicate files in a directory.

        Args:
            directory: Directory to scan
            extensions: List of file extensions to include

        Returns:
            List of detected conflicts
        """
        try:
            # Convert directory to Path
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                logger.error(f"Directory not found: {directory}")
                return []

            # Get all files
            files = []
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    file_path = Path(root) / filename

                    # Filter by extension if provided
                    if extensions and file_path.suffix not in extensions:
                        continue

                    files.append(file_path)

            # Group files by content hash
            files_by_hash = {}
            for file_path in files:
                try:
                    # Calculate file hash
                    file_hash = self._calculate_file_hash(file_path)

                    if file_hash not in files_by_hash:
                        files_by_hash[file_hash] = []

                    files_by_hash[file_hash].append(file_path)

                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {e}")

            # Find duplicates
            duplicates = {file_hash: paths for file_hash, paths in files_by_hash.items() if len(paths) > 1}

            # Create conflicts for duplicates
            conflicts = []
            for file_hash, paths in duplicates.items():
                # Convert paths to strings
                path_strs = [str(path) for path in paths]

                # Create a conflict
                conflict_id = f"duplicate_file_{file_hash[:8]}"

                # Skip if conflict already exists
                if conflict_id in self.conflicts:
                    continue

                # Create a new conflict
                conflict = Conflict(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.DUPLICATE_FILE,
                    items=[{"path": path} for path in path_strs],
                    description=f"Duplicate files with hash {file_hash[:8]}: {', '.join(path_strs)}",
                    severity="low",
                )

                self.conflicts[conflict_id] = conflict
                conflicts.append(conflict)

            # Save to MCP memory
            self._save_to_mcp()

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect duplicate files: {e}")
            return []

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash of the file content
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read and update hash in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def detect_file_conflicts(self, paths: List[Union[str, Path]]) -> List[Conflict]:
        """Detect conflicts between files.

        This method compares the content of files to detect conflicts,
        such as different versions of the same file.

        Args:
            paths: List of file paths to compare

        Returns:
            List of detected conflicts
        """
        try:
            conflicts = []

            # Group files by name
            files_by_name = {}
            for path in paths:
                path_obj = Path(path)
                name = path_obj.name

                if name not in files_by_name:
                    files_by_name[name] = []

                files_by_name[name].append(path_obj)

            # Find files with the same name but different content
            for name, file_paths in files_by_name.items():
                if len(file_paths) <= 1:
                    continue

                # Compare file contents
                file_contents = {}
                for path in file_paths:
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()

                        file_hash = hashlib.sha256(content.encode()).hexdigest()

                        if file_hash not in file_contents:
                            file_contents[file_hash] = []

                        file_contents[file_hash].append(path)

                    except Exception as e:
                        logger.error(f"Failed to read file {path}: {e}")

                # If there are multiple distinct contents, we have a conflict
                if len(file_contents) > 1:
                    # Create a conflict
                    conflict_id = f"file_conflict_{name.replace('.', '_')}"

                    # Skip if conflict already exists
                    if conflict_id in self.conflicts:
                        continue

                    # Create items list for the conflict
                    items = []
                    for file_hash, hash_paths in file_contents.items():
                        for path in hash_paths:
                            items.append({"path": str(path), "hash": file_hash})

                    # Create a new conflict
                    conflict = Conflict(
                        conflict_id=conflict_id,
                        conflict_type=ConflictType.FILE_CONFLICT,
                        items=items,
                        description=f"Conflicting versions of file {name}",
                        severity="medium",
                    )

                    self.conflicts[conflict_id] = conflict
                    conflicts.append(conflict)

            # Save to MCP memory
            self._save_to_mcp()

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect file conflicts: {e}")
            return []

    def detect_reference_inconsistencies(
        self, directory: Union[str, Path], extensions: Optional[List[str]] = None
    ) -> List[Conflict]:
        """Detect inconsistencies in references between files.

        Args:
            directory: Directory to scan
            extensions: List of file extensions to include

        Returns:
            List of detected conflicts
        """
        try:
            # Convert directory to Path
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                logger.error(f"Directory not found: {directory}")
                return []

            # Get all files
            files = []
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    file_path = Path(root) / filename

                    # Filter by extension if provided
                    if extensions and file_path.suffix not in extensions:
                        continue

                    files.append(file_path)

            # Extract references from files
            file_references = {}
            for file_path in files:
                try:
                    references = self._extract_references(file_path)
                    file_references[file_path] = references

                except Exception as e:
                    logger.error(f"Failed to extract references from {file_path}: {e}")

            # Find inconsistencies
            conflicts = []

            # Check for references to non-existent files
            for file_path, references in file_references.items():
                for ref in references:
                    ref_path = dir_path / ref.lstrip("/")

                    if not ref_path.exists():
                        # Create a conflict
                        conflict_id = f"ref_inconsistency_{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}"

                        # Skip if conflict already exists
                        if conflict_id in self.conflicts:
                            continue

                        # Create a new conflict
                        conflict = Conflict(
                            conflict_id=conflict_id,
                            conflict_type=ConflictType.REFERENCE_INCONSISTENCY,
                            items=[{"file": str(file_path), "reference": ref}],
                            description=f"Reference to non-existent file {ref} in {file_path}",
                            severity="medium",
                        )

                        self.conflicts[conflict_id] = conflict
                        conflicts.append(conflict)

            # Save to MCP memory
            self._save_to_mcp()

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect reference inconsistencies: {e}")
            return []

    def _extract_references(self, file_path: Path) -> List[str]:
        """Extract file references from a file.

        Args:
            file_path: Path to the file

        Returns:
            List of referenced file paths
        """
        references = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract references based on file type
            if file_path.suffix.lower() in [".py", ".sh", ".js", ".ts"]:
                # Extract import/require statements for programming languages
                if file_path.suffix.lower() == ".py":
                    # Python imports
                    import_re = re.compile(r"(?:from|import)\s+([a-zA-Z0-9_.]+)")
                    for match in import_re.finditer(content):
                        try:
                            module = match.group(1)
                            references.append(module.replace(".", "/") + ".py")
                        except Exception as e:
                            logger.error(f"Failed to process Python import match: {e}")

                elif file_path.suffix.lower() in [".js", ".ts"]:
                    # JavaScript/TypeScript imports
                    import_re = re.compile(r'(?:import|require)\s*\(?\s*[\'"]([^\'"]+)[\'"]')
                    for match in import_re.finditer(content):
                        try:
                            module = match.group(1)
                            references.append(module)
                        except Exception as e:
                            logger.error(f"Failed to process JS/TS import match: {e}")

            # Extract direct file references (paths)
            path_re = re.compile(r'[\'"]([/\w.-]+\.\w+)[\'"]')
            for match in path_re.finditer(content):
                try:
                    path = match.group(1)
                    # Skip URLs
                    if not path.startswith(("http://", "https://", "ftp://")):
                        references.append(path)
                except Exception as e:
                    logger.error(f"Failed to process path match: {e}")

        except Exception as e:
            logger.error(f"Failed to extract references from {file_path}: {e}")

        return references

    def detect_config_conflicts(self) -> List[Conflict]:
        """Detect conflicts in configuration.

        This method uses the ConfigurationManager to detect conflicts
        between configuration values.

        Returns:
            List of detected conflicts
        """
        try:
            if not get_manager:
                logger.error("Config manager not available")
                return []

            # Get configuration manager
            config_manager = get_manager()

            # Get conflicts
            config_conflicts = []
            try:
                # Access internal conflicts dict if available
                if hasattr(config_manager, "conflicts"):
                    config_conflicts = list(config_manager.conflicts.values())
            except:
                pass

            # Create conflicts for config conflicts
            conflicts = []
            for config_conflict in config_conflicts:
                # Generate a conflict ID
                conflict_id = f"config_conflict_{config_conflict.key}"

                # Skip if conflict already exists
                if conflict_id in self.conflicts:
                    continue

                # Create items list
                items = []
                for entry in config_conflict.entries:
                    items.append(
                        {
                            "key": entry.key,
                            "value": entry.value,
                            "environment": entry.environment,
                            "source": entry.source,
                        }
                    )

                # Create a new conflict
                conflict = Conflict(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.CONFIG_CONFLICT,
                    items=items,
                    description=f"Conflicting configuration values for key: {config_conflict.key}",
                    severity="medium",
                )

                self.conflicts[conflict_id] = conflict
                conflicts.append(conflict)

            # Save to MCP memory
            self._save_to_mcp()

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect config conflicts: {e}")
            return []

    def detect_resource_conflicts(self) -> List[Conflict]:
        """Detect conflicts in resources.

        This method uses the ResourceRegistry to detect conflicts
        between resources.

        Returns:
            List of detected conflicts
        """
        try:
            if not get_registry:
                logger.error("Resource registry not available")
                return []

            # Get resource registry
            registry = get_registry()

            # Group resources by name
            resources_by_name = {}
            for resource in getattr(registry, "resources", {}).values():
                name = resource.name

                if name not in resources_by_name:
                    resources_by_name[name] = []

                resources_by_name[name].append(resource)

            # Find resources with the same name but different attributes
            conflicts = []
            for name, resources in resources_by_name.items():
                if len(resources) <= 1:
                    continue

                # Check for conflicts in access patterns
                access_patterns = set(resource.access_pattern for resource in resources)
                if len(access_patterns) > 1:
                    # Create a conflict
                    conflict_id = f"resource_conflict_{name}"

                    # Skip if conflict already exists
                    if conflict_id in self.conflicts:
                        continue

                    # Create items list
                    items = []
                    for resource in resources:
                        items.append(
                            {
                                "name": resource.name,
                                "type": resource.resource_type,
                                "environment": resource.environment,
                                "access_pattern": resource.access_pattern,
                            }
                        )

                    # Create a new conflict
                    conflict = Conflict(
                        conflict_id=conflict_id,
                        conflict_type=ConflictType.RESOURCE_CONFLICT,
                        items=items,
                        description=f"Conflicting access patterns for resource: {name}",
                        severity="medium",
                    )

                    self.conflicts[conflict_id] = conflict
                    conflicts.append(conflict)

            # Save to MCP memory
            self._save_to_mcp()

            return conflicts

        except Exception as e:
            logger.error(f"Failed to detect resource conflicts: {e}")
            return []

    def detect_all_conflicts(self, directory: Union[str, Path] = ".") -> List[Conflict]:
        """Detect all types of conflicts.

        Args:
            directory: Directory to scan

        Returns:
            List of detected conflicts
        """
        all_conflicts = []

        # Detect duplicate files
        duplicate_conflicts = self.detect_duplicate_files(directory)
        all_conflicts.extend(duplicate_conflicts)

        # Get all Python, JavaScript, and TypeScript files
        code_files = []
        for ext in [".py", ".js", ".ts", ".json", ".yaml", ".yml", ".tf"]:
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(ext):
                        code_files.append(os.path.join(root, filename))

        # Detect file conflicts
        file_conflicts = self.detect_file_conflicts(code_files)
        all_conflicts.extend(file_conflicts)

        # Detect reference inconsistencies
        ref_conflicts = self.detect_reference_inconsistencies(directory, [".py", ".js", ".ts"])
        all_conflicts.extend(ref_conflicts)

        # Detect configuration conflicts
        config_conflicts = self.detect_config_conflicts()
        all_conflicts.extend(config_conflicts)

        # Detect resource conflicts
        resource_conflicts = self.detect_resource_conflicts()
        all_conflicts.extend(resource_conflicts)

        return all_conflicts

    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: ResolutionStrategy,
        manual_actions: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Resolution]:
        """Resolve a conflict.

        Args:
            conflict_id: ID of the conflict to resolve
            strategy: Resolution strategy to use
            manual_actions: Manual actions to take (for MANUAL strategy)

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Check if conflict exists
            if conflict_id not in self.conflicts:
                logger.error(f"Conflict not found: {conflict_id}")
                return None

            conflict = self.conflicts[conflict_id]

            # For manual resolution, use provided actions
            if strategy == ResolutionStrategy.MANUAL:
                if not manual_actions:
                    logger.error("Manual actions required for MANUAL resolution strategy")
                    return None

                # Create resolution
                resolution = Resolution(
                    conflict_id=conflict_id,
                    strategy=strategy,
                    actions=manual_actions,
                    status=ResolutionStatus.RESOLVED,
                    resolved_at=datetime.now().isoformat(),
                    description="Manual resolution",
                )

                # Update conflict
                conflict.resolution_status = ResolutionStatus.RESOLVED
                conflict.resolution_strategy = strategy
                conflict.resolved_at = resolution.resolved_at
                conflict.resolution_description = "Manual resolution"

                # Save resolution
                self.resolutions[conflict_id] = resolution

                # Add to history
                self.resolution_history.append(
                    {
                        "conflict_id": conflict_id,
                        "resolution_id": conflict_id,
                        "timestamp": resolution.resolved_at,
                        "strategy": strategy,
                    }
                )

                # Save to MCP memory
                self._save_to_mcp()

                return resolution

            # Get handler for conflict type
            if conflict.conflict_type not in self.resolution_handlers:
                logger.error(f"No handler for conflict type: {conflict.conflict_type}")
                return None

            handler = self.resolution_handlers[conflict.conflict_type]

            # Call handler
            resolution = handler(conflict, strategy)

            if resolution:
                # Save resolution
                self.resolutions[conflict_id] = resolution

                # Update conflict
                conflict.resolution_status = resolution.status
                conflict.resolution_strategy = strategy
                conflict.resolved_at = resolution.resolved_at
                conflict.resolution_description = resolution.description

                # Add to history
                self.resolution_history.append(
                    {
                        "conflict_id": conflict_id,
                        "resolution_id": conflict_id,
                        "timestamp": resolution.resolved_at,
                        "strategy": strategy,
                    }
                )

                # Save to MCP memory
                self._save_to_mcp()

            return resolution

        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict_id}: {e}")
            return None

    def _resolve_duplicate_file(self, conflict: Conflict, strategy: ResolutionStrategy) -> Optional[Resolution]:
        """Resolve a duplicate file conflict.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Get conflict items
            items = conflict.items

            # Prepare actions
            actions = []

            if strategy == ResolutionStrategy.DELETE_DUPLICATE:
                # Keep the first file, delete others
                keep_path = items[0]["path"]

                for item in items[1:]:
                    path = item["path"]
                    actions.append(
                        {
                            "action": "delete",
                            "path": path,
                            "description": f"Delete duplicate file: {path}",
                        }
                    )

                actions.append(
                    {
                        "action": "keep",
                        "path": keep_path,
                        "description": f"Keep original file: {keep_path}",
                    }
                )

            elif strategy == ResolutionStrategy.RENAME:
                # Rename files to avoid duplication
                for i, item in enumerate(items):
                    path = item["path"]
                    path_obj = Path(path)

                    if i == 0:
                        # Keep the first file as is
                        actions.append(
                            {
                                "action": "keep",
                                "path": path,
                                "description": f"Keep original file: {path}",
                            }
                        )
                    else:
                        # Rename others
                        new_name = f"{path_obj.stem}_{i}{path_obj.suffix}"
                        new_path = str(path_obj.parent / new_name)

                        actions.append(
                            {
                                "action": "rename",
                                "path": path,
                                "new_path": new_path,
                                "description": f"Rename duplicate file: {path} -> {new_path}",
                            }
                        )

            elif strategy == ResolutionStrategy.KEEP_ALL:
                # Keep all files
                for item in items:
                    path = item["path"]
                    actions.append(
                        {
                            "action": "keep",
                            "path": path,
                            "description": f"Keep file: {path}",
                        }
                    )

            else:
                logger.error(f"Unsupported resolution strategy for duplicate files: {strategy}")
                return None

            # Create resolution
            resolution = Resolution(
                conflict_id=conflict.conflict_id,
                strategy=strategy,
                actions=actions,
                status=ResolutionStatus.RESOLVED,
                resolved_at=datetime.now().isoformat(),
                description=f"Resolved duplicate file conflict using {strategy} strategy",
            )

            return resolution

        except Exception as e:
            logger.error(f"Failed to resolve duplicate file conflict: {e}")
            return None

    def _resolve_file_conflict(self, conflict: Conflict, strategy: ResolutionStrategy) -> Optional[Resolution]:
        """Resolve a file conflict.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Get conflict items
            items = conflict.items

            # Prepare actions
            actions = []

            if strategy == ResolutionStrategy.PRIORITY:
                # Get highest priority file (assumed to be the first item)
                keep_path = items[0]["path"]

                for item in items:
                    path = item["path"]
                    if path == keep_path:
                        actions.append(
                            {
                                "action": "keep",
                                "path": path,
                                "description": f"Keep highest priority file: {path}",
                            }
                        )
                    else:
                        actions.append(
                            {
                                "action": "overwrite",
                                "path": path,
                                "source_path": keep_path,
                                "description": f"Overwrite with highest priority file: {path} <- {keep_path}",
                            }
                        )

            elif strategy == ResolutionStrategy.MERGE:
                # Get unique paths
                paths = [item["path"] for item in items]

                # Create merge action
                actions.append(
                    {
                        "action": "merge",
                        "paths": paths,
                        "output_path": paths[0],
                        "description": f"Merge conflicting files into: {paths[0]}",
                    }
                )

            elif strategy == ResolutionStrategy.RENAME:
                # Rename files to avoid conflict
                for i, item in enumerate(items):
                    path = item["path"]
                    path_obj = Path(path)

                    if i == 0:
                        # Keep the first file as is
                        actions.append(
                            {
                                "action": "keep",
                                "path": path,
                                "description": f"Keep original file: {path}",
                            }
                        )
                    else:
                        # Rename others
                        new_name = f"{path_obj.stem}_variant_{i}{path_obj.suffix}"
                        new_path = str(path_obj.parent / new_name)

                        actions.append(
                            {
                                "action": "rename",
                                "path": path,
                                "new_path": new_path,
                                "description": f"Rename conflicting file: {path} -> {new_path}",
                            }
                        )

            else:
                logger.error(f"Unsupported resolution strategy for file conflicts: {strategy}")
                return None

            # Create resolution
            resolution = Resolution(
                conflict_id=conflict.conflict_id,
                strategy=strategy,
                actions=actions,
                status=ResolutionStatus.RESOLVED,
                resolved_at=datetime.now().isoformat(),
                description=f"Resolved file conflict using {strategy} strategy",
            )

            return resolution

        except Exception as e:
            logger.error(f"Failed to resolve file conflict: {e}")
            return None

    def _resolve_resource_conflict(self, conflict: Conflict, strategy: ResolutionStrategy) -> Optional[Resolution]:
        """Resolve a resource conflict.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Get conflict items
            items = conflict.items

            # Prepare actions
            actions = []

            if strategy == ResolutionStrategy.PRIORITY:
                # Use the first item as the highest priority
                priority_item = items[0]

                actions.append(
                    {
                        "action": "update_resource",
                        "name": priority_item["name"],
                        "access_pattern": priority_item["access_pattern"],
                        "description": f"Use access pattern from highest priority resource: {priority_item['access_pattern']}",
                    }
                )

            elif strategy == ResolutionStrategy.ENVIRONMENT:
                # Filter items by environment
                current_env = os.environ.get("DEPLOYMENT_ENV", "development")
                env_items = [item for item in items if item["environment"] == current_env]

                if env_items:
                    env_item = env_items[0]
                    actions.append(
                        {
                            "action": "update_resource",
                            "name": env_item["name"],
                            "access_pattern": env_item["access_pattern"],
                            "description": f"Use access pattern from current environment ({current_env}): {env_item['access_pattern']}",
                        }
                    )
                else:
                    # Fallback to first item
                    fallback_item = items[0]
                    actions.append(
                        {
                            "action": "update_resource",
                            "name": fallback_item["name"],
                            "access_pattern": fallback_item["access_pattern"],
                            "description": f"No resource for current environment, using fallback: {fallback_item['access_pattern']}",
                        }
                    )

            else:
                logger.error(f"Unsupported resolution strategy for resource conflicts: {strategy}")
                return None

            # Create resolution
            resolution = Resolution(
                conflict_id=conflict.conflict_id,
                strategy=strategy,
                actions=actions,
                status=ResolutionStatus.RESOLVED,
                resolved_at=datetime.now().isoformat(),
                description=f"Resolved resource conflict using {strategy} strategy",
            )

            return resolution

        except Exception as e:
            logger.error(f"Failed to resolve resource conflict: {e}")
            return None

    def _resolve_config_conflict(self, conflict: Conflict, strategy: ResolutionStrategy) -> Optional[Resolution]:
        """Resolve a configuration conflict.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Get conflict items
            items = conflict.items

            # Prepare actions
            actions = []

            if strategy == ResolutionStrategy.PRIORITY:
                # Use the first item as the highest priority
                priority_item = items[0]

                actions.append(
                    {
                        "action": "update_config",
                        "key": priority_item["key"],
                        "value": priority_item["value"],
                        "description": f"Use value from highest priority config: {priority_item['value']}",
                    }
                )

            elif strategy == ResolutionStrategy.ENVIRONMENT:
                # Filter items by environment
                current_env = os.environ.get("DEPLOYMENT_ENV", "development")
                env_items = [item for item in items if item["environment"] == current_env]

                if env_items:
                    env_item = env_items[0]
                    actions.append(
                        {
                            "action": "update_config",
                            "key": env_item["key"],
                            "value": env_item["value"],
                            "description": f"Use value from current environment ({current_env}): {env_item['value']}",
                        }
                    )
                else:
                    # Fallback to first item
                    fallback_item = items[0]
                    actions.append(
                        {
                            "action": "update_config",
                            "key": fallback_item["key"],
                            "value": fallback_item["value"],
                            "description": f"No config for current environment, using fallback: {fallback_item['value']}",
                        }
                    )

            else:
                logger.error(f"Unsupported resolution strategy for config conflicts: {strategy}")
                return None

            # Create resolution
            resolution = Resolution(
                conflict_id=conflict.conflict_id,
                strategy=strategy,
                actions=actions,
                status=ResolutionStatus.RESOLVED,
                resolved_at=datetime.now().isoformat(),
                description=f"Resolved config conflict using {strategy} strategy",
            )

            return resolution

        except Exception as e:
            logger.error(f"Failed to resolve config conflict: {e}")
            return None

    def _resolve_reference_inconsistency(
        self, conflict: Conflict, strategy: ResolutionStrategy
    ) -> Optional[Resolution]:
        """Resolve a reference inconsistency.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Get conflict items
            items = conflict.items

            # Prepare actions
            actions = []

            if strategy == ResolutionStrategy.MANUAL:
                # Reference inconsistencies usually require manual resolution
                file_path = items[0]["file"]
                reference = items[0]["reference"]

                actions.append(
                    {
                        "action": "manual",
                        "file": file_path,
                        "reference": reference,
                        "description": f"Manually fix reference in {file_path} to {reference}",
                    }
                )

                # Create resolution
                resolution = Resolution(
                    conflict_id=conflict.conflict_id,
                    strategy=strategy,
                    actions=actions,
                    status=ResolutionStatus.MANUAL_REQUIRED,
                    resolved_at=datetime.now().isoformat(),
                    description=f"Reference inconsistency requires manual resolution",
                )

                return resolution

            else:
                logger.error(f"Unsupported resolution strategy for reference inconsistencies: {strategy}")
                return None

        except Exception as e:
            logger.error(f"Failed to resolve reference inconsistency: {e}")
            return None

    def _resolve_dependency_conflict(self, conflict: Conflict, strategy: ResolutionStrategy) -> Optional[Resolution]:
        """Resolve a dependency conflict.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Dependency conflicts are not implemented yet
            logger.error("Dependency conflict resolution not implemented")
            return None

        except Exception as e:
            logger.error(f"Failed to resolve dependency conflict: {e}")
            return None

    def _resolve_version_conflict(self, conflict: Conflict, strategy: ResolutionStrategy) -> Optional[Resolution]:
        """Resolve a version conflict.

        Args:
            conflict: Conflict to resolve
            strategy: Resolution strategy to use

        Returns:
            Resolution if successful, None otherwise
        """
        try:
            # Version conflicts are not implemented yet
            logger.error("Version conflict resolution not implemented")
            return None

        except Exception as e:
            logger.error(f"Failed to resolve version conflict: {e}")
            return None

    def apply_resolution(self, resolution_id: str) -> bool:
        """Apply a resolution.

        This method executes the actions in a resolution to actually
        resolve the conflict.

        Args:
            resolution_id: ID of the resolution to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if resolution exists
            if resolution_id not in self.resolutions:
                logger.error(f"Resolution not found: {resolution_id}")
                return False

            resolution = self.resolutions[resolution_id]

            # Check if conflict exists
            if resolution.conflict_id not in self.conflicts:
                logger.error(f"Conflict not found: {resolution.conflict_id}")
                return False

            conflict = self.conflicts[resolution.conflict_id]

            # Apply actions
            for action in resolution.actions:
                action_type = action.get("action")

                if action_type == "delete":
                    # Delete a file
                    path = action.get("path")
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                            logger.info(f"Deleted file: {path}")
                        except Exception as e:
                            logger.error(f"Failed to delete file {path}: {e}")
                            return False

                elif action_type == "rename":
                    # Rename a file
                    path = action.get("path")
                    new_path = action.get("new_path")

                    if path and new_path and os.path.exists(path):
                        try:
                            os.rename(path, new_path)
                            logger.info(f"Renamed file: {path} -> {new_path}")
                        except Exception as e:
                            logger.error(f"Failed to rename file {path}: {e}")
                            return False

                elif action_type == "overwrite":
                    # Overwrite a file with another
                    path = action.get("path")
                    source_path = action.get("source_path")

                    if path and source_path and os.path.exists(source_path):
                        try:
                            # Copy source to destination
                            with open(source_path, "rb") as src, open(path, "wb") as dst:
                                dst.write(src.read())

                            logger.info(f"Overwrote file: {path} with {source_path}")
                        except Exception as e:
                            logger.error(f"Failed to overwrite file {path}: {e}")
                            return False

                elif action_type == "merge":
                    # Merge files
                    paths = action.get("paths", [])
                    output_path = action.get("output_path")

                    if paths and output_path:
                        try:
                            # Simple line-based merge
                            lines = []
                            for path in paths:
                                if os.path.exists(path):
                                    with open(path, "r", encoding="utf-8") as f:
                                        path_lines = f.readlines()

                                    lines.extend([f"# From {path}\n"])
                                    lines.extend(path_lines)
                                    lines.extend(["\n"])

                            # Write merged content
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.writelines(lines)

                            logger.info(f"Merged files into: {output_path}")
                        except Exception as e:
                            logger.error(f"Failed to merge files: {e}")
                            return False

                elif action_type == "update_resource":
                    # Update a resource in the registry
                    name = action.get("name")
                    access_pattern = action.get("access_pattern")

                    if name and access_pattern and get_registry:
                        try:
                            registry = get_registry()

                            # Find resources with the name
                            for resource_id, resource in getattr(registry, "resources", {}).items():
                                if resource.name == name:
                                    resource.access_pattern = access_pattern
                                    logger.info(f"Updated resource {name} access pattern: {access_pattern}")

                            # Save registry
                            if hasattr(registry, "_save_to_mcp"):
                                registry._save_to_mcp()
                        except Exception as e:
                            logger.error(f"Failed to update resource {name}: {e}")
                            return False

                elif action_type == "update_config":
                    # Update a configuration value
                    key = action.get("key")
                    value = action.get("value")

                    if key and value is not None and get_manager:
                        try:
                            manager = get_manager()
                            manager.set(key, value)
                            logger.info(f"Updated config {key}: {value}")
                        except Exception as e:
                            logger.error(f"Failed to update config {key}: {e}")
                            return False

                elif action_type == "manual":
                    # Manual action, nothing to do automatically
                    logger.info(f"Manual action required: {action.get('description')}")

                elif action_type == "keep":
                    # Keep action, nothing to do
                    logger.info(f"Keeping: {action.get('path')}")

                else:
                    logger.error(f"Unknown action type: {action_type}")
                    return False

            # Update resolution status
            resolution.status = ResolutionStatus.RESOLVED

            # Update conflict status
            conflict.resolution_status = ResolutionStatus.RESOLVED

            # Save to MCP memory
            self._save_to_mcp()

            return True

        except Exception as e:
            logger.error(f"Failed to apply resolution {resolution_id}: {e}")
            return False

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        """Get a conflict by ID.

        Args:
            conflict_id: ID of the conflict

        Returns:
            Conflict if found, None otherwise
        """
        return self.conflicts.get(conflict_id)

    def get_resolution(self, resolution_id: str) -> Optional[Resolution]:
        """Get a resolution by ID.

        Args:
            resolution_id: ID of the resolution

        Returns:
            Resolution if found, None otherwise
        """
        return self.resolutions.get(resolution_id)

    def get_all_conflicts(self, status: Optional[ResolutionStatus] = None) -> List[Conflict]:
        """Get all conflicts.

        Args:
            status: Filter by resolution status

        Returns:
            List of conflicts
        """
        if status:
            return [conflict for conflict in self.conflicts.values() if conflict.resolution_status == status]
        else:
            return list(self.conflicts.values())

    def get_all_resolutions(self, status: Optional[ResolutionStatus] = None) -> List[Resolution]:
        """Get all resolutions.

        Args:
            status: Filter by resolution status

        Returns:
            List of resolutions
        """
        if status:
            return [resolution for resolution in self.resolutions.values() if resolution.status == status]
        else:
            return list(self.resolutions.values())


# Singleton instance
_default_resolver: Optional[ConflictResolver] = None


def get_resolver(mcp_client: Optional[MCPClient] = None, force_new: bool = False) -> ConflictResolver:
    """Get the default conflict resolver.

    Args:
        mcp_client: Optional MCP client to use
        force_new: Force creation of a new resolver

    Returns:
        The default conflict resolver
    """
    global _default_resolver

    if _default_resolver is None or force_new:
        _default_resolver = ConflictResolver(mcp_client=mcp_client)

    return _default_resolver


# Convenience functions
def detect_conflicts(directory: Union[str, Path] = ".") -> List[Conflict]:
    """Detect all conflicts in a directory.

    Args:
        directory: Directory to scan

    Returns:
        List of detected conflicts
    """
    return get_resolver().detect_all_conflicts(directory)


def resolve_conflict(conflict_id: str, strategy: ResolutionStrategy, **kwargs) -> Optional[Resolution]:
    """Resolve a conflict.

    Args:
        conflict_id: ID of the conflict to resolve
        strategy: Resolution strategy to use
        **kwargs: Additional arguments for ConflictResolver.resolve_conflict()

    Returns:
        Resolution if successful, None otherwise
    """
    return get_resolver().resolve_conflict(conflict_id, strategy, **kwargs)


def apply_resolution(resolution_id: str) -> bool:
    """Apply a resolution.

    Args:
        resolution_id: ID of the resolution to apply

    Returns:
        True if successful, False otherwise
    """
    return get_resolver().apply_resolution(resolution_id)


if __name__ == "__main__":
    """Run the conflict resolver as a script."""
    import argparse

    parser = argparse.ArgumentParser(description="Conflict Resolver for AI Orchestra")
    parser.add_argument("--detect", action="store_true", help="Detect conflicts")
    parser.add_argument("--directory", default=".", help="Directory to scan")
    parser.add_argument("--resolve", metavar="CONFLICT_ID", help="Resolve a conflict")
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in ResolutionStrategy],
        help="Resolution strategy",
    )
    parser.add_argument("--apply", metavar="RESOLUTION_ID", help="Apply a resolution")
    parser.add_argument("--list", action="store_true", help="List conflicts")
    parser.add_argument(
        "--status",
        choices=[s.value for s in ResolutionStatus],
        help="Filter by resolution status",
    )

    args = parser.parse_args()

    resolver = ConflictResolver()

    if args.detect:
        conflicts = resolver.detect_all_conflicts(args.directory)
        print(f"Detected {len(conflicts)} conflicts")
        for conflict in conflicts:
            print(f"  - {conflict.conflict_id}: {conflict.description}")

    if args.resolve:
        if not args.strategy:
            print("Strategy required for resolution")
            exit(1)

        strategy = ResolutionStrategy(args.strategy)
        resolution = resolver.resolve_conflict(args.resolve, strategy)

        if resolution:
            print(f"Resolved conflict {args.resolve} using {strategy} strategy")
            print(f"  Status: {resolution.status}")
            print(f"  Actions:")
            for action in resolution.actions:
                print(f"    - {action.get('description')}")
        else:
            print(f"Failed to resolve conflict {args.resolve}")

    if args.apply:
        success = resolver.apply_resolution(args.apply)
        if success:
            print(f"Successfully applied resolution {args.apply}")
        else:
            print(f"Failed to apply resolution {args.apply}")

    if args.list or (not args.detect and not args.resolve and not args.apply):
        status = ResolutionStatus(args.status) if args.status else None
        conflicts = resolver.get_all_conflicts(status)

        print(f"Conflicts ({len(conflicts)}):")
        for conflict in conflicts:
            print(f"  - {conflict.conflict_id}: {conflict.description}")
            print(f"    Type: {conflict.conflict_type}")
            print(f"    Status: {conflict.resolution_status}")
            print(f"    Severity: {conflict.severity}")
            print()
