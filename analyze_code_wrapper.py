#!/usr/bin/env python3
"""
Gemini code analysis wrapper for pre-commit hooks.

This script sends Python files to Google's Gemini 2.5 Pro API for code analysis,
providing immediate feedback before commit. Utilizes Gemini 2.5 Pro's 1M+ token
context window to analyze files of any size.
"""

import argparse
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Import Google Cloud libraries with proper error handling
try:
    from vertexai.generative_models import GenerationConfig, GenerativeModel
    from google.cloud import aiplatform
except ImportError:
    print("Error: Required Google Cloud libraries not found.")
    print("Install with: pip install google-cloud-aiplatform")
    sys.exit(1)


def get_staged_files(extensions: List[str]) -> List[str]:
    """Get list of staged files with specified extensions."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=True,
    )

    all_files = result.stdout.strip().split("\n")
    return [f for f in all_files if any(f.endswith(ext) for ext in extensions)]


def read_file_content(file_path: str) -> Optional[str]:
    """Read and return file content safely, with no line limitations."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None


def analyze_code_with_gemini(
    files_content: Dict[str, str],
    project_id: str = "cherry-ai-project",
    location: str = "us-central1",
) -> Dict[str, Any]:
    """
    Analyze code using Gemini 2.5 Pro API with 1M+ token context window.

    Args:
        files_content: Dictionary mapping file paths to content
        project_id: GCP project ID
        location: GCP region

    Returns:
        Analysis results
    """
    # Initialize Vertex AI
    try:
        aiplatform.init(project=project_id, location=location)

        # Create the model with 2.5 Pro and configure for large context window
        model = GenerativeModel("gemini-2.5-pro")

        # Configure generation parameters to leverage extended context window
        generation_config = GenerationConfig(
            temperature=0.2,  # Lower temperature for more focused code analysis
            max_output_tokens=8192,  # Allow for detailed analysis output
            top_p=0.95,
            top_k=40,
        )

        # Prepare prompt with code from all files (no line limitations)
        prompt = "You are an expert code reviewer specialized in identifying security vulnerabilities, performance issues, and adherence to best practices. Analyze the following code files thoroughly:\n\n"

        for file_path, content in files_content.items():
            prompt += f"File: {file_path}\n```python\n{content}\n```\n\n"

        prompt += """
Provide a comprehensive analysis focusing on:
1. Security vulnerabilities and their severity
2. Performance issues and bottlenecks
3. Code quality and adherence to best practices
4. Potential bugs or edge cases
5. Recommendations for improvement

Format your response with clear sections and use markdown formatting for readability.
"""

        # Get response from Gemini with extended context window
        response = model.generate_content(prompt, generation_config=generation_config)

        # Basic security scan for common issues
        security_issues = scan_for_security_issues(files_content)
        if security_issues:
            return {
                "analysis": response.text,
                "files_analyzed": list(files_content.keys()),
                "security_issues": security_issues,
                "has_critical_issues": any(
                    issue["severity"] == "critical" for issue in security_issues
                ),
            }

        return {
            "analysis": response.text,
            "files_analyzed": list(files_content.keys()),
            "security_issues": [],
            "has_critical_issues": False,
        }
    except Exception as e:
        print(f"Error with Gemini API: {str(e)}")
        # Fall back to basic security scan only
        security_issues = scan_for_security_issues(files_content)
        return {
            "analysis": f"Unable to get Gemini analysis. Basic security scan performed.\nError: {str(e)}",
            "files_analyzed": list(files_content.keys()),
            "security_issues": security_issues,
            "has_critical_issues": any(
                issue["severity"] == "critical" for issue in security_issues
            ),
        }


def scan_for_security_issues(files_content: Dict[str, str]) -> List[Dict[str, Any]]:
    """Perform a basic security scan on the code."""
    security_issues = []

    # Patterns to check for (very simple implementation)
    security_patterns = [
        {
            "pattern": "os.system(",
            "message": "Potential command injection vulnerability with os.system()",
            "severity": "critical",
        },
        {
            "pattern": "eval(",
            "message": "Dangerous eval() function can execute arbitrary code",
            "severity": "critical",
        },
        {
            "pattern": "exec(",
            "message": "Dangerous exec() function can execute arbitrary code",
            "severity": "critical",
        },
        {
            "pattern": "subprocess.call(",
            "message": "Potential command injection with subprocess.call()",
            "severity": "moderate",
        },
        {
            "pattern": "hardcoded_secret",
            "message": "Possible hardcoded secret",
            "severity": "critical",
        },
        {
            "pattern": "password",
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
    parser = argparse.ArgumentParser(
        description="Analyze code with Gemini 2.5 Pro (unlimited file size)"
    )
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

    print("Running Gemini 2.5 Pro code analysis on files...")
    print(f"Files: {','.join(staged_files)}")

    # Read file contents - no line limits with Gemini 2.5 Pro
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
        # Analyze code with Gemini 2.5 Pro's extended context window
        results = analyze_code_with_gemini(files_content)

        # Print analysis results
        print("\n===== Gemini 2.5 Pro Code Analysis =====\n")
        print(results["analysis"])
        print("\n=========================================\n")

        # Print security issues
        if results.get("security_issues"):
            print("\n===== Security Issues Found =====\n")
            for issue in results["security_issues"]:
                print(
                    f"{issue['severity'].upper()} in {issue['file']} (line {issue['line']})"
                )
                print(f"  Message: {issue['message']}")
                print(f"  Code: {issue['code']}\n")
            print("================================\n")

        # If critical issues are found, exit with error
        if results.get("has_critical_issues"):
            print("Critical security issues found in your code!")
            print(
                "Please fix the issues before committing or use 'git commit --no-verify' to bypass this check."
            )
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
