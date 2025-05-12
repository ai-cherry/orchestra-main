"""
GitHub Actions Workflow Validator for AI Orchestra.

This module provides tools to validate GitHub Actions workflows for security,
reliability, and best practices, helping to identify potential issues before
they impact production.
"""

import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, List, Optional, Any

class GitHubWorkflowValidator:
    """Validates GitHub Actions workflows for security and reliability."""
    
    def __init__(self, workflow_dir: str = ".github/workflows"):
        """Initialize the workflow validator.
        
        Args:
            workflow_dir: Directory containing workflow YAML files
        """
        self.workflow_dir = Path(workflow_dir)
        self.workflows = []
        self._load_workflows()
    
    def _load_workflows(self) -> None:
        """Load all workflow YAML files for validation."""
        if not self.workflow_dir.exists():
            return
            
        for workflow_file in self.workflow_dir.glob("*.yml"):
            with open(workflow_file, "r") as f:
                try:
                    workflow = yaml.safe_load(f)
                    self.workflows.append({
                        "path": workflow_file,
                        "name": workflow.get("name", workflow_file.stem),
                        "content": workflow
                    })
                except yaml.YAMLError:
                    print(f"Error parsing workflow file: {workflow_file}")
    
    def validate_permissions(self) -> List[Dict]:
        """Validate that workflows use restricted permissions.
        
        Returns:
            List of identified permission issues
        """
        issues = []
        
        for workflow in self.workflows:
            # Check if permissions are explicitly defined
            if "permissions" not in workflow["content"]:
                issues.append({
                    "workflow": workflow["name"],
                    "file": str(workflow["path"]),
                    "issue": "No permissions specified, defaults to broad permissions",
                    "severity": "high",
                    "recommendation": "Add explicit restricted permissions"
                })
                continue
                
            permissions = workflow["content"]["permissions"]
            
            # Check if wildcard permissions are used
            if permissions == "write-all" or permissions is True:
                issues.append({
                    "workflow": workflow["name"],
                    "file": str(workflow["path"]),
                    "issue": "Overly permissive 'write-all' permissions",
                    "severity": "critical",
                    "recommendation": "Restrict to only required permissions"
                })
        
        return issues
    
    def validate_timeout_limits(self) -> List[Dict]:
        """Validate that jobs have timeout limits to prevent runaway actions.
        
        Returns:
            List of identified timeout issues
        """
        issues = []
        
        for workflow in self.workflows:
            if "jobs" not in workflow["content"]:
                continue
                
            for job_id, job in workflow["content"]["jobs"].items():
                if "timeout-minutes" not in job:
                    issues.append({
                        "workflow": workflow["name"],
                        "file": str(workflow["path"]),
                        "job": job_id,
                        "issue": "No timeout limit specified",
                        "severity": "medium",
                        "recommendation": "Add timeout-minutes to limit job duration"
                    })
        
        return issues
    
    def validate_action_versions(self) -> List[Dict]:
        """Validate that actions use pinned versions rather than floating refs.
        
        Returns:
            List of identified action version issues
        """
        issues = []
        
        for workflow in self.workflows:
            if "jobs" not in workflow["content"]:
                continue
                
            for job_id, job in workflow["content"]["jobs"].items():
                if "steps" not in job:
                    continue
                    
                for i, step in enumerate(job["steps"]):
                    if "uses" not in step:
                        continue
                        
                    action_ref = step["uses"]
                    
                    # Check for floating refs (main, master, latest)
                    if "@main" in action_ref or "@master" in action_ref:
                        issues.append({
                            "workflow": workflow["name"],
                            "file": str(workflow["path"]),
                            "job": job_id,
                            "step": i + 1,
                            "action": action_ref,
                            "issue": "Using floating ref (main/master)",
                            "severity": "high",
                            "recommendation": "Pin to specific version or commit SHA"
                        })
                    
                    # Check for major version without minor (e.g., v1)
                    elif "@v" in action_ref and len(action_ref.split("@v")[1].split(".")) < 2:
                        issues.append({
                            "workflow": workflow["name"],
                            "file": str(workflow["path"]),
                            "job": job_id,
                            "step": i + 1,
                            "action": action_ref,
                            "issue": "Using major version only",
                            "severity": "medium",
                            "recommendation": "Use more specific version (v1.2.3)"
                        })
        
        return issues
    
    def validate_secret_usage(self) -> List[Dict]:
        """Validate that secrets are not used insecurely.
        
        Returns:
            List of identified secret usage issues
        """
        issues = []
        
        for workflow in self.workflows:
            workflow_content = json.dumps(workflow["content"])
            
            # Check for secrets being logged or exposed
            if "${{ secrets." in workflow_content and "run: " in workflow_content:
                for job_id, job in workflow["content"].get("jobs", {}).items():
                    for i, step in enumerate(job.get("steps", [])):
                        if "run" not in step:
                            continue
                            
                        run_command = step["run"]
                        
                        # Look for echo commands with secrets
                        if "echo" in run_command and "${{ secrets." in run_command:
                            issues.append({
                                "workflow": workflow["name"],
                                "file": str(workflow["path"]),
                                "job": job_id,
                                "step": i + 1,
                                "issue": "Potential secret exposure via echo",
                                "severity": "critical",
                                "recommendation": "Never echo secrets in workflow steps"
                            })
        
        return issues
    
    def validate_environment_usage(self) -> List[Dict]:
        """Validate proper environment usage for deployments.
        
        Returns:
            List of identified environment usage issues
        """
        issues = []
        
        for workflow in self.workflows:
            if "jobs" not in workflow["content"]:
                continue
                
            for job_id, job in workflow["content"]["jobs"].items():
                # Check for deployment without environment
                deploy_indicators = ["deploy", "release", "publish", "push"]
                is_likely_deployment = any(indicator in job_id.lower() for indicator in deploy_indicators)
                
                if is_likely_deployment and "environment" not in job:
                    issues.append({
                        "workflow": workflow["name"],
                        "file": str(workflow["path"]),
                        "job": job_id,
                        "issue": "Deployment job without environment protection",
                        "severity": "high",
                        "recommendation": "Add environment field to enable protection rules"
                    })
        
        return issues
    
    def run_all_validations(self) -> Dict[str, List[Dict]]:
        """Run all validation checks and return comprehensive results.
        
        Returns:
            Dictionary of validation results by category
        """
        return {
            "permissions": self.validate_permissions(),
            "timeouts": self.validate_timeout_limits(),
            "action_versions": self.validate_action_versions(),
            "secret_usage": self.validate_secret_usage(),
            "environments": self.validate_environment_usage()
        }


class TestGitHubWorkflows:
    """Test suite for GitHub workflow validation."""
    
    @pytest.fixture
    def validator(self):
        return GitHubWorkflowValidator()
    
    def test_workflow_permissions(self, validator):
        """Test that workflows use restricted permissions."""
        issues = validator.validate_permissions()
        
        # Assert no critical permission issues
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        assert len(critical_issues) == 0, f"Critical permission issues found: {critical_issues}"
        
        # Log lower severity issues for awareness
        if issues:
            print(f"Found {len(issues)} permission issues to address")
    
    def test_workflow_timeouts(self, validator):
        """Test that jobs have reasonable timeout limits."""
        issues = validator.validate_timeout_limits()
        assert len(issues) == 0, f"Jobs missing timeout limits: {issues}"
    
    def test_action_pinning(self, validator):
        """Test that actions use pinned versions."""
        issues = validator.validate_action_versions()
        
        # Assert no high severity version issues
        high_issues = [i for i in issues if i["severity"] == "high"]
        assert len(high_issues) == 0, f"Actions with floating refs found: {high_issues}"
    
    def test_secret_handling(self, validator):
        """Test that secrets are handled securely."""
        issues = validator.validate_secret_usage()
        assert len(issues) == 0, f"Insecure secret handling found: {issues}"
    
    def test_deployment_protection(self, validator):
        """Test that deployment jobs use environment protection."""
        issues = validator.validate_environment_usage()
        assert len(issues) == 0, f"Deployment jobs without environment protection: {issues}"


if __name__ == "__main__":
    # Simple command-line interface for validation
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate GitHub Actions workflows")
    parser.add_argument("--workflows-dir", default=".github/workflows", 
                       help="Directory containing workflow files")
    parser.add_argument("--output", default="workflow-validation-report.json",
                       help="Output file for JSON validation report")
    parser.add_argument("--fail-on-issues", action="store_true",
                       help="Exit with non-zero code if issues are found")
    
    args = parser.parse_args()
    
    validator = GitHubWorkflowValidator(args.workflows_dir)
    results = validator.run_all_validations()
    
    # Write results to file
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    
    # Count issues by severity
    issue_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for category, issues in results.items():
        for issue in issues:
            severity = issue.get("severity", "medium")
            issue_count[severity] = issue_count.get(severity, 0) + 1
    
    # Print summary
    total_issues = sum(issue_count.values())
    print(f"Found {total_issues} issues:")
    for severity, count in issue_count.items():
        if count > 0:
            print(f"  - {severity}: {count}")
    print(f"Full report written to {args.output}")
    
    # Exit with error code if issues found and fail-on-issues flag is set
    if args.fail_on_issues and total_issues > 0:
        exit(1)