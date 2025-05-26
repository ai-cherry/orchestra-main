#!/usr/bin/env python3
"""Check and summarize pre-commit hook status."""

import subprocess
import sys
from collections import defaultdict


def run_command(cmd: str) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def check_hook_status():
    """Check status of all pre-commit hooks."""
    print("🔍 Checking pre-commit hook status...\n")

    # Run all hooks
    exit_code, output = run_command("pre-commit run --all-files 2>&1")

    # Parse output
    hooks_status = {}
    for line in output.split("\n"):
        if "..." in line and (line.endswith("Passed") or line.endswith("Failed")):
            parts = line.split(".")
            hook_name = parts[0].strip()
            status = "Passed" if line.endswith("Passed") else "Failed"
            hooks_status[hook_name] = status

    # Display results
    print("📊 Pre-commit Hook Status:")
    print("-" * 40)
    for hook, status in hooks_status.items():
        emoji = "✅" if status == "Passed" else "❌"
        print(f"{emoji} {hook}: {status}")

    return hooks_status


def check_flake8_issues():
    """Get detailed flake8 issues."""
    print("\n🔍 Checking flake8 issues...\n")

    exit_code, output = run_command("pre-commit run flake8 --all-files 2>&1")

    if exit_code == 0:
        print("✅ No flake8 issues found!")
        return {}

    # Parse flake8 output
    issues = defaultdict(list)
    for line in output.split("\n"):
        if ":" in line and any(
            code in line for code in ["F401", "F541", "F841", "W605", "F821"]
        ):
            parts = line.split(":", 3)
            if len(parts) >= 4:
                file_path = parts[0]
                error_code = parts[3].split()[0]
                issues[error_code].append(file_path)

    # Display summary
    print("📊 Flake8 Issues Summary:")
    print("-" * 40)
    for code, files in sorted(issues.items()):
        print(f"\n{code} ({len(files)} occurrences):")
        for f in sorted(set(files))[:5]:  # Show first 5 unique files
            print(f"  - {f}")
        if len(set(files)) > 5:
            print(f"  ... and {len(set(files)) - 5} more files")

    return issues


def check_mypy_issues():
    """Get detailed mypy issues."""
    print("\n🔍 Checking mypy issues...\n")

    exit_code, output = run_command("pre-commit run mypy --all-files 2>&1")

    if exit_code == 0:
        print("✅ No mypy issues found!")
        return 0

    # Count errors
    error_count = output.count("error:")
    print(f"📊 Mypy found {error_count} type errors")

    # Show first few errors
    errors = []
    for line in output.split("\n"):
        if "error:" in line:
            errors.append(line.strip())

    print("\nFirst few errors:")
    print("-" * 40)
    for error in errors[:10]:
        print(f"  {error}")

    if len(errors) > 10:
        print(f"\n  ... and {len(errors) - 10} more errors")

    return error_count


def main():
    """Main function."""
    print("🚀 Orchestra AI Pre-commit Status Check\n")

    # Check overall status
    hooks_status = check_hook_status()

    # Get detailed issues for failing hooks
    if hooks_status.get("flake8") == "Failed":
        check_flake8_issues()

    if hooks_status.get("mypy") == "Failed":
        check_mypy_issues()

    # Summary
    print("\n📋 Summary:")
    print("=" * 50)

    passed = sum(1 for s in hooks_status.values() if s == "Passed")
    failed = sum(1 for s in hooks_status.values() if s == "Failed")

    print(f"✅ Passed: {passed} hooks")
    print(f"❌ Failed: {failed} hooks")

    if failed == 0:
        print("\n🎉 All pre-commit hooks are passing! Ready to commit.")
        return 0
    else:
        print("\n⚠️  Some hooks are failing. Please fix the issues above.")
        print("\nNext steps:")
        print("1. Fix type annotations for mypy errors")
        print("2. Remove unused imports (F401)")
        print("3. Fix f-strings without placeholders (F541)")
        print("4. Fix invalid escape sequences (W605)")
        print("5. Run 'pre-commit run --all-files' to verify")
        return 1


if __name__ == "__main__":
    sys.exit(main())
