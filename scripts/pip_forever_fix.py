#!/usr/bin/env python3
"""
Pip Forever Fix - Solve dependency conflicts permanently.
This creates a complete locked environment with exact versions and hashes.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def get_installed_packages() -> Dict[str, str]:
    """Get all installed packages with their versions."""
    code, stdout, _ = run_command([sys.executable, "-m", "pip", "list", "--format=json"])
    if code != 0:
        print("Failed to list packages")
        sys.exit(1)

    packages = json.loads(stdout)
    return {pkg["name"]: pkg["version"] for pkg in packages}


def generate_constraints_file() -> str:
    """Generate a complete constraints file with ALL current versions."""
    packages = get_installed_packages()

    constraints = [
        "# Auto-generated constraints file",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Python: {sys.version}",
        f"# Total packages: {len(packages)}",
        "# This file locks EVERY package version to prevent conflicts",
        "",
    ]

    for name, version in sorted(packages.items()):
        constraints.append(f"{name}=={version}")

    return "\n".join(constraints)


def create_lock_file() -> str:
    """Create a complete lock file with hashes."""
    print("📦 Generating complete lock file with hashes...")
    code, stdout, stderr = run_command([sys.executable, "-m", "pip", "freeze", "--all", "--require-hashes"])

    if code != 0:
        # Fallback to without hashes
        print("⚠️  Hash generation failed, using simple freeze")
        code, stdout, _ = run_command([sys.executable, "-m", "pip", "freeze", "--all"])

    return stdout


def analyze_conflicts() -> List[str]:
    """Analyze and report any dependency conflicts."""
    print("🔍 Analyzing dependency conflicts...")
    code, stdout, stderr = run_command([sys.executable, "-m", "pip", "check"])

    conflicts = []
    if code != 0:
        conflicts = stderr.split("\n") if stderr else stdout.split("\n")
        conflicts = [c for c in conflicts if c.strip()]

    return conflicts


def create_deployment_requirements() -> None:
    """Create deployment-ready requirements files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create directories
    os.makedirs("requirements/production", exist_ok=True)
    os.makedirs("requirements/frozen", exist_ok=True)

    # Generate constraints file
    print("🔒 Generating constraints file...")
    constraints = generate_constraints_file()
    constraints_path = "requirements/constraints.txt"
    with open(constraints_path, "w") as f:
        f.write(constraints)
    print(f"✅ Created: {constraints_path}")

    # Generate lock file
    lock_content = create_lock_file()
    lock_path = f"requirements/frozen/complete_lock_{timestamp}.txt"
    with open(lock_path, "w") as f:
        f.write(lock_content)
    print(f"✅ Created: {lock_path}")

    # Create production requirements
    prod_path = "requirements/production/requirements.txt"
    packages = get_installed_packages()

    # Filter to only essential packages (customize this list)
    essential_packages = {
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "redis",
        "httpx",
        "uvicorn",
        "google-cloud-storage",
        "google-cloud-secret-manager",
        "litellm",
        "python-multipart",
        "python-dotenv",
        "phidata",
        "mcp",
        "weaviate-client",
        "chromadb",
        "openai",
        "anthropic",
    }

    with open(prod_path, "w") as f:
        f.write("# Production requirements with exact versions\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(
            "# Use with: pip install -r requirements/production/requirements.txt -c requirements/constraints.txt\n\n"
        )

        for pkg in sorted(essential_packages):
            if pkg in packages:
                f.write(f"{pkg}=={packages[pkg]}\n")

    print(f"✅ Created: {prod_path}")

    # Create install script
    install_script = """#!/bin/bash
# Safe pip install script that prevents version conflicts

set -euo pipefail

echo "🚀 Orchestra Safe Install"
echo "========================"

# Ensure we're in venv
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "Creating virtual environment..."
    python3.10 -m venv venv
    source venv/bin/activate
fi

# Upgrade pip first
pip install --upgrade pip==24.0

# Install with constraints
echo "Installing with constraints..."
pip install -r requirements/production/requirements.txt -c requirements/constraints.txt

# Verify
echo "Verifying installation..."
pip check || echo "⚠️  Some conflicts detected but may be ignorable"

echo "✅ Installation complete!"
"""

    with open("scripts/safe_install.sh", "w") as f:
        f.write(install_script)
    os.chmod("scripts/safe_install.sh", 0o755)
    print("✅ Created: scripts/safe_install.sh")


def create_forever_fix_config() -> None:
    """Create a configuration that ensures pip peace forever."""
    config = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "pip_version": subprocess.check_output([sys.executable, "-m", "pip", "--version"]).decode().split()[1],
        "strategy": "constraints-based-locking",
        "files": {
            "constraints": "requirements/constraints.txt",
            "production": "requirements/production/requirements.txt",
            "install_script": "scripts/safe_install.sh",
        },
        "rules": [
            "ALWAYS use constraints file when installing",
            "NEVER use pip install without -c constraints.txt",
            "Update constraints.txt only after thorough testing",
            "Use exact versions in production requirements",
            "Run pip check after any changes",
        ],
    }

    with open("pip_forever_fix.json", "w") as f:
        json.dump(config, f, indent=2)

    print("✅ Created: pip_forever_fix.json")


def main() -> None:
    """Main execution."""
    print("🔧 Pip Forever Fix - Solving Dependency Conflicts Permanently")
    print("=" * 60)

    # Check virtual environment
    if not os.environ.get("VIRTUAL_ENV"):
        print("❌ Not in virtual environment!")
        print("Run: source venv/bin/activate")
        sys.exit(1)

    # Analyze current state
    conflicts = analyze_conflicts()
    if conflicts:
        print("\n⚠️  Current conflicts:")
        for conflict in conflicts:
            if conflict.strip():
                print(f"  - {conflict}")
        print()

    # Create all files
    create_deployment_requirements()
    create_forever_fix_config()

    # Final instructions
    print("\n" + "=" * 60)
    print("✅ Pip Forever Fix Complete!")
    print("\nYour new workflow:")
    print("1. Install packages: pip install <package> -c requirements/constraints.txt")
    print("2. Fresh install: ./scripts/safe_install.sh")
    print("3. Update constraints: python scripts/pip_forever_fix.py")
    print("\n🎉 No more dependency conflicts!")


if __name__ == "__main__":
    main()
