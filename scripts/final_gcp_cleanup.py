#!/usr/bin/env python3
"""Final GCP cleanup script to remove all remaining GCP references."""

import json
import re
from pathlib import Path
from typing import Dict


def load_cleanup_report() -> Dict:
    """Load the cleanup report from deep_cleanup.py."""
    report_path = Path("deep_cleanup_report.json")
    if not report_path.exists():
        print("❌ deep_cleanup_report.json not found!")
        return {}

    with open(report_path, "r") as f:
        return json.load(f)


def clean_config_files():
    """Clean up configuration files."""
    config_updates = {
        "core/orchestrator/src/config/config.py": [
            # Remove GCP-specific config
            (r"GCP_PROJECT_ID.*\n", ""),
            (r"FIRESTORE_ENABLED.*\n", ""),
            (
                r"MEMORY_BACKEND_TYPE.*firestore.*\n",
                'MEMORY_BACKEND_TYPE: str = "mongodb"\n',
            ),
            (r"GCP_CREDENTIALS_JSON.*\n", ""),
            (r"GCP_CREDENTIALS_PATH.*\n", ""),
            (r"USE_VERTEX_VECTOR_SEARCH.*\n", ""),
            (r"VERTEX_LOCATION.*\n", ""),
            (r"VERTEX_INDEX_ENDPOINT_ID.*\n.*\n.*\n", ""),
            (r"VERTEX_INDEX_ID.*\n", ""),
        ],
        "config/litellm_config.yaml": [
            # Remove Vertex AI models
            (r"- model_name: vertex_ai/.*\n(?:.*\n)*?(?=- model_name:|$)", ""),
        ],
        "config/agents_new.yaml": [
            # Remove GCP-specific agent configs
            (r"vertex_ai:.*\n(?:  .*\n)*?(?=\w|\Z)", ""),
            (r"gcp_.*:.*\n(?:  .*\n)*?(?=\w|\Z)", ""),
        ],
    }

    for file_path, patterns in config_updates.items():
        if not Path(file_path).exists():
            continue

        print(f"📝 Updating {file_path}")
        with open(file_path, "r") as f:
            content = f.read()

        original_content = content
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        if content != original_content:
            with open(file_path, "w") as f:
                f.write(content)
            print("  ✓ Updated")


def clean_memory_files():
    """Clean up memory-related files."""
    memory_files = [
        "core/orchestrator/src/agents/memory/manager.py",
        "core/orchestrator/src/api/dependencies/memory.py",
        "core/orchestrator/src/memory/factory.py",
        "core/orchestrator/src/memory/layered_memory_manager.py",
    ]

    replacements = [
        # Remove Firestore imports
        (r"from google\.cloud import firestore.*\n", ""),
        (r"import google\.cloud\.firestore.*\n", ""),
        (r"from \.\.\.memory\.backends\.firestore.*\n", ""),
        # Replace Firestore references with MongoDB
        (r"firestore", "mongodb"),
        (r"Firestore", "MongoDB"),
        (r"FIRESTORE", "MONGODB"),
        # Remove GCP-specific code blocks
        (r"if.*firestore.*:.*\n(?:    .*\n)*?(?=\S|\Z)", ""),
        (r"# GCP.*\n", ""),
    ]

    for file_path in memory_files:
        if not Path(file_path).exists():
            continue

        print(f"📝 Updating {file_path}")
        with open(file_path, "r") as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        if content != original_content:
            with open(file_path, "w") as f:
                f.write(content)
            print("  ✓ Updated")


def clean_shell_scripts():
    """Clean up shell scripts."""
    script_files = [
        "run_integration_tests.sh",
        "quick-deploy.sh",
        "start_mcp_system.sh",
        "execute_cleanup.sh",
        "run_connection_tests.sh",
        "implementation_plan.sh",
    ]

    replacements = [
        # Remove gcloud commands
        (r"gcloud.*\n", ""),
        # Remove GOOGLE_APPLICATION_CREDENTIALS
        (r"export GOOGLE_APPLICATION_CREDENTIALS.*\n", ""),
        (r"GOOGLE_APPLICATION_CREDENTIALS.*\n", ""),
        # Remove GCP project references
        (r"GCP_PROJECT.*\n", ""),
        (r"cherry-ai-project.*\n", ""),
    ]

    for file_path in script_files:
        if not Path(file_path).exists():
            continue

        print(f"📝 Updating {file_path}")
        with open(file_path, "r") as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        if content != original_content:
            with open(file_path, "w") as f:
                f.write(content)
            print("  ✓ Updated")


def clean_documentation():
    """Clean up documentation files."""
    doc_files = Path("docs").glob("*.md")

    replacements = [
        # Remove GCP service references
        (r"Google Cloud.*\n", ""),
        (r"GCP.*\n", ""),
        (r"Firestore.*\n", "MongoDB\n"),
        (r"Vertex AI.*\n", ""),
        (r"BigQuery.*\n", ""),
        (r"Cloud Run.*\n", ""),
        (r"Secret Manager.*\n", ""),
    ]

    for file_path in doc_files:
        print(f"📝 Updating {file_path}")
        with open(file_path, "r") as f:
            content = f.read()

        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(
                pattern, replacement, content, flags=re.MULTILINE | re.IGNORECASE
            )

        if content != original_content:
            with open(file_path, "w") as f:
                f.write(content)
            print("  ✓ Updated")


def main():
    """Main cleanup function."""
    print("🧹 Starting final GCP cleanup...")

    # Load the report
    report = load_cleanup_report()
    if not report:
        return

    print(
        f"\n📊 Found {len(report.get('files', {}).get('update', []))} files to update"
    )

    # Clean different file types
    print("\n🔧 Cleaning configuration files...")
    clean_config_files()

    print("\n🔧 Cleaning memory-related files...")
    clean_memory_files()

    print("\n🔧 Cleaning shell scripts...")
    clean_shell_scripts()

    print("\n🔧 Cleaning documentation...")
    clean_documentation()

    print("\n✅ Final GCP cleanup complete!")
    print("\nNext steps:")
    print("1. Review changes: git diff")
    print("2. Test the system: ./start_orchestra.sh")
    print(
        "3. Commit if satisfied: git add -A && git commit -m 'chore: Final GCP cleanup'"
    )


if __name__ == "__main__":
    main()
