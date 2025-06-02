#!/usr/bin/env python3
"""
GitHub Secrets Analyzer and Standardizer

This script analyzes GitHub workflow files for secret usage patterns, validates naming
conventions, and provides recommendations for standardization to ensure consistent
use of GitHub organization-level secrets.

Usage:
    python scripts/update_github_secrets.py [--fix] [--workflow FILE] [--report-file FILE]

Options:
    --fix                Apply recommended changes to workflow files
    --workflow FILE      Path to workflow file (default: .github/workflows/deploy.yaml)
    --report-file FILE   Path to output report file (default: secret_analysis_report.md)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import yaml


# Constants
ORG_SECRET_PREFIX = "ORG_"
GITHUB_SECRET_PATTERN = re.compile(r"secrets\.([A-Za-z0-9_]+)")
ENV_SECRET_PATTERN = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")
PROD_SUFFIX_PATTERN = re.compile(r"(.+)_PROD$")


class SecretAnalyzer:
    """Analyzes GitHub workflow files for secret usage patterns."""

    def __init__(self, workflow_path: str):
        self.workflow_path = workflow_path
        self.workflow_content = ""
        self.secrets: Set[str] = set()
        self.env_vars_with_secrets: Dict[str, List[str]] = {}
        self.inconsistencies: List[Dict] = []
        self.recommended_mappings: Dict[str, str] = {}

    def load_workflow(self) -> bool:
        """Load the workflow file content."""
        try:
            with open(self.workflow_path, "r") as f:
                self.workflow_content = f.read()
            return True
        except Exception as e:
            print(f"Error loading workflow file: {e}", file=sys.stderr)
            return False

    def parse_yaml(self) -> Optional[dict]:
        """Parse the workflow YAML content."""
        try:
            return yaml.safe_load(self.workflow_content)
        except Exception as e:
            print(f"Error parsing YAML: {e}", file=sys.stderr)
            return None

    def extract_secrets(self):
        """Extract all secrets referenced in the workflow file."""
        # Direct secret references
        direct_secrets = GITHUB_SECRET_PATTERN.findall(self.workflow_content)
        # Template expressions with secrets
        template_secrets = ENV_SECRET_PATTERN.findall(self.workflow_content)

        self.secrets = set(direct_secrets + template_secrets)

        # Find environment variables that use secrets
        yaml_content = self.parse_yaml()
        if yaml_content and "jobs" in yaml_content:
            for job_id, job_data in yaml_content["jobs"].items():
                if "env" in job_data:
                    for env_var, env_value in job_data["env"].items():
                        if isinstance(env_value, str) and "secrets." in env_value:
                            matches = ENV_SECRET_PATTERN.findall(env_value)
                            if matches:
                                if env_var not in self.env_vars_with_secrets:
                                    self.env_vars_with_secrets[env_var] = []
                                self.env_vars_with_secrets[env_var].extend(matches)

    def analyze_naming_conventions(self):
        """Analyze if secrets follow naming conventions."""
        for secret in self.secrets:
            issues = []

            # Check if secret follows org-level naming convention
            if not secret.startswith(ORG_SECRET_PREFIX):
                issues.append(f"Doesn't use '{ORG_SECRET_PREFIX}' prefix for organization-level secret")

                # Generate recommended name
                recommended_name = f"{ORG_SECRET_PREFIX}{secret}"

                # Check for _PROD suffix pattern
                prod_match = PROD_SUFFIX_PATTERN.match(secret)
                if prod_match:
                    base_name = prod_match.group(1)
                    issues.append(f"Uses _PROD suffix instead of environment-specific config")
                    recommended_name = f"{ORG_SECRET_PREFIX}{base_name}"

                self.recommended_mappings[secret] = recommended_name

            # Check for other naming issues
            if "_" not in secret:
                issues.append("Missing word separator (_)")

            if issues:
                self.inconsistencies.append(
                    {"secret": secret, "issues": issues, "recommended": self.recommended_mappings.get(secret, secret)}
                )

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a report of findings and recommendations."""
        report = "# GitHub Secrets Analysis Report\n\n"

        # Summary
        report += "## Summary\n\n"
        report += f"- **Workflow File**: `{self.workflow_path}`\n"
        report += f"- **Total Secrets Found**: {len(self.secrets)}\n"
        report += f"- **Inconsistencies Found**: {len(self.inconsistencies)}\n\n"

        # Secrets Found
        report += "## Secrets Found\n\n"
        report += "| Secret Name | Used In Environment Variables |\n"
        report += "|------------|------------------------------|\n"
        for secret in sorted(self.secrets):
            env_vars = []
            for env_var, secrets_list in self.env_vars_with_secrets.items():
                if secret in secrets_list:
                    env_vars.append(env_var)
            env_vars_str = ", ".join(env_vars) if env_vars else "Direct reference only"
            report += f"| `{secret}` | {env_vars_str} |\n"
        report += "\n"

        # Inconsistencies
        if self.inconsistencies:
            report += "## Naming Inconsistencies\n\n"
            report += "| Secret Name | Issues | Recommended Name |\n"
            report += "|------------|--------|------------------|\n"
            for item in self.inconsistencies:
                issues_str = "<br>".join(item["issues"])
                report += f"| `{item['secret']}` | {issues_str} | `{item['recommended']}` |\n"
            report += "\n"

        # Recommendations
        report += "## Recommendations\n\n"

        if self.recommended_mappings:
            report += "### Secret Mapping\n\n"
            report += "Replace the following secrets with organization-level secrets:\n\n"
            report += "```yaml\n"
            for old_name, new_name in self.recommended_mappings.items():
                report += f"{old_name}: {new_name}\n"
            report += "```\n\n"

        report += "### Best Practices\n\n"
        report += (
            "1. **Use Organization Secrets**: Store shared secrets at the organization level with the `ORG_` prefix\n"
        )
        report += "2. **Environment-Specific Configuration**: Use Pulumi environment-specific configuration instead of `_PROD` suffixes\n"
        report += "3. **Consistent Naming**: Use snake_case with meaningful prefixes for all secrets\n"
        report += "4. **Secret Rotation**: Implement a process for regular secret rotation\n\n"

        report += "### Implementation Plan\n\n"
        report += "1. Create all recommended organization secrets in GitHub\n"
        report += "2. Update Pulumi configuration to use the new secret names\n"
        report += "3. Update workflow files to reference the new secret names\n"
        report += "4. Test the changes in a development environment\n"
        report += "5. Remove the old secrets after confirming everything works\n"

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"Report written to {output_file}")

        return report

    def fix_workflow(self) -> Tuple[str, int]:
        """Apply recommended changes to the workflow file."""
        updated_content = self.workflow_content
        replacements = 0

        # Replace direct references to secrets
        for old_name, new_name in self.recommended_mappings.items():
            pattern = f"secrets.{old_name}"
            replacement = f"secrets.{new_name}"
            new_content = updated_content.replace(pattern, replacement)
            if new_content != updated_content:
                replacements += updated_content.count(pattern)
                updated_content = new_content

        return updated_content, replacements

    def run_analysis(self):
        """Run the complete analysis process."""
        if not self.load_workflow():
            return False

        self.extract_secrets()
        self.analyze_naming_conventions()
        return True


def main():
    parser = argparse.ArgumentParser(description="Analyze GitHub workflow files for secret usage patterns")
    parser.add_argument("--fix", action="store_true", help="Apply recommended changes to workflow files")
    parser.add_argument("--workflow", default=".github/workflows/deploy.yaml", help="Path to workflow file")
    parser.add_argument("--report-file", default="secret_analysis_report.md", help="Path to output report file")
    args = parser.parse_args()

    # Check if workflow file exists
    if not os.path.exists(args.workflow):
        print(f"Error: Workflow file '{args.workflow}' not found.", file=sys.stderr)
        return 1

    # Run analysis
    analyzer = SecretAnalyzer(args.workflow)
    if not analyzer.run_analysis():
        return 1

    # Generate and print report
    report = analyzer.generate_report(args.report_file)

    # Fix workflow if requested
    if args.fix and analyzer.recommended_mappings:
        updated_content, replacements = analyzer.fix_workflow()
        if replacements > 0:
            backup_path = f"{args.workflow}.bak"
            print(f"Creating backup of original workflow at {backup_path}")
            with open(backup_path, "w") as f:
                f.write(analyzer.workflow_content)

            print(f"Updating workflow file with {replacements} replacements")
            with open(args.workflow, "w") as f:
                f.write(updated_content)

            print("Workflow file updated successfully")
        else:
            print("No changes needed in workflow file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
