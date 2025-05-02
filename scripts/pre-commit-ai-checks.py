#!/usr/bin/env python3
"""
Pre-commit hook for AI code quality checks in the Orchestra System.

This script runs AI-specific code quality checks on staged Python files before allowing a commit.
It uses the ai_code_quality module to detect issues like hallucinated code patterns, prompt injection
vectors, RAG context window issues, and model version drift. If issues are found, it warns the developer
and suggests human review, but does not block the commit to maintain development velocity.
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Tuple

# Ensure the packages directory is in the Python path
sys.path.append(str(Path(__file__).parent.parent / "packages" / "tools" / "src"))

try:
    from ai_code_quality import run_ai_code_quality_checks
except ImportError:
    print("Error: Could not import ai_code_quality module. Ensure the packages/tools/src directory is accessible.")
    sys.exit(1)

def get_staged_files() -> List[str]:
    """
    Get a list of staged Python files for the current commit.
    
    Returns:
        List of file paths for staged Python files.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.splitlines()
        return [f for f in files if f.endswith('.py')]
    except subprocess.CalledProcessError as e:
        print(f"Error getting staged files: {e}")
        return []

def main() -> int:
    """
    Main function for the pre-commit hook.
    Runs AI code quality checks on staged Python files and reports any issues.
    
    Returns:
        Exit code (0 for success, 1 for issues found but commit allowed).
    """
    staged_files = get_staged_files()
    if not staged_files:
        print("No staged Python files to check.")
        return 0

    print("Running AI Code Quality Checks on staged files...")
    issues_found = False
    for file_path in staged_files:
        if not os.path.exists(file_path):
            continue  # Skip deleted files or files that no longer exist
        
        # Since run_ai_code_quality_checks expects a directory, we process individual files
        # by creating a temporary result for each file. Alternatively, we could modify
        # the function to handle single files, but for now, we'll simulate directory check.
        results = run_ai_code_quality_checks(os.path.dirname(file_path))
        
        if file_path in results:
            issues = results[file_path]
            if issues:
                issues_found = True
                print(f"\nAI Code Quality Issues in {file_path}:")
                for line_num, line_content, issue_desc in issues:
                    print(f"  Line {line_num}: {issue_desc}")
                    print(f"    {line_content}")
                print("  Suggestion: Review these issues for correctness and security before committing.")

    if issues_found:
        print("\nWARNING: AI Code Quality issues were found in staged files.")
        print("You can commit anyway, but it's recommended to review the flagged code.")
        return 0  # Return 0 to allow commit despite issues, maintaining velocity
    else:
        print("No AI code quality issues found in staged files.")
        return 0

if __name__ == "__main__":
    sys.exit(main())