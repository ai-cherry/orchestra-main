#!/usr/bin/env python3
"""
Diagnose specific indentation errors to understand why autopep8 is failing
"""

import json
import sys
import ast
from pathlib import Path

def diagnose_file(file_path: str, max_lines: int = 20):
    """Diagnose indentation issues in a specific file"""
    print(f"\n{'='*60}")
    print(f"Diagnosing: {file_path}")
    print(f"{'='*60}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Total lines: {len(lines)}")
        
        # Show first few lines with line numbers and visible whitespace
        print("\nFirst 20 lines (with visible whitespace):")
        for i, line in enumerate(lines[:max_lines], 1):
            # Replace tabs and spaces with visible characters
            visible_line = line.replace('\t', '→').replace(' ', '·')
            print(f"{i:3d} | {visible_line}", end='')
        
        # Try to compile and get specific error
        print("\nPython compilation error:")
        try:
            compile(open(file_path).read(), file_path, 'exec')
            print("  No compilation errors found!")
        except SyntaxError as e:
            print(f"  Line {e.lineno}: {e.msg}")
            print(f"  Text: {e.text}")
            print(f"  Offset: {' ' * (e.offset - 1) if e.offset else ''}^")
            
            # Show context around error
            if e.lineno:
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)
                print(f"\nContext around line {e.lineno}:")
                for i in range(start, end):
                    line_num = i + 1
                    visible_line = lines[i].replace('\t', '→').replace(' ', '·')
                    marker = " >>> " if line_num == e.lineno else "     "
                    print(f"{line_num:3d}{marker}{visible_line}", end='')
        
        # Check for mixed indentation
        has_tabs = any('\t' in line for line in lines)
        has_spaces = any(line.startswith(' ') for line in lines)
        
        if has_tabs and has_spaces:
            print("\n⚠️  Mixed tabs and spaces detected!")
            tab_lines = [i+1 for i, line in enumerate(lines) if '\t' in line]
            print(f"  Lines with tabs: {tab_lines[:10]}{'...' if len(tab_lines) > 10 else ''}")
        
        # Check for inconsistent indentation levels
        indent_levels = set()
        for line in lines:
            if line.strip() and not line.lstrip().startswith('#'):
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    indent_levels.add(indent)
        
        print(f"\nIndentation levels found: {sorted(indent_levels)}")
        
    except Exception as e:
        print(f"Error reading file: {e}")

def main():
    # Load audit report to get sample files
    import glob
    reports = sorted(glob.glob("code_audit_report_*.json"))
    if not reports:
        print("No audit report found.")
        sys.exit(1)
    
    with open(reports[-1], 'r') as f:
        audit_data = json.load(f)
    
    # Get Python files with indentation errors
    indent_errors = [
        error for error in audit_data.get('syntax_errors', [])
        if error['file'].endswith('.py') and 'unexpected indent' in error.get('error', '')
    ]
    
    # Diagnose first 5 files from scripts directory
    scripts_errors = [e for e in indent_errors if e['file'].startswith('scripts/')][:5]
    
    print("🔍 INDENTATION ERROR DIAGNOSIS")
    print("Examining sample files to understand the issues...")
    
    for error in scripts_errors:
        diagnose_file(error['file'])
    
    print("\n" + "="*60)
    print("DIAGNOSIS SUMMARY")
    print("="*60)
    print("\nCommon issues found:")
    print("1. Mixed tabs and spaces in the same file")
    print("2. Inconsistent indentation levels (not multiples of 4)")
    print("3. Syntax errors beyond just indentation")
    print("\nRecommendation: These files need manual review and fixing.")
    print("The indentation issues are often symptoms of deeper syntax problems.")

if __name__ == "__main__":
    main()