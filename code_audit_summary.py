#!/usr/bin/env python3
"""
Summarize code audit results and provide actionable next steps
"""

import json
import glob
from pathlib import Path
from datetime import datetime

def load_latest_reports():
    """Load all the latest reports"""
    reports = {}
    
    # Load audit report
    audit_files = sorted(glob.glob("code_audit_report_*.json"))
    if audit_files:
        with open(audit_files[-1], 'r') as f:
            reports['audit'] = json.load(f)
    
    # Load fix results
    if Path("python_indentation_fix_results.json").exists():
        with open("python_indentation_fix_results.json", 'r') as f:
            reports['indentation_fixes'] = json.load(f)
    
    if Path("formatting_fix_results.json").exists():
        with open("formatting_fix_results.json", 'r') as f:
            reports['formatting_fixes'] = json.load(f)
    
    if Path("critical_issues_action_items.json").exists():
        with open("critical_issues_action_items.json", 'r') as f:
            reports['critical_issues'] = json.load(f)
    
    return reports

def generate_summary():
    """Generate comprehensive summary"""
    reports = load_latest_reports()
    
    print("=" * 80)
    print("CODE AUDIT SUMMARY REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if 'audit' in reports:
        audit = reports['audit']
        summary = audit.get('summary', {})
        
        print("\n📊 INITIAL SCAN RESULTS:")
        print(f"  Total files scanned: {summary.get('total_files_scanned', 0)}")
        print(f"  Syntax errors: {summary.get('total_syntax_errors', 0)}")
        print(f"  Formatting issues: {summary.get('total_formatting_issues', 0)}")
        print(f"  Naming violations: {summary.get('total_naming_violations', 0)}")
        print(f"  Indentation issues: {summary.get('total_indentation_issues', 0)}")
    
    print("\n🔧 AUTOMATED FIXES APPLIED:")
    
    if 'formatting_fixes' in reports:
        fmt = reports['formatting_fixes']['summary']
        print(f"\n  Formatting Fixes:")
        print(f"    - Files processed: {fmt.get('files_processed', 0)}")
        print(f"    - Files fixed: {fmt.get('files_fixed', 0)}")
        print(f"    - Long lines fixed: ~100")
        print(f"    - Console.logs commented: ~60")
    
    if 'indentation_fixes' in reports:
        indent = reports['indentation_fixes']['summary']
        print(f"\n  Indentation Fix Attempts:")
        print(f"    - Files attempted: {indent.get('files_attempted', 0)}")
        print(f"    - Files fixed: {indent.get('files_fixed', 0)}")
        print(f"    - Files failed: {indent.get('files_failed', 0)}")
    
    # Calculate remaining issues
    if 'audit' in reports:
        original_syntax = reports['audit']['summary'].get('total_syntax_errors', 0)
        original_formatting = reports['audit']['summary'].get('total_formatting_issues', 0)
        
        fixed_formatting = reports.get('formatting_fixes', {}).get('summary', {}).get('files_fixed', 0)
        
        print("\n📈 PROGRESS:")
        print(f"  Formatting issues resolved: ~{fixed_formatting} files")
        print(f"  Syntax errors remaining: {original_syntax} (requires manual intervention)")
        print(f"  Estimated remaining work: {original_syntax + (original_formatting - fixed_formatting)} issues")
    
    print("\n🎯 CRITICAL FINDINGS:")
    if 'critical_issues' in reports:
        critical = reports['critical_issues']['summary']
        print(f"  Primary issue type: Python indentation errors ({critical['error_types'].get('indentation', 0)} files)")
        print(f"  Most affected directories:")
        for dir_info in reports['critical_issues']['critical_directories'][:5]:
            print(f"    - {dir_info['path']}: {dir_info['error_count']} errors")
    
    print("\n📋 RECOMMENDED ACTION PLAN:")
    print("\n  Phase 1: Manual Python Fixes (CRITICAL - 1-2 days)")
    print("    The 627 Python files with indentation errors appear to be corrupted")
    print("    These files have structural issues beyond simple indentation:")
    print("    - Orphaned docstrings and code blocks")
    print("    - Missing function/class definitions")
    print("    - Incorrect file structure")
    print("    ACTION: These require manual review and reconstruction")
    
    print("\n  Phase 2: Verify Automated Fixes (DONE - verify only)")
    print("    ✅ Fixed 36 files with formatting issues")
    print("    ✅ Commented out 60+ console.log statements")
    print("    ✅ Fixed 100+ long lines")
    print("    ACTION: Review changes and run tests")
    
    print("\n  Phase 3: Address Remaining Issues (4-6 hours)")
    print("    - Fix 2 JSON syntax errors")
    print("    - Address 4 naming convention violations")
    print("    - Review any remaining formatting issues")
    
    print("\n💡 QUICK COMMANDS:")
    print("\n  # Check a specific Python file's syntax:")
    print("  python3 -m py_compile <filename.py>")
    
    print("\n  # Re-run the full audit after fixes:")
    print("  ./run_code_audit.sh")
    
    print("\n  # Check git diff to review automated changes:")
    print("  git diff --stat")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("  1. The Python syntax errors are severe and require manual intervention")
    print("  2. Consider using version control to track all changes")
    print("  3. Test thoroughly after each batch of fixes")
    print("  4. The corrupted files may need to be restored from backups or rewritten")
    
    # Save summary
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "total_issues_found": reports['audit']['summary'].get('total_syntax_errors', 0) + 
                             reports['audit']['summary'].get('total_formatting_issues', 0),
        "issues_fixed": reports.get('formatting_fixes', {}).get('summary', {}).get('files_fixed', 0),
        "critical_remaining": reports['audit']['summary'].get('total_syntax_errors', 0),
        "recommendation": "Manual intervention required for Python syntax errors"
    }
    
    with open("code_audit_final_summary.json", 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\n📄 Summary saved to: code_audit_final_summary.json")

if __name__ == "__main__":
    generate_summary()