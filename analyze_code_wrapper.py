#!/usr/bin/env python3
"""
Gemini code analysis wrapper for pre-commit hooks.

This script sends Python files to Google's Gemini 1.5 Pro API for code analysis,
providing immediate feedback before commit. Utilizes Gemini 1.5 Pro's large token
context window to analyze files of any size.
"""

import argparse
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Import Google Cloud libraries with proper error handling
word",
            "message": "Check for hardcoded passwords",
            "severity": "moderate",
        },
        {
            "pattern": "api_key",
            "message": "Check for hardcoded API keys",
            "severity": "moderate",
        },
        {
            "pattern": "SQL",
            "message": "Check for potential SQL injection vulnerability",
            "severity": "high",
        },
        {
            "pattern": "shell=True",
            "message": "Potential command injection with shell=True",
            "severity": "critical",
        },
    ]

    # Scan each file
    for file_path, content in files_content.items():
        lines = content.split("\n")
        for i, line in enumerate(lines):
            for pattern in security_patterns:
                if pattern["pattern"].lower() in line.lower():
                    security_issues.append(
                        {
                            "file": file_path,
                            "line": i + 1,
                            "code": line.strip(),
                            "message": pattern["message"],
                            "severity": pattern["severity"],
                        }
                    )

    return security_issues

def main():
    """Main function to analyze code with Gemini."""
    parser = argparse.ArgumentParser(description="Analyze code with Gemini 1.5 Pro (large file support)")
    parser.add_argument(
        "--extensions",
        default=".py,.js,.ts",
        help="Comma-separated list of file extensions to analyze",
    )
    parser.add_argument("files", nargs="*", help="List of files to analyze")
    parser.add_argument(
        "--file-list",
        help="Explicitly provide a comma-separated list of files to analyze",
    )
    args = parser.parse_args()

    # Get file extensions to analyze
    extensions = args.extensions.split(",")

    # Get files to analyze - from args, file list, or git staging
    if args.files:
        staged_files = args.files
    elif args.file_list:
        staged_files = args.file_list.split(",")
    else:
        staged_files = get_staged_files(extensions)

    if not staged_files or staged_files == [""]:
        print("No matching files to analyze.")
        return 0

    print("Running Gemini 1.5 Pro code analysis on files...")
    print(f"Files: {','.join(staged_files)}")

    # Read file contents - large file support with Gemini 1.5 Pro
    files_content = {}
    for file_path in staged_files:
        content = read_file_content(file_path)
        if content:
            file_size = len(content.split("\n"))
            print(f"Reading {file_path} ({file_size} lines)")
            files_content[file_path] = content

    if not files_content:
        print("No valid files to analyze.")
        return 1

    try:
        # Analyze code with Gemini 1.5 Pro's extended context window
        results = analyze_code_with_gemini(files_content)

        # Print analysis results
        print("\n===== Gemini 1.5 Pro Code Analysis =====\n")
        print(results["analysis"])
        print("\n=========================================\n")

        # Print security issues
        if results.get("security_issues"):
            print("\n===== Security Issues Found =====\n")
            for issue in results["security_issues"]:
                print(f"{issue['severity'].upper()} in {issue['file']} (line {issue['line']})")
                print(f"  Message: {issue['message']}")
                print(f"  Code: {issue['code']}\n")
            print("================================\n")

        # If critical issues are found, exit with error
        if results.get("has_critical_issues"):
            print("Critical security issues found in your code!")
            print("Please fix the issues before committing or use 'git commit --no-verify' to bypass this check.")
            return 1

        # Handle non-critical issues in pre-commit mode (just warn, don't block)
        if results.get("security_issues"):
            print("Non-critical security issues found. Proceeding with commit.")

        return 0

    except Exception as e:
        print(f"Error during code analysis: {str(e)}")
        print("You can still commit, but consider fixing the analysis script.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
