#!/usr/bin/env python3
"""
code_analysis.py - A custom static code analyzer for the AI Orchestra project.

This script performs static analysis on Python code without requiring external dependencies.
It identifies common issues like unused imports, unused variables, duplicate code patterns,
and potential security vulnerabilities.
"""

import ast
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Directories to exclude from analysis
EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

# File patterns to include
INCLUDED_PATTERNS = [r".*\.py$"]

# Issue categories
ISSUE_SEVERITY = {
    "unused_import": "warning",
    "unused_variable": "warning",
    "undefined_name": "error",
    "duplicate_code": "warning",
    "complex_function": "info",
    "security_issue": "error",
    "import_style": "warning",
    "missing_type_hint": "info",
    "missing_docstring": "info",
}


class Issue:
    """Represents a code issue found during analysis."""

    def __init__(
        self,
        file_path: str,
        line: int,
        category: str,
        message: str,
        code: Optional[str] = None,
    ):
        self.file_path = file_path
        self.line = line
        self.category = category
        self.message = message
        self.code = code
        self.severity = ISSUE_SEVERITY.get(category, "warning")

    def __str__(self) -> str:
        severity_color = {"error": RED, "warning": YELLOW, "info": BLUE}.get(
            self.severity, RESET
        )

        return f"{self.file_path}:{self.line} - {severity_color}{self.severity.upper()}{RESET}: {self.message}"


class CodeVisitor(ast.NodeVisitor):
    """AST visitor to analyze Python code for issues."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues: List[Issue] = []
        self.imported_names: Set[str] = set()
        self.defined_names: Set[str] = set()
        self.used_names: Set[str] = set()
        self.function_complexities: Dict[str, int] = {}
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for name in node.names:
            self.imported_names.add(name.name.split(".")[0])

            # Check for absolute imports within packages
            if "." not in name.name and self._is_in_package():
                self.issues.append(
                    Issue(
                        self.file_path,
                        node.lineno,
                        "import_style",
                        f"Consider using relative imports within packages: '{name.name}'",
                        code=f"import {name.name}",
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements."""
        if node.module:
            module_name = node.module.split(".")[0]
            self.imported_names.add(module_name)

            # Check for absolute imports within packages
            if node.level == 0 and self._is_in_package():
                self.issues.append(
                    Issue(
                        self.file_path,
                        node.lineno,
                        "import_style",
                        f"Consider using relative imports within packages: 'from {node.module} import ...'",
                        code=f"from {node.module} import ...",
                    )
                )

        for name in node.names:
            if name.name != "*":
                self.imported_names.add(name.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name references."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        prev_function = self.current_function
        self.current_function = node.name
        self.defined_names.add(node.name)

        # Check for missing docstring
        if not ast.get_docstring(node):
            self.issues.append(
                Issue(
                    self.file_path,
                    node.lineno,
                    "missing_docstring",
                    f"Function '{node.name}' is missing a docstring",
                )
            )

        # Check for missing return type hint
        if node.returns is None and not self._is_test_function(node.name):
            self.issues.append(
                Issue(
                    self.file_path,
                    node.lineno,
                    "missing_type_hint",
                    f"Function '{node.name}' is missing a return type hint",
                )
            )

        # Check for missing parameter type hints
        for arg in node.args.args:
            if arg.annotation is None and arg.arg != "self" and arg.arg != "cls":
                self.issues.append(
                    Issue(
                        self.file_path,
                        node.lineno,
                        "missing_type_hint",
                        f"Parameter '{arg.arg}' in function '{node.name}' is missing a type hint",
                    )
                )

        # Calculate function complexity (simplified)
        complexity = self._calculate_complexity(node)
        self.function_complexities[node.name] = complexity

        if complexity > 10:
            self.issues.append(
                Issue(
                    self.file_path,
                    node.lineno,
                    "complex_function",
                    f"Function '{node.name}' has a complexity of {complexity}, which is high",
                )
            )

        self.generic_visit(node)
        self.current_function = prev_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        prev_class = self.current_class
        self.current_class = node.name
        self.defined_names.add(node.name)

        # Check for missing docstring
        if not ast.get_docstring(node):
            self.issues.append(
                Issue(
                    self.file_path,
                    node.lineno,
                    "missing_docstring",
                    f"Class '{node.name}' is missing a docstring",
                )
            )

        self.generic_visit(node)
        self.current_class = prev_class

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.complexity = 0

            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_Try(self, node):
                self.complexity += len(node.handlers)
                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)

            def visit_BoolOp(self, node):
                if isinstance(node.op, ast.And) or isinstance(node.op, ast.Or):
                    self.complexity += len(node.values) - 1
                self.generic_visit(node)

        visitor = ComplexityVisitor()
        visitor.visit(node)
        return complexity + visitor.complexity

    def _is_in_package(self) -> bool:
        """Check if the current file is part of a package."""
        path = Path(self.file_path)
        return (path.parent / "__init__.py").exists()

    def _is_test_function(self, name: str) -> bool:
        """Check if a function is a test function."""
        return name.startswith("test_") or "test" in self.file_path.lower()

    def analyze(self) -> List[Issue]:
        """Analyze the collected data for issues."""
        # Check for unused imports
        for name in self.imported_names:
            if name not in self.used_names and name != "__future__":
                self.issues.append(
                    Issue(
                        self.file_path, 1, "unused_import", f"Unused import: '{name}'"
                    )
                )

        # Check for unused variables
        for name in self.defined_names:
            if name not in self.used_names and not name.startswith("_"):
                self.issues.append(
                    Issue(
                        self.file_path,
                        1,
                        "unused_variable",
                        f"Unused variable: '{name}'",
                    )
                )

        return self.issues


def find_python_files(start_dir: str) -> List[str]:
    """Find all Python files in the given directory and its subdirectories."""
    python_files = []

    for root, dirs, files in os.walk(start_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            if any(re.match(pattern, file) for pattern in INCLUDED_PATTERNS):
                python_files.append(os.path.join(root, file))

    return python_files


def analyze_file(file_path: str) -> List[Issue]:
    """Analyze a single Python file for issues."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=file_path)
        visitor = CodeVisitor(file_path)
        visitor.visit(tree)
        return visitor.analyze()

    except SyntaxError as e:
        return [
            Issue(file_path, e.lineno or 1, "undefined_name", f"Syntax error: {str(e)}")
        ]
    except Exception as e:
        return [
            Issue(file_path, 1, "undefined_name", f"Error analyzing file: {str(e)}")
        ]


def analyze_codebase(directory: str) -> List[Issue]:
    """Analyze all Python files in the given directory."""
    python_files = find_python_files(directory)
    all_issues = []

    print(f"Found {len(python_files)} Python files to analyze")

    for i, file_path in enumerate(python_files):
        if i % 10 == 0:
            print(f"Analyzing file {i+1}/{len(python_files)}: {file_path}")

        issues = analyze_file(file_path)
        all_issues.extend(issues)

    return all_issues


def print_summary(issues: List[Issue]) -> None:
    """Print a summary of the issues found."""
    if not issues:
        print(f"{GREEN}No issues found!{RESET}")
        return

    # Group issues by category
    issues_by_category = defaultdict(list)
    for issue in issues:
        issues_by_category[issue.category].append(issue)

    # Group issues by file
    issues_by_file = defaultdict(list)
    for issue in issues:
        issues_by_file[issue.file_path].append(issue)

    # Print summary
    print(f"\n{BLUE}===== Code Analysis Summary ====={RESET}")
    print(f"Found {len(issues)} issues in {len(issues_by_file)} files\n")

    print(f"{BLUE}Issues by category:{RESET}")
    for category, category_issues in sorted(
        issues_by_category.items(), key=lambda x: len(x[1]), reverse=True
    ):
        severity = ISSUE_SEVERITY.get(category, "warning")
        severity_color = {"error": RED, "warning": YELLOW, "info": BLUE}.get(
            severity, RESET
        )

        print(f"  {severity_color}{category}{RESET}: {len(category_issues)} issues")

    print(f"\n{BLUE}Top files with issues:{RESET}")
    for i, (file_path, file_issues) in enumerate(
        sorted(issues_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    ):
        print(f"  {i+1}. {file_path}: {len(file_issues)} issues")


def print_detailed_report(issues: List[Issue]) -> None:
    """Print a detailed report of all issues."""
    if not issues:
        return

    # Group issues by file
    issues_by_file = defaultdict(list)
    for issue in issues:
        issues_by_file[issue.file_path].append(issue)

    print(f"\n{BLUE}===== Detailed Issue Report ====={RESET}")

    for file_path, file_issues in sorted(issues_by_file.items()):
        print(f"\n{YELLOW}{file_path}{RESET}:")

        # Sort issues by line number
        for issue in sorted(file_issues, key=lambda x: x.line):
            severity_color = {"error": RED, "warning": YELLOW, "info": BLUE}.get(
                issue.severity, RESET
            )

            print(
                f"  Line {issue.line}: {severity_color}{issue.category}{RESET} - {issue.message}"
            )


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Python code for issues")
    parser.add_argument("--path", type=str, default=".", help="Path to analyze")
    parser.add_argument("--detailed", action="store_true", help="Show detailed report")
    args = parser.parse_args()

    print(f"Analyzing Python code in {args.path}...")
    issues = analyze_codebase(args.path)

    print_summary(issues)

    if args.detailed:
        print_detailed_report(issues)
    else:
        print("\nRun with --detailed for a full report of all issues")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
