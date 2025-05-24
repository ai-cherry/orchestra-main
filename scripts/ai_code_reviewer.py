#!/usr/bin/env python3
"""
AI Code Reviewer - Maintains consistency when using AI coding tools

Checks for common AI-generated anti-patterns:
- Wrong Python version features
- Duplicate functionality
- Unwanted dependencies (Docker, Poetry)
- Complex over-engineering
- Security issues (os.system)

Usage:
    python scripts/ai_code_reviewer.py --check-file somefile.py
    python scripts/ai_code_reviewer.py --check-changes  # Check git changes
    python scripts/ai_code_reviewer.py --full-scan     # Scan entire project
"""

import argparse
import ast
import logging
import os
import re
import subprocess
import sys
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AICodeReviewer:
    """Reviews code for AI-generated anti-patterns and project consistency."""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.project_root = os.getcwd()

        # Files to exclude from review (contain educational examples)
        self.excluded_files = [
            "ai_context_planner.py",
            "ai_context_coder.py",
            "ai_context_reviewer.py",
            "ai_context_debugger.py",
        ]

        # Define anti-patterns
        self.forbidden_imports = [
            "docker",
            "poetry",
            "pipenv",
            "setuptools",
            "distutils",
            "conda",
            "virtualenv",
            "tox",
            "nox",
        ]

        self.forbidden_files = [
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "tox.ini",
            "noxfile.py",
        ]

        self.python311_features = [
            r"match\s+\w+:",  # match/case statements
            r"tomllib",  # tomllib module
            r"ExceptionGroup",  # Exception groups
            r"TaskGroup",  # asyncio.TaskGroup
        ]

        self.existing_tools = {
            "config_validator": "scripts/config_validator.py",
            "health_monitor": "scripts/health_monitor.py",
            "orchestra_cli": "scripts/orchestra.py",
            "check_venv": "scripts/check_venv.py",
            "check_dependencies": "scripts/check_dependencies.py",
        }

    def check_file(self, filepath: str) -> Dict[str, List[str]]:
        """Check a single file for issues."""
        if not os.path.exists(filepath):
            return {"errors": [f"File not found: {filepath}"], "warnings": []}

        # Skip excluded files
        filename = os.path.basename(filepath)
        if filename in self.excluded_files:
            logger.info(f"Skipping excluded file: {filename} (contains educational examples)")
            return {"errors": [], "warnings": []}

        results = {"errors": [], "warnings": []}

        # Check if it's a forbidden file type
        if filename in self.forbidden_files:
            results["errors"].append(f"Forbidden file type: {filename} - We don't use Docker/Poetry!")
            return results

        # Only check Python files for code issues
        if not filepath.endswith(".py"):
            return results

        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Check for forbidden imports
            for forbidden in self.forbidden_imports:
                if re.search(f"import {forbidden}|from {forbidden}", content):
                    results["errors"].append(f"Forbidden import '{forbidden}' - We use pip/venv only!")

            # Check for Python 3.11+ features
            for feature_pattern in self.python311_features:
                if re.search(feature_pattern, content):
                    results["warnings"].append(
                        f"Python 3.11+ feature detected: {feature_pattern} - Ensure target runtime is 3.11 or newer."
                    )

            # Check for os.system usage
            if "os.system(" in content:
                results["errors"].append("Found os.system() - Use subprocess.run() instead!")

            # Check for shell=True
            if "shell=True" in content and "subprocess" in content:
                results["warnings"].append("Found shell=True - Consider using argument list instead!")

            # Parse AST for deeper analysis
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, filepath, results)
            except SyntaxError as e:
                results["errors"].append(f"Syntax error in file: {e}")

        except Exception as e:
            results["errors"].append(f"Error reading file: {e}")

        return results

    def _analyze_ast(self, tree: ast.AST, filepath: str, results: Dict[str, List[str]]) -> None:
        """Analyze AST for patterns."""
        # Check for overly complex classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for abstract base classes
                if any(base.id == "ABC" for base in node.bases if isinstance(base, ast.Name)):
                    if len([n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]) < 3:
                        results["warnings"].append(f"Simple ABC detected in {node.name} - might be over-engineered")

                # Check for multiple inheritance
                if len(node.bases) > 1:
                    results["warnings"].append(f"Multiple inheritance in {node.name} - keep it simple!")

            # Check for metaclasses
            if isinstance(node, ast.ClassDef) and node.keywords:
                if any(kw.arg == "metaclass" for kw in node.keywords):
                    results["errors"].append(f"Metaclass usage in {node.name} - too complex!")

    def check_for_duplicates(self, filepath: str) -> List[str]:
        """Check if functionality already exists in the project."""
        if not filepath.endswith(".py"):
            return []

        # Skip excluded files
        filename = os.path.basename(filepath)
        if filename in self.excluded_files:
            return []

        duplicates = []

        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Check for validator functions
            if re.search(r"def.*validat", content, re.IGNORECASE):
                duplicates.append(f"Validation functionality might duplicate {self.existing_tools['config_validator']}")

            # Check for monitoring/health functions
            if re.search(r"def.*(health|monitor|check.*service)", content, re.IGNORECASE):
                duplicates.append(f"Health/monitoring might duplicate {self.existing_tools['health_monitor']}")

            # Check for CLI tools
            if "argparse" in content or "click" in content:
                duplicates.append(f"CLI functionality might duplicate {self.existing_tools['orchestra_cli']}")

            # Check for environment checking
            if re.search(r"def.*check.*(env|venv|virtual)", content, re.IGNORECASE):
                duplicates.append(f"Environment checking might duplicate {self.existing_tools['check_venv']}")

        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")

        return duplicates

    def check_git_changes(self) -> Dict[str, Dict[str, List[str]]]:
        """Check all files changed in git."""
        try:
            # Get list of changed files
            result = subprocess.run(["git", "diff", "--name-only", "--cached", "HEAD"], capture_output=True, text=True)

            if result.returncode != 0:
                # Try unstaged changes
                result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)

            if result.returncode != 0:
                return {"error": {"errors": ["Failed to get git changes"], "warnings": []}}

            files = result.stdout.strip().split("\n")
            all_results = {}

            for filepath in files:
                if filepath and os.path.exists(filepath):
                    results = self.check_file(filepath)
                    duplicates = self.check_for_duplicates(filepath)
                    if duplicates:
                        results["warnings"].extend(duplicates)

                    if results["errors"] or results["warnings"]:
                        all_results[filepath] = results

            return all_results

        except Exception as e:
            return {"error": {"errors": [f"Git error: {e}"], "warnings": []}}

    def full_project_scan(self) -> Dict[str, Dict[str, List[str]]]:
        """Scan entire project for issues."""
        all_results = {}

        # Check for forbidden files
        for forbidden_file in self.forbidden_files:
            if os.path.exists(forbidden_file):
                all_results[forbidden_file] = {"errors": [f"Forbidden file exists: {forbidden_file}"], "warnings": []}

        # Scan Python files
        for root, dirs, files in os.walk(self.project_root):
            # Skip virtual environment
            if "venv" in root or "__pycache__" in root:
                continue

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    results = self.check_file(filepath)

                    if results["errors"] or results["warnings"]:
                        all_results[filepath] = results

        return all_results

    def generate_report(self, results: Dict[str, Dict[str, List[str]]]) -> str:
        """Generate a readable report from results."""
        if not results:
            return "✅ No issues found! Code follows project standards."

        report = ["🔍 AI Code Review Report", "=" * 50, ""]

        total_errors = sum(len(r["errors"]) for r in results.values())
        total_warnings = sum(len(r["warnings"]) for r in results.values())

        report.append(f"Found {total_errors} errors and {total_warnings} warnings in {len(results)} files\n")

        for filepath, file_results in results.items():
            report.append(f"📄 {filepath}")

            if file_results["errors"]:
                report.append("  ❌ ERRORS:")
                for error in file_results["errors"]:
                    report.append(f"    • {error}")

            if file_results["warnings"]:
                report.append("  ⚠️  WARNINGS:")
                for warning in file_results["warnings"]:
                    report.append(f"    • {warning}")

            report.append("")

        report.extend(
            [
                "📋 Quick Fixes:",
                "1. Replace Docker/Poetry with pip/venv",
                "2. Use subprocess.run() instead of os.system()",
                "3. Check existing tools in scripts/ before creating new ones",
                "4. Ensure Python 3.11+ features are supported in deployment environments",
                "5. Simplify over-engineered patterns",
            ]
        )

        return "\n".join(report)


def main():
    """Main entry point for AI code reviewer."""
    parser = argparse.ArgumentParser(description="AI Code Reviewer - Maintain project consistency")

    parser.add_argument("--check-file", help="Check a specific file")
    parser.add_argument("--check-changes", action="store_true", help="Check git changes")
    parser.add_argument("--full-scan", action="store_true", help="Scan entire project")
    parser.add_argument("--output", help="Output report to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    reviewer = AICodeReviewer()
    results = {}

    if args.check_file:
        results = {args.check_file: reviewer.check_file(args.check_file)}
        duplicates = reviewer.check_for_duplicates(args.check_file)
        if duplicates:
            results[args.check_file]["warnings"].extend(duplicates)

    elif args.check_changes:
        results = reviewer.check_git_changes()

    elif args.full_scan:
        results = reviewer.full_project_scan()

    else:
        parser.print_help()
        return 1

    # Generate report
    report = reviewer.generate_report(results)

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)

    # Return non-zero if errors found
    total_errors = sum(len(r.get("errors", [])) for r in results.values())
    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
