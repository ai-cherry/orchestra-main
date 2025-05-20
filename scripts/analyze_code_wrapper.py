#!/usr/bin/env python3
"""
Wrapper for analyze_code.sh to handle pre-commit file lists properly.

This script takes a list of files as separate arguments (as provided by pre-commit),
joins them into a comma-separated string, and passes that string as a single
argument to analyze_code.sh.
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Wrapper for analyze_code.sh")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Just print the command that would be executed without running it",
    )
    parser.add_argument(
        "--type",
        dest="analysis_type",
        default="security",
        help="Type of analysis: security, performance, or style",
    )
    parser.add_argument("files", nargs="*", help="Files to analyze")
    return parser.parse_args()


def main():
    args = parse_args()

    # Handle files from command line or from pre-commit (sys.argv[1:])
    files = args.files or sys.argv[1:]

    # Join all file arguments with commas
    files_arg = ",".join(files)

    # Only proceed if we have files
    if not files_arg:
        print("No files to analyze")
        return 0

    # Get the directory of this script to ensure we can find analyze_code.sh
    script_dir = Path(__file__).parent.absolute()
    analyze_script = os.path.join(script_dir, "..", "analyze_code.sh")

    # Ensure the path is absolute
    analyze_script = os.path.abspath(analyze_script)

    # Check if analyze_code.sh exists
    if not os.path.exists(analyze_script):
        print(f"Error: Could not find analyze_code.sh at {analyze_script}")
        return 1

    # Build the command
    cmd = [analyze_script, files_arg]
    if args.analysis_type and args.analysis_type != "security":
        cmd = [analyze_script, f"--type={args.analysis_type}", files_arg]

    print(f"Running analysis on: {files_arg}")

    # In dry-run mode, just print the command
    if args.dry_run:
        print(f"DRY RUN: Would execute: {' '.join(cmd)}")
        return 0

    # Call analyze_code.sh with proper format
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Pass through the output and return code
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
