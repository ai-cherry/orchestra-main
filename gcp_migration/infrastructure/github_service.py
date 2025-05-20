"""
GitHub service implementation for interacting with GitHub repositories and Codespaces.

This module provides the implementation of the IGitHubService interface,
allowing the application to fetch repository information, Codespaces configurations,
and other GitHub-related data.
"""

import json
import os
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

import httpx
from httpx import AsyncClient, Response

from gcp_migration.config.settings import settings
from gcp_migration.domain.exceptions import (
    AuthenticationError,
    GitHubError,
    ResourceNotFoundError,
    ValidationError,
)
from gcp_migration.domain.interfaces import IGitHubService
from gcp_migration.domain.models import CodespacesConfig, RepositoryInfo
from gcp_migration.utils.errors import async_wrap_exceptions
from gcp_migration.utils.logging import get_logger


logger = get_logger(__name__)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"


class GitHubService(IGitHubService):
    """
    Service for interacting with GitHub API.

    This service provides methods for fetching repository information,
    Codespaces configurations, and other GitHub-related data.
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        github_api_url: str = GITHUB_API_BASE,
        timeout: int = 30,
    ):
        """
        Initialize the GitHub service.

        Args:
            github_token: GitHub personal access token (defaults to settings)
            github_api_url: GitHub API base URL
            timeout: Request timeout in seconds
        """
        # Get token from settings if not provided
        self.github_token = github_token or (
            settings.github_token.get_secret_value() if settings.github_token else None
        )
        if not self.github_token:
            logger.warning(
                "GitHub token not provided. Some operations may fail due to rate limiting or authorization."
            )

        self.api_url = github_api_url
        self.timeout = timeout
        self.client: Optional[AsyncClient] = None

    async def __aenter__(self) -> "GitHubService":
        """Support using as async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up resources when exiting context."""
        await self.close()

    async def connect(self) -> None:
        """Initialize the HTTP client."""
        if self.client is None or self.client.is_closed:
            # Set up headers
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"GCP-Migration-Toolkit/{settings.app_version}",
            }

            # Add authorization if token is available
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"

            self.client = AsyncClient(
                base_url=self.api_url,
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True,
            )
            logger.debug("GitHub API client initialized")

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None
            logger.debug("GitHub API client closed")

    @async_wrap_exceptions(
        GitHubError,
        (httpx.HTTPError, ValueError, json.JSONDecodeError),
        "Failed to communicate with GitHub API",
    )
    async def _request(self, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Make a request to the GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL path (without base URL)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Parsed JSON response

        Raises:
            GitHubError: If the request fails or the response is invalid
        """
        # Ensure client is initialized
        if self.client is None or self.client.is_closed:
            await self.connect()

        # Ensure we have a client now
        if self.client is None:
            raise GitHubError(message="Failed to initialize GitHub API client")

        client = cast(AsyncClient, self.client)

        # Make request
        response: Response = await client.request(method, url, **kwargs)

        # Handle errors
        if response.status_code == 401:
            raise AuthenticationError(
                message="Invalid GitHub token or insufficient permissions"
            )
        elif response.status_code == 403:
            if "rate limit exceeded" in response.text.lower():
                raise GitHubError(message="GitHub API rate limit exceeded")
            else:
                raise AuthenticationError(
                    message="Forbidden: Check GitHub token permissions"
                )
        elif response.status_code == 404:
            raise ResourceNotFoundError(message=f"Resource not found: {url}")
        elif response.status_code >= 400:
            raise GitHubError(
                message=f"GitHub API error: {response.status_code} - {response.text}"
            )

        # Parse JSON
        return response.json()

    @async_wrap_exceptions(
        GitHubError,
        (httpx.HTTPError, ValueError, KeyError),
        "Failed to get repository information",
    )
    async def get_repository_info(self, repository_name: str) -> RepositoryInfo:
        """
        Get information about a GitHub repository.

        Args:
            repository_name: The name of the GitHub repository

        Returns:
            Information about the repository

        Raises:
            ResourceNotFoundError: If the repository doesn't exist
            GitHubError: If another error occurs
        """
        logger.info(f"Fetching repository information for: {repository_name}")

        # Format repository name (handle full URLs, etc.)
        formatted_name = self._format_repository_name(repository_name)

        # Get repository information
        repo_data = await self._request("GET", f"/repos/{formatted_name}")

        # Get branches
        branches_data = await self._request("GET", f"/repos/{formatted_name}/branches")
        branches = [branch["name"] for branch in branches_data]

        # Check if repository has a devcontainer
        has_devcontainer = False
        try:
            devcontainer_content = await self._request(
                "GET", f"/repos/{formatted_name}/contents/.devcontainer"
            )
            has_devcontainer = (
                isinstance(devcontainer_content, list) and len(devcontainer_content) > 0
            )
        except ResourceNotFoundError:
            # No .devcontainer directory found, which is fine
            pass

        # Check if repository has GitHub Actions
        has_github_actions = False
        try:
            actions_content = await self._request(
                "GET", f"/repos/{formatted_name}/contents/.github/workflows"
            )
            has_github_actions = (
                isinstance(actions_content, list) and len(actions_content) > 0
            )
        except ResourceNotFoundError:
            # No GitHub Actions found, which is fine
            pass

        # Get codespaces configuration if available
        codespaces_config = None
        if has_devcontainer:
            try:
                codespaces_config = await self.get_codespace_config(formatted_name)
            except Exception as e:
                logger.warning(f"Failed to get Codespaces config: {e}")

        # Check for secrets
        secret_count = 0
        try:
            secrets_data = await self._request(
                "GET", f"/repos/{formatted_name}/actions/secrets"
            )
            if "total_count" in secrets_data:
                secret_count = secrets_data["total_count"]
        except Exception as e:
            logger.warning(f"Failed to get secrets count: {e}")

        # Create repository info
        result = RepositoryInfo(
            name=repository_name,
            full_name=repo_data["full_name"],
            description=repo_data.get("description"),
            size_kb=repo_data.get("size", 0),
            branches=branches,
            default_branch=repo_data.get("default_branch", "main"),
            codespaces_config=codespaces_config,
            has_devcontainer=has_devcontainer,
            has_github_actions=has_github_actions,
            has_secrets=secret_count > 0,
            secret_count=secret_count,
            clone_url=repo_data.get("clone_url"),
            created_at=repo_data.get("created_at"),
            updated_at=repo_data.get("updated_at"),
        )

        logger.info(
            f"Successfully fetched repository information for: {repository_name}"
        )
        return result

    @async_wrap_exceptions(
        GitHubError,
        (httpx.HTTPError, ValueError, KeyError),
        "Failed to get Codespaces configuration",
    )
    async def get_codespace_config(self, repository_name: str) -> Dict[str, Any]:
        """
        Get the GitHub Codespaces configuration for a repository.

        Args:
            repository_name: The name of the GitHub repository

        Returns:
            The Codespaces configuration

        Raises:
            ResourceNotFoundError: If the repository or configuration doesn't exist
            GitHubError: If another error occurs
        """
        logger.info(f"Fetching Codespaces configuration for: {repository_name}")

        # Format repository name
        formatted_name = self._format_repository_name(repository_name)

        # Check for .devcontainer/devcontainer.json
        try:
            content_data = await self._request(
                "GET",
                f"/repos/{formatted_name}/contents/.devcontainer/devcontainer.json",
            )
            if "content" in content_data and content_data.get("encoding") == "base64":
                import base64

                content = base64.b64decode(content_data["content"]).decode("utf-8")
                config = json.loads(content)
                logger.info(f"Found devcontainer.json for {repository_name}")
                return config
        except ResourceNotFoundError:
            # Try alternate locations
            pass

        # Check for .devcontainer.json in root
        try:
            content_data = await self._request(
                "GET", f"/repos/{formatted_name}/contents/.devcontainer.json"
            )
            if "content" in content_data and content_data.get("encoding") == "base64":
                import base64

                content = base64.b64decode(content_data["content"]).decode("utf-8")
                config = json.loads(content)
                logger.info(f"Found .devcontainer.json for {repository_name}")
                return config
        except ResourceNotFoundError:
            # No devcontainer.json found
            logger.warning(f"No devcontainer.json found for {repository_name}")
            raise ResourceNotFoundError(
                message=f"No Codespaces configuration found for {repository_name}"
            )

    @async_wrap_exceptions(
        GitHubError,
        (httpx.HTTPError, ValueError, KeyError),
        "Failed to get VS Code extensions",
    )
    async def get_extensions(self, repository_name: str) -> List[str]:
        """
        Get VS Code extensions from GitHub Codespaces configuration.

        Args:
            repository_name: The name of the GitHub repository

        Returns:
            List of extension IDs

        Raises:
            ResourceNotFoundError: If the repository or configuration doesn't exist
            GitHubError: If another error occurs
        """
        logger.info(f"Fetching VS Code extensions for: {repository_name}")

        try:
            # Get Codespaces configuration
            config = await self.get_codespace_config(repository_name)

            # Extract extensions
            extensions = []

            # Check for "extensions" field directly
            if "extensions" in config and isinstance(config["extensions"], list):
                extensions.extend(config["extensions"])

            # Check for "customizations.vscode.extensions"
            if "customizations" in config and isinstance(
                config["customizations"], dict
            ):
                vscode = config["customizations"].get("vscode", {})
                if "extensions" in vscode and isinstance(vscode["extensions"], list):
                    extensions.extend(vscode["extensions"])

            logger.info(f"Found {len(extensions)} extensions for {repository_name}")
            return extensions
        except ResourceNotFoundError:
            # No Codespaces configuration found
            logger.warning(f"No extensions found for {repository_name}")
            return []

    def _format_repository_name(self, repository_name: str) -> str:
        """
        Format repository name to be used in GitHub API calls.

        Args:
            repository_name: The repository name, which could be a simple name,
                            owner/repo format, or a full URL

        Returns:
            Formatted repository name in the format "owner/repo"

        Raises:
            ValidationError: If the repository name is invalid
        """
        # Handle empty values
        if not repository_name:
            raise ValidationError(message="Repository name cannot be empty")

        # Handle URLs
        if repository_name.startswith(("http://", "https://")):
            # Parse URL
            parsed = urlparse(repository_name)
            path = parsed.path.strip("/")

            # Extract owner/repo from path
            if path.count("/") >= 1:
                return "/".join(path.split("/")[:2])
            else:
                raise ValidationError(
                    message=f"Invalid repository URL: {repository_name}"
                )

        # Handle owner/repo format
        if "/" in repository_name:
            parts = repository_name.split("/")
            if len(parts) == 2:
                return repository_name
            elif len(parts) > 2:
                # Take first two parts as owner/repo
                return "/".join(parts[:2])

        # Handle simple name with default organization
        if settings.github_organization:
            return f"{settings.github_organization}/{repository_name}"

        # If we get here, we don't have enough information
        raise ValidationError(
            message=f"Invalid repository name: {repository_name}. "
            f"Please provide as 'owner/repo' or configure github_organization in settings."
        )
