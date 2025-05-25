#!/usr/bin/env python3
"""
Script to find critical linting issues across the codebase.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List

# Critical lint issues to check for
CRITICAL_ISSUES = {
    "F401": "Unused import",
    "F821": "Undefined name",
    "F841": "Unused variable",
    "E999": "SyntaxError",
    "F811": "Redefined name",
    "F601": "Dictionary key repeated",
    "F602": "Dictionary key variable repeated",
    "E711": "Comparison to None should be 'if cond is None:'",
    "E712": "Comparison to True/False should be 'if cond is True:'",
    "F541": "f-string without any placeholders",
    "F631": "Assertion test is a tuple",
    "F632": "Use ==/!= for comparing strings",
    "F633": "Using the walrus operator in an f-string expression",
}

# Complex code issues
COMPLEXITY_ISSUES = {
    "C901": "Function is too complex",
    "PLR0912": "Too many branches",
    "PLR0915": "Too many statements",
}

# File exclusions
EXCLUSIONS = [
    ".git",
    "__pycache__",
    ".venv",
    "google-cloud-sdk",
    "build",
    "dist",
]


def run_ruff(path: str, select: str, format_type: str = "text") -> str:
    """Run ruff with the specified options and return the output."""
    try:
        cmd = [
            "python",
            "-m",
            "ruff",
            "check",
            "--select",
            select,
            "--exclude",
            ",".join(EXCLUSIONS),
            "--format",
            format_type,
            path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running ruff: {e}")
        return ""


def parse_ruff_text_output(output: str) -> Dict[str, List[Dict[str, Any]]]:
    """Parse ruff text output into a structured format."""
    results = defaultdict(list)

    current_file = None
    for line in output.splitlines():
        # Check if this is a file header line
        if line and not line.startswith(" "):
            current_file = line.strip()
        elif line.strip() and current_file:
            # This is an error line
            match = re.match(r"\s+(\d+):(\d+)\s+([A-Z]\d+)\s+(.*)", line)
            if match:
                line_num, col, code, message = match.groups()
                results[current_file].append(
                    {
                        "line": int(line_num),
                        "col": int(col),
                        "code": code,
                        "message": message.strip(),
                    }
                )

    return results


def parse_ruff_json_output(output: str) -> List[Dict[str, Any]]:
    """Parse ruff JSON output into a structured format."""
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return []


def print_summary(results: Dict[str, List[Dict[str, Any]]]) -> None:
    """Print a summary of the linting issues."""
    total_issues = sum(len(issues) for issues in results.values())
    files_with_issues = len(results)

    print("\n===== Critical Linting Issues Summary =====")
    print(f"Found {total_issues} issues in {files_with_issues} files\n")

    # Count issues by type
    issue_counts = Counter()
    for issues in results.values():
        for issue in issues:
            issue_counts[issue["code"]] += 1

    # Print counts by type
    print("Issues by type:")
    for code, count in issue_counts.most_common():
        description = CRITICAL_ISSUES.get(
            code, COMPLEXITY_ISSUES.get(code, "Other issue")
        )
        print(f"  {code}: {count} issues - {description}")

    # Print files with the most issues
    print("\nTop files with issues:")
    files_by_issue_count = sorted(
        results.items(), key=lambda x: len(x[1]), reverse=True
    )
    for i, (filename, issues) in enumerate(files_by_issue_count[:10]):
        print(f"  {i+1}. {filename}: {len(issues)} issues")


def print_detailed_report(results: Dict[str, List[Dict[str, Any]]]) -> None:
    """Print a detailed report of all linting issues."""
    print("\n===== Detailed Linting Issues Report =====")

    for filename, issues in sorted(results.items()):
        print(f"\n{filename}:")

        # Group issues by line number
        issues_by_line = defaultdict(list)
        for issue in issues:
            issues_by_line[issue["line"]].append(issue)

        # Print issues by line
        for line_num in sorted(issues_by_line.keys()):
            for issue in issues_by_line[line_num]:
                code = issue["code"]
                description = CRITICAL_ISSUES.get(
                    code, COMPLEXITY_ISSUES.get(code, "Other issue")
                )
                print(f"  Line {line_num}: {code} - {description}")
                print(f"    {issue['message']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find critical linting issues across the codebase."
    )
    parser.add_argument("--path", type=str, default=".", help="Path to check")
    parser.add_argument("--detailed", action="store_true", help="Show detailed report")
    parser.add_argument(
        "--complexity-only",
        action="store_true",
        help="Only check for complexity issues",
    )
    parser.add_argument(
        "--critical-only", action="store_true", help="Only check for critical issues"
    )
    args = parser.parse_args()

    # Select issues to check
    if args.complexity_only:
        select = ",".join(COMPLEXITY_ISSUES.keys())
        issue_type = "complexity"
    elif args.critical_only:
        select = ",".join(CRITICAL_ISSUES.keys())
        issue_type = "critical"
    else:
        select = ",".join(list(CRITICAL_ISSUES.keys()) + list(COMPLEXITY_ISSUES.keys()))
        issue_type = "all"

    print(f"Checking for {issue_type} linting issues in {args.path}...")

    # Run ruff and get the output
    output = run_ruff(args.path, select)
    results = parse_ruff_text_output(output)

    # Print results
    if not results:
        print("No linting issues found!")
        return 0

    print_summary(results)

    if args.detailed:
        print_detailed_report(results)
    else:
        print("\nRun with --detailed for a full report of all issues")

    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
