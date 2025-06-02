#!/usr/bin/env python3
"""Comprehensive validation of Roo and MCP setup for Orchestra project."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def check_json_validity(file_path: Path) -> Tuple[bool, str]:
    """Check if a JSON file is valid."""
    try:
        with open(file_path) as f:
            json.load(f)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"JSON Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def validate_mode_structure(mode_data: dict, mode_name: str) -> List[str]:
    """Validate the structure of a mode configuration."""
    errors = []
    required_fields = ["slug", "name", "roleDefinition", "groups", "fileRegex", "apiConfiguration"]

    for field in required_fields:
        if field not in mode_data:
            errors.append(f"Missing required field: {field}")

    if "apiConfiguration" in mode_data:
        api_config = mode_data["apiConfiguration"]
        api_required = ["provider", "model", "temperature", "maxTokens"]

        for field in api_required:
            if field not in api_config:
                errors.append(f"Missing API configuration field: {field}")

        if api_config.get("provider") != "openrouter":
            errors.append(f"Provider must be 'openrouter', got: {api_config.get('provider')}")

    if mode_data.get("slug") != mode_name:
        errors.append(f"Slug mismatch: expected '{mode_name}', got '{mode_data.get('slug')}'")

    return errors


def validate_modes() -> Dict[str, Dict]:
    """Validate all mode configurations."""
    modes_dir = Path(".roo/modes")
    expected_modes = [
        "architect",
        "code",
        "debug",
        "orchestrator",
        "strategy",
        "research",
        "analytics",
        "implementation",
        "quality",
        "documentation",
    ]

    # Expected model assignments
    model_assignments = {
        "architect": "anthropic/claude-opus-4",
        "code": "google/gemini-2.5-flash-preview-05-20",
        "debug": "openai/gpt-4.1",
        "orchestrator": "anthropic/claude-sonnet-4",
        "strategy": "anthropic/claude-opus-4",
        "research": "anthropic/claude-sonnet-4",
        "analytics": "google/gemini-2.5-flash-preview-05-20",
        "implementation": "google/gemini-2.5-flash-preview-05-20",
        "quality": "openai/gpt-4.1",
        "documentation": "anthropic/claude-sonnet-4",
    }

    results = {}

    for mode in expected_modes:
        mode_file = modes_dir / f"{mode}.json"
        result = {"exists": False, "valid_json": False, "errors": [], "model_correct": False}

        if mode_file.exists():
            result["exists"] = True
            valid, msg = check_json_validity(mode_file)
            result["valid_json"] = valid

            if valid:
                with open(mode_file) as f:
                    data = json.load(f)

                # Check structure
                errors = validate_mode_structure(data, mode)
                result["errors"] = errors

                # Check model assignment
                actual_model = data.get("apiConfiguration", {}).get("model")
                expected_model = model_assignments[mode]
                result["model_correct"] = actual_model == expected_model
                if not result["model_correct"]:
                    result["errors"].append(f"Model mismatch: expected '{expected_model}', got '{actual_model}'")
            else:
                result["errors"].append(msg)
        else:
            result["errors"].append("File does not exist")

        results[mode] = result

    return results


def validate_rules() -> Dict[str, Dict]:
    """Validate rules directories and content."""
    rules_base = Path(".roo")
    expected_modes = [
        "architect",
        "code",
        "debug",
        "orchestrator",
        "strategy",
        "research",
        "analytics",
        "implementation",
        "quality",
        "documentation",
    ]

    results = {}

    for mode in expected_modes:
        rules_dir = rules_base / f"rules-{mode}"
        result = {"exists": False, "has_files": False, "file_count": 0, "files": []}

        if rules_dir.exists() and rules_dir.is_dir():
            result["exists"] = True
            md_files = list(rules_dir.glob("*.md"))
            result["file_count"] = len(md_files)
            result["has_files"] = len(md_files) > 0
            result["files"] = [f.name for f in md_files]

        results[mode] = result

    return results


def validate_mcp_config() -> Dict[str, any]:
    """Validate MCP configuration."""
    mcp_file = Path(".roo/mcp.json")
    result = {"exists": False, "valid_json": False, "has_servers": False, "servers": {}}

    if mcp_file.exists():
        result["exists"] = True
        valid, msg = check_json_validity(mcp_file)
        result["valid_json"] = valid

        if valid:
            with open(mcp_file) as f:
                data = json.load(f)

            if "mcpServers" in data:
                result["has_servers"] = True
                result["servers"] = {
                    "memory-bank": "memory-bank" in data["mcpServers"],
                    "portkey-router": "portkey-router" in data["mcpServers"],
                    "orchestra-mcp": "orchestra-mcp" in data["mcpServers"],
                }

                # Check orchestra-mcp configuration
                if "orchestra-mcp" in data["mcpServers"]:
                    orch_config = data["mcpServers"]["orchestra-mcp"]
                    result["orchestra_config"] = {
                        "command": orch_config.get("command"),
                        "args": orch_config.get("args"),
                        "env_configured": bool(orch_config.get("env")),
                        "tools_allowed": orch_config.get("alwaysAllow", []),
                    }

    return result


def check_legacy_files() -> List[str]:
    """Check for legacy configuration files that might interfere."""
    potential_conflicts = []

    # Check for old modes.json
    if Path(".roo/modes.json").exists():
        potential_conflicts.append(".roo/modes.json (legacy file - may cause conflicts)")

    # Check for UI config files
    ui_configs = [".roo/ui-config.json", ".roo/settings.json", ".roo/preferences.json"]
    for config in ui_configs:
        if Path(config).exists():
            potential_conflicts.append(f"{config} (UI configuration - should be blank/default)")

    return potential_conflicts


def print_results(modes_results, rules_results, mcp_result, legacy_files):
    """Print comprehensive validation results."""
    print("🔍 Comprehensive Roo & MCP Validation Report\n")
    print("=" * 60)

    # Modes validation
    print("\n📋 MODE CONFIGURATIONS:")
    all_modes_ok = True
    for mode, result in modes_results.items():
        if result["exists"] and result["valid_json"] and not result["errors"] and result["model_correct"]:
            print(f"  ✅ {mode}.json - All checks passed")
        else:
            all_modes_ok = False
            print(f"  ❌ {mode}.json - Issues found:")
            if not result["exists"]:
                print(f"     - File does not exist")
            elif not result["valid_json"]:
                print(f"     - Invalid JSON")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"     - {error}")

    # Rules validation
    print("\n📚 RULES DIRECTORIES:")
    all_rules_ok = True
    for mode, result in rules_results.items():
        if result["exists"] and result["has_files"]:
            print(f"  ✅ rules-{mode}/ - {result['file_count']} file(s): {', '.join(result['files'])}")
        else:
            all_rules_ok = False
            print(f"  ❌ rules-{mode}/ - Issues found:")
            if not result["exists"]:
                print(f"     - Directory does not exist")
            elif not result["has_files"]:
                print(f"     - No markdown files found")

    # MCP validation
    print("\n🔌 MCP CONFIGURATION:")
    mcp_ok = mcp_result["exists"] and mcp_result["valid_json"] and mcp_result["has_servers"]
    if mcp_ok and all(mcp_result["servers"].values()):
        print("  ✅ MCP configuration - All servers configured")
        if "orchestra_config" in mcp_result:
            config = mcp_result["orchestra_config"]
            print(f"     - Command: {config['command']}")
            print(f"     - Tools: {', '.join(config['tools_allowed'][:3])}...")
    else:
        print("  ❌ MCP configuration - Issues found:")
        if not mcp_result["exists"]:
            print("     - Configuration file does not exist")
        elif not mcp_result["valid_json"]:
            print("     - Invalid JSON")
        elif not mcp_result["has_servers"]:
            print("     - No servers configured")
        else:
            for server, exists in mcp_result["servers"].items():
                if not exists:
                    print(f"     - Missing server: {server}")

    # Legacy files
    if legacy_files:
        print("\n⚠️  POTENTIAL CONFLICTS:")
        for file in legacy_files:
            print(f"  - {file}")

    # Summary
    print("\n" + "=" * 60)
    all_ok = all_modes_ok and all_rules_ok and mcp_ok and not legacy_files

    if all_ok:
        print("✅ ALL CHECKS PASSED!")
        print("\nNext steps:")
        print("1. Ensure Roo UI settings for modes are blank/default")
        print("2. Close Roo if running")
        print("3. Start MCP servers:")
        print("   python mcp_server/servers/orchestrator_server.py")
        print("4. Reopen Roo")
        print("5. Test mode switching and MCP tools")
    else:
        print("❌ ISSUES FOUND - Please address the above problems")
        print("\nRemediation:")
        if not all_modes_ok:
            print("- Fix mode configuration files in .roo/modes/")
        if not all_rules_ok:
            print("- Add markdown files to missing rules directories")
        if not mcp_ok:
            print("- Fix MCP configuration in .roo/mcp.json")
        if legacy_files:
            print("- Remove or clear legacy configuration files")


def main():
    """Run comprehensive validation."""
    modes_results = validate_modes()
    rules_results = validate_rules()
    mcp_result = validate_mcp_config()
    legacy_files = check_legacy_files()

    print_results(modes_results, rules_results, mcp_result, legacy_files)


if __name__ == "__main__":
    main()
