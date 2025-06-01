#!/usr/bin/env python3
"""Verify Roo setup for the Orchestra project."""

import json
import os
from pathlib import Path
from typing import Dict, List


def check_modes() -> Dict[str, bool]:
    """Check that all mode files exist."""
    modes_dir = Path(".roo/modes")
    expected_modes = [
        "architect", "code", "debug", "orchestrator", "strategy",
        "research", "analytics", "implementation", "quality", "documentation"
    ]
    
    results = {}
    for mode in expected_modes:
        mode_file = modes_dir / f"{mode}.json"
        if mode_file.exists():
            try:
                with open(mode_file) as f:
                    data = json.load(f)
                    results[mode] = data.get("slug") == mode
            except Exception as e:
                results[mode] = False
                print(f"Error reading {mode}.json: {e}")
        else:
            results[mode] = False
    
    return results


def check_rules() -> Dict[str, bool]:
    """Check that all rules directories exist with at least one file."""
    rules_base = Path(".roo")
    expected_modes = [
        "architect", "code", "debug", "orchestrator", "strategy",
        "research", "analytics", "implementation", "quality", "documentation"
    ]
    
    results = {}
    for mode in expected_modes:
        rules_dir = rules_base / f"rules-{mode}"
        if rules_dir.exists() and rules_dir.is_dir():
            md_files = list(rules_dir.glob("*.md"))
            results[mode] = len(md_files) > 0
        else:
            results[mode] = False
    
    return results


def check_mcp_config() -> bool:
    """Check that MCP configuration exists and is valid."""
    mcp_file = Path(".roo/mcp.json")
    if not mcp_file.exists():
        return False
    
    try:
        with open(mcp_file) as f:
            data = json.load(f)
            return "mcpServers" in data and "orchestra-mcp" in data["mcpServers"]
    except Exception:
        return False


def main():
    """Run all verification checks."""
    print("🔍 Verifying Roo Setup for Orchestra Project\n")
    
    # Check modes
    print("📋 Checking Mode Configurations:")
    modes = check_modes()
    for mode, status in modes.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {mode}.json")
    
    # Check rules
    print("\n📚 Checking Rules Directories:")
    rules = check_rules()
    for mode, status in rules.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} rules-{mode}/")
    
    # Check MCP
    print("\n🔌 Checking MCP Configuration:")
    mcp_ok = check_mcp_config()
    icon = "✅" if mcp_ok else "❌"
    print(f"  {icon} MCP configuration")
    
    # Summary
    all_modes_ok = all(modes.values())
    all_rules_ok = all(rules.values())
    all_ok = all_modes_ok and all_rules_ok and mcp_ok
    
    print("\n" + "="*50)
    if all_ok:
        print("✅ All checks passed! Roo is properly configured.")
        print("\nNext steps:")
        print("1. Close Roo if it's running")
        print("2. Start your MCP server")
        print("3. Reopen Roo")
        print("4. Test mode switching with 'switch to [mode] mode'")
    else:
        print("❌ Some checks failed. Please review the issues above.")
        if not all_modes_ok:
            print("\n⚠️  Missing mode files - check .roo/modes/")
        if not all_rules_ok:
            print("\n⚠️  Missing rules files - check .roo/rules-*/")
        if not mcp_ok:
            print("\n⚠️  MCP configuration issue - check .roo/mcp.json")


if __name__ == "__main__":
    main() 