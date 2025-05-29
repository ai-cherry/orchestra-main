#!/usr/bin/env python3
"""Environment validator to prevent version issues."""

import os
import subprocess
import sys


def check_python():
    """Check Python version."""
    required = (3, 10)
    current = sys.version_info[:2]

    if current < required:
        print(f"❌ Python {'.'.join(map(str, required))}+ required, but running {'.'.join(map(str, current))}")
        return False
    print(f"✅ Python version OK: {'.'.join(map(str, current))}")
    return True


def check_venv():
    """Check if in virtual environment."""
    if not os.environ.get("VIRTUAL_ENV"):
        print("❌ Not in virtual environment!")
        print("   Run: source venv/bin/activate")
        return False
    print(f"✅ Virtual environment active: {os.environ['VIRTUAL_ENV']}")
    return True


def check_npm():
    """Check Node/NPM for admin UI."""
    try:
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True)

        if node_result.returncode == 0:
            print(f"✅ Node.js installed: {node_result.stdout.strip()}")
        else:
            print("⚠️  Node.js not found (needed for admin UI)")

        if npm_result.returncode == 0:
            print(f"✅ NPM installed: {npm_result.stdout.strip()}")
        else:
            print("⚠️  NPM not found (needed for admin UI)")
    except FileNotFoundError:
        print("⚠️  Node.js/NPM not found (needed for admin UI)")


def main():
    """Run all checks."""
    print("🔍 Orchestra Environment Validator")
    print("=" * 50)

    checks_passed = True

    if not check_python():
        checks_passed = False

    if not check_venv():
        checks_passed = False

    check_npm()

    if checks_passed:
        print("\n✅ Environment ready!")
    else:
        print("\n❌ Environment issues found. Fix them before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
