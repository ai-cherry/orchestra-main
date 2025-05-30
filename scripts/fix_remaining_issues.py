#!/usr/bin/env python3
"""Fix remaining flake8 issues in the codebase."""

import re
from pathlib import Path


def fix_file(file_path: Path, fixes: list) -> bool:
    """Apply fixes to a specific file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        original_content = content

        for fix_type, pattern, replacement in fixes:
            if fix_type == "regex":
                content = re.sub(pattern, replacement, content)
            elif fix_type == "line":
                lines = content.split("\n")
                line_num = int(pattern) - 1  # Convert to 0-based
                if 0 <= line_num < len(lines):
                    lines[line_num] = replacement
                content = "\n".join(lines)

        if content != original_content:
            with open(file_path, "w") as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False


def main():
    """Main function to fix issues."""

    # Define fixes for each file
    fixes = {
        "infra/components/monitoring_component.py": [
            ("regex", r"regex: r'([^']+)'", r"regex: r'\\1'"),
        ],
        "orchestrator/enrichment_orchestrator.py": [
            ("regex", r"from typing import .*Optional.*\n", ""),
        ],
        "packages/shared/src/gateway_adapter.py": [
            ("regex", r'f"([^{}"]*)"', r'"\1"'),  # Remove f-string without placeholders
        ],
        "scripts/fix_python_version_permanently.py": [
            ("regex", r'f"([^{}"]*)"', r'"\1"'),  # Remove f-string without placeholders
        ],
        "scripts/orchestra_adapter.py": [
            ("regex", r"import json\n", ""),
            ("regex", r"from typing import .*Protocol.*\n", ""),
            ("regex", r"persona_id = [^\n]+\n", ""),  # Remove unused variable
        ],
        "scripts/performance_test.py": [
            ("regex", r'f"([^{}"]*)"', r'"\1"'),  # Remove f-string without placeholders
        ],
        "scripts/update_dependencies.py": [
            ("regex", r"from typing import .*Tuple.*\n", ""),
            ("regex", r"import piptools\n", ""),
        ],
        "secret-management/rotate_github_pat.py": [
            ("regex", r'f"([^{}"]*)"', r'"\1"'),  # Remove f-string without placeholders
        ],
        "services/admin-api/app/services/gcp_service.py": [
            ("regex", r'f"([^{}"]*)"', r'"\1"'),  # Remove f-string without placeholders
        ],
        "test_mcp_simple.py": [
            ("regex", r"import subprocess\n", ""),
            ("regex", r"import sys\n", ""),
            ("regex", r"import mcp\n", ""),
        ],
        "tests/integration/test_mcp_servers.py": [
            ("regex", r"import asyncio\n", ""),
            ("regex", r"from typing import .*Dict.*Any.*\n", ""),
        ],
        "tools/mode_system_initializer.py": [
            ("regex", r'f"([^{}"]*)"', r'"\1"'),  # Remove f-string without placeholders
        ],
    }

    # Apply fixes
    for file_path, file_fixes in fixes.items():
        if Path(file_path).exists():
            print(f"Fixing {file_path}...")
            if fix_file(Path(file_path), file_fixes):
                print("  ✓ Fixed")
            else:
                print("  - No changes needed")
        else:
            print(f"  ✗ File not found: {file_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
