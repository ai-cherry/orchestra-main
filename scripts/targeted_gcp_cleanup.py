#!/usr/bin/env python3
"""Targeted GCP cleanup for remaining Python files."""

import os
import re
from pathlib import Path
from typing import List


def get_python_files_with_gcp() -> List[Path]:
    """Find Python files that still contain GCP references."""
    gcp_patterns = [
        "google-cloud",
        "firestore",
        "bigquery",
        "vertex",
        "secret_manager",
        "google.cloud",
        "gcp",
        "GCP",
    ]

    python_files = []
    for root, dirs, files in os.walk("."):
        # Skip virtual environments and cache directories
        if any(
            skip in root
            for skip in [".venv", "venv", ".mypy_cache", ".git", "__pycache__"]
        ):
            continue

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if any(pattern in content for pattern in gcp_patterns):
                            python_files.append(file_path)
                except Exception:
                    pass

    return python_files


def clean_imports(content: str) -> str:
    """Remove GCP-related imports."""
    import_patterns = [
        r"from google\.cloud import .*\n",
        r"import google\.cloud\..*\n",
        r"from google import .*\n",
        r"import google\..*\n",
        r"from .*firestore.* import .*\n",
        r"import .*firestore.*\n",
    ]

    for pattern in import_patterns:
        content = re.sub(pattern, "", content, flags=re.MULTILINE)

    return content


def clean_gcp_references(content: str) -> str:
    """Replace GCP service references with alternatives."""
    replacements = [
        # Firestore -> MongoDB
        (r"\bfirestore\b", "mongodb", re.IGNORECASE),
        (r"\bFirestore\b", "MongoDB", 0),
        (r"\bFIRESTORE\b", "MONGODB", 0),
        # Remove GCP project references
        (r"GCP_PROJECT_ID.*=.*\n", "", re.MULTILINE),
        (r"gcp_project_id.*=.*\n", "", re.MULTILINE),
        # Remove Vertex AI references
        (r"vertex_ai", "openai", re.IGNORECASE),
        (r"VERTEX", "OPENAI", 0),
        # Secret Manager -> Environment variables
        (r"secret_manager", "os.environ", re.IGNORECASE),
        (r"SecretManager", "EnvironmentConfig", 0),
    ]

    for pattern, replacement, flags in replacements:
        content = re.sub(pattern, replacement, content, flags=flags)

    return content


def clean_file(file_path: Path) -> bool:
    """Clean a single file of GCP references."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # Skip if it's a cleanup script
        if "cleanup" in str(file_path):
            return False

        content = original_content

        # Clean imports first
        content = clean_imports(content)

        # Clean references
        content = clean_gcp_references(content)

        # Only write if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")

    return False


def main():
    """Main cleanup function."""
    print("🎯 Starting targeted GCP cleanup...")

    # Find files with GCP references
    print("\n🔍 Finding Python files with GCP references...")
    files = get_python_files_with_gcp()

    # Filter out files we shouldn't modify
    skip_patterns = [
        "cleanup",
        "test_",
        "__pycache__",
        ".venv",
        "venv",
        "migrations",
    ]

    files = [f for f in files if not any(skip in str(f) for skip in skip_patterns)]

    print(f"📊 Found {len(files)} files to process")

    if not files:
        print("✅ No files need cleaning!")
        return

    # Process each file
    updated_count = 0
    for file_path in files:
        print(f"\n📝 Processing {file_path}...")
        if clean_file(file_path):
            print("  ✓ Updated")
            updated_count += 1
        else:
            print("  - No changes needed")

    print(f"\n✅ Updated {updated_count} files")

    if updated_count > 0:
        print("\nNext steps:")
        print("1. Review changes: git diff")
        print("2. Run linting: black . && flake8")
        print("3. Test the system: ./start_orchestra.sh")
        print(
            "4. Commit if satisfied: git add -A && git commit -m 'chore: Targeted GCP cleanup'"
        )


if __name__ == "__main__":
    main()
