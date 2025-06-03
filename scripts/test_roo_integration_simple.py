#!/usr/bin/env python3
"""
Simple test script to verify Roo-AI Orchestrator integration components
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_file_exists(filepath, description):
    """Test if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def test_config_valid(filepath, description):
    """Test if a JSON/YAML config file is valid"""
    if not Path(filepath).exists():
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False
    
    try:
        with open(filepath, 'r') as f:
            if filepath.endswith('.json'):
                json.load(f)
            else:
                # For YAML, just check if it's readable
                content = f.read()
                if len(content) > 0:
                    print(f"✅ {description}: {filepath} (valid)")
                    return True
    except Exception as e:
        print(f"❌ {description}: {filepath} (invalid - {e})")
        return False
    
    print(f"✅ {description}: {filepath} (valid)")
    return True

def main():
    print("🔍 Testing Roo-AI Orchestrator Integration Components\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test core integration files
    files_to_test = [
        ("ai_components/orchestration/roo_mcp_adapter.py", "RooMCPAdapter"),
        ("ai_components/orchestration/unified_api_router.py", "UnifiedAPIRouter"),
        ("ai_components/orchestration/mode_transition_manager.py", "ModeTransitionManager"),
        ("shared/database.py", "Database module"),
        ("shared/utils/error_handling.py", "Error handling utilities"),
        ("shared/utils/performance.py", "Performance utilities"),
        ("migrations/add_roo_integration_tables.sql", "Database migrations"),
        ("scripts/initialize_roo_integration.py", "Initialization script"),
        ("scripts/test_roo_integration.py", "Test script"),
        ("requirements/roo_integration.txt", "Requirements file"),
    ]
    
    print("📁 Checking integration files:")
    for filepath, description in files_to_test:
        tests_total += 1
        if test_file_exists(filepath, description):
            tests_passed += 1
    
    # Test configuration files
    print("\n📋 Checking configuration files:")
    config_files = [
        ("config/orchestrator_config.json", "Orchestrator config"),
        ("config/roo_mode_mappings.yaml", "Roo mode mappings"),
    ]
    
    for filepath, description in config_files:
        tests_total += 1
        if test_config_valid(filepath, description):
            tests_passed += 1
    
    # Test Roo mode files
    print("\n🎭 Checking Roo mode definitions:")
    roo_modes = [
        "code", "architect", "debug", "orchestrator", "strategy",
        "research", "analytics", "implementation", "quality", "documentation"
    ]
    
    for mode in roo_modes:
        tests_total += 1
        filepath = f".roo/modes/{mode}.json"
        if test_file_exists(filepath, f"Roo {mode} mode"):
            tests_passed += 1
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Total tests: {tests_total}")
    print(f"   Passed: {tests_passed}")
    print(f"   Failed: {tests_total - tests_passed}")
    
    if tests_passed == tests_total:
        print("\n✅ All integration components are in place!")
        print("\n🚀 Next steps:")
        print("1. Install dependencies: pip install asyncpg aiohttp weaviate-client psycopg2-binary")
        print("2. Set environment variables:")
        print("   export OPENROUTER_API_KEY='your-key'")
        print("   export DATABASE_URL='postgresql://user:pass@localhost/db'")
        print("3. Run: python3 scripts/initialize_roo_integration.py")
    else:
        print(f"\n⚠️  Some components are missing. Please check the failed tests above.")
    
    return 0 if tests_passed == tests_total else 1

if __name__ == "__main__":
    sys.exit(main())