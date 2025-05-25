#!/usr/bin/env python3
"""
Fix Python version inconsistencies across the entire codebase.

This script standardizes on Python 3.10 as the minimum version
since that's what's actually running and working.
"""

import os
import re
import subprocess
import logging
from typing import List, Tuple

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# The ACTUAL Python version we're using
PYTHON_VERSION = "3.10"
MIN_VERSION_TUPLE = "(3, 10)"

# Files to update
FILES_TO_UPDATE = [
    # AI Context files
    (
        "ai_context_planner.py",
        [
            (r"Python 3\.11\+", f"Python {PYTHON_VERSION}+"),
            (r"minimum 3\.11", f"minimum {PYTHON_VERSION}"),
            (r"Python 3\.11\+ REQUIRED", f"Python {PYTHON_VERSION}+ REQUIRED"),
        ],
    ),
    (
        "ai_context_coder.py",
        [
            (r"Python 3\.11\+", f"Python {PYTHON_VERSION}+"),
            (r"Python 3\.11\.4", f"Python {PYTHON_VERSION}"),
            (r">=3\.11 required", f">={PYTHON_VERSION} required"),
            (r"Target Python 3\.11\+", f"Target Python {PYTHON_VERSION}+"),
        ],
    ),
    (
        "ai_context_reviewer.py",
        [
            (r"Python 3\.11\+", f"Python {PYTHON_VERSION}+"),
            (r">3\.11", f">{PYTHON_VERSION}"),
            (r"Python 3\.11", f"Python {PYTHON_VERSION}"),
        ],
    ),
    (
        "ai_context_debugger.py",
        [
            (r"Python 3\.11\+", f"Python {PYTHON_VERSION}+"),
            (r"Python 3\.11\.6", f"Python {PYTHON_VERSION}"),
            (r"minimum 3\.11", f"minimum {PYTHON_VERSION}"),
            (r"after.*Python 3\.11", f"after Python {PYTHON_VERSION}"),
        ],
    ),
    # Script files
    (
        "scripts/config_validator.py",
        [
            (
                r"MIN_PYTHON_VERSION = \(3, 11\)",
                f"MIN_PYTHON_VERSION = {MIN_VERSION_TUPLE}",
            ),
        ],
    ),
    (
        "scripts/check_venv.py",
        [
            (
                r"MIN_PYTHON_VERSION = \(3, 11\)",
                f"MIN_PYTHON_VERSION = {MIN_VERSION_TUPLE}",
            ),
        ],
    ),
    (
        "scripts/health_monitor.py",
        [
            (
                r"MIN_PYTHON_VERSION = \(3, 11\)",
                f"MIN_PYTHON_VERSION = {MIN_VERSION_TUPLE}",
            ),
        ],
    ),
    (
        "scripts/ai_code_reviewer.py",
        [
            (
                r"MIN_PYTHON_VERSION = \(3, 11\)",
                f"MIN_PYTHON_VERSION = {MIN_VERSION_TUPLE}",
            ),
        ],
    ),
    # Setup files
    (
        "packages/vertex_client/setup.py",
        [
            (
                r'python_requires=">=3\.11, <4"',
                f'python_requires=">={PYTHON_VERSION}, <4"',
            ),
        ],
    ),
    # GitHub Actions
    (
        ".github/workflows/ci.yml",
        [
            (r'python-version: "3\.11"', f'python-version: "{PYTHON_VERSION}"'),
            (r"python-version: '3\.11'", f"python-version: '{PYTHON_VERSION}'"),
        ],
    ),
    (
        ".github/workflows/main.yml",
        [
            (r"python-version: '3\.11'", f"python-version: '{PYTHON_VERSION}'"),
        ],
    ),
]


def update_file(filepath: str, replacements: List[Tuple[str, str]]) -> bool:
    """Update a file with the given replacements."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return False

    try:
        with open(filepath, "r") as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"✅ Updated: {filepath}")
            return True
        else:
            logger.info(f"⏭️  No changes needed: {filepath}")
            return False
    except Exception as e:
        logger.error(f"❌ Error updating {filepath}: {e}")
        return False


def create_version_lock_file():
    """Create a version lock file to prevent future confusion."""
    lock_content = f"""# PYTHON VERSION LOCK FILE
# DO NOT MODIFY WITHOUT TEAM CONSENSUS

# This project uses Python {PYTHON_VERSION}
# All code, documentation, and CI/CD must use this version

PYTHON_VERSION={PYTHON_VERSION}
MIN_PYTHON_VERSION={PYTHON_VERSION}
PYTHON_EXECUTABLE=python3

# To check your version:
# python3 --version

# To create a virtual environment:
# python3 -m venv venv
# source venv/bin/activate

# NPM Version (for admin UI)
NODE_VERSION=18
NPM_VERSION=9

# To install Node.js:
# curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
# sudo apt-get install -y nodejs
"""

    with open(".python-version-lock", "w") as f:
        f.write(lock_content)
    logger.info("✅ Created .python-version-lock file")


def create_environment_validator():
    """Create a script to validate the environment."""
    validator_content = f'''#!/usr/bin/env python3
"""Environment validator to prevent version issues."""

import sys
import subprocess
import os

def check_python():
    """Check Python version."""
    required = {MIN_VERSION_TUPLE}
    current = sys.version_info[:2]

    if current < required:
        print(f"❌ Python {{'.'.join(map(str, required))}}+ required, but running {{'.'.join(map(str, current))}}")
        return False
    print(f"✅ Python version OK: {{'.'.join(map(str, current))}}")
    return True

def check_venv():
    """Check if in virtual environment."""
    if not os.environ.get('VIRTUAL_ENV'):
        print("❌ Not in virtual environment!")
        print("   Run: source venv/bin/activate")
        return False
    print(f"✅ Virtual environment active: {{os.environ['VIRTUAL_ENV']}}")
    return True

def check_npm():
    """Check Node/NPM for admin UI."""
    try:
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True)

        if node_result.returncode == 0:
            print(f"✅ Node.js installed: {{node_result.stdout.strip()}}")
        else:
            print("⚠️  Node.js not found (needed for admin UI)")

        if npm_result.returncode == 0:
            print(f"✅ NPM installed: {{npm_result.stdout.strip()}}")
        else:
            print("⚠️  NPM not found (needed for admin UI)")
    except FileNotFoundError:
        print("⚠️  Node.js/NPM not found (needed for admin UI)")

def main():
    """Run all checks."""
    print("🔍 Orchestra Environment Validator")
    print("="*50)

    checks_passed = True

    if not check_python():
        checks_passed = False

    if not check_venv():
        checks_passed = False

    check_npm()

    if checks_passed:
        print("\\n✅ Environment ready!")
    else:
        print("\\n❌ Environment issues found. Fix them before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    with open("scripts/validate_environment.py", "w") as f:
        f.write(validator_content)

    subprocess.run(["chmod", "+x", "scripts/validate_environment.py"], check=True)
    logger.info("✅ Created scripts/validate_environment.py")


def main():
    """Fix Python version issues across the codebase."""
    logger.info("🔧 Fixing Python Version Issues Permanently")
    logger.info("=" * 50)
    logger.info(f"Standardizing on Python {PYTHON_VERSION}+")

    # Update all files
    updated_count = 0
    for filepath, replacements in FILES_TO_UPDATE:
        if update_file(filepath, replacements):
            updated_count += 1

    # Create lock file
    create_version_lock_file()

    # Create validator
    create_environment_validator()

    logger.info(f"\n📊 Summary:")
    logger.info(f"✅ Updated {updated_count} files")
    logger.info(f"✅ Created version lock file")
    logger.info(f"✅ Created environment validator")

    logger.info("\n🎯 Next Steps:")
    logger.info("1. Run: python scripts/validate_environment.py")
    logger.info(
        "2. Commit these changes: git add -A && git commit -m 'Fix: Standardize on Python 3.10'"
    )
    logger.info(
        "3. Always check environment before starting: python scripts/validate_environment.py"
    )


if __name__ == "__main__":
    main()
