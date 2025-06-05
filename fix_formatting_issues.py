#!/usr/bin/env python3
"""
Fix formatting issues in the codebase (long lines, console.logs, etc.)
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple

class FormattingFixer:
    def __init__(self, audit_report_path: str):
        with open(audit_report_path, 'r') as f:
            self.audit_data = json.load(f)
        
        self.formatting_issues = self.audit_data.get('formatting_issues', [])
        self.fixed_count = 0
        self.results = []
    
    def fix_long_lines_python(self, file_path: str, issues: List[Dict]) -> Tuple[bool, str]:
        """Fix long lines in Python files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            for issue in issues:
                line_num = issue.get('line', 0) - 1  # Convert to 0-based
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    
                    # Skip if it's a comment or string
                    stripped = line.strip()
                    if stripped.startswith('#') or '"""' in line or "'''" in line:
                        continue
                    
                    # Try to break long lines at logical points
                    if len(line) > 120:
                        # For imports
                        if 'import' in line and ',' in line:
                            parts = line.split(',')
                            indent = len(line) - len(line.lstrip())
                            new_lines = [parts[0] + ',\n']
                            for part in parts[1:]:
                                new_lines.append(' ' * (indent + 4) + part.strip() + ',\n')
                            new_lines[-1] = new_lines[-1].rstrip(',\n') + '\n'
                            lines[line_num:line_num+1] = new_lines
                            modified = True
                        
                        # For function calls
                        elif '(' in line and ')' in line and ',' in line:
                            # Simple line breaking for function calls
                            indent = len(line) - len(line.lstrip())
                            if line.count('(') == 1 and line.count(')') == 1:
                                before_paren = line[:line.index('(') + 1]
                                after_paren = line[line.index('(') + 1:line.rindex(')')]
                                closing = line[line.rindex(')'):]
                                
                                args = after_paren.split(',')
                                if len(args) > 1:
                                    new_lines = [before_paren + '\n']
                                    for arg in args:
                                        new_lines.append(' ' * (indent + 4) + arg.strip() + ',\n')
                                    new_lines[-1] = new_lines[-1].rstrip(',\n') + '\n'
                                    new_lines.append(' ' * indent + closing)
                                    lines[line_num:line_num+1] = new_lines
                                    modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True, f"Fixed {len(issues)} long lines"
            else:
                return False, "No fixable long lines found"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def fix_console_logs_js(self, file_path: str, issues: List[Dict]) -> Tuple[bool, str]:
        """Remove or comment out console.log statements in JS files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            modified = False
            for issue in issues:
                line_num = issue.get('line', 0) - 1  # Convert to 0-based
                if 0 <= line_num < len(lines):
                    line = lines[line_num]
                    if 'console.log' in line and not line.strip().startswith('//'):
                        # Comment out the line
                        indent = len(line) - len(line.lstrip())
                        lines[line_num] = ' ' * indent + '// ' + line.lstrip()
                        modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True, f"Commented out {len(issues)} console.log statements"
            else:
                return False, "No console.log statements to fix"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def fix_missing_shebang(self, file_path: str) -> Tuple[bool, str]:
        """Add shebang to shell scripts"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('#!'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('#!/bin/bash\n' + content)
                return True, "Added shebang"
            else:
                return False, "Shebang already present"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def process_formatting_issues(self):
        """Process all formatting issues"""
        # Group issues by file
        issues_by_file = {}
        for issue in self.formatting_issues:
            file_path = issue.get('file', '')
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        print(f"🔧 FORMATTING FIXER")
        print(f"=" * 80)
        print(f"Processing {len(self.formatting_issues)} formatting issues in {len(issues_by_file)} files")
        
        # Process each file
        for file_path, issues in issues_by_file.items():
            # Skip files with syntax errors
            has_syntax_error = any(
                error['file'] == file_path 
                for error in self.audit_data.get('syntax_errors', [])
            )
            
            if has_syntax_error:
                print(f"  ⏭️  Skipping {file_path} (has syntax errors)")
                continue
            
            # Determine issue types
            long_lines = [i for i in issues if 'line too long' in i.get('issue', '').lower()]
            console_logs = [i for i in issues if 'console.log' in i.get('issue', '').lower()]
            missing_shebang = any('shebang' in i.get('issue', '').lower() for i in issues)
            
            success = False
            message = ""
            
            # Fix based on file type and issue
            if file_path.endswith('.py') and long_lines:
                success, message = self.fix_long_lines_python(file_path, long_lines)
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')) and console_logs:
                success, message = self.fix_console_logs_js(file_path, console_logs)
            elif file_path.endswith('.sh') and missing_shebang:
                success, message = self.fix_missing_shebang(file_path)
            
            if success:
                self.fixed_count += 1
                print(f"  ✅ Fixed: {file_path} - {message}")
            elif message:
                print(f"  ❌ Failed: {file_path} - {message}")
            
            self.results.append({
                "file": file_path,
                "issues": len(issues),
                "success": success,
                "message": message
            })
        
        # Summary
        print(f"\n{'=' * 80}")
        print(f"SUMMARY:")
        print(f"  Files processed: {len(issues_by_file)}")
        print(f"  Files fixed: {self.fixed_count}")
        print(f"  Total issues addressed: {sum(r['issues'] for r in self.results if r['success'])}")
        
        # Save results
        output_file = "formatting_fix_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_issues": len(self.formatting_issues),
                    "files_processed": len(issues_by_file),
                    "files_fixed": self.fixed_count
                },
                "details": self.results
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")

def main():
    # Find latest audit report
    import glob
    reports = sorted(glob.glob("code_audit_report_*.json"))
    if not reports:
        print("❌ No audit report found. Run ./run_code_audit.sh first.")
        return
    
    report_file = reports[-1]
    print(f"Using audit report: {report_file}")
    
    fixer = FormattingFixer(report_file)
    fixer.process_formatting_issues()
    
    print("\n✅ Formatting fixes complete!")
    print("\nNext steps:")
    print("1. Review the changes made")
    print("2. Run tests to ensure functionality wasn't affected")
    print("3. Re-run the audit to see remaining issues")

if __name__ == "__main__":
    main()