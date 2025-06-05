#!/usr/bin/env python3
"""Batch fix runner for code quality issues"""

import json
import subprocess
import sys
from pathlib import Path

def load_fix_plan(plan_file):
    """Load the fix plan"""
    with open(plan_file, 'r') as f:
        return json.load(f)

def fix_indentation_issues(files):
    """Fix indentation issues in files"""
    python_files = [f for f in files if f.endswith('.py')]
    js_files = [f for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx'))]
    
    if python_files:
        print(f"Fixing indentation in {len(python_files)} Python files...")
        subprocess.run([sys.executable, "fix_python_formatting.py"] + python_files)
    
    if js_files:
        print(f"Fixing indentation in {len(js_files)} JS/TS files...")
        subprocess.run(["./fix_javascript_formatting.sh"] + js_files)

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_fix_runner.py <fix_plan.json>")
        sys.exit(1)
    
    plan = load_fix_plan(sys.argv[1])
    
    # Fix indentation issues first (automated)
    indentation_data = plan.get("batch_fixes", {}).get("indentation", {})
    if indentation_data.get("files"):
        fix_indentation_issues(indentation_data["files"])
    
    print("\n✅ Automated fixes complete!")
    print("\nNext steps:")
    print("1. Review and fix syntax errors manually")
    print("2. Address naming convention violations")
    print("3. Run tests to ensure fixes didn't break functionality")

if __name__ == "__main__":
    main()
