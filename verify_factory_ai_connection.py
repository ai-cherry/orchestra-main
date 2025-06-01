#!/usr/bin/env python3
"""
Verify Factory AI Connection
This script checks that Factory AI is connected to the correct environment
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_environment():
    """Check and display environment information"""
    print("🔍 Factory AI Connection Verification")
    print("=" * 50)
    
    # Check Python environment
    print("\n📍 Python Environment:")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python version: {sys.version.split()[0]}")
    print(f"   Virtual env: {os.environ.get('VIRTUAL_ENV', 'Not activated!')}")
    
    # Check current directory
    print(f"\n📂 Working Directory:")
    print(f"   Current path: {os.getcwd()}")
    print(f"   Expected path: /root/orchestra-main")
    
    # Check git repository
    print("\n🔗 Git Repository:")
    try:
        remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
        branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()[:8]
        
        print(f"   Remote: {remote}")
        print(f"   Branch: {branch}")
        print(f"   Commit: {commit}")
        
        # Check if up to date
        subprocess.run(['git', 'fetch'], capture_output=True)
        status = subprocess.check_output(['git', 'status', '-uno'], text=True)
        if "Your branch is up to date" in status:
            print("   Status: ✅ Up to date with remote")
        else:
            print("   Status: ⚠️  Not synced with remote")
    except Exception as e:
        print(f"   Error checking git: {e}")
    
    # Check Factory AI config
    print("\n⚙️  Factory AI Config:")
    config_path = Path(".factory-ai-config")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        print("   ✅ Config file found")
        print(f"   Workspace: {config.get('workspace')}")
        print(f"   Strategy: {config.get('sync_strategy')}")
    else:
        print("   ❌ No .factory-ai-config found")
    
    # Check important files
    print("\n📄 Key Files:")
    important_files = [
        "venv/bin/python",
        "requirements/base.txt",
        "agent/app/main.py",
        "scripts/factory_ai_sync.sh",
        ".env"
    ]
    
    for file in important_files:
        exists = "✅" if Path(file).exists() else "❌"
        print(f"   {exists} {file}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    issues = []
    if not os.environ.get('VIRTUAL_ENV'):
        issues.append("Activate virtual environment: source venv/bin/activate")
    
    if os.getcwd() != "/root/orchestra-main":
        issues.append("Change to correct directory: cd /root/orchestra-main")
    
    if not Path(".factory-ai-config").exists():
        issues.append("Factory AI config missing - run initial setup")
    
    if issues:
        for issue in issues:
            print(f"   ⚠️  {issue}")
    else:
        print("   ✅ Everything looks good!")
    
    return len(issues) == 0

if __name__ == "__main__":
    if check_environment():
        print("\n🎉 Factory AI is properly connected!")
        sys.exit(0)
    else:
        print("\n❌ Issues found - please fix them before proceeding")
        sys.exit(1) 