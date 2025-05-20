#!/usr/bin/env python3
"""
Scan GitHub Workflow Files for Inconsistencies

This script scans GitHub workflow files for inconsistencies and suggests
standardized approaches. It looks for:

1. Inconsistent GitHub Action versions
2. Hardcoded values that should be environment variables
3. Different authentication methods
4. Inconsistent Python versions

Usage:
    python scan_github_workflows.py [--path PATH] [--fix]

Options:
    --path PATH    Path to scan (default: .github/workflows)
    --fix          Generate suggested fixes (default: False)
"""

import argparse
import os
import re
import sys
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set, Tuple, Any


@dataclass
class WorkflowIssue:
    """Issue found in a workflow file."""

    file_path: Path
    issue_type: str
    description: str
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None


def scan_action_versions(workflow_data: Dict[str, Any]) -> List[WorkflowIssue]:
    """
    Scan for inconsistent GitHub Action versions.

    Args:
        workflow_data: Parsed workflow YAML data

    Returns:
        List of issues found
    """
    issues = []

    # Define latest versions of common actions
    latest_versions = {
        "actions/checkout": "v4",
        "actions/setup-python": "v4",
        "actions/setup-node": "v3",
        "actions/cache": "v3",
        "google-github-actions/auth": "v2",
        "google-github-actions/setup-gcloud": "v2",
        "docker/setup-buildx-action": "v3",
        "docker/build-push-action": "v5",
        "hashicorp/setup-terraform": "v2",
    }

    # Check steps in all jobs
    if "jobs" in workflow_data:
        for job_name, job_data in workflow_data["jobs"].items():
            if "steps" in job_data:
                for i, step in enumerate(job_data["steps"]):
                    if "uses" in step:
                        action = step["uses"]
                        # Extract action name and version
                        match = re.match(r"([^@]+)@(v\d+)", action)
                        if match:
                            action_name, version = match.groups()
                            if (
                                action_name in latest_versions
                                and version != latest_versions[action_name]
                            ):
                                issues.append(
                                    WorkflowIssue(
                                        file_path=Path(
                                            "unknown"
                                        ),  # Will be set by caller
                                        issue_type="Outdated Action Version",
                                        description=f"Action {action_name} is using version {version} instead of {latest_versions[action_name]}",
                                        suggested_fix=f"Update to: {action_name}@{latest_versions[action_name]}",
                                    )
                                )

    return issues


def scan_hardcoded_values(workflow_data: Dict[str, Any]) -> List[WorkflowIssue]:
    """
    Scan for hardcoded values that should be environment variables.

    Args:
        workflow_data: Parsed workflow YAML data

    Returns:
        List of issues found
    """
    issues = []

    # Define patterns for hardcoded values
    hardcoded_patterns = {
        "Project ID": (r"cherry-ai-project", "PROJECT_ID", "${{ env.PROJECT_ID }}"),
        "Region": (r"us-central1", "REGION", "${{ env.REGION }}"),
        "Service Account": (
            r"[a-z-]+@cherry-ai-project\.iam\.gserviceaccount\.com",
            "SERVICE_ACCOUNT",
            "${{ env.SERVICE_ACCOUNT }}",
        ),
        "WIF Provider": (
            r"projects/\d+/locations/global/workloadIdentityPools/[a-z-]+/providers/[a-z-]+",
            "WIF_PROVIDER",
            "${{ env.WIF_PROVIDER }}",
        ),
    }

    # Check env section
    if "env" in workflow_data:
        for key, value in workflow_data["env"].items():
            for name, (pattern, env_var, replacement) in hardcoded_patterns.items():
                if isinstance(value, str) and re.search(pattern, value):
                    issues.append(
                        WorkflowIssue(
                            file_path=Path("unknown"),  # Will be set by caller
                            issue_type="Hardcoded Value",
                            description=f"Hardcoded {name} in env.{key}: {value}",
                            suggested_fix=f"Use GitHub variable: ${{{{ vars.{env_var} || '{value}' }}}}",
                        )
                    )

    # Check steps in all jobs
    if "jobs" in workflow_data:
        for job_name, job_data in workflow_data["jobs"].items():
            if "steps" in job_data:
                for i, step in enumerate(job_data["steps"]):
                    if "with" in step:
                        for key, value in step["with"].items():
                            for name, (
                                pattern,
                                env_var,
                                replacement,
                            ) in hardcoded_patterns.items():
                                if isinstance(value, str) and re.search(pattern, value):
                                    issues.append(
                                        WorkflowIssue(
                                            file_path=Path(
                                                "unknown"
                                            ),  # Will be set by caller
                                            issue_type="Hardcoded Value",
                                            description=f"Hardcoded {name} in step {i+1} with.{key}: {value}",
                                            suggested_fix=f"Use environment variable: {replacement}",
                                        )
                                    )

    return issues


def scan_authentication_methods(workflow_data: Dict[str, Any]) -> List[WorkflowIssue]:
    """
    Scan for different authentication methods.

    Args:
        workflow_data: Parsed workflow YAML data

    Returns:
        List of issues found
    """
    issues = []

    # Check steps in all jobs
    if "jobs" in workflow_data:
        for job_name, job_data in workflow_data["jobs"].items():
            if "steps" in job_data:
                for i, step in enumerate(job_data["steps"]):
                    # Check for service account key authentication
                    if "run" in step and isinstance(step["run"], str):
                        if re.search(
                            r"gcloud auth activate-service-account.*--key-file",
                            step["run"],
                        ):
                            issues.append(
                                WorkflowIssue(
                                    file_path=Path("unknown"),  # Will be set by caller
                                    issue_type="Service Account Key Authentication",
                                    description=f"Using service account key authentication in step {i+1}",
                                    suggested_fix="Use Workload Identity Federation instead",
                                )
                            )

                    # Check for outdated Workload Identity Federation
                    if (
                        "uses" in step
                        and step["uses"] == "google-github-actions/auth@v1"
                    ):
                        issues.append(
                            WorkflowIssue(
                                file_path=Path("unknown"),  # Will be set by caller
                                issue_type="Outdated Authentication",
                                description=f"Using outdated google-github-actions/auth@v1 in step {i+1}",
                                suggested_fix="Update to google-github-actions/auth@v2",
                            )
                        )

    return issues


def scan_python_versions(workflow_data: Dict[str, Any]) -> List[WorkflowIssue]:
    """
    Scan for inconsistent Python versions.

    Args:
        workflow_data: Parsed workflow YAML data

    Returns:
        List of issues found
    """
    issues = []

    # Check steps in all jobs
    if "jobs" in workflow_data:
        for job_name, job_data in workflow_data["jobs"].items():
            if "steps" in job_data:
                for i, step in enumerate(job_data["steps"]):
                    if "uses" in step and step["uses"].startswith(
                        "actions/setup-python@"
                    ):
                        if "with" in step and "python-version" in step["with"]:
                            python_version = step["with"]["python-version"]
                            if python_version != "3.11":
                                issues.append(
                                    WorkflowIssue(
                                        file_path=Path(
                                            "unknown"
                                        ),  # Will be set by caller
                                        issue_type="Inconsistent Python Version",
                                        description=f"Using Python version {python_version} instead of 3.11 in step {i+1}",
                                        suggested_fix="Update to Python 3.11",
                                    )
                                )

    return issues


def scan_workflow_file(file_path: Path) -> List[WorkflowIssue]:
    """
    Scan a workflow file for issues.

    Args:
        file_path: Path to the workflow file

    Returns:
        List of issues found
    """
    issues = []

    try:
        with open(file_path, "r") as f:
            workflow_data = yaml.safe_load(f)

        # Run all scanners
        for scanner in [
            scan_action_versions,
            scan_hardcoded_values,
            scan_authentication_methods,
            scan_python_versions,
        ]:
            scanner_issues = scanner(workflow_data)
            for issue in scanner_issues:
                issue.file_path = file_path
            issues.extend(scanner_issues)

    except Exception as e:
        issues.append(
            WorkflowIssue(
                file_path=file_path,
                issue_type="Error",
                description=f"Error scanning file: {str(e)}",
            )
        )

    return issues


def scan_directory(directory: Path) -> List[WorkflowIssue]:
    """
    Scan a directory for workflow files.

    Args:
        directory: Directory to scan

    Returns:
        List of issues found
    """
    issues = []

    for file_path in directory.glob("*.yml"):
        issues.extend(scan_workflow_file(file_path))

    for file_path in directory.glob("*.yaml"):
        issues.extend(scan_workflow_file(file_path))

    return issues


def print_issues(issues: List[WorkflowIssue]) -> None:
    """
    Print issues found.

    Args:
        issues: List of issues found
    """
    if not issues:
        print("No issues found.")
        return

    print(f"Found {len(issues)} issues:")

    # Group issues by file
    issues_by_file = {}
    for issue in issues:
        if issue.file_path not in issues_by_file:
            issues_by_file[issue.file_path] = []
        issues_by_file[issue.file_path].append(issue)

    # Print issues by file
    for file_path, file_issues in issues_by_file.items():
        print(f"\n{file_path}:")
        for issue in file_issues:
            print(f"  {issue.issue_type}: {issue.description}")
            if issue.suggested_fix:
                print(f"    Suggested fix: {issue.suggested_fix}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Scan GitHub workflow files for inconsistencies"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".github/workflows",
        help="Path to scan (default: .github/workflows)",
    )
    parser.add_argument("--fix", action="store_true", help="Generate suggested fixes")
    args = parser.parse_args()

    directory = Path(args.path)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)

    print(f"Scanning {directory} for GitHub workflow files...")
    issues = scan_directory(directory)
    print_issues(issues)


if __name__ == "__main__":
    main()
