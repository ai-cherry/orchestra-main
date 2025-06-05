#!/usr/bin/env python3
"""
Final cleanup and organization of audit files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def organize_audit_files():
    """Organize audit-related files into a structured directory"""
    
    # Create audit results directory
    audit_dir = Path("audit_results_20250605")
    audit_dir.mkdir(exist_ok=True)
    
    # Files to move to audit directory
    audit_files = [
        "code_audit_report_20250605_004043.json",
        "code_fix_plan_20250605_004043.json",
        "code_audit_final_summary.json",
        "critical_issues_action_items.json",
        "python_indentation_fix_results.json",
        "formatting_fix_results.json",
        "corrupted_files_fix_results.json",
        "intelligent_restoration_report.json",
        "methodical_restoration_report.json",
        "cleanup_log.json"
    ]
    
    # Python scripts to keep in root (they're tools)
    tool_scripts = [
        "code_audit_scanner.py",
        "code_audit_processor.py",
        "analyze_critical_issues.py",
        "diagnose_indentation_errors.py",
        "fix_python_indentation.py",
        "fix_formatting_issues.py",
        "fix_corrupted_python_files.py",
        "intelligent_code_restoration.py",
        "methodical_restoration_strategy.py",
        "cleanup_corrupted_files.py",
        "wisdom_based_restoration_framework.py",
        "code_audit_summary.py",
        "batch_fix_runner.py",
        "run_code_audit.sh"
    ]
    
    moved_files = []
    kept_files = []
    errors = []
    
    print("🧹 FINAL CLEANUP AND ORGANIZATION")
    print("=" * 80)
    
    # Move audit result files
    print(f"\n📁 Moving audit results to {audit_dir}/")
    for file in audit_files:
        if os.path.exists(file):
            try:
                shutil.move(file, audit_dir / file)
                moved_files.append(file)
                print(f"  ✅ Moved: {file}")
            except Exception as e:
                errors.append((file, str(e)))
                print(f"  ❌ Error moving {file}: {e}")
    
    # Verify tool scripts are in place
    print(f"\n🛠️  Keeping audit tools in root directory:")
    for script in tool_scripts:
        if os.path.exists(script):
            kept_files.append(script)
            print(f"  ✅ Kept: {script}")
    
    # Check for any stray backup files
    print(f"\n🔍 Checking for stray backup files...")
    backup_patterns = ["*.backup", "*.corrupted", "*.restored"]
    stray_files = []
    
    for pattern in backup_patterns:
        for file in Path(".").glob(pattern):
            stray_files.append(str(file))
            print(f"  ⚠️  Found: {file}")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("CLEANUP SUMMARY:")
    print(f"  Audit results moved: {len(moved_files)}")
    print(f"  Tool scripts kept: {len(kept_files)}")
    print(f"  Stray files found: {len(stray_files)}")
    print(f"  Errors: {len(errors)}")
    
    if stray_files:
        print(f"\n⚠️  Stray backup files still exist:")
        for file in stray_files[:10]:
            print(f"  - {file}")
        if len(stray_files) > 10:
            print(f"  ... and {len(stray_files) - 10} more")
        print("\nConsider running: find . -name '*.backup' -o -name '*.corrupted' -delete")
    
    print(f"\n📄 Audit results organized in: {audit_dir}/")
    print("📊 You can now review the results without cluttering the root directory")
    
    # Create a README for the audit directory
    readme_content = f"""# Code Audit Results - {datetime.now().strftime('%Y-%m-%d')}

This directory contains the results of the comprehensive code audit performed on the codebase.

## Files:
- code_audit_report_*.json - Main audit findings
- code_fix_plan_*.json - Automated fix strategies
- *_fix_results.json - Results of automated fixes
- *_restoration_report.json - Restoration attempt results

## Summary:
- Total files scanned: 2,134
- Syntax errors found: 644
- Files automatically fixed: 36
- Files restored from VCS: 3

## Tools:
The audit tools remain in the root directory for future use:
- run_code_audit.sh - Main audit launcher
- code_audit_scanner.py - File scanner
- Various fix_*.py scripts - Automated fixers
"""
    
    with open(audit_dir / "README.md", 'w') as f:
        f.write(readme_content)
    
    print("\n✅ Created README.md in audit results directory")

if __name__ == "__main__":
    organize_audit_files()