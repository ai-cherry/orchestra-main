#!/usr/bin/env python3
"""
Resource Registry for AI Orchestra

This module implements a centralized Resource Registry for AI assistants to discover
and maintain awareness of all available development resources (tools, APIs, credentials)
in a hybrid GCP-GitHub-Codespaces environment.

Key features:
- Automatic resource discovery across all environments
- Real-time monitoring of resource availability
- Resource dependency tracking
- Context-aware resource recommendation
- Integration with MCP memory system
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resource-registry")

# Import MCP client
try:
    from gcp_migration.mcp_client_enhanced import (
        MCPClient,
        MCPResponse,
    )
    from gcp_migration.mcp_client_enhanced import get_client as get_mcp_client
except ImportError:
    logger.warning("Could not import enhanced MCP client, attempting to import basic client")
    try:
        from gcp_migration.mcp_client import MCPClient
        from gcp_migration.mcp_client import get_client as get_mcp_client

        # Define a minimal MCPResponse if using the basic client
        class MCPResponse:
            def __init__(self, success, value=None, error=None, status_code=None):
                self.success = success
                self.value = value
                self.error = error
                self.status_code = status_code

            def __bool__(self):
                return self.success

    except ImportError:
        logger.error("Failed to import MCP client. Resource Registry will operate in offline mode.")
        MCPClient = object
        MCPResponse = object

        def get_mcp_client(*args, **kwargs):
            return None


class ResourceType(str, Enum):
    """Types of development resources that can be registered."""

    # Tools and utilities
    CLI_TOOL = "cli_tool"  # Command-line tools
    API_CLIENT = "api_client"  # API client libraries
    SDK = "sdk"  # Software Development Kits

    # Infrastructure and cloud resources
    GCP_SERVICE = "gcp_service"  # Google Cloud Platform services
    GCP_API = "gcp_api"  # Google Cloud Platform APIs
    GITHUB_ACTION = "github_action"  # GitHub Actions

    # Development environment resources
    CODESPACE = "codespace"  # GitHub Codespaces
    CONTAINER = "container"  # Docker containers
    LOCAL_SERVICE = "local_service"  # Locally running services

    # Credentials and access
    CREDENTIAL = "credential"  # Authentication credentials
    SERVICE_ACCOUNT = "service_account"  # Service accounts
    ACCESS_TOKEN = "access_token"  # Access tokens

    # Configuration and documentation
    CONFIG = "config"  # Configuration files
    DOCUMENT = "document"  # Documentation files
    TERRAFORM = "terraform"  # Terraform resources

    # AI tools
    AI_MODEL = "ai_model"  # AI models (Vertex AI, etc.)
    AI_TOOL = "ai_tool"  # AI tools registered with the tool registry


class ResourceStatus(str, Enum):
    """Status of a resource."""

    AVAILABLE = "available"  # Resource is available and operational
    UNAVAILABLE = "unavailable"  # Resource exists but is not currently available
    DEGRADED = "degraded"  # Resource is available but with reduced functionality
    UNKNOWN = "unknown"  # Resource status cannot be determined
    MISSING = "missing"  # Resource is missing or not found
    UNAUTHORIZED = "unauthorized"  # Resource exists but access is unauthorized


class Environment(str, Enum):
    """Environment where resources can be located."""

    LOCAL = "local"  # Local development machine
    CODESPACES = "codespaces"  # GitHub Codespaces
    GCP_CLOUD_RUN = "gcp_cloud_run"  # GCP Cloud Run
    GCP_WORKSTATION = "gcp_workstation"  # GCP Workstation
    CI_CD = "ci_cd"  # CI/CD pipelines
    ALL = "all"  # Available in all environments


class ResourcePriority(int, Enum):
    """Priority levels for resources."""

    CRITICAL = 0  # Critical resources that must be available
    HIGH = 1  # High priority resources
    MEDIUM = 2  # Medium priority resources
    LOW = 3  # Low priority resources
    OPTIONAL = 4  # Optional resources


class Resource:
    """Represents a development resource available to AI assistants."""

    def __init__(
        self,
        name: str,
        resource_type: ResourceType,
        environment: Environment,
        access_pattern: str,
        description: str = "",
        version: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        priority: ResourcePriority = ResourcePriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a development resource.

        Args:
            name: Unique identifier for the resource
            resource_type: Type of resource
            environment: Environment where the resource is available
            access_pattern: How to access the resource (URL, command, etc.)
            description: Human-readable description of the resource
            version: Version of the resource if applicable
            dependencies: List of resource names this resource depends on
            tags: List of tags for categorization and filtering
            priority: Priority level of the resource
            metadata: Additional metadata about the resource
        """
        self.name = name
        self.resource_type = resource_type
        self.environment = environment
        self.access_pattern = access_pattern
        self.description = description
        self.version = version
        self.dependencies = dependencies or []
        self.tags = tags or []
        self.priority = priority
        self.metadata = metadata or {}

        # Status tracking
        self.status = ResourceStatus.UNKNOWN
        self.last_verified = None
        self.last_accessed = None
        self.access_count = 0

        # Generate a unique ID based on name, type, and environment
        self.id = f"{name}:{resource_type}:{environment}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the resource to a dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "resource_type": self.resource_type,
            "environment": self.environment,
            "access_pattern": self.access_pattern,
            "description": self.description,
            "version": self.version,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "status": self.status,
            "last_verified": self.last_verified,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resource":
        """Create a resource from a dictionary."""
        resource = cls(
            name=data["name"],
            resource_type=data["resource_type"],
            environment=data["environment"],
            access_pattern=data["access_pattern"],
            description=data.get("description", ""),
            version=data.get("version"),
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", []),
            priority=ResourcePriority(data.get("priority", ResourcePriority.MEDIUM.value)),
            metadata=data.get("metadata", {}),
        )

        # Add status information
        resource.status = data.get("status", ResourceStatus.UNKNOWN)
        resource.last_verified = data.get("last_verified")
        resource.last_accessed = data.get("last_accessed")
        resource.access_count = data.get("access_count", 0)

        return resource

    def update_access(self) -> None:
        """Update the access tracking information."""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1

    def update_status(self, status: ResourceStatus) -> None:
        """Update the status of the resource."""
        self.status = status
        self.last_verified = datetime.now().isoformat()


class ResourceRegistry:
    """Central registry for all development resources."""

    # MCP memory keys
    REGISTRY_KEY = "resources:registry"
    DEPENDENCIES_KEY = "resources:dependencies"
    ACCESS_PATTERNS_KEY = "resources:access_patterns"

    def __init__(self, mcp_client: Optional[MCPClient] = None):
        """Initialize the Resource Registry.

        Args:
            mcp_client: An instance of MCPClient for accessing shared memory
        """
        self.mcp_client = mcp_client or get_mcp_client()
        self.resources: Dict[str, Resource] = {}
        self.initialized = False
        self._initialize_registry()

    def _initialize_registry(self) -> None:
        """Initialize the registry in MCP memory if it doesn't exist."""
        try:
            if self.mcp_client:
                # Fetch existing registry from MCP memory
                registry_response = self.mcp_client.get(self.REGISTRY_KEY)

                if registry_response and registry_response.success and registry_response.value:
                    # Registry exists, load it
                    registry_data = registry_response.value
                    for resource_data in registry_data.get("resources", []):
                        resource = Resource.from_dict(resource_data)
                        self.resources[resource.id] = resource

                    logger.info(f"Loaded {len(self.resources)} resources from MCP memory")

                else:
                    # Registry doesn't exist, create it
                    self._create_empty_registry()

            else:
                # No MCP client, create an empty registry
                logger.warning("No MCP client available. Creating in-memory registry only.")
                self.resources = {}

            self.initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize resource registry: {e}")
            self.resources = {}

    def _create_empty_registry(self) -> None:
        """Create an empty registry in MCP memory."""
        if not self.mcp_client:
            return

        try:
            # Create empty registry
            registry_data = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "resources": [],
            }

            # Save to MCP memory
            result = self.mcp_client.set(self.REGISTRY_KEY, registry_data)

            if result and result.success:
                logger.info("Created new resource registry in MCP memory")
            else:
                logger.error("Failed to create resource registry in MCP memory")

        except Exception as e:
            logger.error(f"Failed to create empty registry: {e}")

    def register_resource(self, resource: Resource) -> bool:
        """Register a resource in the registry.

        Args:
            resource: The resource to register

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to local registry
            self.resources[resource.id] = resource

            # Save to MCP memory if available
            if self.mcp_client:
                registry_response = self.mcp_client.get(self.REGISTRY_KEY)

                if registry_response and registry_response.success and registry_response.value:
                    registry_data = registry_response.value

                    # Convert all resources to dictionaries
                    resources_data = [r.to_dict() for r in self.resources.values()]

                    # Update registry data
                    registry_data["resources"] = resources_data
                    registry_data["updated_at"] = datetime.now().isoformat()

                    # Save back to MCP memory
                    result = self.mcp_client.set(self.REGISTRY_KEY, registry_data)

                    if not (result and result.success):
                        logger.error("Failed to save updated registry to MCP memory")
                        return False

            logger.info(f"Registered resource: {resource.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register resource {resource.name}: {e}")
            return False

    def unregister_resource(self, resource_id: str) -> bool:
        """Remove a resource from the registry.

        Args:
            resource_id: ID of the resource to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if resource exists
            if resource_id not in self.resources:
                logger.warning(f"Resource {resource_id} not found in registry")
                return False

            # Remove from local registry
            del self.resources[resource_id]

            # Update MCP memory if available
            if self.mcp_client:
                registry_response = self.mcp_client.get(self.REGISTRY_KEY)

                if registry_response and registry_response.success and registry_response.value:
                    registry_data = registry_response.value

                    # Convert all resources to dictionaries
                    resources_data = [r.to_dict() for r in self.resources.values()]

                    # Update registry data
                    registry_data["resources"] = resources_data
                    registry_data["updated_at"] = datetime.now().isoformat()

                    # Save back to MCP memory
                    result = self.mcp_client.set(self.REGISTRY_KEY, registry_data)

                    if not (result and result.success):
                        logger.error("Failed to save updated registry to MCP memory")
                        return False

            logger.info(f"Unregistered resource: {resource_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister resource {resource_id}: {e}")
            return False

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID.

        Args:
            resource_id: ID of the resource to retrieve

        Returns:
            The resource if found, None otherwise
        """
        try:
            # Check if resource exists in local registry
            if resource_id in self.resources:
                resource = self.resources[resource_id]
                resource.update_access()
                return resource

            # If using MCP memory, check for updates
            if self.mcp_client:
                self._refresh_from_mcp()

                # Check again after refresh
                if resource_id in self.resources:
                    resource = self.resources[resource_id]
                    resource.update_access()
                    return resource

            return None

        except Exception as e:
            logger.error(f"Failed to get resource {resource_id}: {e}")
            return None

    def _refresh_from_mcp(self) -> None:
        """Refresh the local registry from MCP memory."""
        if not self.mcp_client:
            return

        try:
            registry_response = self.mcp_client.get(self.REGISTRY_KEY)

            if registry_response and registry_response.success and registry_response.value:
                registry_data = registry_response.value

                # Clear local registry
                self.resources = {}

                # Load resources from registry data
                for resource_data in registry_data.get("resources", []):
                    resource = Resource.from_dict(resource_data)
                    self.resources[resource.id] = resource

        except Exception as e:
            logger.error(f"Failed to refresh registry from MCP memory: {e}")

    def list_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        environment: Optional[Environment] = None,
        tags: Optional[List[str]] = None,
        status: Optional[ResourceStatus] = None,
        min_priority: Optional[ResourcePriority] = None,
    ) -> List[Resource]:
        """List resources with optional filtering.

        Args:
            resource_type: Filter by resource type
            environment: Filter by environment
            tags: Filter by tags (all must match)
            status: Filter by status
            min_priority: Filter by minimum priority

        Returns:
            List of matching resources
        """
        try:
            # If using MCP memory, refresh first
            if self.mcp_client:
                self._refresh_from_mcp()

            # Start with all resources
            resources = list(self.resources.values())

            # Apply filters
            if resource_type:
                resources = [r for r in resources if r.resource_type == resource_type]

            if environment:
                resources = [r for r in resources if r.environment == environment or r.environment == Environment.ALL]

            if tags:
                tags_set = set(tags)
                resources = [r for r in resources if all(tag in r.tags for tag in tags_set)]

            if status:
                resources = [r for r in resources if r.status == status]

            if min_priority:
                # Lower numerical value means higher priority
                resources = [r for r in resources if r.priority.value <= min_priority.value]

            return resources

        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            return []

    async def verify_resource_status(self, resource_id: str) -> ResourceStatus:
        """Verify the status of a resource.

        This performs a verification check on the resource to determine
        its current status. The specific check depends on the resource type.

        Args:
            resource_id: ID of the resource to verify

        Returns:
            The updated status of the resource
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return ResourceStatus.MISSING

        try:
            # Perform verification based on resource type
            if resource.resource_type == ResourceType.CLI_TOOL:
                # Check if CLI tool exists in PATH
                import shutil

                status = ResourceStatus.AVAILABLE if shutil.which(resource.name) else ResourceStatus.MISSING

            elif resource.resource_type == ResourceType.GCP_SERVICE or resource.resource_type == ResourceType.GCP_API:
                # Check GCP service/API status
                # In a real implementation, this would use the Cloud APIs to check service status
                # For now, just assume it's available
                status = ResourceStatus.AVAILABLE

            elif resource.resource_type == ResourceType.LOCAL_SERVICE:
                # Check if local service is running
                # This would typically involve checking a port or endpoint
                # For now, just assume it's available
                status = ResourceStatus.AVAILABLE

            elif resource.resource_type == ResourceType.CREDENTIAL:
                # Check if credential exists and is valid
                if "path" in resource.metadata:
                    path = resource.metadata["path"]
                    if os.path.exists(path):
                        # Check if credential is expired
                        if "expiration" in resource.metadata:
                            expiration = resource.metadata["expiration"]
                            if expiration and datetime.fromisoformat(expiration) < datetime.now():
                                status = ResourceStatus.DEGRADED
                            else:
                                status = ResourceStatus.AVAILABLE
                        else:
                            status = ResourceStatus.AVAILABLE
                    else:
                        status = ResourceStatus.MISSING
                else:
                    # No path, can't verify
                    status = ResourceStatus.UNKNOWN

            else:
                # For other resource types, we can't easily verify
                status = ResourceStatus.UNKNOWN

            # Update resource status
            resource.update_status(status)

            # Update in registry
            self.register_resource(resource)

            return status

        except Exception as e:
            logger.error(f"Failed to verify resource {resource_id}: {e}")
            resource.update_status(ResourceStatus.UNKNOWN)
            return ResourceStatus.UNKNOWN

    async def verify_all_resources(self) -> Dict[str, ResourceStatus]:
        """Verify the status of all resources.

        Returns:
            Dictionary mapping resource IDs to their status
        """
        results = {}

        # Create tasks for all resources
        tasks = []
        for resource_id in self.resources:
            task = asyncio.create_task(self.verify_resource_status(resource_id))
            tasks.append((resource_id, task))

        # Wait for all tasks to complete
        for resource_id, task in tasks:
            try:
                status = await task
                results[resource_id] = status
            except Exception as e:
                logger.error(f"Failed to verify resource {resource_id}: {e}")
                results[resource_id] = ResourceStatus.UNKNOWN

        return results

    async def discover_resources(self) -> List[Resource]:
        """Discover resources in the current environment.

        This method performs automatic discovery of resources
        in the current environment. It updates the registry with
        any new resources found.

        Returns:
            List of newly discovered resources
        """
        new_resources = []

        # Determine current environment
        current_env = self._detect_environment()

        try:
            # Discover CLI tools in PATH
            await self._discover_cli_tools(current_env, new_resources)

            # Discover GCP resources
            await self._discover_gcp_resources(current_env, new_resources)

            # Discover GitHub resources
            await self._discover_github_resources(current_env, new_resources)

            # Discover local services
            await self._discover_local_services(current_env, new_resources)

            # Discover config files
            await self._discover_config_files(current_env, new_resources)

            # Discover credentials
            await self._discover_credentials(current_env, new_resources)

            # Return the list of new resources
            return new_resources

        except Exception as e:
            logger.error(f"Failed to discover resources: {e}")
            return []

    def _detect_environment(self) -> Environment:
        """Detect the current environment.

        Returns:
            The detected environment
        """
        # Check for GitHub Codespaces
        if os.environ.get("CODESPACES") == "true":
            return Environment.CODESPACES

        # Check for GCP Cloud Run
        if os.environ.get("K_SERVICE"):
            return Environment.GCP_CLOUD_RUN

        # Check for GCP Workstation
        if os.environ.get("CLOUD_WORKSTATIONS_AGENT"):
            return Environment.GCP_WORKSTATION

        # Check for CI/CD
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            return Environment.CI_CD

        # Default to local
        return Environment.LOCAL

    async def _discover_cli_tools(self, environment: Environment, new_resources: List[Resource]) -> None:
        """Discover CLI tools in the current environment.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
        """
        import shutil

        # Common CLI tools to check for
        cli_tools = [
            "gcloud",
            "gsutil",
            "terraform",
            "docker",
            "kubectl",
            "python",
            "pip",
            "node",
            "npm",
            "yarn",
            "git",
            "curl",
            "wget",
        ]

        for tool in cli_tools:
            # Check if tool exists in PATH
            path = shutil.which(tool)
            if path:
                # Check if tool is already registered
                tool_id = f"{tool}:{ResourceType.CLI_TOOL}:{environment}"
                if tool_id not in self.resources:
                    # Get version if possible
                    version = await self._get_cli_tool_version(tool)

                    # Create resource
                    resource = Resource(
                        name=tool,
                        resource_type=ResourceType.CLI_TOOL,
                        environment=environment,
                        access_pattern=path,
                        description=f"{tool} command-line tool",
                        version=version,
                        tags=["cli", tool],
                        priority=ResourcePriority.MEDIUM,
                        metadata={"path": path},
                    )

                    # Add to registry
                    if self.register_resource(resource):
                        new_resources.append(resource)

    async def _get_cli_tool_version(self, tool: str) -> Optional[str]:
        """Get the version of a CLI tool.

        Args:
            tool: Name of the CLI tool

        Returns:
            Version string if available, None otherwise
        """

        # Version command mapping
        version_commands = {
            "gcloud": ["gcloud", "--version"],
            "terraform": ["terraform", "--version"],
            "docker": ["docker", "--version"],
            "kubectl": ["kubectl", "version", "--client"],
            "python": ["python", "--version"],
            "pip": ["pip", "--version"],
            "node": ["node", "--version"],
            "npm": ["npm", "--version"],
            "yarn": ["yarn", "--version"],
            "git": ["git", "--version"],
            "curl": ["curl", "--version"],
            "wget": ["wget", "--version"],
        }

        if tool not in version_commands:
            return None

        try:
            # Run version command
            process = await asyncio.create_subprocess_exec(
                *version_commands[tool],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse version from output
                output = stdout.decode() if stdout else stderr.decode()
                # This is a simple version extraction that would need to be customized per tool
                return output.split("\n")[0].strip()
            else:
                return None

        except Exception:
            return None

    async def _discover_gcp_resources(self, environment: Environment, new_resources: List[Resource]) -> None:
        """Discover GCP resources.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
        """
        # Check if gcloud is available
        import shutil

        if not shutil.which("gcloud"):
            return

        try:
            # Get active GCP project
            pass

            process = await asyncio.create_subprocess_exec(
                "gcloud",
                "config",
                "get-value",
                "project",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await process.communicate()

            if process.returncode == 0:
                project_id = stdout.decode().strip()

                if project_id:
                    # Register GCP project as a resource
                    project_resource = Resource(
                        name=project_id,
                        resource_type=ResourceType.GCP_SERVICE,
                        environment=environment,
                        access_pattern=f"gcloud config set project {project_id}",
                        description=f"GCP Project: {project_id}",
                        version=None,
                        tags=["gcp", "project"],
                        priority=ResourcePriority.HIGH,
                        metadata={"project_id": project_id},
                    )

                    # Add to registry
                    if self.register_resource(project_resource):
                        new_resources.append(project_resource)

                    # Discover enabled APIs
                    await self._discover_gcp_apis(environment, new_resources, project_id)

        except Exception as e:
            logger.error(f"Failed to discover GCP project: {e}")

    async def _discover_gcp_apis(
        self, environment: Environment, new_resources: List[Resource], project_id: str
    ) -> None:
        """Discover enabled GCP APIs.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
            project_id: GCP project ID
        """
        try:
            # Get enabled APIs
            pass

            process = await asyncio.create_subprocess_exec(
                "gcloud",
                "services",
                "list",
                "--project",
                project_id,
                "--format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await process.communicate()

            if process.returncode == 0:
                apis = json.loads(stdout.decode())

                for api in apis:
                    name = api.get("config", {}).get("name", "")
                    if name:
                        # Extract API name from full name
                        api_name = name.split(".")[0]

                        # Register API as a resource
                        api_resource = Resource(
                            name=api_name,
                            resource_type=ResourceType.GCP_API,
                            environment=environment,
                            access_pattern=f"gcloud services enable {name}",
                            description=f"GCP API: {name}",
                            version=None,
                            tags=["gcp", "api", api_name],
                            priority=ResourcePriority.MEDIUM,
                            metadata={"project_id": project_id, "api": name},
                        )

                        # Add to registry
                        if self.register_resource(api_resource):
                            new_resources.append(api_resource)

        except Exception as e:
            logger.error(f"Failed to discover GCP APIs: {e}")

    async def _discover_github_resources(self, environment: Environment, new_resources: List[Resource]) -> None:
        """Discover GitHub resources.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
        """
        # Check if git is available
        import shutil

        if not shutil.which("git"):
            return

        try:
            # Get git remote origin URL
            pass

            process = await asyncio.create_subprocess_exec(
                "git",
                "config",
                "--get",
                "remote.origin.url",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await process.communicate()

            if process.returncode == 0:
                remote_url = stdout.decode().strip()

                if remote_url:
                    # Extract repository name from URL
                    import re

                    match = re.search(r"([^/]+)/([^/]+)\.git$", remote_url)
                    if match:
                        owner, repo = match.groups()

                        # Register GitHub repository as a resource
                        repo_resource = Resource(
                            name=f"{owner}/{repo}",
                            resource_type=ResourceType.GITHUB_ACTION,
                            environment=environment,
                            access_pattern=remote_url,
                            description=f"GitHub Repository: {owner}/{repo}",
                            version=None,
                            tags=["github", "repository", owner, repo],
                            priority=ResourcePriority.HIGH,
                            metadata={"owner": owner, "repo": repo, "url": remote_url},
                        )

                        # Add to registry
                        if self.register_resource(repo_resource):
                            new_resources.append(repo_resource)

                        # Check for GitHub Actions
                        await self._discover_github_actions(environment, new_resources, owner, repo)

        except Exception as e:
            logger.error(f"Failed to discover GitHub resources: {e}")

    async def _discover_github_actions(
        self,
        environment: Environment,
        new_resources: List[Resource],
        owner: str,
        repo: str,
    ) -> None:
        """Discover GitHub Actions.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
            owner: GitHub repository owner
            repo: GitHub repository name
        """
        try:
            # Check for .github/workflows directory
            workflows_dir = Path(".github/workflows")
            if not workflows_dir.exists() or not workflows_dir.is_dir():
                return

            # Find workflow files
            for workflow_file in workflows_dir.glob("*.yml"):
                try:
                    with open(workflow_file, "r") as f:
                        workflow = f.read()

                    # Extract workflow name
                    import re

                    name_match = re.search(r"name:\s*(.+)", workflow)
                    workflow_name = name_match.group(1).strip() if name_match else workflow_file.stem

                    # Register GitHub Action as a resource
                    action_resource = Resource(
                        name=workflow_name,
                        resource_type=ResourceType.GITHUB_ACTION,
                        environment=environment,
                        access_pattern=f"https://github.com/{owner}/{repo}/actions",
                        description=f"GitHub Action: {workflow_name}",
                        version=None,
                        tags=["github", "action", workflow_name],
                        priority=ResourcePriority.MEDIUM,
                        metadata={
                            "owner": owner,
                            "repo": repo,
                            "file": str(workflow_file),
                            "url": f"https://github.com/{owner}/{repo}/actions",
                        },
                    )

                    # Add to registry
                    if self.register_resource(action_resource):
                        new_resources.append(action_resource)

                except Exception as e:
                    logger.error(f"Failed to parse workflow file {workflow_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to discover GitHub Actions: {e}")

    async def _discover_local_services(self, environment: Environment, new_resources: List[Resource]) -> None:
        """Discover local services.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
        """
        # Simply check for common ports that might be running services
        common_ports = [
            (8000, "Django/FastAPI"),
            (8080, "Web Server"),
            (5000, "Flask"),
            (3000, "Node.js/React"),
            (4200, "Angular"),
            (5432, "PostgreSQL"),
            (6379, "Redis"),
            (27017, "MongoDB"),
            (9000, "SonarQube"),
            (9090, "Prometheus"),
            (3306, "MySQL"),
            (8888, "Jupyter Notebook"),
        ]

        for port, service_name in common_ports:
            if await self._check_port_open("localhost", port):
                # Register local service as a resource
                service_resource = Resource(
                    name=f"{service_name} on port {port}",
                    resource_type=ResourceType.LOCAL_SERVICE,
                    environment=environment,
                    access_pattern=f"http://localhost:{port}",
                    description=f"Local {service_name} service on port {port}",
                    version=None,
                    tags=["local", "service", service_name.lower()],
                    priority=ResourcePriority.MEDIUM,
                    metadata={
                        "port": port,
                        "host": "localhost",
                        "service": service_name,
                    },
                )

                # Add to registry
                if self.register_resource(service_resource):
                    new_resources.append(service_resource)

    async def _check_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open on a host.

        Args:
            host: Host to check
            port: Port to check

        Returns:
            True if the port is open, False otherwise
        """
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    async def _discover_config_files(self, environment: Environment, new_resources: List[Resource]) -> None:
        """Discover configuration files.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
        """
        # Look for common configuration files
        config_files = [
            (".env", "Environment Variables"),
            ("pyproject.toml", "Python Project Configuration"),
            ("package.json", "Node.js Package Configuration"),
            ("requirements.txt", "Python Requirements"),
            ("docker-compose.yml", "Docker Compose Configuration"),
            ("Dockerfile", "Docker Configuration"),
            (".gitignore", "Git Ignore Configuration"),
            ("terraform/main.tf", "Terraform Configuration"),
            ("poetry.lock", "Poetry Lock File"),
        ]

        for file_path, description in config_files:
            path = Path(file_path)
            if path.exists() and path.is_file():
                # Register config file as a resource
                config_resource = Resource(
                    name=path.name,
                    resource_type=ResourceType.CONFIG,
                    environment=environment,
                    access_pattern=str(path),
                    description=description,
                    version=None,
                    tags=["config", path.name.lower()],
                    priority=ResourcePriority.MEDIUM,
                    metadata={"path": str(path), "type": description},
                )

                # Add to registry
                if self.register_resource(config_resource):
                    new_resources.append(config_resource)

    async def _discover_credentials(self, environment: Environment, new_resources: List[Resource]) -> None:
        """Discover credential files.

        Args:
            environment: Current environment
            new_resources: List to add newly discovered resources to
        """
        # Look for common credential files and environment variables
        credential_locations = [
            (
                "~/.config/gcloud/application_default_credentials.json",
                "GCP Application Default Credentials",
            ),
            ("~/.aws/credentials", "AWS Credentials"),
            ("~/.kube/config", "Kubernetes Configuration"),
        ]

        for file_path, description in credential_locations:
            path = Path(os.path.expanduser(file_path))
            if path.exists() and path.is_file():
                # Register credential as a resource
                cred_resource = Resource(
                    name=path.name,
                    resource_type=ResourceType.CREDENTIAL,
                    environment=environment,
                    access_pattern=str(path),
                    description=description,
                    version=None,
                    tags=["credential", path.name.lower()],
                    priority=ResourcePriority.HIGH,
                    metadata={"path": str(path), "type": description},
                )

                # Add to registry
                if self.register_resource(cred_resource):
                    new_resources.append(cred_resource)

        # Check for environment variables that might contain credentials
        credential_env_vars = [
            ("GOOGLE_APPLICATION_CREDENTIALS", "GCP Service Account Key Path"),
            ("GOOGLE_CLOUD_PROJECT", "GCP Project ID"),
            ("AWS_ACCESS_KEY_ID", "AWS Access Key"),
            ("GITHUB_TOKEN", "GitHub Token"),
        ]

        for env_var, description in credential_env_vars:
            if env_var in os.environ:
                # Register environment variable as a resource
                env_resource = Resource(
                    name=env_var,
                    resource_type=ResourceType.CREDENTIAL,
                    environment=environment,
                    access_pattern=f"os.environ['{env_var}']",
                    description=description,
                    version=None,
                    tags=["credential", "environment-variable", env_var.lower()],
                    priority=ResourcePriority.HIGH,
                    metadata={"type": "environment-variable", "variable": env_var},
                )

                # Add to registry
                if self.register_resource(env_resource):
                    new_resources.append(env_resource)


# Singleton instance
_default_registry: Optional[ResourceRegistry] = None


def get_registry(mcp_client: Optional[MCPClient] = None, force_new: bool = False) -> ResourceRegistry:
    """Get the default resource registry.

    Args:
        mcp_client: Optional MCP client to use
        force_new: Force creation of a new registry

    Returns:
        The default resource registry
    """
    global _default_registry

    if _default_registry is None or force_new:
        _default_registry = ResourceRegistry(mcp_client)

    return _default_registry


async def discover_resources() -> List[Resource]:
    """Discover resources in the current environment.

    Convenience function that uses the default registry.

    Returns:
        List of newly discovered resources
    """
    registry = get_registry()
    return await registry.discover_resources()


async def verify_resources() -> Dict[str, ResourceStatus]:
    """Verify the status of all resources.

    Convenience function that uses the default registry.

    Returns:
        Dictionary mapping resource IDs to their status
    """
    registry = get_registry()
    return await registry.verify_all_resources()


if __name__ == "__main__":
    """Run the resource registry as a script to discover resources."""
    import argparse

    parser = argparse.ArgumentParser(description="Resource Registry for AI Orchestra")
    parser.add_argument("--discover", action="store_true", help="Discover resources")
    parser.add_argument("--verify", action="store_true", help="Verify resource status")
    parser.add_argument("--list", action="store_true", help="List resources")

    args = parser.parse_args()

    async def main():
        registry = get_registry()

        if args.discover:
            print("Discovering resources...")
            resources = await registry.discover_resources()
            print(f"Discovered {len(resources)} new resources")

            for resource in resources:
                print(f"  - {resource.name} ({resource.resource_type})")

        if args.verify:
            print("Verifying resources...")
            statuses = await registry.verify_all_resources()
            print(f"Verified {len(statuses)} resources")

            for resource_id, status in statuses.items():
                resource = registry.get_resource(resource_id)
                if resource:
                    print(f"  - {resource.name}: {status}")

        if args.list or (not args.discover and not args.verify):
            print("Available resources:")
            resources = registry.list_resources()

            for resource in resources:
                print(f"  - {resource.name} ({resource.resource_type}): {resource.status}")
                print(f"    Access: {resource.access_pattern}")
                print(f"    Description: {resource.description}")
                print()

    asyncio.run(main())
