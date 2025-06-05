#!/usr/bin/env python3
"""
Analyze critical issues from code audit report and create actionable work items
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def analyze_audit_report(report_file):
    """Analyze the audit report and extract critical insights"""
    with open(report_file, 'r') as f:
        data = json.load(f)
    
    print("🔍 CRITICAL ISSUES ANALYSIS")
    print("=" * 80)
    
    # Analyze syntax errors by directory
    syntax_errors = data.get('syntax_errors', [])
    errors_by_dir = defaultdict(list)
    errors_by_type = defaultdict(int)
    
    for error in syntax_errors:
        file_path = Path(error['file'])
        dir_path = str(file_path.parent)
        errors_by_dir[dir_path].append(error)
        
        # Extract error type
        error_msg = error.get('error', '')
        if 'unexpected indent' in error_msg:
            errors_by_type['indentation'] += 1
        elif 'invalid syntax' in error_msg:
            errors_by_type['syntax'] += 1
        elif 'EOL while scanning' in error_msg:
            errors_by_type['unclosed_string'] += 1
        elif 'EOF while scanning' in error_msg:
            errors_by_type['unclosed_bracket'] += 1
        else:
            errors_by_type['other'] += 1
    
    # Print error type breakdown
    print("\n📊 Syntax Error Types:")
    for error_type, count in sorted(errors_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {error_type}: {count}")
    
    # Find directories with most errors
    print("\n📁 Directories with Most Syntax Errors:")
    sorted_dirs = sorted(errors_by_dir.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for dir_path, errors in sorted_dirs:
        print(f"  - {dir_path}: {len(errors)} errors")
    
    # Analyze formatting issues
    formatting_issues = data.get('formatting_issues', [])
    format_by_type = defaultdict(int)
    
    for issue in formatting_issues:
        issue_desc = issue.get('issue', '')
        if 'line too long' in issue_desc.lower():
            format_by_type['long_lines'] += 1
        elif 'console.log' in issue_desc.lower():
            format_by_type['console_logs'] += 1
        elif 'shebang' in issue_desc.lower():
            format_by_type['missing_shebang'] += 1
        else:
            format_by_type['other'] += 1
    
    print("\n📐 Formatting Issue Types:")
    for issue_type, count in sorted(format_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {issue_type}: {count}")
    
    # Create prioritized work list
    print("\n🎯 PRIORITIZED WORK ITEMS:")
    print("\n1. IMMEDIATE FIXES (Blocking):")
    
    # Group Python files with indentation errors
    python_indent_errors = [e for e in syntax_errors 
                           if e['file'].endswith('.py') and 'unexpected indent' in e.get('error', '')]
    
    if python_indent_errors:
        print(f"\n   Python Indentation Errors ({len(python_indent_errors)} files):")
        for error in python_indent_errors[:5]:
            print(f"   - {error['file']} (line {error.get('line', 'unknown')})")
        if len(python_indent_errors) > 5:
            print(f"   ... and {len(python_indent_errors) - 5} more")
    
    # Find JSON syntax errors
    json_errors = [e for e in syntax_errors if e.get('language') == 'json']
    if json_errors:
        print(f"\n   JSON Syntax Errors ({len(json_errors)} files):")
        for error in json_errors[:5]:
            print(f"   - {error['file']}: {error.get('error', 'unknown error')}")
    
    print("\n2. QUICK WINS (Automated):")
    print("   - Long lines: Can be auto-formatted")
    print("   - Missing shebangs: Easy to add")
    print("   - Console.log statements: Can be removed/commented")
    
    # Generate fix commands
    print("\n💻 QUICK FIX COMMANDS:")
    print("\n# Fix Python indentation issues in bulk:")
    print("find . -name '*.py' -type f | xargs -I {} python -m py_compile {}")
    
    print("\n# Check specific Python file syntax:")
    print("python -m py_compile <filename.py>")
    
    print("\n# Fix long lines in Python files:")
    print("autopep8 --in-place --max-line-length 120 <filename.py>")
    
    print("\n# Validate JSON files:")
    print("python -m json.tool <filename.json> > /dev/null")
    
    # Save actionable items
    output_file = "critical_issues_action_items.json"
    action_items = {
        "summary": {
            "total_syntax_errors": len(syntax_errors),
            "error_types": dict(errors_by_type),
            "formatting_issues": len(formatting_issues),
            "format_types": dict(format_by_type)
        },
        "critical_directories": [
            {"path": dir_path, "error_count": len(errors)} 
            for dir_path, errors in sorted_dirs
        ],
        "sample_fixes": {
            "python_indentation": python_indent_errors[:10],
            "json_syntax": json_errors[:10]
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(action_items, f, indent=2)
    
    print(f"\n📄 Action items saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Try to find the latest audit report
        import glob
        reports = sorted(glob.glob("code_audit_report_*.json"))
        if reports:
            report_file = reports[-1]
            print(f"Using latest report: {report_file}")
        else:
            print("Usage: python analyze_critical_issues.py <audit_report.json>")
            sys.exit(1)
    else:
        report_file = sys.argv[1]
    
    analyze_audit_report(report_file)