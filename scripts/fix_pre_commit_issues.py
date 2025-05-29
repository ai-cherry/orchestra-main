#!/usr/bin/env python3
"""Script to fix common pre-commit issues automatically."""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def fix_unused_imports(file_path: Path) -> bool:
    """Remove unused imports from a Python file."""
    try:
        # Run autoflake to remove unused imports
        result = subprocess.run(
            ["autoflake", "--in-place", "--remove-unused-variables", str(file_path)],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("autoflake not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "autoflake"])
        return fix_unused_imports(file_path)


def fix_f_strings_without_placeholders(file_path: Path) -> bool:
    """Convert f-strings without placeholders to regular strings."""
    modified = False
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Pattern to match f-strings without placeholders
        pattern = r'f(["\'])([^{]*?)\1'

        def replace_f_string(match):
            quote = match.group(1)
            content = match.group(2)
            # Check if there are any { or } in the content
            if "{" not in content and "}" not in content:
                return f"{quote}{content}{quote}"
            return match.group(0)

        new_content = re.sub(pattern, replace_f_string, content)

        if new_content != content:
            with open(file_path, "w") as f:
                f.write(new_content)
            modified = True

    except Exception as e:
        print(f"Error fixing f-strings in {file_path}: {e}")

    return modified


def fix_escape_sequences(file_path: Path) -> bool:
    """Fix invalid escape sequences by converting to raw strings or escaping properly."""
    modified = False
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            # Check for common invalid escape sequences
            if re.search(r"\\[dws]", line) and not line.strip().startswith("r"):
                # If it's a string literal, convert to raw string
                if re.search(r'["\'].*\\[dws].*["\']', line):
                    # Try to convert to raw string
                    line = re.sub(r'(["\'])(.*\\[dws].*)\1', r"r\1\2\1", line)
                    modified = True
            new_lines.append(line)

        if modified:
            with open(file_path, "w") as f:
                f.writelines(new_lines)

    except Exception as e:
        print(f"Error fixing escape sequences in {file_path}: {e}")

    return modified


def add_type_annotations(file_path: Path) -> bool:
    """Add basic type annotations to functions missing them."""
    # This is a placeholder - adding proper type annotations requires more context
    # For now, we'll just report files that need manual attention
    return False


def get_python_files() -> List[Path]:
    """Get all Python files in the project."""
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".mypy_cache", "node_modules"}

    for root, dirs, files in os.walk("."):
        # Remove excluded directories from dirs to prevent walking into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return python_files


def main():
    """Main function to fix pre-commit issues."""
    print("Fixing common pre-commit issues...")

    # Get list of files with issues from flake8
    result = subprocess.run(["flake8", "--select=F401,F541,F841,W605", "."], capture_output=True, text=True)

    issues = result.stdout.strip().split("\n") if result.stdout else []

    files_to_fix: List[Tuple[Path, str]] = []
    issue_types = {
        "F401": "unused imports",
        "F541": "f-strings without placeholders",
        "F841": "unused variables",
        "W605": "invalid escape sequences",
    }

    for issue in issues:
        if ":" in issue:
            parts = issue.split(":")
            if len(parts) >= 4:
                file_path = Path(parts[0])
                error_code = parts[3].split()[0]
                files_to_fix.append((file_path, error_code))

    # Fix issues
    for file_path, error_code in files_to_fix:
        if not file_path.exists():
            continue

        print(f"Fixing {issue_types.get(error_code, error_code)} in {file_path}")

        if error_code in ["F401", "F841"]:
            fix_unused_imports(file_path)
        elif error_code == "F541":
            fix_f_strings_without_placeholders(file_path)
        elif error_code == "W605":
            fix_escape_sequences(file_path)

    # Run black to format all modified files
    print("\nRunning black formatter...")
    subprocess.run(["black", "."])

    print("\nDone! Please review the changes and run 'pre-commit run --all-files' to verify.")


if __name__ == "__main__":
    main()
