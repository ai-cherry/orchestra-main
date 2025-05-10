#!/usr/bin/env python3
"""
WIF Dependency Validator and Tester

This script validates dependencies and tests the Workload Identity Federation (WIF)
implementation for the AI Orchestra project. It helps ensure that all required
dependencies are installed and properly configured, and that the WIF implementation
works as expected.

The script performs the following validations:
1. Checks for required dependencies and their versions
2. Validates the WIF setup and verification scripts
3. Tests the GitHub Actions workflow template
4. Provides a comprehensive report on the validation results

Usage:
    python wif_dependency_validator.py [options]

Options:
    --check-deps          Check for required dependencies
    --validate-scripts    Validate WIF scripts
    --validate-workflow   Validate GitHub Actions workflow
    --test-setup          Test WIF setup in a sandbox environment
    --all                 Perform all validations
    --report              Generate a detailed report
    --output PATH         Path to write the report to
    --verbose             Show detailed output during processing
    --help                Show this help message and exit
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("wif_validator")


class ValidationStatus(Enum):
    """Status of a validation check."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class DependencyCheck:
    """Result of a dependency check."""
    name: str
    required_version: Optional[str] = None
    actual_version: Optional[str] = None
    status: ValidationStatus = ValidationStatus.SKIPPED
    message: str = ""


@dataclass
class ScriptValidation:
    """Result of a script validation."""
    script_path: str
    status: ValidationStatus = ValidationStatus.SKIPPED
    issues: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class WorkflowValidation:
    """Result of a workflow validation."""
    workflow_path: str
    status: ValidationStatus = ValidationStatus.SKIPPED
    issues: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class ValidationResult:
    """Overall validation results."""
    dependency_checks: List[DependencyCheck] = field(default_factory=list)
    script_validations: List[ScriptValidation] = field(default_factory=list)
    workflow_validations: List[WorkflowValidation] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    
    def add_dependency_check(self, check: DependencyCheck) -> None:
        """Add a dependency check result."""
        self.dependency_checks.append(check)
    
    def add_script_validation(self, validation: ScriptValidation) -> None:
        """Add a script validation result."""
        self.script_validations.append(validation)
    
    def add_workflow_validation(self, validation: WorkflowValidation) -> None:
        """Add a workflow validation result."""
        self.workflow_validations.append(validation)
    
    def get_failed_checks(self) -> List[DependencyCheck]:
        """Get all failed dependency checks."""
        return [check for check in self.dependency_checks if check.status == ValidationStatus.FAILED]
    
    def get_failed_script_validations(self) -> List[ScriptValidation]:
        """Get all failed script validations."""
        return [validation for validation in self.script_validations if validation.status == ValidationStatus.FAILED]
    
    def get_failed_workflow_validations(self) -> List[WorkflowValidation]:
        """Get all failed workflow validations."""
        return [validation for validation in self.workflow_validations if validation.status == ValidationStatus.FAILED]
    
    def has_failures(self) -> bool:
        """Check if there are any failures in the validation results."""
        return (
            len(self.get_failed_checks()) > 0
            or len(self.get_failed_script_validations()) > 0
            or len(self.get_failed_workflow_validations()) > 0
        )


class WIFDependencyValidator:
    """
    Validator for WIF dependencies and implementation.
    
    This class provides functionality to validate dependencies and test the
    Workload Identity Federation implementation for the AI Orchestra project.
    """
    
    # Required dependencies and their minimum versions
    REQUIRED_DEPENDENCIES = {
        "gh": "2.0.0",  # GitHub CLI
        "gcloud": "400.0.0",  # Google Cloud SDK
        "jq": "1.6",  # jq for JSON processing
        "python": "3.8.0",  # Python
        "bash": "4.0.0",  # Bash
    }
    
    # Required GCP APIs
    REQUIRED_GCP_APIS = [
        "iam.googleapis.com",
        "iamcredentials.googleapis.com",
        "cloudresourcemanager.googleapis.com",
        "run.googleapis.com",
        "artifactregistry.googleapis.com",
    ]
    
    # Required GitHub Actions dependencies
    REQUIRED_GH_ACTIONS = {
        "google-github-actions/auth": "v2",
        "google-github-actions/setup-gcloud": "v2",
        "docker/setup-buildx-action": "v3",
        "docker/build-push-action": "v5",
    }
    
    # WIF scripts to validate
    WIF_SCRIPTS = [
        "setup_wif.sh",
        "verify_wif_setup.sh",
        "migrate_to_wif.sh",
    ]
    
    # WIF workflow templates to validate
    WIF_WORKFLOWS = [
        ".github/workflows/wif-deploy-template.yml",
    ]
    
    def __init__(
        self,
        base_path: Union[str, Path] = ".",
        verbose: bool = False,
    ):
        """
        Initialize the WIF dependency validator.
        
        Args:
            base_path: The base path for the project
            verbose: Whether to show detailed output during processing
        """
        self.base_path = Path(base_path).resolve()
        self.verbose = verbose
        self.validation_result = ValidationResult()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"Initialized WIF dependency validator with base path: {self.base_path}")
    
    def check_dependencies(self) -> List[DependencyCheck]:
        """
        Check for required dependencies and their versions.
        
        Returns:
            A list of dependency check results
        """
        logger.info("Checking dependencies...")
        
        results = []
        
        for dep_name, required_version in self.REQUIRED_DEPENDENCIES.items():
            logger.debug(f"Checking dependency: {dep_name} (required: {required_version})")
            
            check = DependencyCheck(
                name=dep_name,
                required_version=required_version,
            )
            
            # Check if dependency is installed
            if not shutil.which(dep_name):
                check.status = ValidationStatus.FAILED
                check.message = f"{dep_name} is not installed or not in PATH"
                results.append(check)
                self.validation_result.add_dependency_check(check)
                continue
            
            # Get version
            try:
                if dep_name == "gh":
                    version_output = subprocess.check_output(["gh", "--version"], text=True)
                    version_match = re.search(r"gh version (\d+\.\d+\.\d+)", version_output)
                elif dep_name == "gcloud":
                    version_output = subprocess.check_output(["gcloud", "--version"], text=True)
                    version_match = re.search(r"Google Cloud SDK (\d+\.\d+\.\d+)", version_output)
                elif dep_name == "jq":
                    version_output = subprocess.check_output(["jq", "--version"], text=True)
                    version_match = re.search(r"jq-(\d+\.\d+)", version_output)
                elif dep_name == "python":
                    version_output = subprocess.check_output(["python", "--version"], text=True)
                    version_match = re.search(r"Python (\d+\.\d+\.\d+)", version_output)
                elif dep_name == "bash":
                    version_output = subprocess.check_output(["bash", "--version"], text=True)
                    version_match = re.search(r"version (\d+\.\d+\.\d+)", version_output)
                else:
                    version_match = None
                
                if version_match:
                    actual_version = version_match.group(1)
                    check.actual_version = actual_version
                    
                    # Compare versions
                    if self._compare_versions(actual_version, required_version) >= 0:
                        check.status = ValidationStatus.PASSED
                        check.message = f"{dep_name} {actual_version} is installed (required: {required_version})"
                    else:
                        check.status = ValidationStatus.FAILED
                        check.message = f"{dep_name} {actual_version} is installed, but {required_version} or higher is required"
                else:
                    check.status = ValidationStatus.WARNING
                    check.message = f"Could not determine version of {dep_name}"
            except subprocess.CalledProcessError:
                check.status = ValidationStatus.FAILED
                check.message = f"Error checking version of {dep_name}"
            except Exception as e:
                check.status = ValidationStatus.FAILED
                check.message = f"Unexpected error checking {dep_name}: {e}"
            
            results.append(check)
            self.validation_result.add_dependency_check(check)
        
        logger.info(f"Dependency check complete. {len([r for r in results if r.status == ValidationStatus.PASSED])} passed, {len([r for r in results if r.status == ValidationStatus.FAILED])} failed.")
        
        return results
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2
        """
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]
        
        # Pad with zeros if necessary
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        
        for i in range(len(v1_parts)):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0
    
    def validate_scripts(self) -> List[ScriptValidation]:
        """
        Validate WIF scripts.
        
        Returns:
            A list of script validation results
        """
        logger.info("Validating WIF scripts...")
        
        results = []
        
        for script_path in self.WIF_SCRIPTS:
            full_path = self.base_path / script_path
            logger.debug(f"Validating script: {full_path}")
            
            validation = ScriptValidation(script_path=script_path)
            
            # Check if script exists
            if not full_path.exists():
                validation.status = ValidationStatus.FAILED
                validation.issues.append(f"Script {script_path} does not exist")
                validation.message = f"Script {script_path} does not exist"
                results.append(validation)
                self.validation_result.add_script_validation(validation)
                continue
            
            # Check if script is executable
            if not os.access(full_path, os.X_OK):
                validation.issues.append(f"Script {script_path} is not executable")
            
            # Check for common issues in shell scripts
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for shebang
                if not content.startswith("#!/bin/bash") and not content.startswith("#!/usr/bin/env bash"):
                    validation.issues.append(f"Script {script_path} does not have a proper shebang")
                
                # Check for set -e (exit on error)
                if "set -e" not in content:
                    validation.issues.append(f"Script {script_path} does not have 'set -e' to exit on error")
                
                # Check for hardcoded paths
                if re.search(r"\/(?:home|workspaces)\/[^\/]+\/", content):
                    validation.issues.append(f"Script {script_path} contains hardcoded paths")
                
                # Check for proper error handling
                if "trap" not in content and script_path != "verify_wif_setup.sh":
                    validation.issues.append(f"Script {script_path} does not have trap handlers for cleanup")
                
                # Validate script with shellcheck if available
                if shutil.which("shellcheck"):
                    try:
                        subprocess.check_output(["shellcheck", "-x", str(full_path)], stderr=subprocess.STDOUT, text=True)
                    except subprocess.CalledProcessError as e:
                        validation.issues.append(f"Shellcheck found issues in {script_path}:\n{e.output}")
            except Exception as e:
                validation.issues.append(f"Error validating script {script_path}: {e}")
            
            # Set status based on issues
            if validation.issues:
                validation.status = ValidationStatus.FAILED
                validation.message = f"Script {script_path} has {len(validation.issues)} issues"
            else:
                validation.status = ValidationStatus.PASSED
                validation.message = f"Script {script_path} passed validation"
            
            results.append(validation)
            self.validation_result.add_script_validation(validation)
        
        logger.info(f"Script validation complete. {len([r for r in results if r.status == ValidationStatus.PASSED])} passed, {len([r for r in results if r.status == ValidationStatus.FAILED])} failed.")
        
        return results
    
    def validate_workflows(self) -> List[WorkflowValidation]:
        """
        Validate GitHub Actions workflow templates.
        
        Returns:
            A list of workflow validation results
        """
        logger.info("Validating GitHub Actions workflows...")
        
        results = []
        
        for workflow_path in self.WIF_WORKFLOWS:
            full_path = self.base_path / workflow_path
            logger.debug(f"Validating workflow: {full_path}")
            
            validation = WorkflowValidation(workflow_path=workflow_path)
            
            # Check if workflow exists
            if not full_path.exists():
                validation.status = ValidationStatus.FAILED
                validation.issues.append(f"Workflow {workflow_path} does not exist")
                validation.message = f"Workflow {workflow_path} does not exist"
                results.append(validation)
                self.validation_result.add_workflow_validation(validation)
                continue
            
            # Check for common issues in GitHub Actions workflows
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for required permissions
                if "permissions:" not in content or "id-token: write" not in content:
                    validation.issues.append(f"Workflow {workflow_path} does not have required permissions for WIF")
                
                # Check for WIF authentication
                if "google-github-actions/auth" not in content:
                    validation.issues.append(f"Workflow {workflow_path} does not use google-github-actions/auth for WIF")
                
                # Check for required secrets
                required_secrets = ["GCP_PROJECT_ID", "GCP_REGION", "GCP_WORKLOAD_IDENTITY_PROVIDER", "GCP_SERVICE_ACCOUNT"]
                for secret in required_secrets:
                    if f"secrets.{secret}" not in content:
                        validation.issues.append(f"Workflow {workflow_path} does not use required secret: {secret}")
                
                # Check for required GitHub Actions
                for action, version in self.REQUIRED_GH_ACTIONS.items():
                    if action not in content:
                        validation.issues.append(f"Workflow {workflow_path} does not use required action: {action}")
                    elif version not in content:
                        validation.issues.append(f"Workflow {workflow_path} does not use required version {version} of action: {action}")
                
                # Check for environment support
                if "environment:" not in content:
                    validation.issues.append(f"Workflow {workflow_path} does not support different environments")
                
                # Check for proper error handling
                if "continue-on-error:" not in content:
                    validation.issues.append(f"Workflow {workflow_path} does not have proper error handling")
                
                # Validate workflow with actionlint if available
                if shutil.which("actionlint"):
                    try:
                        subprocess.check_output(["actionlint", str(full_path)], stderr=subprocess.STDOUT, text=True)
                    except subprocess.CalledProcessError as e:
                        validation.issues.append(f"Actionlint found issues in {workflow_path}:\n{e.output}")
            except Exception as e:
                validation.issues.append(f"Error validating workflow {workflow_path}: {e}")
            
            # Set status based on issues
            if validation.issues:
                validation.status = ValidationStatus.FAILED
                validation.message = f"Workflow {workflow_path} has {len(validation.issues)} issues"
            else:
                validation.status = ValidationStatus.PASSED
                validation.message = f"Workflow {workflow_path} passed validation"
            
            results.append(validation)
            self.validation_result.add_workflow_validation(validation)
        
        logger.info(f"Workflow validation complete. {len([r for r in results if r.status == ValidationStatus.PASSED])} passed, {len([r for r in results if r.status == ValidationStatus.FAILED])} failed.")
        
        return results
    
    def test_setup_in_sandbox(self) -> Dict[str, Any]:
        """
        Test WIF setup in a sandbox environment.
        
        Returns:
            A dictionary with test results
        """
        logger.info("Testing WIF setup in sandbox environment...")
        
        results = {
            "status": ValidationStatus.SKIPPED.value,
            "message": "Sandbox testing is not implemented yet",
            "details": {},
        }
        
        # This would normally create a temporary directory, copy the scripts,
        # and run them in a controlled environment with mock GCP and GitHub APIs.
        # For now, we'll just return a placeholder result.
        
        logger.info("Sandbox testing skipped.")
        
        self.validation_result.test_results = results
        
        return results
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a detailed report of the validation results.
        
        Args:
            output_path: Optional path to write the report to
            
        Returns:
            The report as a string
        """
        logger.info("Generating report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "overall_status": "passed" if not self.validation_result.has_failures() else "failed",
            "dependency_checks": [
                {
                    "name": check.name,
                    "required_version": check.required_version,
                    "actual_version": check.actual_version,
                    "status": check.status.value,
                    "message": check.message,
                }
                for check in self.validation_result.dependency_checks
            ],
            "script_validations": [
                {
                    "script_path": validation.script_path,
                    "status": validation.status.value,
                    "issues": validation.issues,
                    "message": validation.message,
                }
                for validation in self.validation_result.script_validations
            ],
            "workflow_validations": [
                {
                    "workflow_path": validation.workflow_path,
                    "status": validation.status.value,
                    "issues": validation.issues,
                    "message": validation.message,
                }
                for validation in self.validation_result.workflow_validations
            ],
            "test_results": self.validation_result.test_results,
        }
        
        report_json = json.dumps(report, indent=2)
        
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report_json)
                logger.info(f"Report written to: {output_path}")
            except Exception as e:
                logger.error(f"Error writing report to {output_path}: {e}")
        
        return report_json
    
    def generate_markdown_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a detailed markdown report of the validation results.
        
        Args:
            output_path: Optional path to write the report to
            
        Returns:
            The report as a markdown string
        """
        logger.info("Generating markdown report...")
        
        # Build the markdown report
        report = [
            "# WIF Dependency Validation Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- Base Path: `{self.base_path}`",
            f"- Overall Status: **{'PASSED' if not self.validation_result.has_failures() else 'FAILED'}**",
            f"- Dependency Checks: {len([c for c in self.validation_result.dependency_checks if c.status == ValidationStatus.PASSED])} passed, {len(self.validation_result.get_failed_checks())} failed",
            f"- Script Validations: {len([v for v in self.validation_result.script_validations if v.status == ValidationStatus.PASSED])} passed, {len(self.validation_result.get_failed_script_validations())} failed",
            f"- Workflow Validations: {len([v for v in self.validation_result.workflow_validations if v.status == ValidationStatus.PASSED])} passed, {len(self.validation_result.get_failed_workflow_validations())} failed",
            "",
            "## Dependency Checks",
            "",
        ]
        
        # Add dependency checks
        for check in self.validation_result.dependency_checks:
            status_icon = "✅" if check.status == ValidationStatus.PASSED else "❌" if check.status == ValidationStatus.FAILED else "⚠️"
            report.append(f"### {status_icon} {check.name}")
            report.append("")
            report.append(f"- Required Version: {check.required_version}")
            report.append(f"- Actual Version: {check.actual_version or 'Unknown'}")
            report.append(f"- Status: {check.status.value}")
            report.append(f"- Message: {check.message}")
            report.append("")
        
        # Add script validations
        report.append("## Script Validations")
        report.append("")
        
        for validation in self.validation_result.script_validations:
            status_icon = "✅" if validation.status == ValidationStatus.PASSED else "❌" if validation.status == ValidationStatus.FAILED else "⚠️"
            report.append(f"### {status_icon} {validation.script_path}")
            report.append("")
            report.append(f"- Status: {validation.status.value}")
            report.append(f"- Message: {validation.message}")
            
            if validation.issues:
                report.append("- Issues:")
                for issue in validation.issues:
                    report.append(f"  - {issue}")
            
            report.append("")
        
        # Add workflow validations
        report.append("## Workflow Validations")
        report.append("")
        
        for validation in self.validation_result.workflow_validations:
            status_icon = "✅" if validation.status == ValidationStatus.PASSED else "❌" if validation.status == ValidationStatus.FAILED else "⚠️"
            report.append(f"### {status_icon} {validation.workflow_path}")
            report.append("")
            report.append(f"- Status: {validation.status.value}")
            report.append(f"- Message: {validation.message}")
            
            if validation.issues:
                report.append("- Issues:")
                for issue in validation.issues:
                    report.append(f"  - {issue}")
            
            report.append("")
        
        # Add test results
        report.append("## Test Results")
        report.append("")
        
        if self.validation_result.test_results:
            report.append(f"- Status: {self.validation_result.test_results.get('status', 'unknown')}")
            report.append(f"- Message: {self.validation_result.test_results.get('message', 'No message')}")
            
            details = self.validation_result.test_results.get("details", {})
            if details:
                report.append("- Details:")
                for key, value in details.items():
                    report.append(f"  - {key}: {value}")
        else:
            report.append("No test results available.")
        
        report.append("")
        
        # Add recommendations
        report.append("## Recommendations")
        report.append("")
        
        if self.validation_result.has_failures():
            report.append("Based on the validation results, the following actions are recommended:")
            report.append("")
            
            if self.validation_result.get_failed_checks():
                report.append("### Dependency Issues")
                report.append("")
                for check in self.validation_result.get_failed_checks():
                    report.append(f"- {check.message}")
                report.append("")
            
            if self.validation_result.get_failed_script_validations():
                report.append("### Script Issues")
                report.append("")
                for validation in self.validation_result.get_failed_script_validations():
                    for issue in validation.issues:
                        report.append(f"- {issue}")
                report.append("")
            
            if self.validation_result.get_failed_workflow_validations():
                report.append("### Workflow Issues")
                report.append("")
                for validation in self.validation_result.get_failed_workflow_validations():
                    for issue in validation.issues:
                        report.append(f"- {issue}")
                report.append("")
        else:
            report.append("All validations passed! No actions required.")
        
        # Join the report lines
        report_md = "\n".join(report)
        
        # Write to file if output path is provided
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report_md)
                logger.info(f"Markdown report written to: {output_path}")
            except Exception as e:
                logger.error(f"Error writing markdown report to {output_path}: {e}")
        
        return report_md


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate dependencies and test the WIF implementation."
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check for required dependencies",
    )
    
    parser.add_argument(
        "--validate-scripts",
        action="store_true",
        help="Validate WIF scripts",
    )
    
    parser.add_argument(
        "--validate-workflow",
        action="store_true",
        help="Validate GitHub Actions workflow",
    )
    
    parser.add_argument(
        "--test-setup",
        action="store_true",
        help="Test WIF setup in a sandbox environment",
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Perform all validations",
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a detailed report",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Path to write the report to",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output during processing",
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create validator
    validator = WIFDependencyValidator(
        verbose=args.verbose,
    )
    
    # Perform validations
    if args.all or args.check_deps:
        validator.check_dependencies()
    
    if args.all or args.validate_scripts:
        validator.validate_scripts()
    
    if args.all or args.validate_workflow:
        validator.validate_workflows()
    
    if args.all or args.test_setup:
        validator.test_setup_in_sandbox()
    
    # Generate report if requested
    if args.report or args.output:
        output_path = args.output
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = f"wif_validation_report_{timestamp}.md"
        
        validator.generate_markdown_report(output_path)
    
    # Return non-zero exit code if there are failures
    return 1 if validator.validation_result.has_failures() else 0


if __name__ == "__main__":
    sys.exit(main())